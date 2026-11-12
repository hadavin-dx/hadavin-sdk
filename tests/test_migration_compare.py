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


def _prepared_db(rows):
    return _LockDb({mig._LOCK_HOLDER_SQL: [], mig._LOCK_PREPARED_SQL: [(1,)], mig._PREPARED_SQL: rows})


def test_a_lock_held_by_a_prepared_transaction_is_said_so_with_what_finishes_it():
    """No session holds the lock, and a lock row without a session exists: a prepared transaction holds it. The message
    says so, names THE transaction (the query of ticket 6.1 returns one row), gives the two statements that finish it and
    does not tell the reader to end a session (there is none). Killed by: mutant LW8 (a lock without a session is not
    looked for)."""
    db = _prepared_db([("nightly\nbatch", "etl", "2026-01-01 00:00:00+00")])
    with pytest.raises(ConfigError, match="a prepared transaction holds it") as e:
        mig._take_the_lock(db, 3)
    text = str(e.value)
    assert "migrate waited 3 seconds for the migration lock and gave up" in text
    assert "nightly\\nbatch" in text and "\n" not in text, (
        "a control character is written as an escape"
    )
    assert "(owner etl, prepared 2026-01-01 00:00:00+00)" in text
    assert "THAT one" in text and "do not finish any other" in text
    assert "ROLLBACK PREPARED '<its name>'" in text, "a name with a control character is never printed as a statement"
    assert "Nothing was changed." in text and "pg_terminate_backend" not in text
    assert (mig._PREPARED_SQL, (mig.MIGRATE_LOCK,)) in db.log, "the key of the lock goes to the query"


def test_a_plain_name_of_the_prepared_transaction_goes_into_the_printed_statements():
    db = _prepared_db([("nightly-1", "etl", "2026-01-01 00:00:00+00")])
    with pytest.raises(ConfigError) as e:
        mig._take_the_lock(db, 3)
    assert "ROLLBACK PREPARED 'nightly-1' or COMMIT PREPARED 'nightly-1'" in str(e.value)


def test_two_prepared_transactions_that_could_hold_the_lock_are_all_named_and_none_is_picked():
    """Two prepared transactions can carry the same virtual id: the server does not tell them apart, so every one is
    named and the message says to ask the owners. Killed by: mutant V75 (a list of several prepared transactions is not named)."""
    db = _prepared_db(
        [("first", "etl", "2026-01-01 00:00:00+00"), ("second", "bob", "2026-01-02 00:00:00+00")]
    )
    with pytest.raises(ConfigError) as e:
        mig._take_the_lock(db, 3)
    text = str(e.value)
    assert "One of these prepared transactions holds it" in text and "THAT one" not in text
    assert "'first' (owner etl" in text and "'second' (owner bob" in text
    assert "ask their owners" in text and "Nothing was changed." in text


def test_a_prepared_lock_with_no_visible_prepared_transaction_says_so():
    db = _prepared_db([])
    with pytest.raises(ConfigError) as e:
        mig._take_the_lock(db, 3)
    assert "This login cannot see which prepared transaction it is" in str(e.value)
    assert "Nothing was changed." in str(e.value)


@pytest.mark.parametrize("failing", ["holder", "prepared_count", "prepared_names"])
def test_an_unreadable_lock_view_is_a_plain_config_error_whichever_query_fails(failing):
    """Ticket 6.2: a driver error from any of the three reads inside the handler is a ConfigError (exit 2, nothing
    changed), never a raw driver error. Killed by: mutant V73 (the driver error is not caught)."""
    texts = {
        "holder": mig._LOCK_HOLDER_SQL,
        "prepared_count": mig._LOCK_PREPARED_SQL,
        "prepared_names": mig._PREPARED_SQL,
    }

    class Failing(_LockDb):
        def execute(self, query, params=None):
            if query == texts[failing]:
                raise pg_errors.InsufficientPrivilege("permission denied for view pg_stat_activity\nsecond line")
            return super().execute(query, params)

    db = Failing({mig._LOCK_HOLDER_SQL: [], mig._LOCK_PREPARED_SQL: [(1,)], mig._PREPARED_SQL: []})
    outcome = None
    try:
        mig._take_the_lock(db, 3)
    except Exception as exc:  # judged below, outside the handler, so a failure is an assertion and not a chain
        outcome = exc
    assert isinstance(outcome, ConfigError), f"expected the refusal, got {outcome!r}"
    text = str(outcome)
    assert "could not read who holds it" in text
    assert "migrate waited 3 seconds for the migration lock and gave up" in text
    assert "permission denied for view pg_stat_activity" in text and "\n" not in text
    assert "Nothing was changed." in text


def test_the_name_of_the_session_that_holds_the_lock_is_written_without_control_characters():
    """`usename` and `application_name` are chosen by the other session: a newline or an escape in them is written as
    an escape (ticket 6.2). Killed by: mutant V74 (the user name goes in without the escape)."""
    db = _LockDb({mig._LOCK_HOLDER_SQL: [(4242, "bo\nb", "app\x1b[2J", "idle", "2026-01-01 00:00:00+00")]})
    with pytest.raises(ConfigError) as e:
        mig._take_the_lock(db, 3)
    text = str(e.value)
    assert "\n" not in text and "\x1b" not in text
    assert "process 4242" in text and "bo" in text


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
