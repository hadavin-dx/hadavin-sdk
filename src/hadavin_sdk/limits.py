"""Limits: spend meter, daily and monthly budgets, kill switch. Every stop and reset is audited.

A stop is one new request row in the store (it cannot be refused for a naming problem and a compromised runtime
cannot hold it up). A reset is allowed only through a separate store handle (`reset_store`, a different database
login in the operator process) and names the exact set of stops it clears by (version, open count).
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Iterable
from decimal import Decimal

from hadavin_sdk.audit.labelkey import (
    NOKEY_LABEL,
    mask_principal,
    valid_key_id,
)
from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.models import AuditEvent, KillSwitch, StopState, now
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import (
    ResetRefused,
    StaleCount,
    Store,
    StoreBusy,
    SwitchRowMissing,
)

_LOG = logging.getLogger(__name__)
MIN_KEY_BYTES = 16  # the same minimum as a restored audit key
_STAGES = frozenset({"dev", "pilot", "prod"})  # exactly what Config.environment accepts; no alias
_MISSING_ROW = "the kill_switch row is missing; a database administrator must re-seed it"


class StopNotPermitted(RuntimeError):
    """The caller may not do this: a reset by a name that is not listed, a process without a reset credential,
    a database refusal, or a missing label key."""


class SwitchChanged(RuntimeError):
    """The reset did not happen because the switch changed since the operator read it (or its row is missing)."""


class StopNotConfirmed(RuntimeError):
    """A stop returned a row that does not read ON."""


class Limits:
    def __init__(
        self,
        store: Store,
        audit: AuditSink,
        registry: Registry,
        *,
        environment: str,
        stop_store: Store | None = None,
        reset_store: Store | None = None,
        reset_names: Iterable[str] = frozenset(),
        label_key: bytes | None = None,
        key_id: str = "k1",
    ) -> None:
        if not valid_key_id(key_id):
            raise ValueError("key_id must match [A-Za-z0-9_-]{1,32}")
        if environment not in _STAGES:  # no alias: "demo" is not "dev" (Config.environment decides)
            raise ValueError(f"environment must be one of {sorted(_STAGES)}, not {environment!r}")
        dev = environment == "dev"
        if not dev and isinstance(store, MemoryStore):
            raise ValueError("a memory store is allowed only when environment is dev")
        if label_key is None:
            if not dev:
                raise ValueError("a label key is required when environment is not dev")
            label_key = secrets.token_bytes(32)
            _LOG.warning(
                "limits: no label key given; using a per-process random key (environment dev only)"
            )
        self.store, self.audit, self.registry = store, audit, registry
        self.environment = environment
        self.stop_store = stop_store if stop_store is not None else store
        self.reset_store = reset_store
        self.reset_names = frozenset(reset_names)
        self._key, self._key_id = label_key, key_id

    # --- the meter -----------------------------------------------------------------------------------------------

    def charge(self, agent_id: str, usd: Decimal) -> tuple[Decimal, Decimal]:
        return self.store.add_spend(agent_id, now().date(), usd)

    def blocked(self, agent_id: str) -> list[str]:
        reasons = []
        if self.store.get_kill_switch().on:
            reasons.append("kill_switch")
        day, month = self.store.spend_totals(agent_id, now().date())  # a read, no write
        budget = self.registry.agents[agent_id].budget_usd
        if day >= budget.daily:
            reasons.append("daily_budget")
        if month >= budget.monthly:
            reasons.append("monthly_budget")
        return reasons

    def status(self) -> StopState:
        return self.store.get_kill_switch()

    # --- labels --------------------------------------------------------------------------------------------------

    def _key_usable(self) -> bool:
        return len(self._key) >= MIN_KEY_BYTES

    def label(self, name: object) -> str:
        """The keyed label of a name (what `limits whois NAME` prints)."""
        if not self._key_usable():
            raise StopNotPermitted("the label key is unavailable or too short")
        return mask_principal(name, self._key, self._key_id)

    @staticmethod
    def _event(on: bool, by: str, operation: str, object_ref: str | None = None) -> AuditEvent:
        event = AuditEvent(
            run_id="-",
            domain="limits",
            operation=operation,
            principal=by,
            source="cli",
            result="on" if on else "off",
        )
        return event if object_ref is None else event.model_copy(update={"object_ref": object_ref})

    # --- stop ----------------------------------------------------------------------------------------------------

    def stop(self, by: object) -> StopState:
        """An emergency stop works when the audit store is down and never fails for a label-key problem: switch
        first, then audit (the outbox takes the row when the audit store is down)."""
        if self._key_usable():
            label = mask_principal(by, self._key, self._key_id)
        else:
            label = NOKEY_LABEL
            _LOG.error(
                "limits: label key unavailable; the stop is recorded as actor not identified"
            )
        try:
            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
        except StoreBusy:
            # The busy call rolled back, so a second try cannot double a row. Once, on a fresh short connection.
            _LOG.error("limits: the store was busy for the stop; trying once more")
            state = self.stop_store.set_kill_switch(KillSwitch(on=True, by=label))
        if state.on is not True:
            raise StopNotConfirmed("the stop returned a row that does not read ON")
        self.audit.write_outcome(
            self._event(True, label, "stop", f"kill_switch:open{state.open_requests}")
        )
        return state

    # --- reset ---------------------------------------------------------------------------------------------------

    def reset(self, by: str, *, expect_version: int, expect_open: int) -> StopState:
        """Clear exactly the set of stops that (expect_version, expect_open) named when the operator read it."""
        for n, top in ((expect_version, 2**63 - 1), (expect_open, 2**31 - 1)):
            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= top:
                raise ValueError("expect_version and expect_open must be integers in range")
        if not self._key_usable():
            raise StopNotPermitted("the label key is unavailable or too short")
        label = mask_principal(by, self._key, self._key_id)
        if by not in self.reset_names:  # typo guard on the raw name; the real check is the database
            self.audit.write_outcome(self._event(False, label, "reset_denied"))
            raise StopNotPermitted("reset refused; the switch stays ON")
        if self.reset_store is None:
            raise StopNotPermitted("this process holds no reset credential")
        self.audit.write_intent(self._event(False, label, "reset_attempted"))
        try:
            state = self.reset_store.reset_kill_switch(label, expect_version, expect_open)
        except StaleCount as exc:
            self.audit.write_outcome(self._event(False, label, "reset_refused"))
            raise SwitchChanged(
                "the stops changed since they were read; read the status again"
            ) from exc
        except ResetRefused as exc:
            self.audit.write_outcome(self._event(False, label, "reset_denied"))
            raise StopNotPermitted("reset refused; the switch stays ON") from exc
        except SwitchRowMissing as exc:
            self.audit.write_outcome(self._event(False, label, "reset_failed"))
            raise SwitchChanged(_MISSING_ROW) from exc
        except Exception:
            self.audit.write_outcome(self._event(False, label, "reset_failed"))
            raise
        self.audit.write_outcome(
            self._event(state.on, label, "reset", f"kill_switch:v{state.version}")
        )
        return state
