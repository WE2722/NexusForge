"""API Routes for NexusForge."""
from __future__ import annotations

import asyncio
import json
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
