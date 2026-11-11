"""Rules about the migrate wiring that are not a database test:

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
MIGRATION_TEST_FILES = [
    "tests/test_migration_wiring.py",
    "tests/test_migration_postgres.py",
    "tests/test_migration_rules.py",
    "tests/test_migration_compare.py",
    "tests/test_migration_verify.py",
    "tests/test_migration_verify_pg.py",
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


@pytest.mark.parametrize("name", MIGRATION_TEST_FILES)
def test_no_migration_test_skips_silently(name):
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


ALLOWED_TARGET_FORMS = [
    "GRANT SELECT ON t TO r",
    "GRANT SELECT ON TABLE t TO r",
    "GRANT USAGE ON SEQUENCE q TO r",
    "GRANT SELECT (c) ON t TO r",
    "GRANT EXECUTE ON FUNCTION f() TO r",
    "GRANT EXECUTE ON ROUTINE f() TO r",
    "REVOKE ALL ON t FROM PUBLIC",
    "REVOKE GRANT OPTION FOR SELECT ON t FROM r CASCADE",
    'GRANT SELECT ON TABLE t TO "on schema"',
]
REFUSED_TARGET_FORMS = [
    "GRANT USAGE ON SCHEMA s TO r",
    "GRANT CREATE ON SCHEMA s TO PUBLIC",
    "REVOKE ALL ON SCHEMA s FROM r",
    "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA s TO r",
    "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA s TO r",
    "GRANT CREATE ON DATABASE d TO r",
    "GRANT USAGE ON TYPE ty TO r",
    "GRANT USAGE ON DOMAIN dm TO r",
    "GRANT USAGE ON LANGUAGE plpgsql TO r",
    "GRANT SELECT ON LARGE OBJECT 1 TO r",
    "GRANT USAGE ON FOREIGN SERVER fs TO r",
    "GRANT CREATE ON TABLESPACE ts TO r",
    "GRANT SET ON PARAMETER work_mem TO r",
    "GRANT EXECUTE ON PROCEDURE p() TO r",
    "GRANT SELECT ON t TO r; GRANT USAGE ON SCHEMA s TO r",
    "/* on */ GRANT USAGE -- on\n ON SCHEMA s TO r",
    "GRANT USAGE ON\nSCHEMA s TO r",
    'GRANT USAGE ON SCHEMA "s" TO "on schema"',
]
DEFAULT_FORMS = [
    "ALTER DEFAULT PRIVILEGES IN SCHEMA s GRANT SELECT ON TABLES TO r",
    "ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO PUBLIC",
    "alter   default\tprivileges FOR ROLE m REVOKE ALL ON FUNCTIONS FROM PUBLIC",
    "ALTER PUBLICATION p ADD TABLE audit_entries",
]


OWNER_FORMS = [
    "ALTER TABLE t OWNER TO r",
    "ALTER SEQUENCE s OWNER TO r",
    "ALTER VIEW v OWNER TO r",
    "ALTER MATERIALIZED VIEW v OWNER TO r",
    "ALTER FUNCTION f(int) OWNER TO r",
    "ALTER SCHEMA s OWNER TO r",
    "ALTER TYPE t OWNER TO r",
    "alter   table\tonly t\nowner\n  to  r",
    'ALTER TABLE "t" OWNER TO "r"',
    "ALTER TABLE t OWNER TO CURRENT_USER",
    # the word `rename` as a NAME does not switch the rule off (round 12; these three passed the rule on 8382bdd)
    "ALTER TABLE t ADD COLUMN rename int, OWNER TO r",
    "ALTER TYPE rename OWNER TO r",
    "ALTER TABLE a$rename OWNER TO r",
    "ALTER TABLE t RENAME owner TO boss, OWNER TO r",
    'ALTER TABLE "rename" OWNER TO r',
    "ALTER SEQUENCE rename OWNER TO r",
]
NOT_OWNER_FORMS = [
    "ALTER TABLE t ADD COLUMN owner_id int",
    "ALTER TABLE t ADD COLUMN owner text",
    "ALTER TABLE t RENAME COLUMN owner TO owner_name",
    "ALTER TABLE t RENAME owner TO boss",
    "ALTER TABLE s.t RENAME CONSTRAINT owner TO owner_fk",
    'alter  table if exists only "s"."t" * rename\tcolumn owner\nto x',
    "ALTER TYPE t RENAME ATTRIBUTE owner TO x",
    "ALTER TABLE rename RENAME COLUMN owner TO x",
    "ALTER TABLE a$owner RENAME TO b",
    "ALTER TABLE t ADD COLUMN note text DEFAULT 'owner to nobody'",
    "COMMENT ON TABLE t IS 'owner to be set'",
]


@pytest.mark.parametrize("form", OWNER_FORMS)
def test_handing_an_object_to_another_role_is_refused_by_the_text_rule(form):
    """`ALTER <anything> OWNER TO` is refused where the statement starts (no real migration file uses it; a function body
    that does it is found by the read-back). The only form with the words `owner to` that passes is the rename of a
    column, attribute or constraint CALLED `owner`, read from the start of the statement; a table, type or column that
    is called `rename` does not make an owner change pass. Killed by: mutants OT1 (the rule is off) and OT3 (any
    `rename` before `owner` lets the statement pass, the rule of 8382bdd)."""
    assert any("OWNER TO" in r for r in _reasons(form)), (form, _reasons(form))


@pytest.mark.parametrize("before,after", NOISE)
def test_the_owner_refusal_holds_under_noise(before, after):
    missed = [
        f for f in OWNER_FORMS if not any("OWNER TO" in r for r in _reasons(before + f + after))
    ]
    assert not missed, missed[:5]


@pytest.mark.parametrize("form", NOT_OWNER_FORMS)
def test_a_column_or_a_text_that_says_owner_is_not_taken_for_an_owner_change(form):
    """Killed by: mutants OT2 (any statement that holds the word `owner` is refused) and OT4 (the rename of a column
    called `owner` is not let through).
    Pin: the cases that 8382bdd already had also pass on the source before round 11 (they hold the exemption in place); mutant OT4 shows the test can fail."""
    assert not any("OWNER TO" in r for r in _reasons(form)), (form, _reasons(form))


@pytest.mark.parametrize("form", ALLOWED_TARGET_FORMS)
def test_a_right_on_a_table_column_sequence_or_function_is_not_refused(form):
    assert _reasons(form) == [], _reasons(form)


@pytest.mark.parametrize("form", REFUSED_TARGET_FORMS + DEFAULT_FORMS)
def test_a_right_anywhere_but_on_a_table_view_sequence_column_or_function_is_refused(form):
    """The read-back after a file looks at tables, views, sequences, columns and functions (and the schema of the run
    and the default rights of the migration role). A file that changes a right anywhere else (the schema, a database, a
    type, `ALL ... IN SCHEMA`, a default right, a publication) is refused by the text rule first, whatever the
    comments, line breaks, case or quotes around it."""
    assert _reasons(form), form


@pytest.mark.parametrize("before,after", NOISE)
def test_the_refusal_of_a_right_elsewhere_holds_under_noise(before, after):
    missed = [f for f in REFUSED_TARGET_FORMS + DEFAULT_FORMS if not _reasons(before + f + after)]
    assert not missed, missed[:5]


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
FALSE_PHRASE = "numbered 0006 with the name `evidence`"  # how the CHANGELOG says it, so that no search finds the literal


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
    assert (
        FALSE_NAME not in CHANGELOG
    )  # the literal is not written at all: a search for it must find nothing
    assert "`0005_evidence.sql`" in CHANGELOG
    assert "version = '<NEW>'" in CHANGELOG  # the runbook step is generic


def test_the_changelog_names_the_false_name_where_a_person_who_followed_the_old_note_looks():
    bullet = _words(_evidence_bullet())
    assert FALSE_PHRASE in bullet and "back to `0005_evidence`" in bullet and "case (b)" in bullet
    assert "need no repair" not in CHANGELOG  # the old heading contradicted this case
    assert FALSE_PHRASE in _words(rb.case("b")) and "goes back to `0005_evidence`" in _words(
        rb.case("b")
    )


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
    assert "cases (a) to (h)" in doc
    assert "eleven values" in _words(mig._check_read_back.__doc__ or "")
    assert len(mig._READBACK_VALUES) == 11


def test_the_runbook_carries_the_real_lock_the_command_and_every_case():
    runbook = rb.RUNBOOK
    assert str(mn.MIGRATE_LOCK) in runbook and rb.lock_number() == mn.MIGRATE_LOCK
    assert mn.RECIPE_FIRST_LINE in runbook
    assert mn.RECIPE_COMMAND.rsplit(" ", 2)[0] in runbook  # "psql -X -v ON_ERROR_STOP=1"
    assert (
        rb.PSQL_ARGS == mn.RECIPE_COMMAND.split()[:5]
        or " ".join(rb.PSQL_ARGS) == (mn.RECIPE_COMMAND.rsplit(" ", 2)[0])
    )
    for letter in "abcdefgh":
        assert f"**({letter}) " in runbook, letter
    assert "current_user <> '<MIGRATION ROLE>'" in rb.block_with(
        "<MIGRATION ROLE>"
    )  # the assertion of case (a)
    assert "://" not in runbook  # no connection string in a hand step
    assert "recipe" in " ".join((mig.__doc__ or "").split()) and "Migration repair steps" in (
        mig.__doc__ or ""
    )


# --- what the CHANGELOG and the docstrings now say ------------------------------------------


def test_the_hand_file_header_in_the_runbook_has_the_timeouts_and_a_quoted_schema():
    """The hand-file header in the runbook holds the two time limits (read from the constant) and a quoted schema."""
    rule = _words(rb.RUNBOOK[: rb.RUNBOOK.index("- **(a) ")])
    for line in mn.RECIPE_TIMEOUTS:
        assert f"`{line}`" in rule, line
    assert rb.TIMEOUTS == list(mn.RECIPE_TIMEOUTS)
    prose = re.sub(r"`[^`]*`", "", rule)  # the code spans are checked against the constant above
    assert not re.search(r"\b\d+ ?(seconds?|s)\b", prose), "no second copy of the numbers in prose"
    assert rule.index("`BEGIN;`") < rule.index("lock_timeout") < rule.index("pg_advisory_xact_lock")
    assert 'SET search_path TO "<the schema migrate uses>";' in rule
    assert "SET search_path TO <" not in rb.RUNBOOK and "SET search_path TO <" not in (
        mig.__doc__ or ""
    )
    assert "RECIPE_TIMEOUTS" in _words(mig.__doc__ or "")


def test_case_e_puts_the_evidence_block_into_e1_and_e3_always():
    """Case (e) puts the evidence block into steps E1 and E3 and not into E2."""
    e = _words(rb.case("e"))
    assert "In **E1** and **E3** always put the block of case (g)" in e
    assert "**E2** does not need it" in e
    assert "If `tool_calls.error` is missing (an early version of the migration), put" not in e
    assert "no test in this repository runs case (e)" not in e


def test_case_g_says_what_its_last_check_does_not_look_at():
    """Case (g) says what its last check does not look at."""
    g = _words(rb.case("g"))
    assert "compares columns only" in g and "tool_calls_by_run" in g and "primary keys" in g
    assert "the columns of the evidence tables differ" in rb.evidence_block()


def test_case_b_uses_a_plain_placeholder_and_points_at_the_released_list():
    """Case (b) uses a plain placeholder and points at the released list."""
    b = _words(rb.case("b"))
    assert "'<file_stem>'" in b and "that file's name without" in b
    assert "'<that file" not in b
    assert (
        "does not compare the text" in b and "src/hadavin_sdk/store/migrations_released.json" in b
    )


def _upgrade_bullet() -> str:
    """The whole first CHANGELOG bullet (its numbered sub-steps included), up to the next top-level bullet."""
    start = CHANGELOG.index("- **Migrations: stricter checks")
    return CHANGELOG[start : CHANGELOG.index("\n- **", start)]


def test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim():
    """migrate() calls the released-file check. Killed by: mutants R6 (the call removed; the wiring test) and R23 (the CHANGELOG sentence goes)."""
    first = _words(_upgrade_bullet())
    assert "refuses, before it connects, a released file that was edited or deleted" in first
    assert (
        "Not yet run on PostgreSQL 17.10, the CI version, so the `MAINTAIN` check is covered only by tests that fake the server version, until that run exists."
        in first
    )
    assert "asks for `MAINTAIN` only from 17, because 16 rejects that name" in first
    assert (
        "A role that holds `REPLICATION`, or is a member of a role that holds it, is refused"
        in first
    )
    assert "CREATE has no grant option" in first
    assert "an existing trigger left disabled" in first
    assert "that this package manages in the migration schema" in first
    assert "every role the two users or those named roles are a member of" in first
    assert "do not hand it over: point `migrate` at another schema" in first
    tests_part = _words(CHANGELOG[CHANGELOG.index("### Tests") :].split("\n### ", 1)[0])
    assert "On a normal exit it drops what the role owns in every database it used" in tests_part
    assert "named after the role (`application_name`" in tests_part
    assert (
        "a guard test fails when a test calls `make_conninfo` or `connect` with `user=` and no password"
        in tests_part
    )
    assert "Why a test run keeps a connection open.** So that another test run" in tests_part
    assert "a *test schema* is a schema whose name starts with `hadavin_test_`" in tests_part
    assert (
        "Refused: rights for any other role, owners a file handed over, rights on the schema, default rights, and SECURITY DEFINER."
        in first
    )
    assert (
        "`REVIEWED_DEFINER_FUNCTIONS`" in first
        and "waits for the lock at most `lock_wait_seconds`" in first
    )
    assert "Tested on:** PostgreSQL 16.15, on the build machine" in first
    assert "session_user" in first and "WITH GRANT OPTION" in first and "pg_parameter_acl" in first
    assert "PostgreSQL 16 is the lowest version" in first
    assert "TO FILL IN" not in first, "no placeholder is left in the changelog"
    assert "the tests read the same file" in first
    assert "the role memberships" in first and "inside a function body" in first
    assert "pg_auth_members" in _words(mig.__doc__ or "") and "pg_auth_members" in _words(
        mig.migrate.__doc__ or ""
    )


_TIMEOUT = re.compile(r"\w+_timeout = '[^']*'")


def test_every_timeout_value_written_in_the_docs_is_the_constants():
    """the CHANGELOG and both docstrings may write a timeout setting, but only the constant's own."""
    allowed = {m for line in mn.RECIPE_TIMEOUTS for m in _TIMEOUT.findall(line)}
    assert len(allowed) == 2
    for name, text in (
        ("CHANGELOG", CHANGELOG),
        ("migrate module doc", mig.__doc__ or ""),
        ("migrate doc", mig.migrate.__doc__ or ""),
        ("migration_numbers doc", mn.__doc__ or ""),
    ):
        assert set(_TIMEOUT.findall(text)) <= allowed, name
    assert "RECIPE_TIMEOUTS" in _words(mig.__doc__ or "")
    assert "RECIPE_TIMEOUTS" in _words(mig.migrate.__doc__ or "")
    assert "RECIPE_TIMEOUTS" in _words(rb.RUNBOOK)


