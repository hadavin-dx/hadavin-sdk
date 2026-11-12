"""The migration rule as pure functions (`hadavin_sdk.store.migration_numbers`): file-name numbers, late files, the
written recipe, the ledger-without-file message, the one-pass lexer and the refusal list. No database, no psycopg.

The module is imported inside each test (the `mn` fixture), so on a tree without the module every test is one error
and not a collection error. Planted names and SQL are made up. Postgres-side tests live in a later change."""

from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

import pytest

from tests.fixtures import timing
from tests.fixtures.seeded import Seeded

FUZZ_CASES = 2000
FUZZ_SEED = 20261106
CR, LF, FF, VT, ESC = "\r", "\n", "\f", "\v", "\x1b"


@pytest.fixture
def mn():
    import hadavin_sdk.store.migration_numbers as module

    return module


def _folder(tmp_path: Path, names: list[str]) -> Path:
    for name in names:
        (tmp_path / name).write_text("SELECT 1;\n", encoding="utf-8")
    return tmp_path


def _problems(mn, tmp_path, names):
    return mn.check_ledger(mn.list_migration_files(_folder(tmp_path, names)))


def _real(mn) -> list[Path]:
    return mn.list_migration_files(mn.MIGRATIONS)


# --- file names and numbers ---------------------------------------------------------------------------------------


def test_the_real_folder_is_consistent(mn):
    files = _real(mn)
    assert len(files) >= 4, "the check would look at nothing"
    assert mn.check_ledger(files) == []
    mn.check_migration_numbers()


def test_duplicate_number(mn, tmp_path):
    got = _problems(mn, tmp_path, ["0001_a.sql", "0002_b.sql", "0002_c.sql"])
    assert got == ["two migrations are numbered 0002"], "a repeated number must be reported once"


def test_gap(mn, tmp_path):
    assert _problems(mn, tmp_path, ["0001_a.sql", "0003_b.sql"]) == ["migration 0002 is missing"]
    sub = tmp_path / "two"
    sub.mkdir()
    assert _problems(mn, sub, ["0002_a.sql"]) == ["migration 0001 is missing"]


def test_plant_badly_named_file_is_caught(mn, tmp_path):
    got = _problems(mn, tmp_path, ["0001_a.sql", "5_b.sql", "0002_Bad.sql"])
    assert got == [
        "0002_Bad.sql: not named NNNN_<name>.sql",
        "5_b.sql: not named NNNN_<name>.sql",
    ], "the old message text and the file order must stay"


@pytest.mark.parametrize("digits", ["٠٠٠٢", "０００２"], ids=["arabic-indic", "full-width"])
def test_unicode_digit_names_are_refused(mn, tmp_path, digits):
    got = _problems(mn, tmp_path, ["0001_a.sql", f"{digits}_b.sql"])
    assert got != [], "non-ASCII digits are not a migration number"
    assert any("not named" in p for p in got)


@pytest.mark.skipif(sys.platform != "linux", reason="a case-sensitive file system is needed")
def test_uppercase_extension_is_refused(mn, tmp_path):
    _folder(tmp_path, ["0001_a.sql", "0002_b.SQL"])
    assert "0002_b.SQL" in os.listdir(tmp_path)
    got = mn.check_ledger(mn.list_migration_files(tmp_path))
    assert got != [], "a file with an upper-case extension must be listed and refused"
    assert got[0].startswith("0002_b.SQL: not named")


def test_number_zero_is_refused(mn, tmp_path):
    got = _problems(mn, tmp_path, ["0000_a.sql", "0001_b.sql"])
    assert got == ["0000_a.sql: number 0000 is not allowed, numbers start at 0001"]


@pytest.mark.parametrize(
    "name",
    ["1_a.sql", "00001_a.sql", "99999999999_a.sql", "0001-a.sql", "0001_A.sql", "0001_a.sql.bak"],
)
def test_hostile_names_are_refused_or_ignored(mn, tmp_path, name):
    got = _problems(mn, tmp_path, ["0001_ok.sql", name])
    if name.endswith(".bak"):
        assert got == [], "a name without the .sql suffix is not listed at run time"
    else:
        assert got == [f"{name}: not named NNNN_<name>.sql"]


def test_bak_is_ignored_at_runtime(mn, tmp_path):
    _folder(tmp_path, ["0001_a.sql", "0001_a.sql.bak", "notes.txt"])
    assert [p.name for p in mn.list_migration_files(tmp_path)] == ["0001_a.sql"]


def test_directory_named_like_a_migration_is_refused(mn, tmp_path):
    _folder(tmp_path, ["0001_a.sql"])
    (tmp_path / "0002_x.sql").mkdir()
    got = mn.check_ledger(mn.list_migration_files(tmp_path))
    assert got == ["0002_x.sql: not a regular file (a directory, or a link that points nowhere)"]


