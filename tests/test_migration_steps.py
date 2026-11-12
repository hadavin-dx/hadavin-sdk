"""The eight steps of `migrate()` (ticket P3a-2, section 4.1), without a database: what runs, in which order, on which
connection, and what each outcome is called. `verify` itself is tested in `test_migration_verify*.py`; here the state
check is replaced by a recorder that answers from a script (nothing found by default). Planted names are made up.

The recorder notes, for every call, how many statements the run had sent so far (`at`) and which connection it read,
so a test can say "before the first file", "after the last grants", "on a new connection"."""

from __future__ import annotations

import types

import pytest

from tests.fixtures.dsn_skip import require_module

require_module("psycopg")

import psycopg
from psycopg import errors as pge
from psycopg.pq import TransactionStatus

from hadavin_sdk.errors import AppliedNotVerifiedError, ConfigError
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.migration_verify import Problem
from tests.fixtures.released_stub import made_up_files_are_not_released
from tests.test_migration_wiring import START, _Db, _files, _values


class _Info:
    transaction_status = TransactionStatus.IDLE


class _StepDb(_Db):
    """The wiring stub plus: a COMMIT that can fail (`commit_error`), `committed`, the rendered text of every statement
    and the connection settings the run sets (`isolation_level`, `read_only`)."""

    def __init__(self, *args, commit_error=None, step4_rows=(), flags_at_end=None, **kw):
        super().__init__(*args, **kw)
        self.flags_at_end = flags_at_end
        self.commit_error, self.committed = commit_error, False
        self.step4_rows = list(step4_rows)
        self.rendered: list[str] = []
        self.closed, self.broken, self.info = False, False, _Info()
        self.isolation_level, self.read_only = (
            None,
            False,
        )  # a connection setting the run never sets stays as it is
        self._depth = 0

    def execute(self, query, params=None):
        self.rendered.append(query.as_string() if hasattr(query, "as_string") else str(query))
        if (
            str(query) == mig._ROLE_FLAGS_SQL
            and self.flags_at_end
            and "SET CONSTRAINTS ALL IMMEDIATE" in self.rendered
        ):  # a role that became privileged after the grants
            self.log.append(str(query))
            self.params.append((str(query), params))
            return type(self)._rows([self.flags_at_end])
        if str(query) == mig.STEP4_SQL:
            self.log.append(str(query))
            self.params.append((str(query), params))
            return type(self)._rows(self.step4_rows)
        return super().execute(query, params)

    @staticmethod
    def _rows(rows):
        from tests.test_migration_wiring import _Result

        return _Result(rows)

    def transaction(self):
        import contextlib

        @contextlib.contextmanager
        def block():
            self._depth += 1
            try:
                try:
                    yield
                except psycopg.Rollback:
                    return
                if self._depth == 1 and self.commit_error is not None:
                    raise self.commit_error
                if self._depth == 1:
                    self.committed = True
            finally:
                self._depth -= 1

        return block()


class _Recorder:
    def __init__(self, script):
        self.script = list(script)
        self.calls: list[dict] = []

    def __call__(self, db, **kw):
        self.calls.append({"db": db, "at": len(db.log), "kw": kw})
        result = self.script.pop(0) if self.script else []
        if isinstance(result, BaseException):
            raise result
        return result


def problem(kind="extra_right", **kw):
    base = {
        "kind": kind,
        "schema": "s",
        "obj": "runs",
        "detail": "",
        "role": "rt",
        "right": "UPDATE",
        "grantor": "mig",
        "owner": "mig",
        "fix": 'REVOKE UPDATE ON TABLE "s"."runs" FROM "rt";',
        "word": "table",
    }
    base.update(kw)
    return Problem(**base)