def test_no_source_or_test_file_writes_the_timeout_values_a_second_time():
    """the values of the constant (read from it) appear as a quoted literal nowhere else in the
    store code or the migration tests."""
    values = [v for line in mn.RECIPE_TIMEOUTS for v in re.findall(r"= '([^']*)'", line)]
    assert values and all(values)
    root = Path(__file__).resolve().parent
    files = [
        *sorted((root.parent / "src" / "hadavin_sdk" / "store").glob("*.py")),
        *sorted(root.glob("test_migration*.py")),
        *sorted((root / "fixtures").glob("*.py")),
    ]
    assert Path(mn.__file__) in files
    for path in files:
        text = path.read_text(encoding="utf-8")
        for v in values:
            expected = 1 if path == Path(mn.__file__) else 0
            assert text.count(f"'{v}'") == expected, f"{path.name}: '{v}'"


def test_case_f_says_migrate_has_the_same_limits_as_the_hand_file():
    """CHANGELOG case (f) must not say `migrate` has no timeout while it sets them."""
    f = _words(rb.case("f"))
    assert "`migrate` sets the same lock and statement limits as the hand file" in f
    assert "has no timeout in `migrate`" not in f
    first = _words(_upgrade_bullet())
    assert (
        "`migrate` also sets, for its transaction, the same lock-wait and statement time limits"
        in first
    )


