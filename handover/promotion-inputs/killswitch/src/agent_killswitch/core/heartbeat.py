"""Heartbeat monitor for tracking agent health.

Provides a HeartbeatMonitor that tracks periodic heartbeats from agents
and detects when agents become unresponsive. Designed to work with the
KillSwitch for automatic agent termination on death detection.

Thread-safe: All state is protected by a reentrant lock.
No external dependencies: Uses only Python stdlib (threading, time).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone

from .enums import HeartbeatStatus
from .models import HeartbeatRecord

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """Monitor agent health via periodic heartbeats.

    Agents send periodic heartbeats to indicate they are alive.
    The monitor tracks heartbeats and detects dead agents based
    on a configurable miss threshold.

    Example::

        from agent_killswitch import HeartbeatMonitor

        monitor = HeartbeatMonitor(
            interval_seconds=5.0,
            miss_threshold=3,
            on_dead=lambda agent_id: print(f"DEAD: {agent_id}"),
        )

        # Start monitoring
        monitor.start("agent-1")

        # Agent sends heartbeats periodically
        monitor.heartbeat("agent-1")

        # Check health
        health = monitor.check_health()
        for agent_id, status in health.items():
            print(f"{agent_id}: {status}")

        # Stop monitoring
        monitor.stop("agent-1")

    Args:
        interval_seconds: Expected heartbeat interval. Default 5.0s.
        miss_threshold: Number of missed intervals before DEAD. Default 3.
        on_dead: Callback when an agent is detected as dead.
            Signature: (agent_id: str) -> None
        on_suspect: Callback when an agent becomes suspect (missed 1+).
            Signature: (agent_id: str, miss_count: int) -> None
        auto_check_interval: If > 0, starts a background thread that
            checks health periodically. Default 0 (disabled).
    """

    def __init__(
        self,
        interval_seconds: float = 5.0,
        miss_threshold: int = 3,
        on_dead: Callable[[str], None] | None = None,
        on_suspect: Callable[[str, int], None] | None = None,
        auto_check_interval: float = 0.0,
    ) -> None:
        self._interval = interval_seconds
        self._miss_threshold = miss_threshold
        self._on_dead = on_dead
        self._on_suspect = on_suspect
        self._lock = threading.RLock()

        # Agent heartbeat records
        self._records: dict[str, HeartbeatRecord] = {}

        # Track which agents have already been reported as dead
        # (to avoid repeated callbacks)
        self._dead_reported: set[str] = set()

        # Background checker
        self._checker_thread: threading.Thread | None = None
        self._checker_stop = threading.Event()
        self._auto_check_interval = auto_check_interval

        if auto_check_interval > 0:
            self._start_checker()

    def _start_checker(self) -> None:
        """Start the background health check thread."""
        self._checker_stop.clear()
        self._checker_thread = threading.Thread(
            target=self._checker_loop,
            daemon=True,
            name="killswitch-heartbeat-checker",
        )
        self._checker_thread.start()

    def _checker_loop(self) -> None:
        """Background loop that checks health periodically."""
        while not self._checker_stop.is_set():
            try:
                self.check_health()
            except Exception as exc:
                logger.error(
                    "Heartbeat checker error",
                    extra={"error": str(exc)},
                )
            self._checker_stop.wait(self._auto_check_interval)

    def shutdown(self) -> None:
        """Stop the background checker and clean up."""
        self._checker_stop.set()
        if self._checker_thread is not None:
            self._checker_thread.join(timeout=5.0)
            self._checker_thread = None

    def start(
        self,
        agent_id: str,
        interval_seconds: float | None = None,
    ) -> None:
        """Start monitoring an agent.

        Records the initial heartbeat and begins tracking.

        Args:
            agent_id: Unique identifier of the agent to monitor.
            interval_seconds: Override the default interval for this agent.
        """
        now = datetime.now(timezone.utc)
        record = HeartbeatRecord(
            agent_id=agent_id,
            last_heartbeat=now,
            status=HeartbeatStatus.ALIVE,
            miss_count=0,
            interval_seconds=interval_seconds or self._interval,
        )

        with self._lock:
            self._records[agent_id] = record
            self._dead_reported.discard(agent_id)

        logger.info(
            "heartbeat_monitoring_started",
            extra={
                "agent_id": agent_id,
                "interval_seconds": record.interval_seconds,
            },
        )

    def stop(self, agent_id: str) -> None:
        """Stop monitoring an agent.

        Args:
            agent_id: The agent to stop monitoring.
        """
        with self._lock:
            self._records.pop(agent_id, None)
            self._dead_reported.discard(agent_id)

        logger.info("heartbeat_monitoring_stopped", extra={"agent_id": agent_id})

    def heartbeat(self, agent_id: str) -> bool:
        """Record a heartbeat from an agent.

        Resets the miss count and marks the agent as ALIVE.

        Args:
            agent_id: The agent sending the heartbeat.

        Returns:
            True if the heartbeat was recorded, False if agent not monitored.
        """
        with self._lock:
            record = self._records.get(agent_id)
            if record is None:
                return False

            record.last_heartbeat = datetime.now(timezone.utc)
            record.miss_count = 0
            record.status = HeartbeatStatus.ALIVE
            self._dead_reported.discard(agent_id)

        return True

    def check_health(self) -> dict[str, HeartbeatStatus]:
        """Check health of all monitored agents.

        Calculates how many intervals have been missed since the last
        heartbeat and updates the status accordingly.

        Returns:
            Dictionary of agent_id -> HeartbeatStatus.
        """
        time.monotonic()
        now_dt = datetime.now(timezone.utc)
        results: dict[str, HeartbeatStatus] = {}

        with self._lock:
            for agent_id, record in list(self._records.items()):
                if record.last_heartbeat is None:
                    record.status = HeartbeatStatus.UNKNOWN
                    results[agent_id] = HeartbeatStatus.UNKNOWN
                    continue

                elapsed = (now_dt - record.last_heartbeat).total_seconds()
                missed = int(elapsed / record.interval_seconds)

                if missed <= 0:
                    record.miss_count = 0
                    record.status = HeartbeatStatus.ALIVE
                else:
                    record.miss_count = missed

                    if missed >= self._miss_threshold:
                        record.status = HeartbeatStatus.DEAD

                        # Fire dead callback (once per death event)
                        if agent_id not in self._dead_reported:
                            self._dead_reported.add(agent_id)
                            if self._on_dead is not None:
                                try:
                                    self._on_dead(agent_id)
                                except Exception as exc:
                                    logger.error(
                                        "on_dead callback error",
                                        extra={
                                            "agent_id": agent_id,
                                            "error": str(exc),
                                        },
                                    )
                    else:
                        record.status = HeartbeatStatus.SUSPECT

                        # Fire suspect callback
                        if self._on_suspect is not None:
                            try:
                                self._on_suspect(agent_id, missed)
                            except Exception as exc:
                                logger.error(
                                    "on_suspect callback error",
                                    extra={
                                        "agent_id": agent_id,
                                        "error": str(exc),
                                    },
                                )

                results[agent_id] = record.status

        return results

    def get_dead_agents(self) -> list[str]:
        """Return IDs of all agents currently detected as dead.

        Returns:
            List of dead agent IDs.
        """
        health = self.check_health()
        return [agent_id for agent_id, status in health.items() if status == HeartbeatStatus.DEAD]

    def get_record(self, agent_id: str) -> HeartbeatRecord | None:
        """Get the heartbeat record for an agent.

        Args:
            agent_id: The agent to look up.

        Returns:
            The HeartbeatRecord, or None if not monitored.
        """
        with self._lock:
            record = self._records.get(agent_id)
            if record is None:
                return None
            # Return a copy to prevent external mutation
            return HeartbeatRecord(
                agent_id=record.agent_id,
                last_heartbeat=record.last_heartbeat,
                status=record.status,
                miss_count=record.miss_count,
                interval_seconds=record.interval_seconds,
            )

    def get_all_records(self) -> dict[str, HeartbeatRecord]:
        """Get heartbeat records for all monitored agents.

        Returns:
            Dictionary of agent_id -> HeartbeatRecord (copies).
        """
        with self._lock:
            return {
                agent_id: HeartbeatRecord(
                    agent_id=rec.agent_id,
                    last_heartbeat=rec.last_heartbeat,
                    status=rec.status,
                    miss_count=rec.miss_count,
                    interval_seconds=rec.interval_seconds,
                )
                for agent_id, rec in self._records.items()
            }

    @property
    def monitored_count(self) -> int:
        """Number of agents currently being monitored."""
        with self._lock:
            return len(self._records)