@pytest.mark.skipif(sys.platform != "linux", reason="symbolic links need Linux here")
def test_dangling_link_is_refused(mn, tmp_path):
    _folder(tmp_path, ["0001_a.sql"])
    (tmp_path / "0002_b.sql").symlink_to(tmp_path / "missing.sql")
    got = mn.check_ledger(mn.list_migration_files(tmp_path))
    assert "0002_b.sql: not a regular file" in got[0], "a link that points nowhere is not a file"


@pytest.mark.skipif(sys.platform != "linux", reason="symbolic links need Linux here")
def test_runtime_accepts_symlink_to_file(mn, tmp_path):
    src = tmp_path / "elsewhere.txt"
    src.write_text("SELECT 1;\n", encoding="utf-8")
    folder = tmp_path / "m"
    folder.mkdir()
    (folder / "0001_a.sql").symlink_to(src)
    assert mn.check_ledger(mn.list_migration_files(folder)) == [], "installers may link files"


@pytest.mark.skipif(sys.platform != "linux", reason="symbolic links need Linux here")
def test_symlink_in_and_out_are_refused_by_ci(mn, tmp_path):
    folder = tmp_path / "m"
    folder.mkdir()
    _folder(folder, ["0001_a.sql", "0002_b.sql"])
    outside = tmp_path / "outside.sql"
    outside.write_text("SELECT 1;\n", encoding="utf-8")
    (folder / "0003_c.sql").symlink_to(outside)  # out
    (folder / "0004_d.sql").symlink_to(folder / "0001_a.sql")  # in
    with pytest.raises(mn.MigrationNumberError) as e:
        mn.check_migration_numbers(folder)
    assert "0003_c.sql: is a symbolic link" in str(e.value), "a link out of the folder"
    assert "0004_d.sql: is a symbolic link" in str(e.value), "a link inside the folder"


def test_stray_entries_refused_by_ci(mn, tmp_path):
    _folder(tmp_path, ["0001_a.sql", "0001_a.sql.bak"])
    (tmp_path / "__pycache__").mkdir()
    with pytest.raises(mn.MigrationNumberError) as e:
        mn.check_migration_numbers(tmp_path)
    assert "0001_a.sql.bak: not a migration file" in str(e.value)
    assert "__pycache__: not a migration file" in str(e.value)


