"""
NexusForge Base Agent — abstract base class for all specialized agents.
"""
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable

import structlog

from app.core.llm_router import LLMRouter
from app.models.schemas import AgentResult, AgentType, LLMProvider, LLMRequest, Task

logger = structlog.get_logger(__name__)


def retry_on_failure(max_retries: int = 2, delay: float = 1.0):
    """Decorator: retry an async method on exception."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning("agent_retry", attempt=attempt + 1, error=str(exc))
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


class BaseAgent(ABC):
    """
    Abstract base for every NexusForge agent.

    Subclasses must set class-level attributes and implement ``execute()``.
    """

    name: str = "base"
    role: str = "Generic Agent"
    agent_type: AgentType = AgentType.FRONTEND
    expertise: list[str] = []
    preferred_providers: list[LLMProvider] = [LLMProvider.GOOGLE]

    def __init__(self, router: LLMRouter | None = None) -> None:
        self.router = router or LLMRouter()

    # ── Abstract ───────────────────────────────────────────────────
    @abstractmethod
    async def execute(self, task: Task) -> AgentResult:
        """Execute the given task and return a result."""
        ...

    # ── LLM helper ─────────────────────────────────────────────────
    @retry_on_failure(max_retries=2)
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        provider: LLMProvider | None = None,
    ):
        """Call the LLM router, preferring this agent's preferred providers."""
        chosen_provider = provider or (self.preferred_providers[0] if self.preferred_providers else LLMProvider.GOOGLE)
        request = LLMRequest(
            provider=chosen_provider,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return await self.router.generate(request)

    # ── Utilities ──────────────────────────────────────────────────
    def _build_result(
        self,
        task: Task,
        success: bool,
        output: str,
        code_blocks: dict[str, str] | None = None,
        files_created: list[str] | None = None,
        errors: list[str] | None = None,
        reasoning: str = "",
        execution_time_ms: float = 0.0,
    ) -> AgentResult:
        return AgentResult(
            agent_type=self.agent_type,
            task_id=task.id,
            success=success,
            output=output,
            code_blocks=code_blocks or {},
            files_created=files_created or [],
            errors=errors or [],
            reasoning=reasoning,
            execution_time_ms=execution_time_ms,
        )

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "role": self.role,
            "expertise": self.expertise,
            "preferred_providers": [p.value for p in self.preferred_providers],
        }
