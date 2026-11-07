"""Names that hold `$` or non-ASCII characters (order 112). A name in PostgreSQL may hold `$` (`app$on`, `on$x`), so the regex
word boundary, which breaks at `$`, shows a standalone `on` inside one name and a role grant would pass as a grant on an
object. The refusal reads names the way the lexer does (`migration_numbers._NAME_CHAR`). Needs no database and no CHANGELOG, so the
mutant run of `tests/migration_numbers_mutants.py` can copy this file alone."""

from __future__ import annotations

import ast
import itertools
import re
from pathlib import Path

import pglast
import pytest

from hadavin_sdk.store import migration_numbers as mn

REFUSED = "without ON"


def _kind(sql: str) -> str:
    return type(pglast.parse_sql(sql)[0].stmt).__name__


def _reasons(sql: str) -> list[str]:
    return mn.refused_statements(sql)


# Class: a name in PostgreSQL may hold `$` and non-ASCII characters (`app$on`, `on$x`), so the regex word boundary
# (which breaks at `$`) shows a standalone `on` inside one name. The refusal reads names the way the lexer does.
def _names_over(alphabet, longest):
    for n in range(1, longest + 1):
        for combo in itertools.product(alphabet, repeat=n):
            name = "".join(combo)
            if name[0] in (
                "a",
                "o",
                "\u00e9",
                "_",
            ):  # a name starts with a letter, `_` or a non-ASCII character
                yield name


DOLLAR_NAMES = list(_names_over(["on", "$", "a", "\u00e9"], 4))


def test_the_name_corpus_holds_the_bypass_shapes():
    for shape in ("a$on", "on$a", "a$on$", "\u00e9$on", "on$\u00e9", "on$on"):
        assert shape in DOLLAR_NAMES, shape


@pytest.mark.parametrize(
    "name", ["app$on", "on$x", "a$on$b", "x$on$", "\u00e9on", "on\u00e9", "_on$"]
)
@pytest.mark.parametrize(
    "template",
    [
        "GRANT pg_write_all_data TO {n}",
        "GRANT r TO {n}",
        "GRANT {n} TO s",
        "REVOKE r FROM {n}",
        "REVOKE {n} FROM s",
        "GRANT r\nTO {n}",
        "/* on */ GRANT r TO {n} -- on",
        'GRANT r TO {n}, "on"',
    ],
)
def test_a_name_that_holds_on_and_a_dollar_does_not_hide_a_role_grant(template, name):
    sql = template.format(n=name)
    assert _kind(sql) == "GrantRoleStmt", sql
    assert any(REFUSED in r for r in _reasons(sql)), sql


def test_every_short_name_over_the_dollar_alphabet_is_refused_in_a_role_grant():
    wrong = []
    for name in DOLLAR_NAMES:
        for sql in (f"GRANT r TO {name}", f"REVOKE r FROM {name}"):
            try:
                kind = _kind(sql)
            except pglast.parser.ParseError:
                continue  # not a statement the server reads either
            if kind == "GrantRoleStmt" and not any(REFUSED in r for r in _reasons(sql)):
                wrong.append(sql)
    assert not wrong, wrong[:5]


def test_a_standalone_on_still_lets_a_grant_on_an_object_through_even_to_a_dollar_name():
    for sql in (
        "GRANT SELECT ON t TO app$on",
        "GRANT SELECT ON on$t TO r",
        "GRANT SELECT ON\nt TO app$on",
        "REVOKE ALL ON t$on FROM app$on",
    ):
        assert _kind(sql) == "GrantStmt", sql
        assert not any(REFUSED in r for r in _reasons(sql)), sql


def test_copy_program_is_refused_across_blanks_and_lines():
    assert _reasons("COPY t FROM STDIN") == []
    assert any("PROGRAM" in r for r in _reasons("COPY t FROM PROGRAM 'x'"))
    assert any("PROGRAM" in r for r in _reasons("COPY t\nTO\nPROGRAM 'x'"))


# The only patterns that may keep the word boundary: a match there REFUSES, so an over-match is the safe direction.
BOUNDARY_ALLOWED_IN = {"_TRANSACTION", "_SET", "_BLIND", "_COPY_PROGRAM", "_ROLE_MEMBERSHIP"}


def test_the_word_boundary_is_used_only_where_a_match_refuses():
    """Class check over every regex of `migration_numbers.py`: `\\w`, `\\W`, `\\B` nowhere; `\\b` only in the patterns
    above; `\\b` never next to `on` (the look-ahead of the role rule) and never in a pattern whose match lets a statement
    through (`_SET_ALLOWED`, the name and stem patterns)."""
    tree = ast.parse(Path(mn.__file__).read_text(encoding="utf-8"))
    pattern_functions = {
        "compile",
        "search",
        "match",
        "fullmatch",
        "sub",
        "findall",
        "finditer",
        "split",
    }
    bad = []
    for (
        statement
    ) in tree.body:  # every top-level statement, so a pattern inside a function is read too
        target = ""
        if isinstance(statement, ast.Assign) and isinstance(statement.targets[0], ast.Name):
            target = statement.targets[0].id
        for node in ast.walk(statement):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in pattern_functions
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
            ):
                continue
            for part in ast.walk(node):
                if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
                    continue
                text = part.value
                if re.search(r"\\[wWB]", text) or re.search(r"\\bon|on\\b", text):
                    bad.append((target, text))
                if re.search(r"\\b", text) and target not in BOUNDARY_ALLOWED_IN:
                    bad.append((target, text))
    assert not bad, bad
    assert "lock_timeout" in mn._SET_ALLOWED.pattern and "\\b" not in mn._SET_ALLOWED.pattern


def test_the_name_boundary_agrees_with_the_lexer_character_set():
    for ch in ("a", "Z", "0", "_", "$", "\u00e9", "\u4e2d"):
        assert mn._ident_char(ch) and re.fullmatch(mn._NAME_CHAR, ch), ch
    for ch in (" ", "\n", ";", ",", "(", '"', "'", "-", "/", "."):
        assert not mn._ident_char(ch) and not re.fullmatch(mn._NAME_CHAR, ch), ch
