"""Tests de la vidéo finale : MP4 + frise temporelle + sous-titres."""
import numpy as np

from app.core.video import build_video


def test_timeline_and_files(tmp_path):
    frames = [np.full((101, 99, 3), v, np.uint8) for v in (20, 120, 220)]   # dimensions impaires
    entries = [dict(frame_id=f"f{k}", date_utc=f"2025-0{k + 1}-01T00:00:00Z", detector="D2",
                    wavelength_um=1.5, group="G", note="note" if k == 1 else None) for k in range(3)]
    v = build_video(frames, entries, tmp_path / "seq", hold_s=2.0, fade_s=1.0, fps=10)
    assert [e.t_start_s for e in v.timeline] == [0.0, 3.0, 6.0]
    assert all(e.t_start_s < e.seek_s < e.t_hold_end_s for e in v.timeline)
    assert v.duration_s == 9.0                     # 3 x (2 s + 1 s), avec retour au début
    assert v.width % 2 == 0 and v.height % 2 == 0  # exigé par H.264
    assert v.mp4 and (tmp_path / "seq.mp4").stat().st_size > 0, v.mp4_error
    vtt = (tmp_path / "seq.vtt").read_text(encoding="utf-8")
    assert vtt.startswith("WEBVTT") and "00:00:03.000 --> 00:00:06.000" in vtt and "note" in vtt
