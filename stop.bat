@echo off
title NexusForge - Stop
echo.
echo  Stopping NexusForge processes...
echo.

:: Kill Python/uvicorn on port 8000
echo  [1/2] Stopping backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo       Killed PID %%a
)

:: Kill Node/Vite on port 5173
echo  [2/2] Stopping frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo       Killed PID %%a
)

echo.
echo  ✓ All NexusForge processes stopped.
echo.
pause
