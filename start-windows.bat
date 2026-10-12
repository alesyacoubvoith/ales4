@echo off
title Lancement Plateforme Helpdesk
echo ===============================================
echo   Demarrage de la plateforme IT Helpdesk...
echo   (NE FERME PAS les fenetres noires qui s'ouvrent)
echo ===============================================
echo.

REM --- Backend (FastAPI sur le port 8001) ---
start "BACKEND - Helpdesk" cmd /k "cd backend && pip install -r requirements.txt && uvicorn server:app --host 0.0.0.0 --port 8001"

REM --- Frontend (React sur le port 3000) ---
start "FRONTEND - Helpdesk" cmd /k "cd frontend && yarn install && yarn start --host 0.0.0.0"

echo.
echo Les 2 services demarrent dans des fenetres separees.
echo Attends ~1 minute puis ouvre ton navigateur sur :
echo.
echo     http://localhost:3000
echo.
pause
