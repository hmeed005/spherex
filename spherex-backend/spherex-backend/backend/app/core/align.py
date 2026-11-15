"""Étape 5 du pipeline : ALIGN — même vue du ciel pour toutes les images d'un groupe.

Chaque cutout a son propre pointage et sa propre orientation : la cible tombe sur des
pixels détecteur différents d'une image à l'autre, SANS que cela soit un mouvement.
Le WCS de chaque image relie ses pixels aux coordonnées célestes (RA/Dec, distorsion SIP
comprise). On rééchantillonne donc chaque image sur UNE grille céleste commune :
  - centre fixe : position de la cible au milieu de la mission (la grille ne suit PAS
    l'objet, sinon on effacerait son mouvement) ;
  - échelle 6,15"/pixel (pixel SPHEREx natif) ;
  - orientation : nord en haut, est à gauche (projection TAN).

Pour chaque pixel de la grille : (x, y) grille -> (RA, Dec) -> (x, y) dans l'image source
(WCS de l'image) -> interpolation bilinéaire (valeurs, variance) ou plus proche voisin (flags).

Vérification : les étoiles fixes du champ doivent tomber au même pixel de la grille dans
toutes les images (résidu attendu < ~0,3 px). Le déplacement de la cible, lui, doit suivre
son mouvement propre.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

from app.core.screen import ARTIFACT_BITS, DEAD_BITS, SATURATION_BITS, position_at
from app.core.target import PIXSCALE_ARCSEC

BAD_BITS = ARTIFACT_BITS | DEAD_BITS


# ------------------------------------------------------------------ grille commune
def make_grid(ra: float, dec: float, size_px: int, pixscale_arcsec: float = PIXSCALE_ARCSEC):
    from astropy.wcs import WCS
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(size_px + 1) / 2, (size_px + 1) / 2]       # centre de la grille (FITS 1-based)
    w.wcs.cdelt = [-pixscale_arcsec / 3600, pixscale_arcsec / 3600]  # est à gauche, nord en haut
    w.wcs.radesys = "ICRS"
    return w


# ------------------------------------------------------------------ rééchantillonnage
def _bilinear(data: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Interpolation bilinéaire tolérante aux NaN (NaN si moins de 50 % de poids valide)."""
    ny, nx = data.shape
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    acc = np.zeros(x.shape)
    wsum = np.zeros(x.shape)
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        inside = (xi >= 0) & (xi < nx) & (yi >= 0) & (yi < ny)
        v = np.full(x.shape, np.nan)
        v[inside] = data[yi[inside], xi[inside]]
        ok = np.isfinite(v)
        acc[ok] += wt[ok] * v[ok]
        wsum[ok] += wt[ok]
    out = np.full(x.shape, np.nan)
    good = wsum >= 0.5
    out[good] = acc[good] / wsum[good]
    return out


def _nearest(data: np.ndarray, x: np.ndarray, y: np.ndarray, fill=0) -> np.ndarray:
    ny, nx = data.shape
    xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
    inside = (xi >= 0) & (xi < nx) & (yi >= 0) & (yi < ny)
    out = np.full(x.shape, fill, dtype=data.dtype)
    out[inside] = data[yi[inside], xi[inside]]
    return out


def reproject_frame(path: Path, grid, shape: tuple[int, int]) -> dict:
    """Image (zodiacal retiré), sigma et flags d'un cutout, sur la grille commune."""
    from astropy.io import fits
    from astropy.wcs import WCS, FITSFixedWarning
    with fits.open(path) as h, warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        img = h["IMAGE"].data.astype(float)
        if "ZODI" in h:
            img = img - h["ZODI"].data
        var = h["VARIANCE"].data.astype(float) if "VARIANCE" in h else np.full(img.shape, np.nan)
        flags = h["FLAGS"].data.astype(np.int64) if "FLAGS" in h else np.zeros(img.shape, np.int64)
        src_wcs = WCS(h["IMAGE"].header)
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    ra, dec = grid.pixel_to_world_values(xx, yy)              # grille -> ciel
    sx, sy = src_wcs.world_to_pixel_values(ra, dec)           # ciel -> image source (SIP inclus)
    sx, sy = np.asarray(sx), np.asarray(sy)
    img = np.where((flags & BAD_BITS) != 0, np.nan, img)      # pixels défectueux exclus
    out_img = _bilinear(img, sx, sy)
    out_var = _bilinear(np.where(np.isfinite(img), var, np.nan), sx, sy)
    out_flags = _nearest(flags, sx, sy, fill=0)
    coverage = float(np.isfinite(out_img).mean())
    # rotation de l'image source par rapport au nord (pour information)
    cd = src_wcs.pixel_scale_matrix
    rotation = float(np.degrees(np.arctan2(cd[1, 0], cd[1, 1])))
    return dict(image=out_img, sigma=np.sqrt(np.clip(out_var, 0, None)), flags=out_flags,
                coverage=coverage, source_rotation_deg=round(rotation, 2))


