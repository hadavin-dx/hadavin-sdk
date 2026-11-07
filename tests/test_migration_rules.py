"""Rules about the P3a-2 wiring that are not a database test (ledger rows BL-p3a2-001..003 and the order 103 caller rule):

1. a test of `migrate()` never skips silently: no skip when `HADAVIN_TEST_PG_DSN` is set, a reason when it is not;
2. every caller of `lex` / `statement_text` unpacks the PAIR and every caller of `checked_statement_text` takes a `str`;
3. the `migrate()` docstring says where role membership is changed;
4. a tripwire: the refusal of `GRANT r TO s` / `REVOKE r FROM s` (role membership, no `ON`) is compared with the
   PostgreSQL parser (pglast, a test-only package: never imported by the product) over every form of the grammar, so a
   later standalone `on` that the lexer's emptied view leaves in such a statement fails here, loudly;
5. the CHANGELOG no longer gives the false evidence file name and carries the runbook with the real lock and command.
"""

from __future__ import annotations

import ast
import itertools
import types
from pathlib import Path

import pglast
import pytest
from pglast import parser

from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import migration_numbers as mn
from tests.fixtures.dsn_skip import DSN_NAME, require_module

ROOT = Path(__file__).resolve().parents[1]
P3A2_TEST_FILES = [
    "tests/test_migration_wiring.py",
    "tests/test_migration_postgres.py",
    "tests/test_migration_rules.py",
]


# --- 1. no silent skip -------------------------------------------------------------------------------------------------


def _missing(_name: str):
    raise ImportError("made up")


def _outcome(environ):
    """What `require_module` does for a driver that cannot be imported: "fail", "skip" (with its text) or "returned".
    A skip is caught here, so a skip where a failure is required shows as a wrong outcome and fails the test (a bare
    skip would only mark the test as skipped, and the run would stay green)."""
    try:
        require_module("psycopg", environ, _missing)
    except pytest.fail.Exception as e:
        return "fail", str(e)
    except pytest.skip.Exception as e:
        return "skip", str(e)
    return "returned", ""


def test_a_missing_driver_with_the_dsn_set_is_a_failure():
    kind, text = _outcome({DSN_NAME: "postgresql://x"})
    assert kind == "fail", (kind, text)
    assert "psycopg cannot be imported but HADAVIN_TEST_PG_DSN is set" in text


@pytest.mark.parametrize("environ", [{}, {DSN_NAME: ""}])
def test_a_missing_driver_without_the_dsn_is_a_skip_with_a_reason(environ):
    kind, text = _outcome(environ)
    assert kind == "skip", (kind, text)
    assert "psycopg is not installed" in text and DSN_NAME in text


def test_a_present_module_is_returned():
    marker = types.ModuleType("made_up")
    assert require_module("made_up", {DSN_NAME: "x"}, lambda _n: marker) is marker


def _is_not_dsn(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.Not)
        and isinstance(node.operand, ast.Name)
        and node.operand.id == "DSN"
    )


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def skip_violations(source: str) -> list[str]:
    """Every way a test file can skip that the DSN rule does not allow. Allowed: `skipif(not DSN, reason=<text naming
    the variable>)`, and `pytest.skip(...)` under `if not DSN:`. Everything else (importorskip, a bare skip or xfail
    mark, a skip anywhere else) is returned."""
    tree = ast.parse(source)
    parent = _parents(tree)
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("importorskip", "xfail"):
            out.append(f"line {node.lineno}: {node.attr}")
        elif isinstance(node, ast.Attribute) and node.attr == "skip":
            owner = node.value
            if isinstance(owner, ast.Attribute) and owner.attr == "mark":
                out.append(f"line {node.lineno}: unconditional skip mark")
            elif (
                isinstance(owner, ast.Name)
                and owner.id == "pytest"
                and isinstance(parent.get(node), ast.Call)
            ):
                chain, up = [], parent.get(node)
                while up is not None:
                    chain.append(up)
                    up = parent.get(up)
                if not any(isinstance(a, ast.If) and _is_not_dsn(a.test) for a in chain):
                    out.append(f"line {node.lineno}: pytest.skip outside `if not DSN:`")
        elif isinstance(node, ast.Attribute) and node.attr == "skipif":
            call = parent.get(node)
            reason = {k.arg: k.value for k in getattr(call, "keywords", [])}.get("reason")
            ok = (
                isinstance(call, ast.Call)
                and call.args
                and _is_not_dsn(call.args[0])
                and isinstance(reason, ast.Constant)
                and DSN_NAME in str(reason.value)
            )
            if not ok:
                out.append(
                    f"line {node.lineno}: skipif that is not `not DSN` with a reason naming {DSN_NAME}"
                )
    return out


