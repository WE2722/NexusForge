"""Execution Engine — builds DAG and executes tasks in waves."""
from __future__ import annotations

import asyncio
from typing import Callable, Awaitable
import structlog

from app.models.schemas import Task, TaskStatus

logger = structlog.get_logger(__name__)

class ExecutionEngine:
    """Builds a dependency graph and executes tasks in waves."""
    
    def build_dependency_graph(self, tasks: list[Task]) -> dict[int, list[Task]]:
        """
        Groups tasks into waves based on their explicit dependencies.
        (Currently relying on pre-calculated wave property, but could dynamically build it).
        """
        waves: dict[int, list[Task]] = {}
        for task in tasks:
            waves.setdefault(task.wave, []).append(task)
        return waves
        
    async def execute_waves(self, tasks: list[Task], executor_func: Callable[[Task], Awaitable[None]]) -> None:
        """Executes tasks parallel per wave, sequential between waves."""
        waves = self.build_dependency_graph(tasks)
        
        for wave_num in sorted(waves.keys()):
            wave_tasks = waves[wave_num]
            logger.info("execution_engine_wave_start", wave=wave_num, tasks_count=len(wave_tasks))
            
            # Filter out tasks whose dependencies failed
            runnable_tasks = []
            for task in wave_tasks:
                can_run = True
                for dep_id in task.dependencies:
                    dep_task = next((t for t in tasks if t.id == dep_id), None)
                    if dep_task and dep_task.status == TaskStatus.FAILED:
                        can_run = False
                        task.status = TaskStatus.SKIPPED
                        logger.warning("task_skipped_due_to_dependency", task_id=task.id, dep_id=dep_id)
                        break
                if can_run:
                    runnable_tasks.append(task)
            
            # Execute runnable tasks in parallel
            if runnable_tasks:
                await asyncio.gather(*[executor_func(t) for t in runnable_tasks])
                
            logger.info("execution_engine_wave_complete", wave=wave_num)
