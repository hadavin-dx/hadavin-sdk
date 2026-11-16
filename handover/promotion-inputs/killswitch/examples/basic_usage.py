"""Basic usage example for agent-killswitch.

Demonstrates the core kill switch functionality:
- Activate at different levels (PAUSE/STOP/KILL)
- Check status
- Register agents
- Use scoped kills
"""

from __future__ import annotations

from agent_killswitch import KillLevel, KillScope, KillSwitch


def main() -> None:
    # Create a kill switch (uses in-memory backend by default)
    ks = KillSwitch()

    # Register some agents
    ks.register_agent("supervisor")
    ks.register_agent("researcher", parent_id="supervisor")
    ks.register_agent("coder", parent_id="supervisor")

    # Check that everything is safe
    status = ks.check(scope_target="researcher")
    print(f"Researcher status: killed={status.is_killed}")  # False

    # Activate PAUSE on a specific agent
    event = ks.activate(
        level=KillLevel.PAUSE,
        scope=KillScope.AGENT,
        scope_target="researcher",
        reason="Rate limit approaching",
        activated_by="monitoring-system",
    )
    print(f"Activated PAUSE: latency={event.latency_ms:.2f}ms")

    # Check the researcher (should be paused)
    status = ks.check(scope_target="researcher")
    print(f"Researcher: killed={status.is_killed}, level={status.level}")  # True, pause

    # Coder is unaffected
    status = ks.check(scope_target="coder")
    print(f"Coder: killed={status.is_killed}")  # False

    # Escalate to KILL globally
    event = ks.activate(
        level=KillLevel.KILL,
        scope=KillScope.GLOBAL,
        reason="Emergency: runaway agent detected",
        activated_by="operator",
    )
    print(f"Global KILL: latency={event.latency_ms:.2f}ms")

    # Now everyone is killed
    for agent_id in ["supervisor", "researcher", "coder"]:
        status = ks.check(scope_target=agent_id)
        print(f"{agent_id}: killed={status.is_killed}, level={status.level}")

    # Deactivate global kill
    ks.deactivate(KillScope.GLOBAL, deactivated_by="operator")

    # Check audit trail
    events = ks.get_events()
    print(f"\nAudit trail: {len(events)} events")
    for evt in events:
        print(f"  [{evt.level.value}] {evt.scope.value}:{evt.scope_target} - {evt.reason}")

    # Check status summary
    status_summary = ks.get_status()
    print(f"\nActive kill switches: {status_summary['total_active']}")


if __name__ == "__main__":
    main()
