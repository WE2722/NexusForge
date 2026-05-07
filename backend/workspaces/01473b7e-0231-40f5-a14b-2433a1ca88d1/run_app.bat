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
    echo [Backend] Ensuring core dependencies are installed...
    pip install fastapi uvicorn pydantic pydantic-settings loguru
    
    echo [Backend] Starting server...
    set PYTHONPATH=%cd%
    IF EXIST "app\main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "app.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE (
        echo [Backend] WARNING: Entry point main.py or app.py not found!
        start cmd /k "echo WARNING: Backend entry point not found. Check the generated files."
    )
    cd ..
)

IF EXIST "frontend" (
    echo [Frontend] Installing dependencies...
    cd frontend
    
    IF NOT EXIST "package.json" (
        echo [Frontend] WARNING: package.json missing! Creating fallback...
        echo {"name":"app","version":"1.0.0","scripts":{"dev":"vite","start":"react-scripts start"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0","react-scripts":"^5.0.1"},"devDependencies":{"vite":"^4.4.5"}} > package.json
    )
    
    call npm install --legacy-peer-deps
    echo [Frontend] Starting server...
    start cmd /k "npm run dev || npm start"
    cd ..
)
