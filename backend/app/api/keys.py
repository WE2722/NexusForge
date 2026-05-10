"""
API Keys Router — Save, retrieve, and test LLM provider API keys.
"""
from __future__ import annotations

import os
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import structlog

logger = structlog.get_logger(__name__)

keys_router = APIRouter()

KEYS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "api_keys.json"))
os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)


class KeySaveRequest(BaseModel):
    provider: str
    keys: list[str]


class KeyTestRequest(BaseModel):
    provider: str
    key: str


def _load_keys() -> dict[str, list[str]]:
    """Load saved keys from disk."""
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_keys(data: dict[str, list[str]]) -> None:
    """Persist keys to disk."""
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _mask_key(key: str) -> str:
    """Mask API key for safe display: show first 4 and last 4 chars."""
    if len(key) <= 12:
        return key[:3] + "•" * max(0, len(key) - 6) + key[-3:]
    return key[:4] + "•" * (len(key) - 8) + key[-4:]


@keys_router.get("/keys")
async def get_keys():
    """Retrieve all saved keys (masked for security)."""
    all_keys = _load_keys()
    result = {}
    for provider, keys in all_keys.items():
        result[provider] = [
            {"masked": _mask_key(k), "active": True, "index": i}
            for i, k in enumerate(keys)
        ]
    return result


@keys_router.post("/keys")
async def save_keys(request: KeySaveRequest):
    """Save API keys for a provider."""
    all_keys = _load_keys()
    # Filter empty keys
    valid_keys = [k.strip() for k in request.keys if k.strip()]
    all_keys[request.provider] = valid_keys
    _save_keys(all_keys)

    # Also update the .env file so the backend uses them immediately
    _update_env_keys(request.provider, valid_keys)

    logger.info("keys_saved", provider=request.provider, count=len(valid_keys))
    return {"saved": True, "provider": request.provider, "count": len(valid_keys)}


@keys_router.post("/keys/test")
async def test_key(request: KeyTestRequest):
    """Test if an API key works by making a minimal LLM call."""
    provider = request.provider
    key = request.key.strip()

    if not key:
        return {"valid": False, "error": "Empty key"}

    try:
        from app.core.llm_router import LLMRouter
        from app.models.schemas import LLMRequest, LLMProvider

        provider_map = {
            "google": LLMProvider.GOOGLE,
            "groq": LLMProvider.GROQ,
            "mistral": LLMProvider.MISTRAL,
            "openrouter": LLMProvider.OPENROUTER,
        }

        llm_provider = provider_map.get(provider)
        if not llm_provider:
            return {"valid": False, "error": f"Unknown provider: {provider}"}

        # Create a temporary router with the test key
        router = LLMRouter()

        req = LLMRequest(
            provider=llm_provider,
            prompt="Say 'hello' in one word.",
            system_prompt="Respond with exactly one word.",
            temperature=0.0,
            max_tokens=10,
        )
        response = await router.generate(req)

        if response.success:
            return {"valid": True, "response": response.content[:50]}
        else:
            return {"valid": False, "error": response.error or "No response"}

    except Exception as exc:
        logger.warning("key_test_failed", provider=provider, error=str(exc))
        return {"valid": False, "error": str(exc)[:200]}


@keys_router.post("/keys/save-all")
async def save_all_keys(keys: dict[str, str]):
    """Save all provider keys at once (from Settings page)."""
    all_keys = _load_keys()
    for provider, key_value in keys.items():
        if key_value.strip():
            all_keys[provider] = [k.strip() for k in key_value.split(",") if k.strip()]
            _update_env_keys(provider, all_keys[provider])
        elif provider in all_keys:
            all_keys[provider] = []
    _save_keys(all_keys)
    return {"saved": True}


def _update_env_keys(provider: str, keys: list[str]) -> None:
    """Write keys to .env file so the application picks them up."""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    env_key_map = {
        "google": "GOOGLE_API_KEYS",
        "groq": "GROQ_API_KEYS",
        "mistral": "MISTRAL_API_KEYS",
        "openrouter": "OPENROUTER_API_KEYS",
    }

    env_var = env_key_map.get(provider)
    if not env_var:
        return

    keys_str = ",".join(keys)

    # Read existing .env
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(f"{env_var}="):
                    lines.append(f"{env_var}={keys_str}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"{env_var}={keys_str}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Also update env at runtime
    os.environ[env_var] = keys_str
