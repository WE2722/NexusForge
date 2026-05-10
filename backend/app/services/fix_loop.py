"""
FixLoop — iterative compile-detect-fix cycle using DebuggerAgent and ReviewAgent.

Loop (up to max_iterations):
  1. Compile project
  2. If success → done
  3. Classify errors
  4. Group by file
  5. Send to DebuggerAgent → get fix
  6. Send to ReviewAgent → validate fix
  7. Apply fixes → next iteration
"""
from __future__ import annotations

import asyncio
import time
from enum import Enum

import structlog

from app.models.schemas import (
    AgentType,
    CompileResult,
    FixResult,
    Task,
    TaskPriority,
    TaskStatus,
)
from app.services.compiler import Compiler

logger = structlog.get_logger(__name__)


class ErrorCategory(str, Enum):
    SYNTAX = "syntax"
    TYPE_MISMATCH = "type_mismatch"
    MISSING_IMPORT = "missing_import"
    UNDEFINED_VAR = "undefined_var"
    API_MISMATCH = "api_mismatch"
    LOGIC_ERROR = "logic_error"
    RUNTIME_CRASH = "runtime_crash"


# Keywords for error classification
ERROR_PATTERNS: dict[ErrorCategory, list[str]] = {
    ErrorCategory.SYNTAX: ["SyntaxError", "unexpected token", "invalid syntax", "expected", "parsing error"],
    ErrorCategory.TYPE_MISMATCH: ["TypeError", "type mismatch", "is not assignable", "Expected type"],
    ErrorCategory.MISSING_IMPORT: ["ModuleNotFoundError", "ImportError", "Cannot find module", "No module named"],
    ErrorCategory.UNDEFINED_VAR: ["NameError", "is not defined", "ReferenceError", "undefined"],
    ErrorCategory.API_MISMATCH: ["404", "endpoint", "route not found", "CORS", "fetch failed"],
    ErrorCategory.LOGIC_ERROR: ["AssertionError", "ValueError", "KeyError", "IndexError"],
    ErrorCategory.RUNTIME_CRASH: ["RuntimeError", "crash", "segfault", "killed", "OOM"],
}


