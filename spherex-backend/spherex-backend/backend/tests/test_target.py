import pytest
from fastapi.testclient import TestClient

from app.core.target import TargetRequest, resolve_target
from app.main import app

client = TestClient(app)


def test_decimal_degrees():
    t = resolve_target(TargetRequest(ra="269.452", dec="4.693", size_arcmin=6))
    assert t.ra_deg == pytest.approx(269.452)
    assert t.size_px == 59                      # 6' / 6.15" ≈ 59 px
    assert t.resolved_by == "coordinates"


def test_sexagesimal_matches_decimal():
    a = resolve_target(TargetRequest(ra="17h57m48.5s", dec="+04d41m36s"))
    assert a.ra_deg == pytest.approx(269.452, abs=1e-3)
    assert a.dec_deg == pytest.approx(4.6933, abs=1e-3)


def test_ra_wraps_into_0_360():
    assert 0 <= resolve_target(TargetRequest(ra="-10", dec="0")).ra_deg < 360


def test_demo_name_offline_with_pm_warning():
    t = resolve_target(TargetRequest(name="Barnard's star"))
    assert t.resolved_by == "demo_catalog" and t.pmdec > 10000
    assert any("Mouvement propre" in w for w in t.warnings)
    # centrée sur la position 2025.9 : ~10,36"/an x 25,9 ans ≈ 268" plus au nord
    assert (t.dec_deg - 4.693364) * 3600 == pytest.approx(268.4, abs=2)


def test_galactic_plane_warning():
    t = resolve_target(TargetRequest(ra="266.4", dec="-28.9"))  # centre galactique
    assert any("champ dense" in w for w in t.warnings)


def test_same_field_same_cache_key():
    a = resolve_target(TargetRequest(ra="269.45200", dec="4.69300"))
    b = resolve_target(TargetRequest(ra="269.452001", dec="4.693001"))
    assert a.cache_key == b.cache_key


@pytest.mark.parametrize("params", [
    {"ra": "269.4"},                                  # dec manquante
    {},                                               # rien
    {"ra": "abc", "dec": "xyz"},                      # illisible
    {"ra": "10", "dec": "95"},                        # dec hors limites
    {"ra": "10", "dec": "10", "size_arcmin": 30},     # zone trop grande
])
def test_api_rejects_bad_input(params):
    assert client.get("/api/target", params=params).status_code == 422


def test_api_ok():
    r = client.get("/api/target", params={"name": "nep", "size_arcmin": 4})
    assert r.status_code == 200
    assert any("pôle écliptique" in w for w in r.json()["warnings"])
