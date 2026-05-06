"""Debugger Agent — Error diagnosis and fixing specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert debugger and error analyst.
Analyze errors, identify root causes, and generate fixes with:
- Clear error diagnosis
- Step-by-step fix instructions
- Corrected code blocks
- Prevention recommendations
Return fixes in clearly labeled code blocks."""


class DebuggerAgent(BaseAgent):
    name = "debugger"
    role = "Error Fixer"
    agent_type = AgentType.DEBUGGER
    expertise = ["Debugging", "Error Analysis", "Stack Traces", "Performance", "Memory Leaks"]
    preferred_providers = [LLMProvider.MISTRAL, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        prompt = f"Task: {task.title}\n\nDescription: {task.description}\n\nDiagnose and fix the issue."
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        return self._build_result(task, True, response.content, reasoning="Diagnosed and fixed errors", execution_time_ms=elapsed)
