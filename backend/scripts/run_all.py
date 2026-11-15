"""Test complet du backend en UNE commande :
    python -m scripts.run_all            (toutes les cibles de démo)
    python -m scripts.run_all Barnard    (une seule cible)

1. lance les tests automatiques (pytest) ;
2. pour chaque cible : étape 0 (cible) -> étape 1 (recherche IRSA réelle) -> étape 1b (sélection) ;
3. vérifie automatiquement les résultats et écrit un rapport dans cache/rapport_test.txt.
"""
import subprocess
import sys
import time
from pathlib import Path

from app.core import config
from app.core.search import search_images
from app.core.align import align_group
from app.core.group import group_frames
from app.core.measure import (calibrated_sigma_scale, fit_motion, measure_positions, plan_display,
                               positions_plot, render_display)
from app.core.screen import screen_selection
from app.core.select import select_images
from app.core.target import TargetRequest, resolve_target

TARGETS = sys.argv[1:] or ["Barnard", "WISE 0855-0714", "nep"]
REPORT = Path(config.CACHE_DIR) / "rapport_test.txt"
lines: list[str] = []
n_ok = n_fail = 0


def out(msg=""):
    print(msg)
    lines.append(msg)


def check(cond: bool, label: str):
    global n_ok, n_fail
    n_ok += cond
    n_fail += not cond
    out(f"   {'OK  ' if cond else 'ECHEC'} {label}")


# --- 1. Tests automatiques -----------------------------------------------------
out("=" * 70)
out("1. TESTS AUTOMATIQUES (pytest)")
out("=" * 70)
res = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:warnings"],
                     capture_output=True, text=True)
summary = [l for l in res.stdout.strip().splitlines() if "passed" in l or "failed" in l or "error" in l]
out("   " + (summary[-1] if summary else res.stdout[-300:]))
check(res.returncode == 0, "tous les tests unitaires passent")
if res.returncode != 0:
    out(res.stdout[-2000:])

