"""Étape 3 du pipeline : SCREEN — l'objet est-il net et mesurable sur chaque image ?

Pour chaque cutout téléchargé, à la position de la cible À LA DATE de l'image :
  - longueur d'onde au pixel de la cible (WCS spectral) ;
  - qualité des pixels autour de la cible (FLAGS) ;
  - signal sur bruit (S/N) de l'objet, écart entre position attendue et centroïde mesuré.

Statuts possibles (constatés sur les vraies images de Barnard, toutes saturées) :
  nette      : S/N >= 10, pas d'artefact, objet à sa place
  saturee    : objet très brillant, cœur saturé (OVERFLOW / BLOOM / NONLINEAR) -> GARDÉE,
               utilisable pour l'affichage ; la position se mesure sur les ailes
  faible     : 5 <= S/N < 10
  decalee    : objet net mais centroïde à plus de MAX_OFFSET_PX de la position attendue
  invisible  : S/N < 5                                     -> rejetée
  artefact   : fantôme, traînée, persistance... sur la cible -> rejetée
  hors_image : position hors du cutout                    -> rejetée
"""
from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

# Bits FLAGS (noms lus dans l'en-tête FLAGS des vraies images : MSKNnnnn)
TRANSIENT, OVERFLOW, SUR_ERROR, NONFUNC, MISSING = 0, 1, 2, 6, 9
HOT, COLD, NONLINEAR, PERSIST, OUTLIER, CROSSTALK = 10, 11, 15, 17, 19, 20
SOURCE, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO = 21, 22, 23, 24, 25, 26, 27, 28

SATURATION_BITS = (1 << OVERFLOW) | (1 << NONLINEAR) | (1 << BLOOM)
ARTIFACT_BITS = ((1 << GHOST) | (1 << GHOST_FPA) | (1 << GHOST_EXT) | (1 << STREAK)
                 | (1 << SNOWBALL) | (1 << PERSIST) | (1 << CROSSTALK))
DEAD_BITS = (1 << NONFUNC) | (1 << MISSING) | (1 << HOT) | (1 << COLD)
# Ignorés : SOURCE (présent sur 100 % des pixels en champ dense), SUR_ERROR (toléré par
# IRSA) et TRANSIENT (déclenché par les étoiles saturées elles-mêmes sur les vraies images).

APERTURE_PX = 2.5          # rayon d'ouverture (PSF_FWHM ≈ 7,5" ≈ 1,2 px)
ANNULUS_PX = (6.0, 10.0)   # anneau pour le fond de ciel
SNR_CLEAR = 10.0
SNR_MIN = 5.0
MAX_OFFSET_PX = 1.5
MAX_ARTIFACT_FRAC = 0.2    # part max de l'ouverture touchée par des artefacts
# --- Visibilité pixel par pixel ---
CORE_PX = 1.5              # rayon du "cœur" : les pixels les plus importants de l'objet
PIXEL_SNR_SIG = 2.0        # un pixel est "significatif" si (valeur - fond) / sigma >= 2
MIN_SIG_PIXELS = 3         # un vrai objet (PSF ~1,2 px) couvre plusieurs pixels significatifs
MIN_CORE_VALID = 0.5       # au moins 50 % des pixels du cœur doivent avoir valeur + incertitude
MAX_CORE_REL_UNC = 0.2     # incertitude relative médiane du cœur (sigma / signal) <= 20 %
MIN_WING_SIG_PIXELS = 6    # objet saturé : il faut assez de pixels d'ailes fiables


