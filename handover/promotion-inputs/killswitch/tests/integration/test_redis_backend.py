"""Integration tests for Redis backend.

These tests require a Redis instance or use fakeredis for isolation.
"""

from __future__ import annotations

import pytest

try:
    import fakeredis

    HAS_FAKEREDIS = True
except ImportError:
    HAS_FAKEREDIS = False


if HAS_FAKEREDIS:
    from agent_killswitch.backends.redis import RedisBackend


@pytest.mark.integration
@pytest.mark.skipif(not HAS_FAKEREDIS, reason="fakeredis not installed")
class TestRedisBackend:
    """Tests for RedisBackend using fakeredis."""

    @pytest.fixture
    def redis_backend(self) -> RedisBackend:
        client = fakeredis.FakeRedis()
        return RedisBackend(client, prefix="test:")

    def test_set_and_get(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("key1", "value1")
        assert redis_backend.get("key1") == "value1"

    def test_get_missing(self, redis_backend: RedisBackend) -> None:
        assert redis_backend.get("missing") is None

    def test_delete(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("key1", "value1")
        redis_backend.delete("key1")
        assert redis_backend.get("key1") is None

    def test_get_many(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("a", "1")
        redis_backend.set("b", "2")
        result = redis_backend.get_many(["a", "b", "missing"])
        assert result == ["1", "2", None]

    def test_exists(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("key1", "value1")
        assert redis_backend.exists("key1") is True
        assert redis_backend.exists("missing") is False

    def test_keys_pattern(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("agent:a1", "kill")
        redis_backend.set("agent:a2", "pause")
        redis_backend.set("crew:c1", "stop")
        matched = redis_backend.keys("agent:*")
        assert sorted(matched) == ["agent:a1", "agent:a2"]

    def test_clear(self, redis_backend: RedisBackend) -> None:
        redis_backend.set("a", "1")
        redis_backend.set("b", "2")
        redis_backend.clear()
        assert redis_backend.get("a") is None
        assert redis_backend.get("b") is None

    def test_custom_prefix(self) -> None:
        client = fakeredis.FakeRedis()
        backend = RedisBackend(client, prefix="myapp:ks:")
        backend.set("global", "kill")
        # Verify the key has the prefix in Redis
        raw = client.get("myapp:ks:global")
        assert raw is not None
        assert raw.decode("utf-8") == "kill"

    def test_repr(self, redis_backend: RedisBackend) -> None:
        assert "RedisBackend" in repr(redis_backend)


@pytest.mark.integration
@pytest.mark.skipif(not HAS_FAKEREDIS, reason="fakeredis not installed")
class TestRedisBackendWithKillSwitch:
    """Test RedisBackend integrated with KillSwitch."""

    def test_full_flow(self) -> None:
        from agent_killswitch import KillLevel, KillScope, KillSwitch

        client = fakeredis.FakeRedis()
        backend = RedisBackend(client, prefix="ks:")
        ks = KillSwitch(backend=backend)

        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="test")
        status = ks.check()
        assert status.is_killed
        assert status.level == KillLevel.KILL

        ks.deactivate(KillScope.GLOBAL)
        status = ks.check()
        assert not status.is_killed
