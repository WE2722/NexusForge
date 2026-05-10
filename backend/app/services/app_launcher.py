"""App Launcher — extracts, installs, and launches generated projects."""
from __future__ import annotations

import os
import re
import subprocess
import signal
import sys
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

WORKSPACES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspaces"))


class AppLauncher:
    """Manages extracting generated project files to workspaces and launching them."""

    def __init__(self) -> None:
        self._running_processes: dict[str, dict[str, Any]] = {}
        os.makedirs(WORKSPACES_DIR, exist_ok=True)

    def extract_project(self, project) -> dict[str, Any]:
        """Extract all generated code blocks from a project into a workspace directory."""
        workspace_dir = os.path.join(WORKSPACES_DIR, project.id)
        os.makedirs(workspace_dir, exist_ok=True)

        files_added = 0
        for task in project.tasks:
            if not task.result or not task.result.code_blocks:
                continue
            for file_path, content in task.result.code_blocks.items():
                clean_path = self._sanitize_path(file_path)
                if not clean_path:
                    clean_path = f"unnamed_{task.id[:8]}_{files_added}.txt"

                # Prepend appropriate folder
                folder = "frontend" if task.agent_type.value == "frontend" else "backend"
                if not clean_path.startswith(f"{folder}/"):
                    clean_path = f"{folder}/{clean_path.lstrip('/')}"

                # Frontend path normalization
                if clean_path.startswith("frontend/") and not clean_path.startswith("frontend/public/"):
                    filename = os.path.basename(clean_path)
                    filename = re.sub(r'^main\.(tsx|ts|jsx|js)$', r'index.\1', filename)

                    # Scaffold files go to frontend root, NOT src/
                    if filename in ("package.json", "vite.config.ts", "tsconfig.json"):
                        clean_path = f"frontend/{filename}"
                    elif filename == "index.html":
                        clean_path = f"frontend/{filename}"
                    else:
                        clean_path = f"frontend/src/{filename}"

                    if filename.endswith((".tsx", ".ts", ".css", ".js", ".jsx")):
                        content = self._fix_frontend_imports(content)

                # Backend fixes
                if clean_path == "backend/logging.py":
                    clean_path = "backend/custom_logger.py"

                if clean_path.endswith(".py"):
                    content = self._fix_python_imports(content)

                if clean_path.endswith("requirements.txt"):
                    content = self._clean_requirements(content)

                full_path = os.path.join(workspace_dir, clean_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                files_added += 1

        # Write support files
        if files_added > 0:
            self._write_support_files(workspace_dir)

        return {
            "workspace": workspace_dir,
            "files_added": files_added,
        }

    def launch_project(self, project_id: str) -> dict[str, Any]:
        """Launch a previously extracted project."""
        workspace_dir = os.path.join(WORKSPACES_DIR, project_id)
        if not os.path.exists(workspace_dir):
            return {"success": False, "error": "Workspace not found. Extract the project first."}

        bat_path = os.path.join(workspace_dir, "run_app.bat")
        if not os.path.exists(bat_path):
            self._write_support_files(workspace_dir)

        try:
            proc = subprocess.Popen(
                ["cmd.exe", "/c", "start", "cmd", "/c", "run_app.bat"],
                cwd=workspace_dir,
            )
            self._running_processes[project_id] = {
                "pid": proc.pid,
                "workspace": workspace_dir,
            }
            logger.info("project_launched", project_id=project_id, workspace=workspace_dir)
            return {"success": True, "workspace": workspace_dir, "pid": proc.pid}
        except Exception as e:
            logger.error("launch_failed", project_id=project_id, error=str(e))
            return {"success": False, "error": str(e)}

    def stop_project(self, project_id: str) -> dict[str, Any]:
        """Stop a running project's processes."""
        info = self._running_processes.pop(project_id, None)
        stopped = []
        try:
            # Kill any uvicorn on port 8008 and npm on port 3000
            if sys.platform == "win32":
                for port in [8008, 3000]:
                    subprocess.run(
                        ["powershell", "-Command",
                         f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                         f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"],
                        capture_output=True, timeout=10
                    )
                    stopped.append(f"port:{port}")
            logger.info("project_stopped", project_id=project_id)
            return {"success": True, "stopped": stopped}
        except Exception as e:
            logger.error("stop_failed", project_id=project_id, error=str(e))
            return {"success": False, "error": str(e)}

    def get_status(self, project_id: str) -> dict[str, Any]:
        """Get the running status of a project."""
        info = self._running_processes.get(project_id)
        workspace = os.path.join(WORKSPACES_DIR, project_id)
        return {
            "project_id": project_id,
            "workspace_exists": os.path.exists(workspace),
            "running": info is not None,
            "pid": info["pid"] if info else None,
        }

    # ── Private Helpers ────────────────────────────────────────────

    @staticmethod
    def _sanitize_path(file_path: str) -> str:
        clean = re.sub(r"^#+\s*", "", file_path)
        clean = re.sub(r"^[\d\.\s]+", "", clean)
        clean = clean.replace("`", "").replace(":", "").replace("*", "").strip()
        if clean.lower().startswith("file"):
            clean = clean[4:].strip(" -")
        match = re.search(r"\(([^)]+)\)", clean)
        if match:
            clean = match.group(1).replace("`", "").strip()
        return clean

    @staticmethod
    def _fix_frontend_imports(content: str) -> str:
        content = re.sub(r'(from\s+[\'\"])(?:\./|\.\.\/)+.*\/([^\/]+)([\'\"])', r'\1./\2\3', content)
        content = re.sub(r'(import\s+[\'\"])(?:\./|\.\.\/)+.*\/([^\/]+)([\'\"])', r'\1./\2\3', content)
        content = re.sub(r"^([ \t]*)(interface\s+[A-Z][a-zA-Z0-9_]*\s*\{)", r"\1export \2", content, flags=re.MULTILINE)
        content = content.replace("export export ", "export ")
        return content

    @staticmethod
    def _fix_python_imports(content: str) -> str:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("from pydantic import") and "BaseSettings" in line:
                new_line = line.replace("BaseSettings, ", "").replace(", BaseSettings", "").replace("BaseSettings", "").strip()
                if new_line.endswith(","): new_line = new_line[:-1].strip()
                if new_line == "from pydantic import":
                    lines[i] = "from pydantic_settings import BaseSettings"
                else:
                    lines[i] = new_line + "\nfrom pydantic_settings import BaseSettings"
        content = '\n'.join(lines)
        content = content.replace("core.logging", "custom_logger")
        content = content.replace("app.core.logging", "custom_logger")
        content = content.replace("from app.", "from ")
        content = content.replace("import app.", "import ")
        return content

    @staticmethod
    def _clean_requirements(content: str) -> str:
        content = re.sub(r"==[^\s]+", "", content)
        content = re.sub(r'python\s+-m\s+app\.main\s*\n?', '', content)
        content = re.sub(r'python\s+main\.py\s*\n?', '', content)
        return content

    def _write_support_files(self, workspace_dir: str) -> None:
        """Write run scripts and support files to workspace."""
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
    echo [Backend] Ensuring core dependencies...
    pip install fastapi uvicorn pydantic pydantic-settings

    echo [Backend] Starting server on port 8008...
    set PYTHONPATH=%cd%
    IF EXIST "main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn main:app --reload --host 0.0.0.0 --port 8008"
    ) ELSE IF EXIST "app\\main.py" (
        start cmd /k "call venv\\Scripts\\activate.bat && set PYTHONPATH=%%cd%% && uvicorn app.main:app --reload --host 0.0.0.0 --port 8008"
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
"""
        sitecustomize = """import sys, os, importlib.util, importlib.machinery
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

        with open(os.path.join(workspace_dir, "run_app.bat"), "w", encoding="utf-8") as f:
            f.write(bat_script)

        backend_dir = os.path.join(workspace_dir, "backend")
        os.makedirs(backend_dir, exist_ok=True)
        with open(os.path.join(backend_dir, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write(sitecustomize)

        frontend_dir = os.path.join(workspace_dir, "frontend")
        if os.path.exists(frontend_dir):
            # Write Vite-compatible index.html to frontend root (if not already present)
            index_html = os.path.join(frontend_dir, "index.html")
            if not os.path.exists(index_html):
                with open(index_html, "w", encoding="utf-8") as f:
                    f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n<title>App</title>\n<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n</head>\n<body>\n<div id="root"></div>\n<script type="module" src="/src/main.tsx"></script>\n</body>\n</html>')
