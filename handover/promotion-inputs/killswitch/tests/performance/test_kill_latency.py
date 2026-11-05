"""Performance tests for kill switch latency guarantees.

Verifies that kill operations complete within the guaranteed latency:
- PAUSE: <200ms
- STOP: <300ms
- KILL: <500ms
"""

from __future__ import annotations

import statistics
import time

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch


@pytest.mark.performance
class TestKillLatency:
    """Performance tests for kill activation latency."""

    def test_pause_latency_under_200ms(self) -> None:
        """PAUSE activation must complete in <200ms."""
        ks = KillSwitch()
        latencies: list[float] = []

        for _ in range(100):
            start = time.monotonic()
            ks.activate(KillLevel.PAUSE, KillScope.GLOBAL, reason="bench")
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)
            ks.deactivate(KillScope.GLOBAL)

        p99 = sorted(latencies)[98]
        assert p99 < 200.0, f"P99 PAUSE latency {p99:.2f}ms exceeds 200ms"

    def test_stop_latency_under_300ms(self) -> None:
        """STOP activation must complete in <300ms."""
        ks = KillSwitch()
        latencies: list[float] = []

        for _ in range(100):
            start = time.monotonic()
            ks.activate(KillLevel.STOP, KillScope.GLOBAL, reason="bench")
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)
            ks.deactivate(KillScope.GLOBAL)

        p99 = sorted(latencies)[98]
        assert p99 < 300.0, f"P99 STOP latency {p99:.2f}ms exceeds 300ms"

    def test_kill_latency_under_500ms(self) -> None:
        """KILL activation must complete in <500ms."""
        ks = KillSwitch()
        latencies: list[float] = []

        for _ in range(100):
            start = time.monotonic()
            ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="bench")
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)
            ks.deactivate(KillScope.GLOBAL)

        p99 = sorted(latencies)[98]
        assert p99 < 500.0, f"P99 KILL latency {p99:.2f}ms exceeds 500ms"

    def test_check_latency(self) -> None:
        """Check operation should be sub-millisecond for in-memory."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="bench")
        latencies: list[float] = []

        for _ in range(1000):
            start = time.monotonic()
            ks.check(scope_target="agent-1", crew_id="crew-1")
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)

        p99 = sorted(latencies)[989]
        avg = statistics.mean(latencies)
        assert p99 < 10.0, f"P99 check latency {p99:.2f}ms exceeds 10ms"
        assert avg < 1.0, f"Average check latency {avg:.4f}ms exceeds 1ms"

    def test_latency_with_many_agents(self) -> None:
        """Latency should not degrade significantly with many agents."""
        ks = KillSwitch()

        # Register many agents
        for i in range(1000):
            ks.register_agent(f"agent-{i}")

        # Activate a few kills
        for i in range(100):
            ks.activate(
                KillLevel.KILL,
                KillScope.AGENT,
                scope_target=f"agent-{i}",
            )

        # Check latency for a specific agent
        latencies: list[float] = []
        for _ in range(100):
            start = time.monotonic()
            ks.check(scope_target="agent-500")
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)

        p99 = sorted(latencies)[98]
        assert p99 < 50.0, f"P99 check latency {p99:.2f}ms with 1000 agents"
