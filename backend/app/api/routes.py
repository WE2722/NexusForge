"""API Routes for NexusForge."""
from __future__ import annotations

import asyncio
import json
import io
import re
import zipfile
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
                    clean_path = clean_path.replace("`", "").strip()
                    
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
                        # Remove strict version pinning to prevent native compilation issues (e.g. rustup for pydantic-core)
                        content = re.sub(r"==[^\s]+", "", content)

                    zip_file.writestr(clean_path, content)
                    files_added += 1
        
        # Inject executable run scripts
        bat_script = """@echo off
echo Starting NexusForge Generated App...
echo.

IF EXIST "backend" (
    echo [Backend] Installing requirements...
    cd backend
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [Backend] Starting server...
    start cmd /k "uvicorn app.main:app --reload --port 8000"
    cd ..
)

IF EXIST "frontend" (
    echo [Frontend] Installing dependencies...
    cd frontend
    call npm install
    echo [Frontend] Starting server...
    findstr /C:"\"dev\":" package.json >nul
    if %errorlevel% equ 0 (
        start cmd /k "npm run dev"
    ) else (
        start cmd /k "npm start"
    )
    cd ..
)

echo Done! The app is launching in new windows.
pause
"""
        sh_script = """#!/bin/bash
echo "Starting NexusForge Generated App..."

if [ -d "backend" ]; then
    echo "[Backend] Installing requirements..."
    cd backend
    python3 -m pip install --upgrade pip
    pip3 install -r requirements.txt
    echo "[Backend] Starting server on port 8000..."
    uvicorn app.main:app --reload --port 8000 &
    cd ..
fi

if [ -d "frontend" ]; then
    echo "[Frontend] Installing dependencies..."
    cd frontend
    npm install
    echo "[Frontend] Starting server..."
    if grep -q '"dev":' package.json; then
        npm run dev &
    else
        npm start &
    fi
    cd ..
fi

echo "Done! The app is launching in the background."
wait
"""
        if files_added > 0:
            zip_file.writestr("run_app.bat", bat_script)
            zip_file.writestr("run_app.sh", sh_script)

    if files_added == 0:
        raise HTTPException(status_code=400, detail="No generated files found to export.")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f'attachment; filename="{project.brief.title.replace(" ", "_") if project.brief else "project"}.zip"'}
    )


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
