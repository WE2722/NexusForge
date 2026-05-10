"""Error Recovery — classifies errors and suggests or applies fixes with KB integration."""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class ErrorRecovery:
    """Classifies errors and attempts to provide recovery strategies, optionally querying a knowledge base."""

    def __init__(self, project_memory=None) -> None:
        self._memory = project_memory

    def classify_error(self, error_message: str) -> str:
        """Rule-based classification of common error types."""
        lower = error_message.lower()
        if "syntax" in lower or "indentation" in lower or "unexpected token" in lower:
            return "SyntaxError"
        elif "import" in lower or "module not found" in lower or "no module named" in lower:
            return "ImportError"
        elif "type" in lower or "validation" in lower or "pydantic" in lower:
            return "TypeError"
        elif "timeout" in lower or "connection" in lower or "econnrefused" in lower:
            return "NetworkError"
        elif "cors" in lower or "access-control" in lower:
            return "CORSError"
        elif "enoent" in lower or "file not found" in lower or "no such file" in lower:
            return "FileNotFoundError"
        elif "permission" in lower or "eacces" in lower or "forbidden" in lower:
            return "PermissionError"
        elif "memory" in lower or "heap" in lower or "oom" in lower:
            return "MemoryError"
        elif "json" in lower or "decode" in lower or "parse" in lower:
            return "ParseError"
        else:
            return "UnknownError"

    def get_recovery_strategy(self, error_category: str) -> str:
        """Suggests a recovery strategy based on the error category."""
        strategies = {
            "SyntaxError": "Review the code block for syntax issues, missing colons, brackets, or incorrect indentation.",
            "ImportError": "Ensure all required dependencies are in requirements.txt. Check for wrong import paths (use flat imports, not `from app.xxx`).",
            "TypeError": "Check Pydantic models and ensure data matches expected schema. Use `from pydantic_settings import BaseSettings` not `from pydantic`.",
            "NetworkError": "Implement retry logic with exponential backoff. Check if the target service is running and accessible.",
            "CORSError": "Add CORS middleware: `app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])`.",
            "FileNotFoundError": "Check that all referenced files exist. Ensure correct file paths and working directory.",
            "PermissionError": "Check file/directory permissions. On Windows, ensure the process has write access.",
            "MemoryError": "Reduce batch sizes, implement pagination, or increase available memory.",
            "ParseError": "Ensure the response is valid JSON. Strip markdown code fences before parsing.",
            "UnknownError": "Use the DebuggerAgent to analyze the stack trace and provide a fix.",
        }
        return strategies.get(error_category, strategies["UnknownError"])

    async def search_knowledge_base(self, error_message: str) -> list[dict]:
        """Search the project memory KB for similar past errors and their solutions."""
        if not self._memory:
            return []
        try:
            results = await self._memory.search_similar(f"error: {error_message}", limit=3)
            return results
        except Exception as exc:
            logger.warning("kb_search_failed", error=str(exc))
            return []

    async def get_full_recovery(self, error_message: str) -> dict:
        """Get classification, strategy, and KB matches for an error."""
        category = self.classify_error(error_message)
        strategy = self.get_recovery_strategy(category)
        kb_results = await self.search_knowledge_base(error_message)
        return {
            "category": category,
            "strategy": strategy,
            "kb_matches": kb_results,
        }
