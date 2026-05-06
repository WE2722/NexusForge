"""Project Memory — RAG-based project knowledge storage using Qdrant."""
from __future__ import annotations
import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)


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
                logger.warning("qdrant_not_configured")
        except Exception as exc:
            logger.warning("qdrant_init_failed", error=str(exc))

    async def store_project(self, project_id: str, content: str, metadata: dict | None = None) -> bool:
        if not self._client:
            return False
        try:
            from qdrant_client.models import PointStruct
            vector = self._simple_embed(content)
            point = PointStruct(
                id=hash(project_id) % (2**63),
                vector=vector,
                payload={"project_id": project_id, "content": content[:5000], **(metadata or {})},
            )
            self._client.upsert(collection_name=self._collection, points=[point])
            return True
        except Exception as exc:
            logger.error("qdrant_store_failed", error=str(exc))
            return False

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        if not self._client:
            return []
        try:
            vector = self._simple_embed(query)
            results = self._client.search(collection_name=self._collection, query_vector=vector, limit=limit)
            return [{"score": r.score, "payload": r.payload} for r in results]
        except Exception as exc:
            logger.error("qdrant_search_failed", error=str(exc))
            return []

    @staticmethod
    def _simple_embed(text: str) -> list[float]:
        """Simple hash-based embedding (384 dims). Replace with real embeddings in production."""
        import hashlib
        h = hashlib.sha384(text.encode()).digest()
        return [float(b) / 255.0 for b in h]
