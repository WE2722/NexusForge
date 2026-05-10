"""Backend Agent — Python/FastAPI specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert Python/FastAPI backend developer.
Generate COMPLETE, WORKING backend code that can run immediately.

STRICT FILE STRUCTURE RULES (you MUST follow these exactly):
1. ALL Python files go in the ROOT directory — NO subdirectories like app/, src/, core/, etc.
2. The entry point MUST be named `main.py` with `app = FastAPI()`.
3. You MUST generate a `requirements.txt` file.

STRICT CODE RULES:
1. Use `from pydantic_settings import BaseSettings` (NOT `from pydantic import BaseSettings`).
2. Use `from pydantic import BaseModel` for regular models.
3. For simple apps, store data in-memory using Python lists/dicts. Do NOT use databases unless explicitly requested.
4. Use proper async/await patterns.
5. Add CORS middleware: `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])`.
6. All API routes MUST be defined in `main.py` or imported from flat files (e.g., `from routes import router`).
7. Do NOT use `from app.xxx` imports — all imports must be relative to the root.

STRICT OUTPUT FORMAT:
Every file must be in a labeled code block with its filename:

```python main.py
from fastapi import FastAPI
...
```

```txt requirements.txt
fastapi
uvicorn
pydantic
pydantic-settings
```

Generate ALL files needed for a complete, working backend."""


class BackendAgent(BaseAgent):
    name = "backend"
    role = "Backend Developer"
    agent_type = AgentType.BACKEND
    expertise = ["Python 3.10+", "FastAPI", "Pydantic V2", "REST APIs"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")
        prompt = f"""Project: {task.title}

Description: {task.description}

{f'Architecture context (from architect agent):{chr(10)}{context}' if context else ''}

Generate the COMPLETE backend code. Remember:
- ALL files flat in root (no subdirectories)
- Entry point: main.py
- Include requirements.txt
- Use pydantic_settings for BaseSettings
- Add CORS middleware
- For simple apps, use in-memory storage"""
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Generated backend code",
            execution_time_ms=elapsed,
        )