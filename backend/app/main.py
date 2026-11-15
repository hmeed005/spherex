from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core import config
from fastapi.middleware.cors import CORSMiddleware

from app.routers import images, target, updates

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app):
    """Au démarrage : planificateur des mises à jour hebdomadaires (nouvelles images SPHEREx)."""
    import asyncio
    from app.routers import updates
    task = asyncio.ensure_future(updates.scheduler_loop()) if config.AUTO_UPDATE else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="SPHEREx Time-Lapse API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(target.router)
app.include_router(images.router)
app.include_router(updates.router)
# images rendues (PNG/GIF alignés) servies sous /files/...
app.mount("/files", StaticFiles(directory=str(config.CACHE_DIR)), name="files")


# Frontend (dossier ../frontend à la racine du dépôt) servi sous /app/ :
# même adresse que l'API -> pas de problème de CORS ni d'IP à configurer.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/app/" if FRONTEND_DIR.is_dir() else "/docs")


@app.get("/player", include_in_schema=False)
def player():
    """Page de démonstration : vidéo MP4 synchronisée avec le panneau de détails."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    return FileResponse(Path(__file__).parent / "static" / "player.html")


@app.get("/api/health")
def health():
    """État du serveur + diagnostic de l'encodage vidéo MP4."""
    import sys
    info = {"status": "ok", "python": sys.executable}
    try:
        import imageio_ffmpeg
        info["mp4_encoder"] = "ok"
        info["ffmpeg"] = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        info["mp4_encoder"] = f"indisponible : {type(exc).__name__}: {exc}"
        info["fix"] = f'"{sys.executable}" -m pip install imageio-ffmpeg'
    return info
