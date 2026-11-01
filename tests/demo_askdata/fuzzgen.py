"""Grammar-based statement generator for the validator fuzz test (seeded, deterministic, no `hypothesis`).

`case(rng)` returns `(kind, sql)`:
  clean     a valid analytics query built from a small grammar over the exposed views (with comments, odd
            whitespace and keyword case sprinkled between tokens); the validator is free to accept or refuse it
  poisoned  the same, with one hazard dropped between tokens in CODE position (never inside a literal or
            comment): a catalog table, a hidden column, a forbidden function, a regclass cast, a locking
            clause, a backslash, a dollar quote, an escape string, a stacked statement ...; MUST be refused
  mutated   a clean statement with random token edits (delete, duplicate, swap, replace by a hostile token);
            no expectation except the accepted-statement invariants
"""

# test data generator, not security randomness

# ruff: noqa: S608, S311  # the SQL text is the test data; seeded randomness is test data, not security

from __future__ import annotations

import random
import re

from askdata.allowed import VIEWS

KIND = {
    "customer_id": "num", "order_id": "num", "product_id": "num", "order_item_id": "num", "quantity": "num",
    "unit_price": "num", "total_amount": "num", "line_amount": "num", "order_date": "date", "signup_date": "date",
}  # fmt: skip
TOKEN = re.compile(r"'(?:[^']|'')*'|\"[^\"]*\"|\d+\.\d+|\w+|<=|>=|<>|\|\||::|\S")
BACKSLASH = chr(92)
HOSTILE = [
    ";", "--", "/*", "*/", "'", '"', "(", ")", ",", ".", "*", "$", "$$", "$1", "%s", "?", ":x", "@", "#", "&", "|", "~",
    "SELECT", "FROM", "WHERE", "UNION", "INSERT", "DELETE", "COMMIT", "FOR UPDATE", "INTO t", "RECURSIVE", "LATERAL",
    "pg_sleep(1)", "email", "pg_shadow", "shop.customers", "::regclass", "::oid", "E'x'", "U&'x'", "B'1'", "X'1'",
    BACKSLASH, chr(0), chr(0x0456), chr(0xA0), chr(0x202E), chr(10), chr(13), "1e999", "0x1F", "->>", "@>", "!~",
]  # fmt: skip
POISON = [
    "FROM pg_shadow", "FROM shop.customers", "FROM pg_catalog.pg_class", "FROM information_schema.tables",
    "FROM generate_series(1, 3) g", "FROM unnest(ARRAY[1, 2]) u",
    ", email", ", customers_v", ", pg_sleep(1)", ", version()", ", current_setting('x')", ", now()", ", random()",
    ", current_user", ", repeat('x', 9)", ", set_config('a', 'b', false)", ", lo_import('x')", ", 1::regclass",
    ", 'x'::oid", ", 'x'::xml", ", $1", ", %s", ", $$x$$", ", E'x'", ", U&'x'", ", " + BACKSLASH, ", " + chr(0),
    ", " + chr(0x0456), ", ROW(1, 2)", ", ARRAY[1]", ", 'a' ~ 'b'", ", '{}' -> 'a'", ", 1 OPERATOR(+) 1",
    "FOR UPDATE", "FOR SHARE", "INTO scratch_t", "TABLESAMPLE SYSTEM (1)", "CROSS JOIN analytics.orders_v",
    ", analytics.orders_v", "JOIN analytics.orders_v z ON true", "; DELETE FROM shop.orders", "; SELECT 1",
    "WITH RECURSIVE r AS (SELECT 1) SELECT 1 FROM r UNION ALL", "ROWS BETWEEN 1 PRECEDING AND CURRENT ROW",
    "/* unterminated", "' unterminated", '" unterminated',
]  # fmt: skip
SEPARATORS = [" "] * 12 + [
    "  ",
    "\n",
    "\t",
    " /* c */ ",
    " /* a /* nested */ b */ ",
    " -- note\n",
    " /**/ ",
]


