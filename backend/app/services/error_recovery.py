"""Error Recovery — classifies errors and suggests or applies fixes."""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class ErrorRecovery:
    """Classifies errors and attempts to provide recovery strategies."""

    def classify_error(self, error_message: str) -> str:
        """Simple rule-based classification of common error types."""
        error_message = error_message.lower()
        if "syntax" in error_message or "indentation" in error_message:
            return "SyntaxError"
        elif "import" in error_message or "module not found" in error_message:
            return "ImportError"
        elif "type" in error_message or "validation" in error_message:
            return "TypeError"
        elif "timeout" in error_message or "connection" in error_message:
            return "NetworkError"
        else:
            return "UnknownError"

    def get_recovery_strategy(self, error_category: str) -> str:
        """Suggests a recovery strategy based on the error category."""
        strategies = {
            "SyntaxError": "Review the code block for syntax issues, missing colons, or incorrect indentation.",
            "ImportError": "Ensure all required dependencies are added to requirements.txt and installed.",
            "TypeError": "Check Pydantic models and ensure the data matches the expected schema.",
            "NetworkError": "Implement retry logic with exponential backoff.",
            "UnknownError": "Use the DebuggerAgent to analyze the stack trace and provide a fix.",
        }
        return strategies.get(error_category, strategies["UnknownError"])
