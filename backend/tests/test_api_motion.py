"""API /api/motion : deux demandes identiques en même temps partagent UN seul calcul."""
import asyncio
import time
from types import SimpleNamespace

import httpx

from app.core.measure import DisplayPlan, fit_motion
from app.main import app
from app.routers import images


def test_identical_concurrent_requests_share_one_computation(monkeypatch, tmp_path):
    calls = []

    async def fake_search(name, ra, dec, size_arcmin, refresh):
        return SimpleNamespace(target=SimpleNamespace(cache_key="test-dedupe", label="Test"))

    def slow_pipeline(search, detector, tolerance, mpvd, max_total, run_dir=None):
        calls.append(1)
        time.sleep(0.5)                       # calcul long (téléchargements…)
        empty = fit_motion([])
        plan = DisplayPlan(comparisons=[], conflicted_groups=[], sequences=[], summary="")
        return empty, empty, plan, None

    monkeypatch.setattr(images, "_search", fake_search)
    monkeypatch.setattr(images, "_motion_pipeline", slow_pipeline)
    monkeypatch.setattr(images.config, "CACHE_DIR", tmp_path)

    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            rs = await asyncio.gather(*[client.get("/api/motion", params={"name": "x"})
                                        for _ in range(3)])
        return rs

    rs = asyncio.run(run())
    assert all(r.status_code == 200 for r in rs)
    assert len(calls) == 1                    # un seul calcul pour les 3 demandes
    assert images._INFLIGHT == {}             # plus rien en cours ensuite


def test_no_detection_is_explained():
    from app.core.screen import ScreenResult
    from app.routers.images import no_detection_alert

    sc = ScreenResult(target_label="t", n_selected=65, n_downloaded=65, n_download_failed=0,
                      n_kept=0, by_status={"invisible": 65}, kept_visits=0, frames=[],
                      download_errors={})
    a = no_detection_alert(258, sc)
    assert a["title"] == "Objet non détecté par SPHEREx" and "258" in a["message"]
    sc0 = sc.model_copy(update={"n_downloaded": 0, "by_status": {}})
    assert no_detection_alert(258, sc0)["title"] == "Images indisponibles"
    assert no_detection_alert(0, sc)["title"] == "Aucune image SPHEREx ici"


def test_wrong_source_is_flagged_for_known_proper_motion():
    """WISE 0855 : 2,5 ± 0,7″/an mesurés au lieu de 8,2″/an -> source de fond, pas la cible.
    Barnard : 9,6 ± 0,5 au lieu de 10,4 -> cohérent, pas d'alerte."""
    from app.core.measure import MotionResult
    from app.routers.images import wrong_source_alert

    def mot(mu_ra, mu_dec, err):
        import math
        return MotionResult(n_points=4, n_used=4, n_distinct_epochs=3, coverage_start=None,
                            coverage_end=None, span_days=200, model="droite", status="moving",
                            status_reason="", mu_ra_arcsec_yr=mu_ra, mu_dec_arcsec_yr=mu_dec,
                            mu_arcsec_yr=math.hypot(mu_ra, mu_dec), mu_err_arcsec_yr=err)
    wise = SimpleNamespace(label="WISE 0855-0714", pmra=-8123.7, pmdec=673.2)
    a = wrong_source_alert(wise, mot(-2.0, 1.5, 0.68))
    assert a and a["title"] == "Ce n'est probablement pas la bonne source" and "8.2″/an" in a["message"]
    barnard = SimpleNamespace(label="Barnard", pmra=-801.551, pmdec=10362.394)
    assert wrong_source_alert(barnard, mot(-0.7, 9.6, 0.48)) is None
    assert wrong_source_alert(SimpleNamespace(label="x", pmra=None, pmdec=None), mot(1, 1, 0.1)) is None