def test_planted_duplicate_in_a_copy_of_the_real_folder_is_caught(mn, tmp_path):
    for p in _real(mn):
        (tmp_path / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    mn.check_migration_numbers(tmp_path)
    (tmp_path / "0005_dup.sql").write_text("SELECT 1;\n", encoding="utf-8")
    with pytest.raises(mn.MigrationNumberError, match="0005_dup.sql|numbered 0005"):
        mn.check_migration_numbers(tmp_path)


def test_names_in_messages_are_escaped(mn, tmp_path):
    names = [f"0001_a{ESC}[31m.sql", "0002_b\nx.sql", "0003_\udcff.sql"]
    paths = [tmp_path / n for n in names]
    got = mn.check_ledger(paths)
    text = "; ".join(got)
    assert ESC not in text and "\n" not in text and "\udcff" not in text, (
        "raw control characters leaked"
    )
    assert "\\x1b" in text and "\\n" in text and "\\udcff" in text


def test_problem_list_is_capped(mn):
    err = mn.MigrationNumberError([f"p{i}" for i in range(500)])
    assert len(err.problems) == 500, "the exception keeps every problem"
    assert str(err).count(";") == 20, "the message shows 20 problems and the count of the rest"
    assert str(err).endswith("and 480 more")


def test_cap_boundary(mn):
    msg = {n: str(mn.MigrationNumberError([f"p{i}" for i in range(n)])) for n in (20, 21, 22)}
    assert "more" not in msg[20], "20 problems are all shown"
    assert msg[21].endswith("p19; and 1 more"), "21 problems show 20 plus 'and 1 more'"
    assert msg[22].endswith("p19; and 2 more")


def test_a_huge_number_gives_a_capped_message(mn, tmp_path):
    got = _problems(mn, tmp_path, ["9999_a.sql"])
    assert len(got) == 9998, "every gap is a problem for check_ledger itself"
    assert str(mn.MigrationNumberError(got)).count(";") == 20, "but the message is capped"


def test_message_class_and_prefix(mn):
    e = mn.MigrationNumberError(["a", "b"])
    from hadavin_sdk.errors import ConfigError

    assert type(e) is mn.MigrationNumberError and isinstance(e, ConfigError)
    assert str(e) == "migrations are inconsistent: a; b"


def test_lock_key_value(mn):
    assert mn.MIGRATE_LOCK == 3760701656253510835, "the key every migrate run takes"


def test_read_files_reads_each_file_once(mn, tmp_path, monkeypatch):
    files = [tmp_path / "0001_a.sql", tmp_path / "0002_b.sql"]
    for p in files:
        p.write_text("SELECT 1;", encoding="utf-8")
    calls: list[Path] = []
    real = Path.read_text

    def spy(self, *a, **k):
        calls.append(self)
        assert k.get("encoding") == "utf-8"
        return real(self, *a, **k)

    monkeypatch.setattr(Path, "read_text", spy)
    got = mn.read_files(files)
    assert got == {files[0]: "SELECT 1;", files[1]: "SELECT 1;"}
    assert sorted(calls) == sorted(files), "one read per file"


def test_a_file_that_is_not_utf8_raises_the_original_error(mn, tmp_path):
    p = tmp_path / "0001_a.sql"
    p.write_bytes(b"\xff\xfe")
    with pytest.raises(UnicodeDecodeError):
        mn.read_files([p])


# --- late files ---------------------------------------------------------------------------------------------------


def _paths(*names):
    return [Path(n) for n in names]


def test_late_files_basics(mn):
    files = _paths("0001_a.sql", "0002_b.sql", "0003_c.sql")
    assert mn.late_files(set(), files) == [], "an empty ledger has no late file"
    assert mn.late_files({"0001_a", "0002_b", "0003_c"}, files) == [], "all applied"
    assert mn.late_files({"0001_a", "0003_c"}, files) == [files[1]], (
        "0002 is below the applied 0003"
    )
    assert mn.late_files({"0001_a", "zzz"}, files) == [], (
        "an applied name that is not a stem is ignored"
    )


def test_late_files_equal_number(mn):
    files = _paths("0002_new.sql")
    assert mn.late_files({"0002_old"}, files) == files, "the same number with another stem is late"


def test_late_files_uses_highest(mn):
    files = _paths("0001_a.sql", "0002_b.sql", "0004_d.sql")
    got = mn.late_files({"0003_c", "0001_a_other"}, files)
    assert got == [files[0], files[1]], "the highest applied number (3) is used, not the lowest"


def test_late_files_ignores_non_ascii_digit_applied_stems(mn):
    assert mn.late_files({"٠٠٠٩_x"}, _paths("0005_a.sql")) == []


def test_late_files_are_sorted_by_number(mn):
    files = _paths("0003_c.sql", "0001_a.sql", "0002_b.sql")
    assert mn.late_files({"0009_z"}, files) == [files[1], files[2], files[0]]


# --- the recipe ---------------------------------------------------------------------------------------------------


def _recipe(mn, entries=(("0004_x", "SELECT 1;"),), schema="p3a_s"):
    return mn.hand_recipe(list(entries), schema)


def test_recipe_order_and_command(mn):
    entries = [("0004_a", "SELECT 1;"), ("0005_b", "SELECT 2;"), ("0006_c", "SELECT 3;")]
    got = mn.order_problems(
        {"0009_z"},
        _paths("0004_a.sql", "0005_b.sql", "0006_c.sql"),
        {Path(f"{s}.sql"): t for s, t in entries},
        "p3a_s",
    )
    assert len(got) == 1, "one problem, one recipe, however many files are late"
    msg = got[0]
    assert "psql -X -v ON_ERROR_STOP=1 -f recipe.sql" in msg, "the exact printed command"
    recipe = msg[msg.index("-- RECIPE begins") :]
    lines = recipe.split("\n")
    assert lines[0] == "-- RECIPE begins" and lines[-1] == "-- RECIPE ends"
    order = [
        lines.index('SET search_path TO "p3a_s";'),
        lines.index("BEGIN;"),
        lines.index(f"SELECT pg_advisory_xact_lock({mn.MIGRATE_LOCK});"),
        lines.index("SELECT 1;"),
        lines.index("INSERT INTO schema_migrations (version) VALUES ('0004_a');"),
        lines.index("SELECT 2;"),
        lines.index("INSERT INTO schema_migrations (version) VALUES ('0005_b');"),
        lines.index("SELECT 3;"),
        lines.index("INSERT INTO schema_migrations (version) VALUES ('0006_c');"),
        lines.index("COMMIT;"),
    ]
    assert order == sorted(order), "the statements run in this order"
    assert recipe.count(str(mn.MIGRATE_LOCK)) == 1, "one lock for all late files"
    assert "://" not in msg, "no connection string"


def test_recipe_first_line(mn):
    lines = _recipe(mn).split("\n")
    assert lines[:2] == ["-- RECIPE begins", "\\set ON_ERROR_STOP on"], (
        "the stop must not depend on -X"
    )


def test_recipe_has_no_include_command(mn):
    msg = mn.order_problems(
        {"0009_z"}, _paths("0004_x.sql"), {Path("0004_x.sql"): "SELECT 1;"}, "p3a_s"
    )[0]
    assert msg.count("\\") == 1, "the only backslash is the generated first line"
    assert msg.index("\\") == msg.index("\\set ON_ERROR_STOP on")
    assert "\\i " not in msg and "://" not in msg


@pytest.mark.parametrize(
    "sql",
    [
        "\\! x",
        "SELECT 1 \\g",
        "SELECT :name;",
        "SELECT :'name';",
        'SELECT :"name";',
        "SELECT :{?x};",
        "SELECT :é;",
        "SELECT 'a\\d';",
        "SELECT E'\\n';",
        "-- a \\ in a comment\nSELECT 1;",
    ],
    ids=[
        "line-start",
        "mid-line",
        "bare",
        "quoted",
        "dquoted",
        "exists",
        "non-ascii",
        "in-string",
        "e-string",
        "in-comment",
    ],
)
def test_recipe_refuses_psql_syntax(mn, sql):
    with pytest.raises(ValueError, match="0004_x"):
        _recipe(mn, [("0004_x", sql)])


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1::int;",
        "SELECT x[1:2] FROM t;",
        "-- :name in a comment\nSELECT 1;",
        "SELECT ':name';",
        "SELECT $$:name$$;",
        "SELECT a::text::int;",
    ],
    ids=["cast", "slice-digits", "colon-comment", "colon-string", "colon-dollar", "double-cast"],
)
def test_recipe_accepts_what_psql_leaves_alone(mn, sql):
    assert sql in _recipe(mn, [("0004_x", sql)])


