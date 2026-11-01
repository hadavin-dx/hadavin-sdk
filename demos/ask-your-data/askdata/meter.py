"""The cost meter (design 13, amendments A-03): one JSON file shared with the Replay Check, a worst-case pre-check
before every call, billed-error charging, a kill-switch flag file.

File shape (money as decimal strings):
{"total_cap": "10.00", "reserve": "1.00", "demo_cap": "8.00",
 "spent": {"askdata": "0", "replay_check": "0"}, "external_usd": "0", "external_updated_at": "<UTC stamp>"}

A call may start only if `askdata_spent + worst_case <= demo_cap` AND
`sum(spent) + external_usd + worst_case <= total_cap - reserve` (so the reserve stays unspent inside the owner's cap).
`external_usd` is typed in from the provider console; a live step refuses to run while it is older than
`max_external_age`. Writes are write-fsync-replace under a small lock file. The pre-check reads the file fresh each
call; two processes can still overshoot by one call's worst case between check and charge (stated, not hidden).
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hadavin_sdk.config import Route
from hadavin_sdk.llm.common import estimate_tokens

PROJECT = "askdata"
STAMP = "%Y-%m-%dT%H:%M:%SZ"
M = Decimal(1_000_000)


class MeterError(RuntimeError):
    """The meter file is missing, unreadable or inconsistent. Callers treat this as 'do not spend'."""


class OverBudget(MeterError):
    def __init__(self, which: str, detail: str) -> None:
        super().__init__(f"{which}: {detail}")
        self.which = which  # "demo_cap", "shared_cap", "external_stale"


def worst_case_usd(route: Route, prompt_chars: int) -> Decimal:
    """Input estimate (the core's pessimistic 3 characters a token) at the input rate plus `max_tokens` at the
    output rate."""
    tokens_in = estimate_tokens("x" * prompt_chars)
    return (
        Decimal(tokens_in) * route.input_usd_per_mtok
        + Decimal(route.max_tokens) * route.output_usd_per_mtok
    ) / M


def _dec(value: object, name: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except InvalidOperation:
        raise MeterError(f"meter field {name} is not a number") from None
    if not out.is_finite() or out < 0:
        raise MeterError(f"meter field {name} is not a non-negative number")
    return out


def fmt_usd(d: Decimal) -> str:
    return format(d.normalize(), "f") if d != 0 else "0"


class Meter:
    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], datetime] | None = None,
        max_external_age: timedelta = timedelta(hours=24),
        lock_wait_s: float = 5.0,
    ) -> None:
        self.path = Path(path)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.max_external_age = max_external_age
        self.lock_wait_s = lock_wait_s

    # ------------------------------------------------------------------------------------------- file
    @staticmethod
    def create(
        path: Path, *, total_cap: str, reserve: str, demo_cap: str, now: datetime | None = None
    ) -> None:
        stamp = (now or datetime.now(UTC)).strftime(STAMP)
        data = {
            "total_cap": total_cap, "reserve": reserve, "demo_cap": demo_cap,
            "spent": {"askdata": "0", "replay_check": "0"}, "external_usd": "0", "external_updated_at": stamp,
        }  # fmt: skip
        Meter(path)._write(data)

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
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
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, sort_keys=True, indent=2) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        lock = self.path.with_name(self.path.name + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.lock_wait_s
        while True:
            try:
                os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                break
            except FileExistsError:
                with contextlib.suppress(OSError):  # a crashed holder: break a lock older than 30 s
                    if time.time() - lock.stat().st_mtime > 30:
                        lock.unlink()
                        continue
                if time.monotonic() > deadline:
                    raise MeterError("meter lock busy") from None
                time.sleep(0.02)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                lock.unlink()

    # ---------------------------------------------------------------------------------------- numbers
    def snapshot(self) -> dict[str, Decimal | str]:
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
            "external_updated_at": d["external_updated_at"],
        }  # fmt: skip

    def remaining(self) -> Decimal:
        return self.snapshot()["remaining"]  # type: ignore[return-value]

    def check(self, worst_case: Decimal, *, live: bool = True) -> None:
        """Raise `OverBudget` unless this call fits in both caps. A live call also needs a fresh `external_usd`."""
        s = self.snapshot()
        if worst_case > s["demo_room"]:
            raise OverBudget(
                "demo_cap",
                f"spent {s['askdata_spent']} of {s['demo_cap']}, worst case {worst_case}",
            )
        if worst_case > s["shared_room"]:
            raise OverBudget(
                "shared_cap", f"shared room {s['shared_room']}, worst case {worst_case}"
            )
        if live:
            age = self.clock() - datetime.strptime(str(s["external_updated_at"]), STAMP).replace(
                tzinfo=UTC
            )
            if age > self.max_external_age:
                raise OverBudget(
                    "external_stale", f"external_usd was set {s['external_updated_at']}"
                )

    def charge(self, amount: Decimal) -> Decimal:
        """Add `amount` to this project's spend; returns the new total."""
        if amount < 0:
            raise MeterError("negative charge")
        with self._locked():
            d = self._read()
            total = _dec(d["spent"][PROJECT], PROJECT) + amount
            d["spent"][PROJECT] = fmt_usd(total)
            self._write(d)
        return total

    def set_external(self, usd: Decimal) -> None:
        """Type in the spend of other programs (provider console). Stamps the time."""
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
