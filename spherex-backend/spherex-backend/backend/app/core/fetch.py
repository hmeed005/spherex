"""Étape 2 du pipeline : FETCH — téléchargement des cutouts (parallèle, cache, reprises)."""
from __future__ import annotations

import hashlib
import http.client
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

from app.core import config

CUTOUT_DIR = Path(config.CACHE_DIR) / "cutouts"
MAX_WORKERS = 12         # IRSA conseille 7 à 12 téléchargements simultanés
RETRIES = 4
RETRY_ERRORS = (TimeoutError, urllib.error.URLError, http.client.IncompleteRead,
                ConnectionError, OSError)


def cutout_path(url: str) -> Path:
    return CUTOUT_DIR / (hashlib.sha1(url.encode()).hexdigest()[:20] + ".fits")


def _download(url: str, dest: Path) -> None:
    from astropy.io import fits
    tmp = dest.with_suffix(".part")
    with fits.open(url, memmap=False, cache=False) as hdul:
        hdul.writeto(tmp, overwrite=True)
    tmp.replace(dest)  # écriture atomique : jamais de fichier à moitié écrit dans le cache


def fetch_one(url: str, downloader: Callable[[str, Path], None] = _download,
              sleep: Callable[[float], None] = time.sleep) -> tuple[Optional[Path], Optional[str]]:
    """Renvoie (chemin, None) ou (None, message d'erreur). Ne lève pas d'exception."""
    if config.DEMO_MODE and not cutout_path(url).exists():
        return None, "DEMO_MODE : cutout absent du cache"
    CUTOUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = cutout_path(url)
    if dest.exists() and dest.stat().st_size > 0:
        return dest, None
    last = ""
    for attempt in range(RETRIES):
        try:
            downloader(url, dest)
            return dest, None
        except RETRY_ERRORS as exc:
            last = f"{type(exc).__name__}: {exc}"
            msg = str(exc)
            if "422" in msg or "overlap" in msg.lower():
                return None, "cible hors de l'image (422)"   # inutile de réessayer
            if attempt < RETRIES - 1:
                sleep(10 * (attempt + 1))                     # 503 : IRSA surchargé
    return None, last[:200]


def fetch_many(urls: list[str], max_workers: int = MAX_WORKERS,
               progress: Optional[Callable[[int, int], None]] = None,
               **kw) -> dict[str, tuple[Optional[Path], Optional[str]]]:
    results: dict[str, tuple[Optional[Path], Optional[str]]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {url: pool.submit(fetch_one, url, **kw) for url in urls}
        for i, (url, fut) in enumerate(futures.items(), 1):
            results[url] = fut.result()
            if progress:
                progress(i, len(urls))
    return results