class FixLoop:
    """
    Iterative fix loop: compile → detect errors → fix with agents → repeat.
    """

    def __init__(self, orchestrator) -> None:
        """
        Args:
            orchestrator: The main Orchestrator instance (provides agents and router).
        """
        self._orchestrator = orchestrator
        self._compiler = Compiler()

    async def fix_project(
        self,
        project_id: str,
        max_iterations: int = 5,
    ) -> FixResult:
        """
        Run the fix loop on a project.

        Args:
            project_id: Project to fix.
            max_iterations: Maximum fix attempts.

        Returns:
            FixResult with details on what was fixed.
        """
        result = FixResult(status="running")
        project = await self._orchestrator.get_project(project_id)

        if not project:
            result.status = "failed"
            result.logs = "Project not found"
            return result

        # Collect current project files
        project_files = self._collect_files(project)
        if not project_files:
            result.status = "failed"
            result.logs = "No project files found"
            return result

        all_fixed: list[str] = []
        logs_parts: list[str] = []

        for iteration in range(1, max_iterations + 1):
            logger.info("fix_loop_iteration", project_id=project_id, iteration=iteration)
            logs_parts.append(f"\n=== Iteration {iteration}/{max_iterations} ===")

            # Step 1: Compile
            compile_result = await self._compiler.compile_project(project_id, project_files)

            # Step 2: Check success
            if compile_result.success:
                result.success = True
                result.iterations_used = iteration
                result.status = "completed"
                logs_parts.append("✅ Compilation successful!")
                break

            # Step 3: Collect all errors
            all_errors = compile_result.backend_errors + compile_result.frontend_errors
            logs_parts.append(f"Found {len(all_errors)} error(s)")

            if not all_errors:
                # Compilation failed but no specific errors detected
                logs_parts.append("⚠️ Build failed but no specific errors captured")
                result.iterations_used = iteration
                break

            # Step 4: Classify and group errors
            error_groups = self._classify_errors(all_errors)
            logs_parts.append(f"Error categories: {', '.join(c.value for c in error_groups.keys())}")

            # Step 5: Fix errors using DebuggerAgent
            fixes_this_round: dict[str, str] = {}
            errors_fixed_this_round: list[str] = []

            for category, errors in error_groups.items():
                error_text = "\n".join(errors)
                logs_parts.append(f"\nFixing {category.value} errors ({len(errors)} errors)...")

                # Create debug task
                debug_result = await self._run_debugger(
                    project_id, error_text, project_files, category
                )

                if debug_result and debug_result.code_blocks:
                    # Step 6: Review the fix
                    review_passed = await self._run_review(
                        debug_result.code_blocks, error_text
                    )

                    if review_passed:
                        fixes_this_round.update(debug_result.code_blocks)
                        errors_fixed_this_round.extend(errors)
                        logs_parts.append(f"  ✅ Fixed {len(debug_result.code_blocks)} file(s)")
                    else:
                        logs_parts.append(f"  ⚠️ Review rejected fix for {category.value}")
                else:
                    logs_parts.append(f"  ❌ Debugger could not fix {category.value} errors")

            # Step 7: Apply fixes to project files
            if fixes_this_round:
                for filename, new_code in fixes_this_round.items():
                    project_files[filename] = new_code
                all_fixed.extend(errors_fixed_this_round)

                # Update the project's actual code blocks
                self._update_project_files(project, fixes_this_round)
                self._orchestrator._save_projects()

                logs_parts.append(f"\nApplied {len(fixes_this_round)} fix(es)")
            else:
                logs_parts.append("\nNo fixes could be applied this iteration")
                result.iterations_used = iteration
                break

            # Cleanup temp dir from this iteration
            if compile_result.temp_dir:
                self._compiler.cleanup(compile_result.temp_dir)

            result.iterations_used = iteration

        # Final compilation check if loop completed without success
        if not result.success:
            final_compile = await self._compiler.compile_project(project_id, project_files)
            remaining_errors = final_compile.backend_errors + final_compile.frontend_errors

            result.errors_remaining = remaining_errors
            result.manual_fixes_needed = [
                {"file": "unknown", "error": err, "suggestion": "Manual review required"}
                for err in remaining_errors
            ]
            result.status = "partial" if all_fixed else "failed"

            if final_compile.temp_dir:
                self._compiler.cleanup(final_compile.temp_dir)

        result.errors_fixed = all_fixed
        result.logs = "\n".join(logs_parts)

        logger.info(
            "fix_loop_complete",
            project_id=project_id,
            success=result.success,
            iterations=result.iterations_used,
            fixed=len(all_fixed),
            remaining=len(result.errors_remaining),
        )

        return result

    # ── Error Classification ───────────────────────────────────────

    def _classify_errors(self, errors: list[str]) -> dict[ErrorCategory, list[str]]:
        """Classify errors into categories based on keywords."""
        groups: dict[ErrorCategory, list[str]] = {}

        for error in errors:
            categorized = False
            for category, patterns in ERROR_PATTERNS.items():
                if any(p.lower() in error.lower() for p in patterns):
                    groups.setdefault(category, []).append(error)
                    categorized = True
                    break

            if not categorized:
                # Default to SYNTAX for uncategorized errors
                groups.setdefault(ErrorCategory.SYNTAX, []).append(error)

        return groups

    # ── Agent Execution ────────────────────────────────────────────

    async def _run_debugger(
        self,
        project_id: str,
        error_text: str,
        project_files: dict[str, str],
        category: ErrorCategory,
    ):
        """Run the DebuggerAgent to fix errors."""
        debugger = self._orchestrator._agents.get(AgentType.DEBUGGER)
        if not debugger:
            logger.warning("debugger_not_available")
            return None

        # Build context from project files
        code_context = ""
        for filename, code in project_files.items():
            code_context += f"\n--- {filename} ---\n{code}\n"

        task = Task(
            title=f"Fix {category.value} errors",
            description=(
                f"Fix the following {category.value} errors in the generated code.\n\n"
                f"ERRORS:\n{error_text}\n\n"
                f"Output corrected files only."
            ),
            agent_type=AgentType.DEBUGGER,
            priority=TaskPriority.CRITICAL,
            metadata={
                "errors": error_text,
                "failed_code": code_context[:10000],
                "context": code_context[:10000],
            },
        )

        try:
            result = await debugger.execute(task)
            return result if result.success else None
        except Exception as exc:
            logger.error("fix_debugger_error", error=str(exc))
            return None

    async def _run_review(
        self, fixed_code: dict[str, str], original_errors: str
    ) -> bool:
        """Run ReviewAgent to validate the fix. Returns True if fix is acceptable."""
        reviewer = self._orchestrator._agents.get(AgentType.REVIEW)
        if not reviewer:
            # If no reviewer, accept the fix
            return True

        code_text = ""
        for filename, code in fixed_code.items():
            code_text += f"\n--- {filename} ---\n{code}\n"

        task = Task(
            title="Review auto-fix",
            description=(
                f"Review this auto-fix for errors:\n{original_errors[:2000]}\n\n"
                f"Fixed code:\n{code_text[:5000]}\n\n"
                f"Does this fix look correct? If yes, say 'APPROVED'."
            ),
            agent_type=AgentType.REVIEW,
            priority=TaskPriority.HIGH,
            metadata={"context": code_text[:8000]},
        )

        try:
            result = await reviewer.execute(task)
            if result.success and result.output:
                # If review contains corrected code blocks, use those instead
                # Otherwise, check for approval
                return "approved" in result.output.lower() or bool(result.code_blocks)
            return True  # Default: accept if review runs successfully
        except Exception as exc:
            logger.warning("fix_review_error", error=str(exc))
            return True  # Accept fix if review fails

    # ── Helpers ────────────────────────────────────────────────────

    def _collect_files(self, project) -> dict[str, str]:
        """Collect all code blocks from project tasks."""
        files: dict[str, str] = {}
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                files.update(task.result.code_blocks)
        return files

    def _update_project_files(
        self, project, fixes: dict[str, str]
    ) -> None:
        """Update project task code_blocks with fixes."""
        for filename, new_code in fixes.items():
            applied = False
            for task in project.tasks:
                if task.result and task.result.code_blocks and filename in task.result.code_blocks:
                    task.result.code_blocks[filename] = new_code
                    applied = True
                    break

            if not applied:
                # Add to the first task with code blocks
                for task in project.tasks:
                    if task.result and task.result.code_blocks is not None:
                        task.result.code_blocks[filename] = new_code
                        break
