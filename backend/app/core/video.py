"""Vidéo finale : MP4 + frise temporelle synchronisable + sous-titres WebVTT (+ GIF de secours).

Chaque image (une date) est tenue HOLD_S secondes, puis un fondu de FADE_S secondes mène à la
suivante. La frise (« timeline ») donne, pour chaque image, l'instant exact où elle apparaît
dans la vidéo : le frontend synchronise ainsi le panneau de détails et la vidéo dans les deux
sens (video.currentTime <-> entrée de la frise), sans aucun calcul de son côté.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

HOLD_S = 3.0          # durée d'affichage de chaque date
FADE_S = 1.2          # durée du fondu enchaîné vers la date suivante
FPS = 20


class TimelineEntry(BaseModel):
    index: int
    t_start_s: float          # l'image apparaît (fin du fondu précédent)
    t_hold_end_s: float       # début du fondu vers l'image suivante
    t_end_s: float            # l'image suivante est entièrement affichée
    seek_s: float             # instant conseillé pour « aller à cette date »
    frame_id: str
    date_utc: str
    detector: Optional[str] = None
    wavelength_um: Optional[float] = None
    group: Optional[str] = None
    status: Optional[str] = None
    snr: Optional[float] = None
    target_measured_px: Optional[tuple[float, float]] = None
    target_predicted_px: Optional[tuple[float, float]] = None
    used_in_fit: bool = True
    note: Optional[str] = None
    wavelength_change: Optional[str] = None
    group_changed: bool = False          # début d'un nouveau bloc (passage au groupe suivant)
    previous_group: Optional[str] = None # nom du bloc précédent
    disagreement: bool = False           # image d'un groupe en désaccord
    segment_index: int = 0               # bloc 0 = groupes concordants, puis 1 bloc par groupe
    segment_label: str = ""              # "groupes concordants" | "groupe D5_4.326" ...
    image_url: Optional[str] = None      # image fixe de cette date (PNG)


class VideoAssets(BaseModel):
    mp4: Optional[str] = None             # vidéo PROPRE : uniquement l'image du ciel
    mp4_markers: Optional[str] = None     # même vidéo + repères (positions, trajectoire), sans texte
    gif: Optional[str] = None
    vtt: Optional[str] = None
    duration_s: float
    fps: int = FPS
    hold_s: float = HOLD_S
    fade_s: float = FADE_S
    width: int
    height: int
    mp4_error: Optional[str] = None
    # pour dessiner des repères côté frontend : pixel de grille (x, y) -> pixel vidéo
    #   u = (x + 0.5) * px_scale ;  v = height - (y + 0.5) * px_scale   (nord en haut)
    grid_size_px: Optional[int] = None
    px_scale: Optional[float] = None
    timeline: list[TimelineEntry]


def _even(a: np.ndarray) -> np.ndarray:
    """H.264 (yuv420p) exige des dimensions paires."""
    h, w = a.shape[:2]
    return a[: h - h % 2, : w - w % 2]


def _vtt_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def build_video(rgb_frames: list[np.ndarray], entries: list[dict], out_prefix: Path,
                hold_s: float = HOLD_S, fade_s: float = FADE_S, fps: int = FPS,
                loop_back: bool = True, make_gif: bool = True,
                make_vtt: bool = True) -> VideoAssets:
    """rgb_frames : une image RGB (H, W, 3) par date ; entries : détails de chaque date."""
    frames = [_even(np.clip(f, 0, 255).astype(np.uint8)) for f in rgb_frames]
    h, w = frames[0].shape[:2]
    n_hold, n_fade = max(1, round(hold_s * fps)), max(0, round(fade_s * fps))
    period = (n_hold + n_fade) / fps
    n = len(frames)

    # ---- frise temporelle (identique pour MP4, GIF et sous-titres)
    timeline = []
    for k, e in enumerate(entries):
        t0 = k * period
        timeline.append(TimelineEntry(index=k, t_start_s=round(t0, 3),
                                      t_hold_end_s=round(t0 + hold_s, 3),
                                      t_end_s=round(t0 + period, 3), seek_s=round(t0 + 0.05, 3),
                                      **e))
    has_fade_after = [k < n - 1 or (loop_back and n > 1) for k in range(n)]
    duration = sum(n_hold + (n_fade if has_fade_after[k] else 0) for k in range(n)) / fps

    def frame_stream():
        for k in range(n):
            for _ in range(n_hold):
                yield frames[k]
            if has_fade_after[k]:
                nxt = frames[(k + 1) % n]
                for s in range(1, n_fade + 1):
                    t = s / (n_fade + 1)
                    yield ((1 - t) * frames[k] + t * nxt).astype(np.uint8)

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    assets = dict(duration_s=round(duration, 3), fps=fps, hold_s=hold_s, fade_s=fade_s,
                  width=w, height=h, timeline=timeline)

    # ---- MP4 (H.264) ; si ffmpeg est indisponible ou bloqué, on garde le GIF
    mp4 = out_prefix.with_suffix(".mp4")
    try:
        import imageio_ffmpeg
        writer = imageio_ffmpeg.write_frames(
            str(mp4), (w, h), fps=fps, codec="libx264", pix_fmt_in="rgb24", quality=None,
            pix_fmt_out="yuv420p",
            output_params=["-preset", "veryfast", "-crf", "20",
                           "-movflags", "+faststart"], macro_block_size=1)
        writer.send(None)
        for fr in frame_stream():
            writer.send(np.ascontiguousarray(fr))
        writer.close()
        assets["mp4"] = str(mp4)
    except Exception as exc:  # noqa: BLE001
        assets["mp4_error"] = f"{type(exc).__name__}: {str(exc)[:160]}"

    # ---- GIF de secours : seulement si demandé OU si le MP4 a échoué (lent et lourd)
    try:
        if not make_gif and assets.get("mp4"):
            raise StopIteration
        from PIL import Image
        gif_frames, durs = [], []
        step = max(1, n_fade // 8)
        for k in range(n):
            gif_frames.append(Image.fromarray(frames[k]))
            durs.append(int(hold_s * 1000))
            if has_fade_after[k]:
                nxt = frames[(k + 1) % n]
                for s in range(step, n_fade + 1, step):
                    t = s / (n_fade + 1)
                    gif_frames.append(Image.fromarray(((1 - t) * frames[k] + t * nxt).astype(np.uint8)))
                    durs.append(int(1000 * fade_s * step / max(n_fade, 1)))
        gif = out_prefix.with_suffix(".gif")
        if len(gif_frames) > 1:
            gif_frames[0].save(gif, save_all=True, append_images=gif_frames[1:], duration=durs, loop=0)
            assets["gif"] = str(gif)
    except (Exception, StopIteration):  # noqa: BLE001
        pass

    # ---- sous-titres WebVTT (optionnels : les détails sont affichés HORS de la vidéo)
    if not make_vtt:
        return VideoAssets(**assets)
    vtt = out_prefix.with_suffix(".vtt")
    lines = ["WEBVTT", ""]
    for e in timeline:
        txt = f"{e.date_utc[:10]} · {e.detector or ''} · λ = {e.wavelength_um:.3f} µm" \
            if e.wavelength_um else e.date_utc[:10]
        lines += [f"{_vtt_time(e.t_start_s)} --> {_vtt_time(e.t_end_s)}", txt]
        if e.note:
            lines.append(e.note)
        if e.wavelength_change:
            lines.append(e.wavelength_change)
        lines.append("")
    vtt.write_text("\n".join(lines), encoding="utf-8")
    assets["vtt"] = str(vtt)
    return VideoAssets(**assets)