class Gen:
    def __init__(self, rng: random.Random) -> None:
        self.r = rng
        self.n = 0

    def pick(self, seq):
        return self.r.choice(seq)

    def chance(self, p: float) -> bool:
        return self.r.random() < p

    # ---- sources: (sql, alias, {column: kind})
    def view(self, extra=()):
        name = self.pick(sorted(VIEWS))
        self.n += 1
        return (f"analytics.{name}", f"t{self.n}", {c: KIND.get(c, "text") for c in VIEWS[name]})

    # ---- expressions
    def lit(self, kind):
        if kind == "num":
            return self.pick(["0", "1", "2", "10", "100", "0.5", "2.25"])
        if kind == "date":
            return self.pick(
                ["DATE '2026-01-01'", "CAST('2026-06-30' AS DATE)", "make_date(2026, 3, 1)"]
            )
        return self.pick(
            ["'paid'", "'a'", "'US'", "'x y'", "'it''s'", "'a--b'", "'c/*d*/'", "'%a%'", "''"]
        )

    def col(self, scope, kind):
        options = [(a, c) for _, a, cols in scope for c, k in cols.items() if k == kind]
        if not options:
            return self.lit(kind)
        alias, c = self.pick(options)
        return f"{alias}.{c}" if len(scope) > 1 or self.chance(0.5) else c

    def expr(self, scope, kind, d=0):
        leaf = d >= 2 or self.chance(0.35)
        if leaf:
            return self.col(scope, kind) if self.chance(0.75) else self.lit(kind)
        e = lambda k=kind: self.expr(scope, k, d + 1)
        if kind == "num":
            return self.pick(
                [
                    lambda: f"({e()} {self.pick(['+', '-', '*', '/'])} {e()})",
                    lambda: f"{self.pick(['abs', 'ceil', 'floor', 'sqrt'])}({e()})",
                    lambda: f"round({e()}, {self.pick(['0', '1', '2'])})",
                    lambda: f"coalesce({e()}, 0)",
                    lambda: f"nullif({e()}, 0)",
                    lambda: f"{self.pick(['greatest', 'least'])}({e()}, {e()})",
                    lambda: f"power({e()}, 2)",
                    lambda: f"length({e('text')})",
                    lambda: f"strpos({e('text')}, 'a')",
                    lambda: (
                        f"CAST({e()} AS {self.pick(['bigint', 'integer', 'numeric(10, 2)', 'double precision', 'smallint'])})"
                    ),
                    lambda: f"{e()}::{self.pick(['bigint', 'numeric', 'integer'])}",
                    lambda: f"CASE WHEN {self.boolean(scope, d + 1)} THEN {e()} ELSE {e()} END",
                    lambda: (
                        f"extract({self.pick(['year', 'month', 'day', 'epoch'])} FROM {e('date')})"
                    ),
                    lambda: f"date_part('month', {e('date')})",
                    lambda: f"({self.scalar_sub('num', d + 1)})",
                    lambda: f"({e()} % 7)",
                    lambda: f"(-{e()})",
                ]
            )()
        if kind == "date":
            return self.pick(
                [
                    lambda: f"date_trunc('{self.pick(['month', 'year', 'week'])}', {e()})",
                    lambda: (
                        f"({e()} + INTERVAL '{self.pick(['7 days', '1 month', '2 weeks', '1 year'])}')"
                    ),
                    lambda: f"({e()} - INTERVAL '3 days')",
                    lambda: f"CAST({e()} AS DATE)",
                    lambda: f"({e()} AT TIME ZONE 'UTC')",
                ]
            )()
        return self.pick(
            [
                lambda: f"lower({e()})",
                lambda: f"upper({e()})",
                lambda: f"{self.pick(['trim', 'ltrim', 'rtrim'])}({e()})",
                lambda: f"({e()} || {e()})",
                lambda: f"concat({e()}, {e()})",
                lambda: f"substring({e()}, 1, 3)",
                lambda: f"substring({e()} FROM 2)",
                lambda: f"{self.pick(['left', 'right'])}({e()}, 2)",
                lambda: f"replace({e()}, 'a', 'b')",
                lambda: f"coalesce({e()}, 'none')",
                lambda: f"CAST({e('num')} AS text)",
                lambda: f"to_char({e('date')}, 'YYYY-MM')",
                lambda: f"CASE WHEN {self.boolean(scope, d + 1)} THEN {e()} ELSE {e()} END",
                lambda: f"({self.scalar_sub('text', d + 1)})",
            ]
        )()

    def boolean(self, scope, d=0):
        if d > 3:
            return "true"
        k = self.pick(["num", "num", "text", "date"])
        a = self.expr(scope, k, d + 1)
        return self.pick(
            [
                lambda: (
                    f"{a} {self.pick(['=', '<>', '<', '>', '<=', '>=', '!='])} {self.expr(scope, k, d + 1)}"
                ),
                lambda: f"{a} IS {self.pick(['NULL', 'NOT NULL'])}",
                lambda: f"{a} BETWEEN {self.lit(k)} AND {self.lit(k)}",
                lambda: f"{a} {self.pick(['NOT IN', 'IN'])} ({self.lit(k)}, {self.lit(k)})",
                lambda: f"{a} IN ({self.in_sub(k, d + 1)})",
                lambda: (
                    f"{self.expr(scope, 'text', d + 1)} {self.pick(['LIKE', 'ILIKE', 'NOT LIKE'])} '%a%'"
                ),
                lambda: f"NOT ({self.boolean(scope, d + 1)})",
                lambda: (
                    f"({self.boolean(scope, d + 1)} {self.pick(['AND', 'OR'])} {self.boolean(scope, d + 1)})"
                ),
                lambda: f"EXISTS ({self.in_sub('num', d + 1)})",
                lambda: f"{a} IS DISTINCT FROM {self.expr(scope, k, d + 1)}",
            ]
        )()

    def agg(self, scope):
        return self.pick(
            [
                lambda: "count(*)",
                lambda: f"count(DISTINCT {self.col(scope, self.pick(['num', 'text']))})",
                lambda: f"count({self.col(scope, 'text')})",
                lambda: f"sum({self.expr(scope, 'num', 1)})",
                lambda: f"avg({self.expr(scope, 'num', 1)})",
                lambda: f"round(avg({self.expr(scope, 'num', 1)}), 2)",
                lambda: (
                    f"{self.pick(['min', 'max'])}({self.expr(scope, self.pick(['num', 'text', 'date']), 1)})"
                ),
                lambda: (
                    f"{self.pick(['stddev', 'variance', 'stddev_samp', 'var_samp'])}({self.expr(scope, 'num', 1)})"
                ),
                lambda: f"{self.pick(['bool_and', 'bool_or'])}({self.boolean(scope, 2)})",
                lambda: f"percentile_cont(0.5) WITHIN GROUP (ORDER BY {self.col(scope, 'num')})",
                lambda: f"count(*) FILTER (WHERE {self.boolean(scope, 2)})",
                lambda: f"sum({self.col(scope, 'num')}) FILTER (WHERE {self.boolean(scope, 2)})",
            ]
        )()

    def window(self, scope):
        part = f"PARTITION BY {self.col(scope, 'text')} " if self.chance(0.5) else ""
        order = f"ORDER BY {self.col(scope, self.pick(['num', 'date']))}{self.pick(['', ' DESC', ' ASC'])}"
        fn = self.pick(
            [
                lambda: self.pick(["row_number()", "rank()", "dense_rank()"]),
                lambda: f"ntile({self.pick(['2', '4'])})",
                lambda: f"{self.pick(['lag', 'lead'])}({self.col(scope, 'num')})",
                lambda: f"{self.pick(['first_value', 'last_value'])}({self.col(scope, 'num')})",
                lambda: f"sum({self.col(scope, 'num')})",
            ]
        )()
        return f"{fn} OVER ({part}{order})"

    # ---- queries
    def scalar_sub(self, kind, d):
        v = self.view()
        scope = [v]
        fn = (
            self.pick(["max", "min"])
            if kind != "num"
            else self.pick(["max", "min", "sum", "avg", "count"])
        )
        return f"SELECT {fn}({self.col(scope, kind)}) FROM {v[0]} {v[1]}" + self.where(scope, d + 1)

    def in_sub(self, kind, d):
        v = self.view()
        return f"SELECT {self.col([v], kind)} FROM {v[0]} {v[1]}" + self.where([v], d + 1)

    def where(self, scope, d=0):
        return f" WHERE {self.boolean(scope, d + 1)}" if self.chance(0.5) else ""

    def sources(self, ctes, d):
        """FROM clause: first source plus 0-2 joins. Returns (sql, scope)."""
        pool = [("view",)] * 4 + ([("cte",)] * 3 if ctes else []) + ([("sub",)] if d < 2 else [])
        scope, sql = [], ""
        for i in range(self.pick([1, 1, 1, 1, 2, 2, 3]) if d < 3 else 1):
            what = self.pick(pool)[0]
            if what == "cte":
                name, cols = self.pick(ctes)
                self.n += 1
                src = (name, f"t{self.n}", cols)
            elif what == "sub":
                body, cols = self.select(None, ctes, d + 1, plain=True)
                self.n += 1
                src = (f"({body})", f"t{self.n}", cols)
            else:
                src = self.view()
            text = f"{src[0]} {src[1]}" if self.chance(0.9) else f"{src[0]} AS {src[1]}"
            if i == 0:
                sql += text
            else:
                kind = self.pick(
                    ["JOIN", "JOIN", "LEFT JOIN", "INNER JOIN", "RIGHT JOIN", "FULL JOIN"]
                )
                shared = self.shared(scope, src)
                if shared and self.chance(0.25):
                    sql += f" JOIN {text} USING ({shared})"
                else:
                    a, b = self.pair(scope, src)
                    sql += f" {kind} {text} ON {a} = {b}"
            scope.append(src)
        return sql, scope

    def pair(self, scope, src):
        """Two qualified columns of the same kind, one from an earlier source and one from the new one."""
        for kind in self.r.sample(["num", "text", "date"], 3):
            lefts = [(a, c) for _, a, cols in scope for c, k in cols.items() if k == kind]
            rights = [c for c, k in src[2].items() if k == kind]
            if lefts and rights:
                la, lc = self.pick(lefts)
                return f"{la}.{lc}", f"{src[1]}.{self.pick(rights)}"
        return f"{scope[0][1]}.{next(iter(scope[0][2]))}", f"{src[1]}.{next(iter(src[2]))}"

    def shared(self, scope, src):
        """A column name that exactly one earlier source has and the new source has too (so USING is unambiguous)."""
        names = [c for c in src[2] if sum(c in sc[2] for sc in scope) == 1]
        return self.pick(names) if names else None

    def select(self, kinds, ctes, d, plain=False, tail=True):
        """One SELECT. Returns (sql, {out_col: kind}). Output columns are aliased c0.. when `plain`."""
        from_sql, scope = self.sources(ctes, d)
        mode = self.pick(["rows", "rows", "agg", "agg", "window"])
        n = len(kinds) if kinds else self.pick([1, 2, 3])
        want = kinds or [self.pick(["num", "num", "text", "date"]) for _ in range(n)]
        items, out, group = [], {}, []
        for i, k in enumerate(want):
            if mode == "agg" and (i > 0 or n == 1) and k == "num":
                e = self.agg(scope)
            elif mode == "agg":
                e = self.col(scope, k)
                group.append(e)
            elif mode == "window" and k == "num" and i > 0:
                e = self.window(scope)
            else:
                e = self.expr(scope, k)
            items.append(f"{e} AS c{i}" if plain or kinds or self.chance(0.6) else e)
            out[f"c{i}"] = k
        if mode == "agg" and not group and any(not _is_agg(x) for x in items):
            mode = "rows"
        distinct = "DISTINCT " if mode == "rows" and self.chance(0.12) else ""
        sql = f"SELECT {distinct}{', '.join(items)} FROM {from_sql}"
        if self.chance(0.55):
            sql += f" WHERE {self.boolean(scope)}"
        if mode == "agg" and group:
            sql += " GROUP BY " + ", ".join(group)
            if self.chance(0.3):
                sql += f" HAVING {self.agg(scope)} > 1"
        elif mode == "agg" and not group:
            pass
        if tail and not plain and not kinds:
            if mode == "rows" and self.chance(0.4):
                sql += f" ORDER BY {self.pick(['1', self.col(scope, 'num')])} {self.pick(['', 'DESC', 'ASC'])}"
            if self.chance(0.4):
                sql += f" LIMIT {self.pick(['1', '5', '100'])}" + (
                    f" OFFSET {self.pick(['0', '3'])}" if self.chance(0.3) else ""
                )
        return sql, out

    def query(self, d=0):
        ctes, prefix = [], ""
        if self.chance(0.2):
            parts = []
            for i in range(self.pick([1, 2, 3])):
                body, cols = self.select(None, ctes, 1, plain=True)
                name = f"cte{i}"
                parts.append(f"{name} AS ({body})")
                ctes = [*ctes, (name, cols)]
            prefix = "WITH " + ", ".join(parts) + " "
        setop = self.chance(0.2)
        body, out = self.select(None, ctes, d, tail=not setop)
        if setop:
            right, _ = self.select(list(out.values()), ctes, d + 1, tail=False)
            body = f"{body} {self.pick(['UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT'])} {right}"
        return prefix + body