@pytest.mark.parametrize(
    "source",
    [
        "pytest.importorskip('x')",
        "@pytest.mark.skip\ndef t(): pass",
        "def t():\n    pytest.skip('r')",
        "@pytest.mark.skipif(sys.platform != 'linux', reason='x')\ndef t(): pass",
        "@pytest.mark.skipif(not DSN, reason='no database')\ndef t(): pass",
        "if DSN:\n    pytest.skip('r')",
        "@pytest.mark.xfail\ndef t(): pass",
    ],
)
def test_the_skip_rule_flags_each_unguarded_skip(source):
    assert skip_violations(source), source


@pytest.mark.parametrize(
    "source",
    [
        "@pytest.mark.skipif(not DSN, reason='HADAVIN_TEST_PG_DSN not set')\ndef t(): pass",
        "def f():\n    if not DSN:\n        pytest.skip('HADAVIN_TEST_PG_DSN not set')",
        "x = 1",
    ],
)
def test_the_skip_rule_allows_the_two_guarded_forms(source):
    assert skip_violations(source) == []


@pytest.mark.parametrize("name", P3A2_TEST_FILES)
def test_no_p3a2_test_skips_silently(name):
    assert skip_violations((ROOT / name).read_text(encoding="utf-8")) == []


# --- 2. the pair and the str -------------------------------------------------------------------------------------------

PAIR = ("lex", "statement_text")


def _called_name(call: ast.Call) -> str | None:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def text_form_violations(source: str) -> list[str]:
    """`lex` and `statement_text` return `(text, problem)`: the call must sit on the right of an assignment to TWO
    names, or be indexed with 0 or 1, or be returned by `statement_text` itself. `checked_statement_text` returns a
    `str`: it must not be unpacked, indexed or iterated (that would give characters, or a ValueError)."""
    tree = ast.parse(source)
    parent = _parents(tree)
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name, up = _called_name(node), parent.get(node)
        if name in PAIR:
            pair_target = (
                isinstance(up, ast.Assign)
                and len(up.targets) == 1
                and isinstance(up.targets[0], ast.Tuple)
                and len(up.targets[0].elts) == 2
            )
            indexed = (
                isinstance(up, ast.Subscript)
                and up.value is node
                and isinstance(up.slice, ast.Constant)
                and up.slice.value in (0, 1)
            )
            returned = isinstance(up, ast.Return)
            if not (pair_target or indexed or returned):
                out.append(
                    f"line {node.lineno}: {name}(...) is a pair and is not unpacked into two names"
                )
        elif name == "checked_statement_text":
            wrong = (
                (isinstance(up, ast.Assign) and isinstance(up.targets[0], (ast.Tuple, ast.List)))
                or (isinstance(up, ast.Subscript) and up.value is node)
                or (isinstance(up, (ast.For, ast.comprehension)) and up.iter is node)
                or isinstance(up, ast.Starred)
            )
            if wrong:
                out.append(f"line {node.lineno}: checked_statement_text(...) is a str, not a pair")
    return out


@pytest.mark.parametrize(
    "source",
    [
        "text, problem = checked_statement_text(raw)",
        "text = lex(raw)",
        "text = statement_text(raw)",
        "text = lex(raw)[2]",
        "a, b, c = lex(raw)",
        "first = checked_statement_text(raw)[0]",
        "for ch in checked_statement_text(raw): pass",
        "def f(t):\n    return [x for x in checked_statement_text(t)]",
        "print(mn.lex(raw))",
    ],
)
def test_the_form_rule_flags_each_wrong_use(source):
    assert text_form_violations(source), source


