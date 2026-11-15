"""Mise à jour automatique des résultats : SPHEREx publie de nouvelles images sur IRSA chaque
semaine. Le site ne doit jamais attendre ni montrer une vidéo à moitié réécrite :

* une demande sur un résultat de plus de UPDATE_EVERY_DAYS jours répond IMMÉDIATEMENT avec
  l'ancien résultat et lance la vérification en arrière-plan ;
* un planificateur (démarré avec le serveur) fait le tour de tous les résultats déjà calculés
  toutes les UPDATE_CHECK_HOURS heures, et met à jour ceux qui ont plus d'une semaine ;
* la vérification refait la recherche IRSA : si aucune nouvelle image n'est publiée, rien
  n'est recalculé (on note seulement la date de vérification) ; sinon le calcul est refait
  dans un NOUVEAU dossier, puis le résultat est remplacé d'un coup (écriture atomique) ;
* IRSA en panne : l'ancien résultat reste servi, nouvel essai plus tard.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.core import config

log = logging.getLogger("spherex.updates")
router = APIRouter(prefix="/api/updates", tags=["updates"])

_REFRESHING: dict[str, asyncio.Task] = {}      # mises à jour en cours (une par résultat)
_LAST_ATTEMPT: dict[str, float] = {}           # pour ne pas harceler IRSA quand il est en panne
_LAST_OUTCOME: dict[str, dict] = {}            # dernier résultat de vérification, par résultat
_STATE = {"last_cycle_at": None, "next_cycle_at": None, "new_collections": [], "running": False}


# ----------------------------------------------------------------------------- dates
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def last_check(resp) -> Optional[datetime]:
    return _parse(resp.checked_at) or _parse(resp.computed_at)


def next_check(resp) -> Optional[datetime]:
    last = last_check(resp)
    return last + timedelta(days=config.UPDATE_EVERY_DAYS) if last else None


def is_due(resp, now: Optional[datetime] = None) -> bool:
    nxt = next_check(resp)
    return nxt is None or (now or _now()) >= nxt


def update_info(resp) -> dict:
    """Petit résumé joint à chaque réponse /api/motion (affiché sous la vidéo)."""
    key = resp.result_key
    nxt = next_check(resp)
    if key and key in _REFRESHING:
        status = "updating"
    elif not config.AUTO_UPDATE:
        status = "off"
    elif nxt and _now() >= nxt:
        status = "due"
    else:
        status = "fresh"
    out = dict(status=status, every_days=config.UPDATE_EVERY_DAYS,
               computed_at=resp.computed_at, checked_at=resp.checked_at,
               next_check_at=nxt.isoformat() if nxt else None,
               n_images_found=resp.n_images_found, last_image_date=resp.last_image_date)
    if key and key in _LAST_OUTCOME:
        out["last_outcome"] = _LAST_OUTCOME[key]
    return out


# ----------------------------------------------------------------------------- une mise à jour
def maybe_schedule(resp) -> bool:
    """Lance la vérification en arrière-plan si le résultat a plus d'une semaine."""
    if not config.AUTO_UPDATE or not resp.result_key or not resp.request:
        return False
    if not is_due(resp):
        return False
    return schedule(resp.result_key, resp.request) is not None


def schedule(key: str, request: dict, force: bool = False) -> Optional[asyncio.Task]:
    task = _REFRESHING.get(key)
    if task is not None:
        return task
    last = _LAST_ATTEMPT.get(key)
    if not force and last and time.time() - last < config.UPDATE_RETRY_MINUTES * 60:
        return None                                   # essai récent (IRSA en panne ?) : plus tard
    task = asyncio.ensure_future(refresh_one(key, request, force=force))
    _REFRESHING[key] = task
    task.add_done_callback(lambda _t, k=key: _REFRESHING.pop(k, None))
    return task


def _record(key: str, outcome: str, **extra) -> dict:
    rec = dict(outcome=outcome, at=_now().isoformat(), **extra)
    _LAST_OUTCOME[key] = rec
    log.info("mise à jour %s : %s %s", key, outcome, extra or "")
    return rec


