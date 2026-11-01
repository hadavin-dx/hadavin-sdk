"""Reservations with flood control enforced INSIDE the store, from its own rows, in the transaction that inserts.

A looping agent that files many valid proposals must not fill a cap with reservations nobody approved. `Reservations.reserve` counts the
tenant's open (younger than `since`) reservations per cluster and per sender and the not-yet-executed total in the currency, and refuses
with `PENDING_CAP` over the limits; a repeat of a held key is idempotent. A busy write lock is the typed `StoreBusy`, never a raw driver
error. `check_ordered_limits` validates a tier/cap table at start-up. This is the neutral reference implementation (stdlib sqlite3); a
client database implements the same two methods behind `ReservationStore` and runs `tests/test_promote_r8.py::contract`.
"""

from __future__ import annotations

import contextlib
import sqlite3
import threading
from collections.abc import Iterator
from typing import Protocol

SCHEMA = """CREATE TABLE IF NOT EXISTS reservations(tenant TEXT NOT NULL, key TEXT NOT NULL, subject TEXT NOT NULL, sender TEXT NOT NULL,
  currency TEXT NOT NULL, amount_minor INTEGER NOT NULL CHECK (amount_minor > 0), created_at TEXT NOT NULL, PRIMARY KEY (tenant, key))"""


class StoreBusy(Exception):
    """The write lock was not free within the timeout."""


class ReservationStore(Protocol):
    def reserve(
        self,
        tenant: str,
        key: str,
        cluster: list[str],
        sender: str,
        currency: str,
        amount_minor: int,
        at: str,
        since: str,
    ) -> str | None: ...

    def release(self, tenant: str, key: str) -> int: ...


class Reservations:
    def __init__(
        self,
        path: str = ":memory:",
        *,
        max_per_cluster: int,
        max_per_sender: int,
        share_cap_minor: dict[str, int],
        timeout_s: float = 30,
    ) -> None:
        self.max_cluster, self.max_sender, self.share = (
            max_per_cluster,
            max_per_sender,
            dict(share_cap_minor),
        )
        self._db = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None, timeout=timeout_s
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute(SCHEMA)
        self._mutex = threading.RLock()

    @contextlib.contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with self._mutex:
            try:
                self._db.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as e:
                raise StoreBusy(str(e)) from e
            try:
                yield self._db
            except BaseException:
                with contextlib.suppress(
                    sqlite3.Error
                ):  # a failing ROLLBACK must not replace the original error
                    self._db.execute("ROLLBACK")
                raise
            self._db.execute("COMMIT")

    def reserve(
        self,
        tenant: str,
        key: str,
        cluster: list[str],
        sender: str,
        currency: str,
        amount_minor: int,
        at: str,
        since: str,
    ) -> str | None:
        """None when held, "PENDING_CAP" when refused. `cluster` lists the subject ids of the identity cluster; the first is the subject."""
        with self._tx() as db:
            if db.execute(
                "SELECT 1 FROM reservations WHERE tenant=? AND key=?", (tenant, key)
            ).fetchone():
                return None
            n_cluster = sum(
                db.execute(
                    "SELECT COUNT(*) FROM reservations WHERE tenant=? AND created_at>=? AND subject=?",
                    (tenant, since, s),
                ).fetchone()[0]
                for s in sorted(set(cluster))
            )
            n_sender = db.execute(
                "SELECT COUNT(*) FROM reservations WHERE tenant=? AND created_at>=? AND sender=?",
                (tenant, since, sender),
            ).fetchone()[0]
            held = db.execute(
                "SELECT COALESCE(SUM(amount_minor),0) FROM reservations WHERE tenant=? AND currency=? AND created_at>=?",
                (tenant, currency, since),
            ).fetchone()[0]
            if (
                n_cluster >= self.max_cluster
                or n_sender >= self.max_sender
                or held + amount_minor > self.share.get(currency, 0)
            ):
                return "PENDING_CAP"
            db.execute(
                "INSERT INTO reservations VALUES(?,?,?,?,?,?,?)",
                (tenant, key, cluster[0], sender, currency, amount_minor, at),
            )
        return None

    def release(self, tenant: str, key: str) -> int:
        with self._tx() as db:
            return db.execute(
                "DELETE FROM reservations WHERE tenant=? AND key=?", (tenant, key)
            ).rowcount


def check_ordered_limits(tiers: dict[str, tuple[int, int, int, int]]) -> None:
    """Per currency `(one_approver_max, customer_cap, hard_cap, day_cap)`: positive ints (not bool) with
    one_approver_max <= customer_cap < hard_cap <= day_cap. Raises ValueError naming the first broken rule."""
    for cur, vals in tiers.items():
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in vals):
            raise ValueError(f"{cur}: every limit must be a positive int")
        a, b, c, d = vals
        if not a <= b < c <= d:
            raise ValueError(f"{cur}: need one_approver_max <= customer_cap < hard_cap <= day_cap")
