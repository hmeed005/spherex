"""Tests de l'étape Measure (ajustement global, ponts entre groupes, aberrants)."""
import numpy as np

from app.core.measure import PositionMeasure, bridge_components, fit_motion

RNG = np.random.default_rng(42)
T0 = 60900.0


def pm(fid, day, visit, group, x, y, sigma=0.1):
    return PositionMeasure(frame_id=fid, date_utc="2025-01-01T00:00:00Z", mjd=T0 + day,
                           visit=visit, group_id=group, detector="D2", wavelength_um=1.5,
                           x_px=x, y_px=y, sigma_px=sigma)


def track(mu_x, mu_y, days, visits, group, offset=(0, 0), noise=0.05, start=0):
    out = []
    for i, (d, v) in enumerate(zip(days, visits)):
        t = d / 365.25
        out.append(pm(f"{group}{start + i}", d, v, group,
                      29 + mu_x * t + offset[0] + RNG.normal(0, noise),
                      29 + mu_y * t + offset[1] + RNG.normal(0, noise)))
    return out


def test_known_motion_is_recovered():
    m = track(0.0, 1.7, [0, 1, 2, 200, 201, 365, 366], [0, 0, 0, 1, 1, 2, 2], "G1")
    r = fit_motion(m)
    assert r.status == "moving"
    assert abs(r.mu_y_px_yr - 1.7) < 0.15 and abs(r.mu_x_px_yr) < 0.15
    assert abs(r.mu_dec_arcsec_yr - 1.7 * 6.15) < 1.0
    assert abs(r.position_angle_deg - 0) < 10 or abs(r.position_angle_deg - 360) < 10


def test_chain_two_groups_t1_t2_t3_with_offset():
    """G1 couvre t1->t2, G2 couvre t2->t3 et est décalé de 0,5 px : la trajectoire complète
    est retrouvée et le décalage est mesuré grâce au passage commun t2."""
    g1 = track(0.0, 1.7, [0, 1, 180, 181], [0, 0, 1, 1], "G1")
    g2 = track(0.0, 1.7, [182, 183, 365, 366], [1, 1, 2, 2], "G2", offset=(0.0, 0.5), start=10)
    r = fit_motion(g1 + g2)
    assert r.components == [["G1", "G2"]]
    assert r.n_distinct_epochs == 3 and r.status == "moving"
    assert abs(r.mu_y_px_yr - 1.7) < 0.2
    d = {g.group_id: g for g in r.groups}
    off = d["G2"].offset_px if d["G2"].offset_estimated else tuple(-v for v in d["G1"].offset_px)
    assert abs(off[1] - 0.5) < 0.15


def test_without_offsets_the_shift_would_bias_motion():
    g1 = track(0.0, 1.7, [0, 1, 180, 181], [0, 0, 1, 1], "G1", noise=0.01)
    g2 = track(0.0, 1.7, [182, 183, 365, 366], [1, 1, 2, 2], "G2", offset=(0, 0.8), noise=0.01, start=10)
    good, naive = fit_motion(g1 + g2), fit_motion(g1 + g2, with_offsets=False)
    assert abs(good.mu_y_px_yr - 1.7) < abs(naive.mu_y_px_yr - 1.7)


def test_outlier_rejected_but_kept_in_output():
    m = track(0.0, 1.7, [0, 1, 2, 200, 201, 202, 365, 366, 367], [0, 0, 0, 1, 1, 1, 2, 2, 2], "G1")
    m[4].x_px += 3.0                               # une seule image aberrante
    r = fit_motion(m)
    bad = [x for x in r.measures if not x.used]
    assert len(bad) == 1 and bad[0].frame_id == m[4].frame_id and bad[0].rejected_reason
    assert len(r.measures) == len(m)               # rien n'est supprimé de la sortie
    assert abs(r.mu_y_px_yr - 1.7) < 0.2


def test_static_star_is_not_moving():
    r = fit_motion(track(0.0, 0.0, [0, 1, 200, 201, 365, 366], [0, 0, 1, 1, 2, 2], "G1"))
    assert r.status == "not_moving"


