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
from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError, SqlglotError

from askdata.allowed import (
    ARITY,
    CAST_TARGETS,
    EXTRACT_FIELDS,
    FUNCTIONS,
    INTERVAL_UNITS,
    SCHEMA,
    SYNTAX_FUNCTIONS,
    TRUNC_UNITS,
    VIEWS,
)
from askdata.safe_text import is_forbidden

# sqlglot logs a warning when it falls back to a generic Command; the rejection below is the signal we use.
logging.getLogger("sqlglot").setLevel(logging.ERROR)

MAX_CHARS = 4000
MAX_LITERAL = 200
MAX_JOINS = 8
MAX_CTES = 4
MAX_DEPTH = 6
MAX_NODES = 2000

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
    "V11": "the regenerated SQL does not settle: it parses to a different tree that regenerates to different text",
    "V12": "an identifier that is not a plain name (quoted ones must be lower-case)",
}


_OFF: set[str] = (
    set()
)  # rule ids switched off; ONLY the mutation test fills it, production never does


def assert_all_rules_on() -> None:
    """Startup guard: no rule may be switched off outside the mutation test. Raises RuntimeError."""
    if _OFF:
        raise RuntimeError(f"validator rules switched off: {sorted(_OFF)}")


def _fail(rule: str, detail: str) -> None:
    """Reject with `rule`, unless the mutation test switched that rule off (then checking simply continues)."""
    if rule not in _OFF:
        raise Rejected(rule, detail)


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

_PLAIN_TEXT = re.compile(r"[ -~\n\t]*")
_PREFIX_CHARS = frozenset("eEbBxXnN")
_IDENT_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")


def prefilter(text: str) -> tuple[str, bool]:
    """Reject hazards in the raw text; return (text without one trailing semicolon and with every comment turned
    into spaces, saw_comment). The parser therefore never sees a comment: two parsers cannot disagree about where
    a nested comment ends, and a comment inside a multi-word keyword (GROUP /**/ BY) cannot confuse sqlglot.

    One left-to-right pass with the states CODE, STRING, QIDENT, LINE_COMMENT and BLOCK_COMMENT (nested)."""
    if len(text) > MAX_CHARS:
        _fail("V09", f"text is over {MAX_CHARS} characters")
    if not _PLAIN_TEXT.fullmatch(
        text
    ):  # fast path: printable ASCII, newline and tab need no per-character check
        for ch in text:
            if is_forbidden(ch):
                _fail("V09", f"forbidden character U+{ord(ch):04X}")
    if chr(92) in text:
        _fail(
            "V09", "backslash is not allowed"
        )  # two parsers can disagree about where a literal ends
    state, depth, semi, saw_comment = "CODE", 0, -1, False
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        ch, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if state == "CODE":
            if semi >= 0 and not ch.isspace() and not text.startswith(("--", "/*"), i):
                _fail("V01", "more than one statement")  # anything after the first ; but a comment
            if ch == "'":
                state = "STRING"
            elif ch == '"':
                state = "QIDENT"
            elif ch == "-" and nxt == "-":
                state, saw_comment, out[i], out[i + 1], i = "LINE", True, " ", " ", i + 1
            elif ch == "/" and nxt == "*":
                state, depth, saw_comment, out[i], out[i + 1], i = "BLOCK", 1, True, " ", " ", i + 1
            elif ch == "$":
                _fail("V09", "dollar quoting and parameters are not allowed")
            elif ord(ch) > 127:
                _fail("V09", "non-ASCII character outside a string literal")
            elif ch == ";":
                if semi >= 0:
                    _fail("V01", "more than one statement")
                semi = i
                out[i] = " "
            elif ch in _PREFIX_CHARS and nxt == "'" and (i == 0 or text[i - 1] not in _IDENT_CHARS):
                _fail("V09", "string prefix (E, B, X, N) is not allowed")
            elif ch in "uU" and nxt == "&" and (i == 0 or text[i - 1] not in _IDENT_CHARS):
                _fail("V09", "U& escape strings and identifiers are not allowed")
        elif state == "STRING":
            if ch == "'":
                if nxt == "'":
                    i += 1
                else:
                    state = "CODE"
        elif state == "QIDENT":
            if ord(ch) > 127:
                _fail("V09", "non-ASCII character in a quoted identifier")
            if ch == '"':
                if nxt == '"':
                    i += 1
                else:
                    state = "CODE"
        elif state == "LINE":
            if ch == "\n":
                state = "CODE"
            else:
                out[i] = " "
        else:  # BLOCK: every character of a comment (nested ones too) becomes a space
            out[i] = " "
            if ch == "/" and nxt == "*":
                depth, out[i + 1], i = depth + 1, " ", i + 1
            elif ch == "*" and nxt == "/":
                depth, out[i + 1], i = depth - 1, " ", i + 1
                if depth == 0:
                    state = "CODE"
        i += 1
    if state in ("STRING", "QIDENT", "BLOCK"):
        _fail("V01", "unterminated quote or comment")
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
_BARE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# The exposed views the statement is judged against. Default: the spike catalog; the Lumen catalog (the gold set's
# seven views) is passed as `validate(raw, views=...)`. A ContextVar keeps the rule code free of plumbing.
_CATALOG: ContextVar[Mapping[str, tuple[str, ...]]] = ContextVar("askdata_catalog", default=VIEWS)