def _is_agg(item: str) -> bool:
    return bool(
        re.match(
            r"\s*\(?(count|sum|avg|round\(avg|min|max|stddev|variance|bool_|percentile)",
            item,
            re.IGNORECASE,
        )
    )


def render(rng: random.Random, tokens: list[str], poison: str | None = None) -> str:
    """Join tokens with odd separators and random keyword case; drop `poison` in at a token boundary."""
    out = []
    for t in tokens:
        if t[0] not in "'\"" and t.isalpha() and rng.random() < 0.25:
            t = t.upper() if rng.random() < 0.5 else t.lower()
        out.append(t)
    if poison is not None:
        out.insert(rng.randrange(len(out) + 1), poison)
    text = ""
    for t in out:
        text += t + rng.choice(SEPARATORS)
    return text.rstrip(" ") + (";" if rng.random() < 0.1 else "")


def mutate(rng: random.Random, tokens: list[str]) -> list[str]:
    toks = list(tokens)
    for _ in range(rng.choice([1, 1, 2, 3])):
        i = rng.randrange(len(toks))
        op = rng.choice(["delete", "dup", "swap", "replace", "insert"])
        if op == "delete":
            del toks[i]
        elif op == "dup":
            toks.insert(i, toks[i])
        elif op == "swap" and i + 1 < len(toks):
            toks[i], toks[i + 1] = toks[i + 1], toks[i]
        elif op == "replace":
            toks[i] = rng.choice(HOSTILE)
        else:
            toks.insert(i, rng.choice(HOSTILE))
        if not toks:
            toks = ["SELECT"]
    return toks


