"""The cost meter (design 13, amendments A-03): one JSON file shared with the Replay Check, a worst-case pre-check
before every call, billed-error charging, a kill-switch flag file.

File shape (money as decimal strings):
{"total_cap": "10.00", "reserve": "1.00", "demo_cap": "8.00",
 "spent": {"askdata": "0", "replay_check": "0"}, "external_usd": "0", "external_updated_at": "<UTC stamp>"}

A call may start only if `askdata_spent + worst_case <= demo_cap` AND
`sum(spent) + external_usd + worst_case <= total_cap - reserve` (so the reserve stays unspent inside the owner's cap).
`external_usd` is typed in from the provider console; a live step refuses to run while it is older than
`max_external_age`.

Atomic across processes: `reserve(worst_case)` does the check AND books the worst case in one step under an OS file
lock (`msvcrt` on Windows, `fcntl` elsewhere; the OS drops the lock if the holder dies, so there is no stale lock).
After the call, `settle(reserved, actual, rid)` replaces the reservation with the real cost. This is a two-phase
reserve/settle: `reserve` returns an id and records it under `open` BEFORE the call, `settle` removes it. A process
that dies between the two leaves its worst case booked (fails safe) AND an `open` record, so the crash is visible:
`snapshot()["open"]` lists it, a live run refuses to start while one is older than `stale_open_after` (see `stale_open`),
and the owner clears it with `meter --clear-open` after reading the provider console. Writes are write-fsync-replace.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from askdata.settings import RUNTIME, MeterLimits
from hadavin_sdk.config import Route
from hadavin_sdk.llm.common import estimate_tokens
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted, UnusableAnswer

PROJECT = "askdata"
_DEFAULT = MeterLimits()  # the documented defaults live in settings.py
STAMP = "%Y-%m-%dT%H:%M:%SZ"
M = Decimal(1_000_000)


class MeterError(RuntimeError):
    """The meter file is missing, unreadable or inconsistent. Callers treat this as 'do not spend'."""


class OverBudget(MeterError):
    def __init__(self, which: str, detail: str) -> None:
        super().__init__(f"{which}: {detail}")
        self.which = which  # "demo_cap", "shared_cap", "external_stale"


def worst_case_usd(route: Route, prompt_bytes: int) -> Decimal:
    """Input estimate (the core's pessimistic 3 UTF-8 BYTES a token: pass bytes, never characters, or CJK and emoji
    are undercounted) at the input rate plus `max_tokens` at the output rate."""
    tokens_in = estimate_tokens("x" * prompt_bytes)
    return (
        Decimal(tokens_in) * route.input_usd_per_mtok
        + Decimal(route.max_tokens) * route.output_usd_per_mtok
    ) / M


def call_cost(
    per_attempt: Decimal,
    reserved: Decimal,
    *,
    sent: int,
    reply_cost: Decimal | None,
    refused: bool = False,
    answered: int = 1,
    billed: Decimal = Decimal(0),
) -> Decimal:
    """What ONE `chat()` cost, the single place that decides it. A kind may send several requests inside one call
    (retries; some also ask again after an unusable answer). Only an answered request reports usage. So:

    * with a reply: `reply_cost` (the kind sums every answered request) plus `per_attempt` for each request that was
      sent but not answered (a timed-out request may still be billed). A reply cost that is negative is taken as 0
      and one that is not finite as the whole reservation (fail safe); the reply branch may exceed the reservation
      (the overage is recorded, not refused);
    * without a reply: `billed` (what earlier answered requests already cost, carried by the error), plus
      `per_attempt` for each other request sent, EXCEPT that the last one is free when the provider REFUSED it (a
      non-transient 4xx); an unusable 200 body is not a refusal, it was billed. Never above the reservation. When
      every request was answered (`answered == sent`) the unrefused branch still adds one `per_attempt`: it
      over-counts by one request and fails safe."""
    sent = max(1, sent)
    if reply_cost is not None:
        if not reply_cost.is_finite():
            return reserved
        return max(Decimal(0), reply_cost) + per_attempt * max(0, sent - max(answered, 1))
    others = max(0, sent - answered - 1)
    return min(reserved, billed + per_attempt * others + (Decimal(0) if refused else per_attempt))


def error_cost(
    err: BaseException, per_attempt: Decimal, reserved: Decimal, default_attempts: int
) -> Decimal:
    """What a `chat()` that RAISED cost. A `ProviderError` carries `attempts`, `answered` and `billed_usd` (the core
    sets them in `llm/retry.py`); a free refusal is a ProviderError that is neither `ProviderExhausted` nor
    `UnusableAnswer`. Any other error (OSError, timeout) is unknown: `default_attempts` requests may have been sent."""
    known = isinstance(err, ProviderError)
    return call_cost(
        per_attempt,
        reserved,
        sent=getattr(err, "attempts", 1) if known else default_attempts,
        reply_cost=None,
        refused=known and not isinstance(err, ProviderExhausted | UnusableAnswer),
        answered=getattr(err, "answered", 0),
        billed=Decimal(getattr(err, "billed_usd", 0)),
    )


def _dec(value: object, name: str) -> Decimal:
    text = str(value)
    try:
        out = Decimal(text)
    except InvalidOperation:
        raise MeterError(f"meter field {name} is not a number") from None
    if not text.isascii():  # Decimal reads Arabic-Indic and other Unicode digits
        raise MeterError(f"meter field {name} is not a number")
    if (
        out.is_finite() and out.adjusted() > _DEFAULT.max_amount_exponent
    ):  # 1e999999 is finite and ruins every sum after it
        raise MeterError(f"meter field {name} is implausibly large")
    if not out.is_finite() or out < 0:
        raise MeterError(f"meter field {name} is not a non-negative number")
    return out


def fmt_usd(d: Decimal) -> str:
    return format(d.normalize(), "f") if d != 0 else "0"


def _try_lock(f) -> bool:
    """Try to take the exclusive lock on the first byte of an open file; False if another process holds it."""
    f.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(f) -> None:
    f.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class Meter:
    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] | None = None,
        max_external_age: timedelta = timedelta(hours=_DEFAULT.max_external_age_hours),
        stale_open_after: timedelta = timedelta(minutes=_DEFAULT.stale_open_minutes),
        lock_wait_s: float = RUNTIME.lock_wait_s,
    ) -> None:
        self.stale_open_after = stale_open_after
        self.path = Path(path)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.max_external_age = max_external_age
        self.lock_wait_s = lock_wait_s

    # ------------------------------------------------------------------------------------------- file
    @staticmethod
    def create(
        path: Path, *, total_cap: str, reserve: str, demo_cap: str, now: datetime | None = None
    ) -> None:
        if _dec(demo_cap, "demo_cap") > _dec(total_cap, "total_cap") - _dec(reserve, "reserve"):
            raise MeterError("demo_cap must fit under total_cap minus reserve")
        stamp = (now or datetime.now(UTC)).strftime(STAMP)
        data = {
            "total_cap": total_cap, "reserve": reserve, "demo_cap": demo_cap,
            "spent": {"askdata": "0", "replay_check": "0"}, "external_usd": "0", "external_updated_at": stamp,
        }  # fmt: skip
        Meter(path)._write(data)

    def _read_text(self) -> str:
        """The file text; a PermissionError (Windows refuses a read while the file is being replaced) is retried."""
        for attempt in range(RUNTIME.lock_replace_attempts):
            try:
                return self.path.read_text(encoding="utf-8")
            except PermissionError:
                if attempt == RUNTIME.lock_replace_attempts - 1:
                    raise
                time.sleep(RUNTIME.lock_replace_wait_s)
        raise AssertionError("unreachable")  # pragma: no cover

    def _read(self) -> dict:
        try:
            data = json.loads(self._read_text())
            for key in ("total_cap", "reserve", "demo_cap", "external_usd"):
                _dec(data[key], key)
            for key, val in data["spent"].items():
                _dec(val, f"spent.{key}")
            _dec(data["spent"][PROJECT], f"spent.{PROJECT}")
            datetime.strptime(data["external_updated_at"], STAMP)  # noqa: DTZ007  # parsed only to validate the shape
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as err:
            raise MeterError(f"meter file unreadable or malformed: {type(err).__name__}") from None
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + f".tmp{os.getpid()}")
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(data, sort_keys=True, indent=2) + "\n")
                f.flush()
                os.fsync(f.fileno())
            from askdata.evalset import replace_with_retry  # the same retry the sealed files use

            replace_with_retry(tmp, self.path)
        except (
            OSError
        ) as err:  # a PermissionError that survived the retries: callers handle MeterError
            with contextlib.suppress(OSError):
                tmp.unlink(missing_ok=True)
            raise MeterError(f"meter file cannot be written: {type(err).__name__}") from None

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        """Exclusive OS lock on `<file>.lock`, waiting up to `lock_wait_s`."""
        lock = self.path.with_name(self.path.name + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        with open(lock, "a+b") as f:
            deadline = time.monotonic() + self.lock_wait_s
            while not _try_lock(f):
                if time.monotonic() > deadline:
                    raise MeterError("meter lock busy")
                time.sleep(RUNTIME.lock_poll_s)
            try:
                yield
            finally:
                _unlock(f)

    # ---------------------------------------------------------------------------------------- numbers
    def snapshot(self) -> dict[str, Decimal | str]:
        with self._locked():  # a reader never sees (or collides with) a half-finished replace
            d = self._read()
        spent = {k: _dec(v, k) for k, v in d["spent"].items()}
        total, reserve, demo = (
            _dec(d["total_cap"], "total_cap"),
            _dec(d["reserve"], "reserve"),
            _dec(d["demo_cap"], "demo_cap"),
        )
        ext = _dec(d["external_usd"], "external_usd")
        mine = spent[PROJECT]
        shared_room = total - reserve - sum(spent.values(), Decimal(0)) - ext
        return {
            "askdata_spent": mine, "demo_cap": demo, "demo_room": demo - mine, "shared_room": shared_room,
            "remaining": min(demo - mine, shared_room), "external_usd": ext,
            "external_updated_at": d["external_updated_at"], "open": len(d.get("open", {})),
        }  # fmt: skip

    def remaining(self) -> Decimal:
        return self.snapshot()["remaining"]  # type: ignore[return-value]

    def _verify(self, d: dict, worst_case: Decimal, live: bool) -> None:
        spent = {k: _dec(v, k) for k, v in d["spent"].items()}
        total, reserve = _dec(d["total_cap"], "total_cap"), _dec(d["reserve"], "reserve")
        demo, ext = _dec(d["demo_cap"], "demo_cap"), _dec(d["external_usd"], "external_usd")
        mine = spent[PROJECT]
        shared_room = total - reserve - sum(spent.values(), Decimal(0)) - ext
        if worst_case > demo - mine:
            raise OverBudget("demo_cap", f"spent {mine} of {demo}, worst case {worst_case}")
        if worst_case > shared_room:
            raise OverBudget("shared_cap", f"shared room {shared_room}, worst case {worst_case}")
        if live:
            age = self.clock() - datetime.strptime(d["external_updated_at"], STAMP).replace(
                tzinfo=UTC
            )
            if age > self.max_external_age:
                raise OverBudget(
                    "external_stale", f"external_usd was set {d['external_updated_at']}"
                )

    def check(self, worst_case: Decimal, *, live: bool = True) -> None:
        """Raise `OverBudget` unless this call fits in both caps (a look only; use `reserve` before a real call)."""
        with self._locked():
            self._verify(self._read(), worst_case, live)

    def reserve(self, worst_case: Decimal, *, live: bool = True) -> str:
        """Check AND book `worst_case` as spent, atomically across processes, and record it as open under a new id
        (returned; pass it to `settle`). Raises `OverBudget`."""
        if worst_case < 0:
            raise MeterError("negative reservation")
        with self._locked():
            d = self._read()
            self._verify(d, worst_case, live)
            d["spent"][PROJECT] = fmt_usd(_dec(d["spent"][PROJECT], PROJECT) + worst_case)
            rid = uuid.uuid4().hex
            d.setdefault("open", {})[rid] = {
                "amount": fmt_usd(worst_case),
                "ts": self.clock().strftime(STAMP),
            }
            self._write(d)
        return rid

    def settle(self, reserved: Decimal, actual: Decimal, rid: str | None = None) -> None:
        """Replace a reservation with what the call really cost (never below zero; above is recorded, not refused)
        and close its `open` record. With a `rid` the amount released is the one STORED at `reserve` (the caller's
        `reserved` is not trusted). A reservation that `meter --clear-open` forgot mid-flight still books an overage;
        an unknown or already settled `rid` changes nothing."""
        for name, v in (("actual", actual), ("reserved", reserved)):
            if not v.is_finite() or v < 0:
                raise MeterError(f"settlement {name} must be a finite, non-negative number")
        with self._locked():
            d = self._read()
            if rid is not None:
                opened = d.get("open", {})
                if rid in opened:
                    reserved = _dec(opened.pop(rid)["amount"], "open.amount")
                elif rid in d.get(
                    "cleared", {}
                ):  # forgotten by clear_open: its amount is already booked as spent
                    reserved = _dec(d["cleared"].pop(rid), "cleared.amount")
                    actual = max(
                        actual, reserved
                    )  # only the overage is new; never release a booked amount
                else:
                    return  # already settled (or never reserved): a second settle must not move the total again
            now = _dec(d["spent"][PROJECT], PROJECT) - reserved + actual
            d["spent"][PROJECT] = fmt_usd(max(now, Decimal(0)))
            self._write(d)

    def open_reservations(self) -> dict[str, dict[str, str]]:
        """Reservations not yet settled (id -> amount, ts): a call in flight, or a process that died."""
        with self._locked():
            return dict(self._read().get("open", {}))

    def stale_open(self) -> list[str]:
        """Ids of open reservations older than `stale_open_after` (config meter.stale_open_minutes): calls whose process died before `settle`."""
        now = self.clock()
        return [
            rid
            for rid, o in self.open_reservations().items()
            if now - datetime.strptime(o["ts"], STAMP).replace(tzinfo=UTC) > self.stale_open_after
        ]

    def clear_open(self) -> int:
        """Forget every open record (the money stays booked as spent). The owner does this after checking the provider
        console for what the dead calls really cost."""
        with self._locked():
            d = self._read()
            n = len(d.get("open", {}))
            forgotten = {rid: o["amount"] for rid, o in d.get("open", {}).items()}
            d["cleared"] = dict(
                list({**d.get("cleared", {}), **forgotten}.items())[-RUNTIME.cleared_kept :]
            )
            d["open"] = {}
            self._write(d)
        return n

    def charge(self, amount: Decimal) -> Decimal:
        """Add `amount` to this project's spend; returns the new total."""
        if not amount.is_finite() or amount < 0:
            raise MeterError("a charge must be a finite, non-negative number")
        with self._locked():
            d = self._read()
            total = _dec(d["spent"][PROJECT], PROJECT) + amount
            d["spent"][PROJECT] = fmt_usd(total)
            self._write(d)
        return total

    def set_external(self, usd: Decimal) -> None:
        """Type in the spend of other programs (provider console). Stamps the time."""
        if not usd.is_finite() or usd < 0:
            raise MeterError("external spend must be a finite, non-negative number")
        with self._locked():
            d = self._read()
            d["external_usd"] = fmt_usd(usd)
            d["external_updated_at"] = self.clock().strftime(STAMP)
            self._write(d)


class KillSwitch:
    """A flag file: present = the tool is off. Created and removed by the CLI, which audits the change first."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def is_on(self) -> bool:
        return self.path.exists()

    def on(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("off\n", encoding="utf-8")

    def off(self) -> None:
        self.path.unlink(missing_ok=True)