def test_two_epochs_is_insufficient():
    r = fit_motion(track(0.0, 1.7, [0, 1, 365, 366], [0, 0, 1, 1], "G1"))
    assert r.status == "insufficient_data"


def test_curved_track_flagged_non_linear():
    days = [0, 1, 100, 101, 200, 201, 300, 301, 365, 366]
    visits = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    m = [pm(f"c{i}", d, v, "G1", 29 + 3 * np.sin(d / 365.25 * 2 * np.pi), 29.0, 0.05)
         for i, (d, v) in enumerate(zip(days, visits))]
    r = fit_motion(m)
    assert r.status == "non_lineaire"


def test_groups_without_common_visit_are_not_bridged():
    g1 = track(0, 1.7, [0, 1], [0, 0], "G1")
    g2 = track(0, 1.7, [365, 366], [2, 2], "G2", start=5)
    assert bridge_components(g1 + g2) == [["G1"], ["G2"]]


# ---------------- règle d'affichage : concordance -> 1 animation ; décalage -> groupes séparés
from app.core.measure import compare_groups, plan_display
from app.core.screen import FrameQuality


def fq(ms, status="saturee", snr=None):
    return {m.frame_id: FrameQuality(frame_id=m.frame_id, obs_id=m.frame_id, status=status, keep=True,
                                     reason="", snr=snr if snr is not None else 100 + i)
            for i, m in enumerate(ms)}


def two_groups(offset):
    g1 = track(0.0, 1.7, [0, 180], [0, 1], "G1", noise=0.01)
    g2 = track(0.0, 1.7, [181, 365], [1, 2], "G2", offset=offset, noise=0.01, start=10)
    return g1 + g2


def test_agreeing_groups_one_video_most_visible_image():
    ms = two_groups((0, 0))
    frames = fq(ms)
    frames["G210"].snr = 999                     # image G2 au passage commun : la plus visible
    plan = plan_display(ms, frames)
    assert plan.conflicted_groups == [] and len(plan.sequences) == 1
    seq = plan.sequences[0]
    assert seq.kind == "unique" and len(seq.frame_ids) == 3          # t1, t2, t3
    assert seq.frame_ids[1] == "G210"                                 # la plus visible à t2
    assert "concordantes" in seq.notes["G210"]


def test_offset_groups_one_video_in_consecutive_blocks_no_interleaving():
    ms = two_groups((0, 1.5))                    # G2 décalé de 1,5 px >> seuil
    plan = plan_display(ms, fq(ms))
    assert set(plan.conflicted_groups) == {"G1", "G2"}
    assert len(plan.sequences) == 1                                   # TOUJOURS une seule vidéo
    seq = plan.sequences[0]
    # bloc G1 en entier (t1, t2), PUIS bloc G2 en entier (t2, t3) : jamais d'alternance
    assert seq.frame_ids == ["G10", "G11", "G210", "G211"]
    assert [seq.segments[f][1] for f in seq.frame_ids] == ["groupe G1", "groupe G1",
                                                           "groupe G2", "groupe G2"]
    assert seq.notes["G210"].startswith("⚠ nouveau bloc : groupe G2")
    assert len(plan.side_by_side) == 1


def test_small_difference_within_tolerance_is_agreement():
    ms = two_groups((0, 0.3))                    # 0,3 px < 3 x sqrt(0,15² + 0,15²) ≈ 0,64 px
    c = compare_groups(ms, fq(ms))
    assert len(c) == 1 and c[0].agree


def test_groups_without_common_instant_chained_with_warning():
    g1 = track(0, 1.7, [0, 1], [0, 0], "G1")
    g2 = track(0, 1.7, [365, 366], [2, 2], "G2", start=5)
    plan = plan_display(g1 + g2, fq(g1 + g2))
    assert len(plan.sequences) == 1 and plan.comparisons == []
    assert any("non vérifiable" in n for n in plan.sequences[0].notes.values())


