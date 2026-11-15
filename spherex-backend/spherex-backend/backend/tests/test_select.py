"""Tests de l'étape Select, avec des calendriers d'observation réalistes."""
from app.core.search import ImageRecord, SearchResult
from app.core.select import select_images, split_into_visits
from app.core.target import TargetRequest, resolve_target

TARGET = resolve_target(TargetRequest(name="Barnard"))


def img(mjd, det="D2", full=True, i=0):
    return ImageRecord(obs_id=f"o{mjd:.2f}_{i}", release="dr1", detector=det,
                       t_start_mjd=mjd, t_end_mjd=mjd, t_mid_mjd=mjd, date_utc=None,
                       wl_min_um=1.1, wl_max_um=1.6, image_url="u", cutout_url="c",
                       fully_covered=full)


def result(images):
    return SearchResult(target=TARGET, source="test", cached_at=None, query_seconds=0,
                        n_images=len(images), n_days=0, first_date=None, last_date=None,
                        by_detector={}, by_release={}, by_survey={}, errors=[], images=images)


def barnard_like():
    """Calendrier réel observé pour Barnard : 3 passages de ~2 semaines + séries isolées."""
    imgs = []
    for start in (60902, 61110, 61268):            # août 2025, mars 2026, août 2026
        for d in range(15):                        # ~2 semaines
            for det in ("D1", "D2", "D3", "D4", "D5", "D6"):
                imgs.append(img(start + d + 0.1, det))
    imgs += [img(60950.5, "D2"), img(60950.6, "D3")]   # 2 images isolées (fin sept.)
    return imgs


def test_barnard_like_visits():
    sel = select_images(result(barnard_like()))
    assert sel.n_visits == 4
    assert sel.n_major_visits == 3 and sel.usable_for_motion
    assert [v.minor for v in sel.visits] == [False, True, False, False]
    # 8 images max par (passage, détecteur) : 3 passages x 6 détecteurs x 8 + 2 isolées
    assert sel.n_selected == 3 * 6 * 8 + 2


def test_deep_field_is_cut_into_monthly_epochs():
    """Pôle écliptique : une image par jour pendant 400 jours, sans trou."""
    imgs = [img(60800 + d + 0.2) for d in range(400)]
    visits = split_into_visits(imgs)
    assert len(visits) == 14                       # ceil(400 / 30)
    assert all(v[-1].t_mid_mjd - v[0].t_mid_mjd < 30 for v in visits)


def test_global_cap_keeps_every_visit():
    imgs = [img(60800 + d + 0.2, det) for d in range(400) for det in ("D1", "D2", "D3")]
    sel = select_images(result(imgs), max_total=60)
    assert sel.n_selected <= 60 + sel.n_visits     # au moins 1 image par passage
    assert all(v.n_selected >= 1 for v in sel.visits)


def test_filters_and_rejection_reasons():
    imgs = [img(60900.1, "D1"), img(60900.2, "D2", full=False), img(60900.3, "D2")]
    sel = select_images(result(imgs), detector="D2")
    assert sel.n_kept == 1 and sel.n_rejected == 1
    assert sel.rejected_reasons == {"zone demandée partiellement hors de l'image": 1}


def test_selection_is_spread_in_time():
    imgs = [img(60900 + d * 0.5, "D2", i=d) for d in range(20)]   # 10 jours, 20 images
    sel = select_images(result(imgs), max_per_visit_detector=4)
    times = [i.t_mid_mjd for i in sel.selected]
    assert times[0] == 60900 and times[-1] == 60909.5            # début et fin gardés
