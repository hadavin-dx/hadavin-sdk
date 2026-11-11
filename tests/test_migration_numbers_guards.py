"""P3a-1 fix 1: tests for the findings of review round 1 on PR 68 (hidden characters, the dollar rule, a lexer that
fails closed, plain-words messages, the lock key, a refusal list that covers more, the released-file manifest) and the
differential test against the PostgreSQL scanner (pglast, test-only: GPL-3.0, never imported by the product)."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import multiprocessing
import pickle
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from tests.fixtures import timing
from tests.fixtures.seeded import Seeded

SEED = 20261106
CASES = 30000
MANIFEST = Path(__file__).parent / "fixtures" / "migrations_released.json"


@pytest.fixture
def mn():
    import hadavin_sdk.store.migration_numbers as module

    return module


# --- 1. characters that make a reviewer read different text from what psql runs ------------------------------------------

HIDDEN = [
    "\u202e",  # right-to-left override (Cf)
    "\u2066",  # left-to-right isolate (Cf)
    "\u2067",
    "\u2068",
    "\u2069",
    "\u200b",  # zero-width space (Cf)
    "\u200d",  # zero-width joiner (Cf)
    "\ufeff",  # byte order mark / zero-width no-break space (Cf)
    "\u2028",  # line separator (Zl)
    "\u2029",  # paragraph separator (Zp)
    "\x1b",  # escape (Cc)
    "\x7f",  # delete (Cc)
    "\x85",  # next line (Cc)
]


@pytest.mark.parametrize("ch", HIDDEN, ids=lambda c: f"U+{ord(c):04X}")
def test_hidden_characters_are_refused_in_a_file_and_in_a_late_file(mn, ch):
    text = f"SELECT 1; -- a{ch}b\n"
    got = mn.refused_statements(text)
    assert len(got) == 1 and f"U+{ord(ch):04X}" in got[0] and "line 1" in got[0], got
    with pytest.raises(ValueError, match=f"U\\+{ord(ch):04X}"):
        mn.hand_recipe([("0004_x", text)], "s")


def test_the_allowed_blanks_and_ordinary_letters_pass(mn):
    text = (
        "SELECT 'café\t';\r\n\fSELECT 2;\u00a0\n"  # tab, CR, LF, FF, e-acute and a no-break space
    )
    assert mn.refused_statements(text) == []
    assert mn.hand_recipe([("0004_x", text)], "s")


def test_a_byte_order_mark_at_the_start_is_named(mn, tmp_path):
    f = tmp_path / "0001_a.sql"
    f.write_bytes(b"\xef\xbb\xbfSELECT 1;\n")
    text = mn.read_files([f])[f]
    got = mn.refused_statements(text)
    assert len(got) == 1 and "byte order mark" in got[0] and "without it" in got[0], got


def test_a_hidden_character_is_found_on_its_own_line(mn):
    got = mn.refused_statements("SELECT 1;\r\nSELECT 2;\n-- x\u202ey\n")
    assert "line 3" in got[0], got


# --- 2. a late file may not carry what ends the one transaction (review M1) --------------------------------------------


@pytest.mark.parametrize(
    "sql", ["COMMIT;", "ROLLBACK;", "SET ROLE x;", "SELECT 1; END;", "RESET ALL;"]
)
def test_a_late_file_with_transaction_control_or_a_setting_gets_no_recipe(mn, sql):
    with pytest.raises(ValueError, match="0004_x"):
        mn.hand_recipe([("0004_x", sql)], "s")
    got = mn.order_problems({"0005_y"}, [Path("0004_x.sql")], {Path("0004_x.sql"): sql}, "s")
    assert len(got) == 1 and "RECIPE begins" not in got[0] and "No recipe is printed" in got[0]


# --- 3. the dollar rule: a `$` is part of a name only after a NAME, not after a digit or a closing `$` ------------------


def test_dollar_tag_right_after_a_closing_dollar_quote(mn):
    text = "SELECT $a$x$a$$b$ ' $b$; COMMIT; SELECT $c$ ' $c$;"
    assert mn.lex(text) == ("SELECT $$$$; COMMIT; SELECT $$;", "")
    assert mn.refused_statements(text) == [
        "COMMIT: transaction control is not allowed (the run is one transaction)"
    ]


def test_dollar_tag_right_after_a_number(mn):
    # PostgreSQL scans `1` and then the string `$a$ ' $a$` (checked against pglast 8.7)
    assert mn.lex("SELECT 1$a$ ' $a$;") == ("SELECT 1$$;", "")
    assert mn.refused_statements("SELECT 1$a$ ' $a$; COMMIT;") != []


def test_e_prefix_right_after_a_closing_dollar_quote(mn):
    assert mn.lex("SELECT $a$x$a$E'a\\'b';") == ("SELECT $$E'';", "")


def test_a_dollar_after_a_name_is_still_part_of_the_name(mn):
    assert mn.lex("SELECT a1$b$ x; $b$") == (
        "SELECT a1$b$ x; $$",
        "dollar body not closed at line 1",
    )
    assert mn.lex("SELECT a$ ' x") == ("SELECT a$ '", "string not closed at line 1")


def test_a_dollar_right_after_a_dollar_inside_a_name(mn):
    # `a$$` is one name for the server (name characters include `$`), so no tag opens and COMMIT stays live
    assert mn.lex("SELECT a$$ x; COMMIT;") == ("SELECT a$$ x; COMMIT;", "")
    assert mn.refused_statements("SELECT a$$ x; COMMIT;") != []


# --- 4. the lexer fails closed -------------------------------------------------------------------------------------------


def test_checked_statement_text_raises_instead_of_returning_a_cut_text(mn):
    assert issubclass(mn.SqlReadError, ValueError)
    with pytest.raises(mn.SqlReadError, match="string not closed at line 2"):
        mn.checked_statement_text("SELECT 1;\nSELECT 'a")
    with pytest.raises(mn.SqlReadError, match="comment not closed"):
        mn.checked_statement_text("SELECT 1 /* a")
    assert mn.checked_statement_text("SELECT 'a' /* c */;") == "SELECT ''  ;"
    assert mn.checked_statement_text("SELECT 'a' /* c */;", keep_quoted=True) == "SELECT 'a'  ;"


def test_statement_text_called_the_ticket_way_returns_the_pair(mn):
    """Ticket P3a: `statement_text(text, keep_quoted=False) -> tuple[str, str]`. P3a-2 builds `_scan` from the ticket,
    so these are the calls it will write. A function that returned a bare `str` would make `[0]` one character and
    the unpacking either fail or split a two-character text: both are tested."""
    sql = "SELECT 'a' /* c */;"
    cleaned, problem = mn.statement_text(sql)
    assert (cleaned, problem) == ("SELECT ''  ;", "")
    kept, problem = mn.statement_text(
        sql, True
    )  # keep_quoted by position, as the ticket's `_scan` call
    assert (kept, problem) == ("SELECT 'a'  ;", "")
    result = mn.statement_text(sql, keep_quoted=True)
    assert isinstance(result, tuple) and len(result) == 2
    assert result[0] == "SELECT 'a'  ;", "[0] is the whole text, not a character"
    assert len(result[0]) > 1 and isinstance(result[1], str)
    # a text with a problem is a value in the pair, not an exception: the caller must look at it
    cut, problem = mn.statement_text("SELECT 1;\nSELECT 'a")
    assert problem == "string not closed at line 2" and cut.startswith("SELECT 1;")
    # and the other function is a bare str: unpacking it as a pair fails loudly instead of splitting the text
    with pytest.raises(ValueError):
        _, _ = mn.checked_statement_text("SELECT 1;")
    assert isinstance(mn.checked_statement_text("SELECT 1;"), str)
    assert mn.lex(sql) == mn.statement_text(sql)


def test_lex_returns_the_text_and_the_problem(mn):
    assert mn.lex("SELECT 'a") == ("SELECT '", "string not closed at line 1")
    assert mn.lex("SELECT 1;") == ("SELECT 1;", "")


# --- 5. messages in plain words ------------------------------------------------------------------------------------------

JARGON = ("stem", "ledger", "migration lock", "runbook")


def test_gone_messages_use_plain_words(mn):
    files = [Path("0001_a.sql"), Path("0002_b.sql"), Path("0004_x.sql")]
    applied = {
        "0001_a",
        "0002_b",
        "0003_x",
        "0009_newer",
        "junk",
    }  # a rename, a newer database, a person must look
    got = mn.gone_message(applied, files)
    assert "by hand" in got
    for word in JARGON:
        assert word not in got.lower(), (word, got)
    assert got.startswith("applied migrations have no file in this release:")


def test_order_message_uses_plain_words_and_numbered_steps(mn):
    f = Path("0002_b.sql")
    got = mn.order_problems({"0003_c"}, [f], {f: "SELECT 1;"}, "s")[0]
    for word in JARGON:
        assert word not in got.lower(), (word, got)
    assert got.startswith("0002_b.sql would be applied out of order")
    assert "What to do" in got and "\n1. " in got and "\n2. " in got
    assert mn.RECIPE_COMMAND in got
    refused = mn.order_problems({"0003_c"}, [f], {f: "COMMIT;"}, "s")[0]
    for word in JARGON:
        assert word not in refused.lower(), (word, refused)


# --- 6. the lock key has one source -----------------------------------------------------------------------------------


def _assigned(path: Path, name: str):
    """The expression assigned to the module-level `name` in the source file `path`, parsed and not run (the module
    `migrate` imports psycopg; this test must not)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return node.value
    return None


