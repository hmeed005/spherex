"""Test réel de l'étape Search (à lancer chez vous, avec internet) :
    python -m scripts.try_search Barnard
"""
import sys
import time

from app.core.search import search_images
from app.core.target import TargetRequest, resolve_target

name = sys.argv[1] if len(sys.argv) > 1 else "Barnard"
t = resolve_target(TargetRequest(name=name))
print(f"Cible : {t.label}  RA={t.ra_deg}  Dec={t.dec_deg}  rayon={t.radius_deg} deg")
print("Requête IRSA en cours (20 à 60 s)...")
t0 = time.time()
r = search_images(t)
print(f"Source : {r.source}  en {time.time() - t0:.1f} s")
print(f"{r.n_images} images, {r.n_days} jours distincts, du {r.first_date} au {r.last_date}")
print("Par détecteur :", r.by_detector)
print("Par version   :", r.by_release)
print("Par relevé    :", r.by_survey)
if r.errors:
    print("ERREURS :", r.errors)
for img in r.images[:3]:
    print(" -", img.date_utc, img.detector, img.release, img.obs_id)
    print("   ", img.cutout_url)
