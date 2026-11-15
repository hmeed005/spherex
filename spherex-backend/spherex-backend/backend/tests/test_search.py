"""Tests de l'étape Search avec un faux service IRSA (aucun accès réseau)."""
import pytest
from astropy.table import Table

from app.core import config
from app.core.search import search_images
from app.core.target import TargetRequest, resolve_target


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.cache.DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "COLLECTIONS", ["spherex_dr1", "spherex_qr3"])


def fake_table(collection):
    base = "https://irsa.ipac.caltech.edu/ibe/data/spherex"
    rel = collection.split("_")[1]
    rows = [  # 2 dates, 2 détecteurs, + 1 doublon + 1 produit non-FITS
        ("obsA", "SPHEREx-D1", 60800.10, 60800.11, 0.75e-6, 1.09e-6, f"{base}/{rel}/a_D1.fits"),
        ("obsA", "SPHEREx-D2", 60800.10, 60800.11, 1.10e-6, 1.62e-6, f"{base}/{rel}/a_D2.fits"),
        ("obsA", "SPHEREx-D2", 60800.10, 60800.11, 1.10e-6, 1.62e-6, f"{base}/{rel}/a_D2.fits"),
        ("obsB", "SPHEREx-D2", 60990.50, 60990.51, 1.10e-6, 1.62e-6, f"{base}/{rel}/b_D2.fits"),
        ("aux", "SPHEREx-D2", 60990.50, 60990.51, 1.10e-6, 1.62e-6, f"{base}/{rel}/readme.txt"),
    ]
    rows = [(f"{o}_{rel}", *r) for o, *r in rows]
    t = Table(rows=rows, names=["obs_id", "energy_bandpassname", "t_min", "t_max",
                                "em_min", "em_max", "access_url"])
    t["access_estsize"] = 70000.0
    return t


def fake_sia(ra, dec, radius, collection):
    fake_sia.calls += 1
    return fake_table(collection)


fake_sia.calls = 0


def target():
    return resolve_target(TargetRequest(name="Barnard"))


def test_search_parses_dedups_and_sorts():
    r = search_images(target(), sia=fake_sia)
    # 2 collections x 3 images uniques (doublon et .txt exclus)
    assert r.n_images == 6
    assert r.by_release == {"dr1": 3, "qr3": 3}
    assert r.by_detector == {"D1": 2, "D2": 4}
    assert r.n_days == 2 and r.first_date < r.last_date
    mids = [i.t_mid_mjd for i in r.images]
    assert mids == sorted(mids)
    img = r.images[0]
    assert img.wl_min_um == pytest.approx(0.75)
    assert "center=269.446" in img.cutout_url and "size=0.1" in img.cutout_url
    assert img.size_mb == pytest.approx(68.4, abs=0.1)


def test_second_call_uses_cache():
    fake_sia.calls = 0
    search_images(target(), sia=fake_sia)
    r = search_images(target(), sia=fake_sia)
    assert r.source == "cache" and fake_sia.calls == 2   # 2 collections, 1 seule fois


def test_partial_failure_is_reported_not_cached():
    def flaky(ra, dec, radius, collection):
        if collection == "spherex_qr3":
            raise TimeoutError("IRSA lent")
        return fake_table(collection)
    r = search_images(target(), sia=flaky)
    assert r.n_images == 3 and any("qr3" in e for e in r.errors)
    assert search_images(target(), sia=fake_sia).source == "irsa"  # pas figé en cache


def test_total_failure_raises():
    def down(*a):
        raise ConnectionError("down")
    with pytest.raises(ConnectionError):
        search_images(target(), sia=down)


def test_demo_mode_without_cache(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", True)
    with pytest.raises(RuntimeError):
        search_images(target(), sia=fake_sia)


def test_deep_collections_are_tagged(monkeypatch):
    monkeypatch.setattr(config, "COLLECTIONS", ["spherex_dr1", "spherex_dr1_deep"])
    r = search_images(target(), sia=fake_sia)
    assert r.by_survey == {"wide": 3, "deep": 3}


def test_small_search_radius_is_used():
    seen = {}
    def spy(ra, dec, radius, collection):
        seen["radius"] = radius
        return fake_table(collection)
    search_images(target(), sia=spy)
    assert seen["radius"] == pytest.approx(1 / 3600)


def test_irsa_down_falls_back_to_cache():
    search_images(target(), sia=fake_sia)                       # 1re recherche : en cache
    def down(*a):
        raise ConnectionError("502 Proxy Error")
    r = search_images(target(), refresh=True, sia=down)          # IRSA en panne
    assert r.source == "cache" and r.n_images == 6
    assert "IRSA indisponible" in r.errors[0]