def _imports_from_numbers(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(n, ast.ImportFrom)
        and n.module == "hadavin_sdk.store.migration_numbers"
        and any(a.name == name for a in n.names)
        for n in tree.body
    )


def test_the_lock_key_and_the_folder_are_the_ones_migrate_uses(mn):
    """`migrate.py` keeps its own copies of the lock key (`_LOCK`) and the folder (`MIGRATIONS`) until P3a-2 makes it
    import them from this module. Until then this test reads that file as text (no import, so no psycopg) and requires
    the SAME expression for each. After P3a-2, `migrate.py` imports the name from here and the test accepts that."""
    here = Path(mn.__file__)
    other = here.with_name("migrate.py")
    assert other.is_file()
    lock_here = ast.dump(_assigned(here, "MIGRATE_LOCK"))
    lock_there = _assigned(other, "_LOCK")
    assert lock_there is not None or _imports_from_numbers(other, "MIGRATE_LOCK")
    if lock_there is not None:
        assert ast.dump(lock_there) == lock_here
    folder_there = _assigned(other, "MIGRATIONS")
    assert folder_there is not None or _imports_from_numbers(other, "MIGRATIONS")
    if folder_there is not None:
        assert ast.dump(folder_there) == ast.dump(_assigned(here, "MIGRATIONS"))
    # the value itself, computed here from the same bytes: a change of the expression in both files is still caught
    assert mn.MIGRATE_LOCK == int.from_bytes(b"hadvnmig", "big") >> 1
    assert isinstance(mn.MIGRATE_LOCK, int)
    assert mn.MIGRATIONS == here.parent / "migrations" == other.parent / "migrations"


