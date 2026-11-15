"""Tests de l'étape Group (longueurs d'onde comparables)."""
from app.core.group import group_frames
from app.core.screen import FrameQuality
from app.core.select import Visit


def visit(i, start, end):
    return Visit(index=i, start=start, end=end, duration_days=1, n_images=10, n_selected=2,
                 by_detector={}, minor=False)


VISITS = [visit(0, "2025-08-15", "2025-09-05"), visit(1, "2026-03-11", "2026-03-25"),
          visit(2, "2026-08-16", "2026-09-02")]


def frame(fid, date, wl, det="D2", status="saturee", keep=True):
    return FrameQuality(frame_id=fid, obs_id=fid, detector=det, date_utc=date + "T00:00:00Z",
                        status=status, keep=keep, reason="", wavelength_um=wl, snr=300.0)


def test_real_barnard_d2_wavelengths():
    """Les 5 VRAIES images D2 de Barnard (dates et longueurs d'onde mesurées)."""
    frames = [frame("a", "2025-08-21", 1.101), frame("b", "2025-08-30", 1.496),
              frame("c", "2026-03-15", 1.445), frame("d", "2026-03-22", 1.200),
              frame("e", "2026-08-18", 1.511)]
    g = group_frames(frames, VISITS)
    best = g.groups[0]
    assert best.id == g.default_group
    assert best.n_epochs == 3 and best.usable_for_motion          # 3 passages
    assert {f.frame_id for f in best.frames} == {"b", "c", "e"}   # 1,445 / 1,496 / 1,511 µm
    assert best.max_delta_rel <= 0.03
    assert [f.visit for f in best.frames] == [0, 1, 2]            # ordre chronologique
    # 1,101 et 1,200 µm diffèrent de 9 % (> 2 x 3 %) : jamais mélangées -> restent seules
    assert set(g.ungrouped) == {"a", "d"} and g.n_groups == 1


def test_never_mixes_detectors_or_far_wavelengths():
    frames = [frame("a", "2025-08-20", 1.50, "D2"), frame("b", "2026-03-15", 1.50, "D3"),
              frame("c", "2026-08-20", 1.70, "D2")]
    g = group_frames(frames, VISITS)
    assert g.n_groups == 0 and set(g.ungrouped) == {"a", "b", "c"}


def test_one_frame_per_visit_prefers_quality_then_wavelength():
    frames = [frame("a1", "2025-08-20", 1.50, status="faible"),
              frame("a2", "2025-08-21", 1.52, status="nette"),
              frame("b", "2026-03-15", 1.50), frame("c", "2026-08-20", 1.49)]
    g = group_frames(frames, VISITS)
    ids = [f.frame_id for f in g.groups[0].frames]
    assert "a2" in ids and "a1" not in ids and g.groups[0].n_candidates == 4


def test_rejected_frames_are_ignored():
    frames = [frame("a", "2025-08-20", 1.5), frame("b", "2026-03-15", 1.5, keep=False),
              frame("c", "2026-08-20", 1.5)]
    g = group_frames(frames, VISITS)
    assert g.groups[0].n_epochs == 2 and not g.groups[0].usable_for_motion


def test_tolerance_is_configurable():
    frames = [frame("a", "2025-08-20", 1.40), frame("b", "2026-03-15", 1.50),
              frame("c", "2026-08-20", 1.45)]
    assert group_frames(frames, VISITS, tolerance=0.03).groups[0].n_epochs == 2
    assert group_frames(frames, VISITS, tolerance=0.05).groups[0].n_epochs == 3
