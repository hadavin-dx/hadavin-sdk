"""`migrate()` calls the migration rule: the old checks are replaced, not doubled; the text that was scanned
is the text that runs; the read-back after each file is checked against an answering stub (no database).

The read-back queries are module constants of `store.migrate`; the stub answers them by EXACT text and gives every
other statement an empty answer. Planted names and SQL are made up."""

from __future__ import annotations

import contextlib
import json
import types
from pathlib import Path

import pytest

from tests.fixtures.dsn_skip import require_module

# store.migrate imports psycopg (the pg extra); with the DSN set a missing driver FAILS (never a skip)
require_module("psycopg")

import psycopg

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import migration_numbers as mn
from tests.fixtures.released_stub import made_up_files_are_not_released

T0, T1 = "2026-11-06T00:00:00+00:00", "2026-11-06T00:00:01+00:00"
START = (
    "mig",
    "mig",
    "origin",
    '"$user", public',
    "on",
    "safe_encoding",
    "UTF8",
    "5s",
    "60s",
    T0,
    700,
)
# the item names in the order of `START`
ITEMS = (
    "current_user",
    "session_user",
    "session_replication_role",
    "search_path",
    "standard_conforming_strings",
    "backslash_quote",
    "client_encoding",
    "lock_timeout",
    "statement_timeout",
    "transaction_timestamp",
    "txid_current",
)


def _values(**changes):
    row = list(START)
    for name, value in changes.items():
        row[ITEMS.index(name)] = value
    return tuple(row)


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """These tests are about what `migrate` reads and refuses around each file; `verify` itself is tested in
    `test_migration_verify*.py`. Here the state of the database always reads as clean, and each call is recorded."""
    calls: list[dict] = []

    def clean(db, **kw):
        calls.append(kw)
        return []

    monkeypatch.setattr(mig, "_state_problems", clean)
    return calls


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _Db:
    """A connection that answers the read-back queries from canned lists (next answer per call) and records every
    statement."""

    # a connection inside the transaction of the run (a file that ended it is made by a test of its own)
    info = types.SimpleNamespace(transaction_status=psycopg.pq.TransactionStatus.INTRANS)

    def __init__(
        self,
        values,
        triggers,
        applied=(),
        members=None,
        flags=None,
        settings=None,
        borrowed=(),
        parameters=None,
        schema_usage=True,
    ):
        self.parameters, self.schema_usage = parameters, schema_usage
        self.borrowed = [(r,) for r in borrowed]
        self.more_flags = []  # the flags of a second user name (the session user)
        self.values, self.triggers = list(values), list(triggers)
        self.flags = (False,) * 5 if flags is None else flags  # the role flags
        self.settings = None if settings is None else list(settings)  # one answer per read
        self.members = (
            None if members is None else list(members)
        )  # one answer per read; None = never any member
        # Step 6 of `migrate` reads everything once more after the last file and the grants (the final read-back). A
        # test scripts the answers up to the last file; the final read gets the last scripted answer again.
        for script in (self.values, self.triggers, self.settings, self.members):
            if script:
                script.append(script[-1])
        self.applied = list(applied)
        self.log: list[str] = []
        self.params: list[tuple] = []  # (statement, parameters) of every statement, in order

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @contextlib.contextmanager
    def transaction(self):
        """Like psycopg's savepoint: `psycopg.Rollback` leaves the block quietly (which is how `pinned_read` ends)."""
        try:
            yield
        except psycopg.Rollback:
            pass

    @staticmethod
    def _next(script: list, what: str):
        """The next scripted answer. A run that asks for more answers than the test scripted did not stop where the test
        expects, so that is a failed assertion of the test, never an incidental crash (the mutant runner must not count
        a crash as a kill)."""
        if not script:
            raise AssertionError(f"the run read the {what} more often than this test scripted")
        return script.pop(0)

    def execute(self, query, params=None):
        text = str(query)
        self.log.append(text)
        self.params.append((text, params))
        if text == mig._READBACK_VALUES_SQL:
            return _Result([self._next(self.values, "settings")])
        if text == mig._READBACK_TRIGGERS_SQL:
            return _Result(self._next(self.triggers, "triggers"))
        if text == mig._READBACK_MEMBERS_SQL:
            return _Result([] if self.members is None else self._next(self.members, "memberships"))
        if text == mig._ROLE_FLAGS_SQL:
            return _Result([self.flags, *self.more_flags])
        if text == mig._BORROWED_ROLES_SQL:
            return _Result(self.borrowed)
        if text == mig._PARAMETER_TABLE_SQL:
            return _Result([(self.parameters is not None,)])
        if text == mig._PARAMETER_GRANTS_SQL:
            return _Result([(x,) for x in (self.parameters or [])])
        if text == mig._READBACK_SETTINGS_SQL:
            return _Result(
                [] if self.settings is None else self._next(self.settings, "saved settings")
            )
        if text == "SELECT current_schema()":
            return _Result([("s",)])
        if text == mig.V2_SQL:
            return _Result([(160015,)])
        if text == mig._SCHEMA_OWNER_SQL:
            return _Result([("mig",)])
        if text == mig._RUN_IDENTITY_SQL:
            return _Result([("s", "mig", "mig")])
        if text.startswith("SELECT pg_has_role("):  # no named role is a member of another
            return _Result([(False,)])
        if text.startswith("SELECT version FROM schema_migrations"):
            return _Result([(v,) for v in self.applied])
        return _Result([])


def _files(tmp_path: Path, n: int = 2) -> list[Path]:
    paths = []
    for i in range(1, n + 1):
        p = tmp_path / f"{i:04d}_f{i}.sql"
        p.write_text(f"SELECT {i};\n", encoding="utf-8")
        paths.append(p)
    return paths


def _run(
    monkeypatch, tmp_path, values, triggers, n=2, applied=(), members=None, settings=None, **kw
):
    files = _files(tmp_path, n)
    db = _Db(values, triggers, applied, members, settings=settings)
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(
        monkeypatch
    )  # these made-up file names are not the released ones
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    try:
        applied_now = mig.migrate("postgresql://unused", **kw)
        return None, db, applied_now
    except ConfigError as e:
        return e, db, None


def _trigger(
    name="trg",
    enabled="O",
    schema="s",
    table="t",
    definition=None,
    src="BEGIN END",
    secdef=False,
    owner="owner_a",
    relid=None,
):
    """One answer row of `_READBACK_TRIGGERS_SQL`. `src` is the function text; the query returns its md5."""
    import hashlib
    import zlib

    definition = (
        definition
        or f"CREATE TRIGGER {name} BEFORE UPDATE ON {schema}.{table} EXECUTE FUNCTION {schema}.f()"
    )
    relid = zlib.crc32(f"{schema}.{table}".encode()) if relid is None else relid  # one id per table
    return (
        name,
        enabled,
        table,
        schema,
        relid,
        definition,
        hashlib.md5(src.encode(), usedforsecurity=False).hexdigest(),
        secdef,
        owner,
        None,
    )


# --- the old checks are replaced, not doubled -------------------------------------------------------------------


def test_migrate_uses_the_one_implementation_of_each_rule():
    assert mig.check_ledger is mn.check_ledger
    assert mig.MIGRATIONS is mn.MIGRATIONS
    assert mig.MIGRATE_LOCK is mn.MIGRATE_LOCK
    assert not hasattr(mig, "_FILE"), (
        "the second file-name pattern (it accepted Arabic-Indic digits) is gone"
    )
    assert mig._migration_files(mn.MIGRATIONS) == mn.list_migration_files(mn.MIGRATIONS)


def test_unicode_digit_names_are_refused(tmp_path):
    """FAIL-BEFORE 2 (also full-width digits)."""
    for digits in ("٠٠٠٢", "０００２"):
        folder = tmp_path / digits.encode("ascii", "backslashreplace").hex()
        folder.mkdir()
        (folder / "0001_a.sql").write_text("SELECT 1;")
        (folder / f"{digits}_b.sql").write_text("SELECT 1;")
        assert mig.check_ledger(mig._migration_files(folder)) != []


def test_uppercase_extension_is_refused(tmp_path):
    """FAIL-BEFORE 3 (Linux: `glob` is case-sensitive there)."""
    import os

    (tmp_path / "0001_a.sql").write_text("SELECT 1;")
    (tmp_path / "0002_b.SQL").write_text("SELECT 1;")
    assert "0002_b.SQL" in {e.name for e in os.scandir(tmp_path)}
    assert mig.check_ledger(mig._migration_files(tmp_path)) != []


def test_number_zero_is_refused(tmp_path):
    """FAIL-BEFORE 7."""
    (tmp_path / "0000_a.sql").write_text("SELECT 1;")
    (tmp_path / "0001_b.sql").write_text("SELECT 1;")
    assert mig.check_ledger(mig._migration_files(tmp_path)) != []