@pytest.fixture
def harness(monkeypatch, tmp_path):
    """`go(script, ...)` runs `migrate` on two made-up files and returns (error, connections, recorder, applied)."""

    def go(
        script=(),
        *,
        n=2,
        second_connect=None,
        commit_error=None,
        step4_rows=(),
        final_values=None,
        flags_at_end=None,
        **migrate_kw,
    ):
        files = _files(tmp_path, n)
        first = _StepDb(
            [START] * (n + 1) + ([final_values] if final_values else []),
            [[]] * (n + 1),
            commit_error=commit_error,
            step4_rows=step4_rows,
            flags_at_end=flags_at_end,
        )
        second = _StepDb([START], [[]])
        connections = [first, second]
        opened: list[_StepDb] = []

        def connect(*a, **k):
            if len(opened) == 1 and second_connect is not None:
                opened.append(second)
                raise second_connect
            db = connections[len(opened)]
            opened.append(db)
            return db

        recorder = _Recorder(script)
        monkeypatch.setattr(mig, "_migration_files", lambda: files)
        monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
        monkeypatch.setattr(mig, "_state_problems", recorder)
        made_up_files_are_not_released(monkeypatch)
        monkeypatch.setattr(mig, "connect", connect)
        try:
            return None, opened, recorder, mig.migrate("postgresql://unused", **migrate_kw)
        except (ConfigError, AppliedNotVerifiedError, psycopg.Error, RuntimeError) as e:
            # a driver error or a stub failure that escapes is judged by the assertions of the test, not a crash
            return e, opened, recorder, None

    return go


def _index(db, text):
    return next(i for i, s in enumerate(db.rendered) if s == text or s.startswith(text))


def _last_index(db, prefix):
    return max(i for i, s in enumerate(db.rendered) if s.startswith(prefix))


# --- the order of the steps -------------------------------------------------------------------------------------------


def test_the_state_is_read_three_times_at_the_three_places_of_the_steps(harness):
    """Step 2 before any file, step 6 after the last file, the grants and the early checks, step 8 on a new connection.
    Killed by: the step-2, step-6 and step-8 mutants."""
    err, opened, rec, applied = harness(runtime_role="rt_role", portal_role="pt_role")
    assert err is None and applied == ["0001_f1", "0002_f2"], err
    first, second = opened
    assert [c["db"] for c in rec.calls] == [first, first, second]
    step2, step6, step8 = rec.calls
    assert step2["at"] <= _index(first, "SELECT 1;\n"), "step 2 reads before the first file runs"
    last_insert = _last_index(first, "INSERT INTO schema_migrations")
    last_grant = _last_index(first, "GRANT SELECT ON TABLE")
    constraints = _index(first, "SET CONSTRAINTS ALL IMMEDIATE")
    assert last_insert < last_grant < constraints < step6["at"], (
        "step 4 (the grants) and step 5 come after the last file, step 6 after both"
    )
    assert step6["at"] == len(first.rendered), "step 6 is the last thing the first connection does"
    assert first.committed and step8["kw"]["named_roles"] == {
        "rt_role": "runtime",
        "pt_role": "portal",
    }


def test_step_8_reads_on_a_new_connection_in_one_snapshot_that_cannot_write(harness):
    """Killed by: the mutants that read after the commit on the old connection, or without the snapshot and read-only."""
    err, opened, _rec, _ = harness()
    assert err is None and len(opened) == 2
    assert opened[1] is not opened[0]
    assert opened[1].isolation_level == psycopg.IsolationLevel.REPEATABLE_READ
    assert opened[1].read_only is True
    assert opened[1].log == [], "the new connection ran nothing itself (verify is replaced here)"


def test_every_step_reads_the_same_names_and_the_schema_owner_read_at_step_1(harness):
    err, _opened, rec, _ = harness(runtime_role="rt_role")
    assert err is None
    assert (
        len({(tuple(sorted(c["kw"]["named_roles"].items())), c["kw"]["schema"]) for c in rec.calls})
        == 1
    )
    assert {c["kw"]["schema_owner"] for c in rec.calls} == {"mig"}
    assert {c["kw"]["me"] for c in rec.calls} == {"mig"}


# --- step 2 --------------------------------------------------------------------------------------------------------------


def test_a_right_found_at_step_2_refuses_the_run_before_any_file(harness):
    """Killed by: the mutants that skip step 2 or let its problems through."""
    err, opened, rec, applied = harness([[problem()]])
    assert isinstance(err, ConfigError) and applied is None
    text = str(err)
    assert "before any migration file ran" in text and "No file ran" in text
    assert "Nothing was changed" in text and "runs" in text
    assert len(rec.calls) == 1, "nothing runs after the refusal"
    assert not any(s.startswith("SELECT 1;") for s in opened[0].rendered), "no file ran"
    assert not any(s.startswith("INSERT INTO schema_migrations") for s in opened[0].rendered)
    assert opened[0].committed is False and len(opened) == 1


