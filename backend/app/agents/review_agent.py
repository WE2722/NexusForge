"""Review Agent — Code quality and best practices specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert code reviewer.
Review code for quality, security, and best practices:
- Code style and consistency
- Security vulnerabilities
- Performance issues
- Test coverage gaps
- Documentation quality
Return a structured review with severity ratings."""


class ReviewAgent(BaseAgent):
    name = "review"
    role = "Code Reviewer"
    agent_type = AgentType.REVIEW
    expertise = ["Code Review", "Security Audit", "Performance Analysis", "Best Practices", "Testing"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.MISTRAL]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        prompt = f"Task: {task.title}\n\nDescription: {task.description}\n\nReview the code quality."
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=4096)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        return self._build_result(task, True, response.content, reasoning="Completed code review", execution_time_ms=elapsed)
