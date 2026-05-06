"""Git Integrator — manages project version control."""
from __future__ import annotations

import asyncio
import os
import subprocess
import structlog

logger = structlog.get_logger(__name__)

class GitIntegrator:
    """Handles Git operations for generated projects."""
    
    def init_repo(self, project_path: str) -> bool:
        """Initializes a new Git repository."""
        return self._run_git_cmd(["git", "init"], project_path)
        
    def commit_after_step(self, project_path: str, step_name: str, files: list[str]) -> bool:
        """Adds files and commits with a standardized message."""
        # Add files
        self._run_git_cmd(["git", "add", "."], project_path)
        
        # Commit
        msg = f"feat: completed {step_name}"
        return self._run_git_cmd(["git", "commit", "-m", msg], project_path)
        
    def tag_version(self, project_path: str, version: str) -> bool:
        """Creates a Git tag."""
        return self._run_git_cmd(["git", "tag", version], project_path)
        
    def rollback_to_tag(self, project_path: str, tag: str) -> bool:
        """Hard resets the repository to a specific tag."""
        return self._run_git_cmd(["git", "reset", "--hard", tag], project_path)
        
    def _run_git_cmd(self, cmd: list[str], cwd: str) -> bool:
        if not os.path.exists(cwd):
            return False
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            logger.debug("git_cmd_success", cmd=" ".join(cmd), output=result.stdout)
            return True
        except subprocess.CalledProcessError as exc:
            logger.error("git_cmd_failed", cmd=" ".join(cmd), error=exc.stderr)
            return False
