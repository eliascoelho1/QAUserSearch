"""Cache utilities for catalog file repository."""

import asyncio
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CacheEntry(Generic[T]):
    """Immutable cache entry with value and expiration.

    Attributes:
        value: The cached data.
        expires_at: Monotonic timestamp when the entry expires.
    """

    value: T
    expires_at: float


class AsyncTTLCache(Generic[T]):
    """Thread-safe async cache with TTL and thundering herd prevention.

    This cache uses a dual-lock pattern:
    - threading.Lock for protecting the data structure (for thread safety)
    - asyncio.Lock per key for preventing thundering herd (for async safety)

    Attributes:
        _ttl: Time-to-live in seconds.
        _data: Dictionary storing cache entries.
        _data_lock: Threading lock for data structure access.
        _key_locks: Dictionary of per-key async locks.
        _key_locks_lock: Async lock for key locks dictionary access.
    """

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        """Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds.
        """
        self._ttl = ttl_seconds
        self._data: dict[str, CacheEntry[T]] = {}
        self._data_lock = threading.Lock()
        self._key_locks: dict[str, asyncio.Lock] = {}
        self._key_locks_lock: asyncio.Lock | None = None

    def _get_key_locks_lock(self) -> asyncio.Lock:
        """Get or create the key locks lock (lazy initialization for event loop).

        Returns:
            The asyncio lock for key locks dictionary.
        """
        if self._key_locks_lock is None:
            self._key_locks_lock = asyncio.Lock()
        return self._key_locks_lock

    def _get_if_valid(self, key: str) -> T | None:
        """Get cached value if it exists and is not expired.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found/expired.
        """
        with self._data_lock:
            entry = self._data.get(key)
            if entry is not None and time.monotonic() < entry.expires_at:
                return entry.value
            return None

    def _set(self, key: str, value: T) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to store.
        """
        expires_at = time.monotonic() + self._ttl
        with self._data_lock:
            self._data[key] = CacheEntry(value=value, expires_at=expires_at)

    async def _get_key_lock(self, key: str) -> asyncio.Lock:
        """Get or create a per-key lock.

        Args:
            key: The cache key.

        Returns:
            The asyncio lock for this key.
        """
        async with self._get_key_locks_lock():
            if key not in self._key_locks:
                self._key_locks[key] = asyncio.Lock()
            return self._key_locks[key]

    async def get_or_load(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
    ) -> T:
        """Get cached value or load it using the provided loader.

        This method prevents thundering herd by using per-key locks.
        Only one coroutine will load the value, others will wait.

        Args:
            key: The cache key.
            loader: Async callable that loads the value if not cached.

        Returns:
            The cached or newly loaded value.
        """
        # Fast path: check valid cache without lock
        cached = self._get_if_valid(key)
        if cached is not None:
            return cached

        # Slow path: acquire per-key lock to prevent thundering herd
        key_lock = await self._get_key_lock(key)
        async with key_lock:
            # Double-check after acquiring lock
            cached = self._get_if_valid(key)
            if cached is not None:
                return cached

            # Load and cache the value
            value = await loader()
            self._set(key, value)
            return value

    def invalidate(self, key: str) -> bool:
        """Remove a specific key from the cache.

        Args:
            key: The cache key to remove.

        Returns:
            True if the key was found and removed, False otherwise.
        """
        with self._data_lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._data_lock:
            self._data.clear()

    def size(self) -> int:
        """Get the number of entries in the cache.

        Returns:
            Number of cached entries (may include expired ones).
        """
        with self._data_lock:
            return len(self._data)
