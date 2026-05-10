"""Architecture Agent — System design specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert software architect designing a web application.
Your output MUST include clearly labeled code blocks with filenames.

You must produce:
1. A concise architecture overview (folder structure, main components)
2. API endpoint definitions (method, path, request/response shapes)
3. Data model definitions

RULES:
- Backend uses Python 3.10+ with FastAPI and Pydantic V2.
- Frontend uses React 18 with TypeScript.
- For simple apps, use in-memory storage (Python dicts/lists). Do NOT add MongoDB/PostgreSQL unless explicitly requested.
- Keep the design minimal and practical — no over-engineering.
- Label every code block with its filename, e.g.:

```txt architecture_overview.md
# Architecture
...
```

```python api_contracts.py
# API endpoint definitions
...
```
"""


class ArchitectureAgent(BaseAgent):
    name = "architecture"
    role = "System Architect"
    agent_type = AgentType.ARCHITECTURE
    expertise = ["System Design", "Clean Architecture", "API Design"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.OPENROUTER]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")
        prompt = f"""Project: {task.title}

Description: {task.description}

{f'Additional context:{chr(10)}{context}' if context else ''}

Design a clean, minimal architecture for this project. Include API contracts and data models.
Keep it simple and practical."""
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=4096)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Generated system architecture",
            execution_time_ms=elapsed,
        )
