"""Intent Classifier — analyzes prompt to extract deep structural intent."""
from __future__ import annotations

import json
from pydantic import BaseModel, Field
import structlog

from app.core.llm_router import LLMRouter
from app.models.schemas import LLMProvider, LLMRequest

logger = structlog.get_logger(__name__)

class IntentClassification(BaseModel):
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    complexity: str
    tech_stack: list[str]

SYSTEM_PROMPT = """You are an AI intent classifier. Analyze the prompt and return JSON only:
{
  "intent": "core goal or architectural pattern",
  "confidence": 0.0 to 1.0,
  "complexity": "simple|moderate|complex|expert",
  "tech_stack": ["tech1", "tech2"]
}"""

class IntentClassifier:
    def __init__(self, router: LLMRouter | None = None) -> None:
        self.router = router or LLMRouter()

    async def classify(self, prompt: str) -> IntentClassification:
        request = LLMRequest(
            provider=LLMProvider.GOOGLE,
            model="gemini-2.0-flash",
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1024,
        )
        response = await self.router.generate(request)
        
        if not response.success or not response.content:
            return self._fallback(prompt)
            
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            data = json.loads(content.strip())
            return IntentClassification(**data)
        except Exception as exc:
            logger.warning("intent_classify_failed", error=str(exc))
            return self._fallback(prompt)
            
    def _fallback(self, prompt: str) -> IntentClassification:
        return IntentClassification(
            intent="Unknown",
            confidence=0.5,
            complexity="moderate",
            tech_stack=["Python", "React"]
        )
