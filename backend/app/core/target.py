"""Étape 0 du pipeline : entrée utilisateur (cible + taille de la zone).

Transforme ce que l'utilisateur tape (coordonnées en degrés, en sexagésimal,
ou nom d'objet) en une cible normalisée et validée, utilisable par toutes les
étapes suivantes (recherche IRSA, cutouts, grille commune).
"""
from __future__ import annotations

import hashlib
import math
from typing import Optional

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from pydantic import BaseModel, Field, model_validator

# --- Constantes SPHEREx -----------------------------------------------------
PIXSCALE_ARCSEC = 6.15          # taille d'un pixel SPHEREx
MIN_SIZE_ARCMIN = 1.0           # en dessous : trop peu d'étoiles pour aligner/normaliser
MAX_SIZE_ARCMIN = 12.0          # au-dessus (0,2°) : cutouts trop lourds en interactif
DEFAULT_SIZE_ARCMIN = 6.0       # 0,1° ≈ 59 x 59 pixels
GALACTIC_CROWDING_DEG = 15.0    # |b| < 15° : champ dense, risque de mélange de sources
CATALOG_EPOCH = 2000.0          # époque des coordonnées saisies / du catalogue de démo
MISSION_MID_EPOCH = 2025.9      # milieu des données DR1 + QR3 (mai 2025 → nov. 2026)
MISSION_SPAN_YR = 1.5

# Cibles de démo résolues hors ligne (positions ICRS, époque J2000 / Gaia DR3 propagée).
# pm en mas/an. Utile si le service de résolution de noms (Sesame) est indisponible.
DEMO_TARGETS = {
    "barnard": dict(label="Étoile de Barnard", ra=269.452076, dec=4.693364,
                    pmra=-801.551, pmdec=10362.394),
    "wise 0855-0714": dict(label="WISE 0855-0714", ra=133.786245, dec=-7.244372,
                           pmra=-8118.0, pmdec=673.0),
    "nep": dict(label="Pôle nord écliptique", ra=270.0, dec=66.560708,
                pmra=0.0, pmdec=0.0),
}
ALIASES = {
    "barnard's star": "barnard", "barnards star": "barnard", "etoile de barnard": "barnard",
    "wise 0855": "wise 0855-0714", "wise0855": "wise 0855-0714",
    "north ecliptic pole": "nep", "pole nord ecliptique": "nep",
}


class TargetRequest(BaseModel):
    """Ce que le frontend envoie. Soit `name`, soit `ra` + `dec`."""

    name: Optional[str] = Field(None, description="Nom d'objet (ex. 'Barnard', 'M101')")
    ra: Optional[str] = Field(None, description="Ascension droite : degrés ('269.452') ou sexagésimal ('17h57m48.5s')")
    dec: Optional[str] = Field(None, description="Déclinaison : degrés ('4.693') ou sexagésimal ('+04d41m36s')")
    size_arcmin: float = Field(DEFAULT_SIZE_ARCMIN, ge=MIN_SIZE_ARCMIN, le=MAX_SIZE_ARCMIN,
                               description="Côté de la zone carrée autour de la cible, en minutes d'arc")

    @model_validator(mode="after")
    def _name_or_coords(self):
        has_coords = self.ra is not None and self.dec is not None
        if not self.name and not has_coords:
            raise ValueError("Fournir soit 'name', soit 'ra' et 'dec'.")
        if (self.ra is None) != (self.dec is None):
            raise ValueError("'ra' et 'dec' doivent être fournis ensemble.")
        return self


class Target(BaseModel):
    """Cible normalisée, partagée par toutes les étapes du pipeline."""

    label: str
    ra_deg: float
    dec_deg: float
    size_arcmin: float
    size_deg: float
    size_px: int
    radius_deg: float = Field(description="Demi-diagonale de la zone : rayon de recherche IRSA")
    galactic_l: float
    galactic_b: float
    ecliptic_lat: float
    pmra: Optional[float] = Field(None, description="Mouvement propre connu (cibles de démo), mas/an")
    pmdec: Optional[float] = Field(None, description="Mouvement propre connu (cibles de démo), mas/an")
    resolved_by: str = Field(description="'coordinates', 'demo_catalog' ou 'sesame'")
    cache_key: str
    warnings: list[str] = []


def _parse_coords(ra: str, dec: str) -> SkyCoord:
    """Accepte des degrés décimaux ou du sexagésimal."""
    ra, dec = ra.strip(), dec.strip()
    try:
        return SkyCoord(float(ra) * u.deg, float(dec) * u.deg, frame="icrs")
    except ValueError:
        pass
    # Sexagésimal : RA en heures si elle contient 'h' ou ':' sans 'd'
    ra_unit = u.hourangle if ("h" in ra.lower() or (":" in ra and "d" not in ra.lower())) else u.deg
    try:
        return SkyCoord(ra, dec, unit=(ra_unit, u.deg), frame="icrs")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Coordonnées illisibles : ra='{ra}', dec='{dec}' ({exc})") from exc