# --- 2. Chaîne complète sur chaque cible ---------------------------------------
for name in TARGETS:
    out()
    out("=" * 70)
    out(f"2. CHAÎNE COMPLÈTE : {name}")
    out("=" * 70)
    try:
        # Étape 0 : cible
        t = resolve_target(TargetRequest(name=name))
        out(f"[0] Cible   : {t.label}  RA={t.ra_deg:.5f}  Dec={t.dec_deg:.5f}  "
            f"zone={t.size_arcmin}' ({t.size_px} px)  lat. écliptique={t.ecliptic_lat:.1f}°")
        for w in t.warnings:
            out(f"      ! {w}")

        # Étape 1 : recherche IRSA
        t0 = time.perf_counter()
        s = search_images(t)
        dt = time.perf_counter() - t0
        out(f"[1] Search  : {s.n_images} images, {s.n_days} jours, {s.first_date} -> {s.last_date}"
            f"  ({s.source}, {dt:.1f} s)")
        out(f"      détecteurs={s.by_detector}")
        out(f"      versions={s.by_release}  relevés={s.by_survey}")
        if s.errors:
            out(f"      ERREURS IRSA : {s.errors}")
        check(s.n_images > 0, "IRSA renvoie des images")
        check(not s.errors, "aucune collection en erreur")
        check(len(s.by_detector) == 6, "les 6 détecteurs sont présents")
        check(all(i.cutout_url.startswith("https://irsa.ipac.caltech.edu/") for i in s.images),
              "toutes les URLs de cutout pointent vers IRSA")

        # Étape 1b : sélection
        sel = select_images(s)
        out(f"[1b] Select : {sel.n_found} trouvées -> {sel.n_kept} gardées -> "
            f"{sel.n_selected} à télécharger ; {sel.n_visits} passages "
            f"({sel.n_major_visits} principaux)")
        shown = sel.visits if len(sel.visits) <= 12 else sel.visits[:6] + sel.visits[-3:]
        for v in shown:
            out(f"      #{v.index:<3} {v.start} -> {v.end} ({v.duration_days:>5} j) "
                f"{v.n_images:>5} images, {v.n_selected:>3} choisies{' (mineur)' if v.minor else ''}")
        if len(sel.visits) > 12:
            out(f"      ... ({len(sel.visits) - 9} passages non affichés)")
        if sel.rejected_reasons:
            out(f"      rejets : {sel.rejected_reasons}")
        check(sel.usable_for_motion, "au moins 3 passages principaux (mouvement mesurable)")
        check(0 < sel.n_selected <= 200 + sel.n_visits, "nombre d'images à télécharger raisonnable")
        check(sel.n_rejected <= 0.5 * max(sel.n_found, 1), "moins de 50 % d'images rejetées")
        if t.pmra is not None and t.pmdec is not None and sel.visits:
            years = (time.mktime(time.strptime(sel.visits[-1].end, "%Y-%m-%d")) -
                     time.mktime(time.strptime(sel.visits[0].start, "%Y-%m-%d"))) / 3.156e7
            mu = (t.pmra ** 2 + t.pmdec ** 2) ** 0.5 / 1000
            out(f"      durée couverte : {years:.2f} an -> déplacement attendu "
                f"{mu * years:.1f}\" = {mu * years / 6.15:.2f} px")

        # Étapes 2 + 3 : téléchargement + contrôle de netteté (échantillon limité)
        small = select_images(s, max_per_visit_detector=3, max_total=80)
        t0 = time.perf_counter()
        sc = screen_selection(small, progress=lambda i, n: print(f"\r      téléchargement {i}/{n}",
                                                                   end="", flush=True))
        print()
        out(f"[2-3] Fetch+Screen : {sc.n_downloaded}/{sc.n_selected} téléchargées "
            f"({time.perf_counter() - t0:.0f} s), {sc.n_kept} gardées, "
            f"{sc.kept_visits} passages couverts")
        out(f"      statuts : {sc.by_status}")
        if sc.download_errors:
            out(f"      échecs de téléchargement : {len(sc.download_errors)} "
                f"(ex. {next(iter(sc.download_errors.values()))[:80]})")
        snrs = [f.snr for f in sc.frames if f.keep and f.snr]
        if snrs:
            out(f"      S/N de la cible : min {min(snrs):.0f}, médiane {sorted(snrs)[len(snrs)//2]:.0f}")
        offs = [f.centroid_offset_px for f in sc.frames if f.keep and f.centroid_offset_px is not None]
        if offs:
            out(f"      écart position prédite/mesurée : médiane {sorted(offs)[len(offs)//2]:.2f} px")
        check(sc.n_downloaded >= 0.7 * sc.n_selected, "au moins 70 % des cutouts téléchargés")
        check(sc.kept_visits >= 3, "images gardées sur au moins 3 passages")

        # Étape 4 : groupes de longueur d'onde comparable
        g = group_frames(sc.frames, small.visits)
        out(f"[4] Group : {g.n_groups} groupes (tolérance ±{g.tolerance:.0%}), "
            f"{len(g.ungrouped)} images isolées, groupe par défaut = {g.default_group}")
        for gr in g.groups[:6]:
            dates = " ".join(f.date_utc[:10] for f in gr.frames)
            out(f"      {gr.id:<10} {gr.wl_min_um:.3f}-{gr.wl_max_um:.3f} µm "
                f"(±{gr.max_delta_rel:.1%}) {gr.n_epochs} passages sur {gr.span_days:.0f} j : {dates}")
        if g.n_groups > 6:
            out(f"      ... ({g.n_groups - 6} autres groupes)")
        check(g.n_groups > 0, "au moins un groupe de longueur d'onde")
        check(any(gr.usable_for_motion for gr in g.groups),
              "au moins un groupe couvre 3 passages (mouvement visible à λ constante)")

        # Étape 5 : alignement des 3 meilleurs groupes
        fby = {f.frame_id: f for f in sc.frames}
        for gr in g.groups[:3]:
            od = Path(config.CACHE_DIR) / "aligned" / t.cache_key / gr.id
            a = align_group(t, gr, fby, out_dir=od)
            offs = [f.target_offset_px for f in a.frames if f.target_offset_px is not None]
            out(f"[5] Align {gr.id:<10}: étoiles fixes décalées de {a.max_field_shift_px} px max "
                f"({a.n_field_stars_ref} étoiles) ; cible : trajet mesuré {a.target_track_px} px, "
                f"prédit {a.target_expected_track_px} px ; écart médian "
                f"{sorted(offs)[len(offs)//2] if offs else None} px")
            out(f"      animation : {a.gif}")
            check(a.alignment_ok, f"{gr.id} : étoiles fixes alignées à moins de 0,5 px")

        # Étape 6 : trajectoire complète (tous groupes confondus) + animation
        ms, cache = measure_positions(t, sc.frames, g, small.visits)
        mo = fit_motion(ms)
        out(f"[6] Measure : {mo.n_used}/{mo.n_points} positions utilisées, "
            f"{mo.n_distinct_epochs} instants, {mo.coverage_start} -> {mo.coverage_end}")
        if mo.mu_arcsec_yr is not None:
            out(f"      μ = {mo.mu_arcsec_yr} ± {mo.mu_err_arcsec_yr} \"/an "
                f"(est {mo.mu_ra_arcsec_yr}, nord {mo.mu_dec_arcsec_yr}), angle {mo.position_angle_deg}°, "
                f"χ² réduit {mo.chi2_red}, modèle {mo.model}")
        out(f"      statut : {mo.status} ({mo.status_reason})")
        out(f"      ponts entre groupes : {len(mo.components)} composante(s) ; "
            f"groupes signalés : {[d.group_id for d in mo.groups if d.flag]}")
        rejected = [m for m in mo.measures if not m.used]
        if rejected:
            out(f"      {len(rejected)} position(s) écartée(s), ex. {rejected[0].rejected_reason}")
        if t.pmra is not None and t.pmdec is not None and mo.mu_arcsec_yr is not None:
            mu_cat = (t.pmra ** 2 + t.pmdec ** 2) ** 0.5 / 1000
            out(f"      catalogue : {mu_cat:.2f} \"/an -> écart {abs(mo.mu_arcsec_yr - mu_cat):.2f} \"/an "
                f"({abs(mo.mu_arcsec_yr - mu_cat) / max(mo.mu_err_arcsec_yr, 1e-6):.1f}σ)")
            check(abs(mo.mu_arcsec_yr - mu_cat) < 3 * max(mo.mu_err_arcsec_yr, 0.3),
                  "mouvement mesuré compatible avec le catalogue (< 3σ)")
        mo_raw = fit_motion(ms, with_offsets=False)
        if mo_raw.mu_arcsec_yr is not None:
            out(f"      sans correction des décalages : μ = {mo_raw.mu_arcsec_yr} ± "
                f"{mo_raw.mu_err_arcsec_yr} \"/an, angle {mo_raw.position_angle_deg}°")
        plan = plan_display(mo.measures, fby, calibrated_sigma_scale(mo))
        odir = Path(config.CACHE_DIR) / "trajectory" / t.cache_key
        render_display(t, mo, plan, fby, cache, odir)
        plot = positions_plot(t, mo, odir / "positions.png")
        out(f"[7] Affichage : {plan.summary}")
        n_agree = sum(c.agree for c in plan.comparisons)   # (ne pas écraser le compteur n_ok)
        out(f"      comparaisons aux instants communs : {n_agree} concordantes, "
            f"{len(plan.comparisons) - n_agree} en désaccord "
            f"(attendu par hasard à 3σ : ~{0.011 * len(plan.comparisons):.0f})")
        for c in [c for c in plan.comparisons if not c.agree][:5]:
            out(f"      ⚠ {c.date} {c.group_a} vs {c.group_b} : écart {c.distance_px} px > seuil {c.tolerance_px} px")
        for sq in plan.sequences:
            out(f"      séquence {sq.kind:<10} {len(sq.frame_ids)} images, groupes {sq.groups[:4]}"
                f"{'...' if len(sq.groups) > 4 else ''} -> {sq.gif}")
        for it in plan.side_by_side[:5]:
            out(f"      comparaison côte à côte : {it.get('png')}")
        out(f"      graphique positions/temps (brutes) : {plot}")
    except Exception as exc:  # noqa: BLE001
        out(f"   ECHEC  {type(exc).__name__}: {exc}")
        n_fail += 1

# --- Bilan --------------------------------------------------------------------
out()
out("=" * 70)
out(f"BILAN : {n_ok} vérifications OK, {n_fail} échec(s)")
out("=" * 70)
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"Rapport écrit dans {REPORT}")
sys.exit(1 if n_fail else 0)
