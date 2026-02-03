"""Unit tests for AsyncTTLCache."""

import asyncio
import time

import pytest

from src.repositories.catalog.cache import AsyncTTLCache, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_cache_entry_creation(self) -> None:
        """Test creating a cache entry."""
        expires_at = time.monotonic() + 60.0
        entry: CacheEntry[str] = CacheEntry(value="test_value", expires_at=expires_at)

        assert entry.value == "test_value"
        assert entry.expires_at == expires_at

    def test_cache_entry_immutable(self) -> None:
        """Test that cache entry is immutable."""
        entry: CacheEntry[str] = CacheEntry(value="test", expires_at=100.0)

        with pytest.raises(AttributeError):
            entry.value = "modified"  # type: ignore[misc]


class TestAsyncTTLCache:
    """Tests for AsyncTTLCache."""

    @pytest.mark.asyncio
    async def test_get_or_load_caches_value(self) -> None:
        """Test that get_or_load caches and returns value."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)
        load_count = 0

        async def loader() -> str:
            nonlocal load_count
            load_count += 1
            return "loaded_value"

        # First call should invoke loader
        result1 = await cache.get_or_load("key1", loader)
        # Second call should return cached value
        result2 = await cache.get_or_load("key1", loader)

        assert result1 == "loaded_value"
        assert result2 == "loaded_value"
        assert load_count == 1  # Loader should be called only once

    @pytest.mark.asyncio
    async def test_ttl_expiration(self) -> None:
        """Test that cache entries expire after TTL."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=0.1)
        load_count = 0

        async def loader() -> str:
            nonlocal load_count
            load_count += 1
            return f"value_{load_count}"

        # First load
        result1 = await cache.get_or_load("key1", loader)
        assert result1 == "value_1"
        assert load_count == 1

        # Wait for TTL to expire
        await asyncio.sleep(0.15)

        # Should reload after expiration
        result2 = await cache.get_or_load("key1", loader)
        assert result2 == "value_2"
        assert load_count == 2

    @pytest.mark.asyncio
    async def test_thundering_herd_prevention(self) -> None:
        """Test that concurrent requests don't cause multiple loads."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)
        load_count = 0
        load_started = asyncio.Event()
        can_finish_load = asyncio.Event()

        async def slow_loader() -> str:
            nonlocal load_count
            load_count += 1
            load_started.set()
            await can_finish_load.wait()
            return "loaded_value"

        # Start multiple concurrent requests
        tasks = [
            asyncio.create_task(cache.get_or_load("key1", slow_loader))
            for _ in range(5)
        ]

        # Wait for loader to start
        await asyncio.wait_for(load_started.wait(), timeout=1.0)

        # Allow loader to finish
        can_finish_load.set()

        # Wait for all tasks
        results = await asyncio.gather(*tasks)

        # All should get the same value
        assert all(r == "loaded_value" for r in results)
        # Loader should be called only once
        assert load_count == 1

    @pytest.mark.asyncio
    async def test_different_keys_load_independently(self) -> None:
        """Test that different keys load independently."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)

        async def loader_a() -> str:
            return "value_a"

        async def loader_b() -> str:
            return "value_b"

        result_a = await cache.get_or_load("key_a", loader_a)
        result_b = await cache.get_or_load("key_b", loader_b)

        assert result_a == "value_a"
        assert result_b == "value_b"

    @pytest.mark.asyncio
    async def test_invalidate(self) -> None:
        """Test that invalidate removes cached value."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)
        load_count = 0

        async def loader() -> str:
            nonlocal load_count
            load_count += 1
            return f"value_{load_count}"

        # First load
        result1 = await cache.get_or_load("key1", loader)
        assert result1 == "value_1"
        assert load_count == 1

        # Invalidate
        removed = cache.invalidate("key1")
        assert removed is True

        # Should reload after invalidation
        result2 = await cache.get_or_load("key1", loader)
        assert result2 == "value_2"
        assert load_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_key(self) -> None:
        """Test that invalidating nonexistent key returns False."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)

        removed = cache.invalidate("nonexistent")

        assert removed is False

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """Test that clear removes all entries."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)

        async def loader(key: str) -> str:
            return f"value_{key}"

        await cache.get_or_load("key1", lambda: loader("1"))
        await cache.get_or_load("key2", lambda: loader("2"))

        assert cache.size() == 2

        cache.clear()

        assert cache.size() == 0

    @pytest.mark.asyncio
    async def test_size(self) -> None:
        """Test that size returns correct count."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)

        assert cache.size() == 0

        async def loader(key: str) -> str:
            return f"value_{key}"

        await cache.get_or_load("key1", lambda: loader("1"))
        assert cache.size() == 1

        await cache.get_or_load("key2", lambda: loader("2"))
        assert cache.size() == 2

    @pytest.mark.asyncio
    async def test_generic_types(self) -> None:
        """Test that cache works with different types."""
        int_cache: AsyncTTLCache[int] = AsyncTTLCache(ttl_seconds=60.0)
        dict_cache: AsyncTTLCache[dict[str, int]] = AsyncTTLCache(ttl_seconds=60.0)

        async def int_loader() -> int:
            return 42

        async def dict_loader() -> dict[str, int]:
            return {"count": 100}

        int_result = await int_cache.get_or_load("num", int_loader)
        dict_result = await dict_cache.get_or_load("data", dict_loader)

        assert int_result == 42
        assert dict_result == {"count": 100}

    @pytest.mark.asyncio
    async def test_loader_exception_not_cached(self) -> None:
        """Test that loader exceptions are not cached."""
        cache: AsyncTTLCache[str] = AsyncTTLCache(ttl_seconds=60.0)
        call_count = 0

        async def failing_loader() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return "success"

        # First call should raise
        with pytest.raises(ValueError, match="First call fails"):
            await cache.get_or_load("key1", failing_loader)

        # Second call should retry and succeed
        result = await cache.get_or_load("key1", failing_loader)

        assert result == "success"
        assert call_count == 2