class FrameQuality(BaseModel):
    frame_id: Optional[str] = None      # identifiant du cutout (pour /api/frame/{frame_id})
    obs_id: str
    detector: Optional[str] = None
    date_utc: Optional[str] = None
    path: Optional[str] = None
    status: str
    keep: bool
    reason: str
    wavelength_um: Optional[float] = None
    bandwidth_um: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    snr: Optional[float] = None
    flux_mjysr_px: Optional[float] = None
    peak: Optional[float] = None
    centroid_offset_px: Optional[float] = None
    saturated: bool = False
    artifact_frac: float = 0.0
    dead_frac_local: float = 0.0
    background_rms: Optional[float] = None
    # --- valeurs physiques (unité : BUNIT de l'image, MJy/sr) ---
    unit: Optional[str] = None
    value_at_target: Optional[float] = None       # pixel de la cible, zodiacal retiré
    zodi_at_target: Optional[float] = None        # lumière zodiacale retirée
    background: Optional[float] = None            # fond de ciel local (médiane de l'anneau)
    flux_err_mjysr_px: Optional[float] = None     # incertitude sur le flux d'ouverture
    # --- incertitude (racine de l'extension VARIANCE) ---
    sigma_at_target: Optional[float] = None
    sigma_median: Optional[float] = None
    n_nan_in_aperture: int = 0                    # pixels sans valeur (ex. cœur saturé = NaN)
    # --- visibilité pixel par pixel ---
    core_valid_frac: Optional[float] = None       # pixels du cœur avec valeur ET incertitude
    core_pixel_snr: Optional[float] = None        # S/N médian des pixels du cœur
    core_rel_uncertainty: Optional[float] = None  # sigma / signal médian du cœur
    n_significant_pixels: int = 0                 # pixels de l'ouverture à >= 2 sigma
    wing_significant_pixels: int = 0              # idem, hors cœur (utile si saturé)
    # --- flags de qualité (noms lus dans l'en-tête FLAGS) ---
    flags_at_target: list[str] = []
    flags_in_aperture: dict[str, int] = {}        # nom -> nombre de pixels de l'ouverture
    flags_image_frac: dict[str, float] = {}       # nom -> fraction des pixels du cutout


def flag_names(flags_header) -> dict[int, str]:
    """{bit: nom} d'après les mots-clés MSKNnnnn de l'en-tête FLAGS."""
    names = {}
    for key, val in flags_header.items():
        if key.startswith("MSKN") and key[4:].isdigit():
            names[int(key[4:])] = str(val)
    return names


def decode_flags(value: int, names: dict[int, str]) -> list[str]:
    return [names.get(b, f"BIT{b}") for b in range(32) if (int(value) >> b) & 1]


def count_flags(values: np.ndarray, names: dict[int, str]) -> dict[str, int]:
    out = {}
    for b in range(32):
        n = int(((values >> b) & 1).sum())
        if n:
            out[names.get(b, f"BIT{b}")] = n
    return out


def _bits_present(flags: np.ndarray, mask: int) -> np.ndarray:
    return (flags & mask) != 0


def _f(v) -> Optional[float]:
    v = float(v)
    return None if not np.isfinite(v) else round(v, 5)


def wavelength_at(hdul, x: float, y: float) -> tuple[Optional[float], Optional[float]]:
    from astropy.wcs import WCS
    from astropy import log
    try:
        old = log.level
        log.setLevel("WARNING")  # masque le message "-SIP" sans conséquence
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sw = WCS(header=hdul["IMAGE"].header, fobj=hdul, key="W")
        log.setLevel(old)
        sw.sip = None  # obligatoire (tutoriel IRSA)
        wl, bw = sw.pixel_to_world_values(float(x), float(y))
        return float(np.ravel(wl)[0]), float(np.ravel(bw)[0])
    except Exception:  # noqa: BLE001
        return None, None