@pytest.mark.parametrize(
    "source",
    [
        "text, problem = lex(raw, keep_quoted=True)",
        "text, problem = mn.statement_text(raw)",
        "text = checked_statement_text(raw)",
        "whole = lex(raw)[0]",
        "def statement_text(t, k=False):\n    return lex(t, k)",
    ],
)
def test_the_form_rule_allows_the_right_uses(source):
    assert text_form_violations(source) == [], source


def test_every_caller_in_the_package_uses_the_right_form():
    """Covers `migrate.py` (its one caller, `_scan`) and `hand_recipe` (`checked_statement_text`), and any caller added
    later anywhere in `src`."""
    bad = {}
    for path in sorted((ROOT / "src" / "hadavin_sdk").rglob("*.py")):
        if found := text_form_violations(path.read_text(encoding="utf-8")):
            bad[str(path.relative_to(ROOT))] = found
    assert not bad, bad


def test_the_scan_calls_the_pair_function_and_hand_recipe_the_raising_one():
    migrate_src = Path(mig.__file__).read_text(encoding="utf-8")
    assert "lex(raw, keep_quoted=True)" in migrate_src
    recipe = next(
        n
        for n in ast.walk(ast.parse(Path(mn.__file__).read_text(encoding="utf-8")))
        if isinstance(n, ast.FunctionDef) and n.name == "hand_recipe"
    )
    called = {_called_name(c) for c in ast.walk(recipe) if isinstance(c, ast.Call)}
    assert "checked_statement_text" in called and not called & set(PAIR)


# --- 3. the docstring --------------------------------------------------------------------------------------------------


def test_the_migrate_docstring_says_where_role_membership_is_changed():
    doc = " ".join((mig.migrate.__doc__ or "").split())
    assert "GRANT r TO s" in doc and "REVOKE r FROM s" in doc
    assert "refused in a `.sql` file" in doc
    assert "migrate()`'s own Python step, with the role as an argument" in doc


# --- 4. tripwire: role membership is refused, whatever else the statement holds ------------------------------------------

REFUSED = "without ON"
GRANT_ROLES = ["r", "r1, r2", '"on"', '"a on b"', 'U&"\\006f\\006e"']
GRANT_OPTIONS = [
    "",
    " WITH ADMIN OPTION",
    " WITH INHERIT TRUE",
    " WITH SET FALSE",
    " WITH ADMIN TRUE, INHERIT FALSE, SET TRUE",
    " GRANTED BY g",
    " WITH ADMIN OPTION GRANTED BY g",
]
REVOKE_HEADS = ["", "ADMIN OPTION FOR ", "INHERIT OPTION FOR ", "SET OPTION FOR "]
REVOKE_TAILS = ["", " GRANTED BY g", " CASCADE", " RESTRICT", " GRANTED BY g CASCADE"]
NOISE = [
    ("", ""),
    ("-- on\n", ""),
    ("/* on */ ", ""),
    ("", " -- on"),
    ("", " /* on */"),
    ("/* on */ ", " -- on\n"),
]
ROLE_FORMS = [
    f"GRANT {role} TO s{option}" for role, option in itertools.product(GRANT_ROLES, GRANT_OPTIONS)
] + [
    f"REVOKE {head}{role} FROM s{tail}"
    for head, role, tail in itertools.product(REVOKE_HEADS, GRANT_ROLES, REVOKE_TAILS)
]
OBJECT_FORMS = [
    "GRANT SELECT ON t TO r",
    "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA s TO r",
    "GRANT USAGE ON SCHEMA s TO r",
    "GRANT SELECT (c) ON t TO r",
    "GRANT EXECUTE ON FUNCTION f() TO r",
    "GRANT SELECT ON t TO r WITH GRANT OPTION",
    "REVOKE ALL ON t FROM PUBLIC",
    "REVOKE GRANT OPTION FOR SELECT ON t FROM r CASCADE",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA s GRANT SELECT ON TABLES TO r",
]