def test_dangling_link_is_refused(tmp_path):
    """FAIL-BEFORE 4b (Linux)."""
    (tmp_path / "0001_a.sql").write_text("SELECT 1;")
    (tmp_path / "0002_b.sql").symlink_to(tmp_path / "missing-target")
    got = mig.check_ledger(mig._migration_files(tmp_path))
    assert any("0002_b.sql: not a regular file" in p for p in got), got


def test_directory_named_like_a_migration_is_refused(monkeypatch, tmp_path):
    """FAIL-BEFORE 4a: a clear refusal before connecting, not a raw IsADirectoryError."""
    files = mig._migration_files() + [tmp_path / "0006_x.sql"]
    (tmp_path / "0006_x.sql").mkdir()
    monkeypatch.setattr(mig, "_migration_files", lambda: files)

    def no_db(*a, **k):
        raise AssertionError("connected")

    monkeypatch.setattr(mig, "connect", no_db)
    with pytest.raises(Exception) as e:
        mig.migrate("postgresql://unused")
    assert type(e.value) is mn.MigrationNumberError, repr(e.value)
    assert "0006_x.sql: not a regular file" in str(e.value)


def test_commit_in_a_file_is_refused_before_connecting(monkeypatch, tmp_path):
    """FAIL-BEFORE 5: the real files plus one that ends the transaction."""
    planted = tmp_path / "0006_commit.sql"
    planted.write_text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS hadavin_test_c TEXT;\nCOMMIT;\n")
    files = mig._migration_files() + [planted]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)

    def no_db(*a, **k):
        raise AssertionError("connected")

    monkeypatch.setattr(mig, "connect", no_db)
    with pytest.raises(Exception) as e:
        mig.migrate("postgresql://unused")
    assert isinstance(e.value, ConfigError), repr(e.value)
    assert "0006_commit.sql" in str(e.value)


def test_migrate_executes_the_text_it_scanned(monkeypatch, tmp_path):
    """One read per file. A file changed after the read is not run in its new form."""
    files = _files(tmp_path, 2)
    reads = []
    real = Path.read_text

    def counting(self, *a, **k):
        reads.append(self.name)
        return real(self, *a, **k)

    db = _Db([START, START, START], [[], [], []])
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    made_up_files_are_not_released(monkeypatch)  # made-up file names
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    monkeypatch.setattr(Path, "read_text", counting)
    real_scan = mig.check_grants

    def scan_then_change(paths, texts=None):
        out = real_scan(paths, texts=texts)
        files[0].write_text("SELECT 'changed after the read';\n", encoding="utf-8")
        return out

    monkeypatch.setattr(
        mig, "check_grants", lambda p, texts=None: scan_then_change(p, texts) and []
    )
    mig.migrate("postgresql://unused")
    assert reads.count("0001_f1.sql") == 1 and reads.count("0002_f2.sql") == 1, reads
    assert "SELECT 1;\n" in db.log and not any("changed after" in s for s in db.log)


# --- gone names and late files: refused inside the transaction, nothing applied ----------------------------------------


def test_late_file_is_refused_and_nothing_runs(monkeypatch, tmp_path):
    err, db, _ = _run(monkeypatch, tmp_path, [START], [[]], n=3, applied=["0001_f1", "0003_f3"])
    assert type(err) is mn.MigrationNumberError and "0002_f2.sql" in str(err)
    assert not any(s.startswith(("SELECT 2", "INSERT")) for s in db.log)


def test_gone_name_is_refused_with_the_old_phrase(monkeypatch, tmp_path):
    err, db, _ = _run(monkeypatch, tmp_path, [START], [[]], n=2, applied=["0001_f1", "0007_z"])
    assert type(err) is mn.MigrationNumberError
    assert "applied migrations have no file in this release" in str(err)
    assert "newer than this release" in str(err)
    assert not any(s.startswith(("SELECT 2", "INSERT")) for s in db.log)


# --- the read-back ----------------------------------------------------------------------------------------------------


def test_migrate_takes_the_one_advisory_lock_key_first(monkeypatch, tmp_path):
    """The lock `migrate` takes is the key of `migration_numbers` (the key a hand recipe takes too), before anything else."""
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None
    assert db.params[0][0] == (
        f"SET LOCAL lock_timeout = '{mn.MIGRATE_LOCK_WAIT_SECONDS * 1000}ms'; SET LOCAL statement_timeout = 0;"
    )
    assert db.params[1] == ("SELECT pg_advisory_xact_lock(%s)", (mn.MIGRATE_LOCK,))


def test_migrate_sets_the_recipe_limits_right_after_its_lock_and_before_any_file(
    monkeypatch, tmp_path
):
    """`migrate` runs the two `SET LOCAL` lines of `RECIPE_TIMEOUTS`, in order, right after the advisory
    lock and before the first file; they are the constant's, not copies (a patched constant is what runs)."""
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None
    assert db.params[1] == ("SELECT pg_advisory_xact_lock(%s)", (mn.MIGRATE_LOCK,))
    assert [t for t, _ in db.params[2:4]] == list(mn.RECIPE_TIMEOUTS)
    assert db.log.index("SELECT 1;\n") > 3
    other = ("SET LOCAL lock_timeout = '1ms';", "SET LOCAL statement_timeout = '2ms';")
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", other)
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None and tuple(t for t, _ in db.params[2:4]) == other


def test_clean_run_reads_before_each_file_insert(monkeypatch, tmp_path):
    """Cases (i) and (xii): saved values are read BEFORE the first file; each file is followed by both read queries
    and only then by its ledger INSERT (M64, M95)."""
    err, db, applied = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None and applied == ["0001_f1", "0002_f2"]
    log = db.log
    first_file = log.index("SELECT 1;\n")
    assert log.index(mig._READBACK_VALUES_SQL) < first_file, (
        "saved values are read before the first file"
    )
    second_file = log.index("SELECT 2;\n")
    inserts = [i for i, s in enumerate(log) if s.startswith("INSERT INTO schema_migrations")]
    for file_at, insert_at in zip((first_file, second_file), inserts, strict=True):
        reads = [
            i
            for i, s in enumerate(log)
            if s == mig._READBACK_VALUES_SQL and file_at < i < insert_at
        ]
        trig = [
            i
            for i, s in enumerate(log)
            if s == mig._READBACK_TRIGGERS_SQL and file_at < i < insert_at
        ]
        assert reads and trig, "both read queries run after the file and before its ledger row"


def test_nothing_to_apply_reads_nothing(monkeypatch, tmp_path):
    err, db, applied = _run(monkeypatch, tmp_path, [], [], n=2, applied=["0001_f1", "0002_f2"])
    assert err is None and applied == []
    assert mig._READBACK_VALUES_SQL not in db.log


@pytest.mark.parametrize("item", ITEMS[:-2] + ITEMS[-2:])
def test_each_value_is_compared_with_its_own_saved_value(monkeypatch, tmp_path, item):
    """Cases (ii), (x), (xiv), (xv): one value differs after file 1: refused naming file 1 and exactly that item
    (M62, M65 to M71, M91 to M94; M67 reads only after the last file: the second file never runs)."""
    new = {
        "current_user": "other",
        "session_user": "other",
        "session_replication_role": "replica",
        "search_path": "public",
        "standard_conforming_strings": "off",
        "backslash_quote": "on",
        "client_encoding": "LATIN1",
        "lock_timeout": "0",
        "statement_timeout": "0",
        "transaction_timestamp": T1,
        "txid_current": 701,
    }[item]
    err, db, _ = _run(monkeypatch, tmp_path, [START, _values(**{item: new})], [[], []])
    assert isinstance(err, ConfigError) and "0001_f1.sql" in str(err), err
    assert item in str(err) and ascii(new) in str(err)
    others = [i for i in ITEMS if i != item]
    assert not any(f"{o} was" in str(err) for o in others), "only the differing item is named"
    assert "SELECT 2;\n" not in db.log, "file 2 never ran"
    assert not any(s.startswith("INSERT INTO schema_migrations") for s in db.log)


def test_session_authorization_names_both_users(monkeypatch, tmp_path):
    """Case (iii): `set_config('session_authorization', ..)` moves both users: both are named (M65)."""
    err, _, _ = _run(
        monkeypatch, tmp_path, [START, _values(current_user="x", session_user="x")], [[], []]
    )
    assert "current_user" in str(err) and "session_user" in str(err)


def test_saved_users_that_differ_are_not_a_refusal(monkeypatch, tmp_path):
    """Case (xiii): `mig` is the current user and `admin` the session user at the start and nothing moves."""
    start = _values(session_user="admin")
    err, _, applied = _run(monkeypatch, tmp_path, [start, start, start], [[], [], []])
    assert err is None and applied == ["0001_f1", "0002_f2"]


def test_start_value_of_standard_conforming_strings_must_be_on(monkeypatch, tmp_path):
    """Case (ix), M90: refused before any file runs."""
    err, db, _ = _run(monkeypatch, tmp_path, [_values(standard_conforming_strings="off")], [[]])
    assert isinstance(err, ConfigError) and "standard_conforming_strings" in str(err)
    assert "SELECT 1;\n" not in db.log


