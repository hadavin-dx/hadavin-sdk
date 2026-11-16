"""The independent oracle (pglast, the PostgreSQL grammar, CI-only): is this accepted statement what the validator
claims, one SELECT that touches only exposed views and allowlisted functions, built from allowlisted node kinds?

It shares no code with the validator: a different parser, a node-class whitelist and its own rules.
"""

from __future__ import annotations

import pglast
from askdata.allowed import FUNCTIONS, SCHEMA, VIEWS
from pglast import ast
from pglast.visitors import Visitor

# pglast spells some allowed constructs with their catalog names (extract -> pg_catalog.extract, trim -> btrim ...).
ORACLE_FUNCTIONS = FUNCTIONS | {"btrim", "timezone", "date_part", "pg_catalog"}
NODE_WHITELIST = frozenset({
    "RawStmt", "SelectStmt", "ResTarget", "ColumnRef", "A_Star", "String", "Integer", "Float", "Boolean", "A_Const",
    "A_Expr", "BoolExpr", "FuncCall", "TypeCast", "TypeName", "CaseExpr", "CaseWhen", "CoalesceExpr", "MinMaxExpr",
    "NullTest", "BooleanTest", "SubLink", "JoinExpr", "RangeVar", "RangeSubselect", "Alias", "WithClause",
    "CommonTableExpr", "SortBy", "WindowDef",
})  # fmt: skip
OPERATORS = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "%",
        "=",
        "<>",
        "!=",
        "<",
        ">",
        "<=",
        ">=",
        "~~",
        "~~*",
        "!~~",
        "!~~*",
        "||",
    }
)
TYPES = frozenset({
    "date", "timestamp", "timestamptz", "int2", "int4", "int8", "numeric", "float8", "text", "varchar", "bool",
    "interval", "bpchar", "pg_catalog",
})  # fmt: skip
TYPE_SCHEMAS = frozenset({"pg_catalog"})
PG_CATALOG_FUNCTIONS = frozenset(
    {"extract", "substring", "btrim", "timezone", "position", "date_part", "like_escape"}
)


class _Collect(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.ctes: set[str] = set()
        self.aliases: set[str] = set()

    def visit_CommonTableExpr(self, ancestors, node):  # pglast visitor naming
        self.ctes.add(node.ctename)
        self.aliases |= {c.sval for c in node.aliascolnames or ()}

    def visit_Alias(self, ancestors, node):
        self.aliases.add(node.aliasname)
        self.aliases |= {c.sval for c in node.colnames or ()}

    def visit_ResTarget(self, ancestors, node):
        if node.name:
            self.aliases.add(node.name)


class _Judge(Visitor):
    def __init__(self, ctes: set[str], aliases: set[str]) -> None:
        super().__init__()
        self.ctes, self.aliases, self.problems = ctes, aliases, []
        self.columns = {c for cols in VIEWS.values() for c in cols} | aliases

    def visit(self, ancestors, node):
        name = type(node).__name__
        if name not in NODE_WHITELIST:
            self.problems.append(f"node kind {name}")

    def visit_SelectStmt(self, ancestors, node):
        if node.intoClause is not None or node.lockingClause or node.valuesLists:
            self.problems.append("INTO, locking clause or VALUES")

    def visit_RangeVar(self, ancestors, node):
        ok = (
            node.catalogname is None
            and (
                node.schemaname == SCHEMA
                and node.relname in VIEWS
                or node.schemaname is None
                and node.relname in self.ctes
            )
            and node.inh is not False
        )
        if not ok:
            self.problems.append(f"relation {node.schemaname}.{node.relname}")

    def visit_RangeSubselect(self, ancestors, node):
        if node.lateral:
            self.problems.append("LATERAL")

    def visit_FuncCall(self, ancestors, node):
        parts = [p.sval for p in node.funcname]
        if len(parts) == 2 and parts[0] != "pg_catalog" or len(parts) > 2:
            self.problems.append(f"qualified function {parts}")
        elif (
            len(parts) == 2
            and parts[1] not in PG_CATALOG_FUNCTIONS | FUNCTIONS
            or len(parts) == 1
            and parts[0] not in ORACLE_FUNCTIONS
        ):
            self.problems.append(f"function {parts}")
        if node.agg_order is not None and parts[-1] != "percentile_cont":
            self.problems.append("ORDER BY inside an aggregate")

    def visit_WindowDef(self, ancestors, node):
        if node.frameOptions & 0x1:  # FRAMEOPTION_NONDEFAULT: a frame clause was written out
            self.problems.append("explicit window frame")

    def visit_A_Expr(self, ancestors, node):
        names = [n.sval for n in node.name]
        if any(n not in OPERATORS for n in names) and node.kind.name not in {
            "AEXPR_BETWEEN",
            "AEXPR_NOT_BETWEEN",
        }:
            self.problems.append(f"operator {names} {node.kind.name}")

    def visit_TypeCast(self, ancestors, node):
        names = [n.sval for n in node.typeName.names]
        if (
            names[-1] not in TYPES
            or len(names) > 1
            and names[0] not in TYPE_SCHEMAS
            or node.typeName.arrayBounds
        ):
            self.problems.append(f"cast to {names}")

    def visit_ColumnRef(self, ancestors, node):
        fields = [f.sval if isinstance(f, ast.String) else "*" for f in node.fields]
        if fields[-1] != "*" and fields[-1] not in self.columns or len(fields) > 2:
            self.problems.append(f"column {fields}")


def judge(sql: str) -> list[str]:
    """Empty list: the PostgreSQL grammar agrees the text is one allowed SELECT. Otherwise the reasons."""
    try:
        stmts = pglast.parse_sql(sql)
    except pglast.parser.ParseError as err:
        return [f"does not parse: {err}"]
    if len(stmts) != 1 or not isinstance(stmts[0].stmt, ast.SelectStmt):
        return ["not exactly one SELECT"]
    collect = _Collect()
    collect(stmts)
    judge_ = _Judge(collect.ctes, collect.aliases)
    judge_(stmts)
    return judge_.problems