def test_no_dead_runbook_constant(mn):
    assert not hasattr(mn, "RUNBOOK_E")


# --- 7. the refusal list covers more ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stmt",
    [
        "COPY t TO PROGRAM 'x'",
        "copy t from program 'x'",
        "COPY (SELECT 1) TO PROGRAM 'x'",
        "LOAD 'x'",
        "ALTER SYSTEM SET work_mem = 1",
        "CREATE ROLE r",
        "CREATE USER r",
        "CREATE GROUP r",
        "CREATE EXTENSION e",
        "DISCARD ALL",
        "ALTER GROUP g ADD USER u",
        "GRANT r TO s",
        "REVOKE r FROM s",
    ],
)
def test_more_blind_statements_are_refused(mn, stmt):
    got = mn.refused_statements(f"SELECT 1; {stmt};")
    assert len(got) == 1 and "the guard cannot read" in got[0], (stmt, got)


@pytest.mark.parametrize(
    "stmt",
    [
        "GRANT SELECT ON t TO r",
        "GRANT USAGE ON SCHEMA s TO r",
        "GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA s TO r",
        "REVOKE ALL ON t FROM PUBLIC",
        "COPY t TO STDOUT",
        "CREATE TABLE copy_program (x int)",
        "COMMENT ON TABLE t IS 'LOAD it; ALTER SYSTEM'",
    ],
)
def test_the_new_refusals_leave_ordinary_statements_alone(mn, stmt):
    assert mn.refused_statements(f"{stmt};") == [], stmt