async def refresh_one(key: str, request: dict, force: bool = False) -> dict:
    """Vérifie IRSA pour UN résultat ; recalcule seulement s'il y a de nouvelles images."""
    from app.core.search import search_images
    from app.core.target import TargetRequest, resolve_target
    from app.routers import images

    _LAST_ATTEMPT[key] = time.time()
    path = images.result_path(key)
    old = None
    if path.exists():
        try:
            old = images.MotionResponse.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — fichier abîmé : on recalcule
            old = None
    try:
        target = resolve_target(TargetRequest(name=request.get("name"), ra=request.get("ra"),
                                              dec=request.get("dec"),
                                              size_arcmin=request.get("size_arcmin")))
        before = await run_in_threadpool(_cached_search, target)
        search = await run_in_threadpool(search_images, target, True)   # nouvelle recherche IRSA
    except Exception as exc:  # noqa: BLE001 — IRSA injoignable, nom inconnu…
        return _record(key, "irsa-unavailable", error=f"{type(exc).__name__}: {exc}"[:200])
    if search.source != "irsa" or search.errors:
        # IRSA a répondu à moitié : l'ancien résultat reste en place, nouvel essai plus tard
        return _record(key, "irsa-unavailable", error=(search.errors or ["cache"])[0][:200])

    new_fp = images.search_fingerprint(search)
    old_fp = (old.search_fingerprint if old else None) or (
        images.search_fingerprint(before) if before is not None else None)
    old_n = (old.n_images_found if old and old.n_images_found is not None
             else (before.n_images if before is not None else 0))
    n_new = max(0, search.n_images - (old_n or 0))
    if old is not None and new_fp == old_fp and not force:
        # rien de nouveau sur IRSA : on note seulement la date de vérification
        old.checked_at = _now().isoformat()
        old.n_images_found, old.last_image_date = search.n_images, search.last_date
        old.search_fingerprint = new_fp
        images.write_result(path, old)
        return _record(key, "no-new-images", n_images=search.n_images)

    resp = await images.compute_motion(search, key, request)
    has_images = any(sq.video and sq.video.timeline for sq in resp.display.sequences)
    if not has_images:
        return _record(key, "kept-previous", n_images=search.n_images,
                       reason="nouveau calcul sans image exploitable")
    return _record(key, "updated", n_images=search.n_images, new_images=n_new,
                   last_image_date=search.last_date)


def _cached_search(target):
    """Liste d'images de la recherche précédente (cache), sans appeler IRSA."""
    from app.core.search import cached_search
    try:
        return cached_search(target)
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------------------- le planificateur
def tracked_results() -> list:
    """Résultats déjà calculés (version actuelle) que l'on sait recalculer seuls."""
    from app.routers import images
    out = []
    for path in sorted((Path(config.CACHE_DIR) / "results").glob("motion_*.json")):
        try:
            resp = images.MotionResponse.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        key = path.stem.removeprefix("motion_")
        if resp.request and resp.result_key == key and resp.result_version == images.RESULT_VERSION:
            out.append(resp)
    return out


async def run_cycle(force: bool = False, only_key: Optional[str] = None) -> list[dict]:
    """Un tour : vérifie un par un (IRSA n'aime pas les rafales) les résultats à mettre à jour."""
    done = []
    _STATE["running"] = True
    try:
        for resp in await run_in_threadpool(tracked_results):
            if only_key and resp.result_key != only_key:
                continue
            if not (force or is_due(resp)):
                continue
            task = schedule(resp.result_key, resp.request, force=force)
            if task is not None:
                done.append(dict(key=resp.result_key, target=resp.target_label, **(await task)))
        await run_in_threadpool(_check_new_collections)
    finally:
        _STATE["running"] = False
        _STATE["last_cycle_at"] = _now().isoformat()
    return done


async def scheduler_loop() -> None:
    await asyncio.sleep(config.UPDATE_START_DELAY_S)       # laisser le serveur démarrer
    while True:
        _STATE["next_cycle_at"] = None
        try:
            await run_cycle()
        except Exception:  # noqa: BLE001 — le planificateur ne doit jamais s'arrêter
            log.exception("tour de mise à jour en échec")
        nxt = _now() + timedelta(hours=config.UPDATE_CHECK_HOURS)
        _STATE["next_cycle_at"] = nxt.isoformat()
        await asyncio.sleep(config.UPDATE_CHECK_HOURS * 3600)


def _check_new_collections() -> None:
    """SPHEREx change parfois de version de publication (qr2 -> qr3 -> qr4…). On ne bascule pas
    tout seul (risque de doublons entre versions) : on SIGNALE la nouvelle collection."""
    try:
        from astroquery.ipac.irsa import Irsa
        names = [str(n) for n in Irsa.list_collections(servicetype="SIA", filter="spherex")["collection"]]
    except Exception:  # noqa: BLE001 — pas grave : on réessaiera au prochain tour
        return
    known = set(config.COLLECTIONS)
    _STATE["new_collections"] = sorted(n for n in names
                                       if n not in known and not n.endswith("_cal")
                                       and n.startswith(("spherex_qr", "spherex_dr")))


# ----------------------------------------------------------------------------- API
@router.get("/status", summary="État des mises à jour automatiques (nouvelles images SPHEREx)")
async def status():
    rows = []
    for resp in await run_in_threadpool(tracked_results):
        info = update_info(resp)
        rows.append(dict(key=resp.result_key, target=resp.target_label, request=resp.request,
                         **info))
    return dict(auto_update=config.AUTO_UPDATE, every_days=config.UPDATE_EVERY_DAYS,
                check_every_hours=config.UPDATE_CHECK_HOURS, running=_STATE["running"],
                last_cycle_at=_STATE["last_cycle_at"], next_cycle_at=_STATE["next_cycle_at"],
                updating=sorted(_REFRESHING), new_collections=_STATE["new_collections"],
                results=rows)


@router.post("/run", summary="Vérifier tout de suite (toutes les cibles, ou une seule)")
async def run_now(key: Optional[str] = Query(None, description="result_key d'une seule cible"),
                  force: bool = Query(False, description="vérifier même si moins d'une semaine")):
    # en arrière-plan : la réponse revient tout de suite, suivre avec /api/updates/status
    asyncio.ensure_future(run_cycle(force=force, only_key=key))
    return dict(started=True, force=force, key=key)
