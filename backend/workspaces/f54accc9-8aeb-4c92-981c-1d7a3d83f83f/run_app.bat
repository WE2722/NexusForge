@echo off
echo Starting NexusForge Generated App...
echo.

IF EXIST "backend" (
    echo [Backend] Setting up Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip

    IF EXIST "requirements.txt" (
        pip install -r requirements.txt
    )
    echo [Backend] Ensuring core dependencies...
    pip install fastapi uvicorn pydantic pydantic-settings

    echo [Backend] Starting server on port 8008...
    set PYTHONPATH=%cd%
    IF EXIST "main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "app\main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE (
        echo [Backend] WARNING: Entry point not found!
    )
    cd ..
)

IF EXIST "frontend" (
    echo [Frontend] Installing dependencies...
    cd frontend

    IF NOT EXIST "package.json" (
        echo {"name":"app","version":"1.0.0","scripts":{"start":"react-scripts start"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0","react-scripts":"^5.0.1","react-router-dom":"^6.22.0","lucide-react":"^0.344.0","axios":"^1.6.7","tailwindcss":"^3.4.1"},"browserslist":{"production":[">0.2%%","not dead","not op_mini all"],"development":["last 1 chrome version","last 1 firefox version","last 1 safari version"]}} > package.json
    )

    call npm install --legacy-peer-deps
    echo [Frontend] Starting server...
    start cmd /k "npm start"
    cd ..
)

echo Done! The app is launching in new windows.
pause
