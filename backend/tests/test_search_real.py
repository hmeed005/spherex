"""Test sur une VRAIE réponse SIA d'IRSA (5 images DR1, zone de l'étoile de Barnard)."""
from pathlib import Path

import pytest
from astropy.table import Table

from app.core import config
from app.core.search import coverage, parse_polygon, search_images
from app.core.target import TargetRequest, resolve_target

CSV = Path(__file__).parent / "data" / "sia_barnard_dr1.csv"


@pytest.fixture(autouse=True)
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.cache.DB_PATH", tmp_path / "t.sqlite")
    monkeypatch.setattr(config, "COLLECTIONS", ["spherex_dr1"])
    monkeypatch.setattr(config, "DEMO_MODE", False)


def read_irsa_csv(path):
    """Le CSV d'IRSA n'échappe pas le JSON de 'cloud_access' (virgules) : lecture manuelle."""
    lines = path.read_text().strip().splitlines()
    header = lines[0].split(",")
    i_cloud = header.index("cloud_access")
    rows = []
    for line in lines[1:]:
        start = line.index('{"aws"')
        end = line.rindex("}") + 1
        before = line[:start - 1].split(",")
        after = line[end + 1:].split(",")
        fields = before + [line[start:end]] + after
        assert len(fields) == len(header) and len(before) == i_cloud
        rows.append(fields)
    return Table(rows=rows, names=header, dtype=[str] * len(header))


def real_sia(ra, dec, radius, collection):
    return read_irsa_csv(CSV)


def test_real_irsa_rows_are_parsed():
    t = resolve_target(TargetRequest(name="Barnard"))
    r = search_images(t, sia=real_sia)
    assert r.n_images >= 1
    img = r.images[0]
    assert img.release == "dr1"
    assert img.detector in {f"D{i}" for i in range(1, 7)}
    assert img.date_utc.startswith("2025-08")          # MJD 60902 = août 2025
    assert img.wl_min_um > 0.7 and img.wl_max_um < 5.1
    assert img.image_url.startswith("https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/")
    assert "nasa-irsa-spherex" in img.cloud_access
    assert img.size_mb > 50                            # ~63 Mo par image complète


def test_polygon_and_coverage():
    s = ("POLYGON ICRS 266.69818339020907 5.472469522295728 270.1773378537016 5.149486050441448 "
         "269.9973138381142 1.660074934294828 266.5011710028342 1.9904353173956755 "
         "266.69818339020907 5.472469522295728")
    assert len(parse_polygon(s)) == 4
    inside = resolve_target(TargetRequest(ra="268.3", dec="3.5"))
    outside = resolve_target(TargetRequest(ra="275.0", dec="3.5"))
    assert coverage(s, inside) == (True, True)
    assert coverage(s, outside)[0] is False