def screen_frame(path: Path, ra: float, dec: float, obs_id: str = "",
                 detector: Optional[str] = None, date_utc: Optional[str] = None) -> FrameQuality:
    from astropy.io import fits
    from astropy.wcs import WCS, FITSFixedWarning
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    base = dict(frame_id=Path(path).stem, obs_id=obs_id, detector=detector,
                date_utc=date_utc, path=str(path))
    with fits.open(path) as h, warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        img = h["IMAGE"].data.astype(float)
        unit = h["IMAGE"].header.get("BUNIT")
        zodi = h["ZODI"].data.astype(float) if "ZODI" in h else np.zeros(img.shape)
        img = img - zodi
        var = h["VARIANCE"].data.astype(float) if "VARIANCE" in h else None
        flags = (h["FLAGS"].data.astype(np.int64) if "FLAGS" in h
                 else np.zeros(img.shape, np.int64))
        names = flag_names(h["FLAGS"].header) if "FLAGS" in h else {}
        x, y = WCS(h["IMAGE"].header).world_to_pixel(SkyCoord(ra * u.deg, dec * u.deg))
        x, y = float(x), float(y)
        wl, bw = wavelength_at(h, x, y)

    ny, nx = img.shape
    if not (APERTURE_PX <= x < nx - APERTURE_PX and APERTURE_PX <= y < ny - APERTURE_PX):
        return FrameQuality(**base, status="hors_image", keep=False,
                            reason="position de la cible hors du cutout",
                            wavelength_um=wl, bandwidth_um=bw, x=x, y=y)

    yy, xx = np.mgrid[:ny, :nx]
    r = np.hypot(xx - x, yy - y)
    ap = r <= APERTURE_PX
    ann = (r >= ANNULUS_PX[0]) & (r <= ANNULUS_PX[1])
    box = (np.abs(xx - x) <= 7) & (np.abs(yy - y) <= 7)

    sat = _bits_present(flags, SATURATION_BITS)
    art = _bits_present(flags, ARTIFACT_BITS)
    dead = _bits_present(flags, DEAD_BITS)
    bad = art | dead

    saturated = bool(sat[ap].any())
    artifact_frac = float(art[ap].mean())
    dead_frac_local = float(dead[box].mean())

    # fond de ciel et bruit dans l'anneau (pixels propres uniquement)
    ann_ok = ann & ~bad & ~sat & np.isfinite(img)
    bkg = float(np.median(img[ann_ok])) if ann_ok.sum() > 10 else 0.0
    rms = float(1.4826 * np.median(np.abs(img[ann_ok] - bkg))) if ann_ok.sum() > 10 else None

    # flux et S/N dans l'ouverture (pixels morts/artefacts exclus ; saturés conservés)
    use = ap & ~bad & np.isfinite(img)
    flux = float(np.sum(img[use] - bkg)) if use.any() else 0.0
    if var is not None and use.any():
        noise2 = float(np.sum(var[use]))
    else:
        noise2 = 0.0
    if rms is not None:
        noise2 += use.sum() * rms ** 2
    snr = flux / np.sqrt(noise2) if noise2 > 0 else None
    peak = float(np.nanmax(img[ap])) if ap.any() else None

    # centroïde pondéré sur une boîte 7x7, pixels utilisables (ailes si saturée)
    cbox = (np.abs(xx - x) <= 3) & (np.abs(yy - y) <= 3) & ~bad & np.isfinite(img)
    wts = np.where(cbox, np.clip(np.nan_to_num(img - bkg), 0, None), 0.0)
    offset = None
    if wts.sum() > 0:
        cx, cy = (wts * xx).sum() / wts.sum(), (wts * yy).sum() / wts.sum()
        offset = float(np.hypot(cx - x, cy - y))

    xi, yi = int(round(x)), int(round(y))
    sigma = np.sqrt(np.clip(var, 0, None)) if var is not None else None
    n_ap = int(ap.sum())
    phys = dict(
        unit=unit,
        value_at_target=_f(img[yi, xi]),
        zodi_at_target=_f(zodi[yi, xi]),
        background=round(bkg, 5),
        flux_err_mjysr_px=None if noise2 <= 0 else round(float(np.sqrt(noise2)), 5),
        sigma_at_target=None if sigma is None else _f(sigma[yi, xi]),
        sigma_median=None if sigma is None else _f(np.nanmedian(sigma)),
        n_nan_in_aperture=int((~np.isfinite(img[ap])).sum()),
        flags_at_target=decode_flags(flags[yi, xi], names),
        flags_in_aperture=count_flags(flags[ap], names),
        flags_image_frac={k: round(v / flags.size, 4)
                          for k, v in count_flags(flags, names).items()},
    )
    # --- visibilité pixel par pixel ---
    core = r <= CORE_PX
    signal = img - bkg
    if sigma is not None:
        # incertitude effective = bruit du détecteur (VARIANCE) + bruit du fond mesuré
        # (en champ dense, VARIANCE seule sous-estime le bruit : confusion de sources)
        sig_eff = np.sqrt(sigma ** 2 + (rms or 0.0) ** 2)
        valid = np.isfinite(img) & np.isfinite(sigma) & (sigma > 0) & ~bad
        pix_snr = np.where(valid, signal / np.where(valid, sig_eff, 1.0), np.nan)
    else:
        valid = np.isfinite(img) & ~bad
        pix_snr = np.where(valid, signal / (rms or 1.0), np.nan)
    sig_pix = valid & (pix_snr >= PIXEL_SNR_SIG)
    n_core = int(core.sum())
    core_valid = valid & core
    core_valid_frac = core_valid.sum() / n_core if n_core else 0.0
    core_snr = float(np.nanmedian(pix_snr[core_valid])) if core_valid.any() else None
    pos = core_valid & (signal > 0)
    core_rel = (float(np.median(sig_eff[pos] / signal[pos]))
                if sigma is not None and pos.any() else None)
    n_sig = int((sig_pix & ap).sum())
    wing_sig = int((sig_pix & ap & ~core).sum())
    vis = dict(core_valid_frac=round(float(core_valid_frac), 3),
               core_pixel_snr=None if core_snr is None else round(core_snr, 1),
               core_rel_uncertainty=None if core_rel is None else round(core_rel, 4),
               n_significant_pixels=n_sig, wing_significant_pixels=wing_sig)

    metrics = dict(**phys, **vis, wavelength_um=wl, bandwidth_um=bw, x=x, y=y,
                   snr=None if snr is None else round(snr, 1), flux_mjysr_px=round(flux, 4),
                   peak=peak, centroid_offset_px=None if offset is None else round(offset, 2),
                   saturated=saturated, artifact_frac=round(artifact_frac, 3),
                   dead_frac_local=round(dead_frac_local, 3),
                   background_rms=None if rms is None else round(rms, 5))

    if artifact_frac > MAX_ARTIFACT_FRAC:
        return FrameQuality(**base, **metrics, status="artefact", keep=False,
                            reason=f"{artifact_frac:.0%} de l'ouverture touchée par un artefact")
    if snr is None or snr < SNR_MIN:
        return FrameQuality(**base, **metrics, status="invisible", keep=False,
                            reason=f"S/N = {snr if snr is None else round(snr, 1)} < {SNR_MIN}")
    if saturated:
        if wing_sig < MIN_WING_SIG_PIXELS:
            return FrameQuality(**base, **metrics, status="incertaine", keep=False,
                                reason=f"cœur saturé et seulement {wing_sig} pixels d'ailes "
                                       f"fiables (< {MIN_WING_SIG_PIXELS}) : position non mesurable")
        return FrameQuality(**base, **metrics, status="saturee", keep=True,
                            reason=f"cœur saturé : affichage OK, position mesurée sur "
                                   f"{wing_sig} pixels d'ailes fiables")
    if n_sig < MIN_SIG_PIXELS:
        return FrameQuality(**base, **metrics, status="pic_isole", keep=False,
                            reason=f"seulement {n_sig} pixel(s) significatif(s) : pic isolé "
                                   "(rayon cosmique, pixel chaud ?) plutôt qu'un objet")
    if core_valid_frac < MIN_CORE_VALID:
        return FrameQuality(**base, **metrics, status="incertaine", keep=False,
                            reason=f"{core_valid_frac:.0%} des pixels du cœur ont une valeur et "
                                   "une incertitude utilisables")
    if core_rel is not None and core_rel > MAX_CORE_REL_UNC and snr >= SNR_CLEAR:
        return FrameQuality(**base, **metrics, status="faible", keep=True,
                            reason=f"S/N global {snr:.0f} mais pixels du cœur incertains "
                                   f"({core_rel:.0%} d'incertitude relative)")
    if offset is not None and offset > MAX_OFFSET_PX and snr >= SNR_CLEAR:
        return FrameQuality(**base, **metrics, status="decalee", keep=True,
                            reason=f"centroïde à {offset:.1f} px de la position attendue "
                                   "(source voisine ou erreur de position ?)")
    if snr < SNR_CLEAR:
        return FrameQuality(**base, **metrics, status="faible", keep=True,
                            reason=f"S/N = {snr:.1f} (entre {SNR_MIN} et {SNR_CLEAR})")
    return FrameQuality(**base, **metrics, status="nette", keep=True, reason="objet net")