def test_begin_atomic_is_refused_and_the_message_says_what_to_write(mn):
    got = mn.refused_statements(
        "CREATE FUNCTION f() RETURNS int LANGUAGE sql BEGIN ATOMIC SELECT 1; END;"
    )
    assert got and all("$$" in r for r in got), got


# --- 8. lexer cases that had no test ---------------------------------------------------------------------------------------


def test_unicode_escape_strings_are_plain_strings_for_the_lexer(mn):
    # U&'..' and UESCAPE: the backslash is no escape in a standard string; the server reads the same two strings
    assert mn.lex("SELECT U&'d\\0061t' UESCAPE '!';") == ("SELECT U&'' UESCAPE '';", "")
    assert mn.refused_statements("SELECT U&'\\'; COMMIT;") != []


def test_crlf_inside_an_e_string_continuation_is_one_line(mn):
    assert mn.lex("SELECT E'a'\r\n'b';")[1] == "E'' string continued at line 2"


def test_nbsp_is_not_a_blank_for_the_server_and_not_for_us(mn):
    assert (
        mn.refused_statements("SELECT 1;\u00a0COMMIT;") == []
    )  # the server reads one odd name and fails the file
    assert mn.refused_statements("COMMIT\u00a0;") != []  # refused: the safe direction


def test_a_huge_applied_number_makes_every_unapplied_file_late(mn):
    files = [Path("0001_a.sql"), Path("0002_b.sql")]
    assert mn.late_files({"9999_z"}, files) == files


# --- 9. gone_message and order_problems on hostile sizes and inputs -------------------------------------------------------------


def test_gone_message_caps_the_names_and_stays_fast(mn):
    applied = {f"{n % 9000 + 100:04d}_same" for n in range(5000)} | {
        f"0100_x{n}" for n in range(5000)
    }
    t0 = timing.CLOCK()
    got = mn.gone_message(applied, [Path("0001_a.sql")])
    assert timing.CLOCK() - t0 < 5
    assert len(got) < 6000, f"names not capped: {len(got)}"
    assert re.search(r"and \d+ more", got)


def test_order_problems_with_a_missing_text_is_a_message_not_an_exception(mn):
    f = Path("0002_b.sql")
    got = mn.order_problems({"0003_c"}, [f], {}, "s")
    assert len(got) == 1 and "No recipe is printed" in got[0] and "0002_b.sql" in got[0]


# --- 10. forward-only: a released file may not change (review design 8) ---------------------------------------------------------


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_the_real_folder_matches_the_released_manifest(mn):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert mn.released_problems(mn.MIGRATIONS, manifest) == []
    assert len(manifest) == 5