def test_recipe_refuses_a_stem_that_would_break_the_quotes(mn):
    with pytest.raises(ValueError, match=r"0004_x"):
        _recipe(mn, [("0004_x'; DROP", "SELECT 1;")])


@pytest.mark.parametrize(
    "sql",
    [
        "-- RECIPE ends\nSELECT 1;",
        "SELECT 'RECIPE begins';",
        "RECIPE ends",
        f"SELECT 1;{ESC}[2K",
        "SELECT 1;\x07",
        "SELECT 1;\x00",
    ],
    ids=["marker-comment", "marker-string", "marker-plain", "esc", "bel", "nul"],
)
def test_recipe_refuses_markers_and_control_characters(mn, sql):
    with pytest.raises(ValueError, match="0004_x"):
        _recipe(mn, [("0004_x", sql)])


def test_recipe_accepts_tab_lf_cr_ff(mn):
    assert "\tSELECT\f1;\r\n" in _recipe(mn, [("0004_x", "\tSELECT\f1;\r\n")])


def test_recipe_trailing_comment(mn):
    lines = _recipe(mn, [("0004_x", "ALTER TABLE t ADD COLUMN c TEXT; -- done")]).split("\n")
    assert not any("-- done" in ln and "INSERT" in ln for ln in lines), (
        "the comment swallowed the INSERT"
    )
    assert any(ln.startswith("INSERT INTO schema_migrations") for ln in lines)


def test_recipe_unterminated_last_statement(mn):
    assert "\n;\n" in _recipe(mn, [("0004_x", "SELECT 1")]), (
        "a lone ; ends the unterminated statement"
    )
    assert "\n;\n" not in _recipe(mn, [("0004_x", "SELECT 1;")])
    assert "\n;\n" not in _recipe(mn, [("0004_x", "SELECT 1; -- c")])


def test_recipe_schema_quoted(mn):
    assert 'SET search_path TO "default";' in _recipe(mn, schema="default")
    assert 'SET search_path TO "p3a_s";' in _recipe(mn)


def test_schema_name_plain(mn):
    msg = mn.order_problems(
        {"0009_z"}, _paths("0004_x.sql"), {Path("0004_x.sql"): "SELECT 1;"}, "My Schema; DROP"
    )[0]
    assert "-- RECIPE begins" not in msg, "no recipe for an unusual schema name"
    assert "unusual characters" in msg


def test_order_problems_turns_a_refused_file_into_a_message(mn):
    msg = mn.order_problems(
        {"0009_z"}, _paths("0004_x.sql"), {Path("0004_x.sql"): "\\! echo hi"}, "p3a_s"
    )[0]
    assert "-- RECIPE begins" not in msg and "0004_x" in msg and "by hand" in msg


def test_order_problems_empty_when_nothing_is_late(mn):
    assert mn.order_problems({"0001_a"}, _paths("0001_a.sql", "0002_b.sql"), {}, "s") == []


def test_a_hostile_name_never_reaches_the_order_message(mn):
    """The names in the order message are file names that passed `NAME` and a highest applied name that passed `STEM`,
    both ASCII letters, digits and underscores, so the escape (`_esc`) in that message cannot be reached by a hostile
    name: the name is not late at all. This test fails if `NAME` or `STEM` ever lets such a name through unescaped
    into a message that this function builds."""
    hostile = [
        f"0004_x{ESC}[31m.sql",
        "0004_y\nz.sql",
        "0004_\udcff.sql",
        "0004_x .sql",
        "0004_X.sql",
    ]
    files = [Path(n) for n in hostile]
    texts = {p: "SELECT 1;" for p in files}
    assert mn.late_files({"0009_z"}, files) == []
    assert mn.order_problems({"0009_z"}, files, texts, "s") == []
    # and an applied name that is not a stem is not a "highest applied": nothing is late
    good = Path("0004_x.sql")
    assert mn.order_problems({f"0009_z{ESC}\n\udcff"}, [good], {good: "SELECT 1;"}, "s") == []
    # a good late file next to the hostile ones: only the good one is named, and nothing raw is printed
    msg = mn.order_problems({"0009_z"}, [good, *files], {good: "SELECT 1;"}, "s")[0]
    head = msg.split("-- RECIPE begins")[0]
    assert head.startswith("0004_x.sql would be applied out of order")
    assert ESC not in head and "\udcff" not in head and "0004_y" not in head


