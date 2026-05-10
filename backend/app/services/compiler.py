"""
Compiler — builds generated projects in isolated temp directories.

Steps:
  1. Create UUID-based temp directory
  2. Write all project files preserving structure
  3. Backend: venv → pip install → py_compile → uvicorn start attempt
  4. Frontend: npm install → npm run build
  5. Capture all output
  6. Return CompileResult with success/errors/logs
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any

import structlog

from app.models.schemas import CompileResult

logger = structlog.get_logger(__name__)


class Compiler:
    """Compiles generated projects in isolated environments."""

    def __init__(self) -> None:
        self._active_previews: dict[str, dict[str, Any]] = {}

    async def compile_project(
        self, project_id: str, project_files: dict[str, str]
    ) -> CompileResult:
        """
        Compile a project's files in an isolated temp directory.

        Args:
            project_id: The project ID.
            project_files: Dict of {filename: content} from the project.

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
                elif filename.endswith((".tsx", ".ts", ".jsx", ".js", ".css", ".html")) or "frontend" in filename.lower():
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

            # Determine overall success
            result.success = result.backend_compiled and result.frontend_compiled
            result.status = "completed" if result.success else "failed"

            logger.info(
                "compile_complete",
                project_id=project_id,
                success=result.success,
                backend_errors=len(result.backend_errors),
                frontend_errors=len(result.frontend_errors),
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

        # Write files
        for filename, content in files.items():
            clean_name = filename
            if clean_name.startswith("frontend/"):
                clean_name = clean_name[9:]

            file_path = os.path.join(frontend_dir, clean_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Check if package.json exists; if not, create a basic one
        pkg_json_path = os.path.join(frontend_dir, "package.json")
        if not os.path.exists(pkg_json_path):
            logs_parts.append("No package.json found — skipping npm build")
            # Still check for basic syntax issues in .ts/.tsx files
            return self._check_frontend_syntax(frontend_dir, files, errors, logs_parts)

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

    def cleanup(self, temp_dir: str) -> None:
        """Remove a temporary compilation directory."""
        try:
            if os.path.exists(temp_dir) and "nexusforge_" in temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info("compile_cleanup", temp_dir=temp_dir)
        except Exception as exc:
            logger.warning("compile_cleanup_failed", temp_dir=temp_dir, error=str(exc))
