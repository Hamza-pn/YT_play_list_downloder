@echo off
title YouTube Playlist Downloader - Launcher
cd /d "%~dp0"

echo ============================================
echo   YouTube Playlist Downloader - starting
echo ============================================
echo.

if not exist "backend\.venv\Scripts\python.exe" goto no_venv
if not exist "frontend\node_modules" goto no_modules

echo [1/3] Starting backend  on http://localhost:8000 ...
cd /d "%~dp0backend"
start "Backend - uvicorn :8000" cmd /k .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

echo [2/3] Starting frontend on http://localhost:3000 ...
cd /d "%~dp0frontend"
start "Frontend - next dev :3000" cmd /k npm run dev

cd /d "%~dp0"
echo [3/3] Waiting for the servers to come up ...
timeout /t 15 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo Running in two separate windows:
echo    Frontend - http://localhost:3000
echo    Backend  - http://localhost:8000   (API docs at /api/docs)
echo.
echo Close those two windows to stop the project.
timeout /t 10 >nul
exit /b 0

:no_venv
echo ERROR: backend virtualenv not found at backend\.venv
echo.
echo Create it first:
echo     cd backend
echo     python -m venv .venv
echo     .venv\Scripts\python -m pip install -r requirements.txt
echo.
pause
exit /b 1

:no_modules
echo ERROR: frontend dependencies are not installed.
echo.
echo Run this first:
echo     cd frontend
echo     npm install
echo.
pause
exit /b 1
