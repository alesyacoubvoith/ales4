@echo off
title Support IT - Helpdesk & Stock
cd /d "%~dp0"
echo ============================================================
echo   Support IT - Plateforme Helpdesk ^& Stock (local)
echo ============================================================
echo.
echo [1/2] Installation (automatique, la 1ere fois seulement)...
py -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo.
  echo "py" introuvable, nouvelle tentative avec "python"...
  python -m pip install --disable-pip-version-check -q -r requirements.txt
  set PYCMD=python
) else (
  set PYCMD=py
)
echo.
echo [2/2] Demarrage du serveur...
echo.
echo   Ouvre ton navigateur sur :  http://localhost:8001
echo   Tes collegues (meme reseau) :  http://TON-IP:8001
echo.
echo   (Pour connaitre ton IP : ouvre cmd et tape  ipconfig )
echo   NE FERME PAS cette fenetre tant que tu utilises l'appli.
echo.
timeout /t 2 >nul
start "" http://localhost:8001
%PYCMD% -m uvicorn app:app --host 0.0.0.0 --port 8001
pause
