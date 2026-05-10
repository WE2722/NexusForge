"""
NexusForge Orchestrator — coordinates agents to build complete projects.
"""
from __future__ import annotations

import asyncio
import time
import json
from datetime import datetime, timezone

import structlog

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.backend_agent import BackendAgent
from app.agents.base_agent import BaseAgent
from app.agents.database_agent import DatabaseAgent
from app.agents.debugger_agent import DebuggerAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.review_agent import ReviewAgent
from app.core.llm_router import LLMRouter
from app.core.prompt_refiner import PromptRefiner
from app.core.token_budget import TokenBudgetManager
import os
from app.models.schemas import (
    AgentType,
    ComplexityLevel,
    Project,
    ProjectStatus,
    Task,
    TaskPriority,
    TaskStatus,
    TokenUsage,
)

logger = structlog.get_logger(__name__)


class Orchestrator:
    """
    Central coordinator that:
    1. Refines a raw prompt into a ProjectBrief
    2. Decomposes the brief into tasks
    3. Assigns agents and executes tasks in parallel waves
    4. Passes context between waves so agents can see each other's output
    5. Auto-retries failed tasks using the debugger agent
    """

    def __init__(self) -> None:
        self.budget = TokenBudgetManager()
        self.router = LLMRouter(budget_manager=self.budget)
        self.refiner = PromptRefiner(router=self.router)
        self._agents: dict[AgentType, BaseAgent] = {
            AgentType.ARCHITECTURE: ArchitectureAgent(router=self.router),
            AgentType.BACKEND: BackendAgent(router=self.router),
            AgentType.FRONTEND: FrontendAgent(router=self.router),
            AgentType.DATABASE: DatabaseAgent(router=self.router),
            AgentType.DEBUGGER: DebuggerAgent(router=self.router),
            AgentType.REVIEW: ReviewAgent(router=self.router),
        }
        self._projects: dict[str, Project] = {}
        self._paused: set[str] = set()
        self._storage_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "projects.json")
        self._load_projects()

    def _load_projects(self) -> None:
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self._projects[k] = Project.model_validate(v)
                logger.info("projects_loaded", count=len(self._projects))
            except Exception as e:
                logger.error("projects_load_error", error=str(e))

    def _save_projects(self) -> None:
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                data = {k: v.model_dump(mode='json') for k, v in self._projects.items()}
                json.dump(data, f)
        except Exception as e:
            logger.error("projects_save_error", error=str(e))

    # ── Public API ─────────────────────────────────────────────────
    async def create_project(self, raw_prompt: str) -> Project:
        project = Project(raw_prompt=raw_prompt, status=ProjectStatus.REFINING)
        self._projects[project.id] = project
        self._save_projects()
        logger.info("project_created", project_id=project.id)

        # Step 1: Refine prompt
        brief = await self.refiner.refine(raw_prompt)
        project.brief = brief
        project.status = ProjectStatus.PLANNING

        # Step 2: Decompose into tasks
        tasks = self._decompose(brief)
        project.tasks = tasks
        project.status = ProjectStatus.EXECUTING
        self._save_projects()

        # Step 3: Execute tasks in waves with context passing
        await self._execute_waves(project)
        return project

    async def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    async def list_projects(self) -> list[Project]:
        return list(self._projects.values())

    def get_agents(self) -> list[dict]:
        return [agent.get_info() for agent in self._agents.values()]

    def pause_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            self._paused.add(project_id)
            self._projects[project_id].status = ProjectStatus.PAUSED
            self._save_projects()
            return True
        return False

    def resume_project(self, project_id: str) -> bool:
        if project_id in self._paused:
            self._paused.discard(project_id)
            self._projects[project_id].status = ProjectStatus.EXECUTING
            self._save_projects()
            return True
        return False

    # ── Context Collector ──────────────────────────────────────────
    def _collect_context(self, project: Project, up_to_wave: int) -> str:
        """Collect all code blocks from completed tasks in previous waves."""
        context_parts = []
        for task in project.tasks:
            if task.wave < up_to_wave and task.status == TaskStatus.COMPLETED and task.result:
                if task.result.code_blocks:
                    context_parts.append(f"--- {task.agent_type.value} agent output ---")
                    for filename, code in task.result.code_blocks.items():
                        context_parts.append(f"File: {filename}")
                        context_parts.append(f"```\n{code}\n```")
                elif task.result.output:
                    context_parts.append(f"--- {task.agent_type.value} agent output ---")
                    # Truncate very long outputs
                    output = task.result.output[:3000]
                    context_parts.append(output)
        return "\n\n".join(context_parts)

    def _collect_all_code(self, project: Project) -> str:
        """Collect ALL code blocks from ALL completed tasks for review."""
        context_parts = []
        for task in project.tasks:
            if task.status == TaskStatus.COMPLETED and task.result and task.result.code_blocks:
                context_parts.append(f"--- {task.agent_type.value} agent: {task.title} ---")
                for filename, code in task.result.code_blocks.items():
                    context_parts.append(f"File: {filename}")
                    context_parts.append(f"```\n{code}\n```")
        return "\n\n".join(context_parts)

    # ── Task Decomposition ─────────────────────────────────────────
    def _decompose(self, brief) -> list[Task]:
        tasks: list[Task] = []
        is_simple = brief.complexity in (ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE)

        # Wave 0: Architecture
        arch_task = Task(
            title=f"Design architecture for {brief.title}",
            description=f"Create system architecture for: {brief.description}\nFeatures: {', '.join(brief.features)}\nTech: {', '.join(brief.tech_stack)}",
            agent_type=AgentType.ARCHITECTURE,
            priority=TaskPriority.CRITICAL,
            wave=0,
        )
        tasks.append(arch_task)

        # Wave 1: Backend (+ Database only for complex apps)
        backend_task = Task(
            title=f"Implement backend API for {brief.title}",
            description=f"Create backend endpoints for: {brief.description}\nFeatures: {', '.join(brief.features)}",
            agent_type=AgentType.BACKEND,
            priority=TaskPriority.HIGH,
            dependencies=[arch_task.id],
            wave=1,
        )
        tasks.append(backend_task)

        if not is_simple:
            db_task = Task(
                title=f"Design database schema for {brief.title}",
                description=f"Create database models for: {brief.description}\nTech: {', '.join(brief.tech_stack)}",
                agent_type=AgentType.DATABASE,
                priority=TaskPriority.HIGH,
                dependencies=[arch_task.id],
                wave=1,
            )
            tasks.append(db_task)

        # Wave 2: Frontend
        frontend_task = Task(
            title=f"Build frontend UI for {brief.title}",
            description=f"Create React UI for: {brief.description}\nFeatures: {', '.join(brief.features)}",
            agent_type=AgentType.FRONTEND,
            priority=TaskPriority.HIGH,
            dependencies=[backend_task.id],
            wave=2,
        )
        tasks.append(frontend_task)

        # Wave 3: Review
        review_task = Task(
            title=f"Review code quality for {brief.title}",
            description=f"Review all generated code for quality, security, and integration correctness.",
            agent_type=AgentType.REVIEW,
            priority=TaskPriority.MEDIUM,
            dependencies=[frontend_task.id, backend_task.id],
            wave=3,
        )
        tasks.append(review_task)

        return tasks

    # ── Wave Execution ─────────────────────────────────────────────
    async def _execute_waves(self, project: Project) -> None:
        waves: dict[int, list[Task]] = {}
        for task in project.tasks:
            waves.setdefault(task.wave, []).append(task)

        for wave_num in sorted(waves.keys()):
            if project.id in self._paused:
                logger.info("project_paused", project_id=project.id, wave=wave_num)
                return

            wave_tasks = waves[wave_num]
            logger.info("executing_wave", wave=wave_num, tasks=len(wave_tasks))

            # Inject context from previous waves into each task
            context = self._collect_context(project, wave_num)
            for task in wave_tasks:
                task.metadata["context"] = context

            # Special handling for review wave: inject ALL code
            if wave_num == max(waves.keys()):
                all_code = self._collect_all_code(project)
                for task in wave_tasks:
                    if task.agent_type == AgentType.REVIEW:
                        task.metadata["context"] = all_code

            results = await asyncio.gather(
                *[self._execute_task(task, project) for task in wave_tasks],
                return_exceptions=True,
            )

            for task, result in zip(wave_tasks, results):
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.result = self._agents[task.agent_type]._build_result(
                        task, False, "", errors=[str(result)]
                    )
                    logger.error("task_failed", task_id=task.id, error=str(result))

            self._save_projects()

        # Apply review corrections: if review agent produced code blocks, merge them
        self._apply_review_corrections(project)

        # Mark complete
        all_done = all(t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in project.tasks)
        project.status = ProjectStatus.COMPLETED if all_done else ProjectStatus.FAILED
        project.completed_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)
        self._save_projects()

    def _apply_review_corrections(self, project: Project) -> None:
        """If the review agent produced corrected code blocks, merge them into the original tasks."""
        review_blocks: dict[str, str] = {}
        for task in project.tasks:
            if task.agent_type == AgentType.REVIEW and task.result and task.result.code_blocks:
                review_blocks.update(task.result.code_blocks)

        if not review_blocks:
            return

        logger.info("applying_review_corrections", files=list(review_blocks.keys()))

        for task in project.tasks:
            if task.result and task.result.code_blocks:
                for filename, corrected_code in review_blocks.items():
                    if filename in task.result.code_blocks:
                        task.result.code_blocks[filename] = corrected_code
                        logger.info("file_corrected_by_review", filename=filename, task_id=task.id)

        self._save_projects()

    async def _execute_task(self, task: Task, project: Project) -> None:
        agent = self._agents.get(task.agent_type)
        if not agent:
            task.status = TaskStatus.FAILED
            return

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        task.attempts += 1

        try:
            result = await agent.execute(task)
            task.result = result
            if result.success:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
                # Auto-debug: if this is a code-producing agent, try the debugger
                if task.agent_type in (AgentType.BACKEND, AgentType.FRONTEND) and task.attempts < task.max_attempts:
                    await self._auto_debug(task, project)
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.result = agent._build_result(task, False, "", errors=[str(exc)])
            logger.error("task_execution_error", task_id=task.id, error=str(exc))
        finally:
            task.completed_at = datetime.now(timezone.utc)
            self._save_projects()

    async def _auto_debug(self, failed_task: Task, project: Project) -> None:
        """Attempt to fix a failed task using the debugger agent."""
        debugger = self._agents[AgentType.DEBUGGER]
        logger.info("auto_debug_start", task_id=failed_task.id, attempt=failed_task.attempts)

        # Collect error info and failed code
        errors = "\n".join(failed_task.result.errors if failed_task.result else [])
        failed_code = ""
        if failed_task.result and failed_task.result.code_blocks:
            for filename, code in failed_task.result.code_blocks.items():
                failed_code += f"\n--- {filename} ---\n{code}\n"
        elif failed_task.result:
            failed_code = failed_task.result.output[:5000]

        debug_task = Task(
            title=f"Debug: {failed_task.title}",
            description=f"Fix errors in the generated code for: {failed_task.description}",
            agent_type=AgentType.DEBUGGER,
            priority=TaskPriority.CRITICAL,
            wave=failed_task.wave,
            metadata={
                "errors": errors,
                "failed_code": failed_code,
                "context": self._collect_context(project, failed_task.wave),
            },
        )

        try:
            result = await debugger.execute(debug_task)
            if result.success and result.code_blocks:
                # Merge debugger fixes into the failed task's result
                if failed_task.result:
                    failed_task.result.code_blocks.update(result.code_blocks)
                    failed_task.result.success = True
                    failed_task.result.errors = []
                    failed_task.result.output += f"\n\n--- DEBUGGER FIX (attempt {failed_task.attempts}) ---\n{result.output}"
                else:
                    failed_task.result = result
                failed_task.status = TaskStatus.COMPLETED
                logger.info("auto_debug_success", task_id=failed_task.id)
            else:
                logger.warning("auto_debug_failed", task_id=failed_task.id)
        except Exception as exc:
            logger.error("auto_debug_error", task_id=failed_task.id, error=str(exc))

    async def close(self) -> None:
        await self.router.close()