def _kind(sql: str) -> str:
    return type(pglast.parse_sql(sql)[0].stmt).__name__


def _reasons(sql: str) -> list[str]:
    return mn.refused_statements(sql)


def _code_tokens(sql: str) -> list[str]:
    return [t.name for t in parser.scan(sql) if t.name not in ("SQL_COMMENT", "C_COMMENT")]


@pytest.mark.parametrize("before,after", NOISE)
def test_role_membership_is_refused_whatever_the_comments_and_names_hold(before, after):
    """No `GRANT r TO s` / `REVOKE r FROM s` form slips past the refusal: not with `on` in a comment, a quoted name,
    a Unicode-escaped name, nor after a clause, and the server (pglast) agrees each one is a role grant."""
    wrong = []
    for form in ROLE_FORMS:
        sql = before + form + after
        if _kind(sql) != "GrantRoleStmt":
            wrong.append(("not a role grant for the server", sql))
        elif not any(REFUSED in r for r in _reasons(sql)):
            wrong.append(("slipped past the refusal", sql))
    assert not wrong, wrong[:5]


def test_no_role_membership_form_holds_a_standalone_on():
    """The refusal rule is `(grant|revoke)` NOT followed by a standalone `on`. It is right only while the grammar of a
    role grant has no `ON` token. If a later PostgreSQL (a pglast upgrade) adds one, this fails first."""
    with_on = [f for f in ROLE_FORMS if "ON" in _code_tokens(f)]
    assert not with_on, (
        f"a role grant now holds an ON token; fix _ROLE_MEMBERSHIP in migration_numbers: {with_on[:3]}"
    )


@pytest.mark.parametrize("form", OBJECT_FORMS)
def test_privileges_on_objects_are_not_refused_as_role_membership(form):
    assert _kind(form) in ("GrantStmt", "AlterDefaultPrivilegesStmt"), form
    assert "ON" in _code_tokens(form)
    assert not any(REFUSED in r for r in _reasons(form)), _reasons(form)


def test_the_corpus_is_able_to_fail():
    """Control: on the view with the quoted parts KEPT, a role grant with a quoted `on` has a standalone `on` and the
    regex lets it through, so the corpus above does contain a case that a view mistake would turn into a failure."""
    kept, _ = mn.lex('GRANT r TO "on"', keep_quoted=True)
    assert mn._ROLE_MEMBERSHIP.match(kept) is None
    emptied, _ = mn.lex('GRANT r TO "on"')
    assert mn._ROLE_MEMBERSHIP.match(emptied) is not None


# --- 5. the CHANGELOG ---------------------------------------------------------------------------------------------------
# The wording is read case by case (tests/fixtures/runbook.py cuts the runbook into its cases), not as one string; the
# repair steps themselves are RUN in tests/test_migration_postgres.py.

import re

from tests.fixtures import runbook as rb

CHANGELOG = rb.CHANGELOG
FALSE_NAME = (
    "0006" + "_evidence"
)  # the name the older note gave; written in two parts so a search for it finds none


def _evidence_bullet() -> str:
    start = CHANGELOG.index("  - **The evidence migration:")
    return CHANGELOG[start : CHANGELOG.index("\n", start)]


def _words(text: str) -> str:
    return " ".join(text.split())


def test_no_advice_tells_anyone_to_rename_a_row_to_the_false_name():
    """The name may be written (it is the name a person has to recognise); nobody may be told to change TO it."""
    sentences = re.split(r"(?<=[.;:])\s+|\n", CHANGELOG)
    for s in sentences:
        if FALSE_NAME in s:
            assert not re.search(rf"\b(?:to|as|=)\s*['`]?{FALSE_NAME}", s), s
            assert not re.search(rf"version\s*=\s*'{FALSE_NAME}'", s), s
    assert "`0005_evidence.sql`" in CHANGELOG
    assert "version = '<NEW>'" in CHANGELOG  # the runbook step is generic


