"""
NexusForge Prompt Refiner — transforms raw user prompts into structured ProjectBriefs.
"""
from __future__ import annotations

import json
import structlog

from app.core.llm_router import LLMRouter
from app.models.schemas import ComplexityLevel, LLMProvider, LLMRequest, ProjectBrief

logger = structlog.get_logger(__name__)

REFINE_SYSTEM_PROMPT = """You are a senior software architect analyzing a project request.
Extract structured information and respond ONLY with valid JSON (no markdown, no code fences).

Required JSON format:
{
  "title": "short project title (max 6 words)",
  "description": "detailed description of what to build (2-3 sentences)",
  "intent": "the user's core goal in one sentence",
  "features": ["feature1", "feature2", "feature3"],
  "tech_stack": ["tech1", "tech2"],
  "constraints": ["constraint1"],
  "complexity": "simple|moderate|complex|expert",
  "estimated_tasks": 5
}

CLASSIFICATION RULES:
- "simple" = single-page app, 1-3 features, no database required (e.g., todo list, calculator, counter)
- "moderate" = multi-page app, 3-6 features, may need a database (e.g., blog, dashboard)
- "complex" = full-stack with auth, multiple services, database required (e.g., e-commerce, social network)
- "expert" = distributed systems, real-time features, multiple databases (e.g., trading platform)

TECH STACK DEFAULTS:
- Always include "Python", "FastAPI" for backend
- Always include "React", "TypeScript" for frontend
- Only add "MongoDB" if database is explicitly requested or complexity >= complex
- Only add "Redis" if caching is explicitly requested

EXAMPLES:
User: "build me a todo app"
→ {"title": "Todo Application", "description": "A simple task management application with add, complete, and delete functionality. Clean dark-themed UI.", "intent": "Manage daily tasks", "features": ["Add tasks", "Mark complete", "Delete tasks", "Filter by status"], "tech_stack": ["Python", "FastAPI", "React", "TypeScript"], "constraints": [], "complexity": "simple", "estimated_tasks": 4}

User: "weather dashboard with API integration"
→ {"title": "Weather Dashboard", "description": "A weather dashboard that fetches real-time weather data from an API and displays forecasts with charts.", "intent": "View weather information visually", "features": ["Current weather display", "5-day forecast", "City search", "Temperature charts"], "tech_stack": ["Python", "FastAPI", "React", "TypeScript"], "constraints": ["Needs weather API key"], "complexity": "moderate", "estimated_tasks": 5}"""


class PromptRefiner:
    """Refines raw user prompts into structured ProjectBrief objects."""

    def __init__(self, router: LLMRouter | None = None) -> None:
        self.router = router or LLMRouter()

    async def refine(self, raw_prompt: str) -> ProjectBrief:
        request = LLMRequest(
            provider=LLMProvider.GOOGLE,
            model="gemini-2.0-flash",
            prompt=f"Analyze this project request and extract structured information:\n\n{raw_prompt}",
            system_prompt=REFINE_SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.3,
        )
        response = await self.router.generate(request)
        if not response.success or not response.content:
            logger.warning("refine_failed", error=response.error)
            return self._fallback_brief(raw_prompt)
        try:
            content = response.content.strip()
            # Strip markdown code fences if the LLM ignores instructions
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            # Also handle ```json prefix
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
            data = json.loads(content)
            complexity_raw = data.get("complexity", "moderate").lower()
            valid = [c.value for c in ComplexityLevel]
            complexity = ComplexityLevel(complexity_raw) if complexity_raw in valid else ComplexityLevel.MODERATE
            return ProjectBrief(
                title=data.get("title", "Untitled Project"),
                description=data.get("description", raw_prompt),
                intent=data.get("intent", ""),
                features=data.get("features", []),
                tech_stack=data.get("tech_stack", []),
                constraints=data.get("constraints", []),
                complexity=complexity,
                estimated_tasks=max(1, min(100, data.get("estimated_tasks", 5))),
                raw_prompt=raw_prompt,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("refine_parse_error", error=str(exc))
            return self._fallback_brief(raw_prompt)

    @staticmethod
    def _fallback_brief(raw_prompt: str) -> ProjectBrief:
        words = raw_prompt.split()
        title = " ".join(words[:6]).title() if words else "New Project"
        # Heuristic complexity detection
        lower = raw_prompt.lower()
        if any(kw in lower for kw in ["simple", "basic", "todo", "calculator", "counter"]):
            complexity = ComplexityLevel.SIMPLE
        elif any(kw in lower for kw in ["dashboard", "blog", "weather", "portfolio"]):
            complexity = ComplexityLevel.MODERATE
        elif any(kw in lower for kw in ["ecommerce", "e-commerce", "auth", "payment", "social"]):
            complexity = ComplexityLevel.COMPLEX
        else:
            complexity = ComplexityLevel.MODERATE
        return ProjectBrief(
            title=title, description=raw_prompt, intent="Build application as described",
            features=["Core functionality"], tech_stack=["Python", "FastAPI", "React", "TypeScript"],
            constraints=[], complexity=complexity, estimated_tasks=5, raw_prompt=raw_prompt,
        )
