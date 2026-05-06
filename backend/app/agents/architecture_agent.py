"""Architecture Agent — System design specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert software architect.
Generate production-quality system designs with:
- Clean architecture patterns
- Microservice boundaries
- API contract definitions
- Scalability considerations
- Security architecture
Return designs with diagrams and code in labeled blocks."""


class ArchitectureAgent(BaseAgent):
    name = "architecture"
    role = "System Architect"
    agent_type = AgentType.ARCHITECTURE
    expertise = ["System Design", "Clean Architecture", "Microservices", "API Design", "DDD"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.OPENROUTER]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        prompt = f"Task: {task.title}\n\nDescription: {task.description}\n\nGenerate the system architecture."
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        return self._build_result(task, True, response.content, reasoning="Generated architecture", execution_time_ms=elapsed)
