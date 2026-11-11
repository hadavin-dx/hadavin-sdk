"""The oracle of ticket P3a-2 (section 7.2): what can a role really DO in a database, found by trying.

The oracle is a separate connection (the test server's superuser) that becomes each probed role with
`SET SESSION AUTHORIZATION` and tries one statement per right. It lists objects by name and kind only. It reads no
access list, no membership table and no catalog of default rights, and it shares no query and no helper with
`hadavin_sdk` (the repository test `test_the_oracle_shares_nothing_with_the_code_under_test` enforces both). That is
the point of it: `verify` reads access lists, the oracle asks the server what happens, so a mistake in how `verify`
reads an access list cannot also be a mistake in the oracle.

How an attempt is classed (7.2, measured on PostgreSQL 16.15):
- no error: allowed;
- 42501: refused;
- the codes the server raises only AFTER the privilege check (23502, 23503, 23505, 23514, and the 0A000 and 42809
  messages in `_AFTER_CHECK`): allowed;
- a GRANT that ends with the warning "no privileges were granted": refused;
- any other code: INCONCLUSIVE, collected in `Result.inconclusive`; the caller fails on it, it is never classed allowed.

Every attempt runs inside a savepoint that is rolled back whatever happens, so the database is the same afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import psycopg
from psycopg import sql

# Codes raised only after the privilege check passed: the right is there, the statement failed for another reason.
_AFTER_CHECK_CODES = {"23502", "23503", "23505", "23514"}
_AFTER_CHECK_TEXTS = (
    "trigger functions can only be called as triggers",
    "cannot truncate a table referenced in a foreign key constraint",
    "cannot insert into foreign table",
    "cannot update foreign table",
    "cannot delete from foreign table",
    "cannot change materialized view",
)
SCRATCH = "hadavin_oracle_scratch"  # the schema where an attempt may create an object (S-b)
_FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls", "rolreplication")

Fact = tuple[str, str, str]  # (kind, name, right), for example ("table", "s.t", "SELECT")


class _Done(Exception):
    """Raised inside an attempt to leave the savepoint (rolled back)."""


@dataclass
class Result:
    """What one role can do. `facts` are the allowed things; `inconclusive` are attempts that could not be classed."""

    facts: set[Fact] = field(default_factory=set)
    inconclusive: list[str] = field(default_factory=list)


def _q(*parts: str) -> sql.Composed:
    return sql.SQL(".").join(sql.Identifier(p) for p in parts)


def _typed_nulls(types: list[str]) -> str:
    return ", ".join(f"NULL::{t}" for t in types)


class Oracle:
    """`db` is a superuser connection in autocommit mode, to the database that is judged."""

    def __init__(self, db) -> None:
        self.db = db
        db.execute("SET lc_messages = 'C'")  # the English texts of `_AFTER_CHECK_TEXTS`
        self._notices: list[str] = []
        db.add_notice_handler(lambda n: self._notices.append(n.message_primary or ""))

    # ---- listing (names and kinds only) -------------------------------------------------------------------------------

    def relations(self, schema: str) -> list[tuple[str, str, list[str]]]:
        """(name, relkind, column names) of every relation of the schema."""
        rows = self.db.execute(
            "SELECT c.relname, c.relkind, "
            "COALESCE((SELECT array_agg(a.attname ORDER BY a.attnum) FROM pg_catalog.pg_attribute a "
            "WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped), '{}') "
            "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','f','S') ORDER BY 1",
            (schema,),
        ).fetchall()
        return [(r[0], r[1], list(r[2])) for r in rows]

    def functions(self, schema: str) -> list[tuple[str, str, list[str]]]:
        """(name, prokind, argument types) of every function or procedure of the schema."""
        rows = self.db.execute(
            "SELECT p.proname, p.prokind, "
            "COALESCE((SELECT array_agg(pg_catalog.format_type(t, NULL) ORDER BY o) "
            "FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY AS u(t, o)), '{}') "
            "FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace "
            "WHERE n.nspname = %s ORDER BY 1, 2",
            (schema,),
        ).fetchall()
        return [(r[0], r[1], list(r[2])) for r in rows]

    def types(self, schema: str) -> list[str]:
        """Names of the standalone types and domains of the schema (row types of relations are left out)."""
        rows = self.db.execute(
            "SELECT t.typname FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace "
            "LEFT JOIN pg_catalog.pg_class c ON c.oid = t.typrelid "
            "WHERE n.nspname = %s AND t.typelem = 0 AND t.typtype IN ('d','e','r','m') "
            "OR (n.nspname = %s AND t.typtype = 'c' AND c.relkind = 'c') ORDER BY 1",
            (schema, schema),
        ).fetchall()
        return [r[0] for r in rows]

    def role_flags(self, role: str) -> list[str]:
        """The names of the five flags the role carries (attributes, not access lists)."""
        row = self.db.execute(
            "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication "
            "FROM pg_catalog.pg_roles WHERE rolname = %s",
            (role,),
        ).fetchone()
        return [f for f, v in zip(_FLAGS, row or (), strict=False) if v]

    # ---- one attempt ----------------------------------------------------------------------------------------------------

    def attempt(
        self,
        role: str,
        statement: str | sql.Composable,
        *,
        scaffold: list[str | sql.Composable] | None = None,
        set_role: str | None = None,
        grant: bool = False,
    ) -> tuple[str, str]:
        """Try `statement` as `role` (after `SET ROLE set_role` when given). Returns (class, detail) where class is
        "allowed", "refused" or "inconclusive". The scaffold statements run first, as the superuser, in the same
        savepoint, and are rolled back with it."""
        self._notices.clear()
        outcome = ("inconclusive", "")
        try:
            with self.db.transaction():
                for s in scaffold or []:
                    self.db.execute(s)
                self.db.execute(
                    sql.SQL("SET SESSION AUTHORIZATION {}").format(sql.Identifier(role))
                )
                try:
                    if set_role is not None:
                        self.db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(set_role)))
                    self.db.execute(statement)
                    if grant and any("no privileges were granted" in n for n in self._notices):
                        outcome = ("refused", "no privileges were granted")
                    else:
                        outcome = ("allowed", "")
                except psycopg.Error as exc:
                    code = exc.sqlstate or ""
                    text = str(exc)
                    if code == "42501":
                        outcome = ("refused", text)
                    elif code in _AFTER_CHECK_CODES or any(t in text for t in _AFTER_CHECK_TEXTS):
                        outcome = ("allowed", text)
                    else:
                        outcome = ("inconclusive", f"{code} {text}")
                raise _Done
        except _Done:
            pass
        return outcome

    # ---- the whole list of attempts for one acting role --------------------------------------------------------------

    def _schema_scaffold(self, schema: str, acting: str) -> list[sql.Composable]:
        return [
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(acting)
            )
        ]

    def _scratch_scaffold(self, acting: str) -> list[sql.Composable]:
        return [
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(SCRATCH), sql.Identifier(acting)
            )
        ]

    def _tries(self, schema: str, acting: str, *, extras: dict | None = None):
        """Yield (fact, statement, scaffold, grant_flag) for everything the acting role may be able to do."""
        extras = extras or {}
        s_a = self._schema_scaffold(schema, acting)
        s_b = self._scratch_scaffold(acting)
        ident = sql.Identifier
        yield (
            ("schema", schema, "USAGE"),
            sql.SQL("DROP TABLE IF EXISTS {}").format(_q(schema, "hadavin_oracle_no_such_name")),
            [],
            False,
        )
        yield (
            ("schema", schema, "CREATE"),
            sql.SQL("CREATE TABLE {} (i int)").format(_q(schema, "hadavin_oracle_new")),
            s_a,
            False,
        )
        yield (
            ("schema", schema, "GRANT OPTION"),
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                ident(schema), ident(extras.get("helper", "public"))
            ),
            [],
            True,
        )
        yield (
            ("database", "", "CREATE"),
            sql.SQL("CREATE SCHEMA hadavin_oracle_new_schema"),
            [],
            False,
        )
        yield (
            ("database", "", "TEMPORARY"),
            sql.SQL("CREATE TEMP TABLE hadavin_oracle_tmp (i int)"),
            [],
            False,
        )
        yield (
            ("language", "plpgsql", "USAGE"),
            sql.SQL("DO $$BEGIN END$$ LANGUAGE plpgsql"),
            [],
            False,
        )
        for name, kind, cols in self.relations(schema):
            rel = _q(schema, name)
            relk = "sequence" if kind == "S" else "table"
            fq = f"{schema}.{name}"
            if kind == "S":
                yield (
                    (relk, fq, "USAGE"),
                    sql.SQL("SELECT pg_catalog.nextval({})").format(sql.Literal(fq)),
                    s_a,
                    False,
                )
                yield (
                    (relk, fq, "UPDATE"),
                    sql.SQL("SELECT pg_catalog.setval({}, 1)").format(sql.Literal(fq)),
                    s_a,
                    False,
                )
                yield (
                    (relk, fq, "SELECT"),
                    sql.SQL("SELECT last_value FROM {}").format(rel),
                    s_a,
                    False,
                )
                continue
            yield (
                (relk, fq, "SELECT"),
                sql.SQL("SELECT * FROM {} LIMIT 0").format(rel),
                s_a,
                False,
            )
            for col in cols:
                yield (
                    ("column", f"{fq}.{col}", "SELECT"),
                    sql.SQL("SELECT {} FROM {} LIMIT 0").format(ident(col), rel),
                    s_a,
                    False,
                )
                if kind in "rpvmf":
                    yield (
                        ("column", f"{fq}.{col}", "INSERT"),
                        sql.SQL("INSERT INTO {} ({}) SELECT NULL WHERE false").format(
                            rel, ident(col)
                        ),
                        s_a,
                        False,
                    )
                    yield (
                        ("column", f"{fq}.{col}", "UPDATE"),
                        sql.SQL("UPDATE {} SET {} = NULL WHERE false").format(rel, ident(col)),
                        s_a,
                        False,
                    )
            if kind in "rpvmf":
                yield (
                    (relk, fq, "DELETE"),
                    sql.SQL("DELETE FROM {} WHERE false").format(rel),
                    s_a,
                    False,
                )
            if kind in "rp":
                yield ((relk, fq, "TRUNCATE"), sql.SQL("TRUNCATE {}").format(rel), s_a, False)
                yield (
                    (relk, fq, "TRIGGER"),
                    sql.SQL(
                        "CREATE TRIGGER hadavin_oracle_trg BEFORE UPDATE ON {} FOR EACH ROW "
                        "EXECUTE FUNCTION pg_catalog.suppress_redundant_updates_trigger()"
                    ).format(rel),
                    s_a,
                    False,
                )
                yield ((relk, fq, "REINDEX"), sql.SQL("REINDEX TABLE {}").format(rel), s_a, False)
            if kind == "m":
                yield ((relk, fq, "REINDEX"), sql.SQL("REINDEX TABLE {}").format(rel), s_a, False)
            if kind in "rp" and cols:
                ref = _q(SCRATCH, "hadavin_oracle_ref")
                yield (
                    (relk, fq, "REFERENCES"),
                    sql.SQL("ALTER TABLE {} ADD FOREIGN KEY (x) REFERENCES {} ({})").format(
                        ref, rel, ident(cols[0])
                    ),
                    [
                        *s_a,
                        *s_b,
                        sql.SQL("CREATE TABLE {} (x int)").format(ref),
                        sql.SQL("ALTER TABLE {} OWNER TO {}").format(ref, ident(acting)),
                    ],
                    False,
                )
            if kind in "rpvmf":
                yield (
                    (relk, fq, "GRANT OPTION"),
                    sql.SQL("GRANT SELECT ON {} TO {}").format(
                        rel, ident(extras.get("helper", "public"))
                    ),
                    s_a,
                    True,
                )
            word = {"v": "VIEW", "m": "MATERIALIZED VIEW", "f": "FOREIGN TABLE"}.get(kind, "TABLE")
            yield (
                (relk, fq, "OWNER"),
                sql.SQL("COMMENT ON {} {} IS NULL").format(sql.SQL(word), rel),
                s_a,
                False,
            )
        for name, prokind, argtypes in self.functions(schema):
            fq = f"{schema}.{name}({', '.join(argtypes)})"
            if prokind == "p":
                stmt = sql.SQL("CALL {}({})").format(
                    _q(schema, name), sql.SQL(_typed_nulls(argtypes))
                )
            elif prokind == "a":
                stmt = sql.SQL("EXPLAIN SELECT {}({}) FROM (VALUES (1)) v(x)").format(
                    _q(schema, name), sql.SQL(_typed_nulls(argtypes))
                )
            else:
                stmt = sql.SQL("EXPLAIN SELECT {}({})").format(
                    _q(schema, name), sql.SQL(_typed_nulls(argtypes))
                )
            yield (("function", fq, "EXECUTE"), stmt, s_a, False)
        for typ in self.types(schema):
            fq = f"{schema}.{typ}"
            yield (
                ("type", fq, "USAGE"),
                sql.SQL("CREATE TABLE {} (c {})").format(
                    _q(SCRATCH, "hadavin_oracle_t"), _q(schema, typ)
                ),
                [*s_a, *s_b],
                False,
            )
        for (oid,) in self.db.execute(
            "SELECT oid FROM pg_catalog.pg_largeobject_metadata ORDER BY 1"
        ).fetchall():
            yield (
                ("large object", str(oid), "SELECT"),
                sql.SQL("SELECT pg_catalog.lo_get({})").format(sql.Literal(oid)),
                [],
                False,
            )
            yield (
                ("large object", str(oid), "UPDATE"),
                sql.SQL(
                    "SELECT pg_catalog.lowrite(pg_catalog.lo_open({}, 393216), '\\x00')"
                ).format(sql.Literal(oid)),
                [],
                False,
            )
        for srv in extras.get("servers", []):
            yield (
                ("foreign server", srv, "USAGE"),
                sql.SQL("CREATE USER MAPPING FOR CURRENT_USER SERVER {}").format(ident(srv)),
                [],
                False,
            )
        for fdw in extras.get("wrappers", []):
            yield (
                ("foreign data wrapper", fdw, "USAGE"),
                sql.SQL("CREATE SERVER hadavin_oracle_srv FOREIGN DATA WRAPPER {}").format(
                    ident(fdw)
                ),
                [],
                False,
            )
        for ts in extras.get("tablespaces", []):
            yield (
                ("tablespace", ts, "CREATE"),
                sql.SQL("CREATE TABLE {} (i int) TABLESPACE {}").format(
                    _q(SCRATCH, "hadavin_oracle_ts"), ident(ts)
                ),
                s_b,
                False,
            )
        for param in extras.get("parameters", []):
            yield (
                ("parameter", param, "SET"),
                sql.SQL("SET LOCAL {} = 'none'").format(ident(param)),
                [],
                False,
            )

    def _reachable(self, role: str) -> list[str]:
        """The roles `role` can `SET ROLE` to (tried, one level; every role of the server, built-in ones included)."""
        names = [
            r[0]
            for r in self.db.execute(
                "SELECT rolname FROM pg_catalog.pg_roles ORDER BY 1"
            ).fetchall()
        ]
        out = []
        for other in names:
            if other == role:
                continue
            kind, _ = self.attempt(role, "SELECT 1", set_role=other)
            if kind == "allowed":
                out.append(other)
        return out

    def can(self, role: str, schema: str, **extras) -> Result:
        """Everything `role` can do on the objects of `schema` (and the database-level rights), tried as the role
        itself and after `SET ROLE` to each role it can switch to. Flags of the role and of each of those roles are
        read from `pg_roles` and listed as ("role", name, "rolsuper") and so on."""
        res = Result()
        acting_roles: list[tuple[str, str | None]] = [(role, None)] + [
            (role, r) for r in self._reachable(role)
        ]
        for _, via in acting_roles:
            acting = via or role
            for flag in self.role_flags(acting):
                res.facts.add(("role", acting, flag))
            for item in self._tries(schema, acting, extras=extras):
                if item is None:
                    continue
                fact, stmt, scaffold, grant = item
                kind, detail = self.attempt(
                    role, stmt, scaffold=scaffold, set_role=via, grant=grant
                )
                if kind == "allowed":
                    res.facts.add(fact)
                elif kind == "inconclusive":
                    res.inconclusive.append(f"{fact}: {detail}")
        self._derive_table_rights(res, schema)
        return res

    def _derive_table_rights(self, res: Result, schema: str) -> None:
        """INSERT and UPDATE of a whole table are seen as "every column can be inserted / updated" (a statement that
        names no column needs SELECT as well, so the column attempts are the clean test)."""
        for name, kind, cols in self.relations(schema):
            if kind == "S" or not cols:
                continue
            for right in ("INSERT", "UPDATE"):
                if all(("column", f"{schema}.{name}.{c}", right) in res.facts for c in cols):
                    res.facts.add(("table", f"{schema}.{name}", right))

    def can_create_fresh(self, creator: str, probed: str, schema: str) -> Result:
        """Default rights, seen by behaviour (E34 to E36): as `creator`, make one fresh table, sequence, function and
        type in `schema`, then try the rights of `probed` on them, all inside one rolled-back savepoint. The facts are
        named by the fixed fresh names, never by catalog reads of default rights."""
        res = Result()
        ident = sql.Identifier
        names = {
            "t": "hadavin_oracle_fresh_t",
            "q": "hadavin_oracle_fresh_q",
            "f": "hadavin_oracle_fresh_f",
        }
        try:
            with self.db.transaction():
                self.db.execute(
                    sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
                        ident(schema), ident(creator)
                    )
                )
                self.db.execute(sql.SQL("SET SESSION AUTHORIZATION {}").format(ident(creator)))
                self.db.execute(
                    sql.SQL("CREATE TABLE {} (a int PRIMARY KEY)").format(_q(schema, names["t"]))
                )
                self.db.execute(sql.SQL("CREATE SEQUENCE {}").format(_q(schema, names["q"])))
                self.db.execute(
                    sql.SQL("CREATE FUNCTION {}() RETURNS int LANGUAGE sql AS 'SELECT 1'").format(
                        _q(schema, names["f"])
                    )
                )
                self.db.execute("RESET SESSION AUTHORIZATION")
                inner = self.can(probed, schema)
                res.facts |= {
                    f
                    for f in inner.facts
                    if names["t"] in f[1] or names["q"] in f[1] or names["f"] in f[1]
                }
                res.inconclusive += inner.inconclusive
                raise _Done
        except _Done:
            pass
        return res
