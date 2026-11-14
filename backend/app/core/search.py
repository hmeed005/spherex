"""Étape 1 du pipeline : SEARCH.

Pour une cible (sortie de l'étape 0), demande à IRSA la liste des images
spectrales SPHEREx (Level 2) qui la couvrent, dans DR1 et QR3.
On utilise le service SIA (colonnes ObsCore standard, stables) via astroquery.
Les résultats sont mis en cache : une requête IRSA prend 20 à 40 s.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Callable, Optional

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from pydantic import BaseModel

from app.core import config
from app.core.cache import cache_get, cache_set
from app.core.target import Target

CACHE_VERSION = "search-v3"  # changer si le format des résultats change


class ImageRecord(BaseModel):
    obs_id: str
    release: str               # "dr1" ou "qr3"
    survey: str = "wide"       # "wide" (tout le ciel) ou "deep" (pôles écliptiques)
    detector: Optional[str]    # "D1" ... "D6"
    t_start_mjd: Optional[float]
    t_end_mjd: Optional[float]
    t_mid_mjd: Optional[float]
    date_utc: Optional[str]    # ISO, pour l'affichage
    wl_min_um: Optional[float]  # domaine du détecteur (pas encore la λ au pixel cible)
    wl_max_um: Optional[float]
    image_url: str             # image complète (~70 Mo) — ne PAS télécharger en interactif
    cutout_url: str            # petite zone autour de la cible
    cloud_access: Optional[str] = None
    size_mb: Optional[float] = None
    fully_covered: bool = True  # toute la zone demandée est dans l'image


class SearchResult(BaseModel):
    target: Target
    source: str                # "irsa" ou "cache"
    cached_at: Optional[str]
    query_seconds: Optional[float]
    n_images: int
    n_days: int                # nombre de jours d'observation distincts
    first_date: Optional[str]
    last_date: Optional[str]
    by_detector: dict[str, int]
    by_release: dict[str, int]
    by_survey: dict[str, int]
    errors: list[str]
    images: list[ImageRecord]


# --- Accès IRSA (isolé pour pouvoir le remplacer dans les tests) --------------
def _irsa_sia(ra: float, dec: float, radius_deg: float, collection: str):
    from astroquery.ipac.irsa import Irsa
    from astropy.utils.data import conf
    conf.remote_timeout = config.IRSA_TIMEOUT
    coord = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs")
    return Irsa.query_sia(pos=(coord, radius_deg * u.deg), collection=collection)


SiaFn = Callable[[float, float, float, str], object]


# --- Conversion d'une ligne SIA en ImageRecord --------------------------------
def _val(row, col):
    """Valeur d'une colonne, None si absente ou masquée."""
    try:
        v = row[col]
    except (KeyError, IndexError):
        return None
    if getattr(v, "mask", False) is True:
        return None
    if isinstance(v, bytes):
        v = v.decode()
    return v


def _num(row, col) -> Optional[float]:
    v = _val(row, col)
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def _to_um(meters: Optional[float]) -> Optional[float]:
    return None if meters is None else round(meters * 1e6, 4)


def parse_polygon(s_region) -> Optional[list[tuple[float, float]]]:
    """'POLYGON ICRS ra1 dec1 ra2 dec2 ...' -> [(ra, dec), ...] (sans le point de fermeture)."""
    if not s_region or "POLYGON" not in str(s_region).upper():
        return None
    nums = [float(x) for x in str(s_region).split()
            if x.replace(".", "", 1).replace("-", "", 1).replace("e", "", 1).isdigit()]
    pts = list(zip(nums[0::2], nums[1::2]))
    if len(pts) > 3 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts if len(pts) >= 3 else None


def _tangent(ra, dec, ra0, dec0) -> tuple[float, float]:
    """Projection gnomonique (degrés) autour de (ra0, dec0) : gère le passage RA 0/360."""
    r, d, r0, d0 = map(math.radians, (ra, dec, ra0, dec0))
    cosc = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(r - r0)
    x = math.cos(d) * math.sin(r - r0) / cosc
    y = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(r - r0)) / cosc
    return math.degrees(x), math.degrees(y)


def _inside(x, y, poly) -> bool:
    inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def coverage(s_region, target: Target) -> tuple[bool, bool]:
    """(cible dans l'image ?, zone entière dans l'image ?). Si s_region absent : (True, True)."""
    pts = parse_polygon(s_region)
    if pts is None:
        return True, True
    poly = [_tangent(ra, dec, target.ra_deg, target.dec_deg) for ra, dec in pts]
    h = target.size_deg / 2
    center_in = _inside(0.0, 0.0, poly)
    corners_in = all(_inside(cx, cy, poly) for cx in (-h, h) for cy in (-h, h))
    return center_in, center_in and corners_in


