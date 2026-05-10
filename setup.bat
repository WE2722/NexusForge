@echo off
title NexusForge - Setup
echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║       NexusForge First-Time Setup             ║
echo  ╚═══════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Node.js is not installed or not in PATH.
    echo  Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

:: Backend setup
echo  [1/3] Setting up Python backend...
cd backend
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
cd ..

:: Frontend setup
echo  [2/3] Installing frontend dependencies...
cd frontend
call npm install --legacy-peer-deps
cd ..

:: Create .env if needed
echo  [3/3] Checking configuration...
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo       Created backend\.env from .env.example
        echo       IMPORTANT: Edit backend\.env and add your API keys!
    )
)

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║       Setup Complete!                         ║
echo  ╚═══════════════════════════════════════════════╝
echo.
echo  Next steps:
echo    1. Edit backend\.env with your API keys
echo    2. Run Start-NexusForge.bat to launch
echo.
pause