def test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number(mn, tmp_path):
    for name, body in (("0001_a.sql", "SELECT 1;\n"), ("0002_b.sql", "SELECT 2;\n")):
        (tmp_path / name).write_bytes(body.encode())
    manifest = {p.name[:-4]: _sha(p) for p in sorted(tmp_path.glob("*.sql"))}
    assert mn.released_problems(tmp_path, manifest) == []
    (tmp_path / "0003_c.sql").write_text(
        "SELECT 3;\n"
    )  # a new file above the released ones is fine
    assert mn.released_problems(tmp_path, manifest) == []
    (tmp_path / "0002_b.sql").write_bytes(b"SELECT 2; -- edited\n")
    assert mn.released_problems(tmp_path, manifest) == ["0002_b: a released file was changed"]
    (tmp_path / "0002_b.sql").write_bytes(b"SELECT 2;\r\n")  # a Windows line ending is not a change
    assert mn.released_problems(tmp_path, manifest) == []
    (tmp_path / "0001_a.sql").unlink()
    assert mn.released_problems(tmp_path, manifest) == ["0001_a: a released file is missing"]
    (tmp_path / "0001_a.sql").write_bytes(b"SELECT 1;\n")
    (tmp_path / "0003_c.sql").unlink()
    (tmp_path / "0002_zz.sql").write_text("SELECT 9;\n")
    assert mn.released_problems(tmp_path, manifest) == [
        "0002_zz: a new migration is numbered at or below the highest released one (0002_b)"
    ]


# --- 11. differential test against the PostgreSQL scanner (pglast is GPL-3.0: test-only, skipped if absent) -------------------

PIECES = [
    "$a$",
    "$a$",
    "$b$",
    "$",
    "'",
    "E'",
    '"',
    " ",
    "1",
    "a",
    ";",
    "COMMIT",
    "COMMIT;",
    "/*",
    "*/",
    "--",
    "\n",
    "\\",
    "e",
    "x",
]
ALPHABET = list("'\"$-/*\\;EeUa&é") + ["\n", "\r", "\f"] + list("comitsdnbg 1")


def _word(token: str) -> str:
    if token[:1] in "'\"":
        return "Q"
    m = re.match(r"[A-Za-z_]+", token)
    return m.group(0).upper() if m else token[:1]


def _server_statement_starts(sql: str):
    """The first token of each statement as the PostgreSQL scanner sees it; None when the scanner refuses the text."""
    from pglast import parser

    try:
        tokens = parser.scan(sql)
    except parser.ParseError:  # the scanner refused the whole text: that is the answer
        return None
    out: list[str] = []
    at_start = True
    for t in tokens:
        if t.name in ("C_COMMENT", "SQL_COMMENT"):
            continue
        if t.name == "ASCII_59":
            at_start = True
        elif at_start:
            out.append(_word(sql[t.start : t.end + 1]))
            at_start = False
    return out


def _our_statement_starts(mn, sql: str):
    cleaned, problem = mn.lex(sql)
    if problem:
        return None
    out = []
    for stmt in cleaned.split(";"):
        s = stmt.lstrip(mn._WS)
        if s:
            m = re.match(r"[A-Za-z_\u0080-\uffff][A-Za-z0-9_$\u0080-\uffff]*|.", s)
            out.append(_word(m.group(0)))
    return out


def _differential(mn, pieces, cases, longest):
    rng = Seeded(SEED)
    agreed = refused_by_us = server_refused = 0
    for case in range(cases):
        sql = "".join(rng.choice(pieces) for _ in range(rng.randint(0, longest)))
        theirs = _server_statement_starts(sql)
        if theirs is None:
            server_refused += 1  # the server fails the whole file: nothing to hide
            continue
        ours = _our_statement_starts(mn, sql)
        if ours is None:
            refused_by_us += 1  # we refuse text the server reads: the safe direction
            continue
        assert ours == theirs, f"seed {SEED} case {case}: {sql!r}: server {theirs} ours {ours}"
        agreed += 1
    return agreed, refused_by_us, server_refused


