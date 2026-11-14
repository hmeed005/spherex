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


RESULT_VERSION = "motion-v1"   # changer pour invalider les résultats en cache


class MotionResponse(ScreenResult.__base__):
    target_label: str
    motion: MotionResult                 # avec correction des décalages de groupe
    motion_without_offsets: MotionResult # sans correction : rien n'est caché
    display: DisplayPlan                 # séquence principale + groupes séparés si désaccord
    sequence_gif_urls: list[str | None]
    sequence_video_urls: list[str | None]
    side_by_side_urls: list[str | None]
    positions_plot_url: str | None


def _motion_pipeline(search, detector, tolerance, max_per_visit_detector, max_total):
    sel = select_images(search, detector=detector,
                        max_per_visit_detector=max_per_visit_detector, max_total=max_total)
    sc = screen_selection(sel)
    grouping = group_frames(sc.frames, sel.visits, tolerance=tolerance)
    measures, cache = measure_positions(search.target, sc.frames, grouping, sel.visits)
    motion = fit_motion(measures)
    motion_raw = fit_motion(measures, with_offsets=False)
    fby = {f.frame_id: f for f in sc.frames}
    out_dir = Path(config.CACHE_DIR) / "trajectory" / search.target.cache_key
    plan = plan_display(motion.measures, fby, calibrated_sigma_scale(motion))
    if measures:
        render_display(search.target, motion, plan, fby, cache, out_dir)
        plot = positions_plot(search.target, motion, out_dir / "positions.png")
    else:
        plot = None
    return motion, motion_raw, plan, plot


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
    # cache du résultat final : un 2e appel identique répond instantanément
    import hashlib, json
    key = hashlib.sha1(json.dumps([RESULT_VERSION, search.target.cache_key, detector, tolerance,
                                   max_per_visit_detector, max_total]).encode()).hexdigest()[:16]
    cached = Path(config.CACHE_DIR) / "results" / f"motion_{key}.json"
    if cached.exists() and not refresh:
        return MotionResponse.model_validate_json(cached.read_text(encoding="utf-8"))
    motion, motion_raw, plan, plot = await run_in_threadpool(
        _motion_pipeline, search, detector, tolerance, max_per_visit_detector, max_total)
    # chemins disque -> URLs servies sous /files (vidéo, sous-titres, images de la frise)
    for sq in plan.sequences:
        if sq.video:
            sq.video.mp4, sq.video.gif, sq.video.vtt, sq.video.mp4_markers = (
                _url(sq.video.mp4), _url(sq.video.gif), _url(sq.video.vtt), _url(sq.video.mp4_markers))
            for e in sq.video.timeline:
                e.image_url = _url(e.image_url)
    response = MotionResponse(
        target_label=search.target.label, motion=motion, motion_without_offsets=motion_raw,
        display=plan, sequence_gif_urls=[sq.video.gif if sq.video else None for sq in plan.sequences],
        sequence_video_urls=[sq.video.mp4 if sq.video else None for sq in plan.sequences],
        side_by_side_urls=[_url(it.get("png")) for it in plan.side_by_side if it.get("png")],
        positions_plot_url=_url(plot))
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(response.model_dump_json(), encoding="utf-8")
    return response
