"""
NexusForge Token Budget Manager — tracks and enforces LLM usage quotas.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.models.schemas import LLMProvider

logger = structlog.get_logger(__name__)


@dataclass
class ProviderQuota:
    """Rate-limit definition for a single provider."""
    tokens_per_minute: int = 0
    requests_per_minute: int = 0
    requests_per_day: int = 0
    tokens_per_month: int = 0


# Default quotas per provider (free-tier estimates)
DEFAULT_QUOTAS: dict[LLMProvider, ProviderQuota] = {
    LLMProvider.GOOGLE: ProviderQuota(tokens_per_minute=250_000, requests_per_minute=15),
    LLMProvider.GROQ: ProviderQuota(requests_per_day=1_000),
    LLMProvider.MISTRAL: ProviderQuota(requests_per_minute=60, tokens_per_month=1_000_000_000),
    LLMProvider.OPENROUTER: ProviderQuota(tokens_per_minute=100_000, requests_per_minute=60),
}

ALERT_THRESHOLDS = [0.50, 0.80, 0.95]


@dataclass
class UsageBucket:
    """Sliding-window usage counters."""
    tokens_used: int = 0
    requests_made: int = 0
    window_start: float = field(default_factory=time.time)
    daily_requests: int = 0
    daily_window_start: float = field(default_factory=time.time)
    monthly_tokens: int = 0
    monthly_window_start: float = field(default_factory=time.time)
    alerts_fired: set[float] = field(default_factory=set)


class TokenBudgetManager:
    """
    Centralized budget enforcement across all LLM providers.

    Maintains sliding-window counters and fires alerts at configurable
    thresholds (50 %, 80 %, 95 %).
    """

    def __init__(self, quotas: dict[LLMProvider, ProviderQuota] | None = None) -> None:
        self._quotas = quotas or dict(DEFAULT_QUOTAS)
        self._buckets: dict[LLMProvider, UsageBucket] = {
            p: UsageBucket() for p in LLMProvider
        }

    # ── Public API ─────────────────────────────────────────────────
    def track_usage(self, provider: LLMProvider, tokens: int, requests: int = 1) -> list[str]:
        """Record token and request usage; return any alerts triggered."""
        bucket = self._buckets[provider]
        now = time.time()

        # Reset minute window if expired
        if now - bucket.window_start > 60:
            bucket.tokens_used = 0
            bucket.requests_made = 0
            bucket.window_start = now
            bucket.alerts_fired.clear()

        # Reset daily window
        if now - bucket.daily_window_start > 86_400:
            bucket.daily_requests = 0
            bucket.daily_window_start = now

        # Reset monthly window
        if now - bucket.monthly_window_start > 2_592_000:
            bucket.monthly_tokens = 0
            bucket.monthly_window_start = now

        bucket.tokens_used += tokens
        bucket.requests_made += requests
        bucket.daily_requests += requests
        bucket.monthly_tokens += tokens

        return self._check_alerts(provider)

    def get_remaining(self, provider: LLMProvider) -> dict[str, int]:
        """Return remaining capacity for the provider."""
        quota = self._quotas.get(provider, ProviderQuota())
        bucket = self._buckets[provider]
        remaining: dict[str, int] = {}

        if quota.tokens_per_minute:
            remaining["tokens_per_minute"] = max(0, quota.tokens_per_minute - bucket.tokens_used)
        if quota.requests_per_minute:
            remaining["requests_per_minute"] = max(0, quota.requests_per_minute - bucket.requests_made)
        if quota.requests_per_day:
            remaining["requests_per_day"] = max(0, quota.requests_per_day - bucket.daily_requests)
        if quota.tokens_per_month:
            remaining["tokens_per_month"] = max(0, quota.tokens_per_month - bucket.monthly_tokens)

        return remaining

    def can_use(self, provider: LLMProvider, estimated_tokens: int = 0) -> bool:
        """Check whether the provider has remaining capacity."""
        quota = self._quotas.get(provider, ProviderQuota())
        bucket = self._buckets[provider]
        now = time.time()

        # Auto-reset stale minute windows before checking
        if now - bucket.window_start > 60:
            return True

        if quota.tokens_per_minute and (bucket.tokens_used + estimated_tokens) > quota.tokens_per_minute:
            return False
        if quota.requests_per_minute and bucket.requests_made >= quota.requests_per_minute:
            return False
        if quota.requests_per_day and bucket.daily_requests >= quota.requests_per_day:
            return False
        if quota.tokens_per_month and (bucket.monthly_tokens + estimated_tokens) > quota.tokens_per_month:
            return False

        return True

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate (≈ 4 chars per token for English text)."""
        return max(1, len(text) // 4)

    def get_budget_report(self) -> dict[str, Any]:
        """Return a full budget report across all providers."""
        report: dict[str, Any] = {}
        for provider in LLMProvider:
            quota = self._quotas.get(provider, ProviderQuota())
            bucket = self._buckets[provider]
            report[provider.value] = {
                "quota": {
                    "tokens_per_minute": quota.tokens_per_minute,
                    "requests_per_minute": quota.requests_per_minute,
                    "requests_per_day": quota.requests_per_day,
                    "tokens_per_month": quota.tokens_per_month,
                },
                "used": {
                    "tokens_minute": bucket.tokens_used,
                    "requests_minute": bucket.requests_made,
                    "requests_day": bucket.daily_requests,
                    "tokens_month": bucket.monthly_tokens,
                },
                "remaining": self.get_remaining(provider),
                "can_use": self.can_use(provider),
            }
        return report

    # ── Internals ──────────────────────────────────────────────────
    def _check_alerts(self, provider: LLMProvider) -> list[str]:
        """Fire alerts at 50 %, 80 %, 95 % utilisation."""
        alerts: list[str] = []
        quota = self._quotas.get(provider, ProviderQuota())
        bucket = self._buckets[provider]

        if quota.tokens_per_minute:
            usage_pct = bucket.tokens_used / quota.tokens_per_minute
            for threshold in ALERT_THRESHOLDS:
                if usage_pct >= threshold and threshold not in bucket.alerts_fired:
                    bucket.alerts_fired.add(threshold)
                    msg = f"[{provider.value}] Token usage at {usage_pct:.0%} of {quota.tokens_per_minute} TPM limit"
                    alerts.append(msg)
                    logger.warning("budget_alert", provider=provider.value, pct=usage_pct, threshold=threshold)

        if quota.requests_per_minute:
            usage_pct = bucket.requests_made / quota.requests_per_minute
            for threshold in ALERT_THRESHOLDS:
                if usage_pct >= threshold and threshold not in bucket.alerts_fired:
                    bucket.alerts_fired.add(threshold)
                    msg = f"[{provider.value}] Request rate at {usage_pct:.0%} of {quota.requests_per_minute} RPM limit"
                    alerts.append(msg)
                    logger.warning("budget_alert", provider=provider.value, pct=usage_pct, threshold=threshold)

        return alerts