def test_the_changelog_names_the_false_name_where_a_person_who_followed_the_old_note_looks():
    bullet = _words(_evidence_bullet())
    assert FALSE_NAME in bullet and "back to `0005_evidence`" in bullet and "case (b)" in bullet
    assert "need no repair" not in CHANGELOG  # the old heading contradicted this case
    assert FALSE_NAME in rb.case("b") and "goes back to `0005_evidence`" in _words(rb.case("b"))


def test_the_changelog_keeps_a_repair_path_for_an_early_evidence_table():
    bullet = _words(_evidence_bullet())
    assert "`tool_calls`" in bullet and "no column `error`" in bullet and "case (g)" in bullet
    assert "does not compare table structure" in bullet
    g = _words(rb.case("g"))
    assert "migration role" in g and "owner of the tables" in g  # who may run it
    assert "never the runtime role or the purge role" in g
    assert "only the table `tool_calls` gets one column" in g  # which table changes
    assert "`redaction_maps` and `schema_migrations` are only read" in g
    assert "**Verify:**" in g and "hadavin-sdk migrate" in g  # how to check it
    assert "ADD COLUMN IF NOT EXISTS error" in rb.evidence_block()
    # case (b) for the evidence row carries the same block, case (e) points to it
    assert "block of case (g)" in rb.case("b") and "block of case (g)" in rb.case("e")


def test_a_drop_is_advised_in_one_place_only_and_never_for_the_evidence_tables_of_a_live_database():
    assert "drop `tool_calls`" not in CHANGELOG.lower()
    assert "only in case (e)" in _evidence_bullet()
    assert "dropped as a whole" in rb.case("e") and "scratch database" in rb.case("e")
    for letter in "abcdfg":
        assert "dropped as a whole" not in rb.case(letter), letter


def test_case_c_says_a_released_file_cannot_be_renumbered():
    c = _words(rb.case("c"))
    assert "NOT listed in `src/hadavin_sdk/store/migrations_released.json`" in c
    assert "can never be renumbered" in c
    assert "case (b)" in c  # a database that already applied the renumbered file
    assert (ROOT / "src/hadavin_sdk/store/migrations_released.json").is_file()


def test_case_a_failure_wording_and_the_hand_written_fallback():
    a = _words(rb.case("a"))
    assert "the second run fails, and keeps nothing" in a
    assert (
        "at the ledger row" not in a
    )  # a plain CREATE TABLE fails before the ledger row is reached
    assert "A person must write the steps by hand" in a
    for word in ("backslash", "colon", "RECIPE begins", "unusual schema name"):
        assert word in a, word
    # the message the fallback describes really says it
    big = {Path("0002_b.sql"): "SELECT 1; \\echo x"}
    msg = mn.order_problems({"0003_c"}, list(big), big, "s")[0]
    assert "A person must write the steps by hand" in msg


def test_the_rename_refusal_points_to_the_runbook_case_b(tmp_path):
    for name in ("0001_a.sql", "0002_b.sql"):
        (tmp_path / name).write_text("SELECT 1;", encoding="utf-8")
    msg = mn.gone_message({"0001_a", "0003_b"}, mn.list_migration_files(tmp_path))
    assert "0003_b" in msg
    assert "Migration repair steps, case (b)" in msg
    assert "case (b)" in rb.RUNBOOK and "**(b) " in rb.RUNBOOK


def test_the_migrate_docstring_counts_what_it_reads_back():
    doc = _words(mig.__doc__ or "")
    assert "three session settings" not in doc
    assert "current user and the session user" in doc and "search path" in doc
    assert "three settings that change how SQL text is read" in doc
    assert "cases (a) to (g)" in doc
    assert "nine values" in _words(mig._check_read_back.__doc__ or "")
    assert len(mig._READBACK_VALUES) == 9


