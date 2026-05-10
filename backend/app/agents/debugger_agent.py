"""Debugger Agent — Error diagnosis and fixing specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert debugger and error analyst.
You receive code that failed to run, along with the error messages.

Your job is to:
1. Diagnose the ROOT CAUSE of the error
2. Generate CORRECTED code files that fix the issue
3. Explain what you changed and why

STRICT RULES:
- Output corrected files as labeled code blocks with the EXACT same filenames
- Fix ALL errors, not just the first one
- Do NOT change the overall architecture — only fix bugs
- If the error is a missing import, add it
- If the error is a wrong import path, fix the path
- If the error is a syntax error, fix the syntax
- Preserve all existing functionality

Example output format:
```python main.py
# Fixed: changed import from pydantic to pydantic_settings
from pydantic_settings import BaseSettings
...
```
"""


class DebuggerAgent(BaseAgent):
    name = "debugger"
    role = "Error Fixer"
    agent_type = AgentType.DEBUGGER
    expertise = ["Debugging", "Error Analysis", "Stack Traces", "Code Repair"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")
        errors = task.metadata.get("errors", "")
        failed_code = task.metadata.get("failed_code", "")

        prompt = f"""A task has failed and needs debugging.

Task: {task.title}
Description: {task.description}

ERRORS:
{errors if errors else 'No specific error messages provided.'}

CODE THAT FAILED:
{failed_code if failed_code else context if context else 'No code provided.'}

Diagnose the root cause and generate CORRECTED versions of the broken files.
Output each corrected file as a labeled code block with the exact same filename."""

        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Diagnosed and fixed errors",
            execution_time_ms=elapsed,
        )
