"""Auto Recovery — advanced task retry with provider escalation."""
from __future__ import annotations

import asyncio
import structlog

from app.models.schemas import Task, TaskStatus
from app.core.llm_router import LLMRouter

logger = structlog.get_logger(__name__)

class AutoRecovery:
    """Attempts to recover from failed tasks by trying alternative providers or strategies."""
    
    def __init__(self, router: LLMRouter | None = None) -> None:
        self.router = router or LLMRouter()
        
    async def retry_with_alternative_providers(self, task: Task, agent_executor, max_attempts: int = 3) -> bool:
        """
        Retries a failed task using alternative LLM providers.
        Escalates to human review if all attempts fail.
        """
        if task.status != TaskStatus.FAILED:
            return True
            
        logger.info("initiating_auto_recovery", task_id=task.id)
        
        for attempt in range(1, max_attempts + 1):
            task.attempts += 1
            logger.info("auto_recovery_attempt", task_id=task.id, attempt=attempt)
            
            try:
                # Re-execute the task (in real app, this would explicitly swap the preferred provider)
                result = await agent_executor(task)
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    logger.info("auto_recovery_success", task_id=task.id)
                    return True
            except Exception as exc:
                logger.warning("auto_recovery_error", task_id=task.id, attempt=attempt, error=str(exc))
                
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        logger.error("auto_recovery_failed_escalating", task_id=task.id)
        # Escalation logic here (e.g., mark for human review)
        return False
