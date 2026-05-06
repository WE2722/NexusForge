"""Docker Sandbox — safely executes generated code."""
from __future__ import annotations

import asyncio
import subprocess
import tempfile
import os
import structlog

logger = structlog.get_logger(__name__)

class Sandbox:
    """Provides an isolated environment to execute generated code via Docker."""
    
    async def run_code_in_container(self, code: str, lang: str = "python") -> dict:
        """Executes code in a temporary Docker container with a 30s timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            if lang == "python":
                file_path = os.path.join(temp_dir, "script.py")
                with open(file_path, "w") as f:
                    f.write(code)
                
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{temp_dir}:/app",
                    "-w", "/app",
                    "--network", "none",
                    "--memory", "128m",
                    "--cpus", "0.5",
                    "python:3.13-slim",
                    "python", "script.py"
                ]
            else:
                return {"success": False, "output": "", "errors": ["Unsupported language"]}

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode() if stdout else "",
                    "errors": stderr.decode().splitlines() if stderr else []
                }
            except asyncio.TimeoutError:
                if process:
                    process.kill()
                return {"success": False, "output": "", "errors": ["Execution timed out (30s)"]}
            except Exception as exc:
                logger.error("sandbox_execution_failed", error=str(exc))
                return {"success": False, "output": "", "errors": [str(exc)]}
