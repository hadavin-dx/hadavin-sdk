"""The meter: set the worst-case cost of a model call aside BEFORE the call (reserve), replace it with the real cost
AFTER (settle) or give it all back (release), and always settle on the way out of a `with` block.

It is a small library class over the `store` kind (P4d's six reservation methods); it imports no database library.
The counters are the store's rows (day, month, run), the same rows `Limits.charge` and `Limits.blocked` use, so
there is one counter. Everything the meter raises on the way to a model call is a `MeterError`, and any exception
from `reserve` means the model is NOT called (fail closed). A settle for one reservation id changes the books once;
asking again returns the first result. The meter only SIGNALS an overshoot (the real cost passed the reservation);
the reaction belongs to the caller. It has no sweep, no prune and no delete."""

from __future__ import annotations

import contextlib
import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from hadavin_sdk import models
from hadavin_sdk.defaults import (
    METER_MAX_HOLD_LIMIT_S,
    METER_MAX_HOLD_S,
    METER_ORPHAN_AGE_S,
    METER_ORPHAN_FACTOR,
    METER_ORPHAN_MARGIN_S,
    METER_SETTLE_RETRIES,
)
from hadavin_sdk.money import SpendMicro
from hadavin_sdk.store import protocol as store_protocol

log = logging.getLogger("hadavin_sdk.meter")

# Closed list of the codes of `MeterUnavailable`.
CODES = (
    "store_unreachable",
    "store_busy",
    "store_rejected",
    "conflict",
    "unknown_run",
    "unknown_reservation",
    "counter_damaged",
)
# The reason words `Limits.blocked` prints, by the cap that refused.
REASON_BY_WHICH = {"run": "run_budget", "day": "daily_budget", "month": "monthly_budget"}
# The store methods the meter needs (a store without them is refused at construction).
_NEEDED = (
    "reserve_spend",
    "settle_spend",
    "release_spend",
    "get_spend_reservation",
)


class MeterError(RuntimeError):
    """Anything the meter raises on the way to a model call. Not an `OSError` (the store calls those
    "unreachable") and not a `ValueError`."""


class OverBudget(MeterError):
    """A cap (or the kill switch) refused the reservation. `cap`, `current` and `requested` are the `Decimal`
    values of the store's refusal, passed through unchanged; `which` is "run", "day", "month" or None (kill
    switch: no numbers); `day` is the UTC budget day."""

    def __init__(
        self,
        reasons: tuple[str, ...],
        *,
        which: str | None,
        cap: Decimal | None,
        current: Decimal | None,
        requested: Decimal | None,
        day: date,
    ) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons
        self.which, self.cap, self.current, self.requested, self.day = (
            which,
            cap,
            current,
            requested,
            day,
        )


