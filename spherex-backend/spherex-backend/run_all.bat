@echo off
REM Lance le test complet du backend, depuis n importe quel dossier.
REM Usage : run_all.bat            (toutes les cibles)
REM         run_all.bat Barnard    (une seule cible)
cd /d "%~dp0backend"
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo [run_all] Creation de l environnement .venv...
  python -m venv .venv
)
"%PY%" -c "import astropy.wcs, astroquery, matplotlib, fastapi" 2>nul
if errorlevel 1 (
  echo [run_all] Installation des dependances dans .venv ^(1 a 3 minutes^)...
  "%PY%" -m pip install -r requirements.txt
)
"%PY%" -c "import astropy.wcs, astroquery, matplotlib, fastapi" 2>nul
if errorlevel 1 (
  echo [run_all] .venv inutilisable ^(bloque par Windows ?^) : utilisation du Python global.
  set PY=python
)
"%PY%" -m scripts.run_all %*
