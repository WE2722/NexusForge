"""Conflict Resolver — file locking and synchronization with configurable timeout."""
from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator
from contextlib import asynccontextmanager

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ConflictResolver:
    """Provides distributed locking to prevent multiple agents from modifying the same file."""

    def __init__(self, default_timeout: float = 10.0) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock_owners: dict[str, str] = {}
        self._lock_times: dict[str, float] = {}
        self._default_timeout = default_timeout

    @asynccontextmanager
    async def lock_file(self, file_path: str, owner: str = "", timeout: float | None = None) -> AsyncGenerator[None, None]:
        """
        Acquire a lock for a specific file with configurable timeout.
        Uses in-memory asyncio locks.
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout

        if file_path not in self._locks:
            self._locks[file_path] = asyncio.Lock()

        lock = self._locks[file_path]

        try:
            await asyncio.wait_for(lock.acquire(), timeout=effective_timeout)
            self._lock_owners[file_path] = owner or "unknown"
            self._lock_times[file_path] = time.time()
            logger.debug("lock_acquired", file=file_path, owner=owner)
            yield
        except asyncio.TimeoutError:
            logger.error("lock_timeout", file=file_path, timeout=effective_timeout)
            raise RuntimeError(f"Could not acquire lock for {file_path} within {effective_timeout}s")
        finally:
            if lock.locked():
                lock.release()
                self._lock_owners.pop(file_path, None)
                self._lock_times.pop(file_path, None)
                logger.debug("lock_released", file=file_path)

    def get_lock_status(self) -> dict[str, dict]:
        """Return current lock status for all tracked files."""
        status = {}
        now = time.time()
        for file_path, lock in self._locks.items():
            status[file_path] = {
                "locked": lock.locked(),
                "owner": self._lock_owners.get(file_path, ""),
                "held_for_seconds": round(now - self._lock_times[file_path], 2) if file_path in self._lock_times else 0,
            }
        return status

    def force_release(self, file_path: str) -> bool:
        """Force-release a stuck lock (use with caution)."""
        lock = self._locks.get(file_path)
        if lock and lock.locked():
            lock.release()
            self._lock_owners.pop(file_path, None)
            self._lock_times.pop(file_path, None)
            logger.warning("lock_force_released", file=file_path)
            return True
        return False
