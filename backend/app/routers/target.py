from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.core.target import (DEFAULT_SIZE_ARCMIN, MAX_SIZE_ARCMIN, MIN_SIZE_ARCMIN,
                             Target, TargetRequest, resolve_target)

router = APIRouter(prefix="/api", tags=["target"])


@router.get("/target", response_model=Target, summary="Valider et normaliser une cible")
def get_target(
    name: str | None = Query(None, examples=["Barnard"]),
    ra: str | None = Query(None, examples=["269.452"]),
    dec: str | None = Query(None, examples=["4.693"]),
    size_arcmin: float = Query(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN),
):
    try:
        req = TargetRequest(name=name, ra=ra, dec=dec, size_arcmin=size_arcmin)
        return resolve_target(req)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False, include_context=False)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
