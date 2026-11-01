"""Validator v0 (control C1): model-style SQL in, one canonical hashed SELECT out, or a rejection with a rule id.

This is the only module that imports `sqlglot` (a demo-local test enforces it). Order of work:

1. `prefilter` runs on the RAW text before any parser sees it (A-10): control characters, NUL, bidi, backslash,
   dollar signs, escape-string prefixes, non-ASCII code, stacked statements, unterminated quotes or comments.
2. sqlglot parses exactly one statement; the root must be a SELECT (or a set operation over SELECTs).
3. The tree is walked with positive lists only (relations, columns, functions, cast targets, node classes).
4. The canonical SQL is regenerated with `comments=False`, re-filtered, re-parsed and required to be the same
   tree (V11). Only the canonical text is ever hashed, shown or sent to the database.

C1 narrows what can be asked and makes the shown SQL the executed SQL. It is not the write control: that is the
read-only login (C2) and the read-only transaction on the extended protocol (C3).
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from askdata.allowed import CAST_TARGETS, FUNCTIONS, INTERVAL_UNITS, SCHEMA, SYNTAX_FUNCTIONS, VIEWS
from askdata.safe_text import is_forbidden

# sqlglot logs a warning when it falls back to a generic Command; the rejection below is the signal we use.
logging.getLogger("sqlglot").setLevel(logging.ERROR)

MAX_CHARS = 4000
MAX_LITERAL = 200
MAX_JOINS = 8
MAX_CTES = 4
MAX_DEPTH = 6

RULES = {
    "V01": "parse error, empty, unterminated quote or comment, or more than one statement",
    "V02": "the root is not a SELECT",
    "V03": "a write, DDL, utility, locking or SELECT INTO statement or clause",
    "V04": "a relation that is not an exposed view (or a table function, LATERAL, TABLESAMPLE)",
    "V05": "a column that is not in the referenced views",
    "V06": "a function that is not in the allowlist",
    "V07": "a cast to a type outside the allowed list",
    "V08": "WITH RECURSIVE, CROSS JOIN, comma join or a join without a condition",
    "V09": "forbidden character or token in the raw text (control, backslash, dollar, prefix, parameter)",
    "V10": "a construct or operator that is not allowed, or a size limit",
    "V11": "the regenerated SQL does not parse to the same tree",
    "V12": "a quoted identifier that is not a plain lower-case name",
}


class Rejected(Exception):  # a rejection is a verdict, named for the domain, not an error class
    """The statement is refused. `rule` is the registry id; `detail` is a short fixed-style sentence."""

    def __init__(self, rule: str, detail: str) -> None:
        super().__init__(f"{rule}: {detail}")
        self.rule = rule
        self.detail = detail


@dataclass(frozen=True)
class Validated:
    canonical_sql: str
    sha256: str


# ------------------------------------------------------------------------------------------------ pre-filter

_PREFIX_CHARS = frozenset("eEbBxXnN")
_IDENT_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")


def prefilter(text: str) -> tuple[str, bool]:
    """Reject hazards in the raw text; return (text without one trailing semicolon, saw_comment).

    One left-to-right pass with the states CODE, STRING, QIDENT, LINE_COMMENT and BLOCK_COMMENT (nested)."""
    if len(text) > MAX_CHARS:
        raise Rejected("V09", f"text is over {MAX_CHARS} characters")
    for ch in text:
        if is_forbidden(ch):
            raise Rejected("V09", f"forbidden character U+{ord(ch):04X}")
    if chr(92) in text:
        raise Rejected(
            "V09", "backslash is not allowed"
        )  # two parsers can disagree about where a literal ends
    state, depth, semi, saw_comment = "CODE", 0, -1, False
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        ch, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if state == "CODE":
            if semi >= 0 and not ch.isspace() and not text.startswith(("--", "/*"), i):
                raise Rejected(
                    "V01", "more than one statement"
                )  # anything after the first ; but a comment
            if ch == "'":
                state = "STRING"
            elif ch == '"':
                state = "QIDENT"
            elif ch == "-" and nxt == "-":
                state, saw_comment, i = "LINE", True, i + 1
            elif ch == "/" and nxt == "*":
                state, depth, saw_comment, i = "BLOCK", 1, True, i + 1
            elif ch == "$":
                raise Rejected("V09", "dollar quoting and parameters are not allowed")
            elif ord(ch) > 127:
                raise Rejected("V09", "non-ASCII character outside a string literal")
            elif ch == ";":
                if semi >= 0:
                    raise Rejected("V01", "more than one statement")
                semi = i
                out[i] = " "
            elif ch in _PREFIX_CHARS and nxt == "'" and (i == 0 or text[i - 1] not in _IDENT_CHARS):
                raise Rejected("V09", "string prefix (E, B, X, N) is not allowed")
            elif ch in "uU" and nxt == "&" and (i == 0 or text[i - 1] not in _IDENT_CHARS):
                raise Rejected("V09", "U& escape strings and identifiers are not allowed")
        elif state == "STRING":
            if ch == "'":
                if nxt == "'":
                    i += 1
                else:
                    state = "CODE"
        elif state == "QIDENT":
            if ord(ch) > 127:
                raise Rejected("V09", "non-ASCII character in a quoted identifier")
            if ch == '"':
                if nxt == '"':
                    i += 1
                else:
                    state = "CODE"
        elif state == "LINE":
            if ch == "\n":
                state = "CODE"
        elif ch == "/" and nxt == "*":  # BLOCK
            depth, i = depth + 1, i + 1
        elif ch == "*" and nxt == "/":
            depth, i = depth - 1, i + 1
            if depth == 0:
                state = "CODE"
        i += 1
    if state in ("STRING", "QIDENT", "BLOCK"):
        raise Rejected("V01", "unterminated quote or comment")
    return "".join(out), saw_comment


# ------------------------------------------------------------------------------------------------ tree rules

# Node classes that may appear (default deny). Function nodes are NOT listed: they are judged by name.
_ALLOWED_NODES: tuple[type[exp.Expression], ...] = (
    exp.Select, exp.From, exp.Where, exp.Group, exp.Having, exp.Order, exp.Ordered, exp.Limit, exp.Offset,
    exp.Distinct, exp.Join, exp.Table, exp.TableAlias, exp.Alias, exp.Column, exp.Identifier, exp.Star,
    exp.Literal, exp.Boolean, exp.Null, exp.Paren, exp.DataType, exp.DataTypeParam, exp.In, exp.Between,
    exp.Is, exp.Not, exp.And, exp.Or, exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.Add, exp.Sub,
    exp.Mul, exp.Div, exp.Mod, exp.Neg, exp.DPipe, exp.Like, exp.ILike, exp.NullSafeEQ, exp.NullSafeNEQ,
    exp.With, exp.CTE, exp.Window, exp.Filter, exp.WithinGroup, exp.Union, exp.Intersect, exp.Except,
    exp.Subquery, exp.Interval, exp.Var, exp.AtTimeZone,
)  # fmt: skip

_WRITE_ROOTS = (
    exp.DML,
    exp.DDL,
    exp.Command,
    exp.Copy,
    exp.Set,
    exp.TruncateTable,
    exp.Drop,
    exp.Alter,
)
_ZONE = re.compile(r"[A-Za-z0-9_/+-]{1,40}")
_FUNC_NAME = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\(")
_PLAIN_IDENT = re.compile(r"[a-z_][a-z0-9_]*")
_SCHEMA_DICT = {SCHEMA: {v: dict.fromkeys(cols, "TEXT") for v, cols in VIEWS.items()}}


def _gen(node: exp.Expression) -> str:
    return node.sql(dialect="postgres", comments=False)


def _check_root(tree: exp.Expression) -> None:
    if isinstance(tree, exp.Select | exp.SetOperation):
        return
    if isinstance(tree, _WRITE_ROOTS):
        raise Rejected("V03", f"{type(tree).__name__} statements are not allowed")
    raise Rejected("V02", f"root is {type(tree).__name__}, not a SELECT")


def _check_function(node: exp.Func) -> None:
    if isinstance(node, exp.Anonymous):
        raise Rejected("V06", f"function {node.name.lower()} is not allowed")
    if type(node).__name__ in SYNTAX_FUNCTIONS:
        return
    match = _FUNC_NAME.match(_gen(node))
    name = match.group(1).lower() if match else _gen(node).lower()
    if name not in FUNCTIONS:
        raise Rejected("V06", f"function {name} is not allowed")


def _check_cast(node: exp.Cast) -> None:
    target = node.args.get("to")
    # type() is exp.DataType on purpose: ObjectIdentifier (regclass) is a subclass and must not pass.
    if type(target) is not exp.DataType or getattr(target.this, "name", "") not in CAST_TARGETS:
        raise Rejected("V07", "cast target is not in the allowed list")


def _check_table(node: exp.Table, cte_names: set[str]) -> None:
    ident = node.this
    if not isinstance(ident, exp.Identifier):
        raise Rejected("V04", "table functions are not allowed in FROM")
    if node.args.get("catalog") is not None:
        raise Rejected("V04", "three-part relation names are not allowed")
    db = node.args.get("db")
    if db is None:
        if ident.name.lower() not in cte_names:
            raise Rejected("V04", f"relation {ident.name.lower()} is not an exposed view")
    elif db.name.lower() != SCHEMA or ident.name.lower() not in VIEWS:
        raise Rejected(
            "V04", f"relation {db.name.lower()}.{ident.name.lower()} is not an exposed view"
        )


def _check_node(node: exp.Expression, cte_names: set[str]) -> None:
    """Specific rules first (so the rule id names the real problem), then default deny."""
    if isinstance(
        node, exp.Insert | exp.Update | exp.Delete | exp.Merge | exp.Into | exp.Lock | exp.Command
    ):
        raise Rejected("V03", f"{type(node).__name__} is not allowed")
    if isinstance(node, exp.Select) and (node.args.get("into") or node.args.get("locks")):
        raise Rejected("V03", "SELECT INTO and locking clauses are not allowed")
    if isinstance(node, exp.With) and node.args.get("recursive"):
        raise Rejected("V08", "WITH RECURSIVE is not allowed")
    if isinstance(node, exp.Join) and (
        node.args.get("kind") == "CROSS"
        or node.args.get("method")
        or not (node.args.get("on") is not None or node.args.get("using"))
    ):
        raise Rejected("V08", "every join needs ON or USING (no CROSS, NATURAL or comma join)")
    if isinstance(node, exp.Lateral | exp.TableSample | exp.Unnest | exp.Values):
        raise Rejected("V04", f"{type(node).__name__} is not allowed")
    if isinstance(node, exp.Parameter | exp.Placeholder):
        raise Rejected("V09", "parameters and placeholders are not allowed")
    if isinstance(node, exp.Table):
        _check_table(node, cte_names)
    elif isinstance(node, exp.Cast):
        _check_cast(node)
    if isinstance(node, _ALLOWED_NODES):
        pass  # operators such as AND are also Func subclasses in sqlglot: the class list wins
    elif isinstance(node, exp.Binary | exp.Unary):
        raise Rejected(
            "V10", f"operator {type(node).__name__} is not allowed"
        )  # operators that are also Func
    elif isinstance(node, exp.Func):
        _check_function(node)
    else:
        raise Rejected("V10", f"{type(node).__name__} is not allowed")
    _check_detail(node)


def _check_detail(node: exp.Expression) -> None:
    if (
        isinstance(node, exp.Identifier)
        and node.args.get("quoted")
        and not _PLAIN_IDENT.fullmatch(node.name)
    ):
        raise Rejected("V12", "quoted identifiers must be plain lower-case names")
    if isinstance(node, exp.Column) and (node.args.get("db") or node.args.get("catalog")):
        raise Rejected("V05", "columns are referenced by view alias and name only")
    if isinstance(node, exp.Literal) and node.is_string and len(node.this) > MAX_LITERAL:
        raise Rejected("V10", f"string literal over {MAX_LITERAL} characters")
    if isinstance(node, exp.Window) and node.args.get("spec") is not None:
        raise Rejected("V10", "window frames are not allowed")
    if isinstance(node, exp.WithinGroup) and not isinstance(node.this, exp.PercentileCont):
        raise Rejected("V10", "WITHIN GROUP is allowed only after percentile_cont")
    if isinstance(node, exp.Filter) and not isinstance(node.this, exp.AggFunc):
        raise Rejected("V10", "FILTER is allowed only on aggregates")
    if isinstance(node, exp.AtTimeZone):
        zone = node.args.get("zone")
        if not (isinstance(zone, exp.Literal) and zone.is_string and _ZONE.fullmatch(zone.this)):
            raise Rejected("V10", "AT TIME ZONE needs a plain string literal zone")
    if isinstance(node, exp.Interval):
        value, unit = node.this, node.args.get("unit")
        if not (
            isinstance(value, exp.Literal)
            and re.fullmatch(r"\d{1,4}", value.this)
            and isinstance(unit, exp.Var)
            and unit.name.lower() in INTERVAL_UNITS
        ):
            raise Rejected("V10", "INTERVAL needs a number and a unit: day, week, month or year")


def _check_whole_row(tree: exp.Expression, cte_names: set[str]) -> None:
    """A bare relation alias used as a value (`SELECT o FROM orders_v o`) is a whole-row reference in Postgres."""
    relations = {t.alias_or_name.lower() for t in tree.find_all(exp.Table)} | cte_names
    known = {c for cols in VIEWS.values() for c in cols} | {
        a.alias.lower() for a in tree.find_all(exp.Alias)
    }
    for col in tree.find_all(exp.Column):
        name = col.name.lower()
        if not col.table and name in relations and name not in known:
            raise Rejected("V05", "a relation alias cannot be used as a value")


def _select_depth(node: exp.Expression) -> int:
    depth, parent = 0, node.parent
    while parent is not None:
        depth += isinstance(parent, exp.Select)
        parent = parent.parent
    return depth


def _check_tree(tree: exp.Expression) -> None:
    ctes = list(tree.find_all(exp.CTE))
    if len(ctes) > MAX_CTES:
        raise Rejected("V10", f"more than {MAX_CTES} CTEs")
    if len(list(tree.find_all(exp.Join))) > MAX_JOINS:
        raise Rejected("V10", f"more than {MAX_JOINS} joins")
    cte_names = {c.alias.lower() for c in ctes}
    if any(w.args.get("recursive") for w in tree.find_all(exp.With)):
        raise Rejected("V08", "WITH RECURSIVE is not allowed")
    # A CTE must not shadow a catalog or exposed name, nor read itself (non-recursive WITH).
    for cte in ctes:
        name = cte.alias.lower()
        inner = {t.name.lower() for t in cte.this.find_all(exp.Table) if not t.args.get("db")}
        if name.startswith("pg_") or name == "information_schema" or name in VIEWS or name in inner:
            raise Rejected("V04", f"CTE name {name} shadows a relation")
    if (
        max(
            (_select_depth(n) for n in tree.find_all(exp.Select)),
            default=0,
        )
        > MAX_DEPTH
    ):
        raise Rejected("V10", f"subqueries nested deeper than {MAX_DEPTH}")
    for node in tree.walk():
        _check_node(node, cte_names)
    _check_whole_row(tree, cte_names)
    try:
        # Column resolution on a throwaway copy: unknown or ambiguous columns, whole-row aliases.
        from sqlglot.optimizer.qualify import qualify

        qualify(tree.copy(), schema=_SCHEMA_DICT, dialect="postgres", validate_qualify_columns=True)
    except Exception as err:  # fail closed on anything the resolver cannot explain
        raise Rejected("V05", "a column is not in the referenced views") from err


def _parse_one(text: str) -> exp.Expression:
    try:
        stmts = [s for s in sqlglot.parse(text, read="postgres") if s is not None]
    except (SqlglotError, RecursionError) as err:
        raise Rejected("V01", "the text does not parse as one PostgreSQL statement") from err
    if len(stmts) != 1:
        raise Rejected("V01", "expected exactly one statement")
    return stmts[0]


def validate(raw: str) -> Validated:
    """Return the canonical, hashed SELECT or raise `Rejected` with a rule id."""
    text, _ = prefilter(raw)
    tree = _parse_one(text)
    _check_root(tree)
    try:
        _check_tree(tree)
        canonical = _gen(tree)
        again, saw_comment = prefilter(canonical)
        if saw_comment or again.strip() != canonical:
            raise Rejected("V11", "the regenerated SQL contains a comment or a hazard")
        if _parse_one(canonical) != tree:
            raise Rejected("V11", "the regenerated SQL parses to a different tree")
    except RecursionError as err:
        raise Rejected("V10", "nesting too deep") from err
    return Validated(canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest())