def test_the_runbook_carries_the_real_lock_the_command_and_every_case():
    runbook = rb.RUNBOOK
    assert str(mn.MIGRATE_LOCK) in runbook and rb.lock_number() == mn.MIGRATE_LOCK
    assert mn.RECIPE_FIRST_LINE in runbook
    assert mn.RECIPE_COMMAND.rsplit(" ", 2)[0] in runbook  # "psql -X -v ON_ERROR_STOP=1"
    assert (
        rb.PSQL_ARGS == mn.RECIPE_COMMAND.split()[:5]
        or " ".join(rb.PSQL_ARGS) == (mn.RECIPE_COMMAND.rsplit(" ", 2)[0])
    )
    for letter in "abcdefg":
        assert f"**({letter}) " in runbook, letter
    assert "current_user <> '<MIGRATION ROLE>'" in rb.block_with(
        "<MIGRATION ROLE>"
    )  # case (a) assertion (F7)
    assert "://" not in runbook  # no connection string in a hand step
    assert "recipe" in " ".join((mig.__doc__ or "").split()) and "Migration repair steps" in (
        mig.__doc__ or ""
    )


# --- round 2 of PR 73 (order 132): what the CHANGELOG and the docstrings now say ------------------------------------------


def test_the_hand_file_header_in_the_runbook_has_the_timeouts_and_a_quoted_schema():
    """F2, F6. Killed by: mutant R16c (the CHANGELOG rule loses the timeouts), R20 (the unquoted search_path returns)."""
    rule = _words(rb.RUNBOOK[: rb.RUNBOOK.index("- **(a) ")])
    for line in mn.RECIPE_TIMEOUTS:
        assert f"`{line[:-1]}`" in rule or line in rule, line
    assert rb.TIMEOUTS == list(mn.RECIPE_TIMEOUTS)
    assert rule.index("`BEGIN;`") < rule.index("lock_timeout") < rule.index("pg_advisory_xact_lock")
    assert 'SET search_path TO "<the schema migrate uses>";' in rule
    assert "SET search_path TO <" not in rb.RUNBOOK and "SET search_path TO <" not in (
        mig.__doc__ or ""
    )
    assert "lock_timeout" in _words(mig.__doc__ or "")


def test_case_e_puts_the_evidence_block_into_e1_and_e3_always():
    """F3. Killed by: mutant R18 (the sentence goes back to 'if tool_calls.error is missing')."""
    e = _words(rb.case("e"))
    assert "In **E1** and **E3** always put the block of case (g)" in e
    assert "**E2** does not need it" in e
    assert "If `tool_calls.error` is missing (an early version of the migration), put" not in e
    assert "no test in this repository runs case (e)" not in e


def test_case_g_says_what_its_last_check_does_not_look_at():
    """F4. Killed by: mutant R21 (the sentence is removed)."""
    g = _words(rb.case("g"))
    assert "compares columns only" in g and "tool_calls_by_run" in g and "primary keys" in g
    assert "the columns of the evidence tables differ" in rb.evidence_block()


def test_case_b_uses_a_plain_placeholder_and_points_at_the_released_list():
    """F5, F8. Killed by: mutant R22 (the apostrophe placeholder returns)."""
    b = _words(rb.case("b"))
    assert "'<file_stem>'" in b and "that file's name without" in b
    assert "'<that file" not in b
    assert (
        "does not compare the text" in b and "src/hadavin_sdk/store/migrations_released.json" in b
    )


def test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim():
    """M-4 (wired), F1. Killed by: mutants R6 (the call removed; the wiring test) and R23 (the CHANGELOG sentence goes)."""
    first = _words(
        CHANGELOG[CHANGELOG.index("- **Migrations: stricter checks") :].split("\n", 1)[0]
    )
    assert "refuses, before it connects, a released file that was edited or deleted" in first
    assert "the role memberships" in first and "inside a function body" in first
    assert "pg_auth_members" in _words(mig.__doc__ or "") and "pg_auth_members" in _words(
        mig.migrate.__doc__ or ""
    )


def test_migrate_really_calls_the_released_list_check():
    """The CHANGELOG sentence above is only true while this is: migrate() reads the shipped list and calls the check."""
    import inspect

    body = inspect.getsource(mig.migrate)
    assert "released_problems(MIGRATIONS, _released_manifest())" in body
    assert body.index("released_problems") < body.index("connect(")
