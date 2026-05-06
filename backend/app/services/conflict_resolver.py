"""Conflict Resolver — Redis-based file locking and synchronization."""
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

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def lock_file(self, file_path: str, timeout: float = 10.0) -> AsyncGenerator[None, None]:
        """
        Acquire a lock for a specific file.
        Uses in-memory asyncio locks for now. Redis implementation would be used in multi-node setup.
        """
        if file_path not in self._locks:
            self._locks[file_path] = asyncio.Lock()
        
        lock = self._locks[file_path]
        
        try:
            # Wait for the lock with a timeout
            await asyncio.wait_for(lock.acquire(), timeout=timeout)
            logger.debug("lock_acquired", file=file_path)
            yield
        except asyncio.TimeoutError:
            logger.error("lock_timeout", file=file_path)
            raise RuntimeError(f"Could not acquire lock for {file_path} within {timeout}s")
        finally:
            if lock.locked():
                lock.release()
                logger.debug("lock_released", file=file_path)
