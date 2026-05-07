@echo off
title NexusForge Launcher
echo ===================================================
echo             N E X U S F O R G E
echo ===================================================
echo.
echo Starting the NexusForge Application...

:: Start Backend in a new window
echo [1/2] Launching FastAPI Backend on Port 8000...
cd backend
start "NexusForge Backend" cmd /k ".venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"
cd ..

:: Start Frontend in a new window
echo [2/2] Launching React Frontend on Port 5173...
cd frontend
start "NexusForge Frontend" cmd /k "npm run dev"
cd ..

echo.
echo NexusForge components are booting up in separate windows!
echo.
echo You can access the UI at: http://localhost:5173
echo You can access the API at: http://127.0.0.1:8000
echo.
echo Press any key to close this launcher (the servers will remain running in their windows).
pause >nul