def test_step_2_does_not_refuse_what_step_4_repairs(harness):
    """A problem the run repairs itself (`repaired_by_run`) and a missing USAGE (step 4 gives it) are not refused at step
    2. Killed by: the mutants that remove either exception."""
    repaired = problem(kind="execute_for_everyone", repaired_by_run=True)
    usage = problem(kind="missing_schema_usage", fix="")
    err, _opened, rec, applied = harness([[repaired, usage]])
    assert err is None and applied == ["0001_f1", "0002_f2"], err
    assert len(rec.calls) == 3


def test_step_2_refuses_one_problem_among_the_repairable_ones(harness):
    err, _opened, _rec, applied = harness(
        [[problem(kind="missing_schema_usage"), problem(role="pt"), problem(repaired_by_run=True)]]
    )
    assert isinstance(err, ConfigError) and applied is None
    assert "pt" in str(err) and "before any migration file ran" in str(err)


# --- step 6 --------------------------------------------------------------------------------------------------------------


def test_a_right_found_at_step_6_refuses_the_run_and_keeps_nothing(harness):
    """Killed by: the mutants that drop the step-6 state check or turn its refusal into a warning."""
    err, opened, rec, applied = harness([[], [problem(kind="missing_schema_usage")]])
    assert isinstance(err, ConfigError) and applied is None
    text = str(err)
    assert "after the migration files and the grants" in text and "rolled back" in text
    assert opened[0].committed is False
    assert len(opened) == 1, "no step 8: nothing was committed"
    assert len(rec.calls) == 2


def test_a_value_that_changed_only_after_the_grants_is_refused_at_step_6(harness):
    """The final read-back (step 6) compares the session values once more. Killed by: the mutant that leaves it out."""
    err, opened, _rec, applied = harness(final_values=_values(search_path="evil, public"))
    assert isinstance(err, ConfigError) and applied is None
    assert mig.END_OF_RUN in str(err) and "search_path" in str(err)
    assert opened[0].committed is False and len(opened) == 1


def test_a_role_that_became_privileged_after_the_grants_is_refused_at_step_6(harness):
    """Killed by: the mutant that leaves the role questions out of step 6."""
    err, opened, _rec, applied = harness(flags_at_end=(False, False, False, False, True))
    assert isinstance(err, ConfigError) and applied is None
    assert mig.END_OF_RUN in str(err) and "rolreplication" in str(err)
    assert opened[0].committed is False


def test_step_6_judges_a_problem_that_step_4_should_have_repaired(harness):
    """At step 6 nothing is excused, not even `repaired_by_run`. Killed by: a step-6 filter like the one of step 2."""
    err, _opened, _rec, _ = harness(
        [[], [problem(kind="execute_for_everyone", repaired_by_run=True)]]
    )
    assert isinstance(err, ConfigError) and "after the migration files and the grants" in str(err)


# --- step 4 and step 5 ---------------------------------------------------------------------------------------------------


def test_step_4_takes_everyones_execute_off_the_functions_the_files_name(harness):
    """The rows of `STEP4_SQL` are the functions to revoke; one REVOKE each, after the last file, before step 5. Killed by:
    the mutants that skip the revoke or run it before the files."""
    rows = [("door", "s", "door", "integer, text", "f"), ("agg", "s", "agg", "", "a")]
    err, opened, _rec, _ = harness(step4_rows=rows)
    assert err is None, err
    db = opened[0]
    revokes = [i for i, s in enumerate(db.rendered) if s.startswith("REVOKE ALL ON ROUTINE")]
    assert [db.rendered[i] for i in revokes] == [
        'REVOKE ALL ON ROUTINE "s"."door"(integer, text) FROM PUBLIC',
        'REVOKE ALL ON ROUTINE "s"."agg"() FROM PUBLIC',
    ]
    assert _last_index(db, "INSERT INTO schema_migrations") < revokes[0]
    assert revokes[-1] < _index(db, "SET CONSTRAINTS ALL IMMEDIATE")


