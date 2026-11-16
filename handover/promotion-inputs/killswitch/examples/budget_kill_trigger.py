"""Budget kill trigger example for agent-killswitch.

Shows how to automatically kill agents that exceed their budget.
"""

from __future__ import annotations

from agent_killswitch import BudgetKillTrigger, KillSwitch


def main() -> None:
    # Create kill switch and budget trigger
    ks = KillSwitch()

    def on_alert(agent_id: str, utilization: float) -> None:
        print(f"  ALERT: {agent_id} at {utilization * 100:.0f}% budget utilization")

    def on_exceeded(agent_id: str, cost: float, limit: float) -> None:
        print(f"  EXCEEDED: {agent_id} spent ${cost:.2f} of ${limit:.2f} budget!")

    budget = BudgetKillTrigger(
        killswitch=ks,
        default_budget=50.0,
        alert_thresholds=[0.50, 0.80, 0.95],
        kill_on_exceed=True,
        on_alert=on_alert,
        on_budget_exceeded=on_exceeded,
    )

    # Set budgets
    budget.set_budget("research-agent", 50.0)
    budget.set_budget("coding-agent", 100.0)

    print("Simulating agent costs...")
    print("-" * 40)

    # Research agent spends money
    print("\nResearch agent:")
    for cost in [10.0, 15.0, 8.0, 12.0, 7.0]:
        status = budget.track_cost("research-agent", cost)
        print(
            f"  Spent ${cost:.2f} (total: ${status.current_cost:.2f}, "
            f"utilization: {status.utilization * 100:.0f}%)"
        )

    # Check if research agent was killed
    ks_status = ks.check(scope_target="research-agent")
    print(f"\n  Research agent killed: {ks_status.is_killed}")
    if ks_status.is_killed:
        print(f"  Kill reason: {ks_status.reason}")

    # Coding agent spends money (under budget)
    print("\nCoding agent:")
    for cost in [20.0, 25.0, 15.0]:
        status = budget.track_cost("coding-agent", cost)
        print(
            f"  Spent ${cost:.2f} (total: ${status.current_cost:.2f}, "
            f"utilization: {status.utilization * 100:.0f}%)"
        )

    ks_status = ks.check(scope_target="coding-agent")
    print(f"\n  Coding agent killed: {ks_status.is_killed}")

    # Show all budget statuses
    print("\nBudget summary:")
    for agent_id, status in budget.get_all_statuses().items():
        print(
            f"  {agent_id}: ${status.current_cost:.2f} / ${status.budget_limit:.2f} "
            f"({status.utilization * 100:.0f}%)"
        )


if __name__ == "__main__":
    main()
