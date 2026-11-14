"""Tests de Fetch + Screen : une VRAIE image SPHEREx (Barnard, D2, 30/08/2025) + cas simulés."""
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from app.core import config, fetch
from app.core.screen import (BLOOM, GHOST, OVERFLOW, SOURCE, position_at, screen_frame)
from app.core.target import TargetRequest, resolve_target

REAL = Path(__file__).parent / "data" / "barnard_D2_20250830.fits"
BARNARD = resolve_target(TargetRequest(name="Barnard"))


# ---------- vraie image ----------
def test_real_barnard_is_saturated_but_kept():
    mjd = fits.getheader(REAL, "IMAGE")["MJD-OBS"]
    ra, dec = position_at(BARNARD, mjd)
    q = screen_frame(REAL, ra, dec)
    assert q.status == "saturee" and q.keep
    assert q.snr > 100
    assert q.centroid_offset_px < 1.0          # position prédite à moins d'1 pixel
    assert 1.4 < q.wavelength_um < 1.6         # D2, mesuré : 1,496 µm


def test_real_empty_position_is_invisible():
    q = screen_frame(REAL, BARNARD.ra_deg + 0.02, BARNARD.dec_deg + 0.02)
    assert q.status == "invisible" and not q.keep


def test_real_position_outside_cutout():
    q = screen_frame(REAL, BARNARD.ra_deg + 1.0, BARNARD.dec_deg)
    assert q.status == "hors_image"


# ---------- images simulées ----------
def fake(tmp_path, amp=50.0, flag_bits=0, flag_core=False, noise=0.05):
    rng = np.random.default_rng(0)
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [150.0, 2.0]
    w.wcs.crpix = [30, 30]
    w.wcs.cdelt = [-6.15 / 3600, 6.15 / 3600]
    yy, xx = np.mgrid[:59, :59]
    img = rng.normal(0.5, noise, (59, 59)) + amp * np.exp(-((xx - 29) ** 2 + (yy - 29) ** 2) / 2)
    flags = np.full((59, 59), 1 << SOURCE, np.int32)
    if flag_core:
        flags[27:32, 27:32] |= flag_bits
    hdul = fits.HDUList([
        fits.PrimaryHDU(),
        fits.ImageHDU(img.astype("f4"), w.to_header(), name="IMAGE"),
        fits.ImageHDU(flags, name="FLAGS"),
        fits.ImageHDU(np.full((59, 59), noise ** 2, "f4"), name="VARIANCE"),
        fits.ImageHDU(np.full((59, 59), 0.5, "f4"), name="ZODI"),
    ])
    p = tmp_path / "f.fits"
    hdul.writeto(p, overwrite=True)
    return p


def test_sim_clear(tmp_path):
    assert screen_frame(fake(tmp_path), 150.0, 2.0).status == "nette"


def test_sim_faint(tmp_path):
    assert screen_frame(fake(tmp_path, amp=0.35), 150.0, 2.0).status == "faible"


def test_sim_invisible(tmp_path):
    assert screen_frame(fake(tmp_path, amp=0.0), 150.0, 2.0).status == "invisible"


def test_sim_ghost_rejected(tmp_path):
    q = screen_frame(fake(tmp_path, flag_bits=1 << GHOST, flag_core=True), 150.0, 2.0)
    assert q.status == "artefact" and not q.keep


def test_sim_saturated_kept(tmp_path):
    bits = (1 << OVERFLOW) | (1 << BLOOM)
    q = screen_frame(fake(tmp_path, flag_bits=bits, flag_core=True), 150.0, 2.0)
    assert q.status == "saturee" and q.keep


def test_sim_offset(tmp_path):
    q = screen_frame(fake(tmp_path), 150.0 + 3 * 6.15 / 3600, 2.0)   # visée à 3 px à côté
    assert q.status in {"decalee", "nette"} and q.centroid_offset_px > 1.5


# ---------- téléchargement ----------
def test_fetch_retries_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "CUTOUT_DIR", tmp_path)
    monkeypatch.setattr(config, "DEMO_MODE", False)
    calls = {"n": 0}

    def flaky(url, dest):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("HTTP Error 503: Service Unavailable")
        dest.write_bytes(b"x")

    path, err = fetch.fetch_one("https://x/a.fits", downloader=flaky, sleep=lambda s: None)
    assert path is not None and err is None and calls["n"] == 3
    # deuxième appel : servi par le cache, aucun téléchargement
    fetch.fetch_one("https://x/a.fits", downloader=flaky, sleep=lambda s: None)
    assert calls["n"] == 3


def test_fetch_no_retry_on_422(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "CUTOUT_DIR", tmp_path)
    monkeypatch.setattr(config, "DEMO_MODE", False)
    calls = {"n": 0}

    def no_overlap(url, dest):
        calls["n"] += 1
        raise OSError("HTTP Error 422: Arrays do not overlap.")

    path, err = fetch.fetch_one("https://x/b.fits", downloader=no_overlap, sleep=lambda s: None)
    assert path is None and "422" in err and calls["n"] == 1


def test_real_physical_values_flags_and_uncertainty():
    from app.core.screen import frame_arrays
    mjd = fits.getheader(REAL, "IMAGE")["MJD-OBS"]
    ra, dec = position_at(BARNARD, mjd)
    q = screen_frame(REAL, ra, dec)
    assert q.unit.replace(" ", "") == "MJy/sr"
    assert "OVERFLOW" in q.flags_at_target and "BLOOM" in q.flags_at_target
    assert q.flags_in_aperture["BLOOM"] > 0
    assert q.flags_image_frac["SOURCE"] > 0.99          # champ dense
    assert q.value_at_target is None and q.n_nan_in_aperture > 0   # cœur saturé = NaN
    assert q.flux_err_mjysr_px > 0 and 0 < q.sigma_median < 1
    a = frame_arrays(REAL)
    assert a["shape"] == [59, 59]
    assert len(a["image"]) == 59 and len(a["sigma"][0]) == 59 and len(a["flags"]) == 59
    assert a["flag_bits"]["21"] == "SOURCE"


def test_sim_single_hot_pixel_is_not_an_object(tmp_path):
    p = fake(tmp_path, amp=0.0)
    with fits.open(p, mode="update") as h:
        h["IMAGE"].data[29, 29] += 5.0           # un seul pixel très brillant
    q = screen_frame(p, 150.0, 2.0)
    assert q.status in {"pic_isole", "invisible"} and not q.keep
    assert q.n_significant_pixels < 3


def test_sim_core_without_values_is_uncertain(tmp_path):
    p = fake(tmp_path, amp=50.0)
    with fits.open(p, mode="update") as h:
        h["IMAGE"].data[28:31, 28:31] = np.nan   # cœur sans valeur, mais PAS saturé
    q = screen_frame(p, 150.0, 2.0)
    assert q.status == "incertaine" and not q.keep and q.core_valid_frac < 0.5


def test_real_barnard_wings_are_reliable():
    mjd = fits.getheader(REAL, "IMAGE")["MJD-OBS"]
    ra, dec = position_at(BARNARD, mjd)
    q = screen_frame(REAL, ra, dec)
    assert q.wing_significant_pixels >= 6 and q.n_significant_pixels >= 10
