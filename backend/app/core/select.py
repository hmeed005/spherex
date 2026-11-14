"""Étape 1b du pipeline : SELECT (avant tout téléchargement).

À partir de la liste d'images de l'étape Search (métadonnées seulement) :
1. filtre : cible bien couverte, détecteur demandé ;
2. groupe les images en PASSAGES (époques) d'après leurs dates ;
3. choisit un nombre limité d'images par passage et par détecteur, réparties dans le
   temps, pour que le téléchargement des cutouts reste raisonnable.

Le regroupement par longueur d'onde viendra APRÈS le téléchargement : la longueur
d'onde au pixel de la cible se lit dans l'en-tête de chaque cutout.
"""
from __future__ import annotations

from typing import Optional

from astropy.time import Time
from pydantic import BaseModel

from app.core.search import ImageRecord, SearchResult
from app.core.target import Target

# Deux images séparées de plus de VISIT_GAP_DAYS appartiennent à des passages différents.
# (Données réelles Barnard : un passage s'étale sur ~2 semaines, puis ~6 mois de vide.)
VISIT_GAP_DAYS = 7.0
# Champs profonds (pôles écliptiques) : observés presque tous les jours, donc pas de trou.
# On découpe alors les longues séries en époques de VISIT_MAX_DAYS jours.
VISIT_MAX_DAYS = 30.0
# Un passage avec moins d'images est marqué "mineur" (souvent quelques images isolées)
MIN_VISIT_IMAGES = 6
# Nombre max d'images gardées par (passage, détecteur), et au total
MAX_PER_VISIT_DETECTOR = 8
MAX_TOTAL = 200


class Visit(BaseModel):
    index: int
    start: str
    end: str
    duration_days: float
    n_images: int
    n_selected: int
    by_detector: dict[str, int]
    minor: bool


class Rejection(BaseModel):
    obs_id: str
    detector: Optional[str]
    reason: str


class SelectionResult(BaseModel):
    target: Target
    detector_filter: Optional[str]
    n_found: int
    n_kept: int                    # après filtres
    n_selected: int                # à télécharger
    n_visits: int
    n_major_visits: int
    usable_for_motion: bool        # au moins 3 passages principaux
    visits: list[Visit]
    selected: list[ImageRecord]
    n_rejected: int
    rejected_reasons: dict[str, int]
    rejected_sample: list[Rejection]


def _date(mjd: float) -> str:
    return Time(mjd, format="mjd").isot[:10]


def split_into_visits(images: list[ImageRecord]) -> list[list[ImageRecord]]:
    """Groupe des images (triées par date) en passages."""
    imgs = sorted((i for i in images if i.t_mid_mjd is not None), key=lambda i: i.t_mid_mjd)
    chains: list[list[ImageRecord]] = []
    for img in imgs:
        if chains and img.t_mid_mjd - chains[-1][-1].t_mid_mjd <= VISIT_GAP_DAYS:
            chains[-1].append(img)
        else:
            chains.append([img])
    # découper les séries trop longues (champs profonds) en tranches de VISIT_MAX_DAYS
    visits: list[list[ImageRecord]] = []
    for chain in chains:
        t0 = chain[0].t_mid_mjd
        if chain[-1].t_mid_mjd - t0 <= VISIT_MAX_DAYS:
            visits.append(chain)
            continue
        bins: dict[int, list[ImageRecord]] = {}
        for img in chain:
            bins.setdefault(int((img.t_mid_mjd - t0) // VISIT_MAX_DAYS), []).append(img)
        visits.extend(bins[k] for k in sorted(bins))
    return visits


def _spread(items: list[ImageRecord], n: int) -> list[ImageRecord]:
    """Choisit n images réparties régulièrement dans le temps (pointages variés)."""
    if len(items) <= n:
        return list(items)
    step = (len(items) - 1) / (n - 1) if n > 1 else 0
    return [items[round(k * step)] for k in range(n)]


def select_images(search: SearchResult, detector: Optional[str] = None,
                  require_full_coverage: bool = True,
                  max_per_visit_detector: int = MAX_PER_VISIT_DETECTOR,
                  max_total: int = MAX_TOTAL) -> SelectionResult:
    rejected: list[Rejection] = []

    def reject(img: ImageRecord, reason: str):
        rejected.append(Rejection(obs_id=img.obs_id, detector=img.detector, reason=reason))

    kept: list[ImageRecord] = []
    for img in search.images:
        if detector and img.detector != detector:
            continue  # simple filtre, pas un rejet
        if img.t_mid_mjd is None:
            reject(img, "date manquante")
        elif img.detector is None:
            reject(img, "détecteur inconnu")
        elif require_full_coverage and not img.fully_covered:
            reject(img, "zone demandée partiellement hors de l'image")
        else:
            kept.append(img)

    visit_groups = split_into_visits(kept)

    # sélection par (passage, détecteur)
    per_visit: list[list[ImageRecord]] = []
    for group in visit_groups:
        by_det: dict[str, list[ImageRecord]] = {}
        for img in group:
            by_det.setdefault(img.detector, []).append(img)
        chosen = []
        for det in sorted(by_det):
            chosen += _spread(by_det[det], max_per_visit_detector)
        per_visit.append(chosen)

    # plafond global : on réduit chaque passage proportionnellement, sans en supprimer
    total = sum(len(c) for c in per_visit)
    if total > max_total:
        ratio = max_total / total
        per_visit = [_spread(sorted(c, key=lambda i: i.t_mid_mjd), max(1, int(len(c) * ratio)))
                     for c in per_visit]

    visits, selected = [], []
    for k, (group, chosen) in enumerate(zip(visit_groups, per_visit)):
        by_det_count: dict[str, int] = {}
        for img in group:
            by_det_count[img.detector] = by_det_count.get(img.detector, 0) + 1
        t0, t1 = group[0].t_mid_mjd, group[-1].t_mid_mjd
        visits.append(Visit(
            index=k, start=_date(t0), end=_date(t1), duration_days=round(t1 - t0, 1),
            n_images=len(group), n_selected=len(chosen),
            by_detector=dict(sorted(by_det_count.items())),
            minor=len(group) < MIN_VISIT_IMAGES,
        ))
        selected += chosen

    reasons: dict[str, int] = {}
    for r in rejected:
        reasons[r.reason] = reasons.get(r.reason, 0) + 1
    n_major = sum(not v.minor for v in visits)

    return SelectionResult(
        target=search.target, detector_filter=detector,
        n_found=len(search.images), n_kept=len(kept), n_selected=len(selected),
        n_visits=len(visits), n_major_visits=n_major, usable_for_motion=n_major >= 3,
        visits=visits, selected=sorted(selected, key=lambda i: (i.t_mid_mjd, i.detector)),
        n_rejected=len(rejected), rejected_reasons=reasons, rejected_sample=rejected[:20],
    )
