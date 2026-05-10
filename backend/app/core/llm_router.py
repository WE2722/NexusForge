"""
NexusForge LLM Router — multi-provider routing with circuit breaker, fallback & key rotation.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field

import httpx
import structlog

from app.core.config import settings
from app.core.token_budget import TokenBudgetManager
from app.models.schemas import LLMProvider, LLMRequest, LLMResponse, TokenUsage

logger = structlog.get_logger(__name__)

FALLBACK_CHAIN: list[LLMProvider] = [
    LLMProvider.GOOGLE,
    LLMProvider.GROQ,
    LLMProvider.MISTRAL,
    LLMProvider.OPENROUTER,
]

PROVIDER_MODELS: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: "gemini-2.0-flash",
    LLMProvider.GROQ: "llama-3.1-8b-instant",
    LLMProvider.MISTRAL: "mistral-small-latest",
    LLMProvider.OPENROUTER: "google/gemini-2.0-flash-exp:free",
}

CIRCUIT_BREAKER_THRESHOLD = 3
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes


@dataclass
class CircuitState:
    """Per-provider circuit breaker state."""
    failures: int = 0
    last_failure: float = 0.0
    is_open: bool = False
    opened_at: float = 0.0
    successes: int = 0
    total_calls: int = 0


@dataclass
class KeyRotator:
    """Manages rotating through multiple API keys for a provider."""
    keys: list[str] = field(default_factory=list)
    current_index: int = 0
    exhausted_keys: set[int] = field(default_factory=set)
    exhausted_until: dict[int, float] = field(default_factory=dict)

    @property
    def current_key(self) -> str:
        if not self.keys:
            return ""
        self._skip_exhausted()
        return self.keys[self.current_index] if self.current_index < len(self.keys) else ""

    def rotate(self) -> str | None:
        """Move to the next available key. Returns None if all keys are exhausted."""
        if not self.keys:
            return None
        start = self.current_index
        for _ in range(len(self.keys)):
            self.current_index = (self.current_index + 1) % len(self.keys)
            if self.current_index not in self.exhausted_keys:
                return self.keys[self.current_index]
            # Check if exhaustion has expired (60s cooldown)
            if self.current_index in self.exhausted_until:
                if time.time() > self.exhausted_until[self.current_index]:
                    self.exhausted_keys.discard(self.current_index)
                    del self.exhausted_until[self.current_index]
                    return self.keys[self.current_index]
        return None

    def mark_exhausted(self, cooldown: float = 60.0) -> None:
        """Mark the current key as temporarily exhausted (rate limited)."""
        self.exhausted_keys.add(self.current_index)
        self.exhausted_until[self.current_index] = time.time() + cooldown
        logger.warning("key_exhausted", index=self.current_index, cooldown=cooldown)

    def _skip_exhausted(self) -> None:
        """Auto-recover exhausted keys and skip still-exhausted ones."""
        now = time.time()
        # Recover expired exhaustions
        expired = [k for k, t in self.exhausted_until.items() if now > t]
        for k in expired:
            self.exhausted_keys.discard(k)
            del self.exhausted_until[k]

    @property
    def has_available_keys(self) -> bool:
        self._skip_exhausted()
        return len(self.exhausted_keys) < len(self.keys) if self.keys else False


class LLMRouter:
    """
    Routes LLM requests across providers with:
    - Automatic fallback (google → groq → mistral → openrouter)
    - Circuit breaker (3 failures → disable 5 min)
    - Multi-key rotation per provider
    - Token budget integration
    """

    def __init__(self, budget_manager: TokenBudgetManager | None = None) -> None:
        self.budget = budget_manager or TokenBudgetManager()
        self._circuits: dict[LLMProvider, CircuitState] = {
            p: CircuitState() for p in LLMProvider
        }
        self._key_rotators: dict[LLMProvider, KeyRotator] = {}
        self._init_key_rotators()
        self._client: httpx.AsyncClient | None = None

    def _init_key_rotators(self) -> None:
        """Initialize key rotators from settings."""
        for provider in LLMProvider:
            keys = settings.get_keys(provider.value)
            self._key_rotators[provider] = KeyRotator(keys=keys)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def get_current_key(self, provider: LLMProvider) -> str:
        """Get the current active key for a provider."""
        rotator = self._key_rotators.get(provider)
        return rotator.current_key if rotator else ""

    # ── Main Entry Point ───────────────────────────────────────────
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using the specified provider with automatic fallback and key rotation.
        """
        providers_to_try = self._build_provider_chain(request.provider)

        last_error = ""
        for provider in providers_to_try:
            if not self._is_available(provider):
                logger.info("provider_skipped", provider=provider.value, reason="circuit_open_or_no_budget")
                continue

            rotator = self._key_rotators.get(provider)
            if not rotator or not rotator.has_available_keys:
                logger.info("provider_skipped", provider=provider.value, reason="no_keys")
                continue

            # Try each available key for this provider
            keys_tried = 0
            max_key_attempts = len(rotator.keys) if rotator.keys else 1

            while keys_tried < max_key_attempts:
                current_key = rotator.current_key
                if not current_key:
                    break

                try:
                    request_copy = request.model_copy(update={
                        "provider": provider,
                        "model": PROVIDER_MODELS.get(provider, request.model),
                    })
                    response = await self._call_provider(request_copy, api_key=current_key)

                    # Track success
                    circuit = self._circuits[provider]
                    circuit.successes += 1
                    circuit.total_calls += 1
                    circuit.failures = 0

                    # Track token usage
                    self.budget.track_usage(provider, response.usage.total_tokens)

                    return response

                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 429:
                        # Rate limited — rotate key
                        logger.warning("rate_limited", provider=provider.value, key_index=rotator.current_index)
                        rotator.mark_exhausted(cooldown=60.0)
                        next_key = rotator.rotate()
                        if next_key is None:
                            last_error = f"All keys exhausted for {provider.value}"
                            self._record_failure(provider, last_error)
                            break
                        keys_tried += 1
                        continue
                    else:
                        last_error = str(exc)
                        self._record_failure(provider, last_error)
                        logger.error("provider_failed", provider=provider.value, error=last_error)
                        break

                except Exception as exc:
                    last_error = str(exc)
                    self._record_failure(provider, last_error)
                    logger.error("provider_failed", provider=provider.value, error=last_error)
                    break

        return LLMResponse(
            success=False,
            error=f"All providers failed. Last error: {last_error}",
        )

    # ── Provider Implementations ───────────────────────────────────
    async def _call_provider(self, request: LLMRequest, api_key: str = "") -> LLMResponse:
        dispatch = {
            LLMProvider.GOOGLE: self._call_google,
            LLMProvider.GROQ: self._call_groq,
            LLMProvider.MISTRAL: self._call_mistral,
            LLMProvider.OPENROUTER: self._call_openrouter,
        }
        handler = dispatch.get(request.provider)
        if not handler:
            raise ValueError(f"Unknown provider: {request.provider}")
        return await handler(request, api_key)

    async def _call_google(self, req: LLMRequest, api_key: str = "") -> LLMResponse:
        """Call Google Gemini API."""
        client = await self._get_client()
        key = api_key or settings.google_api_key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{req.model}:generateContent?key={key}"

        body: dict = {
            "contents": [{"parts": [{"text": req.prompt}]}],
            "generationConfig": {
                "maxOutputTokens": req.max_tokens,
                "temperature": req.temperature,
                "topP": req.top_p,
            },
        }
        if req.system_prompt:
            body["systemInstruction"] = {"parts": [{"text": req.system_prompt}]}

        start = time.perf_counter()
        resp = await client.post(url, json=body)
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        content = ""
        if "candidates" in data and data["candidates"]:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage_data = data.get("usageMetadata", {})
        usage = TokenUsage(
            provider=LLMProvider.GOOGLE,
            model=req.model,
            prompt_tokens=usage_data.get("promptTokenCount", 0),
            completion_tokens=usage_data.get("candidatesTokenCount", 0),
            total_tokens=usage_data.get("totalTokenCount", 0),
        )

        return LLMResponse(content=content, provider=LLMProvider.GOOGLE, model=req.model, usage=usage, latency_ms=latency)

    async def _call_groq(self, req: LLMRequest, api_key: str = "") -> LLMResponse:
        """Call Groq API (OpenAI-compatible)."""
        client = await self._get_client()
        key = api_key or settings.groq_api_key
        url = "https://api.groq.com/openai/v1/chat/completions"

        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.append({"role": "user", "content": req.prompt})

        body = {
            "model": req.model,
            "messages": messages,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "top_p": req.top_p,
        }

        start = time.perf_counter()
        resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {key}"})
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            provider=LLMProvider.GROQ,
            model=req.model,
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(content=content, provider=LLMProvider.GROQ, model=req.model, usage=usage, latency_ms=latency)

    async def _call_mistral(self, req: LLMRequest, api_key: str = "") -> LLMResponse:
        """Call Mistral API."""
        client = await self._get_client()
        key = api_key or settings.mistral_api_key
        url = "https://api.mistral.ai/v1/chat/completions"

        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.append({"role": "user", "content": req.prompt})

        body = {
            "model": req.model,
            "messages": messages,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "top_p": req.top_p,
        }

        start = time.perf_counter()
        resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {key}"})
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            provider=LLMProvider.MISTRAL,
            model=req.model,
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(content=content, provider=LLMProvider.MISTRAL, model=req.model, usage=usage, latency_ms=latency)

    async def _call_openrouter(self, req: LLMRequest, api_key: str = "") -> LLMResponse:
        """Call OpenRouter API (OpenAI-compatible)."""
        client = await self._get_client()
        key = api_key or settings.openrouter_api_key
        url = "https://openrouter.ai/api/v1/chat/completions"

        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.append({"role": "user", "content": req.prompt})

        body = {
            "model": req.model,
            "messages": messages,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "top_p": req.top_p,
        }

        start = time.perf_counter()
        resp = await client.post(
            url,
            json=body,
            headers={
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://nexusforge.dev",
                "X-Title": "NexusForge",
            },
        )
        latency = (time.perf_counter() - start) * 1000
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            provider=LLMProvider.OPENROUTER,
            model=req.model,
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return LLMResponse(content=content, provider=LLMProvider.OPENROUTER, model=req.model, usage=usage, latency_ms=latency)

    # ── Circuit Breaker ────────────────────────────────────────────
    def _is_available(self, provider: LLMProvider) -> bool:
        """Check if provider is available (circuit closed and has budget)."""
        circuit = self._circuits[provider]

        # Auto-recover after timeout
        if circuit.is_open:
            if time.time() - circuit.opened_at > CIRCUIT_BREAKER_TIMEOUT:
                circuit.is_open = False
                circuit.failures = 0
                logger.info("circuit_half_open", provider=provider.value)
            else:
                return False

        # Check API key is configured
        key_map = {
            LLMProvider.GOOGLE: settings.has_google,
            LLMProvider.GROQ: settings.has_groq,
            LLMProvider.MISTRAL: settings.has_mistral,
            LLMProvider.OPENROUTER: settings.has_openrouter,
        }
        if not key_map.get(provider, False):
            return False

        return self.budget.can_use(provider)

    def _record_failure(self, provider: LLMProvider, error: str) -> None:
        circuit = self._circuits[provider]
        circuit.failures += 1
        circuit.last_failure = time.time()
        circuit.total_calls += 1

        if circuit.failures >= CIRCUIT_BREAKER_THRESHOLD:
            circuit.is_open = True
            circuit.opened_at = time.time()
            logger.warning("circuit_opened", provider=provider.value, failures=circuit.failures)

    def _build_provider_chain(self, preferred: LLMProvider) -> list[LLMProvider]:
        """Build ordered provider list starting with preferred."""
        chain = [preferred]
        for p in FALLBACK_CHAIN:
            if p != preferred:
                chain.append(p)
        return chain

    def get_status(self) -> dict:
        """Return status of all providers."""
        status = {}
        for provider in LLMProvider:
            circuit = self._circuits[provider]
            rotator = self._key_rotators.get(provider)
            status[provider.value] = {
                "available": self._is_available(provider),
                "circuit_open": circuit.is_open,
                "failures": circuit.failures,
                "successes": circuit.successes,
                "total_calls": circuit.total_calls,
                "keys_configured": len(rotator.keys) if rotator else 0,
                "keys_exhausted": len(rotator.exhausted_keys) if rotator else 0,
            }
        return status