def _resolve_name(name: str) -> tuple[SkyCoord, str, dict]:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key in DEMO_TARGETS:
        t = DEMO_TARGETS[key]
        return SkyCoord(t["ra"] * u.deg, t["dec"] * u.deg), "demo_catalog", t
    try:  # résolution en ligne (CDS Sesame) ; peut échouer si réseau indisponible
        return SkyCoord.from_name(name), "sesame", {"label": name}
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Objet '{name}' introuvable ({exc}). Essayez des coordonnées RA/Dec.") from exc


def resolve_target(req: TargetRequest) -> Target:
    extra: dict = {}
    if req.ra is not None:
        coord, how = _parse_coords(req.ra, req.dec), "coordinates"
        label = req.name or f"RA {req.ra} / Dec {req.dec}"
    else:
        coord, how, extra = _resolve_name(req.name)
        label = extra.get("label", req.name)

    # Mouvement propre : uniquement pour les cibles de démo connues (pas une saisie utilisateur)
    pmra = extra.get("pmra")
    pmdec = extra.get("pmdec")
    warnings: list[str] = []

    # Objet à fort mouvement propre : centrer la zone sur sa position au milieu
    # de la mission SPHEREx (et non à J2000, où il n'est plus).
    if pmra and pmdec and math.hypot(pmra, pmdec) > 100:  # > 0,1"/an
        moving = SkyCoord(ra=coord.ra, dec=coord.dec, pm_ra_cosdec=pmra * u.mas / u.yr,
                          pm_dec=pmdec * u.mas / u.yr, obstime=Time(CATALOG_EPOCH, format="jyear"),
                          frame="icrs")
        coord = moving.apply_space_motion(new_obstime=Time(MISSION_MID_EPOCH, format="jyear"))
        warnings.append(f"Zone centrée sur la position de l'objet en {MISSION_MID_EPOCH} "
                        f"(propagée depuis J{CATALOG_EPOCH} avec son mouvement propre).")

    ra = float(coord.ra.wrap_at(360 * u.deg).deg)   # RA toujours dans [0, 360[
    dec = float(coord.dec.deg)
    if not -90.0 <= dec <= 90.0:
        raise ValueError(f"Déclinaison hors limites : {dec}")

    size_deg = req.size_arcmin / 60.0
    size_px = int(round(req.size_arcmin * 60.0 / PIXSCALE_ARCSEC))
    radius_deg = size_deg * math.sqrt(2) / 2

    gal = coord.galactic
    ecl = coord.barycentrictrueecliptic
    if abs(gal.b.deg) < GALACTIC_CROWDING_DEG:
        warnings.append(f"|b| = {abs(gal.b.deg):.1f}° < {GALACTIC_CROWDING_DEG}° : champ dense, "
                        "risque de sources mélangées (faux mouvements).")
    if abs(dec) > 85:
        warnings.append("Cible proche d'un pôle céleste : vérifier l'orientation de la grille.")
    if pmra is not None and pmdec is not None:
        pm_total = math.hypot(pmra, pmdec) / 1000.0  # arcsec/an
        if pm_total > 1.0:
            warnings.append(f"Mouvement propre élevé ({pm_total:.1f}\"/an) : la position sera "
                            "propagée à la date de chaque image.")
        # déplacement pendant la mission (~2 ans) vs taille de la zone
        drift_arcmin = pm_total * MISSION_SPAN_YR / 60
        if drift_arcmin > req.size_arcmin / 4:
            warnings.append(f"L'objet se déplace d'environ {drift_arcmin:.1f}' pendant la mission : "
                            "agrandir la zone.")
    if abs(ecl.lat.deg) > 80:
        warnings.append("Proche d'un pôle écliptique : beaucoup d'époques disponibles (bon champ).")

    # Clé de cache : position arrondie à ~0,36" + taille, pour réutiliser les requêtes IRSA
    raw = f"{ra:.4f}|{dec:.4f}|{req.size_arcmin:.2f}"
    cache_key = hashlib.sha1(raw.encode()).hexdigest()[:16]

    return Target(
        label=label, ra_deg=round(ra, 7), dec_deg=round(dec, 7),
        size_arcmin=req.size_arcmin, size_deg=round(size_deg, 6), size_px=size_px,
        radius_deg=round(radius_deg, 6),
        galactic_l=round(float(gal.l.deg), 4), galactic_b=round(float(gal.b.deg), 4),
        ecliptic_lat=round(float(ecl.lat.deg), 4),
        pmra=pmra, pmdec=pmdec, resolved_by=how, cache_key=cache_key, warnings=warnings,
    )
