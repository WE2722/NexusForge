"""Smart Agent Selector — selects the best agent and provider based on history."""
from __future__ import annotations

import structlog

from app.models.schemas import AgentType, LLMProvider, Task
from app.core.token_budget import TokenBudgetManager

logger = structlog.get_logger(__name__)

class AgentSelector:
    """Selects the optimal agent and LLM provider for a task."""
    
    def __init__(self, budget_manager: TokenBudgetManager | None = None) -> None:
        self.budget = budget_manager or TokenBudgetManager()

    async def select_agent(self, task: Task, history: list[dict] | None = None) -> dict:
        """
        Determines the best agent and provider.
        In production, this would query MongoDB for historical success rates.
        """
        # Base mapping if history is not available
        agent_type = task.agent_type
        
        provider_map = {
            AgentType.FRONTEND: [LLMProvider.GROQ, LLMProvider.GOOGLE],
            AgentType.BACKEND: [LLMProvider.MISTRAL, LLMProvider.GROQ],
            AgentType.DATABASE: [LLMProvider.GOOGLE, LLMProvider.MISTRAL],
            AgentType.ARCHITECTURE: [LLMProvider.OPENROUTER, LLMProvider.GOOGLE],
            AgentType.DEBUGGER: [LLMProvider.GROQ, LLMProvider.MISTRAL],
            AgentType.REVIEW: [LLMProvider.GOOGLE, LLMProvider.OPENROUTER],
        }
        
        preferred_providers = provider_map.get(agent_type, [LLMProvider.GOOGLE])
        
        selected_provider = preferred_providers[0]
        for provider in preferred_providers:
            if self.budget.can_use(provider, estimated_tokens=1000):
                selected_provider = provider
                break
                
        confidence = 0.85 if not history else 0.95
        
        return {
            "agent": agent_type,
            "provider": selected_provider,
            "confidence": confidence
        }
