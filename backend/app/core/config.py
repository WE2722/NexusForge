"""
NexusForge Configuration — Pydantic Settings loading from .env
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM Provider API Keys ──────────────────────────────────────
    # Single-key (backward compatible)
    google_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""
    openrouter_api_key: str = ""

    # Multi-key (comma-separated in .env, e.g. GOOGLE_API_KEYS=key1,key2,key3)
    google_api_keys: str = ""
    groq_api_keys: str = ""
    mistral_api_keys: str = ""
    openrouter_api_keys: str = ""

    # ── Database ───────────────────────────────────────────────────
    mongodb_uri: str = "mongodb://localhost:27017"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # ── Cache (Upstash Redis) ──────────────────────────────────────
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # ── Auth (Clerk) ───────────────────────────────────────────────
    clerk_publishable_key: str = ""
    clerk_secret_key: str = ""

    # ── Application ────────────────────────────────────────────────
    debug: bool = False
    log_level: str = "INFO"
    default_llm_provider: str = "google"
    max_tokens_per_project: int = 50_000

    # ── Derived helpers ────────────────────────────────────────────
    @property
    def has_google(self) -> bool:
        return bool(self.google_api_key) or bool(self.google_api_keys)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key) or bool(self.groq_api_keys)

    @property
    def has_mistral(self) -> bool:
        return bool(self.mistral_api_key) or bool(self.mistral_api_keys)

    @property
    def has_openrouter(self) -> bool:
        return bool(self.openrouter_api_key) or bool(self.openrouter_api_keys)

    def get_keys(self, provider: str) -> list[str]:
        """Return all available keys for a provider as a list."""
        single_map = {
            "google": self.google_api_key,
            "groq": self.groq_api_key,
            "mistral": self.mistral_api_key,
            "openrouter": self.openrouter_api_key,
        }
        multi_map = {
            "google": self.google_api_keys,
            "groq": self.groq_api_keys,
            "mistral": self.mistral_api_keys,
            "openrouter": self.openrouter_api_keys,
        }
        keys: list[str] = []
        # Multi-key takes priority
        multi = multi_map.get(provider, "")
        if multi:
            keys.extend(k.strip() for k in multi.split(",") if k.strip())
        # Fall back to single key
        single = single_map.get(provider, "")
        if single and single not in keys:
            keys.append(single)
        return keys


settings = Settings()
