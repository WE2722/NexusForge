"""
Compiler — builds generated projects in isolated temp directories.

Steps:
  1. Create UUID-based temp directory
  2. Write all project files preserving structure
  3. Inject missing scaffold files (package.json, vite.config.ts, etc.)
  4. Backend: py_compile all .py files
  5. Frontend: npm install → npm run build
  6. Optionally start servers on dynamic ports
  7. Return CompileResult with success/errors/logs/URLs
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from typing import Any

import structlog

from app.models.schemas import CompileResult

logger = structlog.get_logger(__name__)


def _find_free_port(start: int = 3001, end: int = 9000) -> int:
    """Find an available port on localhost."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    raise RuntimeError("No free ports available")


# Default frontend scaffold (same as FrontendAgent uses)
_DEFAULT_PACKAGE_JSON = {
    "name": "app-frontend",
    "private": True,
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "preview": "vite preview",
        "start": "vite"
    },
    "dependencies": {
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "lucide-react": "^0.460.0",
        "axios": "^1.7.0"
    },
    "devDependencies": {
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "@vitejs/plugin-react": "^4.3.0",
        "typescript": "^5.6.0",
        "vite": "^6.0.0",
        "@tailwindcss/vite": "^4.0.0",
        "tailwindcss": "^4.0.0"
    }
}

_DEFAULT_VITE_CONFIG = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: {PORT},
    open: false
  }
})
"""

_DEFAULT_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false
  },
  "include": ["src"]
}
"""

_DEFAULT_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""


