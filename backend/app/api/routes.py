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
from fastapi.responses import StreamingResponse, FileResponse

from app.models.schemas import CreateProjectRequest, HealthResponse, Project, ProjectSummary
from app.services.orchestrator import Orchestrator
from app.services.app_launcher import AppLauncher
from app.services.compiler import Compiler
from app.services.fix_loop import FixLoop
from app.services.delivery import Delivery

router = APIRouter()
orchestrator = Orchestrator()
launcher = AppLauncher()
compiler = Compiler()
fix_loop = FixLoop(orchestrator)
delivery = Delivery(orchestrator)

# In-memory stores for async operation results
_compile_results: dict[str, dict] = {}
_fix_results: dict[str, dict] = {}


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

    # Use app_launcher to extract files
    result = launcher.extract_project(project)
    if result["files_added"] == 0:
        raise HTTPException(status_code=400, detail="No generated files found to export.")

    # Build ZIP from workspace
    workspace_dir = result["workspace"]
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, workspace_dir)
                zip_file.writestr(rel_path, open(abs_path, "r", encoding="utf-8", errors="replace").read())

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

    # Extract files
    extract_result = launcher.extract_project(project)
    if extract_result["files_added"] == 0:
        raise HTTPException(status_code=400, detail="No generated files found to launch.")

    # Launch
    launch_result = launcher.launch_project(project_id)
    if not launch_result["success"]:
        raise HTTPException(status_code=500, detail=launch_result.get("error", "Launch failed"))

    return {"success": True, "message": "App launched", "workspace": launch_result["workspace"]}


@router.post("/projects/{project_id}/stop")
async def stop_project_launch(project_id: str):
    """Stop a running launched project."""
    result = launcher.stop_project(project_id)
    return result


@router.get("/projects/{project_id}/launch-status")
async def get_launch_status(project_id: str):
    """Get the running status of a launched project."""
    return launcher.get_status(project_id)


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


@router.get("/budget")
async def get_budget():
    """Get token budget report across all providers."""
    return orchestrator.budget.get_budget_report()


@router.get("/providers/status")
async def get_provider_status():
    """Get status of all LLM providers."""
    return orchestrator.router.get_status()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check."""
    return HealthResponse(
        status="healthy",
        services={
            "orchestrator": "ok",
            "launcher": "ok",
            "compiler": "ok",
        }
    )


# ── Compile Endpoints ──────────────────────────────────────────────

@router.post("/projects/{project_id}/compile")
async def compile_project(project_id: str, background_tasks: BackgroundTasks):
    """Start compiling a project. Returns a compile_id to poll for results."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Collect project files
    project_files: dict[str, str] = {}
    for task in project.tasks:
        if task.result and task.result.code_blocks:
            project_files.update(task.result.code_blocks)

    if not project_files:
        raise HTTPException(status_code=400, detail="No files to compile")

    import uuid
    compile_id = str(uuid.uuid4())
    _compile_results[compile_id] = {"status": "running", "result": None}

    async def run_compile():
        result = await compiler.compile_project(project_id, project_files)
        _compile_results[compile_id] = {"status": "completed", "result": result.model_dump(mode="json")}

    background_tasks.add_task(run_compile)

    return {"compile_id": compile_id, "status": "running"}


@router.get("/projects/{project_id}/compile/{compile_id}")
async def get_compile_result(project_id: str, compile_id: str):
    """Poll for compilation result."""
    entry = _compile_results.get(compile_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Compile job not found")
    return entry


# ── Fix Loop Endpoints ─────────────────────────────────────────────

@router.post("/projects/{project_id}/fix")
async def fix_project(project_id: str, background_tasks: BackgroundTasks):
    """Start the auto-fix loop. Returns a fix_id to poll for results."""
    project = await orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    import uuid
    fix_id = str(uuid.uuid4())
    _fix_results[fix_id] = {"status": "running", "result": None}

    async def run_fix():
        result = await fix_loop.fix_project(project_id, max_iterations=5)
        _fix_results[fix_id] = {"status": "completed", "result": result.model_dump(mode="json")}

    background_tasks.add_task(run_fix)

    return {"fix_id": fix_id, "status": "running"}


@router.get("/projects/{project_id}/fix/{fix_id}")
async def get_fix_result(project_id: str, fix_id: str):
    """Poll for fix loop result."""
    entry = _fix_results.get(fix_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Fix job not found")
    return entry


# ── Delivery Endpoints ─────────────────────────────────────────────

@router.post("/projects/{project_id}/deliver")
async def deliver_project(project_id: str):
    """Create a deliverable package (ZIP) for a project."""
    result = await delivery.deliver_project(project_id)
    if result.status == "failed":
        raise HTTPException(status_code=500, detail="Delivery failed")
    return result.model_dump(mode="json")


@router.get("/projects/{project_id}/download")
async def download_project(project_id: str):
    """Download the project as a ZIP file."""
    zip_path = delivery.get_zip_path(project_id)
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="No delivery package found. Run /deliver first.")

    filename = os.path.basename(zip_path)
    return FileResponse(
        path=zip_path,
        media_type="application/x-zip-compressed",
        filename=filename,
    )


# ── Preview Endpoints ──────────────────────────────────────────────

@router.post("/projects/{project_id}/preview")
async def preview_project(project_id: str):
    """Start a live preview of the project."""
    result = await delivery.preview_project(project_id)
    if result.status == "failed":
        raise HTTPException(status_code=500, detail="Preview failed to start")
    return result.model_dump(mode="json")


@router.delete("/projects/{project_id}/preview/{preview_id}")
async def stop_preview(project_id: str, preview_id: str):
    """Stop a running preview."""
    stopped = await delivery.stop_preview(preview_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="Preview not found or already stopped")
    return {"status": "stopped"}


@router.get("/projects/{project_id}/preview/{preview_id}/status")
async def get_preview_status(project_id: str, preview_id: str):
    """Check preview status."""
    return delivery.get_preview_status(preview_id)



