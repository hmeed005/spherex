"""Réglages du backend (modifiables par variables d'environnement)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = Path(os.getenv("CACHE_DIR", BASE_DIR / "cache"))
DB_PATH = Path(os.getenv("DB_PATH", CACHE_DIR / "spherex.sqlite"))

# Collections IRSA à interroger (DR1 = année 1 retraitée, QR3 = année 2 ;
# "_deep" = relevé profond aux pôles écliptiques, beaucoup plus d'époques)
COLLECTIONS = os.getenv(
    "COLLECTIONS", "spherex_dr1,spherex_dr1_deep,spherex_qr3,spherex_qr3_deep").split(",")

# Rayon de recherche SIA : petit, pour n'obtenir que les images qui CONTIENNENT la cible
# (méthode du tutoriel IRSA "Data Overview")
SEARCH_RADIUS_ARCSEC = float(os.getenv("SEARCH_RADIUS_ARCSEC", "1"))

# Délai max d'une requête IRSA (s) ; les requêtes SPHEREx prennent 20-40 s
IRSA_TIMEOUT = int(os.getenv("IRSA_TIMEOUT", "180"))

# true = n'utiliser que le cache, aucune requête externe (pour la démo)
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# --- Mise à jour automatique : SPHEREx publie de nouvelles images sur IRSA chaque semaine.
# Le serveur revérifie IRSA pour chaque résultat déjà calculé tous les UPDATE_EVERY_DAYS jours
# et ne recalcule que s'il y a de nouvelles images (sans jamais faire attendre le site).
AUTO_UPDATE = os.getenv("SPHEREX_AUTO_UPDATE", "true").lower() == "true" and not DEMO_MODE
UPDATE_EVERY_DAYS = float(os.getenv("SPHEREX_UPDATE_EVERY_DAYS", "7"))
UPDATE_CHECK_HOURS = float(os.getenv("SPHEREX_UPDATE_CHECK_HOURS", "6"))     # tour de vérification
UPDATE_START_DELAY_S = float(os.getenv("SPHEREX_UPDATE_START_DELAY_S", "60"))
UPDATE_RETRY_MINUTES = float(os.getenv("SPHEREX_UPDATE_RETRY_MINUTES", "60"))  # si IRSA en panne

CACHE_DIR.mkdir(parents=True, exist_ok=True)