class Compiler:
    """Compiles generated projects in isolated environments."""

    def __init__(self) -> None:
        self._active_processes: dict[str, list[subprocess.Popen]] = {}

    async def compile_project(
        self, project_id: str, project_files: dict[str, str],
        start_servers: bool = False,
    ) -> CompileResult:
        """
        Compile a project's files in an isolated temp directory.

        Args:
            project_id: The project ID.
            project_files: Dict of {filename: content} from the project.
            start_servers: If True, start backend/frontend servers on dynamic ports.

        Returns:
            CompileResult with compilation status and errors.
        """
        result = CompileResult(status="running")

        # Step 1: Create isolated temp directory
        temp_dir = os.path.join(tempfile.gettempdir(), f"nexusforge_{project_id}_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)
        result.temp_dir = temp_dir

        logger.info("compile_start", project_id=project_id, temp_dir=temp_dir)

        try:
            # Step 2: Write project files to temp dir
            backend_files: dict[str, str] = {}
            frontend_files: dict[str, str] = {}

            for filename, content in project_files.items():
                # Classify files
                if filename.endswith((".py", ".txt")) or "backend" in filename.lower():
                    backend_files[filename] = content
                elif filename.endswith((".tsx", ".ts", ".jsx", ".js", ".css", ".html", ".json")) or "frontend" in filename.lower():
                    frontend_files[filename] = content
                else:
                    # Write to root
                    file_path = os.path.join(temp_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

            # Step 3: Backend compilation
            if backend_files:
                result.backend_compiled, result.backend_errors, result.backend_logs = (
                    await self._compile_backend(temp_dir, backend_files)
                )
            else:
                result.backend_compiled = True  # No backend to compile

            # Step 4: Frontend compilation
            if frontend_files:
                result.frontend_compiled, result.frontend_errors, result.frontend_logs = (
                    await self._compile_frontend(temp_dir, frontend_files)
                )
            else:
                result.frontend_compiled = True  # No frontend to compile

            # Step 5: Start servers if requested
            if start_servers:
                await self._start_servers(project_id, temp_dir, result, bool(backend_files), bool(frontend_files))

            # Determine overall success
            result.success = result.backend_compiled and result.frontend_compiled
            result.status = "completed" if result.success else "failed"

            logger.info(
                "compile_complete",
                project_id=project_id,
                success=result.success,
                backend_errors=len(result.backend_errors),
                frontend_errors=len(result.frontend_errors),
                backend_url=result.backend_url,
                frontend_url=result.frontend_url,
            )

        except Exception as exc:
            result.success = False
            result.status = "failed"
            result.backend_errors.append(f"Compilation exception: {str(exc)}")
            logger.error("compile_error", project_id=project_id, error=str(exc))

        return result

    async def _compile_backend(
        self, temp_dir: str, files: dict[str, str]
    ) -> tuple[bool, list[str], str]:
        """Compile backend Python files."""
        backend_dir = os.path.join(temp_dir, "backend")
        os.makedirs(backend_dir, exist_ok=True)

        errors: list[str] = []
        logs_parts: list[str] = []

        # Write files
        for filename, content in files.items():
            # Strip leading "backend/" if present
            clean_name = filename
            if clean_name.startswith("backend/"):
                clean_name = clean_name[8:]

            file_path = os.path.join(backend_dir, clean_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Syntax check all .py files
        py_files = []
        for root, _, filenames in os.walk(backend_dir):
            for fname in filenames:
                if fname.endswith(".py"):
                    py_files.append(os.path.join(root, fname))

        for py_file in py_files:
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "py_compile", py_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

                if proc.returncode != 0:
                    rel_path = os.path.relpath(py_file, backend_dir)
                    error_msg = stderr.decode("utf-8", errors="replace").strip()
                    errors.append(f"{rel_path}: {error_msg}")
                    logs_parts.append(f"FAIL: {rel_path}\n{error_msg}")
                else:
                    rel_path = os.path.relpath(py_file, backend_dir)
                    logs_parts.append(f"OK: {rel_path}")

            except asyncio.TimeoutError:
                rel_path = os.path.relpath(py_file, backend_dir)
                errors.append(f"{rel_path}: Compilation timed out")
            except Exception as exc:
                rel_path = os.path.relpath(py_file, backend_dir)
                errors.append(f"{rel_path}: {str(exc)}")

        success = len(errors) == 0
        logs = "\n".join(logs_parts)

        return success, errors, logs

    async def _compile_frontend(
        self, temp_dir: str, files: dict[str, str]
    ) -> tuple[bool, list[str], str]:
        """Compile frontend TypeScript/JavaScript files."""
        frontend_dir = os.path.join(temp_dir, "frontend")
        os.makedirs(frontend_dir, exist_ok=True)

        errors: list[str] = []
        logs_parts: list[str] = []

        # Write files — route scaffold files to root, source to src/
        for filename, content in files.items():
            clean_name = filename
            if clean_name.startswith("frontend/"):
                clean_name = clean_name[9:]

            # Scaffold files go to frontend root
            basename = os.path.basename(clean_name)
            if basename in ("package.json", "vite.config.ts", "tsconfig.json", "index.html"):
                file_path = os.path.join(frontend_dir, basename)
            elif clean_name.startswith("src/"):
                file_path = os.path.join(frontend_dir, clean_name)
            else:
                # Source files go to src/
                file_path = os.path.join(frontend_dir, "src", clean_name)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # CRITICAL: Inject missing scaffold files
        self._inject_scaffold_files(frontend_dir)

        # Check if package.json exists after injection
        pkg_json_path = os.path.join(frontend_dir, "package.json")
        if not os.path.exists(pkg_json_path):
            logs_parts.append("WARNING: No package.json found and injection failed — skipping npm build")
            return self._check_frontend_syntax(frontend_dir, files, errors, logs_parts)

        logs_parts.append("package.json found — running npm build")

        # Try npm install + build
        try:
            # npm install
            proc = await asyncio.create_subprocess_exec(
                "npm", "install", "--legacy-peer-deps",
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            logs_parts.append(f"npm install: {'OK' if proc.returncode == 0 else 'FAILED'}")

            if proc.returncode != 0:
                error_text = stderr.decode("utf-8", errors="replace").strip()
                errors.append(f"npm install failed: {error_text[:500]}")
                return False, errors, "\n".join(logs_parts)

            # npm run build
            proc = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=frontend_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            build_output = stdout.decode("utf-8", errors="replace")
            build_errors = stderr.decode("utf-8", errors="replace")
            logs_parts.append(f"npm run build: {'OK' if proc.returncode == 0 else 'FAILED'}")

            if proc.returncode != 0:
                # Parse TypeScript/build errors
                combined = build_output + "\n" + build_errors
                for line in combined.split("\n"):
                    line = line.strip()
                    if line and ("error" in line.lower() or "Error" in line):
                        errors.append(line[:200])

                if not errors:
                    errors.append(f"Build failed with exit code {proc.returncode}")

            logs_parts.append(build_output[:2000])

        except asyncio.TimeoutError:
            errors.append("Frontend build timed out (120s)")
        except FileNotFoundError:
            logs_parts.append("npm not found — skipping frontend build")
            return self._check_frontend_syntax(frontend_dir, files, errors, logs_parts)
        except Exception as exc:
            errors.append(f"Frontend build error: {str(exc)}")

        success = len(errors) == 0
        return success, errors, "\n".join(logs_parts)

    def _inject_scaffold_files(self, frontend_dir: str) -> None:
        """Inject missing scaffold files into the frontend directory."""
        pkg_path = os.path.join(frontend_dir, "package.json")
        if not os.path.exists(pkg_path):
            # Scan source files to detect needed deps
            pkg = dict(_DEFAULT_PACKAGE_JSON)
            src_dir = os.path.join(frontend_dir, "src")
            if os.path.exists(src_dir):
                all_code = ""
                for fname in os.listdir(src_dir):
                    fpath = os.path.join(src_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                                all_code += f.read()
                        except Exception:
                            pass
                if "react-router-dom" in all_code:
                    pkg["dependencies"]["react-router-dom"] = "^7.0.0"
                if "zustand" in all_code:
                    pkg["dependencies"]["zustand"] = "^5.0.0"

            with open(pkg_path, "w", encoding="utf-8") as f:
                json.dump(pkg, f, indent=2)
            logger.info("injected_package_json", dir=frontend_dir)

        tsconfig_path = os.path.join(frontend_dir, "tsconfig.json")
        if not os.path.exists(tsconfig_path):
            with open(tsconfig_path, "w", encoding="utf-8") as f:
                f.write(_DEFAULT_TSCONFIG.strip())

        vite_path = os.path.join(frontend_dir, "vite.config.ts")
        if not os.path.exists(vite_path):
            with open(vite_path, "w", encoding="utf-8") as f:
                f.write(_DEFAULT_VITE_CONFIG.replace("{PORT}", "3000").strip())

        index_html_path = os.path.join(frontend_dir, "index.html")
        if not os.path.exists(index_html_path):
            with open(index_html_path, "w", encoding="utf-8") as f:
                f.write(_DEFAULT_INDEX_HTML.strip())

    async def _start_servers(
        self, project_id: str, temp_dir: str, result: CompileResult,
        has_backend: bool, has_frontend: bool
    ) -> None:
        """Start backend and frontend servers on dynamic ports."""
        processes: list[subprocess.Popen] = []

        if has_backend and result.backend_compiled:
            backend_port = _find_free_port(8010, 8999)
            backend_dir = os.path.join(temp_dir, "backend")
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(backend_port)],
                    cwd=backend_dir,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                processes.append(proc)
                result.backend_url = f"http://localhost:{backend_port}"
                logger.info("backend_started", port=backend_port)
            except Exception as exc:
                logger.warning("backend_start_failed", error=str(exc))

        if has_frontend and result.frontend_compiled:
            frontend_port = _find_free_port(3001, 3999)
            frontend_dir = os.path.join(temp_dir, "frontend")

            # Update vite.config.ts with the dynamic port
            vite_path = os.path.join(frontend_dir, "vite.config.ts")
            if os.path.exists(vite_path):
                with open(vite_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Replace port number
                import re
                content = re.sub(r"port:\s*\d+", f"port: {frontend_port}", content)
                with open(vite_path, "w", encoding="utf-8") as f:
                    f.write(content)

            try:
                proc = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=frontend_dir,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                processes.append(proc)
                result.frontend_url = f"http://localhost:{frontend_port}"
                logger.info("frontend_started", port=frontend_port)
            except Exception as exc:
                logger.warning("frontend_start_failed", error=str(exc))

        if processes:
            self._active_processes[project_id] = processes

    def _check_frontend_syntax(
        self,
        frontend_dir: str,
        files: dict[str, str],
        errors: list[str],
        logs_parts: list[str],
    ) -> tuple[bool, list[str], str]:
        """Basic syntax checking for frontend files (no npm available)."""
        # Simple bracket/paren balance check
        for filename, content in files.items():
            if filename.endswith((".ts", ".tsx", ".js", ".jsx")):
                open_parens = content.count("(") - content.count(")")
                open_braces = content.count("{") - content.count("}")
                open_brackets = content.count("[") - content.count("]")

                if open_parens != 0:
                    errors.append(f"{filename}: Unbalanced parentheses (diff: {open_parens})")
                if open_braces != 0:
                    errors.append(f"{filename}: Unbalanced braces (diff: {open_braces})")
                if open_brackets != 0:
                    errors.append(f"{filename}: Unbalanced brackets (diff: {open_brackets})")

                if not errors:
                    logs_parts.append(f"OK (syntax): {filename}")

        success = len(errors) == 0
        return success, errors, "\n".join(logs_parts)

    def stop_servers(self, project_id: str) -> None:
        """Stop running servers for a project."""
        processes = self._active_processes.pop(project_id, [])
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def cleanup(self, temp_dir: str) -> None:
        """Remove a temporary compilation directory."""
        try:
            if os.path.exists(temp_dir) and "nexusforge_" in temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info("compile_cleanup", temp_dir=temp_dir)
        except Exception as exc:
            logger.warning("compile_cleanup_failed", temp_dir=temp_dir, error=str(exc))