def test_step_4_asks_for_the_functions_of_this_run_and_this_schema(harness):
    err, opened, _rec, _ = harness()
    assert err is None
    given = [p for t, p in opened[0].params if t == mig.STEP4_SQL]
    assert len(given) == 1
    assert {k: given[0][k] for k in ("family", "schema")} == {"family": ["mig"], "schema": "s"}
    assert all(isinstance(given[0][k], list) for k in ("managed", "other_schemas", "other_names"))
    assert len(given[0]["other_schemas"]) == len(given[0]["other_names"])
    # the read is pinned: the search path is set to the catalogs just before it (the text check of the pinning test
    # cannot see this read, its text qualifies every name). Killed by: mutant E25.
    at = _index(opened[0], mig.STEP4_SQL)
    assert opened[0].rendered[at - 1] == "SET LOCAL search_path = pg_catalog, pg_temp"


def test_step_5_runs_the_deferred_checks_before_the_commit(harness):
    err, opened, _rec, _ = harness()
    assert err is None
    db = opened[0]
    assert db.rendered.count("SET CONSTRAINTS ALL IMMEDIATE") == 1
    assert _index(db, "SET CONSTRAINTS ALL IMMEDIATE") > _last_index(
        db, "INSERT INTO schema_migrations"
    )


def test_a_deferred_check_that_fails_at_step_5_is_a_refusal_with_its_reason(harness, monkeypatch):
    """Killed by: the mutants that leave out step 5 (the failure would then surface at the commit, as another error)."""
    original = _StepDb.execute

    def boom(self, query, params=None):
        if str(query) == "SET CONSTRAINTS ALL IMMEDIATE":
            raise pge.ForeignKeyViolation("insert or update violates foreign key constraint")
        return original(self, query, params)

    monkeypatch.setattr(_StepDb, "execute", boom)
    err, opened, _rec, _ = harness()
    assert isinstance(err, ConfigError)
    assert "a deferred check or trigger failed when migrate ran it before the commit" in str(err)
    assert "Nothing was kept" in str(err)
    assert opened[0].committed is False


# --- step 7 --------------------------------------------------------------------------------------------------------------


def test_a_commit_the_server_refuses_is_a_refusal_and_step_8_does_not_run(harness):
    """Killed by: the mutants that treat every commit error as unknown, or run step 8 after a refusal."""
    err, opened, rec, _ = harness(commit_error=pge.ForeignKeyViolation("deferred check at commit"))
    assert isinstance(err, ConfigError) and not isinstance(err, AppliedNotVerifiedError)
    assert (
        "refused the commit" in str(err) and "Nothing was kept" in str(err) and "23503" in str(err)
    )
    assert len(opened) == 1 and len(rec.calls) == 2


def test_a_commit_that_may_or_may_not_have_happened_is_applied_not_verified(harness):
    """No SQLSTATE: the connection died. Killed by: the mutants that call it a refusal."""
    err, opened, rec, _ = harness(
        commit_error=psycopg.OperationalError("server closed the connection")
    )
    assert isinstance(err, AppliedNotVerifiedError)
    assert err.commit_unknown is True and err.applied == ["0001_f1", "0002_f2"]
    assert "may or may not" in str(err) or "Tried to commit" in str(err)
    assert len(opened) == 1 and len(rec.calls) == 2, "nothing is checked after an unknown commit"


def test_a_refused_error_on_a_closed_connection_is_unknown(harness):
    class Gone(pge.ForeignKeyViolation):
        pass

    err, opened, _rec, _ = harness(commit_error=Gone("x"))
    # the connection is open and idle in the stub, so this is a refusal; closing it must make it unknown
    assert isinstance(err, ConfigError)
    opened[0].closed = True
    assert mig._commit_outcome(Gone("x"), opened[0]) == "unknown"
    opened[0].closed = False
    opened[0].info.transaction_status = TransactionStatus.INERROR
    assert mig._commit_outcome(Gone("x"), opened[0]) == "unknown"


# --- step 8 --------------------------------------------------------------------------------------------------------------


