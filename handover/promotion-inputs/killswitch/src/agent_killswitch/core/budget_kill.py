"""Budget-based kill trigger for autonomous AI agents.

Monitors cost accumulation and triggers kill switches when budget
thresholds are exceeded. Supports configurable alert thresholds
and automatic PAUSE or KILL on budget exhaustion.

Thread-safe: All state is protected by a reentrant lock.
No external dependencies: Uses only Python stdlib.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from .enums import KillLevel, KillScope
from .models import BudgetStatus

logger = logging.getLogger(__name__)


class BudgetKillTrigger:
    """Monitor agent costs and kill when budget is exceeded.

    Tracks cost accumulation per agent and fires alerts at configurable
    thresholds. When the budget is exhausted, automatically activates
    the kill switch (PAUSE or KILL, configurable).

    Example::

        from agent_killswitch import KillSwitch, BudgetKillTrigger

        ks = KillSwitch()
        budget = BudgetKillTrigger(
            killswitch=ks,
            default_budget=50.0,  # $50 per agent
            on_alert=lambda agent_id, pct: print(f"{agent_id}: {pct * 100:.0f}% used"),
        )

        budget.set_budget("agent-1", 50.0)
        budget.track_cost("agent-1", 10.0)  # $10 spent
        budget.track_cost("agent-1", 35.0)  # $45 total -> 90% alert fires

    Args:
        killswitch: Optional KillSwitch instance for auto-kill on exceed.
        default_budget: Default budget limit for new agents. Default 0 (unlimited).
        alert_thresholds: Budget utilization thresholds for alerts.
            Default [0.50, 0.80, 0.95].
        kill_on_exceed: If True, activate KILL when budget exceeded.
            If False, activate PAUSE. Default True.
        on_alert: Callback when a threshold is reached.
            Signature: (agent_id: str, utilization: float) -> None
        on_budget_exceeded: Callback when budget is fully exceeded.
            Signature: (agent_id: str, current_cost: float, limit: float) -> None
    """

    def __init__(
        self,
        killswitch: Any = None,
        default_budget: float = 0.0,
        alert_thresholds: list[float] | None = None,
        kill_on_exceed: bool = True,
        on_alert: Callable[[str, float], None] | None = None,
        on_budget_exceeded: Callable[[str, float, float], None] | None = None,
    ) -> None:
        self._killswitch = killswitch
        self._default_budget = default_budget
        self._alert_thresholds = sorted(alert_thresholds or [0.50, 0.80, 0.95])
        self._kill_on_exceed = kill_on_exceed
        self._on_alert = on_alert
        self._on_budget_exceeded = on_budget_exceeded
        self._lock = threading.RLock()

        # Per-agent budget tracking
        self._budgets: dict[str, BudgetStatus] = {}

    def set_budget(self, agent_id: str, limit: float) -> None:
        """Set the budget limit for an agent.

        Args:
            agent_id: The agent to set the budget for.
            limit: Maximum allowed cost. Use 0 for unlimited.
        """
        with self._lock:
            if agent_id in self._budgets:
                self._budgets[agent_id].budget_limit = limit
            else:
                self._budgets[agent_id] = BudgetStatus(
                    agent_id=agent_id,
                    budget_limit=limit,
                    alert_thresholds=list(self._alert_thresholds),
                )

        logger.info(
            "budget_set",
            extra={"agent_id": agent_id, "limit": limit},
        )

    def track_cost(self, agent_id: str, amount: float) -> BudgetStatus:
        """Record a cost for an agent.

        Updates the accumulated cost and checks thresholds. If the budget
        is exceeded, triggers the kill switch.

        Args:
            agent_id: The agent incurring the cost.
            amount: The cost amount to add.

        Returns:
            Updated BudgetStatus for the agent.
        """
        with self._lock:
            if agent_id not in self._budgets:
                self._budgets[agent_id] = BudgetStatus(
                    agent_id=agent_id,
                    budget_limit=self._default_budget,
                    alert_thresholds=list(self._alert_thresholds),
                )

            status = self._budgets[agent_id]
            status.current_cost += amount

            # Calculate utilization
            if status.budget_limit > 0:
                status.utilization = status.current_cost / status.budget_limit
            else:
                status.utilization = 0.0

            # Check alert thresholds
            if status.budget_limit > 0:
                for threshold in status.alert_thresholds:
                    if status.utilization >= threshold and threshold not in status.alerts_fired:
                        status.alerts_fired.add(threshold)
                        logger.warning(
                            "budget_alert",
                            extra={
                                "agent_id": agent_id,
                                "threshold": threshold,
                                "utilization": round(status.utilization, 4),
                                "current_cost": status.current_cost,
                                "budget_limit": status.budget_limit,
                            },
                        )
                        if self._on_alert is not None:
                            try:
                                self._on_alert(agent_id, status.utilization)
                            except Exception as exc:
                                logger.error(
                                    "on_alert callback error",
                                    extra={"error": str(exc)},
                                )

                # Check if budget exceeded
                if status.utilization >= 1.0:
                    self._handle_budget_exceeded(agent_id, status)

            # Return a copy
            return BudgetStatus(
                agent_id=status.agent_id,
                budget_limit=status.budget_limit,
                current_cost=status.current_cost,
                utilization=status.utilization,
                alert_thresholds=list(status.alert_thresholds),
                alerts_fired=set(status.alerts_fired),
            )

    def _handle_budget_exceeded(self, agent_id: str, status: BudgetStatus) -> None:
        """Handle budget exceeded by triggering kill switch.

        Args:
            agent_id: The agent that exceeded its budget.
            status: The current budget status.
        """
        logger.critical(
            "budget_exceeded",
            extra={
                "agent_id": agent_id,
                "current_cost": status.current_cost,
                "budget_limit": status.budget_limit,
                "utilization": round(status.utilization, 4),
            },
        )

        # Fire callback
        if self._on_budget_exceeded is not None:
            try:
                self._on_budget_exceeded(agent_id, status.current_cost, status.budget_limit)
            except Exception as exc:
                logger.error(
                    "on_budget_exceeded callback error",
                    extra={"error": str(exc)},
                )

        # Trigger kill switch
        if self._killswitch is not None:
            level = KillLevel.KILL if self._kill_on_exceed else KillLevel.PAUSE
            try:
                self._killswitch.activate(
                    level=level,
                    scope=KillScope.AGENT,
                    scope_target=agent_id,
                    reason=f"Budget exceeded: ${status.current_cost:.2f} / ${status.budget_limit:.2f}",
                    activated_by="budget_kill_trigger",
                )
            except Exception as exc:
                logger.error(
                    "budget_kill_activation_error",
                    extra={"agent_id": agent_id, "error": str(exc)},
                )

    def get_status(self, agent_id: str) -> BudgetStatus | None:
        """Get the budget status for an agent.

        Args:
            agent_id: The agent to check.

        Returns:
            BudgetStatus or None if no budget tracked.
        """
        with self._lock:
            status = self._budgets.get(agent_id)
            if status is None:
                return None
            return BudgetStatus(
                agent_id=status.agent_id,
                budget_limit=status.budget_limit,
                current_cost=status.current_cost,
                utilization=status.utilization,
                alert_thresholds=list(status.alert_thresholds),
                alerts_fired=set(status.alerts_fired),
            )

    def get_all_statuses(self) -> dict[str, BudgetStatus]:
        """Get budget status for all tracked agents.

        Returns:
            Dictionary of agent_id -> BudgetStatus.
        """
        with self._lock:
            return {
                agent_id: BudgetStatus(
                    agent_id=s.agent_id,
                    budget_limit=s.budget_limit,
                    current_cost=s.current_cost,
                    utilization=s.utilization,
                    alert_thresholds=list(s.alert_thresholds),
                    alerts_fired=set(s.alerts_fired),
                )
                for agent_id, s in self._budgets.items()
            }

    def reset_cost(self, agent_id: str) -> None:
        """Reset the accumulated cost for an agent.

        Args:
            agent_id: The agent to reset.
        """
        with self._lock:
            if agent_id in self._budgets:
                self._budgets[agent_id].current_cost = 0.0
                self._budgets[agent_id].utilization = 0.0
                self._budgets[agent_id].alerts_fired.clear()

        logger.info("budget_cost_reset", extra={"agent_id": agent_id})

    def remove_agent(self, agent_id: str) -> None:
        """Remove all budget tracking for an agent.

        Args:
            agent_id: The agent to remove.
        """
        with self._lock:
            self._budgets.pop(agent_id, None)

    @property
    def tracked_agents(self) -> int:
        """Number of agents with budget tracking."""
        with self._lock:
            return len(self._budgets)