def test_lexer_problem_in_a_late_file_is_a_message(mn):
    msg = mn.order_problems(
        {"0009_z"}, _paths("0004_x.sql"), {Path("0004_x.sql"): "SELECT 'x;"}, "s"
    )[0]
    assert "string not closed" in msg and "-- RECIPE begins" not in msg


# --- ledger names with no file ------------------------------------------------------------------------------------


def _gone(mn, applied, names):
    return mn.gone_message(applied, [Path(n) for n in names])


REAL = [
    "0001_core.sql",
    "0002_audit_chain.sql",
    "0003_approvals_tick.sql",
    "0004_x.sql",
    "0005_evidence.sql",
]


def test_gone_message_empty_when_all_have_files(mn):
    assert _gone(mn, {"0001_core", "0005_evidence"}, REAL) == ""
    assert _gone(mn, set(), REAL) == ""


def test_gone_rename_case(mn):
    msg = _gone(mn, {"0006_evidence"}, REAL)
    lines = msg.split("\n")
    assert lines[0] == "applied migrations have no file in this release: 0006_evidence."
    assert len(lines) == 2 and "probably renamed" in lines[1] and "by hand" in lines[1]
    assert "0005_evidence" not in msg, (
        "the file's stem is not printed (an existing test depends on that)"
    )


def test_gone_newer_case(mn):
    msg = _gone(mn, {"0007_z"}, REAL)
    assert "newer than this release" in msg and "runbook" not in msg
    assert "a database administrator must look at the records before anyone changes them." in msg
    assert "drop what it made" not in msg and "by hand" not in msg


def test_gone_hotfix_collision_is_a_person_must_look(mn):
    msg = _gone(mn, {"0006_hotfix"}, [*REAL, "0006_x.sql"])
    assert "A person must look" in msg and "by hand" not in msg and "drop what it made" not in msg


def test_gone_same_text_file_that_is_itself_applied_is_not_a_rename(mn):
    msg = _gone(mn, {"0006_evidence", "0005_evidence"}, REAL)
    assert "probably renamed" not in msg, (
        "the same-text file is applied: it cannot be the renamed one"
    )
    assert "newer than this release" in msg


def test_gone_two_orphans_with_one_same_text_file_are_not_a_rename(mn):
    msg = _gone(mn, {"0006_evidence", "0007_evidence"}, REAL)
    assert "probably renamed" not in msg, "two orphans cannot both be that file"


def test_gone_name_that_is_not_a_stem_needs_a_person(mn):
    msg = _gone(mn, {"٠٠٠٢_b", ""}, REAL)
    assert msg.count("\n") == 1 and "A person must look" in msg


def test_gone_mixed_ledger_prints_one_line_per_case(mn):
    msg = _gone(mn, {"0006_evidence", "0009_z"}, REAL)
    lines = msg.split("\n")
    assert len(lines) == 3, "prefix plus one line per case present"
    assert lines[0].startswith(
        "applied migrations have no file in this release: 0006_evidence, 0009_z."
    )
    assert (
        "0006_evidence: the folder has a file" in lines[1]
        and "0009_z: this database is newer" in lines[2]
    )


def test_gone_message_names_escaped(mn):
    msg = _gone(mn, {f"0009_a{ESC}[31m", "0010_b\n0011_c"}, REAL)
    assert ESC not in msg
    assert "\\x1b" in msg and "\\n" in msg
    assert msg.count("\n") == 1, "the prefix plus one line for the one case present (3)"


def test_gone_message_prefix_in_every_case(mn):
    for applied in ({"0006_evidence"}, {"0007_z"}, {"0006_hotfix"}, {"junk"}):
        assert _gone(mn, applied, [*REAL, "0006_x.sql"]).startswith(
            "applied migrations have no file in this release: "
        )


# --- the lexer ----------------------------------------------------------------------------------------------------


def test_statement_text_exact_output(mn):
    st = mn.lex
    assert st("SELECT 'a''b';") == ("SELECT '';", "")
    assert st('SELECT "x""y" FROM t;') == ('SELECT "" FROM t;', "")
    assert st('SELECT "x""y" FROM t;', keep_quoted=True) == ('SELECT "x""y" FROM t;', "")
    assert st("SELECT '--';--c", keep_quoted=True) == ("SELECT '--'; ", "")
    assert st("a/*b*/c") == ("a c", "")
    assert st("$f$ x $f$") == ("$$", "")
    assert st("a -- c\nb") == ("a  \nb", "")
    assert st("SELECT 1 - 2 / 3;") == ("SELECT 1 - 2 / 3;", "")


