@echo off
title NexusForge Launcher
color 0A
echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║          N E X U S F O R G E                  ║
echo  ║       AI Development Platform                 ║
echo  ╚═══════════════════════════════════════════════╝
echo.

:: Start Backend
echo [1/2] Starting FastAPI Backend on port 8000...
cd backend
start "NexusForge Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"
cd ..

:: Wait for backend to be ready
echo      Waiting for backend to start...
timeout /t 3 /noq >nul

:: Start Frontend
echo [2/2] Starting React Frontend on port 5173...
cd frontend
start "NexusForge Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ✓ NexusForge is starting up!
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://127.0.0.1:8000
echo   API Docs:  http://127.0.0.1:8000/docs
echo.
echo Press any key to close this launcher (servers keep running).
pause >nul
