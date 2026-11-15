"""Tests de l'étape Align : pointage et orientation différents -> même vue du ciel."""
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from app.core.align import align_group, centroid, make_grid, reproject_frame
from app.core.group import GroupFrame, WavelengthGroup
from app.core.screen import FrameQuality, SOURCE
from app.core.target import TargetRequest, resolve_target

RA0, DEC0 = 150.0, 2.0
STARS = [(150.025, 2.02), (149.975, 1.985), (150.03, 1.975), (149.97, 2.025)]   # à ~15-20 px du centre
PIX = 6.15 / 3600


def make_frame(path, crval, rot_deg, star_extra=None):
    """Cutout simulé : pointage `crval`, tourné de `rot_deg`, étoiles aux positions STARS."""
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = list(crval)
    w.wcs.crpix = [30.0, 30.0]
    th = np.radians(rot_deg)
    w.wcs.cd = np.array([[-PIX * np.cos(th), PIX * np.sin(th)], [PIX * np.sin(th), PIX * np.cos(th)]])
    yy, xx = np.mgrid[:59, :59]
    img = np.full((59, 59), 0.5)
    for ra, dec in STARS + ([star_extra] if star_extra else []):
        x, y = w.world_to_pixel_values(ra, dec)
        img += 40 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 0.6 ** 2))
    fits.HDUList([
        fits.PrimaryHDU(),
        fits.ImageHDU(img.astype("f4"), w.to_header(), name="IMAGE"),
        fits.ImageHDU(np.full((59, 59), 1 << SOURCE, np.int32), name="FLAGS"),
        fits.ImageHDU(np.full((59, 59), 1e-4, "f4"), name="VARIANCE"),
        fits.ImageHDU(np.full((59, 59), 0.5, "f4"), name="ZODI"),
    ]).writeto(path, overwrite=True)
    return w


def test_grid_is_north_up_east_left():
    g = make_grid(RA0, DEC0, 59)
    x0, y0 = g.world_to_pixel_values(RA0, DEC0)
    xn, yn = g.world_to_pixel_values(RA0, DEC0 + 0.01)       # plus au nord
    xe, ye = g.world_to_pixel_values(RA0 + 0.01, DEC0)       # plus à l'est
    assert abs(x0 - 29) < 1e-6 and abs(y0 - 29) < 1e-6      # centre de la grille
    assert yn > y0 and abs(xn - x0) < 1e-6                   # nord en haut
    assert xe < x0                                           # est à gauche


def test_rotated_and_shifted_pointings_give_same_sky_positions(tmp_path):
    """Même étoile, deux pointages (dont un tourné de 180°) : même pixel de grille."""
    grid = make_grid(RA0, DEC0, 59)
    make_frame(tmp_path / "a.fits", (RA0, DEC0), 0)
    make_frame(tmp_path / "b.fits", (RA0 + 0.01, DEC0 - 0.008), 180)
    a = reproject_frame(tmp_path / "a.fits", grid, (59, 59))
    b = reproject_frame(tmp_path / "b.fits", grid, (59, 59))
    for ra, dec in STARS:
        gx, gy = grid.world_to_pixel_values(ra, dec)
        ca, cb = centroid(a["image"], float(gx), float(gy)), centroid(b["image"], float(gx), float(gy))
        assert np.hypot(ca[0] - cb[0], ca[1] - cb[1]) < 0.15
        assert np.hypot(ca[0] - gx, ca[1] - gy) < 0.15


def test_align_group_detects_real_motion_not_pointing(tmp_path):
    target = resolve_target(TargetRequest(ra=str(RA0), dec=str(DEC0), size_arcmin=6))
    # cible qui se déplace de 2 pixels vers le nord entre les deux dates
    p1 = tmp_path / "f1.fits"
    p2 = tmp_path / "f2.fits"
    make_frame(p1, (RA0, DEC0), 0, star_extra=(RA0, DEC0))
    make_frame(p2, (RA0 - 0.01, DEC0 + 0.01), 180, star_extra=(RA0, DEC0 + 2 * PIX))
    fq = {k: FrameQuality(frame_id=k, obs_id=k, path=str(p), status="nette", keep=True,
                          reason="", detector="D2", wavelength_um=1.5)
          for k, p in (("f1", p1), ("f2", p2))}
    group = WavelengthGroup(
        id="D2_1.500", detector="D2", wavelength_um=1.5, wl_min_um=1.5, wl_max_um=1.5,
        max_delta_rel=0, n_epochs=2, n_candidates=2, span_days=180, max_gap_days=180,
        usable_for_motion=False,
        frames=[GroupFrame(frame_id="f1", obs_id="f1", date_utc="2025-08-30T00:00:00Z", visit=0,
                           wavelength_um=1.5, delta_wl_rel=0, status="nette", snr=100),
                GroupFrame(frame_id="f2", obs_id="f2", date_utc="2026-03-01T00:00:00Z", visit=1,
                           wavelength_um=1.5, delta_wl_rel=0, status="nette", snr=100)])
    r = align_group(target, group, fq, out_dir=tmp_path / "out", render=True)
    assert r.alignment_ok and r.max_field_shift_px < 0.2       # étoiles fixes immobiles
    assert abs(r.target_track_px - 2.0) < 0.3                  # la cible a bougé de 2 px
    m1, m2 = r.frames[0].target_measured_px, r.frames[1].target_measured_px
    assert m2[1] - m1[1] > 1.7                                 # ... vers le nord (haut)
    assert Path(r.gif).exists() and Path(r.sheet).exists()
