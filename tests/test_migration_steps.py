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
        self.closed, self.info = False, _Info()
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


def test_step_4_never_writes_a_function_with_a_control_character_in_its_name_into_a_statement(
    monkeypatch,
):
    """`_revoke_default_execute` writes a statement only for names that print as they are; the one that does not is left
    for the check at step 6 to refuse with a line a person can act on. The good function next to it is still revoked."""
    import contextlib

    class _Result:
        def fetchall(self):
            return [
                ("x", "app", "bad\nname", "(integer)", "f"),
                ("x", "app", "good", "(integer)", "f"),
            ]

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
    assert len(db.statements) == 1, db.statements
    text = db.statements[0].as_string(None) if hasattr(db.statements[0], "as_string") else ""
    assert "good" in repr(db.statements[0]) or "good" in text
    assert "bad" not in repr(db.statements[0])