def row_to_record(row, collection: str, target: Target) -> Optional[ImageRecord]:
    url = _val(row, "access_url")
    if not url or not str(url).split("?")[0].lower().endswith((".fits", ".fits.gz")):
        return None  # pas une image FITS (ex. produit auxiliaire)
    url = str(url)

    # SIA renvoie aussi des images qui touchent seulement le bord du cercle de recherche :
    # on ne garde que celles qui contiennent vraiment la cible (sinon le cutout échoue
    # avec "Arrays do not overlap").
    center_in, full = coverage(_val(row, "s_region"), target)
    if not center_in:
        return None

    band = str(_val(row, "energy_bandpassname") or "")   # ex. "SPHEREx-D2"
    detector = band.split("-")[-1] if "-D" in band else None

    t0, t1 = _num(row, "t_min"), _num(row, "t_max")
    t_mid = (t0 + t1) / 2 if t0 is not None and t1 is not None else (t0 or t1)
    date = Time(t_mid, format="mjd").isot[:19] + "Z" if t_mid is not None else None

    release = collection.replace("spherex_", "").split("_")[0]   # dr1 / qr3
    survey = "deep" if collection.endswith("_deep") else "wide"
    sep = "&" if "?" in url else "?"
    cutout = f"{url}{sep}center={target.ra_deg},{target.dec_deg}&size={target.size_deg}"

    size = _num(row, "access_estsize")   # en ko dans ObsCore
    return ImageRecord(
        obs_id=str(_val(row, "obs_id") or url.rsplit("/", 1)[-1]),
        release=release, survey=survey, detector=detector,
        t_start_mjd=t0, t_end_mjd=t1, t_mid_mjd=t_mid, date_utc=date,
        wl_min_um=_to_um(_num(row, "em_min")), wl_max_um=_to_um(_num(row, "em_max")),
        image_url=url, cutout_url=cutout,
        cloud_access=_val(row, "cloud_access"),
        size_mb=round(size / 1024, 1) if size else None,
        fully_covered=full,
    )


# --- Recherche principale -----------------------------------------------------
def search_images(target: Target, refresh: bool = False,
                  sia: SiaFn = _irsa_sia) -> SearchResult:
    key = f"{CACHE_VERSION}|{target.cache_key}|{','.join(config.COLLECTIONS)}"

    hit = cache_get(key)

    def from_cache(note: Optional[str] = None) -> SearchResult:
        data, created = hit
        data.update(source="cache", target=target.model_dump(),
                    cached_at=datetime.fromtimestamp(created, timezone.utc).isoformat())
        res = SearchResult(**data)
        if note:
            res.errors = [note] + list(res.errors)
        return res

    if not refresh and hit is not None:
        return from_cache()

    if config.DEMO_MODE:
        raise RuntimeError("DEMO_MODE actif et aucun résultat en cache pour cette cible. "
                           "Lancez le préchargement avant la démo.")

    t_start = time.perf_counter()
    records: dict[tuple, ImageRecord] = {}
    errors: list[str] = []
    for coll in config.COLLECTIONS:
        try:
            table = sia(target.ra_deg, target.dec_deg,
                        config.SEARCH_RADIUS_ARCSEC / 3600.0, coll)
        except Exception as exc:  # noqa: BLE001 — IRSA peut être lent ou en panne
            errors.append(f"{coll}: {type(exc).__name__}: {exc}")
            continue
        for row in table:
            rec = row_to_record(row, coll, target)
            if rec is not None:
                records.setdefault((rec.obs_id, rec.detector, rec.release, rec.survey), rec)  # sans doublons

    images = sorted(records.values(), key=lambda r: (r.t_mid_mjd or 0, r.detector or ""))
    if errors and hit is not None:
        # IRSA indisponible ou incomplet : on garde la dernière recherche complète en cache
        return from_cache("IRSA indisponible, résultat en cache utilisé : " + errors[0][:150])
    if not images and errors:
        raise ConnectionError("IRSA injoignable : " + " | ".join(errors))

    days = sorted({r.date_utc[:10] for r in images if r.date_utc})
    by_det: dict[str, int] = {}
    by_rel: dict[str, int] = {}
    by_srv: dict[str, int] = {}
    for r in images:
        by_det[r.detector or "?"] = by_det.get(r.detector or "?", 0) + 1
        by_rel[r.release] = by_rel.get(r.release, 0) + 1
        by_srv[r.survey] = by_srv.get(r.survey, 0) + 1

    result = SearchResult(
        target=target, source="irsa", cached_at=None,
        query_seconds=round(time.perf_counter() - t_start, 1),
        n_images=len(images), n_days=len(days),
        first_date=days[0] if days else None, last_date=days[-1] if days else None,
        by_detector=dict(sorted(by_det.items())), by_release=by_rel, by_survey=by_srv,
        errors=errors, images=images,
    )
    if not errors:  # ne pas figer en cache un résultat incomplet
        cache_set(key, result.model_dump(exclude={"source", "cached_at", "target"}))
    return result
