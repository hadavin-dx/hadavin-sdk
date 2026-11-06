"""`migrate()` calls the migration rule (P3a-2): the old checks are replaced, not doubled; the text that was scanned
is the text that runs; the read-back after each file is checked against an answering stub (no database).

The read-back queries are module constants of `store.migrate`; the stub answers them by EXACT text and gives every
other statement an empty answer. Planted names and SQL are made up."""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from tests.fixtures.dsn_skip import require_module

require_module(
    "psycopg"
)  # store.migrate imports psycopg (the pg extra); with the DSN set a missing driver FAILS

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import migration_numbers as mn

T0, T1 = "2026-11-06T00:00:00+00:00", "2026-11-06T00:00:01+00:00"
START = ("mig", "mig", "origin", '"$user", public', "on", "safe_encoding", "UTF8", T0, 700)
# the item names in the order of `START`
ITEMS = (
    "current_user",
    "session_user",
    "session_replication_role",
    "search_path",
    "standard_conforming_strings",
    "backslash_quote",
    "client_encoding",
    "transaction_timestamp",
    "txid_current",
)


def _values(**changes):
    row = list(START)
    for name, value in changes.items():
        row[ITEMS.index(name)] = value
    return tuple(row)


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

    def __init__(self, values, triggers, applied=()):
        self.values, self.triggers = list(values), list(triggers)
        self.applied = list(applied)
        self.log: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def transaction(self):
        return contextlib.nullcontext()

    def execute(self, query, params=None):
        text = str(query)
        self.log.append(text)
        if text == mig._READBACK_VALUES_SQL:
            return _Result([self.values.pop(0)])
        if text == mig._READBACK_TRIGGERS_SQL:
            return _Result(self.triggers.pop(0))
        if text == "SELECT current_schema()":
            return _Result([("s",)])
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


def _run(monkeypatch, tmp_path, values, triggers, n=2, applied=()):
    files = _files(tmp_path, n)
    db = _Db(values, triggers, applied)
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    monkeypatch.setattr(mig, "check_grants", lambda paths, texts=None: [])
    monkeypatch.setattr(mig, "connect", lambda *a, **k: db)
    try:
        applied_now = mig.migrate("postgresql://unused")
        return None, db, applied_now
    except ConfigError as e:
        return e, db, None


def _trigger(name="trg", enabled="O", relid=1, schema="s", table="t"):
    return (relid, name, enabled, table, schema)


# --- the old checks are replaced, not doubled -------------------------------------------------------------------


def test_migrate_uses_the_one_implementation_of_each_rule():
    assert mig.check_ledger is mn.check_ledger
    assert mig.MIGRATIONS is mn.MIGRATIONS
    assert mig._LOCK == mn.MIGRATE_LOCK
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
    planted.write_text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS p3a_c TEXT;\nCOMMIT;\n")
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
    """Cases (vii), M88: state D or R that was not there before; A and O pass."""
    for state in ("D", "R"):
        err, _, _ = _run(
            monkeypatch, tmp_path, [START, START], [[_trigger()], [_trigger(enabled=state)]]
        )
        assert isinstance(err, ConfigError) and "0001_f1.sql" in str(err)
        assert "trigger s.t.trg" in str(err), err
    for state in ("A", "O"):
        err, _, _applied = _run(
            monkeypatch,
            tmp_path,
            [START] * 3,
            [[_trigger()], [_trigger(enabled=state)], [_trigger(enabled=state)]],
        )
        assert err is None, err


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


def test_trigger_query_reads_only_the_migration_schema():
    """Case (xvi), M102: the schema filter is in the query text (a stub cannot answer for another schema)."""
    assert "current_schema()" in mig._READBACK_TRIGGERS_SQL
    assert "NOT t.tgisinternal" in mig._READBACK_TRIGGERS_SQL


def test_the_message_has_no_connection_string_and_escapes_names(monkeypatch, tmp_path):
    err, _, _ = _run(monkeypatch, tmp_path, [START, _values(search_path="a\x1b[31mred")], [[], []])
    assert "\x1b" not in str(err) and "://" not in str(err)
