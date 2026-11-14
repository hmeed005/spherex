"""Inspecter visuellement de vraies images SPHEREx :
    python -m scripts.preview Barnard          (détecteur D2 par défaut)
    python -m scripts.preview Barnard D4 3     (détecteur D4, 3 images par passage)

Télécharge quelques cutouts (cache local), puis crée :
  - cache/preview/<cible>_<det>.png : planche des images, une colonne par passage,
    avec la position de la cible marquée (propagée à la date si le mouvement propre est connu) ;
  - cache/preview/<cible>_<det>_blink.gif : animation (clignotement) d'une image par passage.
"""
import hashlib
import sys
import time
import urllib.error
import http.client
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

from app.core import config
from app.core.search import search_images
from app.core.select import select_images
from app.core.target import CATALOG_EPOCH, TargetRequest, resolve_target

# Bits FLAGS qui ne sont PAS des défauts : 2 (SUR_ERROR, toléré par IRSA) et 21 (SOURCE)
OK_BITS = (1 << 2) | (1 << 21)
CUTOUT_DIR = Path(config.CACHE_DIR) / "cutouts"
OUT_DIR = Path(config.CACHE_DIR) / "preview"


def fetch_cutout(url: str, retries: int = 3) -> Path:
    """Télécharge un cutout (avec cache disque et tentatives répétées)."""
    CUTOUT_DIR.mkdir(parents=True, exist_ok=True)
    path = CUTOUT_DIR / (hashlib.sha1(url.encode()).hexdigest()[:20] + ".fits")
    if path.exists() and path.stat().st_size > 0:
        return path
    for attempt in range(retries):
        try:
            with fits.open(url, memmap=False, cache=False) as hdul:
                hdul.writeto(path, overwrite=True)
            return path
        except (TimeoutError, urllib.error.URLError, http.client.IncompleteRead, OSError) as exc:
            if attempt == retries - 1:
                raise
            print(f"      tentative {attempt + 1} échouée ({exc}), nouvel essai...")
            time.sleep(5 * (attempt + 1))
    return path


def load_frame(path: Path, ra: float, dec: float):
    """Image nettoyée (zodiacal retiré, pixels défectueux masqués) + infos."""
    with fits.open(path) as h:
        img = h["IMAGE"].data.astype(float)
        hdr = h["IMAGE"].header
        if "ZODI" in h:
            img = img - h["ZODI"].data
        bad_frac = 0.0
        if "FLAGS" in h:
            flags = h["FLAGS"].data.astype(np.int64)
            bad = (flags & ~OK_BITS) != 0
            bad_frac = float(bad.mean())
            img[bad] = np.nan
        wcs = WCS(hdr)
        x, y = wcs.world_to_pixel(SkyCoord(ra * u.deg, dec * u.deg))
        wl = None
        try:  # longueur d'onde au pixel de la cible (WCS spectral "W")
            sw = WCS(header=hdr, fobj=h, key="W")
            sw.sip = None
            wl = float(np.ravel(sw.pixel_to_world_values(float(x), float(y)))[0])
        except Exception:  # noqa: BLE001
            pass
    return img, float(x), float(y), wl, bad_frac


def position_at(t, mjd):
    """Position de la cible à la date de l'image (si mouvement propre connu)."""
    if not (t.pmra and t.pmdec):
        return t.ra_deg, t.dec_deg
    from app.core.target import MISSION_MID_EPOCH
    c = SkyCoord(t.ra_deg * u.deg, t.dec_deg * u.deg, pm_ra_cosdec=t.pmra * u.mas / u.yr,
                 pm_dec=t.pmdec * u.mas / u.yr, obstime=Time(MISSION_MID_EPOCH, format="jyear"))
    c = c.apply_space_motion(new_obstime=Time(mjd, format="mjd"))
    return float(c.ra.deg), float(c.dec.deg)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "Barnard"
    det = sys.argv[2] if len(sys.argv) > 2 else "D2"
    per_visit = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from astropy.visualization import AsinhStretch, ImageNormalize, PercentileInterval

    t = resolve_target(TargetRequest(name=name))
    sel = select_images(search_images(t), detector=det, max_per_visit_detector=per_visit)
    visits = [v for v in sel.visits if not v.minor] or sel.visits
    print(f"{t.label} / {det} : {len(visits)} passages principaux, "
          f"{per_visit} image(s) par passage")

    frames = []  # (visit, record, img, x, y, wl, bad)
    for v in visits:
        recs = [r for r in sel.selected
                if v.start <= r.date_utc[:10] <= v.end][:per_visit]
        for r in recs:
            print(f"   {r.date_utc[:16]}  {r.obs_id}  téléchargement...", end=" ", flush=True)
            try:
                p = fetch_cutout(r.cutout_url)
                ra, dec = position_at(t, r.t_mid_mjd)
                img, x, y, wl, bad = load_frame(p, ra, dec)
                frames.append((v, r, img, x, y, wl, bad))
                wl_txt = f"{wl:.3f} µm" if wl else "λ ?"
                print(f"OK  {img.shape[1]}x{img.shape[0]} px, {wl_txt}, {bad:.0%} masqué")
            except Exception as exc:  # noqa: BLE001
                print(f"ECHEC ({type(exc).__name__}: {str(exc)[:80]})")

    if not frames:
        print("Aucune image téléchargée.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = name.lower().replace(" ", "_")
    # même étirement de contraste pour toutes les images (sinon faux changements d'éclat)
    ref = np.concatenate([f[2][np.isfinite(f[2])].ravel() for f in frames])
    norm = ImageNormalize(ref, interval=PercentileInterval(99.5), stretch=AsinhStretch(0.1))

    ncol = len(visits)
    nrow = max(sum(1 for f in frames if f[0] is v) for v in visits)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.2 * ncol, 3.4 * nrow), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for c, v in enumerate(visits):
        for r_i, f in enumerate([f for f in frames if f[0] is v]):
            _, rec, img, x, y, wl, bad = f
            ax = axes[r_i][c]
            ax.imshow(img, origin="lower", cmap="gray", norm=norm)
            ax.plot(x, y, marker="o", ms=14, mfc="none", mec="red", mew=1.2)
            wl_txt = f"{wl:.3f} µm" if wl else ""
            ax.set_title(f"{rec.date_utc[:10]}  {wl_txt}", fontsize=8)
    fig.suptitle(f"{t.label} — SPHEREx {det} — cercle rouge = position attendue", fontsize=10)
    fig.tight_layout()
    sheet = OUT_DIR / f"{slug}_{det}.png"
    fig.savefig(sheet, dpi=110)
    plt.close(fig)
    print(f"\nPlanche : {sheet}")

    # animation : la première image de chaque passage
    try:
        from PIL import Image
        gif_frames = []
        for v in visits:
            f = next((f for f in frames if f[0] is v), None)
            if f is None:
                continue
            fig, ax = plt.subplots(figsize=(4, 4.3))
            ax.imshow(f[2], origin="lower", cmap="gray", norm=norm)
            ax.plot(f[3], f[4], marker="o", ms=16, mfc="none", mec="red", mew=1.2)
            ax.set_title(f"{f[1].date_utc[:10]}", fontsize=10)
            ax.axis("off")
            fig.canvas.draw()
            gif_frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
            plt.close(fig)
        if len(gif_frames) > 1:
            gif = OUT_DIR / f"{slug}_{det}_blink.gif"
            gif_frames[0].save(gif, save_all=True, append_images=gif_frames[1:],
                               duration=700, loop=0)
            print(f"Animation : {gif}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
