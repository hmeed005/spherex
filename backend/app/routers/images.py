import asyncio
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from app.core.search import SearchResult, search_images
from pathlib import Path

from app.core import config
from app.core.align import AlignResult, align_group
from app.core.measure import (DisplayPlan, MotionResult, calibrated_sigma_scale, fit_motion,
                               measure_positions, plan_display, positions_plot, render_display)
from app.core.group import WL_TOLERANCE, GroupResult, group_frames
from app.core.screen import ScreenResult, frame_arrays, screen_selection
from app.core.fetch import CUTOUT_DIR
from fastapi.responses import FileResponse
from app.core.select import MAX_PER_VISIT_DETECTOR, MAX_TOTAL, SelectionResult, select_images
from app.core.target import (DEFAULT_SIZE_ARCMIN, MAX_SIZE_ARCMIN, MIN_SIZE_ARCMIN,
                             TargetRequest, resolve_target)

router = APIRouter(prefix="/api", tags=["search"])


async def _search(name, ra, dec, size_arcmin, refresh):
    try:
        target = resolve_target(TargetRequest(name=name, ra=ra, dec=dec, size_arcmin=size_arcmin))
    except ValidationError as exc:
        raise HTTPException(422, exc.errors(include_url=False, include_context=False)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        return await run_in_threadpool(search_images, target, refresh)
    except RuntimeError as exc:      # DEMO_MODE sans cache
        raise HTTPException(503, str(exc)) from exc
    except ConnectionError as exc:   # IRSA injoignable
        raise HTTPException(502, str(exc)) from exc


@router.get("/selection", response_model=SelectionResult,
            summary="Filtrer, grouper en passages et choisir les images à télécharger")
async def get_selection(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    detector: str | None = Query(None, pattern="^D[1-6]$"),
    max_per_visit_detector: int = Query(MAX_PER_VISIT_DETECTOR, ge=1, le=50),
    max_total: int = Query(MAX_TOTAL, ge=10, le=2000),
    require_full_coverage: bool = True,
    refresh: bool = False,
):
    search = await _search(name, ra, dec, size_arcmin, refresh)
    return select_images(search, detector=detector, require_full_coverage=require_full_coverage,
                         max_per_visit_detector=max_per_visit_detector, max_total=max_total)


@router.get("/images", response_model=SearchResult,
            summary="Lister les images SPHEREx (DR1 + QR3) qui couvrent la cible")
async def get_images(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    detector: str | None = Query(None, pattern="^D[1-6]$", description="Filtrer un détecteur"),
    refresh: bool = Query(False, description="Ignorer le cache et réinterroger IRSA"),
):
    result = await _search(name, ra, dec, size_arcmin, refresh)

    if detector:
        result.images = [i for i in result.images if i.detector == detector]
        result.n_images = len(result.images)
    return result


@router.get("/frames", response_model=ScreenResult,
            summary="Télécharger les cutouts sélectionnés et contrôler la netteté de l'objet")
async def get_frames(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    detector: str | None = Query(None, pattern="^D[1-6]$"),
    max_per_visit_detector: int = Query(2, ge=1, le=50),
    max_total: int = Query(60, ge=1, le=500),
    only_kept: bool = Query(False, description="Ne renvoyer que les images gardées"),
    refresh: bool = False,
):
    search = await _search(name, ra, dec, size_arcmin, refresh)
    sel = select_images(search, detector=detector,
                        max_per_visit_detector=max_per_visit_detector, max_total=max_total)
    result = await run_in_threadpool(screen_selection, sel)
    if only_kept:
        result.frames = [f for f in result.frames if f.keep]
    return result


@router.get("/frame/{frame_id}",
            summary="Valeurs de pixels, incertitude et flags complets d'une image")
async def get_frame(frame_id: str, format: str = Query("json", pattern="^(json|fits)$")):
    if not frame_id.isalnum():
        raise HTTPException(422, "frame_id invalide")
    path = CUTOUT_DIR / f"{frame_id}.fits"
    if not path.exists():
        raise HTTPException(404, "Image absente du cache : appelez d'abord /api/frames")
    if format == "fits":
        return FileResponse(path, media_type="application/fits", filename=f"{frame_id}.fits")
    return await run_in_threadpool(frame_arrays, path)


class GroupsResponse(ScreenResult.__base__):  # BaseModel
    target_label: str
    n_frames_kept: int
    by_status: dict[str, int]
    grouping: GroupResult


@router.get("/groups", response_model=GroupsResponse,
            summary="Séquences d'images à longueur d'onde comparable (une image par passage)")
async def get_groups(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    detector: str | None = Query(None, pattern="^D[1-6]$"),
    tolerance: float = Query(WL_TOLERANCE, gt=0, le=0.2,
                             description="Écart relatif max à la longueur d'onde centrale"),
    max_per_visit_detector: int = Query(3, ge=1, le=50),
    max_total: int = Query(80, ge=1, le=500),
    refresh: bool = False,
):
    search = await _search(name, ra, dec, size_arcmin, refresh)
    sel = select_images(search, detector=detector,
                        max_per_visit_detector=max_per_visit_detector, max_total=max_total)
    sc = await run_in_threadpool(screen_selection, sel)
    grouping = group_frames(sc.frames, sel.visits, tolerance=tolerance)
    return GroupsResponse(target_label=sc.target_label, n_frames_kept=sc.n_kept,
                          by_status=sc.by_status, grouping=grouping)


class GroupSummary(ScreenResult.__base__):
    id: str
    detector: str
    wavelength_um: float
    n_epochs: int
    span_days: float


class TimelineResponse(ScreenResult.__base__):
    target_label: str
    group: AlignResult
    available_groups: list[GroupSummary]
    frame_urls: list[str]
    gif_url: str | None
    sheet_url: str | None


def _url(path: str | None) -> str | None:
    if not path:
        return None
    rel = Path(path).resolve().relative_to(Path(config.CACHE_DIR).resolve())
    return "/files/" + rel.as_posix()


@router.get("/timeline", response_model=TimelineResponse,
            summary="Séquence alignée (même centre, échelle, orientation) d'un groupe")
async def get_timeline(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    group: str | None = Query(None, description="id du groupe (défaut : le meilleur)"),
    detector: str | None = Query(None, pattern="^D[1-6]$"),
    tolerance: float = Query(WL_TOLERANCE, gt=0, le=0.2),
    max_per_visit_detector: int = Query(3, ge=1, le=50),
    max_total: int = Query(80, ge=1, le=500),
    refresh: bool = False,
):
    search = await _search(name, ra, dec, size_arcmin, refresh)
    sel = select_images(search, detector=detector,
                        max_per_visit_detector=max_per_visit_detector, max_total=max_total)
    sc = await run_in_threadpool(screen_selection, sel)
    grouping = group_frames(sc.frames, sel.visits, tolerance=tolerance)
    if not grouping.groups:
        raise HTTPException(404, "Aucun groupe de longueur d'onde comparable (au moins 2 passages)")
    chosen = next((g for g in grouping.groups if g.id == (group or grouping.default_group)), None)
    if chosen is None:
        raise HTTPException(404, f"Groupe inconnu : {group}")
    out_dir = Path(config.CACHE_DIR) / "aligned" / search.target.cache_key / chosen.id
    frames_by_id = {f.frame_id: f for f in sc.frames}
    aligned = await run_in_threadpool(align_group, search.target, chosen, frames_by_id, out_dir)
    return TimelineResponse(
        target_label=search.target.label, group=aligned,
        available_groups=[GroupSummary(id=g.id, detector=g.detector, wavelength_um=g.wavelength_um,
                                       n_epochs=g.n_epochs, span_days=g.span_days)
                          for g in grouping.groups],
        frame_urls=[_url(f.png) for f in aligned.frames],
        gif_url=_url(aligned.gif), sheet_url=_url(aligned.sheet))


RESULT_VERSION = "motion-v9"   # changer pour invalider les résultats en cache


class MotionResponse(ScreenResult.__base__):
    target_label: str
    motion: MotionResult                 # avec correction des décalages de groupe
    motion_without_offsets: MotionResult # sans correction : rien n'est caché
    display: DisplayPlan                 # séquence principale + groupes séparés si désaccord
    sequence_gif_urls: list[str | None]
    sequence_video_urls: list[str | None]
    side_by_side_urls: list[str | None]
    positions_plot_url: str | None
    # --- fraîcheur des données (mise à jour automatique hebdomadaire) ---
    result_key: Optional[str] = None       # identifiant du résultat (fichier de cache)
    result_version: Optional[str] = None
    request: Optional[dict] = None         # paramètres pour pouvoir le recalculer seul
    computed_at: Optional[str] = None      # date du calcul (UTC, ISO)
    checked_at: Optional[str] = None       # dernière vérification de nouvelles images sur IRSA
    n_images_found: Optional[int] = None   # images SPHEREx trouvées sur IRSA pour cette cible
    last_image_date: Optional[str] = None  # date de la plus récente
    search_fingerprint: Optional[str] = None   # empreinte de la liste d'images utilisée
    update: Optional[dict] = None          # état de la mise à jour (ajouté à chaque réponse)


def result_key(target_cache_key: str, detector, tolerance, max_per_visit_detector, max_total) -> str:
    import hashlib, json
    return hashlib.sha1(json.dumps([RESULT_VERSION, target_cache_key, detector, tolerance,
                                    max_per_visit_detector, max_total]).encode()).hexdigest()[:16]


def result_path(key: str) -> Path:
    return Path(config.CACHE_DIR) / "results" / f"motion_{key}.json"


def search_fingerprint(search) -> str:
    """Empreinte de la liste d'images IRSA : change dès qu'une nouvelle image est publiée."""
    import hashlib
    ids = sorted(f"{i.obs_id}|{i.detector}|{i.release}|{i.survey}" for i in (search.images or []))
    return hashlib.sha1("\n".join(ids).encode()).hexdigest()[:16]


def write_result(path: Path, resp: "MotionResponse") -> None:
    """Écriture atomique : le site lit toujours un fichier complet (ancien OU nouveau)."""
    import os, time
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(resp.model_dump_json(exclude={"update"}), encoding="utf-8")
    for attempt in range(5):          # Windows : le fichier peut être lu au même instant
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
    os.replace(tmp, path)


def _motion_pipeline(search, detector, tolerance, max_per_visit_detector, max_total, run_dir=None):
    sel = select_images(search, detector=detector,
                        max_per_visit_detector=max_per_visit_detector, max_total=max_total)
    sc = screen_selection(sel)
    grouping = group_frames(sc.frames, sel.visits, tolerance=tolerance)
    measures, cache = measure_positions(search.target, sc.frames, grouping, sel.visits)
    motion = fit_motion(measures)
    motion_raw = fit_motion(measures, with_offsets=False)
    fby = {f.frame_id: f for f in sc.frames}
    # chaque calcul dans SON dossier : une mise à jour n'efface jamais la vidéo en cours de lecture
    out_dir = run_dir or Path(config.CACHE_DIR) / "trajectory" / search.target.cache_key
    plan = plan_display(motion.measures, fby, calibrated_sigma_scale(motion))
    if measures:
        render_display(search.target, motion, plan, fby, cache, out_dir)
        plot = positions_plot(search.target, motion, out_dir / "positions.png")
        wrong = wrong_source_alert(search.target, motion)   # prioritaire sur les autres messages
        if wrong:
            plan.alert = wrong
    else:
        plot = None
        plan.alert = no_detection_alert(len(search.images), sc)   # expliquer POURQUOI rien
    return motion, motion_raw, plan, plot


def wrong_source_alert(target, motion: MotionResult) -> Optional[dict]:
    """Cible au mouvement propre CONNU : si le mouvement mesuré ne lui correspond pas (> 3σ),
    la source vue dans les images n'est sans doute pas la cible (étoile ou galaxie proche,
    confondue dans les gros pixels de SPHEREx). Ex. WISE 0855 : invisible pour SPHEREx sous
    2 µm, mais une source de fond y est visible -> 2,5″/an mesurés au lieu de 8,2″/an."""
    pmra, pmdec = getattr(target, "pmra", None), getattr(target, "pmdec", None)
    if not pmra or not pmdec or motion.mu_ra_arcsec_yr is None or motion.mu_dec_arcsec_yr is None:
        return None
    exp_ra, exp_dec = pmra / 1000.0, pmdec / 1000.0
    expected = float(np.hypot(exp_ra, exp_dec))
    if expected < 0.5:                          # mouvement trop petit pour juger
        return None
    diff = float(np.hypot(motion.mu_ra_arcsec_yr - exp_ra, motion.mu_dec_arcsec_yr - exp_dec))
    err = max(motion.mu_err_arcsec_yr or 0.0, 0.1)
    if diff <= 3 * err:
        return None
    mu = motion.mu_arcsec_yr or 0.0
    return dict(level="warn", title="Ce n'est probablement pas la bonne source",
                message=f"Sur ces images, la source visible se déplace de {mu:.1f}″/an, alors que "
                        f"{target.label} se déplace de {expected:.1f}″/an (valeur connue). La source "
                        f"visible est sans doute une autre étoile ou galaxie proche de sa position : "
                        f"{target.label} lui-même n'est probablement pas détecté par SPHEREx.")


def no_detection_alert(n_found: int, sc: ScreenResult) -> dict:
    """Message clair quand aucune image n'est exploitable (au lieu de « aucune observation »)."""
    if n_found == 0 or sc.n_selected == 0:
        return dict(level="warn", title="Aucune image SPHEREx ici",
                    message="SPHEREx n'a pas encore d'image publiée qui couvre cette position. "
                            "Essayez une autre cible ou une autre position.")
    if sc.n_downloaded == 0:
        return dict(level="warn", title="Images indisponibles",
                    message=f"{n_found} images SPHEREx couvrent cette position, mais elles n'ont pas "
                            "pu être téléchargées depuis IRSA (service momentanément indisponible ?). "
                            "Réessayez dans quelques minutes.")
    st = sc.by_status
    n_inv = st.get("invisible", 0) + st.get("faible", 0)
    return dict(level="warn", title="Objet non détecté par SPHEREx",
                message=f"{n_found} images SPHEREx couvrent cette position et {sc.n_downloaded} ont été "
                        f"examinées, mais l'objet n'est nettement visible sur aucune "
                        f"({n_inv} où son signal ne dépasse pas le bruit). Soit il est trop faible pour "
                        "SPHEREx à ces longueurs d'onde, soit il n'est pas à cette position : pour une "
                        "étoile qui se déplace vite, choisissez-la dans la liste (sa position est alors "
                        "corrigée de son mouvement).")


@router.get("/motion", response_model=MotionResponse,
            summary="Trajectoire complète : mouvement (avec et sans correction), animations, désaccords")
async def get_motion(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None),
    dec: str | None = Query(None),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
    detector: str | None = Query(None, pattern="^D[1-6]$"),
    tolerance: float = Query(WL_TOLERANCE, gt=0, le=0.2),
    max_per_visit_detector: int = Query(3, ge=1, le=50),
    max_total: int = Query(80, ge=1, le=500),
    refresh: bool = Query(False, description="Recalculer le résultat (avec la recherche IRSA en cache)"),
    refresh_search: bool = Query(False, description="Refaire aussi la recherche sur IRSA"),
):
    search = await _search(name, ra, dec, size_arcmin, refresh_search)
    from app.routers import updates
    # cache du résultat final : un 2e appel identique répond instantanément
    key = result_key(search.target.cache_key, detector, tolerance, max_per_visit_detector, max_total)
    request = dict(name=name, ra=ra, dec=dec, size_arcmin=size_arcmin, detector=detector,
                   tolerance=tolerance, max_per_visit_detector=max_per_visit_detector,
                   max_total=max_total)
    cached = result_path(key)
    if cached.exists() and not refresh:
        resp = MotionResponse.model_validate_json(cached.read_text(encoding="utf-8"))
        # anciens résultats : on note de quoi les mettre à jour seuls ensuite
        if resp.request is None or resp.result_key is None or resp.computed_at is None:
            from datetime import datetime, timezone
            mtime = datetime.fromtimestamp(cached.stat().st_mtime, timezone.utc).isoformat()
            resp.request = resp.request or request
            resp.result_key, resp.result_version = key, RESULT_VERSION
            resp.computed_at = resp.computed_at or mtime
            resp.checked_at = resp.checked_at or resp.computed_at
            resp.n_images_found = resp.n_images_found if resp.n_images_found is not None \
                else getattr(search, "n_images", None)
            resp.last_image_date = resp.last_image_date or getattr(search, "last_date", None)
            write_result(cached, resp)
        wrong = wrong_source_alert(search.target, resp.motion)   # aussi pour les résultats en cache
        if wrong:
            resp.display.alert = wrong
        # données de plus d'une semaine : réponse IMMÉDIATE avec l'ancien résultat, et
        # vérification des nouvelles images SPHEREx en arrière-plan (le site n'attend jamais)
        updates.maybe_schedule(resp)
        resp.update = updates.update_info(resp)
        return resp
    # Même calcul déjà en cours (rechargement de la page, clic répété, script de précalcul) :
    # on attend CE calcul au lieu d'en lancer un 2e en parallèle (double téléchargement et
    # deux rendus qui écrivent dans le même dossier). shield : si le navigateur abandonne,
    # le calcul continue et son résultat est mis en cache pour le prochain clic.
    task = _INFLIGHT.get(key)
    if task is None:
        task = asyncio.ensure_future(compute_motion(search, key, request))
        _INFLIGHT[key] = task
        task.add_done_callback(lambda _t, k=key: _INFLIGHT.pop(k, None))
    resp = await asyncio.shield(task)
    resp = resp.model_copy()
    resp.update = updates.update_info(resp)
    return resp


