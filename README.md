# SPHEREx Time-Lapse — Backend (NASA Space Apps 2026, « Planet X and SPHEREx »)

API Python (FastAPI) qui montre comment le ciel change dans les images du télescope SPHEREx :
elle trouve les images d'une cible sur IRSA, les filtre, les groupe par longueur d'onde, les
aligne sur une même vue du ciel, mesure le mouvement de l'objet et produit **une vidéo MP4**
avec une **frise temporelle** pour synchroniser les détails affichés sous la vidéo.

## Installation (Windows)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer le serveur

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Documentation interactive : http://localhost:8000/docs
- Page de démonstration (vidéo + case synchronisée) : http://localhost:8000/player?name=Barnard
- Diagnostic (Python utilisé, encodeur MP4) : http://localhost:8000/api/health

## L'appel principal pour le frontend

```
GET /api/motion?name=Barnard          (ou ?ra=269.446&dec=4.768)
```

Réponse (résumé) :

| Champ | Contenu |
|---|---|
| `motion` | vitesse (″/an) ± incertitude, direction, statut (`moving`, `not_moving`, `insufficient_data`, `non_lineaire`) |
| `motion_without_offsets` | le même résultat sans correction des décalages de groupe |
| `display.sequences[0].video.mp4` | **la vidéo** (uniquement l'image du ciel) |
| `display.sequences[0].video.mp4_markers` | la même vidéo avec repères (positions, trajectoire) |
| `display.sequences[0].video.timeline` | une entrée par image : `t_start_s`, `t_end_s`, `seek_s`, date, λ, détecteur, groupe, qualité, positions, `note`, `group_changed`… |
| `display.conflicted_groups`, `side_by_side_urls` | désaccords entre groupes et images côte à côte |
| `positions_plot_url` | graphique des positions mesurées brutes |

Synchronisation côté frontend :
- **vidéo → case** : image courante = dernière entrée de `timeline` avec `t_start_s <= video.currentTime` ;
- **case → vidéo** : `video.currentTime = entry.seek_s`.

Les médias sont servis sous `/files/...` (URLs relatives : les préfixer par l'adresse de l'API).

Paramètres utiles : `refresh=true` (recalculer le résultat), `refresh_search=true` (réinterroger IRSA).

## Tests

```powershell
cd backend
pytest -q                 # tests unitaires
python -m scripts.run_all Barnard   # chaîne complète sur données réelles (ou ..\run_all.bat)
```

## Pipeline

`target` → `search` (IRSA SIA, DR1 + QR3) → `select` (passages) → `fetch` (cutouts) →
`screen` (qualité, visibilité) → `group` (λ à ±3 %) → `align` (grille céleste commune) →
`measure` (ajustement global, ponts entre groupes) → `video` (MP4 + frise).

Données : SPHEREx via IRSA (Caltech/IPAC). Code des tutoriels IRSA (BSD-3) utilisé comme référence.

## Frontend + backend ensemble (branche `integration`)

Le frontend est dans `frontend/` (`index.html`, `css.css`, `main.js`) et le backend le sert lui-même :

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Puis ouvrir **http://localhost:8000/** (redirige vers `/app/`). L'API reste sur `/api/...` et `/docs`.

Le lien se fait dans `frontend/observationsApi.js` : `main.js` appelle
`window.ObservationsApi.fetchObservations({ ra, dec, fov, band, target })`, l'adaptateur appelle
`GET /api/motion` et renvoie `{ frames: [...] }` (une image par date, dans l'ordre de la vidéo).
Barnard et WISE 0855 sont envoyés par leur **nom** (le backend corrige leur mouvement propre).
Le premier calcul d'une cible prend plusieurs minutes ; ensuite la réponse vient du cache.
