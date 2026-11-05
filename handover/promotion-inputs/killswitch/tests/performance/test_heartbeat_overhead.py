"""Performance tests for heartbeat monitoring overhead."""

from __future__ import annotations

import statistics
import time

import pytest

from agent_killswitch import HeartbeatMonitor


@pytest.mark.performance
class TestHeartbeatOverhead:
    """Performance tests for heartbeat operations."""

    def test_heartbeat_send_latency(self) -> None:
        """Sending a heartbeat should be sub-millisecond."""
        monitor = HeartbeatMonitor(interval_seconds=5.0)
        try:
            monitor.start("agent-1")
            latencies: list[float] = []

            for _ in range(1000):
                start = time.monotonic()
                monitor.heartbeat("agent-1")
                elapsed_ms = (time.monotonic() - start) * 1000
                latencies.append(elapsed_ms)

            p99 = sorted(latencies)[989]
            avg = statistics.mean(latencies)
            assert p99 < 5.0, f"P99 heartbeat latency {p99:.2f}ms exceeds 5ms"
            assert avg < 1.0, f"Avg heartbeat latency {avg:.4f}ms exceeds 1ms"
        finally:
            monitor.shutdown()

    def test_health_check_with_many_agents(self) -> None:
        """Health check should scale linearly with agent count."""
        monitor = HeartbeatMonitor(interval_seconds=5.0)
        try:
            # Register 500 agents
            for i in range(500):
                monitor.start(f"agent-{i}")

            latencies: list[float] = []
            for _ in range(50):
                start = time.monotonic()
                monitor.check_health()
                elapsed_ms = (time.monotonic() - start) * 1000
                latencies.append(elapsed_ms)

            p99 = sorted(latencies)[48]
            assert p99 < 100.0, f"P99 health check latency {p99:.2f}ms with 500 agents"
        finally:
            monitor.shutdown()

    def test_start_stop_overhead(self) -> None:
        """Starting and stopping monitoring should be fast."""
        monitor = HeartbeatMonitor(interval_seconds=5.0)
        try:
            latencies: list[float] = []

            for i in range(100):
                agent_id = f"agent-{i}"
                start = time.monotonic()
                monitor.start(agent_id)
                elapsed_ms = (time.monotonic() - start) * 1000
                latencies.append(elapsed_ms)
                monitor.stop(agent_id)

            p99 = sorted(latencies)[98]
            assert p99 < 5.0, f"P99 start latency {p99:.2f}ms exceeds 5ms"
        finally:
            monitor.shutdown()
