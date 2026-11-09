"""Worker functions for the process rows of the reservation proofs (ticket P4d, B4). They run in a `spawn`ed child
process (never fork), build their own store from a DSN, and report to the parent through a queue. No driver import:
the store comes from the factory like the application's own."""

import time
from datetime import date
from decimal import Decimal

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.store.protocol import SpendCapExceeded

DSN_NAME = "pg-dsn"  # the NAME the secrets kind looks up, not a secret


def _store(dsn):
    settings = PostgresSettings(
        kind="postgres", dsn_secret_name=DSN_NAME, lock_timeout_ms=60000, call_budget_ms=60000
    )
    return make("store", settings, FakeSecretProvider({DSN_NAME: dsn}))


def _pid(store):
    return store._exec("SELECT pg_backend_pid() AS p").fetchone()["p"]


def _reserve(store, rid, agent, day, amount, cap):
    return store.reserve_spend(
        rid,
        agent,
        date.fromisoformat(day),
        Decimal(amount),
        day_cap=cap,
        month_cap=None,
        run_id=None,
        run_cap=None,
    )


def race(dsn, agent, day, cap, amount, attempts, barrier, settle_gate, out, index):
    """Reserve `attempts` times against one cap, then settle every granted reservation at half its amount."""
    # an unexpected error ends the child with a non-zero exit code; the parent checks every exit code
    store = _store(dsn)
    out.put(("pid", index, _pid(store)))
    barrier.wait(120)
    granted, refused = [], 0
    for i in range(attempts):
        rid = f"proc-{index}-{i}"
        try:
            _reserve(store, rid, agent, day, amount, Decimal(cap))
            granted.append(rid)
        except SpendCapExceeded:
            refused += 1
    settle_gate.wait(
        120
    )  # nobody settles (and so frees room under the cap) before every attempt is made
    for rid in granted:
        store.settle_spend(rid, Decimal(amount) / 2)
    out.put(("done", index, granted, refused))


def blocked_reserve(dsn, agent, day, rid, out):
    """Report the backend pid first, then reserve (the parent holds a counter row, so this blocks)."""
    store = _store(dsn)
    out.put(("pid", 0, _pid(store)))
    _reserve(store, rid, agent, day, "1", None)
    out.put(("done", 0))


def reserve_then_hang(dsn, agent, day, rid, out):
    """Commit a reservation and then stop before reporting anything (the parent kills this process)."""
    store = _store(dsn)
    out.put(("pid", 0, _pid(store)))
    _reserve(store, rid, agent, day, "1", None)
    time.sleep(600)