def test_e_string_and_dollar_cases(mn):
    st = mn.lex
    assert st("SELECT E'a\\'b';") == ("SELECT E'';", "")
    assert st("SELECT E'a\\'b';", keep_quoted=True) == ("SELECT E'a\\'b';", "")
    assert st("SELECT e'x';") == ("SELECT e'';", "")
    for text in (
        "SELECT E'\\' ; COMMIT; --'",
        "SELECT $a$ $b$ COMMIT; $b$ $a$",
        "SELECT $a$ x $A$ COMMIT; $a$",
    ):
        assert mn.refused_statements(text) == [], text
        assert st(text)[1] == "", text


def test_e_string_continuation_is_refused(mn):
    text = "SELECT E'a'\n'\\';\nCOMMIT;\n-- it's\n"
    got = mn.lex(text)[1]
    assert got == "E'' string continued at line 2", (
        "a literal after an E literal keeps E mode on the server"
    )
    assert (
        mn.refused_statements(text)
        == ["E'' string continued at line 2"] + mn.refused_statements(text)[1:]
    )
    assert mn.lex("SELECT E'a' -- c\n /* x */ 'b';")[1] == "E'' string continued at line 2"
    assert mn.lex("SELECT 'a'\n'b';")[1] == "", "a plain literal continues in plain mode"
    assert mn.lex("SELECT E'a', 'b';")[1] == ""


def test_e_after_identifier_is_not_a_prefix(mn):
    assert mn.lex("SELECT NE'x\\';") == ("SELECT NE'';", "")


def test_dollar_after_identifier_is_not_a_tag(mn):
    assert mn.lex("SELECT a$b$ x; $b$") == (
        "SELECT a$b$ x; $$",
        "dollar body not closed at line 1",
    )


def test_non_ascii_dollar_tag(mn):
    assert mn.refused_statements("SELECT $é$ COMMIT; $é$;") == []
    assert mn.lex("SELECT $€$ x $€$;") == ("SELECT $$;", "")
    assert mn.refused_statements("SELECT $é$ x $é$; COMMIT;") == [
        "COMMIT: transaction control is not allowed (the run is one transaction)"
    ]


def test_parameters_are_left_alone(mn):
    assert mn.lex("SELECT $1, $23;") == ("SELECT $1, $23;", "")


def test_unrecognised_dollar_refuses(mn):
    assert mn.lex("SELECT $;")[1] == "unrecognised $ at line 1"
    assert mn.lex("SELECT\n$ab;")[1] == "unrecognised $ at line 2"


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("SELECT 'x;", "string not closed at line 1"),
        ('SELECT "x;', "quoted identifier not closed at line 1"),
        ("SELECT 1; /* x /* y */", "comment not closed at line 1"),
        ("SELECT 1;\n$a$ x", "dollar body not closed at line 2"),
        ("SELECT E'x\\';", "string not closed at line 1"),
    ],
)
def test_unterminated_parts_refuse_with_the_line(mn, text, problem):
    assert mn.lex(text)[1] == problem
    assert mn.lex(text, keep_quoted=True)[1] == problem, "both views give the same problem"
    assert mn.refused_statements(text)[0] == problem


def test_crlf_counts_as_one_line(mn):
    assert mn.lex("SELECT 1;\r\nSELECT 2;\r\nSELECT 'x;").__getitem__(1).endswith("at line 3")
    assert mn.lex("a\rb\rSELECT 'x;")[1].endswith("at line 3")


def test_comment_ends_at_cr(mn):
    for text, word in (
        (f"-- x{CR}COMMIT;", "COMMIT"),
        (f"-- x{CR}SET ROLE r;", "SET"),
        (f"-- x{CR}{LF}COMMIT;", "COMMIT"),
        (f"SELECT 1;{CR}COMMIT;", "COMMIT"),
        (f"SELECT 1;{FF}COMMIT;", "COMMIT"),
        (f"SELECT 1;{VT}COMMIT;", "COMMIT"),
    ):
        got = mn.refused_statements(text)
        assert any(r.startswith(word) for r in got), repr(
            text
        )  # a vertical tab is also a hidden character
    assert mn.refused_statements(f"-- x{LF}COMMIT;")[0].startswith("COMMIT"), (
        "the line feed control"
    )
    assert mn.refused_statements(f"SELECT 1; -- x{CR}SELECT 2;") == [], (
        "nothing hides after a plain comment"
    )


def test_apostrophe_in_a_comment_does_not_hide_a_statement(mn):
    assert mn.refused_statements("-- it's\nCOMMIT;")[0].startswith("COMMIT")
    assert mn.refused_statements("-- it's\nSET ROLE x;")[0].startswith("SET")
    assert mn.refused_statements("SELECT '--'; COMMIT;")[0].startswith("COMMIT")
    assert mn.refused_statements("SELECT E'a\\'b'; COMMIT;")[0].startswith("COMMIT")
    assert mn.refused_statements('SELECT "it\'s"; COMMIT;')[0].startswith("COMMIT")
    assert mn.refused_statements("/* a /* b */ COMMIT; */ SELECT 1;") == [], (
        "a nested comment hides it"
    )