def position_at(target, mjd: float) -> tuple[float, float]:
    """Position de la cible à la date de l'image (propagée si mouvement propre connu)."""
    if not (target.pmra and target.pmdec):
        return target.ra_deg, target.dec_deg
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u
    from app.core.target import MISSION_MID_EPOCH
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c = SkyCoord(target.ra_deg * u.deg, target.dec_deg * u.deg,
                     pm_ra_cosdec=target.pmra * u.mas / u.yr, pm_dec=target.pmdec * u.mas / u.yr,
                     obstime=Time(MISSION_MID_EPOCH, format="jyear"))
        c = c.apply_space_motion(new_obstime=Time(mjd, format="mjd"))
    return float(c.ra.deg), float(c.dec.deg)


logging.getLogger("astropy").setLevel(logging.WARNING)


# --- Étape complète : télécharger les images sélectionnées puis les filtrer -----------
class ScreenResult(BaseModel):
    target_label: str
    n_selected: int
    n_downloaded: int
    n_download_failed: int
    n_kept: int
    by_status: dict[str, int]
    kept_visits: int
    frames: list[FrameQuality]
    download_errors: dict[str, str]


def screen_selection(selection, fetcher=None, progress=None) -> ScreenResult:
    """selection : SelectionResult (étape 1b). Télécharge et contrôle chaque image."""
    from app.core.fetch import fetch_many
    fetcher = fetcher or fetch_many
    target = selection.target
    recs = selection.selected
    fetched = fetcher([r.cutout_url for r in recs], progress=progress)

    frames: list[FrameQuality] = []
    errors: dict[str, str] = {}
    for r in recs:
        path, err = fetched.get(r.cutout_url, (None, "non téléchargé"))
        if path is None:
            errors[r.obs_id + "/" + (r.detector or "?")] = err or "erreur inconnue"
            continue
        ra, dec = position_at(target, r.t_mid_mjd)
        try:
            q = screen_frame(Path(path), ra, dec, obs_id=r.obs_id, detector=r.detector,
                             date_utc=r.date_utc)
        except Exception as exc:  # noqa: BLE001 — fichier corrompu, extension manquante...
            q = FrameQuality(obs_id=r.obs_id, detector=r.detector, date_utc=r.date_utc,
                             path=str(path), status="illisible", keep=False,
                             reason=f"{type(exc).__name__}: {str(exc)[:120]}")
        frames.append(q)

    by_status: dict[str, int] = {}
    for f in frames:
        by_status[f.status] = by_status.get(f.status, 0) + 1
    kept = [f for f in frames if f.keep]
    kept_visits = sum(
        1 for v in selection.visits
        if any(f.date_utc and v.start <= f.date_utc[:10] <= v.end for f in kept))
    return ScreenResult(
        target_label=target.label, n_selected=len(recs), n_downloaded=len(frames),
        n_download_failed=len(errors), n_kept=len(kept), by_status=by_status,
        kept_visits=kept_visits, frames=frames, download_errors=errors)



