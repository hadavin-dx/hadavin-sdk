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

CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
FALSE_NAME = (
    "0006" + "_evidence"
)  # the file never had this name; written in two parts so a grep for it finds none


def test_the_changelog_never_gives_the_false_evidence_name():
    assert FALSE_NAME not in CHANGELOG
    assert "`0005_evidence.sql`" in CHANGELOG


def test_the_changelog_no_longer_advises_dropping_the_evidence_tables():
    """Open point 2: the drop advice is gone from the repair step; a scratch database is the one place (runbook (e))."""
    start = CHANGELOG.index("**Databases built from the merged code need no repair.**")
    step = CHANGELOG[start : CHANGELOG.index("\n", start)]
    assert "drop `tool_calls`" not in step and "redaction_maps" not in step
    assert CHANGELOG.count("is the only place a drop is advised") == 1


def test_the_runbook_carries_the_real_lock_the_command_and_every_case():
    start = CHANGELOG.index("### Migration runbook")
    runbook = CHANGELOG[start:]
    assert str(mn.MIGRATE_LOCK) in runbook
    assert mn.RECIPE_FIRST_LINE in runbook
    assert mn.RECIPE_COMMAND.rsplit(" ", 2)[0] in runbook  # "psql -X -v ON_ERROR_STOP=1"
    for case in ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)"):
        assert f"**{case} " in runbook, case
    assert "SELECT current_user;" in runbook
    assert "://" not in runbook  # no connection string in a hand step
    assert "recipe" in " ".join((mig.__doc__ or "").split()) and "Migration runbook" in (
        mig.__doc__ or ""
    )