# ------------------------------------------------------------------ mesures sur la grille
def annulus_background(img: np.ndarray, x: float, y: float, r_in: float = 6.0,
                       r_out: float = 10.0) -> float:
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    r = np.hypot(xx - x, yy - y)
    v = img[(r >= r_in) & (r <= r_out) & np.isfinite(img)]
    return float(np.median(v)) if v.size else 0.0


def centroid(img: np.ndarray, x: float, y: float, half: int = 3,
             mask: Optional[np.ndarray] = None,
             bkg: Optional[float] = None) -> Optional[tuple[float, float]]:
    """Centroïde pondéré dans une boîte autour de (x, y).
    bkg : fond à soustraire ; par défaut, médiane du bord de la boîte (étoiles faibles).
    Pour un objet brillant, passer le fond d'un anneau éloigné (annulus_background)."""
    ny, nx = img.shape
    xi, yi = int(round(x)), int(round(y))
    x0, x1, y0, y1 = max(xi - half, 0), min(xi + half + 1, nx), max(yi - half, 0), min(yi + half + 1, ny)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    sub = img[y0:y1, x0:x1].copy()
    if mask is not None:
        sub[mask[y0:y1, x0:x1]] = np.nan
    if bkg is None:
        ring = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
        ring = ring[np.isfinite(ring)]
        bkg = float(np.median(ring)) if ring.size else 0.0
    w = np.clip(np.nan_to_num(sub - bkg), 0, None)
    if w.sum() <= 0:
        return None
    gy, gx = np.mgrid[y0:y1, x0:x1]
    return float((w * gx).sum() / w.sum()), float((w * gy).sum() / w.sum())


def find_field_stars(img: np.ndarray, sat: np.ndarray, exclude_xy: tuple[float, float],
                     n_max: int = 15, min_snr: float = 15.0) -> list[tuple[float, float]]:
    """Étoiles fixes brillantes mais non saturées, loin de la cible et des bords."""
    ny, nx = img.shape
    finite = np.isfinite(img)
    if finite.sum() < 50:
        return []
    bkg = np.median(img[finite])
    rms = 1.4826 * np.median(np.abs(img[finite] - bkg)) or 1.0
    a = np.nan_to_num(img, nan=-np.inf)
    peaks = []
    for y in range(4, ny - 4):
        for x in range(4, nx - 4):
            v = a[y, x]
            if v < bkg + min_snr * rms or sat[y - 1:y + 2, x - 1:x + 2].any():
                continue
            if v < a[y - 2:y + 3, x - 2:x + 3].max():
                continue
            if np.hypot(x - exclude_xy[0], y - exclude_xy[1]) < 8:
                continue
            peaks.append((v, x, y))
    peaks.sort(reverse=True)
    return [(float(x), float(y)) for _, x, y in peaks[:n_max]]


# ------------------------------------------------------------------ alignement d'un groupe
class AlignedFrame(BaseModel):
    frame_id: Optional[str]
    obs_id: str
    date_utc: Optional[str]
    wavelength_um: float
    status: str
    coverage: float                       # part de la grille couverte par l'image
    source_rotation_deg: float            # orientation d'origine (info)
    target_expected_px: tuple[float, float]       # position prédite (x, y) sur la grille
    target_measured_px: Optional[tuple[float, float]] = None
    target_offset_px: Optional[float] = None      # mesuré - prédit
    field_shift_px: Optional[tuple[float, float]] = None   # décalage médian des étoiles fixes
    field_residual_px: Optional[float] = None              # dispersion de ce décalage
    n_field_stars: int = 0
    png: Optional[str] = None


