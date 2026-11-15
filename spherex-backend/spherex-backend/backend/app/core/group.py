"""Étape 4 du pipeline : GROUP — séquences d'images à longueur d'onde comparable.

Problème : SPHEREx observe chaque point du ciel à une longueur d'onde différente selon
le pointage (filtres à variation linéaire). Une étoile change donc d'éclat d'une image à
l'autre même si rien ne bouge. On ne compare que des images prises à une longueur
d'onde proche AU PIXEL DE LA CIBLE (mesurée à l'étape Screen).

Algorithme (par détecteur) :
  1. chaque image gardée est rattachée à son passage (époque) ;
  2. fenêtre glissante sur les longueurs d'onde triées : une fenêtre [λmin, λmax] est
     valide si toutes ses images sont à ±tol de son milieu λc = (λmin + λmax) / 2 ;
     on compte les passages distincts dans chaque fenêtre ;
  3. on retient le centre qui couvre le plus de passages (puis le plus d'images, puis la
     plus faible dispersion), on retire ses images, et on recommence ;
  4. dans chaque groupe, une image par passage : la plus proche de λc, à qualité égale.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from astropy.time import Time
from pydantic import BaseModel

from app.core.screen import FrameQuality

WL_TOLERANCE = 0.03          # ±3 % autour de la longueur d'onde centrale
MIN_EPOCHS_FOR_MOTION = 3
STATUS_RANK = {"nette": 0, "saturee": 1, "decalee": 2, "faible": 3}


class GroupFrame(BaseModel):
    frame_id: Optional[str]
    obs_id: str
    date_utc: Optional[str]
    visit: int
    wavelength_um: float
    delta_wl_rel: float          # (λ - λc) / λc
    status: str
    snr: Optional[float]


class WavelengthGroup(BaseModel):
    id: str
    detector: str
    wavelength_um: float         # λc
    wl_min_um: float
    wl_max_um: float
    max_delta_rel: float         # dispersion réelle du groupe
    n_epochs: int
    n_candidates: int            # toutes les images du groupe (avant 1 par passage)
    span_days: float
    max_gap_days: Optional[float]
    usable_for_motion: bool
    frames: list[GroupFrame]     # 1 image par passage, triées par date


class GroupResult(BaseModel):
    tolerance: float
    n_frames_in: int
    n_without_wavelength: int
    n_groups: int
    default_group: Optional[str]
    groups: list[WavelengthGroup]
    ungrouped: list[str]         # frame_id des images restées seules (1 seul passage)


def _mjd(date_utc: str) -> float:
    return float(Time(date_utc.rstrip("Z"), format="isot").mjd)


def visit_of(date_utc: Optional[str], visits) -> Optional[int]:
    """Index du passage contenant cette date (visits : liste d'objets Visit de Select)."""
    if not date_utc:
        return None
    d = date_utc[:10]
    for v in visits:
        if v.start <= d <= v.end:
            return v.index
    return None


def group_frames(frames: list[FrameQuality], visits, tolerance: float = WL_TOLERANCE,
                 min_epochs: int = 2) -> GroupResult:
    usable = [f for f in frames if f.keep]
    no_wl = [f for f in usable if f.wavelength_um is None or f.detector is None]
    pool = [(f, visit_of(f.date_utc, visits)) for f in usable
            if f.wavelength_um is not None and f.detector is not None]
    pool = [(f, v) for f, v in pool if v is not None]

    groups: list[WavelengthGroup] = []
    ungrouped: list[str] = []
    for det in sorted({f.detector for f, _ in pool}):
        remaining = [(f, v) for f, v in pool if f.detector == det]
        while remaining:
            remaining.sort(key=lambda fv: fv[0].wavelength_um)
            wls_all = [f.wavelength_um for f, _ in remaining]
            best = None
            for i in range(len(remaining)):
                j = i
                # agrandir la fenêtre tant que tout reste à ±tol du milieu
                while (j + 1 < len(remaining) and
                       wls_all[j + 1] - wls_all[i] <= tolerance * (wls_all[i] + wls_all[j + 1])):
                    j += 1
                lc = (wls_all[i] + wls_all[j]) / 2
                members = remaining[i:j + 1]
                n_vis = len({v for _, v in members})
                spread = float(np.mean([abs(f.wavelength_um - lc) / lc for f, _ in members]))
                key = (n_vis, len(members), -spread)
                if best is None or key > best[0]:
                    best = (key, lc, members)
            (n_vis, _, _), lc, members = best
            if n_vis < min_epochs:
                ungrouped += [f.frame_id or f.obs_id for f, _ in remaining]
                break
            # une image par passage : meilleure qualité, puis la plus proche de λc
            per_visit: dict[int, FrameQuality] = {}
            for f, v in members:
                cur = per_visit.get(v)
                k = (STATUS_RANK.get(f.status, 9), abs(f.wavelength_um - lc))
                if cur is None or k < (STATUS_RANK.get(cur.status, 9),
                                       abs(cur.wavelength_um - lc)):
                    per_visit[v] = f
            chosen = sorted(per_visit.items(), key=lambda kv: kv[1].date_utc or "")
            mjds = [_mjd(f.date_utc) for _, f in chosen]
            gaps = np.diff(mjds) if len(mjds) > 1 else np.array([])
            wls = [f.wavelength_um for _, f in chosen]
            groups.append(WavelengthGroup(
                id=f"{det}_{lc:.3f}",
                detector=det, wavelength_um=round(lc, 4),
                wl_min_um=round(min(wls), 4), wl_max_um=round(max(wls), 4),
                max_delta_rel=round(max(abs(w - lc) / lc for w in wls), 4),
                n_epochs=len(chosen), n_candidates=len(members),
                span_days=round(mjds[-1] - mjds[0], 1) if mjds else 0.0,
                max_gap_days=round(float(gaps.max()), 1) if gaps.size else None,
                usable_for_motion=len(chosen) >= MIN_EPOCHS_FOR_MOTION,
                frames=[GroupFrame(frame_id=f.frame_id, obs_id=f.obs_id, date_utc=f.date_utc,
                                   visit=v, wavelength_um=round(f.wavelength_um, 4),
                                   delta_wl_rel=round((f.wavelength_um - lc) / lc, 4),
                                   status=f.status, snr=f.snr)
                        for v, f in chosen],
            ))
            used = {id(f) for f, _ in members}
            remaining = [(f, v) for f, v in remaining if id(f) not in used]

    # tri : d'abord les groupes avec le plus de passages, puis la plus longue durée couverte
    groups.sort(key=lambda g: (g.n_epochs, g.span_days, g.n_candidates), reverse=True)
    return GroupResult(
        tolerance=tolerance, n_frames_in=len(usable), n_without_wavelength=len(no_wl),
        n_groups=len(groups), default_group=groups[0].id if groups else None,
        groups=groups, ungrouped=ungrouped,
    )
