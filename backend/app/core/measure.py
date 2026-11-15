"""Étape 6 du pipeline : MEASURE — trajectoire complète de la cible, tous groupes confondus.

1. Mesures : TOUTES les images gardées par Screen (union des groupes, chaque image une seule
   fois). Pour chacune : position de la cible sur la grille céleste commune (centroïde,
   pixels saturés exclus, ailes conservées) et incertitude.
2. Ponts : deux groupes sont reliés s'ils ont chacun une image au même passage. Dans chaque
   composante connexe, un décalage δ_g par groupe est estimé (le groupe de référence a δ = 0).
3. Ajustement global, exact (moindres carrés pondérés, non glouton) :
       x_i = x0 + μ·(t_i − t0) + δ_g(i)   (séparément en x et en y)
4. Points aberrants : rejet itératif du pire résidu au-delà de 3σ ; ils restent dans la
   sortie, marqués "écartés", avec leur écart.
5. Modèle : immobile vs droite (BIC) ; χ² réduit pour signaler une trajectoire non linéaire.
Les mesures brutes ne sont jamais modifiées : la droite est une estimation à côté.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from astropy.time import Time
from pydantic import BaseModel

from app.core.target import PIXSCALE_ARCSEC

SIGMA_FLOOR_PX = 0.15        # erreur minimale d'une position (PSF sous-échantillonnée, saturation)
CLIP_SIGMA = 3.0
MAX_CLIP_FRAC = 0.25
YEAR = 365.25


class PositionMeasure(BaseModel):
    frame_id: str
    date_utc: str
    mjd: float
    visit: Optional[int]
    group_id: Optional[str]          # groupe de rattachement (λ centrale la plus proche)
    detector: Optional[str]
    wavelength_um: Optional[float]
    x_px: float
    y_px: float
    sigma_px: float
    used: bool = True
    rejected_reason: Optional[str] = None
    residual_sigma: Optional[float] = None
    offset_corrected_x: Optional[float] = None   # position après correction du décalage
    offset_corrected_y: Optional[float] = None


class GroupDiagnostic(BaseModel):
    group_id: str
    n_points: int
    offset_px: tuple[float, float]
    offset_estimated: bool           # False : groupe de référence ou sans pont (δ = 0)
    chi2_red: Optional[float]
    flag: Optional[str] = None


class MotionResult(BaseModel):
    n_points: int
    n_used: int
    n_distinct_epochs: int
    coverage_start: Optional[str]
    coverage_end: Optional[str]
    span_days: float
    model: str                       # "immobile" | "droite"
    mu_x_px_yr: Optional[float] = None
    mu_y_px_yr: Optional[float] = None
    mu_px_yr: Optional[float] = None
    mu_ra_arcsec_yr: Optional[float] = None    # vers l'est (μα* = μα cos δ)
    mu_dec_arcsec_yr: Optional[float] = None   # vers le nord
    mu_arcsec_yr: Optional[float] = None
    mu_err_arcsec_yr: Optional[float] = None
    position_angle_deg: Optional[float] = None  # 0 = nord, 90 = est
    significance: Optional[float] = None
    chi2_red: Optional[float] = None
    errors_rescaled: bool = False
    status: str                      # moving | not_moving | insufficient_data | non_lineaire
    status_reason: str
    components: list[list[str]] = []
    groups: list[GroupDiagnostic] = []
    measures: list[PositionMeasure] = []
    t0_mjd: Optional[float] = None
    x0_px: Optional[float] = None
    y0_px: Optional[float] = None

    def predict(self, mjd: float, group_id: Optional[str] = None) -> tuple[float, float]:
        dt = (mjd - self.t0_mjd) / YEAR
        x = self.x0_px + (self.mu_x_px_yr or 0.0) * dt
        y = self.y0_px + (self.mu_y_px_yr or 0.0) * dt
        return x, y


# ----------------------------------------------------------------- ponts entre groupes
def bridge_components(measures: list[PositionMeasure]) -> list[list[str]]:
    """Composantes connexes du graphe « groupes reliés par un passage commun » (exact)."""
    groups = sorted({m.group_id for m in measures if m.group_id})
    parent = {g: g for g in groups}

    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    by_visit: dict[int, set[str]] = {}
    for m in measures:
        if m.group_id is not None and m.visit is not None:
            by_visit.setdefault(m.visit, set()).add(m.group_id)
    for gs in by_visit.values():
        gs = sorted(gs)
        for g in gs[1:]:
            parent[find(g)] = find(gs[0])
    comps: dict[str, list[str]] = {}
    for g in groups:
        comps.setdefault(find(g), []).append(g)
    return sorted(comps.values(), key=lambda c: (-len(c), c))


# ----------------------------------------------------------------- ajustement global
def _design(measures, free_groups, t0):
    """Matrice du modèle : [1, Δt, indicatrices des groupes à décalage libre]."""
    n, k = len(measures), 2 + len(free_groups)
    A = np.zeros((n, k))
    A[:, 0] = 1.0
    A[:, 1] = [(m.mjd - t0) / YEAR for m in measures]
    for j, g in enumerate(free_groups):
        A[:, 2 + j] = [1.0 if m.group_id == g else 0.0 for m in measures]
    return A


def _wls(A, b, sigma):
    w = 1.0 / sigma
    coef, *_ = np.linalg.lstsq(A * w[:, None], b * w, rcond=None)
    cov = np.linalg.pinv((A * w[:, None]).T @ (A * w[:, None]))
    return coef, cov


def fit_motion(measures: list[PositionMeasure], with_offsets: bool = True) -> MotionResult:
    ms = [m.model_copy() for m in measures]
    for m in ms:
        m.sigma_px = max(m.sigma_px, SIGMA_FLOOR_PX)
    comps = bridge_components(ms)
    # groupes à décalage libre : tous sauf la référence (le plus fourni) de chaque composante
    free = []
    if with_offsets:
        for comp in comps:
            if len(comp) < 2:
                continue
            counts = {g: sum(1 for m in ms if m.group_id == g) for g in comp}
            ref = max(comp, key=lambda g: (counts[g], g))
            free += [g for g in comp if g != ref]

    epochs_all = {m.visit if m.visit is not None else round(m.mjd) for m in ms}
    base = dict(n_points=len(ms), components=comps)
    if not ms:
        return MotionResult(**base, n_used=0, n_distinct_epochs=0, coverage_start=None,
                            coverage_end=None, span_days=0, model="immobile",
                            status="insufficient_data", status_reason="aucune mesure")

    t0 = float(np.mean([m.mjd for m in ms]))
    max_clip = int(MAX_CLIP_FRAC * len(ms))
    while True:
        used = [m for m in ms if m.used]
        fg = [g for g in free if any(m.group_id == g for m in used)]
        n_par = 2 + len(fg)
        if len(used) <= n_par or len({m.visit for m in used}) < 2:
            break
        A = _design(used, fg, t0)
        sig = np.array([m.sigma_px for m in used])
        cx, covx = _wls(A, np.array([m.x_px for m in used]), sig)
        cy, covy = _wls(A, np.array([m.y_px for m in used]), sig)
        rx, ry = A @ cx - [m.x_px for m in used], A @ cy - [m.y_px for m in used]
        chi2 = float(np.sum((rx ** 2 + ry ** 2) / sig ** 2))
        dof = 2 * (len(used) - n_par)
        chi2_red = chi2 / dof if dof > 0 else None
        scale = max(1.0, np.sqrt(chi2_red)) if chi2_red else 1.0
        norm_res = np.hypot(rx, ry) / (sig * scale)
        for m, r in zip(used, norm_res):
            m.residual_sigma = round(float(r), 2)
        worst = int(np.argmax(norm_res))
        n_rej = sum(1 for m in ms if not m.used)
        if norm_res[worst] > CLIP_SIGMA and n_rej < max_clip and len(used) - 1 > n_par:
            used[worst].used = False
            used[worst].rejected_reason = (f"écart de {norm_res[worst]:.1f}σ à la trajectoire "
                                           "commune (artefact ou étoile voisine ?)")
            continue
        break

    used = [m for m in ms if m.used]
    epochs = {m.visit if m.visit is not None else round(m.mjd) for m in used}
    mjds = [m.mjd for m in used] or [m.mjd for m in ms]
    span = float(max(mjds) - min(mjds))
    cov_start = Time(min(mjds), format="mjd").isot[:10]
    cov_end = Time(max(mjds), format="mjd").isot[:10]
    common = dict(**base, n_used=len(used), n_distinct_epochs=len(epochs),
                  coverage_start=cov_start, coverage_end=cov_end, span_days=round(span, 1),
                  measures=ms, t0_mjd=t0)
    if len(epochs) < 2 or 'cx' not in locals():
        return MotionResult(**common, model="immobile", status="insufficient_data",
                            status_reason=f"{len(epochs)} instant(s) distinct(s) : il en faut au moins 3")

    # incertitudes (agrandies si le χ² réduit dépasse 1 : erreurs sous-estimées)
    rescaled = bool(chi2_red and chi2_red > 1)
    covx, covy = covx * scale ** 2, covy * scale ** 2
    mux, muy = float(cx[1]), float(cy[1])
    smux, smuy = float(np.sqrt(covx[1, 1])), float(np.sqrt(covy[1, 1]))
    mu = float(np.hypot(mux, muy))
    smu = float(np.hypot(mux * smux, muy * smuy) / mu) if mu > 0 else float(np.hypot(smux, smuy))
    signif = mu / smu if smu > 0 else None

    # décalages par groupe et positions corrigées (pour l'affichage)
    offsets = {g: (float(cx[2 + j]), float(cy[2 + j])) for j, g in enumerate(fg)}
    for m in ms:
        dx, dy = offsets.get(m.group_id, (0.0, 0.0))
        m.offset_corrected_x, m.offset_corrected_y = round(m.x_px - dx, 3), round(m.y_px - dy, 3)
    diags = []
    for g in sorted({m.group_id for m in ms if m.group_id}):
        gm = [m for m in used if m.group_id == g]
        if gm:
            Ag = _design(gm, fg, t0)
            rx_g = Ag @ cx - [m.x_px for m in gm]
            ry_g = Ag @ cy - [m.y_px for m in gm]
            s_g = np.array([m.sigma_px for m in gm]) * scale
            c2 = float(np.sum((rx_g ** 2 + ry_g ** 2) / s_g ** 2)) / (2 * len(gm))
        else:
            c2 = None
        off = offsets.get(g, (0.0, 0.0))
        flag = None
        if c2 is not None and c2 > 4:
            flag = "désaccord avec la trajectoire commune"
        elif np.hypot(*off) > 1.0:
            flag = "décalage > 1 px (étoile voisine à cette longueur d'onde ?)"
        diags.append(GroupDiagnostic(group_id=g, n_points=len(gm),
                                     offset_px=(round(off[0], 3), round(off[1], 3)),
                                     offset_estimated=g in offsets,
                                     chi2_red=None if c2 is None else round(c2, 2), flag=flag))

    # conversion en secondes d'arc (grille : x vers l'ouest, y vers le nord)
    mu_ra, mu_dec = -mux * PIXSCALE_ARCSEC, muy * PIXSCALE_ARCSEC
    pa = (np.degrees(np.arctan2(mu_ra, mu_dec)) + 360) % 360
    # modèle immobile vs droite (BIC, 2 paramètres de mouvement en plus)
    w = 1.0 / (np.array([m.sigma_px for m in used]) * scale)
    xs, ys = np.array([m.x_px for m in used]), np.array([m.y_px for m in used])
    chi2_static = float(np.sum(((xs - np.average(xs, weights=w ** 2)) * w) ** 2 +
                               ((ys - np.average(ys, weights=w ** 2)) * w) ** 2))
    chi2_line = float(np.sum(((A @ cx - xs) * w) ** 2 + ((A @ cy - ys) * w) ** 2))
    bic_gain = (chi2_static - chi2_line) - 2 * np.log(2 * len(used))
    model = "droite" if bic_gain > 0 else "immobile"

    if len(epochs) < 3:
        status, reason = "insufficient_data", f"{len(epochs)} instants distincts : il en faut au moins 3"
    elif chi2_red is not None and chi2_red > 9:
        status, reason = "non_lineaire", (f"χ² réduit = {chi2_red:.1f} : une droite n'explique pas "
                                          "les positions (parallaxe, compagnon, objet du système solaire ?)")
    elif signif is not None and signif >= 5 and model == "droite":
        status, reason = "moving", f"mouvement détecté à {signif:.0f}σ sur {len(epochs)} instants"
    elif signif is not None and signif < 3:
        status, reason = "not_moving", f"mouvement compatible avec zéro ({signif:.1f}σ)"
    else:
        status, reason = "insufficient_data", f"mouvement incertain ({signif:.1f}σ, entre 3 et 5σ)"

    return MotionResult(
        **common, model=model,
        mu_x_px_yr=round(mux, 4), mu_y_px_yr=round(muy, 4), mu_px_yr=round(mu, 4),
        mu_ra_arcsec_yr=round(mu_ra, 3), mu_dec_arcsec_yr=round(mu_dec, 3),
        mu_arcsec_yr=round(mu * PIXSCALE_ARCSEC, 3), mu_err_arcsec_yr=round(smu * PIXSCALE_ARCSEC, 3),
        position_angle_deg=round(float(pa), 1),
        significance=None if signif is None else round(signif, 1),
        chi2_red=None if chi2_red is None else round(chi2_red, 2), errors_rescaled=rescaled,
        status=status, status_reason=reason, groups=diags,
        x0_px=round(float(cx[0]), 4), y0_px=round(float(cy[0]), 4),
    )


# ----------------------------------------------------------------- mesures sur les images
def measure_positions(target, frames, grouping, visits) -> tuple[list[PositionMeasure], dict]:
    """Position de la cible sur la grille commune pour TOUTES les images gardées (sans doublon)."""
    from app.core.align import annulus_background, centroid, make_grid, reproject_frame
    from app.core.group import visit_of

    n = target.size_px
    grid = make_grid(target.ra_deg, target.dec_deg, n)
    # rattachement : groupe dont la λ centrale est la plus proche (règle fixe, sans ordre)
    member_of: dict[str, list] = {}
    for g in grouping.groups:
        for gf in g.frames:
            member_of.setdefault(gf.frame_id, []).append(g)
    out, cache = [], {}
    seen = set()
    for f in frames:
        if not f.keep or f.frame_id in seen or f.path is None or f.date_utc is None:
            continue
        seen.add(f.frame_id)
        rp = reproject_frame(Path(f.path), grid, (n, n))
        cache[f.frame_id] = rp
        from app.core.screen import position_at
        mjd = float(Time(f.date_utc.rstrip("Z"), format="isot").mjd)
        ex, ey = (float(v) for v in grid.world_to_pixel_values(*position_at(target, mjd)))
        c = centroid(rp["image"], ex, ey, bkg=annulus_background(rp["image"], ex, ey))
        if c is None:
            continue
        gs = member_of.get(f.frame_id, [])
        g = min(gs, key=lambda gg: abs(gg.wavelength_um - (f.wavelength_um or 0))) if gs else None
        fwhm_px = 1.2
        sig = fwhm_px / f.snr if f.snr else 1.0
        out.append(PositionMeasure(
            frame_id=f.frame_id, date_utc=f.date_utc, mjd=mjd, visit=visit_of(f.date_utc, visits),
            group_id=g.id if g else None, detector=f.detector, wavelength_um=f.wavelength_um,
            x_px=round(c[0], 4), y_px=round(c[1], 4), sigma_px=round(sig, 4)))
    return out, cache


# ----------------------------------------------------------------- règle d'affichage
# Principe : ne rien cacher. Aux instants communs à deux groupes :
#   - positions identiques (à 3σ près)  -> une seule animation, image la plus visible ;
#   - décalage                          -> les deux groupes sont montrés séparément
#                                          (groupe 1 puis groupe 2), positions BRUTES,
#                                          et les deux images côte à côte à l'instant commun.
# Groupes sans instant commun : enchaînés, avec la mention « raccord non vérifiable ».
AGREE_K = 3.0
MAKE_GIF = False            # GIF seulement en secours si le MP4 échoue (lent et ~15x plus lourd)
MAX_SIDE_BY_SIDE = 12       # nombre max d'images côte à côte générées
QUALITY_RANK = {"nette": 0, "saturee": 1, "decalee": 2, "faible": 3}


def pseudo_group(m: PositionMeasure) -> str:
    return m.group_id or f"isolee_{m.frame_id[:6]}"


class GroupComparison(BaseModel):
    group_a: str
    group_b: str
    visit: int
    date: str
    dx_px: float
    dy_px: float
    distance_px: float
    tolerance_px: float
    agree: bool
    frame_a: str
    frame_b: str


class DisplaySequence(BaseModel):
    kind: str                    # "principale" | "separee"
    video: Optional["VideoAssets"] = None   # MP4 + frise temporelle + sous-titres + GIF
    groups: list[str]
    frame_ids: list[str]         # une image par passage, ordre chronologique
    notes: dict[str, str] = {}   # frame_id -> message affiché sous l'image
    segments: dict[str, list] = {}   # frame_id -> [indice du bloc, nom du bloc]
    gif: Optional[str] = None
    frames_png: list[str] = []
    title: str = ""              # vue par groupe : libellé lisible (détecteur, λ, passages…)
    info: dict = {}              # vue par groupe : détecteur, λ, dates, mouvement de ce groupe seul


class DisplayPlan(BaseModel):
    comparisons: list[GroupComparison]
    conflicted_groups: list[str]
    sequences: list[DisplaySequence]
    side_by_side: list[dict] = []   # images comparées aux instants de désaccord
    summary: str
    # une vidéo PAR groupe (même détecteur, λ à ±3 %) : l'utilisateur choisit le groupe à
    # regarder ; la vue par défaut reste « tous les groupes » (sequences[0])
    group_sequences: list["DisplaySequence"] = []
    alert: Optional[dict] = None    # message court pour l'utilisateur : {level, title, message}


def _mean_pos(ms: list[PositionMeasure], scale: float = 1.0):
    w = np.array([1 / (max(m.sigma_px, SIGMA_FLOOR_PX) * scale) ** 2 for m in ms])
    x = float(np.sum(w * [m.x_px for m in ms]) / w.sum())
    y = float(np.sum(w * [m.y_px for m in ms]) / w.sum())
    return x, y, float(1 / np.sqrt(w.sum()))


def compare_groups(measures: list[PositionMeasure], frames_by_id: dict,
                   sigma_scale: float = 1.0) -> list[GroupComparison]:
    """Compare les positions BRUTES de chaque paire de groupes à chaque passage commun.
    sigma_scale : facteur qui calibre les incertitudes sur les données réelles
    (√χ²_réduit de l'ajustement global, si > 1). Sans lui, les incertitudes théoriques,
    trop optimistes, font apparaître de faux désaccords."""
    by_vg: dict[tuple, list[PositionMeasure]] = {}
    for m in measures:
        if m.visit is not None:
            by_vg.setdefault((m.visit, pseudo_group(m)), []).append(m)
    out = []
    for v in sorted({k[0] for k in by_vg}):
        gs = sorted(g for (vv, g) in by_vg if vv == v)
        for i, a in enumerate(gs):
            for b in gs[i + 1:]:
                ma, mb = by_vg[(v, a)], by_vg[(v, b)]
                xa, ya, sa = _mean_pos(ma, sigma_scale)
                xb, yb, sb = _mean_pos(mb, sigma_scale)
                d = float(np.hypot(xb - xa, yb - ya))
                tol = AGREE_K * float(np.hypot(sa, sb))
                best = lambda ms: min(ms, key=lambda m: (QUALITY_RANK.get(
                    frames_by_id[m.frame_id].status, 9), -(frames_by_id[m.frame_id].snr or 0)))
                out.append(GroupComparison(
                    group_a=a, group_b=b, visit=v, date=ma[0].date_utc[:10],
                    dx_px=round(xb - xa, 3), dy_px=round(yb - ya, 3), distance_px=round(d, 3),
                    tolerance_px=round(tol, 3), agree=d <= tol,
                    frame_a=best(ma).frame_id, frame_b=best(mb).frame_id))
    return out


def calibrated_sigma_scale(motion: "MotionResult") -> float:
    """Facteur d'échelle des incertitudes, mesuré sur les données (≥ 1).

    IMPORTANT : on le mesure sur la dispersion À L'INTÉRIEUR de chaque groupe, en laissant à
    chaque groupe (y compris les images isolées) son propre décalage libre. Ainsi un écart
    ENTRE groupes ne peut pas gonfler la tolérance et se cacher lui-même (raisonnement
    circulaire constaté avec le χ² global)."""
    ms = []
    for m in motion.measures:
        c = m.model_copy()
        c.group_id = pseudo_group(m)
        c.used = True
        c.rejected_reason = None
        ms.append(c)
    if len(ms) < 4:
        return 1.0
    r = fit_motion(ms, with_offsets=True)
    if not r.chi2_red:
        return 1.0
    return float(min(max(1.0, np.sqrt(r.chi2_red)), 5.0))


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
        "octobre", "novembre", "décembre"]


def fr_date(iso: Optional[str]) -> str:
    """'2026-03-11...' -> '11 mars 2026'."""
    if not iso or len(iso) < 10:
        return iso or "?"
    y, mth, d = iso[:4], int(iso[5:7]), int(iso[8:10])
    return f"{'1er' if d == 1 else d} {MOIS[mth - 1]} {y}"


def fr_month(iso: Optional[str]) -> str:
    """'2026-03-11...' -> 'mars 2026' (un passage s'étale sur plusieurs jours)."""
    if not iso or len(iso) < 7:
        return iso or "?"
    return f"{MOIS[int(iso[5:7]) - 1]} {iso[:4]}"


def fr_num(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def group_numbers(measures: list[PositionMeasure]) -> dict[str, str]:
    """Numéro affiché de chaque groupe d'au moins 2 images : G1, G2… (« D » est réservé aux
    détecteurs). Même ordre que les vues par groupe : plus de passages, puis plus longue durée."""
    by_g: dict[str, list[PositionMeasure]] = {}
    for m in measures:
        by_g.setdefault(pseudo_group(m), []).append(m)
    ranked = []
    for g, ms in by_g.items():
        if g.startswith("isolee_") or len(ms) < 2:
            continue
        visits = {m.visit if m.visit is not None else round(m.mjd) for m in ms}
        span = max(m.mjd for m in ms) - min(m.mjd for m in ms)
        ranked.append((-len(visits), -span, g))
    return {g: f"G{k}" for k, (_, _, g) in enumerate(sorted(ranked), 1)}


def group_labels(measures: list[PositionMeasure]) -> dict[str, str]:
    """Nom lisible de chaque groupe : « le groupe G2 (détecteur D2, 1,64 µm) » ;
    image isolée : « l'image seule (détecteur D3, 1,78 µm) du 25 mars 2026 »."""
    nums = group_numbers(measures)
    by_g: dict[str, list[PositionMeasure]] = {}
    for m in measures:
        by_g.setdefault(pseudo_group(m), []).append(m)
    out = {}
    for g, ms in by_g.items():
        det = ms[0].detector or "?"
        wls = [m.wavelength_um for m in ms if m.wavelength_um]
        wl = f", {fr_num(float(np.median(wls)))} µm" if wls else ""
        if g in nums:
            out[g] = f"le groupe {nums[g]} (détecteur {det}{wl})"
        else:
            out[g] = f"l'image seule (détecteur {det}{wl}) du {fr_date(ms[0].date_utc)}"
    return out


def conflict_sigma(n_comparisons: int, false_alarm: float = 0.05) -> float:
    """Seuil (en σ) pour qu'au total moins de 5 % de chances d'un faux désaccord."""
    if n_comparisons <= 0:
        return 3.0
    return max(3.0, float(np.sqrt(2 * np.log(n_comparisons / false_alarm))))


def explain_conflicts(comps: list[GroupComparison],
                      labels: Optional[dict[str, str]] = None) -> tuple[dict[str, str], dict]:
    """Remarques sur les désaccords (n'influencent PAS l'affichage : tout groupe impliqué
    dans un dépassement de 3σ reste montré à part, règle d'origine). Elles disent à
    l'utilisateur de quel type de désaccord il s'agit :
      - groupe en désaccord avec la plupart des autres -> image probablement aberrante ;
      - groupe en désaccord seulement avec un tel groupe -> il concorde avec tous les autres ;
      - écart au-delà du seuil corrigé du nombre de comparaisons -> décalage net ;
      - sinon -> compatible avec le hasard (≈ 1 % des comparaisons dépassent 3σ par hasard)."""
    n = len(comps)
    k = conflict_sigma(n)
    expected = n * float(np.exp(-4.5))           # P(écart > 3σ) pour un écart 2D gaussien
    bad = [c for c in comps if not c.agree]
    partners: dict[str, set] = {}
    bad_partners: dict[str, set] = {}
    for c in comps:
        partners.setdefault(c.group_a, set()).add(c.group_b)
        partners.setdefault(c.group_b, set()).add(c.group_a)
    for c in bad:
        bad_partners.setdefault(c.group_a, set()).add(c.group_b)
        bad_partners.setdefault(c.group_b, set()).add(c.group_a)
    culprits: set[str] = set()
    while True:
        best = None
        for g, ps in partners.items():
            if g in culprits:
                continue
            ps = ps - culprits
            bads = bad_partners.get(g, set()) - culprits
            if len(ps) >= 2 and 2 * len(bads) > len(ps):
                score = (len(bads) / len(ps), len(bads), g)
                if best is None or score > best:
                    best = score
        if best is None:
            break
        culprits.add(best[2])

    def other(c, g):
        return c.group_b if c.group_a == g else c.group_a

    def sig(c):
        return 3.0 * c.distance_px / c.tolerance_px if c.tolerance_px else float("inf")

    lab = (lambda g: (labels or {}).get(g, g))
    px = PIXSCALE_ARCSEC
    # notes[g] = (gravité, explication en langage simple) ; gravité : "warn" | "info"
    notes: dict[str, tuple[str, str]] = {}
    for g in sorted({x for c in bad for x in (c.group_a, c.group_b)}):
        mine = sorted((c for c in bad if g in (c.group_a, c.group_b)), key=sig, reverse=True)
        w = mine[0]
        o, date, dist = other(w, g), fr_month(w.date), w.distance_px * px
        n_part = len(partners.get(g, set()))
        moi = "cette image" if lab(g).startswith("l'image") else "ce groupe"
        Moi = moi[0].upper() + moi[1:]
        le = "la" if moi == "cette image" else "le"
        if g in culprits:
            qui = (f"les {n_part} autres groupes" if len(bad_partners.get(g, set())) == n_part
                   else f"{len(bad_partners.get(g, set()))} des {n_part} autres groupes")
            notes[g] = ("warn",
                        f"Au même passage, {moi} place l'étoile à {dist:.0f}″ de l'endroit où la voient "
                        f"{qui}. Elle est donc probablement défectueuse (artefact, rayon cosmique ou "
                        "étoile voisine). On la montre quand même, à part, pour ne rien cacher.")
        elif all(other(c, g) in culprits for c in mine):
            notes[g] = ("info",
                        f"{Moi} est d'accord avec tous les autres groupes. {'Elle' if le == 'la' else 'Il'} "
                        f"est montré{'e' if le == 'la' else ''} à part seulement parce "
                        f"qu'{'elle' if le == 'la' else 'il'} ne concorde pas avec {lab(o)}, une image probablement défectueuse "
                        f"({dist:.0f}″ d'écart lors du passage de {date}).")
        elif sig(w) <= k:
            notes[g] = ("info",
                        f"Lors du passage de {date}, {moi} et {lab(o)} placent l'étoile à {dist:.0f}″ l'un "
                        f"de l'autre (environ {fr_num(w.distance_px, 1)} pixel). Pour ne rien cacher, on {le} "
                        "montre à "
                        f"part. Mais cet écart est petit : sur {n} comparaisons, environ "
                        f"{expected:.0f} écarts comme celui-ci arrivent par hasard. "
                        "La trajectoire reste fiable.")
        else:
            notes[g] = ("warn",
                        f"Lors du passage de {date}, {moi} et {lab(o)} placent l'étoile à {dist:.0f}″ l'un "
                        "de l'autre : "
                        "c'est un écart net, trop grand pour être dû au hasard. Comparez les deux groupes "
                        "avec « Groupe affiché » pour juger (artefact, étoile voisine ou effet de la "
                        "longueur d'onde ?).")
    clear = sorted((c for c in bad if sig(c) > k), key=sig, reverse=True)
    outlier_details = []
    for g in sorted(culprits):
        cs = [c for c in clear if g in (c.group_a, c.group_b)] or \
             [c for c in bad if g in (c.group_a, c.group_b)]
        if cs:
            c = max(cs, key=sig)
            outlier_details.append(dict(group=g, date=c.date, distance_px=c.distance_px,
                                        n_bad=len(bad_partners.get(g, set())),
                                        n_partners=len(partners.get(g, set()))))
    clear_pairs = [dict(group_a=c.group_a, group_b=c.group_b, date=c.date, distance_px=c.distance_px,
                        sigma=round(sig(c), 1))
                   for c in clear if not ({c.group_a, c.group_b} & culprits)]
    stats = dict(n_comparisons=n, n_over_3sigma=len(bad), expected_by_chance=round(expected, 1),
                 corrected_sigma=round(k, 2), n_clear=len(clear), likely_outliers=sorted(culprits),
                 outlier_details=outlier_details, clear_pairs=clear_pairs)
    return notes, stats


def user_alert(conflicted: list[str], stats: dict, n_comparisons: int,
               labels: Optional[dict[str, str]] = None) -> Optional[dict]:
    """Message court et clair pour l'utilisateur (zone à droite de la vidéo).
    level : ok | info | warn."""
    px = PIXSCALE_ARCSEC
    if n_comparisons == 0:
        return dict(level="info", title="Groupes non comparables",
                    message="Aucun passage n'est commun à deux groupes : on ne peut pas vérifier "
                            "qu'ils donnent la même position. Regardez chaque groupe séparément "
                            "avec « Groupe affiché ».")
    if not conflicted:
        return dict(level="ok", title="Groupes concordants",
                    message="Tous les groupes placent l'objet au même endroit aux mêmes instants : "
                            "la trajectoire affichée est fiable.")
    if stats["n_clear"] == 0:
        return dict(level="info", title="Petits écarts dus au hasard",
                    message=f"Sur {n_comparisons} comparaisons entre groupes, {stats['n_over_3sigma']} "
                            "montrent un petit écart, autant qu'on en attend par hasard "
                            f"(environ {stats['expected_by_chance']:.0f}). Ces groupes sont rejoués à part "
                            "à la fin de la vidéo pour ne rien cacher, mais la trajectoire reste fiable.")
    parts, title = [], "Désaccord entre groupes"
    if stats["outlier_details"]:
        title = ("Image probablement aberrante" if not stats["clear_pairs"]
                 else "Désaccord entre groupes")
        for o in stats["outlier_details"][:2]:
            who = (f"les {o['n_partners']} autres groupes" if o["n_bad"] == o["n_partners"]
                   else f"{o['n_bad']} des {o['n_partners']} autres groupes")
            name = (labels or {}).get(o["group"], f"l'image {o['group']}")
            name = name[0].upper() + name[1:]
            parts.append(f"{name} place l'étoile à {o['distance_px'] * px:.0f}″ de l'endroit où la "
                         f"voient {who} au même passage : elle est sans doute défectueuse. "
                         "Elle est rejouée à part à la fin de la vidéo.")
    if stats["clear_pairs"]:
        c = stats["clear_pairs"][0]
        more = (f" ({len(stats['clear_pairs'])} cas)" if len(stats["clear_pairs"]) > 1 else "")
        la, lb = ((labels or {}).get(c["group_a"], c["group_a"]),
                  (labels or {}).get(c["group_b"], c["group_b"]))
        parts.append(f"Lors du passage de {fr_month(c['date'])}, {la} et {lb} placent l'étoile à "
                     f"{c['distance_px'] * px:.0f}″ l'un de l'autre{more}. Comparez ces groupes avec "
                     "« Groupe affiché » pour juger (artefact, étoile voisine ou effet de longueur d'onde).")
    return dict(level="warn", title=title, message=" ".join(parts))


def plan_display(measures: list[PositionMeasure], frames_by_id: dict,
                 sigma_scale: float = 1.0) -> DisplayPlan:
    """UNE SEULE vidéo, faite de blocs joués l'un après l'autre (jamais d'alternance) :
      - bloc 1 : les groupes concordants, une image par passage (la plus visible),
                 dans l'ordre chronologique ;
      - puis, s'il y a des désaccords : un bloc PAR groupe en désaccord, chacun en entier et
        dans l'ordre chronologique, les blocs étant rangés par date de début.
    Le passage d'un bloc au suivant est signalé dans la frise (changement de groupe)."""
    comps = compare_groups(measures, frames_by_id, sigma_scale)
    conflicted = sorted({g for c in comps if not c.agree for g in (c.group_a, c.group_b)})
    labels = group_labels(measures)
    explain, stats = explain_conflicts(comps, labels)
    groups_all = sorted({pseudo_group(m) for m in measures})
    agree_edges = {frozenset((c.group_a, c.group_b)) for c in comps if c.agree}

    def rank(m):
        f = frames_by_id[m.frame_id]
        return (QUALITY_RANK.get(f.status, 9), -(f.snr or 0))

    def block(groups: list[str]) -> list[PositionMeasure]:
        per_visit: dict = {}
        for m in measures:
            if pseudo_group(m) not in groups:
                continue
            v = m.visit if m.visit is not None else round(m.mjd)
            if v not in per_visit or rank(m) < rank(per_visit[v]):
                per_visit[v] = m                       # image la plus visible du passage
        return sorted(per_visit.values(), key=lambda m: m.mjd)

    blocks: list[tuple[str, list[PositionMeasure]]] = []
    main_groups = [g for g in groups_all if g not in conflicted]
    if main_groups:
        blocks.append(("groupes concordants", block(main_groups)))
    first = {g: min(m.mjd for m in measures if pseudo_group(m) == g) for g in conflicted}
    for g in sorted(conflicted, key=lambda g: (first[g], g)):
        blocks.append((f"groupe {g}", block([g])))

    notes: dict[str, str] = {}
    frame_ids: list[str] = []
    segments: dict[str, tuple[int, str]] = {}
    n_sep = sum(1 for label, _ in blocks if label.startswith("groupe "))
    k_sep = 0
    for bi, (label, ms) in enumerate(blocks):
        for j, m in enumerate(ms):
            frame_ids.append(m.frame_id)
            segments[m.frame_id] = (bi, label)
            if j:
                continue
            if label.startswith("groupe "):
                k_sep += 1
                g = pseudo_group(m)
                level, why = explain.get(g, ("warn", ""))
                if bi == 0:
                    where = ("Les groupes ne sont pas tous d'accord : la vidéo les montre un par un, "
                             "chacun dans l'ordre des dates.")
                elif blocks[0][0] == "groupes concordants":
                    where = ("La date revient en arrière : après la trajectoire commune, on rejoue "
                             "ce groupe seul.")
                else:
                    where = "La date revient en arrière : on passe au groupe suivant, rejoué seul."
                notes[m.frame_id] = ("⚠ " if level == "warn" else "ℹ ") + (
                    f"Séquence à part {k_sep}/{n_sep} : {labels.get(g, g)}.\n{where}\n"
                    f"Pourquoi ? {why}")
            elif n_sep:
                notes[m.frame_id] = (
                    "ℹ La vidéo montre d'abord tous les groupes qui sont d'accord, dans l'ordre des "
                    f"dates. Ensuite, {n_sep} groupe(s) qui ne sont pas d'accord avec les autres sont "
                    "rejoués un par un : la date reviendra alors en arrière.")
        # à l'intérieur d'un bloc : passages concordants et raccords non vérifiables
        for prev, cur in zip(ms, ms[1:]):
            ga, gb = pseudo_group(prev), pseudo_group(cur)
            if ga != gb and frozenset((ga, gb)) not in agree_edges and cur.frame_id not in notes:
                notes[cur.frame_id] = (f"Passage de {labels.get(ga, ga)} à {labels.get(gb, gb)} : "
                                       "aucune date commune ne permet de vérifier qu'ils voient "
                                       "l'étoile au même endroit.")
        for m in ms:
            ok = [c for c in comps if c.agree and c.visit == m.visit
                  and pseudo_group(m) in (c.group_a, c.group_b)]
            if ok and m.frame_id not in notes:
                c = ok[0]
                notes[m.frame_id] = (f"À cette date, {labels.get(c.group_a, c.group_a)} et "
                                     f"{labels.get(c.group_b, c.group_b)} voient l'étoile au même "
                                     "endroit : on montre l'image la plus nette.")

    seq = DisplaySequence(kind="unique", groups=groups_all, frame_ids=frame_ids, notes=notes,
                          segments={fid: list(v) for fid, v in segments.items()})
    sbs = [dict(date=c.date, group_a=c.group_a, group_b=c.group_b, frame_a=c.frame_a,
                frame_b=c.frame_b, distance_px=c.distance_px, tolerance_px=c.tolerance_px)
           for c in comps if not c.agree]
    if not conflicted:
        detail = "tous les groupes concordent : une image par passage, ordre chronologique"
    else:
        detail = (f"{stats['n_over_3sigma']} écart(s) > 3σ sur {stats['n_comparisons']} comparaisons "
                  f"(≈ {stats['expected_by_chance']} attendu(s) par hasard ; "
                  f"{stats['n_clear']} au-delà du seuil corrigé {stats['corrected_sigma']}σ) : "
                  f"vidéo en {len(blocks)} blocs joués l'un après l'autre (groupes concordants, "
                  f"puis chaque groupe en désaccord en entier)")
        if stats["likely_outliers"]:
            detail += f" ; probablement aberrant(s) : {', '.join(stats['likely_outliers'])}"
    summary = (f"incertitudes calibrées x{sigma_scale:.2f} ; " if sigma_scale > 1 else "") + detail
    return DisplayPlan(comparisons=comps, conflicted_groups=conflicted,
                       sequences=[seq] if frame_ids else [], side_by_side=sbs, summary=summary,
                       alert=user_alert(conflicted, stats, len(comps), labels))


# ----------------------------------------------------------------- rendu
def clean_crop(shown: list[np.ndarray]) -> int:
    """Marge (en pixels vidéo) à retirer de chaque bord pour la vidéo propre.

    La grille est orientée nord en haut, mais les détecteurs de SPHEREx sont tournés :
    la découpe IRSA apparaît comme un carré incliné, avec des coins vides (NaN).
    On garde le plus grand carré centré (sur la cible) valide dans TOUTES les images.
    Un carré tourné de n'importe quel angle contient toujours le carré centré de côté
    n/sqrt(2) : on ne rogne donc jamais plus que cela (le reste éventuel reste noir).
    """
    N = shown[0].shape[0]
    valid = np.all([np.isfinite(img) for img in shown], axis=0)
    c_max = int(round(N / 2 * (1 - 1 / np.sqrt(2))))
    for c0 in range(0, c_max + 1):
        if valid[c0:N - c0, c0:N - c0].all():
            return c0
    return c_max


def _render_sequence(target, seq: DisplaySequence, motion: MotionResult, frames_by_id: dict,
                     cache: dict, out_dir: Path, tag: str, light: bool = False) -> None:
    """light=True : seulement la vidéo propre (pas d'images PNG annotées ni de vidéo à
    repères) — utilisé pour les vues par groupe, pour ne pas multiplier le temps de calcul."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patches  # noqa: F401
    import matplotlib.pyplot as plt
    from astropy.visualization import AsinhStretch, ImageNormalize, ManualInterval
    from PIL import Image
    from app.core.align import (GIF_CROSSFADE_STEPS, GIF_FADE_MS, GIF_HOLD_MS, display_image,
                                find_field_stars)
    from app.core.screen import SATURATION_BITS

    meas = {m.frame_id: m for m in motion.measures}
    chosen = seq.frame_ids
    imgs = [cache[fid]["image"].copy() for fid in chosen]
    # luminosité harmonisée par les étoiles fixes (affichage seulement)
    ref, m0 = imgs[0], meas[chosen[0]]
    stars = find_field_stars(ref, (cache[chosen[0]]["flags"] & SATURATION_BITS) != 0,
                             (m0.x_px, m0.y_px), n_max=20, min_snr=10)

    def star_flux(img, x, y):
        yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
        r = np.hypot(xx - x, yy - y)
        ap, ann = r <= 2.0, (r >= 3.5) & (r <= 5.5)
        if not np.isfinite(img[ap]).all() or np.isfinite(img[ann]).sum() < 5:
            return None
        return float(np.sum(img[ap] - np.nanmedian(img[ann])))

    for i, img in enumerate(imgs):
        ratios = [a / b for x, y in stars
                  for a, b in [(star_flux(ref, x, y), star_flux(img, x, y))] if a and b and a > 0 and b > 0]
        if len(ratios) >= 3:
            imgs[i] = img * float(np.median(ratios))
    shown = [display_image(img) for img in imgs]
    n = imgs[0].shape[0]
    extent = (-0.5, n - 0.5, -0.5, n - 0.5)
    vals = np.concatenate([d[np.isfinite(d)] for d in shown])
    lo, hi = np.percentile(vals, [5, 98.5])
    norm = ImageNormalize(interval=ManualInterval(lo, hi), stretch=AsinhStretch(0.04))
    cmap = plt.get_cmap("magma").copy()
    cmap.set_bad("#20242c")

    groups = sorted({pseudo_group(m) for m in motion.measures})
    palette = ["#00e5ff", "#7CFC00", "#ffd400", "#ff6ec7", "#ff8c00", "#9b8cff", "#ffffff"]
    gcol = {g: palette[i % len(palette)] for i, g in enumerate(groups)}
    seq_meas = [m for m in motion.measures if pseudo_group(m) in seq.groups]
    t_all = [m.mjd for m in motion.measures if m.used]
    line = ([motion.predict(t) for t in np.linspace(min(t_all), max(t_all), 50)]
            if motion.x0_px is not None and t_all else [])
    cx_, cy_ = line[len(line) // 2] if line else (n / 2, n / 2)
    zh = max(3.0, (np.hypot(line[-1][0] - line[0][0], line[-1][1] - line[0][1]) if line else 0) + 1.5)

    def overlay(ax, upto, ms_pt):
        if line:
            ax.plot([p[0] for p in line], [p[1] for p in line], "-", color="white", lw=0.9, alpha=0.6)
        for mm in seq_meas:                       # positions BRUTES, jamais corrigées
            if mm.mjd > upto + 1e-6:
                continue
            ax.plot(mm.x_px, mm.y_px, "o", ms=ms_pt,
                    **({"color": gcol[pseudo_group(mm)]} if mm.used else
                       {"mfc": "none", "mec": "#999999"}))

    rgb, prev_wl, pngs = [], None, []
    for k, fid in enumerate([] if light else chosen):
        m, f = meas[fid], frames_by_id[fid]
        fig, ax = plt.subplots(figsize=(5.4, 5.4))
        ax.imshow(shown[k], origin="lower", cmap=cmap, norm=norm, extent=extent, interpolation="bilinear")
        overlay(ax, m.mjd, 2.5)
        ax.plot(m.x_px, m.y_px, "o", ms=12, mfc="none", mec="#00e5ff", mew=1.2)
        ax.add_patch(matplotlib.patches.Rectangle((cx_ - zh, cy_ - zh), 2 * zh, 2 * zh, fill=False,
                                                  ec="white", lw=0.8, ls="--"))
        ax.set_xlim(extent[0], extent[1]), ax.set_ylim(extent[2], extent[3])
        ax.set_xticks([]), ax.set_yticks([])
        ins = ax.inset_axes([0.60, 0.60, 0.38, 0.38])
        ins.imshow(shown[k], origin="lower", cmap=cmap, extent=extent, interpolation="bilinear",
                   norm=ImageNormalize(interval=ManualInterval(np.nanpercentile(shown[k], 60),
                                                               np.nanpercentile(shown[k], 99.9)),
                                       stretch=AsinhStretch(0.3)))
        overlay(ins, m.mjd, 4)
        ins.plot(m.x_px, m.y_px, "o", ms=16, mfc="none", mec="#00e5ff", mew=1.2)
        ins.set_xlim(cx_ - zh, cx_ + zh), ins.set_ylim(cy_ - zh, cy_ + zh)
        ins.set_xticks([]), ins.set_yticks([])
        for sp in ins.spines.values():
            sp.set_color("white")
        wl = f.wavelength_um or 0
        lines = []
        if prev_wl and abs(wl - prev_wl) / prev_wl > 0.03:
            lines.append(f"λ change ({prev_wl:.2f} → {wl:.2f} µm) : l'éclat peut changer, pas la position")
        prev_wl = wl
        if fid in seq.notes:
            lines.append(seq.notes[fid])
        # aucun texte dans l'image : date, λ, notes... sont fournis à part (frise temporelle)
        fig.subplots_adjust(0, 0, 1, 1)
        fig.canvas.draw()
        png = out_dir / f"{tag}_{k:02d}.png"
        fig.savefig(png, dpi=120)
        pngs.append(str(png))
        rgb.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(float))
        plt.close(fig)
    if light:
        pngs = [None] * len(chosen)
    seq.frames_png = [p for p in pngs if p]
    # ---- vidéo MP4 + frise temporelle synchronisable (+ sous-titres, GIF de secours)
    from app.core.video import build_video
    entries, prev, prev_seg, prev_label = [], None, None, None
    conflicted_set = {seq.segments[f][1].replace("groupe ", "", 1) for f in seq.segments
                      if seq.segments[f][1].startswith("groupe ")}
    for fid, png in zip(chosen, pngs):
        m, f = meas[fid], frames_by_id[fid]
        wl = f.wavelength_um
        change = (f"λ change ({prev:.2f} → {wl:.2f} µm) : l'éclat peut changer, pas la position"
                  if prev and wl and abs(wl - prev) / prev > 0.03 else None)
        prev = wl or prev
        pred = motion.predict(m.mjd) if motion.x0_px is not None else None
        entries.append(dict(
            frame_id=fid, date_utc=m.date_utc, detector=f.detector,
            wavelength_um=None if wl is None else round(wl, 4), group=pseudo_group(m),
            status=f.status, snr=f.snr, target_measured_px=(m.x_px, m.y_px),
            target_predicted_px=None if pred is None else (round(pred[0], 3), round(pred[1], 3)),
            used_in_fit=m.used, note=seq.notes.get(fid), wavelength_change=change, image_url=png,
            group_changed=prev_seg is not None and seq.segments.get(fid, [0])[0] != prev_seg,
            previous_group=prev_label if (prev_seg is not None and
                                          seq.segments.get(fid, [0])[0] != prev_seg) else None,
            disagreement=pseudo_group(m) in conflicted_set,
            segment_index=seq.segments.get(fid, [0, ""])[0],
            segment_label=seq.segments.get(fid, [0, ""])[1]))
        prev_seg, prev_label = seq.segments.get(fid, [0, ""])
    if shown:
        # vidéo PROPRE : uniquement l'image du ciel (même contraste pour toutes les dates)
        up = shown[0].shape[0] / n
        c0 = clean_crop(shown)                           # pas de coins vides (découpe tournée)
        N = shown[0].shape[0]
        clean = []
        for img in shown:
            sub = np.flipud(img)[c0:N - c0, c0:N - c0]   # nord en haut, carré centré sur la cible
            rgba = cmap(norm(sub))
            ok = np.isfinite(sub)[..., None]
            clean.append((np.where(ok, rgba[..., :3], 0.0) * 255).astype(np.uint8))
        # une image fixe PROPRE par date (la même que dans la vidéo : nord en haut, sans coins
        # vides, sans repère ni médaillon) -> utilisée par « Compare 2 Dates »
        import matplotlib.image as mpimg
        for k, (img, e) in enumerate(zip(clean, entries)):
            still = out_dir / f"{tag}_date_{k:02d}.png"
            mpimg.imsave(still, img)
            e["image_url"] = str(still)
        seq.video = build_video(clean, entries, out_dir / tag, loop_back=len(clean) > 1,
                                make_gif=MAKE_GIF)
        seq.video.grid_size_px = n
        seq.video.px_scale = round(float(up), 4)
        seq.video.crop_px = int(c0)
        # variante avec repères dessinés (positions, trajectoire), toujours sans texte
        if rgb:
            mk = build_video(rgb, entries, out_dir / f"{tag}_reperes", loop_back=len(rgb) > 1,
                             make_gif=False, make_vtt=False)
            seq.video.mp4_markers = mk.mp4
        seq.gif = seq.video.gif


def _render_side_by_side(item: dict, cache: dict, frames_by_id: dict, measures: dict,
                         out_dir: Path, k: int) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from astropy.visualization import AsinhStretch, ImageNormalize, ManualInterval
    from app.core.align import display_image
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.6))
    imgs = [display_image(cache[item[k_]]["image"]) for k_ in ("frame_a", "frame_b")]
    n = cache[item["frame_a"]]["image"].shape[0]
    ext = (-0.5, n - 0.5, -0.5, n - 0.5)
    mA, mB = measures[item["frame_a"]], measures[item["frame_b"]]
    # contraste calculé sur la zone zoomée (sinon le cœur d'une étoile brillante sature tout)
    up = imgs[0].shape[0] / n
    cxp, cyp = (mA.x_px + mB.x_px) / 2, (mA.y_px + mB.y_px) / 2
    sl = (slice(max(int((cyp - 6 + 0.5) * up), 0), int((cyp + 6 + 0.5) * up)),
          slice(max(int((cxp - 6 + 0.5) * up), 0), int((cxp + 6 + 0.5) * up)))
    vals = np.concatenate([d[sl][np.isfinite(d[sl])] for d in imgs])
    norm = ImageNormalize(interval=ManualInterval(*np.percentile(vals, [20, 99.9])),
                          stretch=AsinhStretch(0.3))
    for ax, img, key, gname in ((axes[0], imgs[0], "frame_a", item["group_a"]),
                                (axes[1], imgs[1], "frame_b", item["group_b"])):
        f = frames_by_id[item[key]]
        ax.imshow(img, origin="lower", cmap="magma", norm=norm, extent=ext, interpolation="bilinear")
        ax.plot(mA.x_px, mA.y_px, "o", ms=10, mfc="none", mec="#00e5ff", mew=1.3)
        ax.plot(mB.x_px, mB.y_px, "s", ms=10, mfc="none", mec="#7CFC00", mew=1.3)
        cx, cy = (mA.x_px + mB.x_px) / 2, (mA.y_px + mB.y_px) / 2
        ax.set_xlim(cx - 6, cx + 6), ax.set_ylim(cy - 6, cy + 6)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_title(f"{gname}  λ = {f.wavelength_um:.3f} µm", fontsize=9)
    fig.suptitle(f"{item['date']} — même instant, deux groupes : écart {item['distance_px']:.2f} px "
                 f"(seuil {item['tolerance_px']:.2f} px)\n○ position mesurée par {item['group_a']}   "
                 f"□ position mesurée par {item['group_b']}", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    path = out_dir / f"comparaison_{k:02d}.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return str(path)


def group_views(motion: MotionResult, frames_by_id: dict,
                conflicted: Optional[list[str]] = None) -> list[tuple[DisplaySequence, MotionResult]]:
    """Une séquence par groupe : toutes ses images, dans l'ordre chronologique, avec le
    mouvement mesuré sur CE groupe seul (positions brutes, aucune correction).
    Rangées comme les groupes : plus de passages, puis plus longue durée ; isolées à la fin."""
    nums = group_numbers(motion.measures)
    by_g: dict[str, list[PositionMeasure]] = {}
    for m in motion.measures:
        by_g.setdefault(pseudo_group(m), []).append(m)
    out = []
    for g, ms in by_g.items():
        ms = sorted(ms, key=lambda m: m.mjd)
        visits = {m.visit if m.visit is not None else round(m.mjd) for m in ms}
        fit = fit_motion([m.model_copy() for m in ms], with_offsets=False)
        wls = [m.wavelength_um for m in ms if m.wavelength_um]
        det = sorted({m.detector for m in ms if m.detector})
        span = ms[-1].mjd - ms[0].mjd
        info = dict(group=g, number=nums.get(g), detector=", ".join(det) or None,
                    wavelength_um=round(float(np.median(wls)), 4) if wls else None,
                    n_images=len(ms), n_passages=len(visits),
                    date_start=ms[0].date_utc, date_end=ms[-1].date_utc, span_days=round(span, 1),
                    in_disagreement=bool(conflicted and g in conflicted),
                    mu_arcsec_yr=fit.mu_arcsec_yr, mu_err_arcsec_yr=fit.mu_err_arcsec_yr,
                    position_angle_deg=fit.position_angle_deg,
                    motion_status=fit.status, motion_reason=fit.status_reason)
        wl_txt = f"{info['wavelength_um']:.2f} µm" if info["wavelength_um"] else "λ ?"
        if fit.mu_arcsec_yr is not None and len(visits) >= 2:
            mu_txt = f"{fit.mu_arcsec_yr:.1f}″/an" + (f" ± {fit.mu_err_arcsec_yr:.1f}"
                                                      if fit.mu_err_arcsec_yr else "")
        else:
            mu_txt = "1 passage : pas de mouvement mesurable" if len(visits) < 2 else fit.status
        title = (f"{nums.get(g, 'Image seule')} · {info['detector'] or '?'} · {wl_txt} · {len(visits)} passage(s) · "
                 f"{ms[0].date_utc[:7]} → {ms[-1].date_utc[:7]} · {mu_txt}")
        seq = DisplaySequence(kind="groupe", groups=[g], frame_ids=[m.frame_id for m in ms],
                              segments={m.frame_id: [0, f"groupe {g}"] for m in ms},
                              title=title, info=info)
        out.append(((len(visits), span, not g.startswith("isolee_")), seq, fit))
    out.sort(key=lambda t: (t[0][2], t[0][0], t[0][1]), reverse=True)
    return [(seq, fit) for _, seq, fit in out]


def render_display(target, motion: MotionResult, plan: DisplayPlan, frames_by_id: dict,
                   cache: dict, out_dir: Path) -> DisplayPlan:
    import shutil
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meas = {m.frame_id: m for m in motion.measures}
    for i, seq in enumerate(plan.sequences):
        if seq.frame_ids:
            tag = "trajectoire" if seq.kind in ("unique", "principale") else f"separee_{i:02d}_{seq.groups[0]}"
            _render_sequence(target, seq, motion, frames_by_id, cache, out_dir, tag)
    # images côte à côte : seulement les désaccords les plus marqués (rendu coûteux)
    ranked = sorted(plan.side_by_side, key=lambda it: it["distance_px"] / max(it["tolerance_px"], 1e-6),
                    reverse=True)
    for k, item in enumerate(ranked[:MAX_SIDE_BY_SIDE]):
        item["png"] = _render_side_by_side(item, cache, frames_by_id, meas, out_dir, k)
    # une vidéo par groupe (rendu léger : vidéo propre seulement)
    plan.group_sequences = []
    for gi, (seq, fit) in enumerate(group_views(motion, frames_by_id, plan.conflicted_groups)):
        if not fit.measures:
            continue
        _render_sequence(target, seq, fit, frames_by_id, cache, out_dir, f"groupe_{gi:02d}", light=True)
        if seq.video:
            plan.group_sequences.append(seq)
    return plan


def positions_plot(target, motion: MotionResult, out_path: Path) -> str:
    """Positions BRUTES dans le temps (barres d'erreur), écartées en gris, trajectoire ajustée."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    groups = sorted({pseudo_group(m) for m in motion.measures})
    palette = ["#0097a7", "#2e7d32", "#c49000", "#c2185b", "#e65100", "#5e35b1", "#444444"]
    gcol = {g: palette[i % len(palette)] for i, g in enumerate(groups)}
    t_all = [m.mjd for m in motion.measures if m.used]
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 5.8), sharex=True)
    for ax, comp, lab in ((axes[0], "x", "x (px, vers l'ouest)"), (axes[1], "y", "y (px, vers le nord)")):
        for g in groups:
            ms = [m for m in motion.measures if pseudo_group(m) == g]
            for m in ms:
                v = getattr(m, f"{comp}_px")
                if m.used:
                    ax.errorbar(m.mjd, v, yerr=max(m.sigma_px, SIGMA_FLOOR_PX), fmt="o", ms=4, color=gcol[g])
                else:
                    ax.plot(m.mjd, v, "o", mfc="none", mec="#999999")
        if motion.t0_mjd is not None and t_all:
            tt = np.linspace(min(t_all), max(t_all), 50)
            ax.plot(tt, [motion.predict(t)[0 if comp == "x" else 1] for t in tt], "k-", lw=1)
        ax.set_ylabel(lab)
    axes[1].set_xlabel("date (MJD)")
    handles = [plt.Line2D([], [], marker="o", ls="", color=gcol[g], label=g) for g in groups[:7]]
    axes[0].legend(handles=handles, fontsize=7, loc="best")
    fig.suptitle(f"{target.label} — positions mesurées BRUTES et trajectoire ajustée", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return str(out_path)


from app.core.video import VideoAssets  # noqa: E402
DisplaySequence.model_rebuild()