class AlignResult(BaseModel):
    group_id: str
    grid_center_ra: float
    grid_center_dec: float
    grid_size_px: int
    pixscale_arcsec: float
    orientation: str = "nord en haut, est à gauche"
    frames: list[AlignedFrame]
    n_field_stars_ref: int
    max_field_shift_px: Optional[float]   # pire décalage des étoiles fixes (qualité d'alignement)
    target_track_px: Optional[float]      # déplacement mesuré de la cible, 1re -> dernière image
    target_expected_track_px: Optional[float]
    alignment_ok: bool
    gif: Optional[str] = None
    sheet: Optional[str] = None


def align_group(target, group, frames_by_id: dict, out_dir: Optional[Path] = None,
                render: bool = True) -> AlignResult:
    """group : WavelengthGroup ; frames_by_id : frame_id -> FrameQuality (avec .path)."""
    n = target.size_px
    grid = make_grid(target.ra_deg, target.dec_deg, n)
    shape = (n, n)

    aligned, metas = [], []
    for gf in group.frames:
        fq = frames_by_id[gf.frame_id]
        rp = reproject_frame(Path(fq.path), grid, shape)
        from astropy.time import Time
        mjd = Time(gf.date_utc.rstrip("Z"), format="isot").mjd
        ra, dec = position_at(target, mjd)
        ex, ey = (float(v) for v in grid.world_to_pixel_values(ra, dec))
        aligned.append(rp)
        metas.append((gf, ex, ey))

    # étoiles fixes de référence (image la plus couverte), mesurées dans toutes les images
    ref_i = int(np.argmax([a["coverage"] for a in aligned]))
    ref = aligned[ref_i]
    ref_sat = (ref["flags"] & SATURATION_BITS) != 0
    stars = find_field_stars(ref["image"], ref_sat, (metas[ref_i][1], metas[ref_i][2]))
    ref_pos = [centroid(ref["image"], x, y) for x, y in stars]

    out: list[AlignedFrame] = []
    for a, (gf, ex, ey) in zip(aligned, metas):
        sat = (a["flags"] & SATURATION_BITS) != 0
        shifts = []
        for (sx, sy), rpos in zip(stars, ref_pos):
            c = centroid(a["image"], sx, sy)
            if c and rpos and np.hypot(c[0] - rpos[0], c[1] - rpos[1]) < 2:
                shifts.append((c[0] - rpos[0], c[1] - rpos[1]))
        if shifts:
            sh = np.array(shifts)
            med = np.median(sh, axis=0)
            resid = float(np.median(np.hypot(*(sh - med).T))) if len(sh) > 1 else None
        else:
            med, resid = None, None
        # cible : pixels saturés = NaN (déjà exclus) ; on garde les ailes, même marquées BLOOM,
        # car le débordement tourne avec l'orientation de l'image. Fond : anneau éloigné.
        tc = centroid(a["image"], ex, ey, bkg=annulus_background(a["image"], ex, ey))
        out.append(AlignedFrame(
            frame_id=gf.frame_id, obs_id=gf.obs_id, date_utc=gf.date_utc,
            wavelength_um=gf.wavelength_um, status=gf.status,
            coverage=round(a["coverage"], 3), source_rotation_deg=a["source_rotation_deg"],
            target_expected_px=(round(ex, 2), round(ey, 2)),
            target_measured_px=None if tc is None else (round(tc[0], 2), round(tc[1], 2)),
            target_offset_px=None if tc is None else round(float(np.hypot(tc[0] - ex, tc[1] - ey)), 2),
            field_shift_px=None if med is None else (round(float(med[0]), 3), round(float(med[1]), 3)),
            field_residual_px=None if resid is None else round(resid, 3),
            n_field_stars=len(shifts),
        ))

    shifts_all = [np.hypot(*f.field_shift_px) for f in out if f.field_shift_px]
    max_shift = round(float(max(shifts_all)), 3) if shifts_all else None
    meas = [f.target_measured_px for f in out if f.target_measured_px]
    track = (round(float(np.hypot(meas[-1][0] - meas[0][0], meas[-1][1] - meas[0][1])), 2)
             if len(meas) > 1 else None)
    exp = (round(float(np.hypot(out[-1].target_expected_px[0] - out[0].target_expected_px[0],
                                out[-1].target_expected_px[1] - out[0].target_expected_px[1])), 2)
           if len(out) > 1 else None)

    result = AlignResult(
        group_id=group.id, grid_center_ra=target.ra_deg, grid_center_dec=target.dec_deg,
        grid_size_px=n, pixscale_arcsec=PIXSCALE_ARCSEC, frames=out,
        n_field_stars_ref=len(stars), max_field_shift_px=max_shift,
        target_track_px=track, target_expected_track_px=exp,
        alignment_ok=max_shift is not None and max_shift < 0.5,
    )
    if render and out_dir is not None:
        render_group(result, aligned, out_dir, target.label)
    return result


