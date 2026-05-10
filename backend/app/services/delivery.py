"""
Delivery — packages completed projects for download with README, configs, and ZIP archive.

Capabilities:
  1. deliver_project: Run FixLoop → create final package → ZIP → return download URL
  2. preview_project: Start live servers in temp dir → return URLs → auto-stop after 1 hour
"""
from __future__ import annotations

import asyncio
import io
import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone

import structlog

from app.models.schemas import DeliveryResult, PreviewResult
from app.services.compiler import Compiler
from app.services.fix_loop import FixLoop

logger = structlog.get_logger(__name__)

DELIVERY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "deliveries"))


class Delivery:
    """Packages and delivers completed projects."""

    def __init__(self, orchestrator) -> None:
        self._orchestrator = orchestrator
        self._compiler = Compiler()
        self._fix_loop = FixLoop(orchestrator)
        self._active_previews: dict[str, dict] = {}
        os.makedirs(DELIVERY_DIR, exist_ok=True)

    async def deliver_project(self, project_id: str) -> DeliveryResult:
        """
        Full delivery pipeline:
        1. Run FixLoop for clean compilation
        2. Generate README and support files
        3. Create ZIP archive
        4. Return download info
        """
        result = DeliveryResult(status="running")

        project = await self._orchestrator.get_project(project_id)
        if not project:
            result.status = "failed"
            return result

        logger.info("delivery_start", project_id=project_id)

        # Step 1: Run fix loop (optional — try to get clean build)
        fix_result = await self._fix_loop.fix_project(project_id, max_iterations=3)

        # Step 2: Collect all project files
        project_files: dict[str, str] = {}
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                project_files.update(task.result.code_blocks)

        if not project_files:
            result.status = "failed"
            return result

        # Step 3: Generate support files
        readme = self._generate_readme(project)
        env_example = self._generate_env_example(project)
        project_files["README.md"] = readme
        project_files[".env.example"] = env_example

        # Step 4: Create ZIP
        zip_filename = f"{project.brief.title.replace(' ', '_')}_{project_id[:8]}.zip"
        zip_path = os.path.join(DELIVERY_DIR, zip_filename)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in project_files.items():
                zf.writestr(filename, content)

        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())

        size_bytes = os.path.getsize(zip_path)

        result.download_url = f"/api/projects/{project_id}/download"
        result.size_bytes = size_bytes
        result.zip_path = zip_path
        result.readme_generated = True
        result.status = "completed"

        logger.info("delivery_complete", project_id=project_id, size=size_bytes)
        return result

    async def preview_project(self, project_id: str) -> PreviewResult:
        """
        Start live preview servers for a project.
        Auto-stops after 1 hour.
        """
        result = PreviewResult(status="starting")

        project = await self._orchestrator.get_project(project_id)
        if not project:
            result.status = "failed"
            return result

        # Collect files
        project_files: dict[str, str] = {}
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                project_files.update(task.result.code_blocks)

        if not project_files:
            result.status = "failed"
            return result

        # Compile (which writes files to temp dir)
        compile_result = await self._compiler.compile_project(project_id, project_files)

        result.backend_url = compile_result.backend_url
        result.frontend_url = compile_result.frontend_url
        result.status = "running" if compile_result.success else "failed"

        # Track active preview
        self._active_previews[result.id] = {
            "project_id": project_id,
            "temp_dir": compile_result.temp_dir,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Schedule auto-stop after 1 hour
        asyncio.create_task(self._auto_stop_preview(result.id, 3600))

        return result

    async def stop_preview(self, preview_id: str) -> bool:
        """Stop a running preview."""
        info = self._active_previews.pop(preview_id, None)
        if not info:
            return False

        temp_dir = info.get("temp_dir", "")
        if temp_dir:
            self._compiler.cleanup(temp_dir)

        logger.info("preview_stopped", preview_id=preview_id)
        return True

    def get_preview_status(self, preview_id: str) -> dict:
        """Check if a preview is still running."""
        info = self._active_previews.get(preview_id)
        return {
            "running": info is not None,
            "preview_id": preview_id,
            "started_at": info.get("started_at") if info else None,
        }

    def get_zip_path(self, project_id: str) -> str | None:
        """Find the ZIP file for a project delivery."""
        for filename in os.listdir(DELIVERY_DIR):
            if project_id[:8] in filename and filename.endswith(".zip"):
                return os.path.join(DELIVERY_DIR, filename)
        return None

    # ── Private Helpers ────────────────────────────────────────────

    async def _auto_stop_preview(self, preview_id: str, timeout_seconds: int) -> None:
        """Auto-stop a preview after timeout."""
        await asyncio.sleep(timeout_seconds)
        if preview_id in self._active_previews:
            await self.stop_preview(preview_id)
            logger.info("preview_auto_stopped", preview_id=preview_id)

    def _generate_readme(self, project) -> str:
        """Generate a README.md for the project."""
        title = project.brief.title if project.brief else "NexusForge Project"
        description = project.brief.description if project.brief else ""
        tech_stack = project.brief.tech_stack if project.brief else []
        features = project.brief.features if project.brief else []

        readme = f"""# {title}

{description}

> Generated by [NexusForge](https://nexusforge.dev) — Multi-Agent AI Orchestration System

## Tech Stack

{chr(10).join(f'- {t}' for t in tech_stack) if tech_stack else '- Python + React'}

## Features

{chr(10).join(f'- {f}' for f in features) if features else '- Core application functionality'}

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8008
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## API Documentation

Once the backend is running, visit: `http://localhost:8008/docs`

## Project Structure

```
├── backend/          # Python/FastAPI backend
│   ├── main.py       # Application entry point
│   └── ...
├── frontend/         # React frontend
│   ├── src/
│   └── ...
├── .env.example      # Environment variables template
└── README.md         # This file
```

---

*Built with ❤️ by NexusForge AI*
"""
        return readme

    def _generate_env_example(self, project) -> str:
        """Generate a .env.example file."""
        return """# Application Configuration
# Copy this file to .env and fill in your values

# Backend
PORT=8008
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=mongodb://localhost:27017/myapp
# DATABASE_URL=postgresql://user:pass@localhost:5432/myapp

# Frontend
REACT_APP_API_URL=http://localhost:8008

# Authentication (if applicable)
# JWT_SECRET=your-jwt-secret
# JWT_ALGORITHM=HS256

# External Services (if applicable)
# REDIS_URL=redis://localhost:6379
"""