def test_a_disabled_trigger_is_refused(monkeypatch, tmp_path):
    """Any change of the enabled state of a trigger that existed BEFORE the file is refused (`O` to `A` too: a list
    of only `D` and `R` let it pass). Killed by: mutant T1 (back to a D/R-only check). A trigger that the file itself
    creates disabled is another branch of the code; it is tested by the next test (mutant M88)."""
    for state in ("D", "R", "A"):
        err, _, _ = _run(
            monkeypatch, tmp_path, [START, START], [[_trigger()], [_trigger(enabled=state)]]
        )
        assert isinstance(err, ConfigError) and "0001_f1.sql" in str(err)
        assert "trigger s.t.trg changed: enabled state" in str(err), err
    for was, now in (("A", "O"), ("D", "O"), ("R", "A")):
        err, _, _ = _run(
            monkeypatch,
            tmp_path,
            [START, START],
            [[_trigger(enabled=was)], [_trigger(enabled=now)]],
        )
        assert isinstance(err, ConfigError), (was, now)


def test_a_trigger_created_disabled_is_refused_and_one_created_enabled_is_not(
    monkeypatch, tmp_path
):
    """A trigger the file creates disabled (`D`) or replica-only (`R`) is refused; one created enabled is not.
    Killed by: mutant M88 (the check of a new trigger's state removed)."""
    for state in ("D", "R"):
        err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[], [_trigger(enabled=state)]])
        assert isinstance(err, ConfigError) and "is created" in str(err), err
    for state in ("O", "A"):
        err, _, _ = _run(
            monkeypatch,
            tmp_path,
            [START] * 3,
            [[], [_trigger(enabled=state)], [_trigger(enabled=state)]],
        )
        assert err is None, err


def test_a_trigger_recreated_with_another_definition_or_function_is_refused(monkeypatch, tmp_path):
    """the trigger keeps its name, enabled state and table but not what it does.
    Killed by: mutants T1, T2, T3, T4, T5 and T7 of tests/migrate_mutants.py (one part of the saved trigger not compared)."""
    changes = {
        "definition": {
            "definition": "CREATE TRIGGER trg AFTER INSERT ON s.t EXECUTE FUNCTION s.g()"
        },
        "function text": {"src": "BEGIN RETURN NULL; END"},
        "function security mode": {"secdef": True},
        "function owner": {"owner": "owner_b"},
    }
    for part, change in changes.items():
        err, _, _ = _run(
            monkeypatch, tmp_path, [START, START], [[_trigger()], [_trigger(**change)]]
        )
        assert isinstance(err, ConfigError) and f"trigger s.t.trg changed: {part}" in str(err), (
            part,
            err,
        )


def test_the_trigger_query_reads_definition_function_text_and_security_mode():
    q = mig._READBACK_TRIGGERS_SQL
    assert (
        "pg_get_triggerdef(t.oid)" in q
        and "p.prosrc" in q
        and "md5" not in q
        and "p.prosecdef" in q
    )
    assert "pg_get_userbyid(p.proowner)" in q and "p.proconfig" in q
    assert "pg_proc" in q


def test_a_trigger_that_was_disabled_at_the_start_is_not_a_refusal(monkeypatch, tmp_path):
    same = [_trigger(enabled="D")]
    err, _, _ = _run(monkeypatch, tmp_path, [START] * 3, [same, same, same])
    assert err is None, err


def test_a_dropped_trigger_is_refused(monkeypatch, tmp_path):
    """Case (viii), M89."""
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[_trigger()], []])
    assert isinstance(err, ConfigError) and "trigger s.t.trg no longer exists" in str(err)


def test_a_new_trigger_is_not_a_refusal_and_is_watched_from_then_on(monkeypatch, tmp_path):
    """Case (xvii), M101: file 1 adds trigger O (fine); file 2 makes it vanish: refused naming file 2."""
    err, _, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [_trigger(name="new")], []])
    assert isinstance(err, ConfigError) and "0002_f2.sql" in str(err), err
    assert "trigger s.t.new no longer exists" in str(err)


def test_a_trigger_change_is_not_reported_as_a_changed_session(monkeypatch, tmp_path):
    """the message names the trigger, what changed and the way to allow it; it does not say the database
    session changed. Killed by: mutant T8 (a trigger change goes into the session list again)."""
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START, START],
        [[_trigger()], [_trigger(src="BEGIN RETURN NULL; END")]],
    )
    msg = str(err)
    assert "0001_f1.sql changed a trigger: trigger s.t.trg changed: function text" in msg, msg
    assert "migrations_trigger_changes.json" in msg
    assert "session" not in msg, msg
    # a session change and a trigger change together are both named
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START, _values(search_path="public")],
        [[_trigger()], [_trigger(src="x")]],
    )
    assert "left the database session changed: search_path" in str(err)
    assert "changed a trigger: trigger s.t.trg changed" in str(err)


def test_a_renamed_table_with_a_trigger_is_reported_as_a_renamed_table(monkeypatch, tmp_path):
    """The audit trigger stays on the same table id when the table is renamed, but code that
    names the table and a new table made under the old name would not have the trigger, so a rename is refused, and the
    message says "renamed", not "no longer exists". Killed by: mutant T9 (a renamed table reads as a vanished trigger)."""
    old = _trigger(table="t", relid=77)
    new = _trigger(table="t2", relid=77)
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[old], [new]])
    msg = str(err)
    assert "its table was renamed from t to t2" in msg, msg
    assert "no longer exists" not in msg
    # a table dropped and made again under ANOTHER name (new id) is not a rename
    err, _, _ = _run(
        monkeypatch, tmp_path, [START, START], [[old], [_trigger(table="t2", relid=78)]]
    )
    assert "trigger s.t.trg no longer exists" in str(err)


def _listed(*entries):
    """A fake reviewed list: entries are (migration, schema or None, table, trigger[, state])."""
    return frozenset(mig.TriggerChange(*e) for e in entries)


def test_an_allowed_trigger_change_passes_only_for_that_file_table_and_trigger(
    monkeypatch, tmp_path
):
    """The reviewed list names (migration, table, trigger); it allows a change, never a disappearance, and no other
    trigger, table or file. Killed by: mutant T10 (any trigger is allowed once any entry exists) and T11 (a disappearance
    is allowed)."""
    changed = [_trigger(src="BEGIN RETURN NULL; END")]
    monkeypatch.setattr(mig, "_trigger_changes", lambda: _listed(("0001_f1", None, "t", "trg")))
    err, _, applied = _run(monkeypatch, tmp_path, [START] * 3, [[_trigger()], changed, changed])
    assert err is None and applied == ["0001_f1", "0002_f2"], err
    # same trigger, another file: refused
    err, _, _ = _run(monkeypatch, tmp_path, [START] * 3, [[_trigger()], [_trigger()], changed])
    assert isinstance(err, ConfigError) and "0002_f2.sql" in str(err), err
    # same file, another trigger: refused
    other = [_trigger(), _trigger(name="other")]
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START, START],
        [other, [_trigger(), _trigger(name="other", src="x")]],
    )
    assert "trigger s.t.other changed" in str(err), err
    # same file, same trigger name on ANOTHER table: refused (the name alone is not the key)
    on_two = [_trigger(), _trigger(table="u", relid=78)]
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START, START],
        [on_two, [_trigger(), _trigger(table="u", relid=78, src="x")]],
    )
    assert "trigger s.u.trg changed: function text" in str(err), err
    # the allowed trigger vanishes: refused
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[_trigger()], []])
    assert "trigger s.t.trg no longer exists" in str(err), err


def test_an_entry_that_names_another_schema_does_not_allow_the_change(monkeypatch, tmp_path):
    """An entry written `schema.table` allows only that schema; one with no schema means the schema `migrate` uses."""
    changed = [_trigger(src="BEGIN RETURN NULL; END")]
    monkeypatch.setattr(
        mig, "_trigger_changes", lambda: _listed(("0001_f1", "elsewhere", "t", "trg"))
    )
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[_trigger()], changed])
    assert isinstance(err, ConfigError) and "trigger s.t.trg changed: function text" in str(err), (
        err
    )
    monkeypatch.setattr(mig, "_trigger_changes", lambda: _listed(("0001_f1", "s", "t", "trg")))
    err, _, _ = _run(monkeypatch, tmp_path, [START] * 3, [[_trigger()], changed, changed])
    assert err is None, err