# ------------------------------------------------------------------ embellissement (AFFICHAGE SEULEMENT)
# Ces traitements ne servent qu'aux images montrées à l'utilisateur. Toutes les mesures
# (centroïdes, mouvement, contrôles d'alignement) utilisent les données brutes alignées.
DISPLAY_SMOOTH_SIGMA = 0.6   # lissage gaussien léger (pixels) : réduit le bruit, garde la PSF
DISPLAY_UPSAMPLE = 6         # agrandissement bicubique : pixels "carrés" -> image lisse
GIF_CROSSFADE_STEPS = 8      # images intermédiaires de fondu entre deux dates
GIF_HOLD_MS = 3000           # durée d'affichage de chaque date (ms)
GIF_FADE_MS = 150            # durée de chaque image du fondu (ms) -> fondu de ~1,2 s


def fill_holes(img: np.ndarray, max_iter: int = 6) -> np.ndarray:
    """Bouche les petits trous (pixels masqués) par la moyenne de leurs voisins valides."""
    out = img.copy()
    for _ in range(max_iter):
        nan = ~np.isfinite(out)
        if not nan.any():
            break
        pad = np.pad(out, 1, constant_values=np.nan)
        neigh = np.stack([pad[1 + dy:1 + dy + out.shape[0], 1 + dx:1 + dx + out.shape[1]]
                          for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
        cnt = np.isfinite(neigh).sum(0)
        mean = np.nansum(neigh, 0) / np.maximum(cnt, 1)
        fill = nan & (cnt >= 3)               # au moins 3 voisins valides : vrai petit trou
        if not fill.any():
            break
        out[fill] = mean[fill]
    return out


def gaussian_smooth(img: np.ndarray, sigma: float) -> np.ndarray:
    """Lissage gaussien séparable qui ignore les NaN (pas de dépendance à scipy)."""
    if sigma <= 0:
        return img
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    valid = np.isfinite(img).astype(float)
    data = np.nan_to_num(img)
    for axis in (0, 1):
        data = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), axis, data)
        valid = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), axis, valid)
    out = np.where(valid > 0.3, data / np.maximum(valid, 1e-9), np.nan)
    return out


def upsample(img: np.ndarray, factor: int) -> np.ndarray:
    """Agrandissement bilinéaire (Pillow) : après le lissage gaussien, c'est déjà très lisse, et
    contrairement au bicubique, il ne crée pas d'anneau sombre autour des étoiles saturées."""
    from PIL import Image
    if factor <= 1:
        return img
    nan = ~np.isfinite(img)
    base = np.where(nan, np.nanmedian(img), img).astype(np.float32)
    big = np.asarray(Image.fromarray(base, mode="F").resize(
        (img.shape[1] * factor, img.shape[0] * factor), Image.BILINEAR))
    nan_big = np.asarray(Image.fromarray(nan.astype(np.uint8) * 255).resize(
        (img.shape[1] * factor, img.shape[0] * factor), Image.NEAREST)) > 127
    return np.where(nan_big, np.nan, big)


