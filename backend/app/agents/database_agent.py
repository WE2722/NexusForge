"""Database Agent — DB architecture specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert database architect.
Generate production-quality database designs with:
- Normalized schemas (3NF where appropriate)
- Proper indexes for query patterns
- Migration scripts
- MongoDB collection designs with validation
- Redis caching strategies
Return code in clearly labeled code blocks with filenames."""


class DatabaseAgent(BaseAgent):
    name = "database"
    role = "Database Architect"
    agent_type = AgentType.DATABASE
    expertise = ["MongoDB", "PostgreSQL", "Redis", "Schema Design", "Indexing"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.MISTRAL]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")
        prompt = f"""Project: {task.title}

Description: {task.description}

{f'Architecture context:{chr(10)}{context}' if context else ''}

Generate the database schema, models, and queries. Label every code block with its filename."""
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=4096)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Generated DB schema",
            execution_time_ms=elapsed,
        )