def test_the_scope_the_order_and_the_file_own_limits_are_written_down():
    """The upgrade bullet says what migrate checks, in what order, and which limits each file has."""
    first = _words(_upgrade_bullet())
    assert (
        "also the role checks and grants, so a normal run with no new file is covered too" in first
    )
    assert 'in the paragraph "Rule for every hand step"' in first
    assert (
        "The statement limit is for each statement" in first and "seen on PostgreSQL 16.15" in first
    )
    f = _words(rb.case("f"))
    assert (
        "The order differs on purpose: the hand file sets the limits before the advisory lock" in f
    )
    assert "A migration file may not change either limit" in f
    doc = _words(mig.migrate.__doc__ or "")
    assert "so a run with no pending file is covered too" in doc
    assert "sets the limits BEFORE the advisory lock" in doc and "AFTER it, on purpose" in doc
    assert "A migration file may not change either limit" in doc


# --- 6. both JSON lists are inside the built package -------------------------------------------------

PACKAGED_JSON = ("migrations_released.json", "migrations_trigger_changes.json")


def test_the_built_wheel_holds_both_migration_lists(tmp_path):
    """`migrate()` reads both lists at run time from the folder of the package, so an installed copy must have them.
    The wheel is built into a temporary folder (`uv build`) and its file list is read; each file in it must equal the
    file in the source tree. `uv build` fetches the build backend on a first run (then it is cached), so with an empty
    cache and no network this test fails with uv's own message; it is not skipped."""
    import asyncio
    import shutil
    import zipfile

    uv = shutil.which("uv")
    assert uv is not None, "uv is needed to build the wheel (it runs the whole test suite)"
    out = tmp_path / "wheel"

    async def build() -> tuple[int | None, bytes]:
        proc = await asyncio.create_subprocess_exec(
            uv,
            "build",
            "--wheel",
            "--out-dir",
            str(out),
            str(ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        text, _ = await asyncio.wait_for(proc.communicate(), 300)
        return proc.returncode, text

    code, text = asyncio.run(build())
    assert code == 0, text.decode("utf-8", "replace")[-2000:]
    (wheel,) = out.glob("*.whl")
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
        for name in PACKAGED_JSON:
            member = f"hadavin_sdk/store/{name}"
            assert member in names, f"{member} is not in the wheel"
            source = (ROOT / "src" / "hadavin_sdk" / "store" / name).read_bytes()
            assert z.read(member) == source
        assert any(n.startswith("hadavin_sdk/store/migrations/0001_") for n in names)


def test_every_migrate_mutant_still_applies_to_the_source():
    """The list of mutants in `tests/migrate_mutants.py` cannot rot: each `old` text is in its file exactly once and each
    killer test exists (the run itself needs a database and is documented at the top of that file)."""
    from tests import migrate_mutants

    assert migrate_mutants.problems_with_the_list() == []
    assert len(migrate_mutants.M) >= 80


def test_the_mutant_runner_refuses_an_unknown_id():
    """`M88,TYPO` used to run one mutant and exit 0. Killed by: mutant RN1."""
    from tests import migrate_mutants as mm

    assert mm.unknown_ids("M88,TYPO") == ["TYPO"]
    assert mm.unknown_ids("M88,R4") == [] and mm.unknown_ids("") == []
    assert mm.main(["M88,TYPO"]) == 2


def _failure(test: str, head: str, name: str = "tests/test_x.py") -> str:
    """The part of a `pytest --tb=short -rf` output that belongs to one failed test whose exception reads `head`."""
    return (
        f"=== FAILURES ===\n_______ {test} _______\n{name}:12: in {test}\n    code()\nE   {head}\n"
        f"=== short test summary info ===\nFAILED {name}::{test} - {head}\n"
    )


def test_the_mutant_runner_does_not_count_a_broken_line_as_a_kill():
    """A planted line that only breaks the code (a NameError, a syntax error, a server error, an error nobody has named
    yet) makes a test fail but proves nothing about the named killer: only the exceptions a test raises on purpose count.
    Killed by: mutants RN2 (status_of does not look), RN3 (the allow list takes everything), RN4 (any dotted name is
    allowed) and RN5 (a test that could not start counts as a kill)."""
    from tests import migrate_mutants as mm

    m = next(x for x in mm.M if x.name == "R4")
    names = mm.killers_of(m)
    path, _, test = names[0].partition("::")

    def runs(out):
        return [(1, out)] + [(0, "")] * (len(names) - 1)

    def one(head):
        return mm.status_of(m, runs(_failure(test, head, path)))

    for head in (
        "AssertionError: assert 1 == 2",
        "assert ['a'] == ['b']",
        "Failed: DID NOT RAISE <class 'hadavin_sdk.errors.ConfigError'>",
        "AssertionError: Regex pattern did not match.",
        "hadavin_sdk.errors.ConfigError: the roles changed",
    ):
        assert one(head) == "KILLED", head
    for head in (
        "NameError: name 'x' is not defined",
        "AttributeError: module has no attribute 'x'",
        "TypeError: 'NoneType' object is not subscriptable",
        "KeyError: 'x'",
        "UnboundLocalError: cannot access local variable 'x'",
        "ValueError: not enough values to unpack",
        "IndexError: list index out of range",
        "ZeroDivisionError: division by zero",
        "RuntimeError: the loop is not running",
        'psycopg.errors.UndefinedTable: relation "x" does not exist',
        "errors.InsufficientPrivilege: permission denied",
        "DeadlockDetected: deadlock detected",
        "SomeErrorNobodyHasNamedYet: x",
        "Failed: TEST SETUP PROBLEM: this test needs CREATEDB on the HADAVIN_TEST_PG_DSN login",
        "AssertionError: TEST SETUP PROBLEM, a timing flake and not a defect: the file started waiting",
        "assert 1 == 2, TEST SETUP PROBLEM",
    ):
        # the message holds only the first word: a failure line that quoted the text "TEST SETUP PROBLEM" would be
        # read by the mutant runner as a test that could not start
        assert one(head) == "BROKEN", head.split()[0]
    postgres_tests = (Path(__file__).resolve().parent / "test_migration_postgres.py").read_text(
        encoding="utf-8"
    )
    assert postgres_tests.count(mm.SETUP_PROBLEM) == 8, (
        "the eight places where a test can fail for want of a setup, or by a timing flake, say so"
    )
    two = _failure(test, "AssertionError: x", path) + _failure("test_other", "KeyError: 'x'", path)
    assert mm.status_of(m, runs(two)) == "BROKEN", "one broken failure among the failures"
    other = _failure("test_other", "AssertionError: x", "tests/test_other.py")
    assert mm.status_of(m, runs(other)) == "BROKEN", "another test failed, not the named killer"
    assert mm.failure_heads(_failure(test, "KeyError: 'x'")) == ["KeyError: 'x'"]
    long = "test_" + "a_very_long_name_" * 5
    assert mm.failure_heads(f"=== FAILURES ===\n_ {long} _\nt.py:1: in f\nE   KeyError: 'x'\n") == [
        "KeyError: 'x'"
    ], "pytest pads a long title with a single underscore on each side"
    assert not mm.only_test_failures("no failures here")
    assert mm.status_of(m, [(0, "")] * len(names)) == "SURVIVED"
    assert mm.status_of(m, [(2, "")] + [(0, "")] * (len(names) - 1)).startswith("ERROR")


def _password_keys_in(node: ast.AST) -> list[ast.AST | None]:
    """The values given for a `password` key by an expression that can be a dict literal, a `dict(password=...)` call,
    or either branch of `a if c else b`; an empty list when it is none of those or has no `password` key."""
    if isinstance(node, ast.Dict):
        return [
            v
            for key, v in zip(node.keys, node.values, strict=True)
            if isinstance(key, ast.Constant) and key.value == "password"
        ]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        return [k.value for k in node.keywords if k.arg == "password"]
    if isinstance(node, ast.IfExp):
        return _password_keys_in(node.body) + _password_keys_in(node.orelse)
    return []


def _is_none(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _passes_a_password(call: ast.Call) -> bool:
    """A `password=` argument, or a `**` expansion of a dict literal (or of `{"password": p} if p else {}`) that has a
    `password` key in at least one branch: the password is given when there is one."""
    for k in call.keywords:
        if k.arg == "password":
            return True
        # `**{"password": None}` passes no password
        if k.arg is None and any(not _is_none(v) for v in _password_keys_in(k.value)):
            return True
    return False


@pytest.mark.parametrize(
    ("call", "has_password"),
    [
        ("make_conninfo(d, user=u, password=p)", True),
        ('make_conninfo(d, user=u, **{"password": p})', True),
        ('make_conninfo(d, user=u, **({"password": p} if p else {}))', True),
        ("make_conninfo(d, user=u, **dict(password=p))", True),
        ("make_conninfo(d, user=u, **dict(sslmode=m))", False),
        ('make_conninfo(d, user=u, **{"password": None})', False),
        ("make_conninfo(d, user=u, **extra)", False),
        ("make_conninfo(d, user=u, **options())", False),
        ('make_conninfo(d, user=u, **{"sslmode": "x"})', False),
        ("make_conninfo(d, user=u)", False),
    ],
)
def test_the_password_scan_reads_the_star_star_forms(call, has_password):
    """Killed by: mutant GD2 (any `**` expansion counts as a password)."""
    assert _passes_a_password(ast.parse(call).body[0].value) is has_password


def test_no_test_logs_in_as_a_role_without_passing_its_password():
    """A test that makes a login role and connects as it must pass the password (`login_dsn`, or `password=` in
    `make_conninfo`), or the test fails with a connection error on a server that asks for a password instead of
    testing what it is about. The scan reads every test file: a call of `make_conninfo` or `connect` with a `user=`
    argument and no password is a failure. A `**` expansion counts only when it is a dict literal, a `dict(password=...)` call, or the two-branch
    form `{"password": p} if p else {}`, with a `password` key whose value is not the constant `None`; a `**` of a
    name or of any other call is a failure (the scan cannot tell what the name holds, so the line says `# pw-env`
    or passes the password as `password=`). A line of the
    call that says `# pw-env` (the password travels in the environment) is skipped.

    What this scan does NOT see, on purpose: a connection string written as text (`f"... user={role} ..."`), a
    `conninfo_to_dict` result changed by hand, `user` given as a positional or in a `**` dict, a function that is called
    `connect` but is not psycopg's, and whether the text after `# pw-env` is true (only that the marker is there).
    Killed by: mutant GD1 (one login loses its password)."""
    root = Path(__file__).resolve().parent
    bad = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in ("make_conninfo", "connect"):
                continue
            if "user" not in {k.arg for k in node.keywords} or _passes_a_password(node):
                continue
            span = lines[node.lineno - 1 : (node.end_lineno or node.lineno)]
            if not any("# pw-env" in line for line in span):
                bad.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not bad, "a login without its password: " + ", ".join(bad)