def test_a_listed_trigger_may_not_be_left_disabled_or_replica_only_unless_the_entry_says_so(
    monkeypatch, tmp_path
):
    """The list allows a change of what a trigger does; it does not allow switching it off. `D` and `R` are refused for a
    listed trigger unless the entry names that exact state. Killed by: mutant T14 (a listed trigger may be left in any
    state)."""
    for state in ("D", "R"):
        monkeypatch.setattr(mig, "_trigger_changes", lambda: _listed(("0001_f1", None, "t", "trg")))
        err, _, _ = _run(
            monkeypatch, tmp_path, [START, START], [[_trigger()], [_trigger(enabled=state)]]
        )
        assert isinstance(err, ConfigError) and "which its list entry does not name" in str(err), (
            err
        )
        assert "enabled_state" in str(err)
        # the entry names the OTHER state: still refused
        other = "R" if state == "D" else "D"
        monkeypatch.setattr(
            mig,
            "_trigger_changes",
            lambda other=other: _listed(("0001_f1", None, "t", "trg", other)),
        )
        err, _, _ = _run(
            monkeypatch, tmp_path, [START, START], [[_trigger()], [_trigger(enabled=state)]]
        )
        assert isinstance(err, ConfigError) and "does not name" in str(err), err
        # the entry names this state: allowed
        monkeypatch.setattr(
            mig,
            "_trigger_changes",
            lambda state=state: _listed(("0001_f1", None, "t", "trg", state)),
        )
        err, _, applied = _run(
            monkeypatch,
            tmp_path,
            [START] * 3,
            [[_trigger()], [_trigger(enabled=state)], [_trigger(enabled=state)]],
        )
        assert err is None and applied == ["0001_f1", "0002_f2"], (state, err)
    # a listed trigger that stays enabled and changes only its function: allowed, no state named
    monkeypatch.setattr(mig, "_trigger_changes", lambda: _listed(("0001_f1", None, "t", "trg")))
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START] * 3,
        [[_trigger()], [_trigger(enabled="A", src="x")], [_trigger(enabled="A", src="x")]],
    )
    assert err is None, err


def test_the_list_of_allowed_trigger_changes_is_empty_today_and_strictly_read(
    monkeypatch, tmp_path
):
    """The shipped list is empty. A bad list is a ConfigError (never "allow"). Killed by: mutant T12 (the loader ignores
    a bad shape)."""
    assert mig._trigger_changes() == frozenset()
    good = {
        "migration": "0007_x",
        "table": "audit_entries",
        "trigger": "trg",
        "reason": "replaces the function, same rule",
    }

    def load(text):
        f = tmp_path / "list.json"
        f.write_text(text, encoding="utf-8")
        monkeypatch.setattr(mig, "TRIGGER_CHANGES", f)
        return mig._trigger_changes()

    import json

    assert load(json.dumps([good])) == _listed(("0007_x", None, "audit_entries", "trg"))
    assert load(
        json.dumps([{**good, "table": "app.audit_entries", "enabled_state": "D"}])
    ) == _listed(("0007_x", "app", "audit_entries", "trg", "D"))
    # the same trigger name on two tables is two entries, not a repeat
    assert len(load(json.dumps([good, {**good, "table": "other"}]))) == 2
    for bad in (
        "{}",
        "not json",
        json.dumps([{**good, "extra": "x"}]),
        json.dumps([{"migration": "0007_x", "trigger": "trg", "reason": "x"}]),  # no table
        json.dumps([{**good, "reason": " "}]),
        json.dumps([{**good, "reason": "a\nb"}]),
        json.dumps([{**good, "migration": "7_x"}]),
        json.dumps([{**good, "migration": "0007_X"}]),
        json.dumps([{**good, "trigger": 5}]),
        json.dumps([{**good, "table": "a.b.c"}]),
        json.dumps([{**good, "table": "a b"}]),
        json.dumps([{**good, "enabled_state": "A"}]),
        json.dumps([{**good, "enabled_state": ""}]),
        json.dumps([good, good]),
    ):
        with pytest.raises(ConfigError, match="allowed trigger changes"):
            load(bad)
    monkeypatch.setattr(mig, "TRIGGER_CHANGES", tmp_path / "missing.json")
    with pytest.raises(ConfigError, match="cannot be read"):
        mig._trigger_changes()


def test_trigger_query_reads_only_the_migration_schema():
    """Case (xvi), M102: the schema filter is in the query text (a stub cannot answer for another schema)."""
    assert "n.nspname = %s" in mig._READBACK_TRIGGERS_SQL
    assert (
        "current_schema()" not in mig._READBACK_TRIGGERS_SQL
    )  # the schema is the one read at step 1
    assert "NOT t.tgisinternal" in mig._READBACK_TRIGGERS_SQL


def test_the_message_has_no_connection_string_and_escapes_names(monkeypatch, tmp_path):
    err, _, _ = _run(monkeypatch, tmp_path, [START, _values(search_path="a\x1b[31mred")], [[], []])
    assert "\x1b" not in str(err) and "://" not in str(err)


# --- role memberships: a grant made inside a function body is found by the read-back ------------------------

EDGE = ("app_rw", "app_admin", '{"admin_option": false, "grantor": 10}')


def test_a_new_role_membership_after_a_file_is_refused(monkeypatch, tmp_path):
    """Killed by: mutant R1 (membership not compared) and mutant R2 (membership not read after the file)."""
    err, db, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], members=[[], [EDGE]])
    assert isinstance(err, ConfigError) and "0001_f1.sql" in str(err), err
    assert "role app_rw has a new member app_admin" in str(err)
    assert "SELECT 2;\n" not in db.log, "file 2 never ran"


def test_a_removed_role_membership_is_refused(monkeypatch, tmp_path):
    """Killed by: mutant R3 (a removed membership is not reported)."""
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], members=[[EDGE], []])
    assert isinstance(err, ConfigError) and "role app_rw lost the member app_admin" in str(err), err


def test_a_changed_grant_option_of_a_membership_is_refused(monkeypatch, tmp_path):
    """Killed by: mutant R4 (only role and member compared, not the other columns)."""
    other = (*EDGE[:2], '{"admin_option": true, "grantor": 10}')
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], members=[[EDGE], [other]])
    assert isinstance(err, ConfigError) and "app_rw" in str(err), err


def test_memberships_that_were_there_at_the_start_are_not_a_refusal(monkeypatch, tmp_path):
    err, _, applied = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []], members=[[EDGE]] * 3)
    assert err is None and applied == ["0001_f1", "0002_f2"], err


def test_the_membership_message_escapes_names(monkeypatch, tmp_path):
    bad = ("r\x1b[31m", "s", "{}")
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], members=[[], [bad]])
    assert "\x1b" not in str(err) and "\\x1b" in str(err)


def test_the_membership_is_read_after_every_file_and_before_its_ledger_row(monkeypatch, tmp_path):
    """Killed by: mutant R2 (the members query is never sent by the read-back)."""
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None
    log = db.log
    assert (
        log.count(mig._READBACK_MEMBERS_SQL) == 4
    )  # the start, one per file, and the final read (step 6)
    inserts = [i for i, s in enumerate(log) if s.startswith("INSERT INTO schema_migrations")]
    reads = [i for i, s in enumerate(log) if s == mig._READBACK_MEMBERS_SQL]
    assert reads[1] < inserts[0] < reads[2] < inserts[1] < reads[3]


def test_the_membership_query_reads_names_and_every_other_column():
    assert "pg_auth_members" in mig._READBACK_MEMBERS_SQL
    assert "::regrole::text" in mig._READBACK_MEMBERS_SQL
    assert "to_jsonb(m)" in mig._READBACK_MEMBERS_SQL


# --- a trigger is the same trigger when its table is dropped and made again --------------------------------


def test_a_table_made_again_with_its_trigger_is_not_a_false_refusal(monkeypatch, tmp_path):
    """The table has a new OID after DROP + CREATE; the trigger has the same schema, table and name."""
    err, _, applied = _run(
        monkeypatch,
        tmp_path,
        [START] * 3,
        [[_trigger()], [_trigger()], [_trigger()]],
    )
    assert err is None and applied == ["0001_f1", "0002_f2"], err


def test_a_trigger_on_another_table_with_the_same_name_is_another_trigger(monkeypatch, tmp_path):
    err, _, _ = _run(
        monkeypatch,
        tmp_path,
        [START] * 2,
        [[_trigger(table="a")], [_trigger(table="b")]],
    )
    assert isinstance(err, ConfigError) and "trigger s.a.trg no longer exists" in str(err), err


# --- the migration role is not a superuser ----------------------------------------------------------------


FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls", "rolreplication")


@pytest.mark.parametrize("flag", FLAGS)
def test_a_privileged_migration_role_is_refused_before_any_file_runs(monkeypatch, tmp_path, flag):
    """Killed by: mutants S1 (no check), S2..S5 (one flag not read)."""
    files = _files(tmp_path, 2)
    flags = tuple(f == flag for f in FLAGS)
    db = _Db([START] * 3, [[], [], []], flags=flags)
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(
        monkeypatch
    )  # these made-up file names are not the released ones
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError, match=f"it holds: {flag}"):
        mig.migrate("postgresql://unused")
    assert "SELECT 1;\n" not in db.log
    assert not any(s.startswith("CREATE TABLE IF NOT EXISTS schema_migrations") for s in db.log)


