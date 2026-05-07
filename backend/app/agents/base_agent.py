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

    def _extract_code_blocks(self, content: str) -> dict[str, str]:
        import re
        blocks: dict[str, str] = {}
        lines = content.split("\n")
        i, block_name, block_lines = 0, "", []
        in_block = False
        while i < len(lines):
            line = lines[i]
            if line.startswith("```") and not in_block:
                in_block = True
                lang_parts = line[3:].strip().split()
                lang = lang_parts[0] if lang_parts else "txt"
                
                # Extract filename from markdown
                found_name = ""
                # 1. If filename is in the ``` tag (e.g., ```python src/main.py)
                if len(lang_parts) > 1:
                    found_name = lang_parts[1].split("/")[-1]
                else:
                    # 2. Look backwards up to 5 lines for a filename hint
                    prev_idx = i - 1
                    while prev_idx >= 0 and i - prev_idx <= 5:
                        p_line = lines[prev_idx].strip()
                        if p_line:
                            # Search for typical extensions
                            m = re.search(r"([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)", p_line)
                            if m:
                                found_name = m.group(1).split("/")[-1]
                                break
                            # Or if it's bold/header
                            if p_line.startswith("#") or p_line.startswith("**"):
                                found_name = p_line.strip("#* :`").split("/")[-1]
                                break
                        prev_idx -= 1
                        
                block_name = found_name if found_name else f"block_{len(blocks)}.{lang}"
                block_lines = []
            elif line.startswith("```") and in_block:
                in_block = False
                blocks[block_name] = "\n".join(block_lines)
            elif in_block:
                block_lines.append(line)
            i += 1
            
        if in_block and block_lines:
            blocks[block_name] = "\n".join(block_lines)
            
        return blocks
