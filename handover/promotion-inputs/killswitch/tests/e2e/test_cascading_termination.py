"""E2E tests for cascading termination."""

from __future__ import annotations

import pytest

from agent_killswitch import KillLevel, KillSwitch
from agent_killswitch.core.cascading import CascadingTerminator


class TestCascadingTermination:
    """E2E tests for cascade kill through agent hierarchy."""

    @pytest.mark.e2e
    def test_deep_hierarchy_cascade(self) -> None:
        """Cascade through a deep hierarchy: root -> level1 -> level2 -> level3."""
        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks)

        # Build 4-level hierarchy
        ks.register_agent("root")
        ks.register_agent("l1-a", parent_id="root")
        ks.register_agent("l1-b", parent_id="root")
        ks.register_agent("l2-a", parent_id="l1-a")
        ks.register_agent("l2-b", parent_id="l1-a")
        ks.register_agent("l3-a", parent_id="l2-a")

        # Kill root
        killed = cascade.cascade_kill("root", KillLevel.KILL, reason="deep test")

        # All agents should be killed
        expected = {"root", "l1-a", "l1-b", "l2-a", "l2-b", "l3-a"}
        assert set(killed) == expected

        # Verify all are actually killed in the backend
        for agent_id in expected:
            status = ks.check(scope_target=agent_id)
            assert status.is_killed, f"{agent_id} should be killed"

    @pytest.mark.e2e
    def test_cascade_only_affects_descendants(self) -> None:
        """Cascade from a subtree root should not affect siblings."""
        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks)

        ks.register_agent("root")
        ks.register_agent("branch-a", parent_id="root")
        ks.register_agent("branch-b", parent_id="root")
        ks.register_agent("leaf-a1", parent_id="branch-a")
        ks.register_agent("leaf-b1", parent_id="branch-b")

        # Kill only branch-a
        killed = cascade.cascade_kill("branch-a", KillLevel.KILL, reason="subtree kill")

        assert "branch-a" in killed
        assert "leaf-a1" in killed
        assert "root" not in killed
        assert "branch-b" not in killed
        assert "leaf-b1" not in killed

        # Verify branch-b is still safe
        assert not ks.check(scope_target="branch-b").is_killed
        assert not ks.check(scope_target="leaf-b1").is_killed

    @pytest.mark.e2e
    def test_orphan_detection_and_cleanup(self) -> None:
        """Orphans are detected and cleaned up after parent removal."""
        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks)

        ks.register_agent("parent")
        ks.register_agent("child-1", parent_id="parent")
        ks.register_agent("child-2", parent_id="parent")

        # Remove parent without cascade
        ks.unregister_agent("parent")

        # Detect orphans
        orphans = cascade.detect_orphans()
        assert set(orphans) == {"child-1", "child-2"}

        # Clean up orphans
        killed = cascade.cleanup_orphans(level=KillLevel.STOP)
        assert set(killed) == {"child-1", "child-2"}

    @pytest.mark.e2e
    def test_cascade_with_delay(self) -> None:
        """Cascade with delay between levels."""
        import time

        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks, cascade_delay=0.01)

        ks.register_agent("root")
        ks.register_agent("child-1", parent_id="root")
        ks.register_agent("child-2", parent_id="root")

        start = time.monotonic()
        killed = cascade.cascade_kill("root", KillLevel.KILL)
        elapsed = time.monotonic() - start

        assert set(killed) == {"root", "child-1", "child-2"}
        # Should have taken at least cascade_delay * number_of_children
        assert elapsed >= 0.01