def _views() -> Mapping[str, tuple[str, ...]]:
    return _CATALOG.get()


def _schema_dict() -> dict:
    return {SCHEMA: {v: dict.fromkeys(cols, "TEXT") for v, cols in _views().items()}}


def _gen(node: exp.Expression) -> str:
    return node.sql(dialect="postgres", comments=False)


def _check_root(tree: exp.Expression) -> None:
    if isinstance(tree, exp.Select | exp.SetOperation):
        return
    if isinstance(tree, _WRITE_ROOTS):
        _fail("V03", f"{type(tree).__name__} statements are not allowed")
    _fail("V02", f"root is {type(tree).__name__}, not a SELECT")


def _check_function(node: exp.Func) -> None:
    if isinstance(node, exp.Anonymous):
        # sqlglot has no typed node for a few allowed functions (age, make_date): judged by name like the rest.
        if node.name.lower() not in FUNCTIONS:
            _fail("V06", f"function {node.name.lower()} is not allowed")
        _check_arity(node, node.name.lower())
        return
    if type(node).__name__ in SYNTAX_FUNCTIONS:
        return
    name = _function_name(node)
    if name not in FUNCTIONS:
        _fail("V06", f"function {name} is not allowed")
    _check_arity(node, name)


def _function_name(node: exp.Func) -> str:
    match = _FUNC_NAME.match(_gen(node))
    return match.group(1).lower() if match else type(node).__name__.lower()


def _arg_count(call: str) -> int:
    """Top-level arguments in the text `NAME(a, b, ...)` (string and parenthesis aware); 0 for `NAME()`."""
    inner, depth, quote, count, seen = call[call.index("(") + 1 :], 0, False, 1, False
    for ch in inner:
        if quote:
            quote = ch != "'"
        elif ch == "'":
            quote, seen = True, True
        elif ch == "(":
            depth, seen = depth + 1, True
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
        elif ch == "," and depth == 0:
            count += 1
        elif not ch.isspace():
            seen = True
    return count if seen else 0


def _check_arity(node: exp.Func, name: str) -> None:
    """sqlglot accepts any number of arguments; PostgreSQL would answer 42883. Refuse here, with a clear rule."""
    if name in ARITY and "(" in _gen(node):
        low, high = ARITY[name]
        n = _arg_count(_gen(node))
        if n < low or (high is not None and n > high):
            _fail("V06", f"function {name} does not take {n} arguments")


def _check_cast(node: exp.Cast) -> None:
    target = node.args.get("to")
    # type() is exp.DataType on purpose: ObjectIdentifier (regclass) is a subclass and must not pass.
    if type(target) is not exp.DataType or getattr(target.this, "name", "") not in CAST_TARGETS:
        _fail("V07", "cast target is not in the allowed list")


def _visible_ctes(node: exp.Expression) -> set[str]:
    """CTE names a relation reference can see, by position: inside a WITH, only the CTEs defined BEFORE the one
    containing the reference (itself too if RECURSIVE, which is rejected elsewhere); in the body of a query, every
    CTE of its own WITH and of the enclosing queries. Anything else resolves to the catalog in Postgres."""
    names: set[str] = set()
    child, parent = node, node.parent
    while parent is not None:
        if isinstance(parent, exp.With):
            idx = (
                parent.expressions.index(child)
                if child in parent.expressions
                else len(parent.expressions)
            )
            upto = idx + 1 if parent.args.get("recursive") else idx
            names |= {c.alias.lower() for c in parent.expressions[:upto]}
        else:
            with_ = parent.args.get("with_")
            if with_ is not None and child is not with_:
                names |= {c.alias.lower() for c in with_.expressions}
        child, parent = parent, parent.parent
    return names


