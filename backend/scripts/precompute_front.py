"""Précalcule /api/motion pour toutes les cibles du catalogue du frontend.

Le premier calcul d'une cible télécharge des centaines de découpes SPHEREx sur IRSA
(de quelques minutes à plus d'une demi-heure). Ce script fait ces calculs à l'avance,
une cible après l'autre, en appelant le serveur déjà lancé : ensuite, chaque clic dans
le frontend répond instantanément depuis le cache.

Il envoie exactement la même requête que frontend/observationsApi.js :
  - étoiles connues du backend (mouvement propre corrigé) -> ?name=...
  - autres cibles -> ?ra=...&dec=... (coordonnées lues dans frontend/main.js)
  - taille 6' (DEMO_SIZE_ARCMIN de l'adaptateur), tous détecteurs

Usage (serveur lancé dans un autre terminal) :
    python scripts/precompute_front.py
    python scripts/precompute_front.py --only barnards-star epsilon-indi-b
    python scripts/precompute_front.py --base http://localhost:8000
    python scripts/precompute_front.py --check-updates   # chercher TOUT DE SUITE de nouvelles
                                                         # images SPHEREx pour toutes les cibles

Mise à jour automatique : le serveur revérifie IRSA chaque semaine tout seul (voir
/api/updates/status). --check-updates force cette vérification maintenant.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SIZE_ARCMIN = 6  # doit rester égal à DEMO_SIZE_ARCMIN dans frontend/observationsApi.js

# mêmes règles que KNOWN_TARGETS dans frontend/observationsApi.js
KNOWN_TARGETS = [
    (re.compile(r"barnard", re.I), "barnard"),
    (re.compile(r"wise\s*j?0855", re.I), "wise 0855-0714"),
    (re.compile(r"eps(ilon)?\s*ind", re.I), "eps indi b"),
]

MAIN_JS = Path(__file__).resolve().parents[2] / "frontend" / "main.js"


def front_targets() -> list[dict]:
    """Lit les cibles (id, name, ra, dec) du catalogue DWARF_TARGETS de main.js."""
    src = MAIN_JS.read_text(encoding="utf-8")
    out = []
    pat = re.compile(r'id:\s*"([^"]+)",\s*galaxyId:\s*"[^"]*",\s*name:\s*"([^"]+)"(.*?)\n\s{4}\},', re.S)
    for m in pat.finditer(src):
        ra = re.search(r'\bra:\s*"([^"]+)"', m.group(3))
        dec = re.search(r'\bdec:\s*"([^"]+)"', m.group(3))
        if ra and dec:
            out.append(dict(id=m.group(1), name=m.group(2), ra=ra.group(1), dec=dec.group(1)))
    return out


def query_for(t: dict) -> dict:
    for pattern, backend_name in KNOWN_TARGETS:
        if pattern.search(t["name"]):
            return {"name": backend_name, "size_arcmin": SIZE_ARCMIN}
    return {"ra": t["ra"], "dec": t["dec"], "size_arcmin": SIZE_ARCMIN}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--only", nargs="*", help="ids de cibles (ex. barnards-star)")
    ap.add_argument("--timeout", type=float, default=3 * 3600, help="secondes par cible")
    ap.add_argument("--check-updates", action="store_true",
                    help="vérifier maintenant s'il y a de nouvelles images SPHEREx (toutes cibles)")
    args = ap.parse_args()

    if args.check_updates:
        return check_updates(args.base)

    targets = front_targets()
    if args.only:
        targets = [t for t in targets if t["id"] in args.only]
    if not targets:
        print(f"Aucune cible trouvée dans {MAIN_JS}")
        return 1

    try:
        urllib.request.urlopen(f"{args.base}/api/health", timeout=10).read()
    except Exception as exc:  # noqa: BLE001
        print(f"Serveur injoignable sur {args.base} ({exc}). Lancez d'abord uvicorn.")
        return 1

    print(f"{len(targets)} cibles à précalculer (taille {SIZE_ARCMIN}')\n")
    report = []
    for k, t in enumerate(targets, 1):
        q = query_for(t)
        url = f"{args.base}/api/motion?{urllib.parse.urlencode(q)}"
        print(f"[{k}/{len(targets)}] {t['name']}  ->  {url}", flush=True)
        t0 = time.time()
        try:
            with urllib.request.urlopen(url, timeout=args.timeout) as r:
                data = json.loads(r.read())
            seq = (data.get("display") or {}).get("sequences") or [{}]
            video = seq[0].get("video") or {}
            n = len(video.get("timeline") or [])
            status = (data.get("motion") or {}).get("status")
            msg = f"OK  {n} images, vidéo {'oui' if video.get('mp4') else 'NON'}, mouvement : {status}"
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            msg = f"ERREUR HTTP {exc.code} : {detail}"
        except Exception as exc:  # noqa: BLE001
            msg = f"ERREUR : {type(exc).__name__}: {exc}"
        dt = time.time() - t0
        line = f"    {msg}  ({dt / 60:.1f} min)"
        print(line, flush=True)
        report.append(f"{t['id']:<20} {line.strip()}")

    print("\nRésumé :")
    print("\n".join(report))
    return 0


def check_updates(base: str) -> int:
    """Lance la vérification IRSA de toutes les cibles et suit son avancement."""
    try:
        req = urllib.request.Request(f"{base}/api/updates/run?force=true", method="POST")
        urllib.request.urlopen(req, timeout=30).read()
    except Exception as exc:  # noqa: BLE001
        print(f"Serveur injoignable sur {base} ({exc}). Lancez d'abord uvicorn.")
        return 1
    print("Vérification des nouvelles images SPHEREx lancée (une cible après l'autre)…")
    seen = set()
    time.sleep(2)
    while True:
        st = json.loads(urllib.request.urlopen(f"{base}/api/updates/status", timeout=60).read())
        for r in st["results"]:
            out = r.get("last_outcome")
            if out and (r["key"], out["at"]) not in seen:
                seen.add((r["key"], out["at"]))
                extra = f" (+{out['new_images']} images)" if out.get("new_images") else ""
                print(f"  {r['target']:<28} {out['outcome']}{extra}")
        if not st["running"] and not st["updating"]:
            break
        time.sleep(5)
    if st.get("new_collections"):
        print("\nNouvelle(s) collection(s) SPHEREx sur IRSA : " + ", ".join(st["new_collections"]))
        print("  -> à ajouter dans COLLECTIONS (backend/app/core/config.py) après vérification.")
    print("Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