def test_statement_start_anchor(mn):
    for text in (
        "SELECT CASE WHEN true THEN 1 END;",
        "COMMENT ON TABLE runs IS 'begin';",
        "ALTER TABLE t ADD COLUMN release TEXT;",
        "CREATE TRIGGER t AFTER INSERT ON x FOR EACH ROW EXECUTE FUNCTION f();",
        "UPDATE t SET a = 1;",
        "SELECT set_config('a','b',true);",
        "SELECT * FROM commits;",
    ):
        assert mn.refused_statements(text) == [], text


@pytest.mark.parametrize(
    "stmt",
    [
        "COMMIT",
        "END",
        "BEGIN",
        "START TRANSACTION",
        "ROLLBACK",
        "ABORT",
        "SAVEPOINT a",
        "RELEASE a",
        "PREPARE TRANSACTION 'x'",
        "commit",
        "Start\n  Transaction",
    ],
)
def test_each_transaction_word_is_refused(mn, stmt):
    got = mn.refused_statements(f"SELECT 1; {stmt};")
    assert len(got) == 1 and "transaction control" in got[0], stmt


@pytest.mark.parametrize(
    "stmt",
    [
        "SET ROLE r",
        "SET LOCAL ROLE r",
        "SET SESSION AUTHORIZATION r",
        "RESET ROLE",
        "SET TRANSACTION READ ONLY",
        "SET LOCAL search_path TO x",
        "SET session_replication_role = replica",
        "RESET ALL",
        "set x to 1",
    ],
)
def test_each_set_form_is_refused(mn, stmt):
    got = mn.refused_statements(f"SELECT 1; {stmt};")
    assert len(got) == 1 and "may not be changed" in got[0], stmt


@pytest.mark.parametrize(
    "stmt", ["SET LOCAL lock_timeout = '10s'", "set  local  statement_timeout TO 0"]
)
def test_the_two_allowed_set_forms_pass(mn, stmt):
    assert mn.refused_statements(f"{stmt};") == []


@pytest.mark.parametrize(
    "stmt",
    [
        "DO $$ BEGIN NULL; END $$",
        "EXECUTE p",
        "ALTER ROLE x SET y = 1",
        "ALTER USER x",
        "ALTER DATABASE d SET y TO 1",
        "DROP OWNED BY r",
        "REASSIGN OWNED BY a TO b",
    ],
)
def test_each_blind_statement_is_refused(mn, stmt):
    got = mn.refused_statements(f"SELECT 1; {stmt};")
    assert len(got) == 1 and "the guard cannot read" in got[0], stmt


def test_text_rules_leave_set_config_and_trigger_state_to_the_readback(mn):
    for text in (
        "SELECT set_config('search_path','x',true)",
        "SELECT \"set_config\"('search_path','x',true)",
        "COMMENT ON TABLE runs IS 'set_config'",
        "ALTER TABLE audit_entries DISABLE TRIGGER audit_entries_append_only",
        "ALTER TABLE t ENABLE REPLICA TRIGGER x",
        "ALTER TABLE t ENABLE ALWAYS TRIGGER x",
        "DROP TRIGGER x ON t",
    ):
        assert mn.refused_statements(text + ";") == [], text


def test_false_positives_stay_clean(mn):
    for text in (
        "SELECT 'COMMIT; SET ROLE x; DO';",
        "CREATE FUNCTION f() RETURNS int AS $$ BEGIN RETURN 1; END $$ LANGUAGE plpgsql;",
    ):
        assert mn.refused_statements(text) == [], text


def test_the_real_files_read_clean(mn):
    counts = []
    for p in _real(mn):
        text = p.read_text(encoding="utf-8")
        cleaned, problem = mn.lex(text)
        assert problem == "", p.name
        assert mn.refused_statements(text) == [], p.name
        counts.append(len([s for s in cleaned.split(";") if s.strip()]))
    # the first five files are the released ones (34 statements, the ticket's counts); a new file may follow
    assert len(counts) >= 5 and counts[:5] == [12, 9, 8, 2, 3]


def test_a_million_characters_finish(mn):
    text = "SELECT 'a''b' /* c */ -- d\n;" * 40000
    assert len(text) > 1_000_000
    assert mn.lex(text)[1] == ""


def _median_time(fn, text: str) -> float:
    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        fn(text)
        runs.append(time.perf_counter() - t0)
    return statistics.median(runs)