def _check_table(node: exp.Table, cte_names: set[str]) -> None:
    ident = node.this
    if not isinstance(ident, exp.Identifier):
        _fail("V04", "table functions are not allowed in FROM")
    if node.args.get("catalog") is not None:
        _fail("V04", "three-part relation names are not allowed")
    db = node.args.get("db")
    if db is None:
        if ident.name.lower() not in _visible_ctes(node):
            _fail("V04", f"relation {ident.name.lower()} is not an exposed view")
    elif db.name.lower() != SCHEMA or ident.name.lower() not in _views():
        _fail("V04", f"relation {db.name.lower()}.{ident.name.lower()} is not an exposed view")


def _relation_columns(rel: exp.Expression) -> set[str] | None:
    """Lower-case output column names of a FROM item, or None when they cannot be known (then any column may match)."""
    if isinstance(rel, exp.Table):
        if rel.args.get("db") is not None:
            return {c.lower() for c in _views().get(rel.name.lower(), ())}
        for cte in rel.root().find_all(exp.CTE):
            if cte.alias.lower() == rel.name.lower():
                listed = cte.args["alias"].columns if cte.args.get("alias") else []
                return {c.name.lower() for c in listed} or _select_names(cte.this)
        return None
    if isinstance(rel, exp.Subquery):
        return _select_names(rel.this)
    return None


def _select_names(query: exp.Expression) -> set[str] | None:
    selects = getattr(query, "selects", None)
    if not selects or any(isinstance(s, exp.Star) or s.is_star for s in selects):
        return None
    return {s.alias_or_name.lower() for s in selects}


def _on_links(join: exp.Join) -> bool:
    """The ON condition names a column of the joined relation AND a column of a relation that comes before it."""
    select = join.parent
    if not isinstance(select, exp.Select):
        return False
    first = select.args.get("from_") or select.args.get("from")
    earlier = [first.this] if first is not None else []
    for other in select.args.get("joins") or []:
        if other is join:
            break
        earlier.append(other.this)
    columns = {r.alias_or_name.lower(): _relation_columns(r) for r in [*earlier, join.this]}
    joined = join.this.alias_or_name.lower()
    before = {r.alias_or_name.lower() for r in earlier}

    def touches(aliases: set[str], col: exp.Column) -> bool:
        if col.table:
            return col.table.lower() in aliases
        return any(columns[a] is None or col.name.lower() in columns[a] for a in aliases)

    cols = list(join.args["on"].find_all(exp.Column))
    return any(touches({joined}, c) for c in cols) and any(touches(before, c) for c in cols)


def _check_node(node: exp.Expression, cte_names: set[str]) -> None:
    """Specific rules first (so the rule id names the real problem), then default deny."""
    if isinstance(
        node, exp.Insert | exp.Update | exp.Delete | exp.Merge | exp.Into | exp.Lock | exp.Command
    ):
        _fail("V03", f"{type(node).__name__} is not allowed")
    if isinstance(node, exp.Select) and (node.args.get("into") or node.args.get("locks")):
        _fail("V03", "SELECT INTO and locking clauses are not allowed")
    if isinstance(node, exp.With) and node.args.get("recursive"):
        _fail("V08", "WITH RECURSIVE is not allowed")
    if isinstance(node, exp.Join) and (
        node.args.get("kind") == "CROSS"
        or node.args.get("method")
        or not (node.args.get("on") is not None or node.args.get("using"))
    ):
        _fail("V08", "every join needs ON or USING (no CROSS, NATURAL or comma join)")
    if (
        isinstance(node, exp.Join)
        and node.args.get("on") is not None
        and len({(c.table.lower(), c.name.lower()) for c in node.args["on"].find_all(exp.Column)})
        < 2
    ):
        _fail(
            "V08",
            "a join condition must compare two different columns (ON TRUE, ON 1 = 1 are cross joins)",
        )
    if isinstance(node, exp.Join) and node.args.get("on") is not None and not _on_links(node):
        _fail(
            "V08", "a join condition must use a column of the joined relation and of an earlier one"
        )
    if isinstance(node, exp.Dot) and isinstance(node.expression, exp.Func):
        _fail("V06", "schema-qualified function names are not allowed")
    if isinstance(node, exp.Lateral | exp.TableSample | exp.Unnest | exp.Values):
        _fail("V04", f"{type(node).__name__} is not allowed")
    if isinstance(node, exp.Parameter | exp.Placeholder):
        _fail("V09", "parameters and placeholders are not allowed")
    if isinstance(node, exp.Table):
        _check_table(node, cte_names)
    elif isinstance(node, exp.Cast):
        _check_cast(node)
    if isinstance(node, _ALLOWED_NODES):
        pass  # operators such as AND are also Func subclasses in sqlglot: the class list wins
    elif isinstance(node, exp.Binary | exp.Unary) and not isinstance(
        node, exp.Pow
    ):  # POWER() is a function
        _fail(
            "V10", f"operator {type(node).__name__} is not allowed"
        )  # operators that are also Func
    elif isinstance(node, exp.Func):
        _check_function(node)
    else:
        _fail("V10", f"{type(node).__name__} is not allowed")
    _check_detail(node)