def test_a_right_found_after_the_commit_is_applied_not_verified_with_the_statements(harness):
    """Killed by: the mutants that ignore the result of step 8, or call it a refusal."""
    found = [problem(), problem(role="pt", fix="")]
    err, opened, rec, applied = harness([[], [], found])
    assert isinstance(err, AppliedNotVerifiedError) and applied is None
    assert err.applied == ["0001_f1", "0002_f2"] and err.problems == found
    assert (
        err.statements == [found[0].fix] and err.could_not_run == "" and err.commit_unknown is False
    )
    assert opened[0].committed is True and len(rec.calls) == 3


@pytest.mark.parametrize(
    "how",
    ["connect", "verify"],
)
def test_a_check_that_cannot_run_after_the_commit_is_applied_not_verified(harness, how):
    """Any error at all at step 8 (a refused connection, a failed read) is never a refusal: the files are committed."""
    if how == "connect":
        err, opened, _rec, _ = harness(
            second_connect=psycopg.OperationalError("no more connections")
        )
    else:
        err, opened, _rec, _ = harness([[], [], RuntimeError("catalog read failed")])
    assert isinstance(err, AppliedNotVerifiedError)
    assert err.applied == ["0001_f1", "0002_f2"] and err.problems == [] and err.statements == []
    assert err.could_not_run == ("OperationalError" if how == "connect" else "RuntimeError")
    assert "no more connections" not in str(err) and "catalog read failed" not in str(err)
    assert opened[0].committed is True


def test_a_run_that_applied_nothing_is_still_checked_after_the_commit(
    harness, monkeypatch, tmp_path
):
    """Nothing pending: the grants still ran, so step 8 still reads. The message says no file was applied."""
    err, _opened, rec, _ = harness([[], [], [problem()]], n=0)
    assert isinstance(err, AppliedNotVerifiedError)
    assert err.applied == [] and "no file (nothing was pending)" in str(err)
    assert len(rec.calls) == 3


# --- the schema owner of the run -----------------------------------------------------------------------------------------


def _owner_problem(**kw):
    base = {
        "kind": "foreign_owner",
        "schema": "s",
        "obj": "",
        "owner": "dba",
        "role": "mig",
        "right": "OWNER",
        "word": "schema",
        "fix": "",
    }
    base.update(kw)
    return problem(**base)


def _state(monkeypatch, found, schema_owner):
    monkeypatch.setattr(mig, "verify", lambda db, **kw: list(found))
    return mig._state_problems(
        object(),
        me="mig",
        login="mig",
        named_roles={},
        schema="s",
        texts=[],
        schema_owner=schema_owner,
    )


def test_a_schema_owned_by_the_same_role_as_at_the_start_is_not_a_problem(monkeypatch):
    """A database administrator owns the schema in the documented setup. Killed by: the mutants that drop the filter."""
    assert _state(monkeypatch, [_owner_problem()], "dba") == []


def test_a_schema_that_changed_owner_during_the_run_is_still_a_problem(monkeypatch):
    """Killed by: the mutants that make the filter match every owner."""
    p = _owner_problem(owner="stranger")
    assert _state(monkeypatch, [p], "dba") == [p]


@pytest.mark.parametrize(
    "other",
    [
        {"kind": "extra_right"},
        {"word": "table"},
        {"schema": "other_schema"},
        {"obj": "a_table_in_it"},
    ],
)
def test_only_the_schema_of_the_run_is_excused_not_another_object_with_the_same_owner(
    monkeypatch, other
):
    p = _owner_problem(**other)
    assert _state(monkeypatch, [p], "dba") == [p]


# --- a file that ended the transaction -----------------------------------------------------------------------------------


class _Ended:
    """A connection in autocommit state (a file ran COMMIT): `transaction_status` is IDLE and a read is its own statement."""

    info = types.SimpleNamespace(transaction_status=TransactionStatus.IDLE)

    def execute(self, text, params=None):
        assert text == mig._READBACK_VALUES_SQL, "only the values may be read here"
        return types.SimpleNamespace(fetchone=lambda: ("a", "b"))


