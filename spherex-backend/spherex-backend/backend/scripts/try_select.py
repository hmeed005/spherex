"""Test réel de l'étape Select (utilise le cache de l'étape Search) :
    python -m scripts.try_select Barnard
    python -m scripts.try_select nep D2
"""
import sys

from app.core.search import search_images
from app.core.select import select_images
from app.core.target import TargetRequest, resolve_target

name = sys.argv[1] if len(sys.argv) > 1 else "Barnard"
det = sys.argv[2] if len(sys.argv) > 2 else None
t = resolve_target(TargetRequest(name=name))
s = search_images(t)
sel = select_images(s, detector=det)
print(f"{t.label} ({s.source}) : {sel.n_found} trouvées -> {sel.n_kept} gardées -> "
      f"{sel.n_selected} à télécharger")
print(f"Passages : {sel.n_visits} (dont {sel.n_major_visits} principaux) ; "
      f"mouvement mesurable : {sel.usable_for_motion}")
for v in sel.visits:
    tag = " (mineur)" if v.minor else ""
    print(f"  #{v.index:<3} {v.start} -> {v.end} ({v.duration_days:>5} j) "
          f"{v.n_images:>5} images, {v.n_selected:>3} choisies{tag}")
if sel.rejected_reasons:
    print("Rejets :", sel.rejected_reasons)