def test_a_role_that_is_a_member_of_a_privileged_role_is_refused_before_any_file_runs(
    monkeypatch, tmp_path
):
    files = _files(tmp_path, 1)
    db = _Db([START], [[]], borrowed=("boss_role", "other_boss"))
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError, match="member of a role that is a superuser") as e:
        mig.migrate("postgresql://unused")
    assert "boss_role, other_boss" in str(e.value) and "REVOKE" in str(e.value)
    assert "SELECT 1;\n" not in db.log
    assert not any(s.startswith("CREATE TABLE IF NOT EXISTS schema_migrations") for s in db.log)


def test_the_membership_check_reads_both_user_names_all_five_flags_and_the_built_in_roles():
    """A pin on the query text; the real-server tests show the behaviour."""
    q = mig._BORROWED_ROLES_SQL
    assert "current_user" in q and "session_user" in q and "'MEMBER'" in q and "'pg_'" in q
    for flag in FLAGS:
        assert flag in q


def test_the_role_flags_are_read_for_the_current_user_and_the_session_user():
    """A pin on the query text. Killed by: mutant SU1 (the query then no longer names `session_user`), alone."""
    assert "current_user" in mig._ROLE_FLAGS_SQL and "session_user" in mig._ROLE_FLAGS_SQL
    assert "pg_roles" in mig._ROLE_FLAGS_SQL
    for flag in FLAGS:
        assert flag in mig._ROLE_FLAGS_SQL


def _refused_by(monkeypatch, tmp_path, **db_args):
    files = _files(tmp_path, 1)
    db = _Db([START], [[]], **db_args)
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    return db


def test_a_privileged_session_user_is_refused_even_when_the_current_user_is_plain(
    monkeypatch, tmp_path
):
    """Killed by: mutants SU1 and SU2 (the second row of flags is not read). Pin: it also passes on the source before round 11 (42fc259), as the independent run of 8382bdd showed; it holds the behaviour in place."""
    db = _refused_by(monkeypatch, tmp_path)
    db.more_flags = [(True, False, False, False, False)]
    with pytest.raises(ConfigError, match="it holds: rolsuper"):
        mig.migrate("postgresql://unused")
    assert "SELECT 1;\n" not in db.log


def test_a_parameter_grant_is_refused_before_any_file_runs(monkeypatch, tmp_path):
    """Killed by: mutant PA1."""
    db = _refused_by(monkeypatch, tmp_path, parameters=["session_replication_role"])
    with pytest.raises(ConfigError, match="may change server settings it must not change") as e:
        mig.migrate("postgresql://unused")
    assert "session_replication_role" in str(e.value)
    assert "SELECT 1;\n" not in db.log


def test_a_server_without_parameter_grants_is_not_asked_about_them(monkeypatch, tmp_path):
    files = _files(tmp_path, 2)
    db = _Db([START] * 3, [[], [], []], parameters=None)
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    mig.migrate("postgresql://unused")
    assert mig._PARAMETER_TABLE_SQL in db.log and mig._PARAMETER_GRANTS_SQL not in db.log


@pytest.mark.parametrize("name", ["bad\nname", "tab\there"])
def test_a_trigger_name_that_is_not_plain_is_refused_in_the_list(monkeypatch, tmp_path, name):
    """Killed by: mutant TN1 (the name check is gone)."""
    f = tmp_path / "list.json"
    f.write_text(
        json.dumps([{"migration": "0001_x", "table": "a", "trigger": name, "reason": "r"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(mig, "TRIGGER_CHANGES", f)
    with pytest.raises(ConfigError, match="trigger name with a control or unusual character"):
        mig._trigger_changes()


def test_there_is_no_switch_that_turns_the_role_check_off():
    """no argument, setting or module name can switch the check off."""
    import inspect

    assert "allow_privileged_role_for_tests" not in inspect.signature(mig.migrate).parameters
    assert not any("privileged" in name for name in dir(mig) if name != "_refuse_privileged_role")
    assert "allow_privileged_role_for_tests" not in inspect.getsource(mig)


def test_the_refusal_says_how_to_make_a_plain_migration_role(monkeypatch, tmp_path):
    """The message names the flags held and gives one SQL example with no password or other secret. Pin: it also passes on the source before round 11 (42fc259), as the independent run of 8382bdd showed; it holds the behaviour in place."""
    files = _files(tmp_path, 1)
    db = _Db([START], [[]], flags=(True, False, False, False, False))
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(
        monkeypatch
    )  # these made-up file names are not the released ones
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError) as e:
        mig.migrate("postgresql://unused")
    msg = str(e.value)
    assert "it holds: rolsuper" in msg and mig.PLAIN_MIGRATION_ROLE_SQL in msg
    assert "NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS" in msg
    assert "password" not in msg.lower()


# --- settings saved per database or role and the two time limits ---------------------------------


def test_a_new_saved_setting_for_a_role_is_refused(monkeypatch, tmp_path):
    """`ALTER ROLE x SET search_path = ...` changes the NEXT session, not this one: only pg_db_role_setting shows it.
    Killed by: mutants PS1 (settings not read), PS2 (not compared)."""
    saved = ("mydb", "app_rw", "{search_path=evil}")
    err, _db, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], settings=[[], [saved]])
    assert isinstance(err, ConfigError) and "0001_f1.sql" in str(err), err
    assert "saved setting in database mydb for role app_rw is new" in str(err)
    err, _, _ = _run(monkeypatch, tmp_path, [START, START], [[], []], settings=[[saved], []])
    assert isinstance(err, ConfigError) and "is gone" in str(err), err
    err, _, applied = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []], settings=[[saved]] * 3)
    assert err is None and applied == ["0001_f1", "0002_f2"]


@pytest.mark.parametrize("item", ["lock_timeout", "statement_timeout"])
def test_a_file_that_changes_a_time_limit_is_refused(monkeypatch, tmp_path, item):
    """Killed by: mutant L1 (the limits are not in the read-back)."""
    err, _, _ = _run(monkeypatch, tmp_path, [START, _values(**{item: "0"})], [[], []])
    assert isinstance(err, ConfigError) and f"{item} was '" in str(err), err


def test_the_membership_message_says_it_may_be_another_session(monkeypatch, tmp_path):
    """A role membership of the migration roles that changed while the file ran is reported in words that say another
    session may have done it. Killed by: mutant SC4 (the old wording)."""
    row = ("role_a", "role_b", '{"admin_option": false}')
    err, _db, _ = _run(monkeypatch, tmp_path, [START] * 2, [[], []], members=[[], [row]])
    assert isinstance(err, ConfigError), err
    assert (
        "a role membership changed while the file ran (it may be another session; run migrate again)"
        in str(err)
    )
    assert "role role_a has a new member role_b" in str(err)
    assert "left the database session changed" not in str(err)


def test_the_named_roles_reach_the_two_scoped_read_back_queries(monkeypatch, tmp_path):
    """The names of the runtime, portal and purge roles are the one parameter of the members query and of the settings
    query, at the start, after each file and at the final read (step 6). Killed by: mutants SC5 (the names are not
    passed) and SC3."""
    err, db, _ = _run(
        monkeypatch,
        tmp_path,
        [START] * 3,
        [[], [], []],
        runtime_role="rt_role",
        portal_role="pt_role",
    )
    assert err is None, err
    for query in (mig._READBACK_MEMBERS_SQL, mig._READBACK_SETTINGS_SQL):
        given = [p for t, p in db.params if t == query]
        assert given == [(["rt_role", "pt_role"],)] * 4, given


def test_the_ownership_query_gets_the_managed_names(monkeypatch, tmp_path):
    """In a whole run the ownership check gets the names this package manages: the relations for the relation half of
    the query. (That the function half gets the function names and not the relation names is shown, with a file that
    creates a function, by tests/test_migration_compare.py.) Killed by: mutant OA6 (the relation half gets no names)."""
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []])
    assert err is None, err
    given = [p for t, p in db.params if t == mig._FOREIGN_OWNED_SQL]
    assert len(given) == 1, given
    schema_a, relations, schema_b, functions = given[0]
    assert schema_a == schema_b, "both halves look in the one schema read at step 1"
    assert "spend" in relations and "schema_migrations" in relations, given
    assert functions == [], "the made-up files of this test create no function"


def test_the_managed_names_are_the_grant_map_the_ledger_and_the_functions_the_files_create():
    """Killed by: mutants OA3 (functions are not added) and OA5 (the ledger table is not named)."""
    texts = [
        "CREATE OR REPLACE FUNCTION audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$;",
        "create function \"Quoted_Fn\"(a int) returns int language sql as 'select 1';",
        "CREATE FUNCTION some_schema.qualified_fn() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "-- CREATE FUNCTION in_a_comment() RETURNS int\nSELECT 1;",
    ]
    relations, names = mig._managed_names(texts, "some_schema")
    assert names == sorted(set(names)) and relations == sorted(set(relations))
    assert set(relations) == set(mig.GRANTS) | {"schema_migrations"}
    assert set(names) == {"audit_guard", "Quoted_Fn", "qualified_fn"}
    assert "in_a_comment" not in names and "some_schema" not in names


