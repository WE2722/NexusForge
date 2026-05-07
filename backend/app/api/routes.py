"""API Routes for NexusForge."""
from __future__ import annotations

import asyncio
import json
import io
import re
import zipfile
import os
import subprocess
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import CreateProjectRequest, HealthResponse, Project, ProjectSummary
from app.services.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


@router.post("/projects", response_model=Project)
async def create_project(request: CreateProjectRequest, background_tasks: BackgroundTasks):
    """Create a new project from a prompt."""
    project = await orchestrator.create_project(request.prompt)
    return project


@router.get("/projects", response_model=list[ProjectSummary])
async def list_projects():
    """List all projects."""
    projects = await orchestrator.list_projects()
    return [
        ProjectSummary(
            id=p.id,
            title=p.brief.title if p.brief else "Unknown",
            status=p.status,
            task_count=len(p.tasks),
            completed_tasks=sum(1 for t in p.tasks if t.status == "completed"),
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/export")
async def export_project(project_id: str):
    """Export project files as a ZIP archive with executable launch scripts."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        files_added = 0
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                for file_path, content in task.result.code_blocks.items():
                    # Sanitize the file path extracted from markdown headers
                    clean_path = re.sub(r"^#+\s*", "", file_path)
                    clean_path = re.sub(r"^[\d\.\s]+", "", clean_path)
                    clean_path = clean_path.replace("`", "").replace(":", "").replace("*", "").strip()
                    if clean_path.lower().startswith("file"):
                        clean_path = clean_path[4:].strip(" -")
                    
                    # Handle cases like "Tailwind Config (tailwind.config.js)"
                    match = re.search(r"\(([^)]+)\)", clean_path)
                    if match:
                        clean_path = match.group(1).replace("`", "").strip()
                        
                    if not clean_path:
                        clean_path = f"unnamed_{task.id[:8]}_{files_added}.txt"
                        
                    # Prepend appropriate folder if not already there
                    folder = "frontend" if task.agent_type.value == "frontend" else "backend"
                    if not clean_path.startswith(f"{folder}/"):
                        clean_path = f"{folder}/{clean_path.lstrip('/')}"
                        
                    if "requirements.txt" in clean_path.lower():
                        # Remove strict version pinning to prevent native compilation issues
                        content = re.sub(r"==[^\s]+", "", content)

                    # Prevent Python standard library shadowing
                    if clean_path == "backend/logging.py":
                        clean_path = "backend/custom_logger.py"
                        
                    if clean_path.endswith(".py"):
                        # Fix imports if logging.py was renamed
                        content = content.replace("from logging import ", "from custom_logger import ")
                        content = content.replace("import logging\n", "import custom_logger\n")
                        # Fix AI syntax error: missing colon
                        if "if settings" in content and "if settings:" not in content:
                            content = content.replace("if settings\n", "if settings:\n")
                            content = content.replace("if settings \n", "if settings:\n")
                        # Fix flat directory import hallucination
                        content = content.replace("from app.", "from ")
                        content = content.replace("import app.", "import ")

                    if clean_path.endswith("package.json"):
                        # Remove hallucinated/broken npm packages
                        content = re.sub(r'"@types/tailwindcss":\s*"[^"]+",?', '', content)
                        content = re.sub(r'"@types/react":\s*"[^"]+",?', '"@types/react": "*",', content)
                        content = re.sub(r'"react-typescript-script":\s*"[^"]+",?', '', content)
                        content = re.sub(r'"react-scripts-ts":\s*"[^"]+",?', '', content)
                        # Fix AI hallucinated JavaScript comments inside JSON
                        content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)

                    if clean_path.endswith("requirements.txt"):
                        # Remove hallucinated invalid pip commands
                        content = re.sub(r'python\s+-m\s+app\.main\s*\n?', '', content)
                        content = re.sub(r'python\s+main\.py\s*\n?', '', content)

                    zip_file.writestr(clean_path, content)
                    files_added += 1
        
        # Inject executable run scripts
        bat_script = """@echo off
echo Starting NexusForge Generated App...
echo.

IF EXIST "backend" (
    echo [Backend] Setting up Python virtual environment...
    cd backend
    python -m venv venv
    call venv\\Scripts\\activate.bat
    python -m pip install --upgrade pip
    
    IF EXIST "requirements.txt" (
        pip install -r requirements.txt
    )
    echo [Backend] Ensuring core dependencies are installed...
    pip install fastapi uvicorn pydantic pydantic-settings loguru
    
    echo [Backend] Starting server...
    set PYTHONPATH=%cd%
    IF EXIST "app\\main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "app.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app:app --reload --host 0.0.0.0 --port 8008"
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
        echo {"name":"app","version":"1.0.0","scripts":{"dev":"vite","start":"react-scripts start"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0","react-scripts":"^5.0.1"},"devDependencies":{"vite":"^4.4.5"},"browserslist":{"production":[">0.2%%","not dead","not op_mini all"],"development":["last 1 chrome version","last 1 firefox version","last 1 safari version"]}} > package.json
    )
    
    call npm install --legacy-peer-deps
    echo [Frontend] Starting server...
    start cmd /k "npm run dev || npm start"
    cd ..
)

echo Done! The app is launching in new windows.
pause
"""
        sh_script = """#!/bin/bash
echo "Starting NexusForge Generated App..."

if [ -d "backend" ]; then
    echo "[Backend] Setting up Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "[Backend] WARNING: requirements.txt not found. Using fallback..."
        pip install fastapi uvicorn pydantic
    fi
    
    echo "[Backend] Starting server on port 8000..."
    export PYTHONPATH=$PWD
    if [ -f "app/main.py" ]; then
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    elif [ -f "main.py" ]; then
        uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    elif [ -f "app.py" ]; then
        uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
    else
        echo "[Backend] WARNING: Entry point not found! Check generated files."
    fi
    cd ..
fi

if [ -d "frontend" ]; then
    echo "[Frontend] Installing dependencies..."
    cd frontend
    
    if [ ! -f "package.json" ]; then
        echo "[Frontend] WARNING: package.json missing! Creating fallback..."
        echo '{"name":"app","version":"1.0.0","scripts":{"dev":"vite","start":"react-scripts start"},"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0","react-scripts":"^5.0.1"},"devDependencies":{"vite":"^4.4.5"},"browserslist":{"production":[">0.2%","not dead","not op_mini all"],"development":["last 1 chrome version","last 1 firefox version","last 1 safari version"]}}' > package.json
    fi
    
    npm install
    echo "[Frontend] Starting server..."
    if grep -q '"dev"[ \t]*:' package.json; then
        npm run dev &
    else
        npm start &
    fi
    cd ..
fi

echo "Done! The app is launching in the background."
wait
"""
        sitecustomize_content = """import sys, os, importlib.util, importlib.machinery
class FlatImporter:
    def find_spec(self, fullname, path, target=None):
        parts = fullname.split('.')
        if parts[0] in ['app', 'api', 'src', 'core', 'models', 'routers', 'endpoints', 'services', 'utils', 'db', 'schemas', 'controllers', 'config']:
            name = parts[-1]
            if os.path.exists(name + '.py'):
                return importlib.util.spec_from_file_location(fullname, os.path.abspath(name + '.py'))
            class DummyLoader:
                def create_module(self, spec): return None
                def exec_module(self, module): pass
            return importlib.machinery.ModuleSpec(fullname, DummyLoader(), is_package=True)
        return None
sys.meta_path.append(FlatImporter())"""

        if files_added > 0:
            if not any(n.endswith("public/index.html") for n in zip_file.namelist()) and any(n.startswith("frontend/") for n in zip_file.namelist()):
                zip_file.writestr("frontend/public/index.html", '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>App</title></head><body><noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div></body></html>')
            zip_file.writestr("run_app.bat", bat_script)
            zip_file.writestr("run_app.sh", sh_script)
            zip_file.writestr("backend/sitecustomize.py", sitecustomize_content)

    if files_added == 0:
        raise HTTPException(status_code=400, detail="No generated files found to export.")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f'attachment; filename="{project.brief.title.replace(" ", "_") if project.brief else "project"}.zip"'}
    )


@router.post("/projects/{project_id}/launch")
async def launch_project(project_id: str):
    """Extract project files to a local workspace and launch them."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspaces", project_id))
    
    files_added = 0
    for task in project.tasks:
        if task.result and task.result.code_blocks:
            for file_path, content in task.result.code_blocks.items():
                clean_path = re.sub(r"^#+\s*", "", file_path)
                clean_path = re.sub(r"^[\d\.\s]+", "", clean_path)
                clean_path = clean_path.replace("`", "").replace(":", "").replace("*", "").strip()
                if clean_path.lower().startswith("file"):
                    clean_path = clean_path[4:].strip(" -")
                
                match = re.search(r"\(([^)]+)\)", clean_path)
                if match:
                    clean_path = match.group(1).replace("`", "").strip()
                    
                if not clean_path:
                    clean_path = f"unnamed_{task.id[:8]}_{files_added}.txt"
                    
                folder = "frontend" if task.agent_type.value == "frontend" else "backend"
                if not clean_path.startswith(f"{folder}/"):
                    clean_path = f"{folder}/{clean_path.lstrip('/')}"
                    
                if "requirements.txt" in clean_path.lower():
                    content = re.sub(r"==[^\s]+", "", content)
                    content = re.sub(r'python\s+-m\s+app\.main\s*\n?', '', content)
                    content = re.sub(r'python\s+main\.py\s*\n?', '', content)

                if clean_path == "backend/logging.py":
                    clean_path = "backend/custom_logger.py"
                    
                if clean_path.startswith("frontend/") and not clean_path.startswith("frontend/src/") and not clean_path.startswith("frontend/public/"):
                    if clean_path.endswith((".tsx", ".ts", ".css", ".js", ".jsx")):
                        clean_path = clean_path.replace("frontend/", "frontend/src/", 1)

                if clean_path.endswith(".py"):
                    content = content.replace("core.logging", "custom_logger")
                    content = content.replace("app.core.logging", "custom_logger")
                    if "if settings" in content and "if settings:" not in content:
                        content = content.replace("if settings", "if settings:")
                    content = content.replace("from app.", "from ")
                    content = content.replace("import app.", "import ")

                if clean_path.endswith("package.json"):
                    content = re.sub(r'"@types/tailwindcss":\s*"[^"]+",?', '', content)
                    content = re.sub(r'"@types/react-router-dom":\s*"[^"]+",?', '', content)
                    content = re.sub(r'"@types/react":\s*"[^"]+",?', '"@types/react": "*",', content)
                    content = re.sub(r'"react-typescript-script":\s*"[^"]+",?', '', content)
                    content = re.sub(r'"react-scripts-ts":\s*"[^"]+",?', '', content)
                    content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
                    if '"browserslist"' not in content and '"dependencies"' in content:
                        content = content.replace('"dependencies"', '"browserslist": {"production": [">0.2%", "not dead", "not op_mini all"], "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]}, "dependencies"')

                full_path = os.path.join(workspace_dir, clean_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                files_added += 1

    if files_added == 0:
        raise HTTPException(status_code=400, detail="No generated files found to launch.")

    bat_script = """@echo off
echo Starting NexusForge Generated App...
echo.

IF EXIST "backend" (
    echo [Backend] Setting up Python virtual environment...
    cd backend
    python -m venv venv
    call venv\\Scripts\\activate.bat
    python -m pip install --upgrade pip
    
    IF EXIST "requirements.txt" (
        pip install -r requirements.txt
    )
    echo [Backend] Ensuring core dependencies are installed...
    pip install fastapi uvicorn pydantic pydantic-settings loguru
    
    echo [Backend] Starting server...
    set PYTHONPATH=%cd%
    IF EXIST "app\\main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "app.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app:app --reload --host 0.0.0.0 --port 8008"
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
"""
    bat_path = os.path.join(workspace_dir, "run_app.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_script)
        
    sitecustomize_content = """import sys, os, importlib.util, importlib.machinery
class FlatImporter:
    def find_spec(self, fullname, path, target=None):
        parts = fullname.split('.')
        if parts[0] in ['app', 'api', 'src', 'core', 'models', 'routers', 'endpoints', 'services', 'utils', 'db', 'schemas', 'controllers', 'config']:
            name = parts[-1]
            if os.path.exists(name + '.py'):
                return importlib.util.spec_from_file_location(fullname, os.path.abspath(name + '.py'))
            class DummyLoader:
                def create_module(self, spec): return None
                def exec_module(self, module): pass
            return importlib.machinery.ModuleSpec(fullname, DummyLoader(), is_package=True)
        return None
sys.meta_path.append(FlatImporter())"""
    
    backend_dir = os.path.join(workspace_dir, "backend")
    os.makedirs(backend_dir, exist_ok=True)
    with open(os.path.join(backend_dir, "sitecustomize.py"), "w", encoding="utf-8") as f:
        f.write(sitecustomize_content)
        
    frontend_dir = os.path.join(workspace_dir, "frontend")
    if os.path.exists(frontend_dir):
        public_dir = os.path.join(frontend_dir, "public")
        os.makedirs(public_dir, exist_ok=True)
        index_html_path = os.path.join(public_dir, "index.html")
        if not os.path.exists(index_html_path):
            with open(index_html_path, "w", encoding="utf-8") as f:
                f.write('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>App</title></head><body><noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div></body></html>')
        
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "cmd", "/c", "run_app.bat"], cwd=workspace_dir)
        return {"success": True, "message": "App launched", "workspace": workspace_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/stream")
async def stream_project_events(project_id: str):
    """Stream real-time project updates via SSE."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        last_status = None
        while True:
            current_status = project.status
            if current_status != last_status:
                data = json.dumps({"status": current_status.value})
                yield f"data: {data}\n\n"
                last_status = current_status
            
            if current_status in ["completed", "failed"]:
                data = json.dumps({"status": current_status.value, "final": True})
                yield f"data: {data}\n\n"
                break
                
            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/agents")
async def list_agents():
    """List available agents."""
    return orchestrator.get_agents()


@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: str):
    """Pause an executing project."""
    success = orchestrator.pause_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or already paused")
    return {"status": "paused"}


@router.post("/projects/{project_id}/resume")
async def resume_project(project_id: str):
    """Resume a paused project."""
    success = orchestrator.resume_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found or not paused")
    return {"status": "resumed"}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    return HealthResponse(
        status="healthy",
        services={
            "orchestrator": "ok",
        }
    )
