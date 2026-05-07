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
    ) ELSE (
        echo [Backend] WARNING: requirements.txt not found. Using fallback...
        pip install fastapi uvicorn pydantic
    )
    
    echo [Backend] Generating flat import resolver...
    echo import sys, os, importlib.util, importlib.machinery > sitecustomize.py
    echo class FlatImporter: >> sitecustomize.py
    echo     def find_spec(self, fullname, path, target=None): >> sitecustomize.py
    echo         parts = fullname.split('.') >> sitecustomize.py
    echo         if parts[0] in ['app', 'api', 'src', 'core', 'models', 'routers', 'endpoints', 'services']: >> sitecustomize.py
    echo             name = parts[-1] >> sitecustomize.py
    echo             if os.path.exists(name + '.py'): >> sitecustomize.py
    echo                 return importlib.util.spec_from_file_location(fullname, os.path.abspath(name + '.py')) >> sitecustomize.py
    echo             class DummyLoader: >> sitecustomize.py
    echo                 def create_module(self, spec): return None >> sitecustomize.py
    echo                 def exec_module(self, module): pass >> sitecustomize.py
    echo             return importlib.machinery.ModuleSpec(fullname, DummyLoader(), is_package=True) >> sitecustomize.py
    echo         return None >> sitecustomize.py
    echo sys.meta_path.append(FlatImporter()) >> sitecustomize.py

    echo [Backend] Starting server...
    set PYTHONPATH=%cd%
    IF EXIST "app\main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    ) ELSE IF EXIST "main.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    ) ELSE IF EXIST "app.py" (
        start cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app:app --reload --host 0.0.0.0 --port 8000"
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