def test_a_plain_function_name_is_folded_to_lower_case_and_a_quoted_one_is_read_whole():
    """PostgreSQL stores `Mixed_Case` as `mixed_case`, and a quoted name keeps its case, spaces and doubled quotes.
    Killed by: mutants MN1 (a plain name is not folded) and MN2 (a quoted name is cut at the first space)."""
    texts = [
        "CREATE FUNCTION Mixed_Case() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "create or replace function \"a b\"(x int) returns int language sql as 'select 1';",
        'CREATE FUNCTION "other_schema"."Q""x"() RETURNS int LANGUAGE sql AS \'SELECT 1\';',
        "CREATE FUNCTION Other_Schema.Folded_Too() RETURNS int LANGUAGE sql AS 'SELECT 1';",
    ]
    names = set(mig._managed_names(texts, "other_schema")[1])
    assert {"mixed_case", "a b", 'Q"x', "folded_too"} <= names
    assert not {"Mixed_Case", "a"} & names


def test_a_function_of_another_schema_is_not_a_managed_name():
    """`CREATE FUNCTION other.audit()` makes no function in the schema of the run, so an unrelated `audit` there that
    another role owns is no reason to refuse the run. The schema is read as the server reads it (a plain one is
    folded, a quoted one keeps its case). Killed by: mutants SQ1 (the schema before the dot is ignored) and SQ2 (a
    name written with the schema of the run is not read)."""
    texts = [
        "CREATE OR REPLACE FUNCTION other_schema.audit_other() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION \"Mixed\".quoted_other() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION my_schema.audit_mine() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION \"My_Schema\".audit_quoted_mine() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION audit_bare() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        # three parts: database.schema.name (the database part is left out; the schema decides)
        "CREATE FUNCTION some_db.my_schema.audit_three() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION \"Some Db\".other_schema.audit_three_other() RETURNS int LANGUAGE sql AS 'SELECT 1';",
    ]
    names = set(mig._managed_names(texts, "my_schema")[1])
    assert {"audit_mine", "audit_bare", "audit_three"} <= names, names
    assert not {"audit_other", "quoted_other", "audit_quoted_mine", "audit_three_other"} & names, (
        names
    )
    assert "audit_quoted_mine" in set(mig._managed_names(texts, "My_Schema")[1])


def test_a_name_is_folded_as_the_server_folds_it_and_is_read_only_at_the_start_of_a_statement():
    """PostgreSQL folds only the letters A to Z (not the capitals of other scripts), a plain name may hold `$` after its
    first character, and text that only looks like a statement (in a comment, or in the middle of a statement) is not a function this
    package creates. Killed by: mutants FQ1 (every capital is folded), PL1 (`$` ends a plain name) and ST1 (a statement
    start is not needed)."""
    texts = [
        "CREATE FUNCTION Cost$Fn() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "CREATE FUNCTION \u00c4rger_\u00dc() RETURNS int LANGUAGE sql AS 'SELECT 1';",
        "SELECT 1; -- CREATE FUNCTION Hidden_In_Comment()\n",
        "SELECT 1 CREATE FUNCTION Hidden_Mid_Statement() RETURNS int;",
    ]
    names = set(mig._managed_names(texts, "public")[1])
    assert {"cost$fn", "\u00c4rger_\u00dc"} <= names, names
    assert not {"\u00e4rger_\u00fc", "cost"} & names, names
    assert not {n for n in names if n.startswith("hidden")}, names
    # The text of a string that holds `; CREATE FUNCTION name` is read as a function too. That adds a name that no
    # object has (or a same-named function of another owner, which is refused): a run can be refused that need not be.
    # A function made by `EXECUTE format('CREATE FUNCTION ...')` in a body is not read by name here; the check of rights
    # finds it by what is new in the schema (test_a_security_definer_function_made_by_dynamic_sql_...).
    assert "in_string" in set(
        mig._managed_names(["SELECT 'x; CREATE FUNCTION In_String() y';"], "public")[1]
    )


def test_the_roles_are_asked_again_after_every_file(monkeypatch, tmp_path):
    """The flags, the borrowed roles and the parameter grants are asked at the start and again after each file; a file
    that left the migration user a member of a powerful role is refused by name of the file. Killed by: mutant RC1 (the
    questions are not asked again)."""

    class _Borrows(_Db):
        def execute(self, query, params=None):
            if str(query) == mig._BORROWED_ROLES_SQL:
                self.log.append(str(query))
                asked = self.log.count(mig._BORROWED_ROLES_SQL)
                return _Result([("boss_role",)] if asked >= 2 else [])
            return super().execute(query, params)

    files = _files(tmp_path, 1)
    db = _Borrows([START] * 2, [[], []])
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError, match=r"migration 0001_f1\.sql left the roles changed") as e:
        mig.migrate("postgresql://unused")
    assert "boss_role" in str(e.value)
    assert not any(s.startswith("INSERT INTO schema_migrations") for s in db.log)


def test_the_replication_flag_is_read_again_after_every_file(monkeypatch, tmp_path):
    """A file that gave the migration role the `REPLICATION` flag is refused by name of the file (the flags are asked at
    the start and again after each file). Killed by: mutants RC1 (the questions are not asked again) and RF1 (the flag is
    not one of the flags)."""

    class _Flips(_Db):
        def execute(self, query, params=None):
            if str(query) == mig._ROLE_FLAGS_SQL:
                self.log.append(str(query))
                asked = self.log.count(mig._ROLE_FLAGS_SQL)
                return _Result([(False, False, False, False, asked >= 2)])
            return super().execute(query, params)

    files = _files(tmp_path, 1)
    db = _Flips([START] * 2, [[], []])
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError, match=r"migration 0001_f1\.sql left the roles changed") as e:
        mig.migrate("postgresql://unused")
    assert "rolreplication" in str(e.value)
    assert not any(s.startswith("INSERT INTO schema_migrations") for s in db.log)


# --- the released-file list is checked by migrate() itself ---------------------------------------------


def test_migrate_refuses_a_changed_released_file_before_it_connects(monkeypatch, tmp_path):
    """Killed by: mutant R6 (the call to released_problems removed from migrate())."""
    import json

    manifest = dict(mig._released_manifest())
    first = min(manifest)
    manifest[first] = "0" * 64
    path = tmp_path / "released.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(mig, "RELEASED_MANIFEST", path)

    def no_connect(*a, **k):
        raise AssertionError("migrate connected although a released file changed")

    monkeypatch.setattr(mig, "connect", no_connect)
    with pytest.raises(mn.MigrationNumberError, match=f"{first}: a released file was changed"):
        mig.migrate("postgresql://unused")


def test_migrate_refuses_when_the_released_list_is_unreadable_or_wrong(monkeypatch, tmp_path):
    """An unreadable or wrongly shaped list of released files is a ConfigError before any connection."""
    monkeypatch.setattr(mig, "connect", lambda *a, **k: pytest.fail("connected"))
    missing = tmp_path / "none.json"
    monkeypatch.setattr(mig, "RELEASED_MANIFEST", missing)
    with pytest.raises(ConfigError, match="released migration files cannot be read"):
        mig.migrate("postgresql://unused")
    wrong = tmp_path / "wrong.json"
    wrong.write_text('["0001_core"]', encoding="utf-8")
    monkeypatch.setattr(mig, "RELEASED_MANIFEST", wrong)
    with pytest.raises(ConfigError, match="not a name -> SHA-256 table"):
        mig.migrate("postgresql://unused")


def test_the_released_list_ships_inside_the_package_and_the_real_folder_passes_it():
    assert mig.RELEASED_MANIFEST.parent == mn.MIGRATIONS.parent
    assert mig.RELEASED_MANIFEST.is_file()
    assert mn.released_problems(mn.MIGRATIONS, mig._released_manifest()) == []


def test_every_entry_of_the_trigger_list_names_a_file_that_is_in_the_folder():
    """A stale entry (its file was renamed or removed) would allow nothing and hide that; the shipped list is checked
    against the real folder (it is empty today, so this holds trivially until the first entry)."""
    stems = {p.stem for p in mig._migration_files()}
    assert {c.migration for c in mig._trigger_changes()} <= stems


def test_the_released_check_looks_at_the_files_migrate_runs_not_at_the_folder(
    monkeypatch, tmp_path
):
    """`migrate` runs the list `_migration_files()` gives it; the released check must read that same list. Here the files
    are copies in another folder with one released file edited: the folder itself is untouched, so a check that listed
    the folder would pass. Killed by: mutant R7 (the check lists the folder again)."""
    import shutil

    for p in mn.MIGRATIONS.glob("*.sql"):
        shutil.copy(p, tmp_path / p.name)
    edited = tmp_path / "0002_audit_chain.sql"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nSELECT 1;\n", encoding="utf-8")
    monkeypatch.setattr(mig, "_migration_files", lambda: sorted(tmp_path.glob("*.sql")))
    monkeypatch.setattr(mig, "connect", lambda *a, **k: pytest.fail("connected"))
    with pytest.raises(
        mn.MigrationNumberError, match="0002_audit_chain: a released file was changed"
    ):
        mig.migrate("postgresql://unused")