# (slot, text, rule): a hazard placed where the grammar allows it, so ONLY that hazard can be the reason for refusal.
SLOT_POISON = [
    ("select", ", email", "V05"), ("select", ", customers_v", "V05"), ("select", ", pg_sleep(1)", "V06"),
    ("select", ", version()", "V06"), ("select", ", current_setting('x')", "V06"), ("select", ", now()", "V06"),
    ("select", ", random()", "V06"), ("select", ", current_user", "V06"), ("select", ", repeat('x', 9)", "V06"),
    ("select", ", set_config('a', 'b', false)", "V06"), ("select", ", lo_import('x')", "V06"),
    ("select", ", pg_catalog.pg_sleep(1)", "V06"), ("select", ", query_to_xml('select 1', true, true, '')", "V06"),
    ("select", ", 1::regclass", "V07"), ("select", ", 'x'::oid", "V07"), ("select", ", 'x'::xml", "V07"),
    ("select", ", CAST(1 AS regproc)", "V07"), ("select", ", 'a' ~ 'b'", "V10"), ("select", ", '{}' -> 'a'", "V10"),
    ("select", ", 1 OPERATOR(+) 1", "V10"), ("select", ", (1 AS x)", "V10"), ("select", ", $1", "V09"),
    ("select", ", %s", "V09"), ("select", ", $$x$$", "V09"), ("select", ", E'x'", "V09"), ("select", ", U&'x'", "V09"),
    ("select", ", " + BACKSLASH, "V09"), ("select", ", " + chr(0), "V09"), ("select", ", " + chr(0x0456), "V09"),
    ("select", ", ROW(1, 2)", "V06"), ("select", ", ARRAY[1]", "V06"), ("select", ", to_json(1)", "V06"),
    ("into", "INTO scratch_t", "V03"),
    ("join", "JOIN pg_shadow zz USING (customer_id)", "V04"),
    ("join", "JOIN shop.customers zz USING (customer_id)", "V04"),
    ("join", "JOIN information_schema.tables zz USING (customer_id)", "V04"),
    ("join", "JOIN generate_series(1, 3) zz USING (customer_id)", "V04"),
    ("join", "JOIN analytics.orders_v zz TABLESAMPLE SYSTEM (1) USING (customer_id)", "V04"),
    ("join", "CROSS JOIN analytics.orders_v zz", "V08"), ("join", ", analytics.orders_v zz", "V08"),
    ("join", "NATURAL JOIN analytics.orders_v zz", "V08"), ("join", "JOIN analytics.orders_v zz ON true", "V08"),
    ("tail", "FOR UPDATE", "V03"), ("tail", "FOR SHARE", "V03"), ("tail", "FOR NO KEY UPDATE NOWAIT", "V03"),
]  # fmt: skip
_JOIN_STOP = {
    "WHERE",
    "GROUP",
    "HAVING",
    "ORDER",
    "LIMIT",
    "OFFSET",
    "UNION",
    "INTERSECT",
    "EXCEPT",
}


