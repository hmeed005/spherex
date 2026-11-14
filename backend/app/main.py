from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core import config
from fastapi.middleware.cors import CORSMiddleware

from app.routers import images, target

app = FastAPI(title="SPHEREx Time-Lapse API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(target.router)
app.include_router(images.router)
# images rendues (PNG/GIF alignés) servies sous /files/...
app.mount("/files", StaticFiles(directory=str(config.CACHE_DIR)), name="files")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


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