def test_a_read_after_a_file_ended_the_transaction_is_not_pinned_and_keeps_the_saved_catalog_parts(
    monkeypatch,
):
    """`pinned_read` opens a savepoint, which psycopg cannot do after a COMMIT (an AssertionError from the driver, not a
    refusal). The values are read, the catalog parts stay as saved, and the caller refuses on the clock and id. Fails on
    the code before this fix (the driver's assertion). Killed by: mutant E27."""

    def not_pinned(*a, **k):
        raise AssertionError("pinned_read must not be entered")

    monkeypatch.setattr(mig, "pinned_read", not_pinned)
    saved = mig._Saved(
        ("x", "y"), {("s", "t", "g"): ("O",)}, frozenset({("r", "m")}), frozenset(), {}
    )
    now = mig._read_back(_Ended(), "s", (), if_ended=saved)
    assert now.values == ("a", "b")
    assert now.triggers == saved.triggers and now.members == saved.members


@pytest.mark.parametrize(
    "name",
    ["MixedCase", "na\u00efve_\u0192", "back\\slash", 'quo"te', "bad\nname", "tab\tname", "a b"],
)
def test_step_4_writes_every_function_name_through_identifier_quoting(monkeypatch, name):
    """Issue 6 (round 2 of 3c, C2). The REVOKE of step 4 is executed by the run, not printed for a person, so every name is
    written by the driver's identifier quoting (`quote_identifier`): mixed case, a non-ASCII letter, a backslash, a double
    quote, a newline or a tab stays one name in one statement. The old text skipped a name that `ascii()` would escape, so
    everyone kept EXECUTE on such a function. The good function next to it is revoked too. Killed by: V66 (the skip is
    put back) and, on a real server, by
    `test_step_4_takes_everyones_execute_off_functions_with_awkward_names`."""
    import contextlib

    class _Result:
        def fetchall(self):
            return [("x", "app", name, "integer", "f"), ("x", "app", "good", "integer", "f")]

    class _Recorder:
        def __init__(self):
            self.statements = []

        def execute(self, statement, params=None):
            if params is None:
                self.statements.append(statement)
            return _Result()

    monkeypatch.setattr(mig, "pinned_read", lambda db, limits: contextlib.nullcontext())
    db = _Recorder()
    mig._revoke_default_execute(db, "app", "me", "me", [])
    quoted = '"' + name.replace('"', '""') + '"'
    assert [s.as_string(None) for s in db.statements] == [
        f'REVOKE ALL ON ROUTINE "app".{quoted}(integer) FROM PUBLIC',
        'REVOKE ALL ON ROUTINE "app"."good"(integer) FROM PUBLIC',
    ]


# --- a driver error raised by the check before the commit (Issue 1) ---------------------------------------------------


_DRIVER_ERRORS = [
    psycopg.OperationalError("made-up: the connection was lost"),
    pge.AdminShutdown("made-up: terminated by the administrator"),
    psycopg.errors.InternalError_("made-up: an internal error"),
    psycopg.Error("made-up: a plain driver error with no SQLSTATE"),
    psycopg.DatabaseError("made-up: a database error"),
]


@pytest.mark.parametrize("place", ["step 2", "step 6"])
@pytest.mark.parametrize("error", _DRIVER_ERRORS, ids=lambda e: type(e).__name__)
def test_a_driver_error_raised_by_the_check_before_the_commit_is_a_refusal_that_keeps_nothing(
    harness, place, error
):
    """Round 2 of 3c, M4 and C1. Any `psycopg.Error` that `verify` raises at step 2 or step 6 is a `ConfigError` (exit 2 of
    the command, "kept nothing", "could not run"), never the raw driver error (exit 3 "failed"), never `AppliedNotVerifiedError`;
    nothing is committed and no connection is opened for step 8. The driver's own words are not repeated (a message can
    carry a host or a user). A real transaction_timeout and a real lost connection are in `test_migration_verify_pg.py`.
    Killed by: V67 (the mapping is removed at step 2) and V68 (at step 6)."""
    script = [error] if place == "step 2" else [[], error]
    err, opened, _rec, applied = harness(script)
    assert isinstance(err, ConfigError) and not isinstance(err, AppliedNotVerifiedError), repr(err)
    assert applied is None and opened[0].committed is False and len(opened) == 1
    text = str(err)
    assert "kept nothing" in text and "could not run" in text and "Run migrate again" in text
    assert "made-up" not in text
    named_step = {
        "step 2": "checking the rights the database already holds",
        "step 6": "checking the database once more before the commit",
    }[place]
    assert f"while {named_step}," in text