def test_a_bad_hash_in_the_released_list_is_a_config_error_not_a_changed_file(
    monkeypatch, tmp_path
):
    """a value that is not 64 lower-case hex digits is a broken list (ConfigError, before any connection),
    not "a released file was changed"."""
    import json

    monkeypatch.setattr(mig, "connect", lambda *a, **k: pytest.fail("connected"))
    good = dict(mig._released_manifest())
    first = min(good)
    for bad in ("xyz", "", "0" * 63, "0" * 65, "A" * 64, "0" * 63 + "g", ("0" * 64) + "\n"):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({**good, first: bad}), encoding="utf-8")
        monkeypatch.setattr(mig, "RELEASED_MANIFEST", path)
        with pytest.raises(ConfigError, match="no SHA-256 .* for"):
            mig.migrate("postgresql://unused")


def test_a_json_name_written_twice_in_the_released_list_is_refused(monkeypatch, tmp_path):
    """`json` would keep the last of two equal names, so an edited second hash would hide the first."""
    good = mig._released_manifest()
    first, digest = next(iter(good.items()))
    path = tmp_path / "dup.json"
    path.write_text(
        '{"' + first + '": "' + digest + '", "' + first + '": "' + "1" * 64 + '"}', encoding="utf-8"
    )
    monkeypatch.setattr(mig, "RELEASED_MANIFEST", path)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: pytest.fail("connected"))
    with pytest.raises(ConfigError, match="cannot be read: .*written twice"):
        mig.migrate("postgresql://unused")


class _Raises(_Db):
    """The connection raises `error` when the text of file `trigger` is executed."""

    def __init__(self, error, trigger, *a):
        super().__init__(*a)
        self.error, self.trigger = error, trigger

    def execute(self, query, params=None):
        if str(query) == self.trigger:
            raise self.error
        return super().execute(query, params)


def _run_raising(monkeypatch, tmp_path, error):
    files = _files(tmp_path, 2)
    db = _Raises(error, "SELECT 2;\n", [START] * 3, [[], [], []])
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(
        monkeypatch
    )  # these made-up file names are not the released ones
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    mig.migrate("postgresql://unused")


def test_a_lock_wait_or_a_slow_statement_is_a_plain_config_error_naming_step_and_setting(
    monkeypatch, tmp_path
):
    """A lock wait that runs out is reported with the file being applied and the setting `lock_timeout`."""
    from psycopg import errors as pge

    with pytest.raises(ConfigError, match=r"applying 0002_f2\.sql.*lock_timeout") as got:
        _run_raising(
            monkeypatch, tmp_path, pge.LockNotAvailable("canceling statement due to lock timeout")
        )
    assert "kept nothing" in str(got.value) and "Migration repair steps" in str(got.value)
    assert mn.RECIPE_TIMEOUTS[0].split("'")[1] in str(
        got.value
    )  # the number comes from the constant
    with pytest.raises(ConfigError, match=r"applying 0002_f2\.sql.*statement_timeout"):
        _run_raising(
            monkeypatch, tmp_path, pge.QueryCanceled("canceling statement due to statement timeout")
        )


def test_the_statement_limit_is_found_by_the_error_code_not_by_the_words(monkeypatch, tmp_path):
    """the server words follow `lc_messages` (a German server says "wegen Zeitüberschreitung"); the code
    57014 does not."""
    from psycopg import errors as pge

    with pytest.raises(ConfigError, match=r"applying 0002_f2\.sql.*statement_timeout"):
        _run_raising(
            monkeypatch,
            tmp_path,
            pge.QueryCanceled("Anweisung wurde wegen Zeitüberschreitung abgebrochen"),
        )
    with pytest.raises(pge.DeadlockDetected):
        _run_raising(monkeypatch, tmp_path, pge.DeadlockDetected("statement timeout"))


# --- the test role helper: one CREATE ROLE, and the password is never in a statement ---------------------------------------


class _Roles:
    """A connection for `ensure_plain_role`: `exists` answers the `pg_roles` look-up; every statement is recorded."""

    def __init__(self, exists: bool, sees: bool = True, password: str = ""):
        self.exists, self.sees, self.log = exists, sees, []
        self.pgconn = self
        self.info = types.SimpleNamespace(
            dsn="host=made-up-host port=5999 dbname=made_up", password=password
        )

    def transaction(self):
        return contextlib.nullcontext()

    def encrypt_password(self, password, user, algorithm):
        self.encrypted = (password, user, algorithm)
        return b"SCRAM-SHA-256$4096:made-up-salt$made-up-keys"

    def execute(self, query, params=None):
        text = query if isinstance(query, str) else query.as_string()
        self.log.append(text)
        if "pg_read_all_stats" in text:
            return _Result([(self.sees,)])  # may this login see the sessions of other users?
        if "pg_stat_activity" in text:
            return _Result([])  # no stale roles to sweep
        return _Result([(1,)] if "FROM pg_roles WHERE rolname = %s" in text and self.exists else [])


class _Hold:
    """The long-lived connection that holds the live-process lock: records what it is asked and that it is closed."""

    def __init__(self, server):
        self.server, self.log, self.closed = server, [], False

    def execute(self, query, params=None):
        self.log.append((query, params))
        return _Result([(True,)])  # the try-lock is granted

    def close(self):
        self.closed = True


@pytest.fixture
def holds(monkeypatch):
    """Every `psycopg.connect` of the helper goes to a recorder, and the helper's own table of held locks starts empty."""
    from tests.fixtures import migration_role as mr

    made = []
    monkeypatch.setattr(mr, "_MARKS", {})
    monkeypatch.setattr(
        "psycopg.connect", lambda server, **k: made.append(_Hold(server)) or made[-1]
    )
    return made


def test_the_live_process_lock_is_taken_on_the_connection_target_that_makes_the_role(holds):
    """The lock of "this test process is alive" is taken on the database of the connection that creates the role, not on
    one named by an environment variable, and it is taken once per database. Killed by: mutants SW4
    (`_mark_the_role` is not called) and SW5 (the lock is taken on a fixed local server)."""
    from tests.fixtures import migration_role as mr

    mr.ensure_plain_role(_Roles(exists=False))
    assert len(holds) == 1, [h.server for h in holds]
    assert "made-up-host" in holds[0].server and "5999" in holds[0].server
    assert f"application_name={mr.PLAIN_ROLE}" in holds[0].server, holds[0].server
    assert "password" not in str(list(mr._MARKS)), "the table of held connections keeps no password"
    ((query, params),) = holds[0].log
    assert "pg_try_advisory_lock" in query and params == (mr._mark_key(mr._TOKEN),)
    mr.ensure_plain_role(_Roles(exists=False))
    assert len(holds) == 1, "a second role creation on the same server takes no second lock"


def test_the_marking_connection_is_closed_when_the_lock_cannot_be_taken(holds):
    """Killed by: mutant SW9 (the new connection is left open when the lock statement raises)."""
    from tests.fixtures import migration_role as mr

    class Boom(Exception):
        pass

    def fail(self, query, params=None):
        raise Boom

    _Hold.execute, saved = fail, _Hold.execute
    try:
        with pytest.raises(Boom):
            mr._mark_the_role(_Roles(exists=False))
    finally:
        _Hold.execute = saved
    assert len(holds) == 1 and holds[0].closed and mr._MARKS == {}


def test_a_role_that_exists_takes_no_lock_and_a_missing_environment_variable_changes_nothing(
    holds, monkeypatch
):
    from tests.fixtures import migration_role as mr

    monkeypatch.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    mr.ensure_plain_role(_Roles(exists=True))
    assert holds == []
    mr.ensure_plain_role(_Roles(exists=False))
    assert len(holds) == 1, "the lock does not depend on HADAVIN_TEST_PG_DSN"


@pytest.mark.parametrize(
    "token", ["+1234567", " 1234567", "1_234567", "ABCDEF12", "1234567", "123456789", ""]
)
def test_only_eight_lower_case_hex_digits_are_a_token(token):
    """`int(x, 16)` alone reads signs, spaces and underscores. Killed by: mutant SW6 (the strict check is removed)."""
    from tests.fixtures import migration_role as mr

    with pytest.raises(ValueError):
        mr._mark_key(token)
    assert mr._mark_key("0123abcd") == mr._MARK_BASE + 0x0123ABCD


def test_the_test_role_is_looked_up_first_and_not_made_a_second_time(holds):
    """A repeated `CREATE ROLE ... PASSWORD` fails on the server and the server logs the failed statement. Killed by:
    mutant TR2 (the role is created without the look-up)."""
    from tests.fixtures import migration_role as mr

    db = _Roles(exists=True)
    mr.ensure_plain_role(db)
    assert len(db.log) == 1 and "FROM pg_roles" in db.log[0], db.log


