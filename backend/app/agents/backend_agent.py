"""Backend Agent — Python/FastAPI specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert Python and FastAPI backend developer.
Generate production-quality code with:
- Async endpoints with proper error handling
- Pydantic models for request/response validation
- Dependency injection patterns
- Structured logging and monitoring
- Security best practices
Return code in clearly labeled code blocks with filenames."""


class BackendAgent(BaseAgent):
    name = "backend"
    role = "Backend Developer"
    agent_type = AgentType.BACKEND
    expertise = ["Python 3.13", "FastAPI", "Pydantic", "SQLAlchemy", "MongoDB", "Redis"]
    preferred_providers = [LLMProvider.MISTRAL, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        prompt = f"Task: {task.title}\n\nDescription: {task.description}\n\nGenerate the complete backend code."
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Generated backend code", execution_time_ms=elapsed,
        )

    @staticmethod
    def _extract_code_blocks(content: str) -> dict[str, str]:
        blocks: dict[str, str] = {}
        lines = content.split("\n")
        i, block_name, block_lines = 0, "", []
        in_block = False
        while i < len(lines):
            line = lines[i]
            if line.startswith("```") and not in_block:
                in_block = True
                lang = line[3:].strip()
                if i > 0 and lines[i - 1].strip():
                    block_name = lines[i - 1].strip().strip(":").strip("`").split("/")[-1]
                else:
                    block_name = f"block_{len(blocks)}.{lang or 'txt'}"
                block_lines = []
            elif line.startswith("```") and in_block:
                in_block = False
                blocks[block_name] = "\n".join(block_lines)
            elif in_block:
                block_lines.append(line)
            i += 1
        return blocks