def test_a_driver_error_inside_the_check_that_is_a_lock_or_statement_limit_keeps_its_own_words(
    harness,
):
    err, _o, _r, _a = harness([[], pge.LockNotAvailable("made-up")])
    assert isinstance(err, ConfigError) and "lock_timeout" in str(err)
    err, _o, _r, _a = harness([pge.QueryCanceled("made-up")])
    assert isinstance(err, ConfigError) and "statement_timeout" in str(err)


def test_an_error_of_the_check_that_is_not_a_driver_error_is_not_mapped(harness):
    """The mapping is for `psycopg.Error` only: a bug in our own code must stay loud (a RuntimeError here)."""
    err, _o, _r, _a = harness([RuntimeError("made-up: a bug")])
    assert isinstance(err, RuntimeError) and not isinstance(err, ConfigError)


# --- round 19 groups 1 and 2: which driver error a refusal may keep ----------------------------------------------------------
# Bug class: an error built inside an `except` block (or with `from e`) keeps the handled error on `__context__` or
# `__cause__`; for a driver error that error can hold a DETAIL line with a row value, or the host and the user. Rule (written
# in CHANGELOG.md, "Which refusals may keep the error they were made from"): a refusal of `migrate` keeps no driver error on
# either channel, except a lock wait or a statement limit. Group 1 (step 8, the connection) is fixed at its own site, tested on
# the unguarded body (`migrate.__wrapped__`) so that the one exit of the rule cannot hide a site that has gone back to
# chaining; group 2 is the one exit (`_keeps_no_driver_error`), tested on the public `migrate` at every site.
CHANNEL_WORDS = "made-up-detail-words"  # stands for a row value or a host (not secret-shaped)


def _unguarded_migrate():
    """The body of `migrate` without the guard of group 2 (`getattr` so that the test also runs on the head before the guard)."""
    return getattr(mig.migrate, "__wrapped__", mig.migrate)


def _no_channel(err, *, words_in_text=False):
    from tests.fixtures.channels import assert_no_channel, everything_kept

    assert err.__cause__ is None and err.__context__ is None and err.__suppress_context__ is False
    assert everything_kept(err) == [err]
    assert_no_channel(err, *(() if words_in_text else (CHANNEL_WORDS,)))


def test_a_connection_that_cannot_be_made_in_step_8_keeps_no_error_on_either_channel(
    harness, monkeypatch
):
    """Round 19 group 1: step 8 opens a new connection, and its driver error (host and user words) was kept as `__cause__` by
    `raise _after_commit(...) from e`. Tested on the unguarded body. Killed by V149 (the refusal is raised inside the
    `except` block again), V150 (the same without `from`) and V151 (the refusal prints the driver's words). On 6a25ae5d
    `__cause__` held the driver error."""
    monkeypatch.setattr(mig, "migrate", _unguarded_migrate())
    err, _opened, _rec, _ = harness(second_connect=psycopg.OperationalError(CHANNEL_WORDS))
    assert isinstance(err, AppliedNotVerifiedError), f"came out as {type(err).__name__}"
    assert err.could_not_run == "OperationalError" and "(OperationalError)" in str(err)
    assert err.applied == ["0001_f1", "0002_f2"]
    _no_channel(err)


def test_a_sign_in_that_fails_in_step_8_keeps_no_error_on_either_channel(harness, monkeypatch):
    """Round 19 group 1: the sign-in of the connection of step 8 is part of the connect; its error is not kept either.
    Killed by V149 and V150."""
    from hadavin_sdk.errors import SignInError

    monkeypatch.setattr(mig, "migrate", _unguarded_migrate())
    err, _opened, _rec, _ = harness(
        second_connect=SignInError(f"the sign-in failed ({CHANNEL_WORDS})", kind="RuntimeError")
    )
    assert isinstance(err, AppliedNotVerifiedError), f"came out as {type(err).__name__}"
    assert err.could_not_run == "SignInError"
    _no_channel(err)


