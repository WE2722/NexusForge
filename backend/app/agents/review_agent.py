"""Review Agent — Code quality and best practices specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert code reviewer specializing in full-stack web applications.
You receive ALL generated code from a project and must review it for correctness.

Your job is to:
1. Check that frontend imports match actual file names
2. Check that frontend API calls match backend endpoints (correct URL paths, request/response shapes)
3. Check for missing imports, wrong import paths, syntax errors
4. Check that TypeScript interfaces are exported
5. Check for security issues (missing CORS, XSS, injection)
6. If you find issues, generate CORRECTED code files

STRICT RULES:
- If code is correct, say so and return no code blocks
- If code has issues, output corrected files as labeled code blocks with the EXACT same filenames
- Focus on bugs that would PREVENT the app from running (import errors, type mismatches, missing files)
- Do NOT refactor working code for style preferences

Example output for issues found:
```tsx App.tsx
// Fixed: corrected API endpoint from /api/todos to /todos
...
```
"""


class ReviewAgent(BaseAgent):
    name = "review"
    role = "Code Reviewer"
    agent_type = AgentType.REVIEW
    expertise = ["Code Review", "Security Audit", "Type Safety", "Integration Testing"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.MISTRAL]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")

        prompt = f"""Review the following generated code for a project.

Project: {task.title}
Description: {task.description}

ALL GENERATED CODE:
{context if context else 'No code provided for review.'}

Review checklist:
1. Do all frontend imports resolve to actual files?
2. Do frontend API calls match backend endpoints?
3. Are all TypeScript interfaces exported?
4. Are there any syntax errors or missing imports?
5. Does the backend have CORS middleware?
6. Is there an index.tsx entry point for the frontend?
7. Is there a main.py entry point for the backend?

If you find issues, generate corrected files. If everything looks good, say so."""

        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Completed code review",
            execution_time_ms=elapsed,
        )