def _check_detail(node: exp.Expression) -> None:
    if isinstance(node, exp.Identifier) and not (
        _PLAIN_IDENT.fullmatch(node.name)
        if node.args.get("quoted")
        else _BARE_IDENT.fullmatch(
            node.name
        )  # ->> or ~ as an alias parses in sqlglot, not in Postgres
    ):
        _fail("V12", "identifiers must be plain names (quoted ones lower-case)")
    if isinstance(node, exp.Var) and not (
        (isinstance(node.parent, exp.Interval) and node.arg_key == "unit")
        or (isinstance(node.parent, exp.TimestampTrunc) and node.name.lower() in TRUNC_UNITS)
        or (isinstance(node.parent, exp.Extract) and node.arg_key == "this")
    ):
        _fail(
            "V10", "a bare keyword is not allowed here"
        )  # sqlglot reads `f(2026, 3, SELECT)` as a Var
    if isinstance(node, exp.Alias) and not (
        isinstance(node.parent, exp.Select) and node.arg_key == "expressions"
    ):  # sqlglot accepts `(x AS y)` anywhere; PostgreSQL only in a select list
        _fail("V10", "an alias is allowed only on a select-list item")
    if isinstance(node, exp.Select) and not (
        node.parent is None
        or isinstance(node.parent, exp.Subquery | exp.CTE | exp.Exists | exp.SetOperation)
    ):
        _fail(
            "V10", "a nested SELECT needs parentheses"
        )  # sqlglot reads `f(1, SELECT 1)` and `FROM SELECT 1`
    if (
        isinstance(node, exp.Distinct)
        and not node.expressions
        and not isinstance(node.parent, exp.Select)
    ):
        _fail("V10", "DISTINCT needs an argument")
    if isinstance(node, exp.Group | exp.Order) and not node.expressions:
        _fail("V10", "GROUP BY and ORDER BY need at least one expression")
    if isinstance(node, exp.Extract) and not (
        isinstance(node.this, exp.Var) and node.this.name.lower() in EXTRACT_FIELDS
    ):
        _fail("V10", "EXTRACT needs a plain field name such as year, month or day")
    if isinstance(node, exp.DataTypeParam) and not (
        isinstance(node.this, exp.Literal) and not node.this.is_string
    ):
        _fail(
            "V07", "a type parameter must be a number"
        )  # sqlglot reads DECIMAL(email, 2) as a column
    if isinstance(node, exp.Column) and not isinstance(node.this, exp.Identifier | exp.Star):
        _fail("V05", "a column reference must be a name")  # sqlglot reads `order_id.7` as a column
    if isinstance(node, exp.Star) and not isinstance(
        node.parent, exp.Select | exp.Count | exp.Column
    ):
        _fail("V10", "* is allowed only as a select item, in count(*) and as alias.*")
    if isinstance(node, exp.In) and not (
        node.expressions or node.args.get("query") or node.args.get("field")
    ):
        _fail("V10", "IN needs a list or a subquery")
    if isinstance(node, exp.Column) and (node.args.get("db") or node.args.get("catalog")):
        _fail("V05", "columns are referenced by view alias and name only")
    if isinstance(node, exp.Literal) and node.is_string and len(node.this) > MAX_LITERAL:
        _fail("V10", f"string literal over {MAX_LITERAL} characters")
    if isinstance(node, exp.Select) and node.args.get("windows"):
        _fail("V10", "named windows are not allowed")
    if isinstance(node, exp.Window) and node.args.get("alias") is not None:
        _fail(
            "V10", "named windows are not allowed"
        )  # sqlglot reads `OVER (ORDER ORDER BY x)` as window ORDER
    if isinstance(node, exp.Window) and node.args.get("spec") is not None:
        _fail("V10", "window frames are not allowed")
    if isinstance(node, exp.WithinGroup) and not isinstance(node.this, exp.PercentileCont):
        _fail("V10", "WITHIN GROUP is allowed only after percentile_cont")
    if isinstance(node, exp.PercentileCont) and node.args.get("expression") is not None:
        _fail(
            "V06", "function percentile_cont does not take 2 arguments"
        )  # sqlglot swaps them silently
    if isinstance(node, exp.Filter) and not isinstance(node.this, exp.AggFunc):
        _fail("V10", "FILTER is allowed only on aggregates")
    if isinstance(node, exp.AtTimeZone):
        zone = node.args.get("zone")
        if not (isinstance(zone, exp.Literal) and zone.is_string and _ZONE.fullmatch(zone.this)):
            _fail("V10", "AT TIME ZONE needs a plain string literal zone")
    if isinstance(node, exp.Interval):
        value, unit = node.this, node.args.get("unit")
        if not (
            isinstance(value, exp.Literal)
            and re.fullmatch(r"\d{1,4}", value.this)
            and isinstance(unit, exp.Var)
            and unit.name.lower() in INTERVAL_UNITS
        ):
            _fail("V10", "INTERVAL needs a number and a unit: day, week, month or year")


