"""Unit tests for the core KillSwitch class."""

from __future__ import annotations

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.backends.memory import InMemoryBackend


class TestKillSwitchActivation:
    """Tests for kill switch activation."""

    def test_activate_global_pause(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(KillLevel.PAUSE, KillScope.GLOBAL, reason="test pause")
        assert event.level == KillLevel.PAUSE
        assert event.scope == KillScope.GLOBAL
        assert event.reason == "test pause"
        assert event.latency_ms >= 0

    def test_activate_global_stop(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(KillLevel.STOP, KillScope.GLOBAL, reason="test stop")
        assert event.level == KillLevel.STOP

    def test_activate_global_kill(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(KillLevel.KILL, KillScope.GLOBAL, reason="test kill")
        assert event.level == KillLevel.KILL

    def test_activate_agent_scope_requires_target(self, killswitch: KillSwitch) -> None:
        with pytest.raises(ValueError, match="scope_target required"):
            killswitch.activate(KillLevel.PAUSE, KillScope.AGENT)

    def test_activate_agent_scope_with_target(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(
            KillLevel.STOP, KillScope.AGENT, scope_target="agent-1", reason="runaway"
        )
        assert event.scope == KillScope.AGENT
        assert event.scope_target == "agent-1"

    def test_activate_crew_scope(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(KillLevel.PAUSE, KillScope.CREW, scope_target="crew-alpha")
        assert event.scope == KillScope.CREW
        assert event.scope_target == "crew-alpha"

    def test_activate_task_scope(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(KillLevel.KILL, KillScope.TASK, scope_target="task-42")
        assert event.scope == KillScope.TASK

    def test_activate_records_event(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")
        events = killswitch.get_events()
        assert len(events) == 1
        assert events[0].level == KillLevel.KILL

    def test_activate_fires_callback(self) -> None:
        events_received: list = []
        ks = KillSwitch(on_kill=lambda e: events_received.append(e))
        ks.activate(KillLevel.STOP, KillScope.GLOBAL, reason="callback test")
        assert len(events_received) == 1
        assert events_received[0].level == KillLevel.STOP

    def test_activate_with_metadata(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(
            KillLevel.KILL,
            KillScope.GLOBAL,
            reason="meta",
            metadata={"source": "test"},
        )
        assert event.metadata["source"] == "test"

    def test_activate_with_activated_by(self, killswitch: KillSwitch) -> None:
        event = killswitch.activate(
            KillLevel.PAUSE,
            KillScope.GLOBAL,
            activated_by="operator-jane",
        )
        assert event.activated_by == "operator-jane"


class TestKillSwitchDeactivation:
    """Tests for kill switch deactivation."""

    def test_deactivate_global(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        killswitch.deactivate(KillScope.GLOBAL)
        status = killswitch.check()
        assert not status.is_killed

    def test_deactivate_agent(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.STOP, KillScope.AGENT, scope_target="a1")
        killswitch.deactivate(KillScope.AGENT, scope_target="a1")
        status = killswitch.check(scope_target="a1")
        assert not status.is_killed

    def test_deactivate_nonexistent_is_safe(self, killswitch: KillSwitch) -> None:
        # Should not raise
        killswitch.deactivate(KillScope.GLOBAL)


class TestKillSwitchCheck:
    """Tests for kill switch status checks."""

    def test_check_safe_by_default(self, killswitch: KillSwitch) -> None:
        status = killswitch.check()
        assert not status.is_killed
        assert status.level is None

    def test_check_detects_global_kill(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL, reason="global kill")
        status = killswitch.check()
        assert status.is_killed
        assert status.level == KillLevel.KILL
        assert status.reason == "global kill"

    def test_check_global_overrides_agent(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.PAUSE, KillScope.AGENT, scope_target="a1")
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        status = killswitch.check(scope_target="a1")
        # Global has higher priority
        assert status.is_killed
        assert status.scope == KillScope.GLOBAL
        assert status.level == KillLevel.KILL

    def test_check_crew_scope(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.STOP, KillScope.CREW, scope_target="crew-1")
        status = killswitch.check(crew_id="crew-1")
        assert status.is_killed
        assert status.scope == KillScope.CREW
        assert status.level == KillLevel.STOP

    def test_check_agent_scope(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.PAUSE, KillScope.AGENT, scope_target="a1")
        status = killswitch.check(scope_target="a1")
        assert status.is_killed
        assert status.scope == KillScope.AGENT

    def test_check_different_agent_not_affected(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.AGENT, scope_target="a1")
        status = killswitch.check(scope_target="a2")
        assert not status.is_killed

    def test_check_priority_order_global_crew_agent(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.PAUSE, KillScope.AGENT, scope_target="a1")
        killswitch.activate(KillLevel.STOP, KillScope.CREW, scope_target="c1")
        status = killswitch.check(scope_target="a1", crew_id="c1")
        # CREW has higher priority than AGENT
        assert status.scope == KillScope.CREW
        assert status.level == KillLevel.STOP

    def test_check_returns_reason(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL, reason="budget exceeded")
        status = killswitch.check()
        assert status.reason == "budget exceeded"

    def test_check_returns_activation_time(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        status = killswitch.check()
        assert status.activated_at is not None


class TestKillSwitchFailClosed:
    """Tests for fail-closed behavior."""

    def test_fail_closed_on_backend_error(self) -> None:
        class BrokenBackend:
            def get(self, key: str):
                raise ConnectionError("backend down")

            def set(self, key: str, value: str):
                raise ConnectionError("backend down")

            def delete(self, key: str):
                raise ConnectionError("backend down")

            def get_many(self, keys: list):
                raise ConnectionError("backend down")

            def keys(self, pattern: str):
                return []

            def exists(self, key: str):
                return False

            def clear(self):
                pass

        ks = KillSwitch(backend=BrokenBackend(), fail_closed=True)
        status = ks.check(scope_target="agent-1")
        assert status.is_killed
        assert status.level == KillLevel.KILL

    def test_fail_open_when_configured(self) -> None:
        class BrokenBackend:
            def get(self, key: str):
                raise ConnectionError("backend down")

            def set(self, key: str, value: str):
                raise ConnectionError("backend down")

            def delete(self, key: str):
                raise ConnectionError("backend down")

            def get_many(self, keys: list):
                raise ConnectionError("backend down")

            def keys(self, pattern: str):
                return []

            def exists(self, key: str):
                return False

            def clear(self):
                pass

        ks = KillSwitch(backend=BrokenBackend(), fail_closed=False)
        status = ks.check(scope_target="agent-1")
        assert not status.is_killed


class TestKillSwitchAgentRegistry:
    """Tests for agent registration."""

    def test_register_agent(self, killswitch: KillSwitch) -> None:
        reg = killswitch.register_agent("agent-1")
        assert reg.agent_id == "agent-1"
        assert reg.parent_id is None

    def test_register_agent_with_parent(self, killswitch: KillSwitch) -> None:
        killswitch.register_agent("parent")
        reg = killswitch.register_agent("child", parent_id="parent")
        assert reg.parent_id == "parent"

    def test_register_agent_with_unregistered_parent_fails(self, killswitch: KillSwitch) -> None:
        with pytest.raises(ValueError, match="Parent agent not registered"):
            killswitch.register_agent("child", parent_id="nonexistent")

    def test_unregister_agent(self, killswitch: KillSwitch) -> None:
        killswitch.register_agent("agent-1")
        killswitch.unregister_agent("agent-1")
        assert len(killswitch.get_children("agent-1")) == 0

    def test_get_children(self, killswitch: KillSwitch) -> None:
        killswitch.register_agent("parent")
        killswitch.register_agent("child-1", parent_id="parent")
        killswitch.register_agent("child-2", parent_id="parent")
        children = killswitch.get_children("parent")
        assert sorted(children) == ["child-1", "child-2"]

    def test_get_all_descendants(self, killswitch: KillSwitch) -> None:
        killswitch.register_agent("root")
        killswitch.register_agent("c1", parent_id="root")
        killswitch.register_agent("c2", parent_id="root")
        killswitch.register_agent("gc1", parent_id="c1")
        descendants = killswitch.get_all_descendants("root")
        assert set(descendants) == {"c1", "c2", "gc1"}


class TestKillSwitchStatus:
    """Tests for status reporting."""

    def test_get_status_empty(self, killswitch: KillSwitch) -> None:
        status = killswitch.get_status()
        assert status["total_active"] == 0
        assert status["global"] is None

    def test_get_status_with_active(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        status = killswitch.get_status()
        assert status["global"] == "kill"
        assert status["total_active"] >= 1

    def test_get_events(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.PAUSE, KillScope.GLOBAL, reason="one")
        killswitch.activate(KillLevel.STOP, KillScope.GLOBAL, reason="two")
        events = killswitch.get_events()
        assert len(events) == 2
        # Most recent first
        assert events[0].reason == "two"
        assert events[1].reason == "one"

    def test_get_event_count(self, killswitch: KillSwitch) -> None:
        killswitch.activate(KillLevel.PAUSE, KillScope.GLOBAL)
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        counts = killswitch.get_event_count()
        assert counts["pause"] == 1
        assert counts["kill"] == 2

    def test_is_active_property(self, killswitch: KillSwitch) -> None:
        assert not killswitch.is_active
        killswitch.activate(KillLevel.KILL, KillScope.GLOBAL)
        assert killswitch.is_active


class TestKillSwitchPrefix:
    """Tests for key prefix configuration."""

    def test_custom_prefix(self) -> None:
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend, prefix="myapp:")
        ks.activate(KillLevel.KILL, KillScope.GLOBAL)
        # The backend key should use the prefix
        assert backend.get("myapp:global") == "kill"

    def test_two_switches_different_prefixes(self) -> None:
        backend = InMemoryBackend()
        ks1 = KillSwitch(backend=backend, prefix="app1:")
        ks2 = KillSwitch(backend=backend, prefix="app2:")

        ks1.activate(KillLevel.KILL, KillScope.GLOBAL)
        assert ks1.check().is_killed
        assert not ks2.check().is_killed