def test_agreeing_groups_first_then_each_conflicted_group_entirely():
    g1 = track(0, 1.7, [0, 180], [0, 1], "G1", noise=0.01)
    g2 = track(0, 1.7, [181, 365], [1, 2], "G2", offset=(0, 1.5), noise=0.01, start=10)
    g3 = track(0, 1.7, [2, 3], [0, 0], "G3", noise=0.01, start=20)   # d'accord avec G1 seulement
    allm = g1 + g2 + g3
    plan = plan_display(allm, fq(allm))
    seq = plan.sequences[0]
    labels = [seq.segments[f][1] for f in seq.frame_ids]
    assert labels == ["groupes concordants", "groupe G1", "groupe G1", "groupe G2", "groupe G2"]
    mjd = {m.frame_id: m.mjd for m in allm}
    for lab in set(labels):                     # chaque bloc est chronologique
        ts = [mjd[f] for f in seq.frame_ids if seq.segments[f][1] == lab]
        assert ts == sorted(ts)


def test_calibration_cannot_hide_a_real_offset():
    """Régression : avec l'ancien calcul (χ² global), le décalage gonflait la tolérance et
    disparaissait. Le bruit doit être calibré DANS les groupes, pas entre eux."""
    from app.core.measure import calibrated_sigma_scale
    g1 = track(0.0, 1.7, [0, 1, 180, 181, 182], [0, 0, 1, 1, 1], "G1", noise=0.03)
    g2 = track(0.0, 1.7, [183, 184, 365, 366], [1, 1, 2, 2], "G2", offset=(0, 1.5), noise=0.03, start=10)
    r = fit_motion(g1 + g2, with_offsets=False)          # χ² global gonflé par le décalage
    scale = calibrated_sigma_scale(r)
    assert scale < 1.5
    plan = plan_display(r.measures, fq(r.measures), scale)
    assert set(plan.conflicted_groups) == {"G1", "G2"}


def test_calibrated_uncertainties_remove_false_disagreements():
    """Bruit réel 0,3 px (plus grand que l'incertitude théorique 0,15 px) : sans calibration,
    beaucoup de faux désaccords ; avec la calibration, presque aucun."""
    from app.core.measure import calibrated_sigma_scale
    ms = []
    for gi in range(6):
        ms += track(0, 1.7, [0 + gi * 0.1, 180 + gi * 0.1, 365 + gi * 0.1], [0, 1, 2], f"G{gi}",
                    noise=0.3, start=gi * 10)
    for m in ms:
        m.sigma_px = 0.15
    r = fit_motion(ms, with_offsets=False)
    raw = plan_display(r.measures, fq(r.measures))
    cal = plan_display(r.measures, fq(r.measures), calibrated_sigma_scale(r))
    bad_raw = sum(not c.agree for c in raw.comparisons)
    bad_cal = sum(not c.agree for c in cal.comparisons)
    assert bad_cal < bad_raw and bad_cal <= 0.15 * len(cal.comparisons)


def test_clean_crop_removes_empty_corners_of_rotated_cutout():
    """Découpe tournée de 30° dans une grille nord en haut : la vidéo propre ne garde
    que le carré centré entièrement couvert (pas de coins vides), jamais moins que n/√2."""
    import numpy as np
    from app.core.measure import clean_crop

    N = 300
    yy, xx = np.indices((N, N)) - (N - 1) / 2
    full = np.ones((N, N))
    assert clean_crop([full, full]) == 0                       # rien à rogner

    th = np.radians(30)
    u = xx * np.cos(th) + yy * np.sin(th)
    v = -xx * np.sin(th) + yy * np.cos(th)
    rot = np.where((np.abs(u) <= N / 2) & (np.abs(v) <= N / 2), 1.0, np.nan)
    c0 = clean_crop([full, rot])
    sub = rot[c0:N - c0, c0:N - c0]
    assert np.isfinite(sub).all()                              # plus de coins vides
    assert c0 <= round(N / 2 * (1 - 1 / np.sqrt(2)))           # au pire n/√2
    assert not np.isfinite(rot[c0 - 1:N - c0 + 1, c0 - 1:N - c0 + 1]).all()  # carré maximal
