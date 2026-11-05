"""Unit tests for CascadingTerminator."""

from __future__ import annotations

from agent_killswitch import KillLevel, KillSwitch
from agent_killswitch.core.cascading import CascadingTerminator


class TestCascadeKill:
    """Tests for cascading kill propagation."""

    def test_cascade_kills_root(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("root")
        killed = cascading.cascade_kill("root", KillLevel.KILL, reason="test")
        assert "root" in killed

    def test_cascade_kills_children(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("parent")
        killswitch.register_agent("child-1", parent_id="parent")
        killswitch.register_agent("child-2", parent_id="parent")
        killed = cascading.cascade_kill("parent", KillLevel.KILL, reason="runaway")
        assert "parent" in killed
        assert "child-1" in killed
        assert "child-2" in killed

    def test_cascade_kills_grandchildren(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("root")
        killswitch.register_agent("child", parent_id="root")
        killswitch.register_agent("grandchild", parent_id="child")
        killed = cascading.cascade_kill("root", KillLevel.KILL, reason="deep cascade")
        assert set(killed) == {"root", "child", "grandchild"}

    def test_cascade_uses_specified_level(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("parent")
        killswitch.register_agent("child", parent_id="parent")
        cascading.cascade_kill("parent", KillLevel.STOP, reason="stop")
        status = killswitch.check(scope_target="child")
        assert status.is_killed
        assert status.level == KillLevel.STOP

    def test_cascade_with_no_children(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("lone-agent")
        killed = cascading.cascade_kill("lone-agent", KillLevel.KILL)
        assert killed == ["lone-agent"]


class TestCascadeCallback:
    """Tests for cascade callbacks."""

    def test_on_cascade_callback(self, killswitch: KillSwitch) -> None:
        cascades: list[tuple[str, str, KillLevel]] = []
        cascade = CascadingTerminator(
            killswitch=killswitch,
            on_cascade=lambda p, c, level: cascades.append((p, c, level)),
        )
        killswitch.register_agent("parent")
        killswitch.register_agent("child", parent_id="parent")
        cascade.cascade_kill("parent", KillLevel.KILL)
        assert len(cascades) >= 1
        assert cascades[0][0] == "parent"
        assert cascades[0][1] == "child"


class TestOrphanDetection:
    """Tests for orphan agent detection."""

    def test_detect_orphans_none(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("root")
        killswitch.register_agent("child", parent_id="root")
        orphans = cascading.detect_orphans()
        assert len(orphans) == 0

    def test_detect_orphans_after_unregister(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("parent")
        killswitch.register_agent("child", parent_id="parent")
        killswitch.unregister_agent("parent")
        orphans = cascading.detect_orphans()
        assert "child" in orphans

    def test_cleanup_orphans(self, killswitch: KillSwitch, cascading: CascadingTerminator) -> None:
        killswitch.register_agent("parent")
        killswitch.register_agent("child", parent_id="parent")
        killswitch.unregister_agent("parent")
        killed = cascading.cleanup_orphans(level=KillLevel.STOP)
        assert "child" in killed
        status = killswitch.check(scope_target="child")
        assert status.is_killed


class TestHierarchy:
    """Tests for hierarchy inspection."""

    def test_get_hierarchy_empty(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        result = cascading.get_hierarchy()
        assert result.get("total_agents", 0) == 0

    def test_get_hierarchy_tree(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("root")
        killswitch.register_agent("c1", parent_id="root")
        killswitch.register_agent("c2", parent_id="root")
        result = cascading.get_hierarchy()
        assert result["total_agents"] == 3
        assert len(result["roots"]) == 1
        assert result["roots"][0]["agent_id"] == "root"
        assert len(result["roots"][0]["children"]) == 2

    def test_get_hierarchy_subtree(
        self, killswitch: KillSwitch, cascading: CascadingTerminator
    ) -> None:
        killswitch.register_agent("root")
        killswitch.register_agent("c1", parent_id="root")
        result = cascading.get_hierarchy(root_id="root")
        assert result["agent_id"] == "root"
        assert len(result["children"]) == 1
