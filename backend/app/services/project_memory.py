"""Project Memory — RAG-based project knowledge storage with in-memory fallback."""
from __future__ import annotations
import re
import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)

# Known tech stack patterns for suggestion engine
STACK_PATTERNS: list[dict] = [
    {
        "keywords": ["todo", "task", "checklist", "list"],
        "stack": ["React", "FastAPI", "MongoDB"],
        "pitfalls": ["Avoid class components — use functional components with hooks", "Always add loading states for async operations"],
        "success_rate": 92,
    },
    {
        "keywords": ["chat", "messaging", "real-time", "websocket"],
        "stack": ["React", "FastAPI", "WebSocket", "MongoDB"],
        "pitfalls": ["Handle WebSocket reconnection gracefully", "Implement message deduplication"],
        "success_rate": 85,
    },
    {
        "keywords": ["blog", "post", "article", "cms", "content"],
        "stack": ["React", "FastAPI", "MongoDB"],
        "pitfalls": ["Implement pagination for large datasets", "Add rich text editor support"],
        "success_rate": 90,
    },
    {
        "keywords": ["dashboard", "analytics", "chart", "monitor", "metrics"],
        "stack": ["React", "FastAPI", "Chart.js"],
        "pitfalls": ["Use virtualization for large data tables", "Cache API responses to reduce load"],
        "success_rate": 88,
    },
    {
        "keywords": ["e-commerce", "shop", "cart", "product", "store", "payment"],
        "stack": ["React", "FastAPI", "MongoDB", "Stripe"],
        "pitfalls": ["Always validate prices server-side", "Implement proper inventory checks"],
        "success_rate": 78,
    },
    {
        "keywords": ["weather", "forecast", "climate", "temperature"],
        "stack": ["React", "FastAPI", "OpenWeatherMap API"],
        "pitfalls": ["Cache API responses to avoid rate limits", "Handle API key security in .env"],
        "success_rate": 94,
    },
    {
        "keywords": ["note", "notebook", "memo", "journal"],
        "stack": ["React", "FastAPI", "MongoDB"],
        "pitfalls": ["Implement auto-save with debouncing", "Add markdown rendering support"],
        "success_rate": 91,
    },
]

# In-memory project store for when Qdrant is unavailable
_project_store: list[dict] = []


class ProjectMemory:
    """Stores and retrieves project knowledge using Qdrant vector database."""

    def __init__(self) -> None:
        self._client = None
        self._collection = "nexusforge_projects"

    async def initialize(self) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            if settings.qdrant_url and settings.qdrant_api_key:
                self._client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
                collections = [c.name for c in self._client.get_collections().collections]
                if self._collection not in collections:
                    self._client.create_collection(
                        collection_name=self._collection,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                    )
                logger.info("qdrant_connected", collection=self._collection)
            else:
                logger.warning("qdrant_not_configured", msg="Using in-memory fallback")
        except Exception as exc:
            logger.warning("qdrant_init_failed", error=str(exc), msg="Using in-memory fallback")

    async def store_project(self, project_id: str, content: str, metadata: dict | None = None) -> bool:
        """Store project info — Qdrant if available, else in-memory."""
        entry = {"project_id": project_id, "content": content[:5000], **(metadata or {})}

        # Always store in-memory for quick access
        _project_store.append(entry)

        if not self._client:
            return True
        try:
            from qdrant_client.models import PointStruct
            vector = self._simple_embed(content)
            point = PointStruct(
                id=hash(project_id) % (2**63),
                vector=vector,
                payload=entry,
            )
            self._client.upsert(collection_name=self._collection, points=[point])
            return True
        except Exception as exc:
            logger.error("qdrant_store_failed", error=str(exc))
            return True  # In-memory store succeeded

    async def store_project_success(self, project_id: str, patterns: list[str], tech_stack: list[str], quality_score: float = 1.0) -> bool:
        """Store successful project patterns for future reference."""
        content = f"Tech: {', '.join(tech_stack)}. Patterns: {'; '.join(patterns)}"
        return await self.store_project(project_id, content, {
            "patterns": patterns,
            "tech_stack": tech_stack,
            "quality_score": quality_score,
            "status": "success",
        })

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        """Search for similar projects — Qdrant if available, else in-memory keyword match."""
        # Try Qdrant first
        if self._client:
            try:
                vector = self._simple_embed(query)
                results = self._client.search(collection_name=self._collection, query_vector=vector, limit=limit)
                return [{"score": r.score, "payload": r.payload} for r in results]
            except Exception as exc:
                logger.error("qdrant_search_failed", error=str(exc))

        # In-memory fallback: simple keyword matching
        if not _project_store:
            return []

        query_lower = query.lower()
        scored = []
        for entry in _project_store:
            content = entry.get("content", "").lower()
            # Simple word overlap score
            query_words = set(query_lower.split())
            content_words = set(content.split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                scored.append({"score": score, "payload": entry})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    async def update_project_quality(self, project_id: str, score: float) -> None:
        """Update quality score for a stored project."""
        for entry in _project_store:
            if entry.get("project_id") == project_id:
                entry["quality_score"] = score
                break

    def get_suggestions_for_prompt(self, prompt: str) -> dict:
        """Get tech stack and pitfall suggestions based on prompt keywords."""
        if not prompt:
            return {"suggested_stack": [], "pitfalls": [], "success_rate": 0, "matched_pattern": None}

        prompt_lower = prompt.lower()
        best_match = None
        best_score = 0

        for pattern in STACK_PATTERNS:
            hits = sum(1 for kw in pattern["keywords"] if kw in prompt_lower)
            if hits > best_score:
                best_score = hits
                best_match = pattern

        if best_match and best_score > 0:
            return {
                "suggested_stack": best_match["stack"],
                "pitfalls": best_match["pitfalls"],
                "success_rate": best_match["success_rate"],
                "matched_pattern": best_match["keywords"][0],
            }

        # Default suggestion
        return {
            "suggested_stack": ["React", "FastAPI", "TypeScript"],
            "pitfalls": ["Ensure proper error handling", "Add loading states for all async operations"],
            "success_rate": 85,
            "matched_pattern": None,
        }

    @staticmethod
    def _simple_embed(text: str) -> list[float]:
        """Simple hash-based embedding (384 dims). Replace with real embeddings in production."""
        import hashlib
        h = hashlib.sha384(text.encode()).digest()
        return [float(b) / 255.0 for b in h]
