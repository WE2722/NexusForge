"""Pattern Extractor — analyzes completed projects for reusable patterns."""
from __future__ import annotations

import structlog

from app.models.schemas import Project
from app.services.project_memory import ProjectMemory

logger = structlog.get_logger(__name__)

class PatternExtractor:
    """Extracts common architectural and code patterns from successful projects."""
    
    def __init__(self, memory: ProjectMemory | None = None) -> None:
        self.memory = memory or ProjectMemory()

    async def extract_patterns(self, project: Project) -> list[dict]:
        """Analyzes a project and extracts reusable patterns, storing them in Qdrant."""
        if project.status != "completed":
            return []
            
        patterns = []
        
        # Example naive extraction: if it has auth + db, it's a "Secure CRUD API" pattern
        tech_set = set(project.brief.tech_stack)
        features_set = set(project.brief.features)
        
        if "FastAPI" in tech_set and "React" in tech_set:
            patterns.append({
                "name": "FastAPI + React Monorepo",
                "description": "Standard setup for a React frontend talking to a FastAPI backend.",
                "tech_stack": ["FastAPI", "React"],
                "project_id": project.id
            })
            
        # Store embeddings for these patterns (mocked logic)
        for pattern in patterns:
            try:
                await self.memory.store_project(
                    project_id=f"pattern_{project.id}_{pattern['name']}",
                    content=pattern["description"],
                    metadata=pattern
                )
            except Exception as exc:
                logger.error("pattern_storage_failed", error=str(exc))
                
        return patterns
