"""
NexusForge Orchestrator — coordinates agents to build complete projects.
"""
from __future__ import annotations

import asyncio
import time
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
from app.models.schemas import (
    AgentType,
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

    # ── Public API ─────────────────────────────────────────────────
    async def create_project(self, raw_prompt: str) -> Project:
        project = Project(raw_prompt=raw_prompt, status=ProjectStatus.REFINING)
        self._projects[project.id] = project
        logger.info("project_created", project_id=project.id)

        # Step 1: Refine prompt
        brief = await self.refiner.refine(raw_prompt)
        project.brief = brief
        project.status = ProjectStatus.PLANNING

        # Step 2: Decompose into tasks
        tasks = self._decompose(brief)
        project.tasks = tasks
        project.status = ProjectStatus.EXECUTING

        # Step 3: Execute tasks in waves
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
            return True
        return False

    def resume_project(self, project_id: str) -> bool:
        if project_id in self._paused:
            self._paused.discard(project_id)
            self._projects[project_id].status = ProjectStatus.EXECUTING
            return True
        return False

    # ── Task Decomposition ─────────────────────────────────────────
    def _decompose(self, brief) -> list[Task]:
        tasks: list[Task] = []

        # Wave 0: Architecture
        arch_task = Task(
            title=f"Design architecture for {brief.title}",
            description=f"Create system architecture for: {brief.description}",
            agent_type=AgentType.ARCHITECTURE,
            priority=TaskPriority.CRITICAL,
            wave=0,
        )
        tasks.append(arch_task)

        # Wave 1: Database + Backend (parallel)
        db_task = Task(
            title=f"Design database schema for {brief.title}",
            description=f"Create database models for: {brief.description}\nTech: {', '.join(brief.tech_stack)}",
            agent_type=AgentType.DATABASE,
            priority=TaskPriority.HIGH,
            dependencies=[arch_task.id],
            wave=1,
        )
        tasks.append(db_task)

        backend_task = Task(
            title=f"Implement backend API for {brief.title}",
            description=f"Create backend endpoints for: {brief.description}\nFeatures: {', '.join(brief.features)}",
            agent_type=AgentType.BACKEND,
            priority=TaskPriority.HIGH,
            dependencies=[arch_task.id],
            wave=1,
        )
        tasks.append(backend_task)

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
            description="Review all generated code for quality, security, and best practices.",
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

            results = await asyncio.gather(
                *[self._execute_task(task) for task in wave_tasks],
                return_exceptions=True,
            )

            for task, result in zip(wave_tasks, results):
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.result = self._agents[task.agent_type]._build_result(
                        task, False, "", errors=[str(result)]
                    )
                    logger.error("task_failed", task_id=task.id, error=str(result))

        # Mark complete
        all_done = all(t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in project.tasks)
        project.status = ProjectStatus.COMPLETED if all_done else ProjectStatus.FAILED
        project.completed_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)

    async def _execute_task(self, task: Task) -> None:
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
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.result = agent._build_result(task, False, "", errors=[str(exc)])
            logger.error("task_execution_error", task_id=task.id, error=str(exc))
        finally:
            task.completed_at = datetime.now(timezone.utc)

    async def close(self) -> None:
        await self.router.close()