def _check_whole_row(tree: exp.Expression, cte_names: set[str]) -> None:
    """A bare relation alias used as a value (`SELECT o FROM orders_v o`) is a whole-row reference in Postgres."""
    relations = (
        {t.alias_or_name.lower() for t in tree.find_all(exp.Table)}
        | {q.alias.lower() for q in tree.find_all(exp.Subquery) if q.alias}
        | cte_names
    )
    known = {c for cols in _views().values() for c in cols} | {
        a.alias.lower() for a in tree.find_all(exp.Alias)
    }
    for col in tree.find_all(exp.Column):
        name = col.name.lower()
        if not col.table and name in relations and name not in known:
            _fail("V05", "a relation alias cannot be used as a value")


def _select_depth(node: exp.Expression) -> int:
    depth, parent = 0, node.parent
    while parent is not None:
        depth += isinstance(parent, exp.Select)
        parent = parent.parent
    return depth


def _check_tree(tree: exp.Expression) -> None:
    if sum(1 for _ in tree.walk()) > MAX_NODES:
        _fail("V10", f"more than {MAX_NODES} nodes")
    ctes = list(tree.find_all(exp.CTE))
    if len(ctes) > MAX_CTES:
        _fail("V10", f"more than {MAX_CTES} CTEs")
    if len(list(tree.find_all(exp.Join))) > MAX_JOINS:
        _fail("V10", f"more than {MAX_JOINS} joins")
    cte_names = {c.alias.lower() for c in ctes}
    if any(w.args.get("recursive") for w in tree.find_all(exp.With)):
        _fail("V08", "WITH RECURSIVE is not allowed")
    # A CTE must not shadow a catalog or exposed name, nor read itself (non-recursive WITH).
    for cte in ctes:
        name = cte.alias.lower()
        inner = {t.name.lower() for t in cte.this.find_all(exp.Table) if not t.args.get("db")}
        if (
            name.startswith("pg_")
            or name == "information_schema"
            or name in _views()
            or name in inner
        ):
            _fail("V04", f"CTE name {name} shadows a relation")
    if (
        max(
            (_select_depth(n) for n in tree.find_all(exp.Select)),
            default=0,
        )
        > MAX_DEPTH
    ):
        _fail("V10", f"subqueries nested deeper than {MAX_DEPTH}")
    for node in tree.walk():
        _check_node(node, cte_names)
    _check_whole_row(tree, cte_names)
    resolved = None
    try:
        # Column resolution on a throwaway copy: unknown or ambiguous columns, whole-row aliases.
        from sqlglot.optimizer.qualify import qualify

        resolved = qualify(
            tree.copy(), schema=_schema_dict(), dialect="postgres", validate_qualify_columns=True
        )
    except OptimizeError:
        _fail("V05", "a column is not in the referenced views")
    except Exception:  # noqa: BLE001  # fail closed on anything else the resolver trips over (a sqlglot bug)
        _fail("V05", "the column resolver could not check this statement")
    # sqlglot's resolver lets an unknown bare column through in HAVING (it may be a select alias): after
    # resolution every column must belong to a relation, except an output name in ORDER BY (legal in Postgres).
    for col in resolved.find_all(exp.Column) if resolved is not None else ():
        if not col.table and not _output_name_in_order_by(col):
            _fail("V05", "a column is not in the referenced views")
            break