# --- Tableaux complets d'une image (pour l'API /api/frame/{frame_id}) -------------------
def frame_arrays(path: Path) -> dict:
    """Valeurs de pixels, incertitude et flags d'un cutout, prêts pour du JSON."""
    from astropy.io import fits
    from astropy.wcs import WCS, FITSFixedWarning
    with fits.open(path) as h, warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        hdr = h["IMAGE"].header
        img = h["IMAGE"].data.astype(float)
        zodi = h["ZODI"].data.astype(float) if "ZODI" in h else np.zeros(img.shape)
        var = h["VARIANCE"].data.astype(float) if "VARIANCE" in h else np.full(img.shape, np.nan)
        flags = h["FLAGS"].data.astype(np.int64) if "FLAGS" in h else np.zeros(img.shape, np.int64)
        names = flag_names(h["FLAGS"].header) if "FLAGS" in h else {}
        wcs_hdr = {k: v for k, v in WCS(hdr).to_header(relax=True).items()}
        wl_c, bw_c = wavelength_at(h, (img.shape[1] - 1) / 2, (img.shape[0] - 1) / 2)

    def clean(a):
        return [[None if not np.isfinite(v) else round(float(v), 5) for v in row] for row in a]

    return {
        "frame_id": Path(path).stem,
        "shape": list(img.shape),
        "unit": hdr.get("BUNIT"),
        "date_obs": hdr.get("DATE-OBS"),
        "mjd_obs": hdr.get("MJD-OBS"),
        "detector": hdr.get("DETECTOR"),
        "wavelength_center_um": wl_c,
        "bandwidth_center_um": bw_c,
        "flag_bits": {str(b): n for b, n in sorted(names.items())},
        "wcs": wcs_hdr,
        "image": clean(img),                    # brillance de surface brute (MJy/sr)
        "zodi": clean(zodi),                    # modèle de lumière zodiacale (MJy/sr)
        "image_minus_zodi": clean(img - zodi),
        "sigma": clean(np.sqrt(np.clip(var, 0, None))),   # incertitude 1 sigma (MJy/sr)
        "flags": flags.tolist(),                # entier par pixel, bits décodés via flag_bits
    }
