"""Template Engine — finds similar project templates."""
from __future__ import annotations

import structlog

from app.services.project_memory import ProjectMemory

logger = structlog.get_logger(__name__)

class TemplateEngine:
    """Searches for existing templates matching a query and autofills."""
    
    def __init__(self, memory: ProjectMemory | None = None) -> None:
        self.memory = memory or ProjectMemory()

    async def find_similar(self, query: str) -> list[dict]:
        """Find templates with similarity scores > 0.8."""
        try:
            results = await self.memory.search_similar(query, limit=3)
            templates = []
            for res in results:
                if res["score"] > 0.8:
                    templates.append(res["payload"])
            return templates
        except Exception as exc:
            logger.error("template_search_failed", error=str(exc))
            return []
            
    async def auto_fill(self, query: str) -> dict | None:
        """Returns a template directly if similarity is very high (> 0.95)."""
        templates = await self.find_similar(query)
        if templates and templates[0].get("score", 1.0) > 0.95:
            return templates[0]
        return None