def _output_name_in_order_by(col: exp.Column) -> bool:
    """True when the nearest enclosing Select/Order of `col` is an ORDER BY (an output name there is legal); a
    column inside a subquery that merely sits in an ORDER BY belongs to that subquery's Select and is not exempt."""
    node = col.parent
    while node is not None and not isinstance(node, exp.Select | exp.Order):
        node = node.parent
    return isinstance(node, exp.Order)


def _parse_one(text: str) -> exp.Expression:
    try:
        stmts = [s for s in sqlglot.parse(text, read="postgres") if s is not None]
    except (SqlglotError, RecursionError) as err:
        raise Rejected("V01", "the text does not parse as one PostgreSQL statement") from err
    if not stmts:
        raise Rejected("V01", "the text holds no statement")
    if len(stmts) != 1:
        _fail("V01", "expected exactly one statement")
    return stmts[0]


def validate(raw: str, *, views: Mapping[str, tuple[str, ...]] | None = None) -> Validated:
    """Return the canonical, hashed SELECT or raise `Rejected` with a rule id. `views` overrides the exposed catalog."""
    token = _CATALOG.set(views if views is not None else VIEWS)
    try:
        return _validate(raw)
    finally:
        _CATALOG.reset(token)


def describe(
    raw: str, *, views: Mapping[str, tuple[str, ...]] | None = None
) -> dict[str, list[str]]:
    """What an ACCEPTED statement is made of: node classes, function names and cast targets (the allowlist
    derivation tool and its test use this; it raises `Rejected` for a statement that does not validate)."""
    canonical = validate(raw, views=views).canonical_sql
    nodes: set[str] = set()
    funcs: set[str] = set()
    casts: set[str] = set()
    for node in sqlglot.parse_one(canonical, read="postgres").walk():
        nodes.add(type(node).__name__)
        if isinstance(node, exp.Anonymous):
            funcs.add(node.name.lower())
        elif (
            isinstance(node, exp.Func)
            and not isinstance(node, (*_ALLOWED_NODES, exp.Binary, exp.Unary))
            and type(node).__name__ not in SYNTAX_FUNCTIONS
        ):
            funcs.add(_function_name(node))
        if isinstance(node, exp.Cast):
            casts.add(node.args["to"].this.name)
    return {"nodes": sorted(nodes), "functions": sorted(funcs), "casts": sorted(casts)}


def _validate(raw: str) -> Validated:
    text, _ = prefilter(raw)
    tree = _parse_one(text)
    _check_root(tree)
    try:
        _check_tree(tree)
        canonical = _gen(tree)
        again, saw_comment = prefilter(canonical)
        if saw_comment or again.strip() != canonical:
            _fail("V11", "the regenerated SQL contains a comment or a hazard")
        again_tree = _parse_one(canonical)
        if again_tree != tree:
            # The generator may normalise (ROUND(AVG(x), 2) gains a CAST). What matters is that the tree of the text
            # that will RUN passes every rule too and that regenerating it gives the same text (a fixed point).
            _check_root(again_tree)
            _check_tree(again_tree)
            if _gen(again_tree) != canonical or _parse_one(_gen(again_tree)) != again_tree:
                _fail("V11", "the regenerated SQL parses to a different tree and does not settle")
    except RecursionError as err:
        raise Rejected("V10", "nesting too deep") from err
    except Rejected:
        raise
    except (
        Exception
    ) as err:  # a malformed tree sqlglot built (found by the fuzz): refuse, never crash
        raise Rejected("V10", "the statement has a shape the validator cannot check") from err
    return Validated(canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest())
