"""Frontend Agent — React/TypeScript specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert React 19 and TypeScript frontend developer.
Generate production-quality code with:
- Functional components with hooks
- TypeScript interfaces and types
- Responsive CSS with modern design patterns
- Error boundaries and loading states
- Accessibility best practices
Return code in clearly labeled code blocks with filenames."""


class FrontendAgent(BaseAgent):
    name = "frontend"
    role = "Frontend Developer"
    agent_type = AgentType.FRONTEND
    expertise = ["React 19", "TypeScript", "Tailwind CSS", "Vite", "Zustand", "React Router"]
    preferred_providers = [LLMProvider.GROQ, LLMProvider.GOOGLE]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        prompt = f"Task: {task.title}\n\nDescription: {task.description}\n\nGenerate the complete frontend code."
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        files = list(code_blocks.keys())
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=files, reasoning="Generated frontend components", execution_time_ms=elapsed,
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