def test_the_test_role_is_made_without_the_replication_flag(holds):
    """Killed by: mutant RP1 (NOREPLICATION is left out of the statement)."""
    from tests.fixtures import migration_role as mr

    db = _Roles(exists=False)
    mr.ensure_plain_role(db)
    created = [s for s in db.log if s.startswith("CREATE ROLE")]
    assert "NOREPLICATION" in created[0], created


def test_the_test_role_password_is_sent_only_as_a_hash(holds):
    """The raw password is in no statement: the statement holds the SCRAM hash made on this side. Killed by: mutant TR3."""
    from tests.fixtures import migration_role as mr

    db = _Roles(exists=False)
    mr.ensure_plain_role(db)
    created = [s for s in db.log if s.startswith("CREATE ROLE")]
    assert len(created) == 1, db.log
    assert mr._PASSWORD not in " ".join(db.log)
    assert "SCRAM-SHA-256$4096:made-up-salt" in created[0] and "ALTER ROLE" not in " ".join(db.log)
    assert db.encrypted[2] == b"scram-sha-256"


def test_making_the_test_role_first_sweeps_the_stale_roles_of_killed_processes(holds):
    """Killed by: mutant SW1 (the sweep is not called before the role is made)."""
    from tests.fixtures import migration_role as mr

    db = _Roles(exists=False)
    mr.ensure_plain_role(db)
    swept = [i for i, s in enumerate(db.log) if "pg_stat_activity" in s and "LIKE" in s]
    created = [i for i, s in enumerate(db.log) if s.startswith("CREATE ROLE")]
    assert swept and created and swept[0] < created[0], db.log
    db = _Roles(exists=True)
    mr.ensure_plain_role(db)
    assert not any("pg_stat_activity" in s for s in db.log), "a role that exists is not swept for"


def test_a_login_that_cannot_see_other_sessions_sweeps_nothing(capsys):
    """Without the right to see the sessions of other users a live role could look unused, so the sweep asks first and
    does nothing, and says so in one line. Killed by: mutants SW11 (the question is not asked) and SW16 (it does not
    say so)."""
    from tests.fixtures import migration_role as mr

    db = _Roles(exists=False, sees=False)
    assert mr.sweep_stale_roles(db) == []
    said = capsys.readouterr().out.strip().splitlines()
    assert len(said) == 1 and said[0].startswith("stale test roles were not looked for"), said
    assert "cannot see the sessions" in said[0]
    assert not any("pg_stat_activity" in s for s in db.log), db.log
    seeing = _Roles(exists=False, sees=True)
    mr.sweep_stale_roles(seeing)
    assert any("pg_stat_activity" in s for s in seeing.log)


def test_the_marking_connection_is_given_the_password_of_the_connection(holds):
    """`info.dsn` leaves the password out, so it is passed on; it is not kept in the table of held connections. Killed
    by: mutant SW10 (the password is not passed on)."""
    from tests.fixtures import migration_role as mr

    made_up = "pw" + "-made-up"
    mr.ensure_plain_role(_Roles(exists=False, password=made_up))
    assert f"password={made_up}" in holds[0].server, holds[0].server
    assert not any(made_up in str(key) for key in mr._MARKS), list(mr._MARKS)


def test_a_failed_unlock_does_not_fail_the_setup(monkeypatch):
    """The unlock runs on a connection that may be broken; its error is not raised out of the setup of a test. Killed
    by: mutant SW12 (the unlock is not guarded)."""
    import psycopg

    from tests.fixtures import migration_role as mr

    class Db(_Roles):
        def execute(self, query, params=None):
            text = query if isinstance(query, str) else query.as_string()
            if "pg_advisory_unlock" in text:
                raise psycopg.OperationalError("connection lost")
            if "pg_try_advisory_lock" in text:
                return _Result([(True,)])
            if "pg_stat_activity" in text:
                return _Result([("hadavin_test_migrator_0123abcd",)])
            return super().execute(query, params)

    raised = None
    got = None
    try:
        got = mr.sweep_stale_roles(Db(exists=False))
    except psycopg.Error as e:
        raised = str(e)
    assert raised is None, f"the error of the unlock was raised out of the sweep: {raised}"
    assert got == ["hadavin_test_migrator_0123abcd"]


def test_only_a_schema_with_the_test_prefix_is_a_scratch_schema():
    """A schema called `t_...` is not one (a real application could call a schema that). Killed by: mutant TR4."""
    from tests.fixtures import migration_role as mr

    assert mr._is_scratch("hadavin_test_abc") and not mr._is_scratch("t_abc")
    assert not mr._is_scratch("") and not mr._is_scratch(None) and not mr._is_scratch("public")


def test_the_named_roles_are_checked_against_each_other_after_every_file(monkeypatch, tmp_path):
    """Two of the runtime, portal and purge roles that are members of each other are refused right after the first file,
    by name of the file, not only at the end of the run. Killed by: mutant RC2."""

    class _Members(_Db):
        def execute(self, query, params=None):
            if str(query).startswith("SELECT pg_has_role("):
                self.log.append(str(query))
                return _Result([(True,)])
            return super().execute(query, params)

    files = _files(tmp_path, 2)
    db = _Members([START] * 3, [[], [], []])
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    made_up_files_are_not_released(monkeypatch)
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    with pytest.raises(ConfigError, match=r"migration 0001_f1\.sql left the roles changed") as e:
        mig.migrate("postgresql://unused", runtime_role="rt_role", portal_role="pt_role")
    assert "must not be members of each other" in str(e.value)
    assert not any(s.startswith("INSERT INTO schema_migrations") for s in db.log)


def test_the_wait_for_the_lock_is_limited_by_the_argument(monkeypatch, tmp_path):
    """The number of seconds is the argument's (milliseconds in the setting), before the lock is asked for. Killed by:
    mutants LW1 (no limit is set) and LW3 (the constant is used, not the argument)."""
    err, db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []], lock_wait_seconds=7)
    assert err is None
    assert db.params[0][0] == "SET LOCAL lock_timeout = '7000ms'; SET LOCAL statement_timeout = 0;"
    assert "pg_advisory_xact_lock" in db.params[1][0]


@pytest.mark.parametrize("bad", [0, -1, 1.5, "5", True, None])
def test_the_wait_for_the_lock_must_be_a_whole_number_of_seconds(monkeypatch, tmp_path, bad):
    err, _db, _ = _run(monkeypatch, tmp_path, [START] * 3, [[], [], []], lock_wait_seconds=bad)
    assert type(err) is ConfigError and "lock_wait_seconds" in str(err)


def test_cli_migrate_maps_applied_not_verified_to_exit_5(cfg_dir, monkeypatch, capsys):
    """Exit 5 (ticket P3a-2, 4.2): the message on standard error, the statements of the package's own objects on standard
    output, then a comment line and the statements for objects that are not this package's; no "applied" line."""
    import yaml

    from hadavin_sdk import cli
    from hadavin_sdk.errors import AppliedNotVerifiedError
    from hadavin_sdk.store.migration_verify import Problem

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")
    own = Problem(
        "right",
        "app",
        "runs",
        "",
        "EVERYONE",
        "SELECT",
        "mig",
        owner="mig",
        grantor_is_owner=True,
        fix='REVOKE SELECT ON TABLE "app"."runs" FROM PUBLIC;',
        word="table",
    )
    other = Problem(
        "everyone",
        "other",
        "secret",
        "",
        "EVERYONE",
        "SELECT",
        "someone",
        owner="someone",
        outside_package=True,
        fix='REVOKE SELECT ON TABLE "other"."secret" FROM PUBLIC;',
        word="table",
    )

    def fake(dsn, **kw):
        raise AppliedNotVerifiedError(
            "FIRST SENTENCE of the message", applied=["0001"], problems=[other, own]
        )

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", fake)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--runtime-role", "rt"]) == 5
    out, err = capsys.readouterr()
    assert "FIRST SENTENCE of the message" in err
    assert "applied:" not in out and "applied:" not in err
    assert out.splitlines() == [
        'REVOKE SELECT ON TABLE "app"."runs" FROM PUBLIC;',
        "-- NOT THIS PACKAGE'S OBJECTS: confirm each with its owner before running",
        'REVOKE SELECT ON TABLE "other"."secret" FROM PUBLIC;',
    ]

    def fake_statements_only(dsn, **kw):
        raise AppliedNotVerifiedError("could not run", could_not_run="made-up reason")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", fake_statements_only)
    assert cli.main(["--config", str(cfg_dir), "migrate"]) == 5
    out, err = capsys.readouterr()
    assert out == "" and "could not run" in err


def test_applied_not_verified_is_not_a_config_error():
    """`ConfigError` means "refused, nothing happened" in this package; the new error must never be caught as one."""
    from hadavin_sdk.errors import AppliedNotVerifiedError

    assert not issubclass(AppliedNotVerifiedError, ConfigError)
    e = AppliedNotVerifiedError("m", applied=("0001",), commit_unknown=True)
    assert (e.applied, e.problems, e.statements, e.could_not_run, e.commit_unknown) == (
        ["0001"],
        [],
        [],
        "",
        True,
    )