def place(tokens: list[str], slot: str, text: str) -> list[str] | None:
    """Insert `text` as one token at the grammar slot of the TOP-LEVEL select; None if the shape has no such slot."""
    depth, sel, frm, ops = 0, None, None, False
    for i, t in enumerate(tokens):
        u = t.upper()
        depth += t == "("
        depth -= t == ")"
        if depth == 0 and u == "SELECT" and sel is None:
            sel = i
        elif depth == 0 and sel is not None and u == "FROM" and frm is None:
            frm = i
        elif depth == 0 and u in ("UNION", "INTERSECT", "EXCEPT"):
            ops = True
    if frm is None:
        return None
    out = list(tokens)
    if slot in ("select", "into"):
        out.insert(frm, text)
    elif slot == "tail":
        if ops:
            return None
        out.append(text)
    else:  # join: right after the FROM list, before WHERE / GROUP BY / ORDER BY / LIMIT / a set operation
        end, depth = len(out), 0
        for i in range(frm + 1, len(out)):
            depth += out[i] == "("
            depth -= out[i] == ")"
            if depth < 0 or depth == 0 and out[i].upper() in _JOIN_STOP:
                end = i
                break
        out.insert(end, text)
    return out


def case(rng: random.Random) -> tuple[str, str, tuple[str, str] | None]:
    """(kind, sql, extra). For kind 'slot', extra is (base sql that is clean, rule the hazard must be refused with)."""
    g = Gen(rng)
    tokens = TOKEN.findall(g.query())
    roll = rng.random()
    if roll < 0.40:
        return "clean", render(rng, tokens), None
    if roll < 0.52:
        return "poisoned", render(rng, tokens, rng.choice(POISON)), None
    if roll < 0.72:
        slot, text, rule = rng.choice(SLOT_POISON)
        placed = place(tokens, slot, text)
        if placed is not None:
            seed = (
                rng.random()
            )  # the same casing and spacing for base and hazard: only the hazard differs
            base = render(random.Random(seed), tokens)
            return "slot", render(random.Random(seed), placed), (base, rule)
    return "mutated", render(rng, mutate(rng, tokens)), None
