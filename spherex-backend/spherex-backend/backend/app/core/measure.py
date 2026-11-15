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


class DisplayPlan(BaseModel):
    comparisons: list[GroupComparison]
    conflicted_groups: list[str]
    sequences: list[DisplaySequence]
    side_by_side: list[dict] = []   # images comparées aux instants de désaccord
    summary: str


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
    for bi, (label, ms) in enumerate(blocks):
        for j, m in enumerate(ms):
            frame_ids.append(m.frame_id)
            segments[m.frame_id] = (bi, label)
            if label.startswith("groupe ") and j == 0:
                bad = [c for c in comps if not c.agree and pseudo_group(m) in (c.group_a, c.group_b)]
                why = " ; ".join(f"décalage de {c.distance_px:.2f} px avec "
                                 f"{c.group_b if c.group_a == pseudo_group(m) else c.group_a} "
                                 f"le {c.date} (seuil {c.tolerance_px:.2f} px)" for c in bad[:3])
                notes[m.frame_id] = (f"⚠ nouveau bloc : {label} (montré à part car en désaccord : "
                                     f"{why}). À juger par l'utilisateur.")
        # à l'intérieur d'un bloc : passages concordants et raccords non vérifiables
        for prev, cur in zip(ms, ms[1:]):
            ga, gb = pseudo_group(prev), pseudo_group(cur)
            if ga != gb and frozenset((ga, gb)) not in agree_edges and cur.frame_id not in notes:
                notes[cur.frame_id] = (f"raccord non vérifiable : {ga} -> {gb} "
                                       "(aucun passage commun pour comparer les positions)")
        for m in ms:
            ok = [c for c in comps if c.agree and c.visit == m.visit
                  and pseudo_group(m) in (c.group_a, c.group_b)]
            if ok and m.frame_id not in notes:
                c = ok[0]
                notes[m.frame_id] = (f"positions concordantes {c.group_a} / {c.group_b} "
                                     f"(écart {c.distance_px:.2f} px ≤ {c.tolerance_px:.2f} px) : "
                                     "image la plus visible affichée")

    seq = DisplaySequence(kind="unique", groups=groups_all, frame_ids=frame_ids, notes=notes,
                          segments={fid: list(v) for fid, v in segments.items()})
    sbs = [dict(date=c.date, group_a=c.group_a, group_b=c.group_b, frame_a=c.frame_a,
                frame_b=c.frame_b, distance_px=c.distance_px, tolerance_px=c.tolerance_px)
           for c in comps if not c.agree]
    summary = (f"incertitudes calibrées x{sigma_scale:.2f} ; " if sigma_scale > 1 else "") + (
        "tous les groupes concordent : une image par passage, ordre chronologique"
        if not conflicted else
        f"{len(sbs)} désaccord(s) : vidéo en {len(blocks)} blocs joués l'un après l'autre "
        f"(groupes concordants, puis chaque groupe en désaccord en entier)")
    return DisplayPlan(comparisons=comps, conflicted_groups=conflicted,
                       sequences=[seq] if frame_ids else [], side_by_side=sbs, summary=summary)


# ----------------------------------------------------------------- rendu
def _render_sequence(target, seq: DisplaySequence, motion: MotionResult, frames_by_id: dict,
                     cache: dict, out_dir: Path, tag: str) -> None:
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
            if motion.t0_mjd is not None and t_all else [])
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
    for k, fid in enumerate(chosen):
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
    seq.frames_png = pngs
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
        pred = motion.predict(m.mjd) if motion.t0_mjd is not None else None
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
    if rgb:
        # vidéo PROPRE : uniquement l'image du ciel (même contraste pour toutes les dates)
        up = shown[0].shape[0] / n
        clean = []
        for img in shown:
            rgba = cmap(norm(np.flipud(img)))            # nord en haut
            clean.append((np.nan_to_num(rgba[..., :3], nan=0.12) * 255).astype(np.uint8))
        seq.video = build_video(clean, entries, out_dir / tag, loop_back=len(clean) > 1,
                                make_gif=MAKE_GIF)
        seq.video.grid_size_px = n
        seq.video.px_scale = round(float(up), 4)
        # variante avec repères dessinés (positions, trajectoire), toujours sans texte
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
