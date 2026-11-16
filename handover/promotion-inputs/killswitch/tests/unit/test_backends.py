"""Unit tests for backends."""

from __future__ import annotations

from agent_killswitch.backends.base import KillSwitchBackend
from agent_killswitch.backends.memory import InMemoryBackend


class TestInMemoryBackend:
    """Tests for InMemoryBackend."""

    def test_get_missing_returns_none(self, backend: InMemoryBackend) -> None:
        assert backend.get("nonexistent") is None

    def test_set_and_get(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "value1")
        assert backend.get("key1") == "value1"

    def test_set_overwrites(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "old")
        backend.set("key1", "new")
        assert backend.get("key1") == "new"

    def test_delete(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "value1")
        backend.delete("key1")
        assert backend.get("key1") is None

    def test_delete_nonexistent_is_safe(self, backend: InMemoryBackend) -> None:
        backend.delete("nonexistent")  # Should not raise

    def test_get_many(self, backend: InMemoryBackend) -> None:
        backend.set("a", "1")
        backend.set("b", "2")
        backend.set("c", "3")
        result = backend.get_many(["a", "b", "missing", "c"])
        assert result == ["1", "2", None, "3"]

    def test_get_many_empty(self, backend: InMemoryBackend) -> None:
        assert backend.get_many([]) == []

    def test_keys_prefix_pattern(self, backend: InMemoryBackend) -> None:
        backend.set("killswitch:global", "kill")
        backend.set("killswitch:agent:a1", "pause")
        backend.set("killswitch:agent:a2", "stop")
        backend.set("other:key", "value")

        matched = backend.keys("killswitch:agent:*")
        assert sorted(matched) == ["killswitch:agent:a1", "killswitch:agent:a2"]

    def test_keys_exact_match(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "value1")
        matched = backend.keys("key1")
        assert matched == ["key1"]

    def test_keys_no_match(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "value1")
        matched = backend.keys("nonexistent")
        assert matched == []

    def test_exists_true(self, backend: InMemoryBackend) -> None:
        backend.set("key1", "value1")
        assert backend.exists("key1") is True

    def test_exists_false(self, backend: InMemoryBackend) -> None:
        assert backend.exists("nonexistent") is False

    def test_clear(self, backend: InMemoryBackend) -> None:
        backend.set("a", "1")
        backend.set("b", "2")
        backend.clear()
        assert len(backend) == 0
        assert backend.get("a") is None

    def test_len(self, backend: InMemoryBackend) -> None:
        assert len(backend) == 0
        backend.set("a", "1")
        backend.set("b", "2")
        assert len(backend) == 2

    def test_repr(self, backend: InMemoryBackend) -> None:
        assert "InMemoryBackend" in repr(backend)

    def test_implements_protocol(self) -> None:
        backend = InMemoryBackend()
        assert isinstance(backend, KillSwitchBackend)


class TestInMemoryBackendThreadSafety:
    """Thread safety tests for InMemoryBackend."""

    def test_concurrent_set_get(self, backend: InMemoryBackend) -> None:
        import threading

        errors: list[str] = []

        def writer(n: int) -> None:
            for i in range(100):
                backend.set(f"key-{n}-{i}", f"val-{n}-{i}")

        def reader(n: int) -> None:
            for i in range(100):
                val = backend.get(f"key-{n}-{i}")
                # Value is either None (not yet written) or correct
                if val is not None and val != f"val-{n}-{i}":
                    errors.append(f"Unexpected value: {val}")

        threads = []
        for n in range(5):
            threads.append(threading.Thread(target=writer, args=(n,)))
            threads.append(threading.Thread(target=reader, args=(n,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