def test_lexer_agrees_with_the_postgresql_scanner_on_statement_starts(mn):
    pytest.importorskip("pglast")
    agreed, refused_by_us, server_refused = _differential(mn, PIECES, CASES, 12)
    assert agreed > CASES // 4, (agreed, refused_by_us, server_refused)
    agreed2, _, _ = _differential(mn, ALPHABET, CASES, 30)
    assert agreed2 > CASES // 4


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; /* a /* b */ COMMIT; */ ; SELECT 2;",
        "SELECT 1; -- a\rCOMMIT;",
        "SELECT $é$ COMMIT; $é$; COMMIT;",
        "SELECT '\\'; COMMIT;",
        "SELECT E'\\'; COMMIT;';",
        "SELECT $a$ x $A$ COMMIT; $a$; COMMIT;",
        "SELECT a$b$ x; $b$ y $b$;",
        "SELECT $a$x$a$$b$ ' $b$; COMMIT;",
        "SELECT 1$a$ ' $a$; COMMIT;",
        "SELECT U&'\\'; COMMIT;",
        "SELECT a$$ x; COMMIT;",
    ],
)
def test_probe_cases_agree_with_the_scanner(mn, sql):
    pytest.importorskip("pglast")
    theirs = _server_statement_starts(sql)
    ours = _our_statement_starts(mn, sql)
    assert theirs is not None
    assert ours == theirs, (sql, theirs, ours)


# --- 8. the error survives copy and pickle ----------------------------------------------------------------------------------


def _echo(value):
    return value


def _same_error(mn, original, other):
    assert type(other) is mn.MigrationNumberError and other is not original
    assert other.problems == original.problems == ("a", "b")
    assert str(other) == str(original) == "migrations are inconsistent: a; b"


def test_migration_number_error_survives_copy_deepcopy_and_pickle(mn):
    err = mn.MigrationNumberError(["a", "b"])
    _same_error(mn, err, copy.copy(err))
    _same_error(mn, err, copy.deepcopy(err))
    # a pickle round trip in both directions: a worker process receives the error and returns it (the standard library
    # does the pickling and the unpickling; this test loads no pickle by hand)
    assert pickle.dumps(err)
    with ProcessPoolExecutor(
        max_workers=1, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        _same_error(mn, err, pool.submit(_echo, err).result(timeout=120))
    # a long list keeps all problems and the same capped message
    many = mn.MigrationNumberError([f"p{i}" for i in range(25)])
    twin = copy.copy(many)
    assert len(twin.problems) == 25 and str(twin) == str(many)
    assert str(twin).endswith("and 5 more")
    assert isinstance(twin, mn.ConfigError)


# --- 9. the mutants file cannot rot ------------------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


def test_every_mutant_still_applies_to_the_source():
    """The slow run is `python tests/migration_numbers_mutants.py` (its docstring has the command). This cheap check
    runs with the ordinary tests: every mutant's `old` text is still in its file (so the mutation changes something),
    differs from `new`, its killer test exists, and no mutant name is used twice."""
    if not (ROOT / "tests" / "migration_numbers_mutants.py").is_file():
        pytest.skip(
            "the mutants file is not in this tree (the mutant runner copies only some test files)"
        )
    from tests import migration_numbers_mutants as mutants

    names = [m.name for m in mutants.M]
    assert len(names) == len(set(names)) >= 36, "mutant names are unique and none was dropped"
    for m in mutants.M:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        assert m.old in text, f"{m.name}: the text to change is no longer in {m.file}"
        assert m.new != m.old, m.name
        test_path, _, test_id = m.pinned.partition("::")
        function = test_id.split("[")[0]
        assert f"def {function}(" in (ROOT / f"{test_path}.py").read_text(encoding="utf-8"), m.name