@pytest.mark.perf
def test_lexer_is_linear(mn):
    small, big = 16 * 1024, 256 * 1024
    units = ["'", '"', "$a$", "/*", "--", "E'\\", ";", "$a$ x ", "a$"]
    slow = [
        (fn.__name__, unit)
        for fn in (mn.lex, mn.refused_statements)
        for unit in units
        if timing.is_superlinear(lambda t, f=fn: _median_time(f, t), unit, small, big)
    ]
    assert not slow, slow


@pytest.mark.perf
def test_the_timing_harness_flags_a_quadratic_stand_in():
    def quadratic(t: str) -> float:
        return _median_time(lambda s: sum(s.count("a", 0, i) for i in range(0, len(s), 64)), t)

    assert timing.is_superlinear(quadratic, "a", 16 * 1024, 256 * 1024), (
        "a quadratic function must be flagged"
    )


# --- seeded property tests ----------------------------------------------------------------------------------------

ALPHABET = list("'\"$-/*\\;EeUa&é") + [LF, CR, FF, VT] + list("comitsdnbg ")


def test_lexer_property_never_raises_and_cr_equals_lf(mn):
    rng = Seeded(FUZZ_SEED)
    for case in range(FUZZ_CASES):
        text = "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 40)))
        cleaned, problem = mn.lex(text)  # must never raise
        _, problem_kept = mn.lex(text, keep_quoted=True)
        msg = f"seed {FUZZ_SEED} case {case}: {text!r}"
        assert problem == problem_kept, msg
        if not problem:
            assert "--" not in cleaned and "/*" not in cleaned, msg
        swapped = text.replace(LF, CR)
        strip = lambda rs: [r.split(" at line ")[0] for r in rs]
        assert strip(mn.refused_statements(swapped)) == strip(mn.refused_statements(text)), msg


def test_ledger_property_only_the_named_error_and_agreement(mn, tmp_path):
    rng = Seeded(FUZZ_SEED)
    pool = [
        "0001_a.sql",
        "0002_b.sql",
        "0003_c.sql",
        "0003_d.sql",
        "0005_e.sql",
        "٠٠٠٢_f.sql",
        "0000_g.sql",
        "1_h.sql",
        "0004_I.sql",
        "x.txt",
        "0006_ok.sql.bak",
    ]
    for case in range(200):
        folder = tmp_path / str(case)
        folder.mkdir()
        names = rng.sample(pool, rng.randint(0, len(pool)))
        _folder(folder, names)
        files = mn.list_migration_files(folder)
        assert mn.folder_problems(folder) == mn.check_ledger(files), f"{FUZZ_SEED} {names}"
        applied = set(
            rng.sample(["0001_a", "0002_b", "0007_z", "junk", "", "٠٠٠٢_f"], rng.randint(0, 6))
        )
        msg = mn.gone_message(applied, files)  # must never raise
        mn.late_files(applied, files)
        orphans = [a for a in applied if a not in {f.name[:-4] for f in files}]
        assert len(msg.split("\n")) <= 1 + 3 and (msg == "") == (not orphans)
    valid = ["0001_a.sql", "0002_b.sql", "0003_c.sql"]
    sub = tmp_path / "valid"
    sub.mkdir()
    _folder(sub, valid)
    mn.check_migration_numbers(sub)
    assert mn.late_files({"0001_a", "0002_b"}, mn.list_migration_files(sub)) == []


# --- the inbound ledger migration (AK-G2-a): file 0006 follows the released files and reads clean -------------------


def test_the_inbound_migration_is_the_next_number_and_is_not_yet_released(mn):
    import json

    manifest = json.loads(
        (Path(__file__).parent / "fixtures" / "migrations_released.json").read_text("utf-8")
    )
    names = [p.name for p in _real(mn)]
    assert "0006_inbound.sql" in names and "0006_inbound" not in manifest
    assert (
        mn.released_problems(mn.MIGRATIONS, manifest) == []
    )  # a file numbered above the highest released one
    assert names.index("0006_inbound.sql") == 5 and len({n[:4] for n in names}) == len(names)


def test_the_inbound_migration_reads_clean_and_holds_the_fifteen_statements_of_the_ticket(mn):
    path = next(p for p in _real(mn) if p.name == "0006_inbound.sql")
    text = path.read_text(encoding="utf-8")
    cleaned, problem = mn.lex(text)
    assert problem == "" and mn.refused_statements(text) == [] and mn.hidden_character(text) == ""
    statements = [" ".join(s.split()) for s in cleaned.split(";") if s.strip()]
    heads = [" ".join(s.split()[:4]) for s in statements]
    assert sum(h.startswith("CREATE TABLE inbound_key_checks") for h in heads) == 1
    assert sum(h.startswith("CREATE TABLE inbound_") for h in heads) == 4
    assert sum(h.startswith("CREATE INDEX") for h in heads) == 2
    assert sum(h.startswith("CREATE OR REPLACE FUNCTION") for h in heads) == 3
    assert sum(h.startswith("CREATE OR REPLACE TRIGGER") for h in heads) == 3
    assert sum(h.startswith("ALTER TABLE") for h in heads) == 3
    assert len(statements) == 15