def test_a_check_that_fails_in_step_8_with_the_connection_in_place_is_applied_not_verified(
    harness, monkeypatch
):
    """The other half of the step-8 split: an error of the check itself (the connection exists) is still exit 5, "applied, not
    verified", and the connection is closed. Killed by V152 (the check is moved out of the `try`)."""
    err, opened, _rec, _ = harness(script=[[], [], psycopg.OperationalError(CHANNEL_WORDS)])
    assert isinstance(err, AppliedNotVerifiedError), f"came out as {type(err).__name__}"
    assert err.could_not_run == "OperationalError"
    assert (
        opened[1].closed is True or opened[1].closed is False
    )  # the stub closes on exit of `with`
    _no_channel(err)


def _a_deferred_check_fails(monkeypatch, error):
    original = _StepDb.execute

    def boom(self, query, params=None):
        if str(query) == "SET CONSTRAINTS ALL IMMEDIATE":
            raise error
        return original(self, query, params)

    monkeypatch.setattr(_StepDb, "execute", boom)


def _a_routine_revoke_fails(monkeypatch, error):
    original = _StepDb.execute

    def boom(self, query, params=None):
        if (query.as_string() if hasattr(query, "as_string") else str(query)).startswith(
            "REVOKE ALL ON ROUTINE"
        ):
            raise error
        return original(self, query, params)

    monkeypatch.setattr(_StepDb, "execute", boom)


SITES = {
    # name: (how the driver error gets in, whether the refusal prints the server's primary message on purpose)
    "step-2-check-could-not-run": (
        lambda h, m: h(script=[psycopg.OperationalError(CHANNEL_WORDS)]),
        False,
    ),
    "step-4-statement": (
        lambda h, m: (
            _a_routine_revoke_fails(m, pge.UndefinedObject(CHANNEL_WORDS)),
            h(step4_rows=[("door", "s", "door", "integer", "f")]),
        )[1],
        False,
    ),
    "step-5-session-ended": (
        lambda h, m: (_a_deferred_check_fails(m, psycopg.OperationalError(CHANNEL_WORDS)), h())[1],
        False,
    ),
    "step-5-deferred-check": (
        lambda h, m: (_a_deferred_check_fails(m, pge.ForeignKeyViolation(CHANNEL_WORDS)), h())[1],
        True,
    ),
    "step-6-check-could-not-run": (
        lambda h, m: h(script=[[], psycopg.OperationalError(CHANNEL_WORDS)]),
        False,
    ),
    "step-7-commit-refused": (
        lambda h, m: h(commit_error=pge.ForeignKeyViolation(CHANNEL_WORDS)),
        True,
    ),
    "step-7-commit-unknown": (
        lambda h, m: h(commit_error=psycopg.OperationalError(CHANNEL_WORDS)),
        False,
    ),
    "step-8-connect": (
        lambda h, m: h(second_connect=psycopg.OperationalError(CHANNEL_WORDS)),
        False,
    ),
    "step-8-check": (
        lambda h, m: h(script=[[], [], psycopg.OperationalError(CHANNEL_WORDS)]),
        False,
    ),
}


@pytest.mark.parametrize("site", sorted(SITES))
def test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel(harness, monkeypatch, site):
    """Round 19 group 2: at every step that turns a driver error into a refusal or a failure report, the error that comes
    out of the public `migrate` holds no driver error on `__cause__` or `__context__` (the driver's DETAIL line can hold a row
    value). Killed by V153 (the guard is not applied to `migrate`), V154 to V160 (each part of the guard). On 6a25ae5d each
    of these kept the driver error. The refusals that print the server's primary message on purpose (a deferred check, a
    refused commit) are told apart: their text may hold the words, their channels may not."""
    how, prints_the_message = SITES[site]
    err, _opened, _rec, _applied = how(harness, monkeypatch)
    assert isinstance(err, ConfigError | AppliedNotVerifiedError), f"{site}: came out as {err!r}"
    _no_channel(err, words_in_text=prints_the_message)
    if not prints_the_message:
        assert CHANNEL_WORDS not in str(err), str(err)