_INFLIGHT: dict[str, "asyncio.Future"] = {}


def _run_dir(search, key: str) -> Path:
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")   # unique, et triable
    return Path(config.CACHE_DIR) / "trajectory" / search.target.cache_key / f"{key}-{stamp}"


def _cleanup_runs(search, key: str, keep: int = 2) -> None:
    """Garde les 2 derniers rendus de ce résultat (la page ouverte peut encore lire l'ancien)."""
    import shutil
    base = Path(config.CACHE_DIR) / "trajectory" / search.target.cache_key
    runs = sorted(p for p in base.glob(f"{key}-*") if p.is_dir())
    for old in runs[:-keep]:
        shutil.rmtree(old, ignore_errors=True)


async def compute_motion(search, key: str, request: dict) -> "MotionResponse":
    from datetime import datetime, timezone
    detector, tolerance = request.get("detector"), request.get("tolerance", WL_TOLERANCE)
    mpvd, max_total = request.get("max_per_visit_detector", 3), request.get("max_total", 80)
    run_dir = _run_dir(search, key)
    motion, motion_raw, plan, plot = await run_in_threadpool(
        _motion_pipeline, search, detector, tolerance, mpvd, max_total, run_dir)
    # chemins disque -> URLs servies sous /files (vidéo, sous-titres, images de la frise)
    for sq in list(plan.sequences) + list(plan.group_sequences):
        if sq.video:
            sq.video.mp4, sq.video.gif, sq.video.vtt, sq.video.mp4_markers = (
                _url(sq.video.mp4), _url(sq.video.gif), _url(sq.video.vtt), _url(sq.video.mp4_markers))
            for e in sq.video.timeline:
                e.image_url = _url(e.image_url)
    now = datetime.now(timezone.utc).isoformat()
    checked = getattr(search, "cached_at", None) or now
    response = MotionResponse(
        target_label=search.target.label, motion=motion, motion_without_offsets=motion_raw,
        display=plan, sequence_gif_urls=[sq.video.gif if sq.video else None for sq in plan.sequences],
        sequence_video_urls=[sq.video.mp4 if sq.video else None for sq in plan.sequences],
        side_by_side_urls=[_url(it.get("png")) for it in plan.side_by_side if it.get("png")],
        positions_plot_url=_url(plot),
        result_key=key, result_version=RESULT_VERSION, request=request, computed_at=now,
        checked_at=checked, n_images_found=getattr(search, "n_images", None),
        last_image_date=getattr(search, "last_date", None),
        search_fingerprint=search_fingerprint(search) if getattr(search, "images", None) is not None
        else None)
    # un résultat vide (IRSA en panne, aucune image exploitable) n'est pas mis en cache :
    # la prochaine demande réessaiera au lieu de renvoyer « aucune image » pour toujours
    has_images = any(sq.video and sq.video.timeline for sq in plan.sequences)
    if has_images:
        write_result(result_path(key), response)
        _cleanup_runs(search, key)
    return response
