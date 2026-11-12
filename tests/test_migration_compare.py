"""Server-free tests of the message helpers of `migrate`: the ownership check before the files, the cut list and the
lock-holder message. (The old before/after comparison and its tests are gone: `verify` judges the final state, see
tests/test_migration_verify.py and tests/test_migration_verify_pg.py.) No database: the rows a server would answer are
made up here, so each branch is shown with exactly the row that reaches it.
"""

from __future__ import annotations

import contextlib

import pytest
from psycopg import errors as pg_errors

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig


class _Result:
    def __init__(self, rows):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _Db:
    """Answers each query of the check with the made-up rows given for it (by the exact query text) and records every
    statement with its parameters."""

    def __init__(self, rows: dict[str, list[tuple]] | None = None):
        self.rows, self.log = rows or {}, []

    def execute(self, query, params=None):
        text = query if isinstance(query, str) else query.as_string(None)
        self.log.append((text, params))
        if text == "SELECT current_schema()":
            return _Result([("s",)])
        return _Result(self.rows.get(text, []))


def test_the_ownership_check_before_the_files_gets_the_relation_names_and_the_function_names_apart():
    """`_refuse_foreign_owned` asks about relations with the relation names and about functions with the function
    names. Killed by: mutants OA4 (the function half gets no names) and MC1 (it gets the relation names)."""
    db = _Db()
    text = "CREATE OR REPLACE FUNCTION audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;"
    mig._refuse_foreign_owned(db, "s", [text])
    ((schema_a, relations, schema_b, functions),) = [
        p for t, p in db.log if t == mig._FOREIGN_OWNED_SQL
    ]
    assert (schema_a, schema_b) == ("s", "s")
    assert functions == ["audit_guard"]
    assert set(relations) == set(mig.GRANTS) | {"schema_migrations"}


def test_a_long_list_is_cut_with_a_count_of_what_was_left_out():
    """A refusal lists at most `_PROBLEMS_SHOWN` things and then says how many more there are (it used to stop without
    a word). Killed by: mutant SH1 (the count is left out)."""
    items = [f"role_{i:02d}" for i in range(mig._PROBLEMS_SHOWN + 5)]
    shown = mig._shown(items)
    assert shown.endswith("; and 5 more") and shown.count("role_") == mig._PROBLEMS_SHOWN
    assert mig._shown(["a", "b"]) == "a; b" and mig._shown([]) == ""
    assert mig._shown(["a", "b", "c"], ", ", limit=2) == "a, b, and 1 more"
    assert mig._shown(iter(["a", "b"]), limit=2) == "a; b"


# --- who holds the migration lock ----------------------------------------------------------------------------------------


class _LockDb(_Db):
    """A connection on which the wait for the migration lock runs out."""

    def transaction(self):
        return contextlib.nullcontext()

    def execute(self, query, params=None):
        if isinstance(query, str) and query.startswith("SELECT pg_advisory_xact_lock"):
            self.log.append((query, params))
            raise pg_errors.LockNotAvailable("made up: the wait ran out")
        return super().execute(query, params)


def test_a_lock_held_by_a_prepared_transaction_is_said_so_with_what_finishes_it():
    """No session holds the lock, and a lock row without a session exists: a prepared transaction holds it. The message
    says so, lists the prepared transactions of the database and the two statements that finish one, and does not tell
    the reader to end a session (there is none). Killed by: mutant LW8 (a lock without a session is not looked for)."""
    db = _LockDb(
        {
            mig._LOCK_HOLDER_SQL: [],
            mig._LOCK_PREPARED_SQL: [(1,)],
            mig._PREPARED_SQL: [("nightly\nbatch", "etl", "2026-01-01 00:00:00+00")],
        }
    )
    with pytest.raises(ConfigError, match="a prepared transaction holds it") as e:
        mig._take_the_lock(db, 3)
    text = str(e.value)
    assert "migrate waited 3 seconds for the migration lock and gave up" in text
    assert "nightly\\nbatch" in text and "\n" not in text, (
        "a control character is written as an escape"
    )
    assert "(owner etl, prepared 2026-01-01 00:00:00+00)" in text
    assert "ROLLBACK PREPARED" in text and "COMMIT PREPARED" in text
    assert "Nothing was changed." in text and "pg_terminate_backend" not in text


@pytest.mark.parametrize("prepared", [[], [(0,)]])
def test_a_lock_holder_that_cannot_be_seen_at_all_is_still_called_a_session_this_login_cannot_see(
    prepared,
):
    """No session row and no lock row without a session: the old words stay. Pin."""
    db = _LockDb({mig._LOCK_HOLDER_SQL: [], mig._LOCK_PREPARED_SQL: prepared})
    with pytest.raises(ConfigError, match="a session this login cannot see holds it") as e:
        mig._take_the_lock(db, 3)
    assert "prepared transaction" not in str(e.value)
    assert mig._PREPARED_SQL not in [t for t, _ in db.log]
