"""One server-wide gate for every test that runs `migrate` or the who-else check on a shared PostgreSQL.

Below PostgreSQL 16 `migrate` lists every non-superuser CREATEROLE login of the SERVER, so a test that makes one
(test_stop_state_roles.py) would make every other test's `migrate` with named roles refuse, in the same
pytest process or in another xdist worker. The gate is an advisory lock on the database of HADAVIN_TEST_PG_DSN:
every `migrate` call holds it SHARED for the whole call (tests/conftest.py wraps it for every test module, so no
module has to remember), and the one test that makes the server-wide role holds it EXCLUSIVE for as long as the
role exists. A migrate never waits for the gate while holding another lock: the lock is taken before it starts."""

from __future__ import annotations

import contextlib
import functools
import os

GATE = 7311
_exclusive_here = False  # this process holds the exclusive lock: its own migrate calls must not wait for it


def _connect():
    import psycopg

    return psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"], autocommit=True)


@contextlib.contextmanager
def shared():
    if not os.environ.get("HADAVIN_TEST_PG_DSN") or _exclusive_here:
        yield
        return
    with _connect() as db:  # closing the session releases the lock
        db.execute("SELECT pg_advisory_lock_shared(%s)", (GATE,))
        yield


@contextlib.contextmanager
def exclusive():
    global _exclusive_here
    with _connect() as db:
        db.execute("SELECT pg_advisory_lock(%s)", (GATE,))
        _exclusive_here = True
        try:
            yield
        finally:
            _exclusive_here = False


def gated(fn):
    @functools.wraps(fn)
    def run(*args, **kwargs):
        with shared():
            return fn(*args, **kwargs)

    return run