def display_image(img: np.ndarray, smooth: bool = True) -> np.ndarray:
    if not smooth:
        return img
    return upsample(gaussian_smooth(fill_holes(img), DISPLAY_SMOOTH_SIGMA), DISPLAY_UPSAMPLE)


# ------------------------------------------------------------------ rendu PNG / GIF
def render_group(result: AlignResult, aligned: list[dict], out_dir: Path, label: str,
                 smooth: bool = True) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from astropy.visualization import AsinhStretch, ImageNormalize, ManualInterval
    from PIL import Image

    out_dir.mkdir(parents=True, exist_ok=True)
    n = aligned[0]["image"].shape[0]
    extent = (-0.5, n - 0.5, -0.5, n - 0.5)       # garde les coordonnées en pixels de grille
    shown = [display_image(a["image"], smooth) for a in aligned]
    vals = np.concatenate([d[np.isfinite(d)] for d in shown])
    # MÊME étirement pour toutes les images du groupe (sinon faux changements d'éclat) ;
    # bornes basses pour que l'objet brillant n'écrase pas les étoiles du fond
    lo, hi = np.percentile(vals, [5, 98.5] if smooth else [5, 99.0]) if vals.size else (0, 1)
    norm = ImageNormalize(interval=ManualInterval(lo, hi),
                          stretch=AsinhStretch(0.04 if smooth else 0.08))
    cmap = plt.get_cmap("magma" if smooth else "gray").copy()
    cmap.set_bad("#20242c" if smooth else "#3b6ea8")

    def draw(ax, img, f):
        ax.imshow(img, origin="lower", cmap=cmap, norm=norm, extent=extent,
                  interpolation="bilinear" if smooth else "nearest")
        ex, ey = f.target_expected_px
        ax.plot(ex, ey, marker="o", ms=18, mfc="none", mec="#00e5ff", mew=1.3)
        first = result.frames[0].target_expected_px
        ax.plot(*first, marker="+", ms=11, color="#7CFC00", mew=1.3)   # position à la 1re date
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xticks([]), ax.set_yticks([])

    def figure_for(img, f):
        fig, ax = plt.subplots(figsize=(5, 5.5))
        draw(ax, img, f)
        ax.set_title(f"{f.date_utc[:10]}   λ = {f.wavelength_um:.3f} µm", fontsize=11)
        fig.text(0.5, 0.02, "N ↑  E ←   cercle = position prédite, + = 1re date",
                 ha="center", fontsize=8)
        fig.canvas.draw()
        return fig

    rgb_frames = []
    for i, (img, f) in enumerate(zip(shown, result.frames)):
        fig = figure_for(img, f)
        png = out_dir / f"{i:02d}_{f.frame_id}.png"
        fig.savefig(png, dpi=130)
        f.png = str(png)
        rgb_frames.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(float))
        plt.close(fig)

    if len(rgb_frames) > 1:
        # animation fluide : chaque date tenue ~1 s, puis fondu enchaîné vers la suivante
        seq, durations = [], []
        steps = GIF_CROSSFADE_STEPS if smooth else 0
        for i, cur in enumerate(rgb_frames):
            seq.append(cur)
            durations.append(GIF_HOLD_MS)
            nxt = rgb_frames[(i + 1) % len(rgb_frames)]
            for k in range(1, steps + 1):
                t = k / (steps + 1)
                seq.append((1 - t) * cur + t * nxt)
                durations.append(GIF_FADE_MS)
        imgs = [Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)) for a in seq]
        gif = out_dir / "blink.gif"
        imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=durations, loop=0)
        result.gif = str(gif)

    ncol = len(aligned)
    fig, axes = plt.subplots(1, ncol, figsize=(3.6 * ncol, 4.1), squeeze=False)
    for ax, img, f in zip(axes[0], shown, result.frames):
        draw(ax, img, f)
        ax.set_title(f"{f.date_utc[:10]}\n{f.wavelength_um:.3f} µm", fontsize=9)
    fig.suptitle(f"{label} — groupe {result.group_id} — vue alignée (N en haut, E à gauche)",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    sheet = out_dir / ("sheet.png" if smooth else "sheet_raw.png")
    fig.savefig(sheet, dpi=130)
    plt.close(fig)
    result.sheet = str(sheet)
