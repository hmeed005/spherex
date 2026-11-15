"""Mise à jour automatique hebdomadaire : réponse immédiate, recalcul seulement s'il y a de
nouvelles images SPHEREx sur IRSA, ancien résultat conservé si IRSA est en panne."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

from app.core import config
from app.core.measure import DisplayPlan, DisplaySequence, fit_motion
from app.core.video import TimelineEntry, VideoAssets
from app.main import app
from app.routers import images, updates


def fake_search(n_images, last_date="2026-11-01", source="irsa", errors=()):
    imgs = [SimpleNamespace(obs_id=f"obs{i}", detector="D2", release="qr3", survey="wide")
            for i in range(n_images)]
    return SimpleNamespace(target=SimpleNamespace(cache_key="upd-test", label="Test star"),
                           images=imgs, n_images=n_images, last_date=last_date, source=source,
                           errors=list(errors), cached_at=None)


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Serveur sur un cache vide, IRSA simulé, calcul simulé (compte les recalculs)."""
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "AUTO_UPDATE", True)
    monkeypatch.setattr(config, "UPDATE_RETRY_MINUTES", 60.0)
    for d in (updates._REFRESHING, updates._LAST_ATTEMPT, updates._LAST_OUTCOME):
        d.clear()
    # cached = recherche en cache (lue par le site), irsa = ce que renvoie une NOUVELLE recherche
    state = SimpleNamespace(cached=fake_search(10), irsa=fake_search(10), computations=0,
                            irsa_calls=0)

    async def _search(name, ra, dec, size_arcmin, refresh):
        return state.cached

    def pipeline(search, detector, tolerance, mpvd, max_total, run_dir=None):
        state.computations += 1
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "trajectoire.mp4").write_bytes(b"x")
        entry = TimelineEntry(index=0, t_start_s=0, t_hold_end_s=1, t_end_s=1, seek_s=0,
                              frame_id="f0", date_utc="2026-01-01T00:00:00")
        video = VideoAssets(mp4=str(run_dir / "trajectoire.mp4"), duration_s=1, width=10,
                            height=10, timeline=[entry])
        seq = DisplaySequence(kind="unique", video=video, groups=["g"], frame_ids=["f0"])
        plan = DisplayPlan(comparisons=[], conflicted_groups=[], sequences=[seq], summary="")
        m = fit_motion([])
        return m, m, plan, None

    def search_images(target, refresh=False):
        state.irsa_calls += 1
        if isinstance(state.irsa, Exception):
            raise state.irsa
        return state.irsa

    monkeypatch.setattr(images, "_search", _search)
    monkeypatch.setattr(images, "_motion_pipeline", pipeline)
    import app.core.search as search_mod
    import app.core.target as target_mod
    monkeypatch.setattr(search_mod, "search_images", search_images)
    monkeypatch.setattr(search_mod, "cached_search", lambda t: None)
    monkeypatch.setattr(target_mod, "resolve_target", lambda req: state.cached.target)
    return state


def get(params=None):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get("/api/motion", params=params or {"name": "x"})
            # laisser finir la mise à jour lancée en arrière-plan
            for _ in range(100):
                if not updates._REFRESHING:
                    break
                await asyncio.sleep(0.02)
            return r
    return asyncio.run(run())


def age_result(days):
    """Fait vieillir le résultat en cache (comme s'il avait été calculé il y a `days` jours)."""
    path = next((config.CACHE_DIR / "results").glob("motion_*.json"))
    resp = images.MotionResponse.model_validate_json(path.read_text(encoding="utf-8"))
    old = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp.computed_at = resp.checked_at = old
    images.write_result(path, resp)
    return path


def test_first_result_is_dated_and_fresh(env):
    r = get().json()
    assert env.computations == 1
    assert r["computed_at"] and r["n_images_found"] == 10 and r["request"]["name"] == "x"
    assert r["update"]["status"] == "fresh" and r["update"]["next_check_at"]
    get()
    assert env.computations == 1                     # 2e demande : depuis le cache


def test_week_old_result_answers_at_once_and_skips_recompute_when_nothing_new(env):
    get()
    path = age_result(8)
    r = get().json()
    assert r["update"]["status"] == "updating"       # réponse immédiate, vérification en fond
    assert env.computations == 1                     # rien de nouveau sur IRSA : pas de recalcul
    after = images.MotionResponse.model_validate_json(path.read_text(encoding="utf-8"))
    assert datetime.fromisoformat(after.checked_at) > datetime.now(timezone.utc) - timedelta(minutes=1)
    assert updates._LAST_OUTCOME[after.result_key]["outcome"] == "no-new-images"
    assert get().json()["update"]["status"] == "fresh"


def test_new_images_on_irsa_trigger_a_recompute_in_a_new_folder(env):
    first = get().json()
    age_result(8)
    env.irsa = fake_search(14, last_date="2026-11-12")   # 4 nouvelles images publiées
    get()
    assert env.computations == 2
    r = get().json()
    assert r["n_images_found"] == 14 and r["last_image_date"] == "2026-11-12"
    assert r["sequence_video_urls"][0] != first["sequence_video_urls"][0]   # nouveau dossier
    out = updates._LAST_OUTCOME[r["result_key"]]
    assert out["outcome"] == "updated" and out["new_images"] == 4
    runs = list((config.CACHE_DIR / "trajectory" / "upd-test").glob(f"{r['result_key']}-*"))
    assert 1 <= len(runs) <= 2                        # anciens rendus nettoyés (2 gardés au plus)


def test_irsa_down_keeps_previous_result_and_waits_before_retrying(env):
    get()
    path = age_result(8)
    before = path.read_text(encoding="utf-8")
    env.irsa = ConnectionError("IRSA injoignable")
    r = get()
    assert r.status_code == 200                           # le site répond avec l'ancien résultat
    key = next(iter(updates._LAST_OUTCOME))
    assert updates._LAST_OUTCOME[key]["outcome"] == "irsa-unavailable"
    assert path.read_text(encoding="utf-8") == before     # ancien résultat intact
    calls = env.irsa_calls
    resp = images.MotionResponse.model_validate_json(before)
    assert updates.schedule(resp.result_key, resp.request) is None   # pas de nouvel essai tout de suite
    assert env.irsa_calls == calls


def test_scheduler_cycle_only_checks_results_older_than_a_week(env):
    get()
    assert asyncio.run(updates.run_cycle()) == []          # trop récent : rien à faire
    age_result(8)
    done = asyncio.run(updates.run_cycle())
    assert [d["outcome"] for d in done] == ["no-new-images"]
    st = asyncio.run(updates.status())
    assert st["results"][0]["status"] == "fresh" and st["every_days"] == 7