class MeterUnavailable(MeterError):
    """The meter could not do its job; `code` is one of `CODES`. No exception text is kept."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, kw_only=True)
class Caps:
    """The three caps of one reservation, in US dollars; `None` means no cap at this level. All three are
    required so that a forgotten cap is a `TypeError`, not a silent "no limit"."""

    day: Decimal | None
    month: Decimal | None
    run: Decimal | None


@dataclass(frozen=True)
class Settled:
    """The result of a settle or release. `applied` is true only when THIS call changed the books; `overshoot`
    is zero unless the real cost passed the reservation."""

    reservation_id: str
    status: str
    charged: SpendMicro
    applied: bool
    overshoot: SpendMicro


@dataclass(frozen=True)
class SettleFailure:
    """The exit settle of a hold failed and the reservation was kept. `planned` is the amount the hold meant to
    settle (None: the reserved worst case); `code` is one of `CODES`."""

    reservation_id: str
    planned: SpendMicro | None
    code: str


class Hold:
    """One reservation seen from the code that made it. Callers do not construct it; `Meter.reserve` and
    `Meter.hold` do. Nothing here calls the store: `record` and `release` only plan the exit."""

    def __init__(
        self,
        *,
        reservation_id: str,
        agent_id: str,
        run_id: str | None,
        reserved: SpendMicro,
        day: date,
        monotonic: Callable[[], float],
    ) -> None:
        self.reservation_id, self.agent_id, self.run_id = reservation_id, agent_id, run_id
        self.reserved, self.day = reserved, day
        self._monotonic = monotonic
        self._t0 = monotonic()
        self._release = False
        self._actual: SpendMicro | None = None
        self._measured = False
        self.settled: Settled | None = None
        self.settle_failure: SettleFailure | None = None

    def age_s(self) -> float:
        """Seconds since the reservation, by the injected monotonic clock (wall time is never used for age)."""
        return self._monotonic() - self._t0

    def record(self, actual: SpendMicro | None, *, measured: bool = True) -> None:
        """Plan to settle at `actual` (None: at the reserved worst case). `measured` says the amount is a
        measured provider usage: only then can an excess raise `on_overshoot`. The LAST of `record` and
        `release` wins."""
        if actual is not None and type(actual) is not SpendMicro:
            raise TypeError("actual must be a SpendMicro or None")
        if actual is not None and actual.micro == 0:
            raise ValueError("a settle amount of zero is refused; use release()")
        if type(measured) is not bool:
            raise TypeError("measured must be a bool")
        self._release, self._actual, self._measured = False, actual, measured

    def release(self) -> None:
        """Plan to give the whole reservation back (the call was never sent)."""
        self._release, self._actual, self._measured = True, None, False


class Meter:
    def __init__(
        self,
        store: Any,
        *,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        max_hold_s: int | None = None,
        on_overshoot: Callable[[Settled], None] | None = None,
        on_settle_failed: Callable[[SettleFailure], None] | None = None,
    ) -> None:
        absent = sorted(set(_NEEDED) & set(store_protocol.missing_methods(store)))
        if absent:
            raise MeterError("the store lacks: " + ", ".join(absent))
        hold_s = METER_MAX_HOLD_S if max_hold_s is None else max_hold_s
        if type(hold_s) is not int or not 1 <= hold_s <= METER_MAX_HOLD_LIMIT_S:
            raise ValueError(f"max_hold_s must be an int from 1 to {METER_MAX_HOLD_LIMIT_S}")
        self.store = store
        self.max_hold_s = hold_s
        # resolved at CALL time, so a later patch of `models.now` or `time.monotonic` is seen
        self._clock, self._monotonic = clock, monotonic
        self._on_overshoot, self._on_settle_failed = on_overshoot, on_settle_failed

    # --- clocks ------------------------------------------------------------------------------------------------
    def _mono(self) -> float:
        if self._monotonic is not None:
            return self._monotonic()
        return time.monotonic()

    def spend_day(self) -> date:
        """The UTC budget day: the same expression `Limits.blocked` and `Limits.charge` use."""
        return (self._clock if self._clock is not None else models.now)().date()

    def orphan_age_s(self) -> int:
        """The age (seconds) at which an open hold counts as orphaned: age policy only (the sweep is not here)."""
        return max(
            METER_ORPHAN_AGE_S, METER_ORPHAN_FACTOR * self.max_hold_s + METER_ORPHAN_MARGIN_S
        )

    # --- error mapping -----------------------------------------------------------------------------------------
    @staticmethod
    def _is_busy(exc: BaseException) -> bool:
        busy = getattr(store_protocol, "StoreBusy", None)  # looked up at call time
        return busy is not None and isinstance(exc, busy)

    def _code(self, exc: BaseException, *, reserving: bool) -> str:
        """The closed code for a store exception (the one error table)."""
        if isinstance(exc, store_protocol.CounterDamaged):
            return "counter_damaged"
        if self._is_busy(exc):
            return "store_busy"
        if isinstance(exc, store_protocol.NotFound):
            return "unknown_run" if reserving else "unknown_reservation"
        if isinstance(exc, store_protocol.StaleState):  # ReservationConflict is a StaleState
            return "conflict"
        if isinstance(exc, ValueError):
            return "store_rejected"
        return "store_unreachable"

    # --- reserve -----------------------------------------------------------------------------------------------
    def reserve(
        self, agent_id: str, worst: SpendMicro, caps: Caps, *, run_id: str | None = None
    ) -> Hold:
        """Set `worst` aside. Raises `OverBudget` or `MeterUnavailable` (the model must not be called then);
        a bad argument is `TypeError` or `ValueError` before any store call."""
        if type(worst) is not SpendMicro:
            raise TypeError("worst must be a SpendMicro")
        if worst.micro == 0:
            raise ValueError("worst must be above zero")
        if type(caps) is not Caps:
            raise TypeError("caps must be a Caps")
        store_protocol.check_id(agent_id, "agent_id")
        if run_id is not None:
            store_protocol.check_id(run_id, "run_id")
        elif caps.run is not None:
            raise ValueError("a run cap needs a run_id")
        for cap in (caps.day, caps.month, caps.run):
            store_protocol.check_cap(cap)
        day = self.spend_day()
        rid = models.new_id("rsv")
        try:
            self.store.reserve_spend(
                rid,
                agent_id,
                day,
                worst.to_usd(),
                day_cap=caps.day,
                month_cap=caps.month,
                run_id=run_id,
                run_cap=caps.run,
            )
        except BaseException as exc:  # noqa: BLE001 - fail closed: any outcome of the store call is mapped; interrupts are re-raised
            raise self._reserve_failure(exc, rid, day) from None
        return Hold(
            reservation_id=rid,
            agent_id=agent_id,
            run_id=run_id,
            reserved=worst,
            day=day,
            monotonic=self._mono,
        )

    def _reserve_failure(self, exc: BaseException, rid: str, day: date) -> BaseException:
        """The release table: release when the outcome is unknown to the meter, never when the store answered.
        Returns the exception to raise (or re-raises `KeyboardInterrupt` and `SystemExit` unchanged)."""
        if isinstance(exc, store_protocol.KillSwitchOn):
            return OverBudget(
                ("kill_switch",), which=None, cap=None, current=None, requested=None, day=day
            )
        if isinstance(exc, store_protocol.SpendCapExceeded):
            reason = REASON_BY_WHICH.get(exc.which)
            if reason is None:
                return MeterUnavailable("store_rejected")
            return OverBudget(
                (reason,),
                which=exc.which,
                cap=exc.cap,
                current=exc.current,
                requested=exc.requested,
                day=day,
            )
        code = self._code(exc, reserving=True)
        if code in ("conflict", "unknown_run", "counter_damaged", "store_rejected"):
            return MeterUnavailable(
                code
            )  # the store answered and rolled back: nothing of ours is written
        # StoreBusy or anything unknown: the outcome is unknown, so give the claim back (best effort)
        try:
            self.store.release_spend(rid)
        except Exception as release_exc:  # noqa: BLE001 - the release is best effort; its own error is logged by class name only
            log.warning(
                "meter release after an unknown reserve failed: %s", type(release_exc).__name__
            )
        if isinstance(exc, KeyboardInterrupt | SystemExit):
            raise exc
        return MeterUnavailable(code)

    # --- settle and release ------------------------------------------------------------------------------------
    @staticmethod
    def _settled(outcome: Any) -> tuple[Settled, SpendMicro]:
        """The `Settled` of a store outcome and the reserved amount of its row."""
        row = outcome.reservation
        reserved = SpendMicro.from_usd(row.reserved_usd)
        if row.status == "released" or row.settled_usd is None:
            charged = SpendMicro(0)
        else:
            charged = SpendMicro.from_usd(row.settled_usd)
        over = charged - reserved if charged > reserved else SpendMicro(0)
        status = "released" if row.status == "released" else "settled"
        return Settled(row.reservation_id, status, charged, bool(outcome.applied), over), reserved

    def _call(self, method: str, *args: Any) -> Any:
        try:
            return getattr(self.store, method)(*args)
        except Exception as exc:  # noqa: BLE001 - every store failure becomes a closed code, never the store's own text
            raise MeterUnavailable(self._code(exc, reserving=False)) from None

    def settle(self, reservation_id: str, actual: SpendMicro | None) -> Settled:
        """Replace the reservation by the real cost `actual` (None: the reserved worst case). IDEMPOTENT: a
        second call for the same id, with any amount, returns the first call's result with `applied=False`.
        A standalone settle never calls `on_overshoot` (only the exit of `hold` does)."""
        store_protocol.check_id(reservation_id, "reservation_id")
        if actual is not None and type(actual) is not SpendMicro:
            raise TypeError("actual must be a SpendMicro or None")
        if actual is not None and actual.micro == 0:
            raise ValueError("a settle amount of zero is refused; use release()")
        if actual is None:
            row = self._call("get_spend_reservation", reservation_id)
            actual = SpendMicro.from_usd(row.reserved_usd)
        outcome = self._call("settle_spend", reservation_id, actual.to_usd())
        settled, reserved = self._settled(outcome)
        if not settled.applied and settled.status == "released":
            log.warning(
                "superseded: reservation %s was released first; %d micro-dollars not booked",
                reservation_id,
                actual.micro,
            )
        if settled.applied and settled.overshoot.micro > 0:
            log.warning(
                "overshoot: reservation %s agent %s reserved %d charged %d micro-dollars",
                reservation_id,
                outcome.reservation.agent_id,
                reserved.micro,
                settled.charged.micro,
            )
        return settled

    def release(self, reservation_id: str) -> Settled:
        """Give the whole reservation back. IDEMPOTENT like `settle`."""
        store_protocol.check_id(reservation_id, "reservation_id")
        return self._settled(self._call("release_spend", reservation_id))[0]

    # --- the context manager -----------------------------------------------------------------------------------
    @contextlib.contextmanager
    def hold(
        self, agent_id: str, worst: SpendMicro, caps: Caps, *, run_id: str | None = None
    ) -> Iterator[Hold]:
        """Reserve, run the body, and on EVERY exit (also `KeyboardInterrupt` and `SystemExit`) settle: the last
        of `record`/`release` wins; neither settles at the reserved worst case. The body's exception keeps
        propagating and an exit failure never replaces it."""
        h = self.reserve(agent_id, worst, caps, run_id=run_id)
        try:
            yield h
        finally:
            self._exit(h)

    def _exit(self, h: Hold) -> None:
        age = h.age_s()
        if age > self.max_hold_s:
            log.warning(
                "hold %s stayed open %d seconds (limit %d)",
                h.reservation_id,
                int(age),
                self.max_hold_s,
            )
        code = "store_unreachable"
        for _try in range(METER_SETTLE_RETRIES + 1):  # the SAME settle each time
            try:
                if h._release:
                    h.settled = self.release(h.reservation_id)
                else:
                    h.settled = self.settle(h.reservation_id, h._actual)
            except MeterUnavailable as exc:
                code = exc.code
                if code != "store_busy":
                    break
            except Exception:  # noqa: BLE001 - a bad plan or a bug: still never replace the body's exception
                code = "store_unreachable"
                break
            else:
                self._signal_overshoot(h)
                return
        self._failed(h, code)

    def _signal_overshoot(self, h: Hold) -> None:
        s = h.settled
        if s is None or not (s.applied and s.overshoot.micro > 0 and h._measured):
            return
        if self._on_overshoot is None:
            return
        try:
            self._on_overshoot(s)
        except Exception as exc:  # noqa: BLE001 - a callback must never break the exit; logged by class name only
            log.error("on_overshoot raised %s", type(exc).__name__)

    def _failed(self, h: Hold, code: str) -> None:
        planned = None if h._release else h._actual
        shown = (planned or h.reserved).micro
        failure = SettleFailure(h.reservation_id, planned, code)
        h.settle_failure = failure
        log.error(
            "settle failed: reservation %s kept open, planned %d micro-dollars, code %s",
            h.reservation_id,
            shown,
            code,
        )
        if self._on_settle_failed is None:
            return
        try:
            self._on_settle_failed(failure)
        except Exception as exc:  # noqa: BLE001 - a callback must never break the exit; logged by class name only
            log.error("on_settle_failed raised %s", type(exc).__name__)
