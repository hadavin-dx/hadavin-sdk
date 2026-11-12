"""The oracle of ticket P3a-2 (section 7.2), tested on its own (commit 2 of 6). The generated matrix of cases comes in
commit 5; this file holds only what the oracle needs to be trusted first:

- the oracle shares nothing with the code under test;
- the hand-written grant map equals `GRANTS`;
- the oracle sees every effect when it is applied raw (the sensitivity control: an effect the oracle cannot see fails
  the suite, it does not count as covered);
- a session guard for the server-wide things a killed run can leave behind (tablespaces, parameter rights, roles,
  databases with the test prefix).

Every case runs in its own database `hadavin_test_m<pid>_<n>`; its roles carry the same prefix. Server-wide effects (a
tablespace, a parameter right) hold an exclusive advisory lock, so no other case runs while they exist."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from tests.fixtures.dsn_skip import require_module

psycopg = require_module("psycopg")  # with the DSN set a missing driver FAILS (never a skip)
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.store.migrate import GRANTS
from tests.fixtures.oracle import SCRATCH, Oracle

DSN = os.environ.get("HADAVIN_TEST_PG_DSN")
needs_pg = pytest.mark.skipif(
    not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
)

ROOT = Path(__file__).resolve().parent.parent
PREFIX = f"hadavin_test_m{os.getpid()}_"
_LOCK_KEY = 7_302_613_001  # the server-wide lock of the matrix: shared by every case, exclusive for server-wide effects
_COUNTER = [0]
_ROLE_RE = r"^hadavin_test_m[0-9]+_"
_DB_RE = r"^hadavin_test_m[0-9]+_[0-9]+$"


# --- 1. repository checks (no server) ---------------------------------------------------------------------------------

_FORBIDDEN = re.compile(
    r"\b(acl|aclexplode|aclitem|acldefault|relacl|attacl|proacl|nspacl|typacl|datacl|fdwacl|srvacl|lanacl|lomacl|"
    r"paracl|spcacl|defaclacl|initprivs|pg_auth_members|pg_shdepend|pg_default_acl|pg_has_role|has_\w+_privilege)\b"
)


def test_the_oracle_shares_nothing_with_the_code_under_test():
    text = (ROOT / "tests" / "fixtures" / "oracle.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+hadavin_sdk\b", text, re.MULTILINE)
    assert "hadavin_sdk" not in re.sub(r'"""[\s\S]*?"""', "", text, count=1).replace(
        "hadavin_sdk`", ""
    ).replace("`hadavin_sdk", "")
    assert _FORBIDDEN.findall(text) == []


def test_the_forbidden_words_check_catches_each_word():
    """The check above is only as good as its pattern: each word it forbids is caught, a harmless text is not."""
    for word in (
        "relacl",
        "aclexplode",
        "pg_auth_members",
        "pg_default_acl",
        "has_table_privilege",
        "has_schema_privilege",
        "pg_has_role",
        "initprivs",
    ):
        assert _FORBIDDEN.search("use " + word + " here")
    assert not _FORBIDDEN.search("the oracle tries a statement; Oracle; privileges (plain word)")


# The grant map written by hand, as (relation, right) pairs per role. It is NOT computed from `GRANTS`.
HAND_TABLE_RIGHTS = {
    "runtime": {
        ("runs", "SELECT"),
        ("runs", "INSERT"),
        ("runs", "UPDATE"),
        ("plans", "SELECT"),
        ("plans", "INSERT"),
        ("plans", "UPDATE"),
        ("gate_decisions", "SELECT"),
        ("gate_decisions", "INSERT"),
        ("approval_requests", "SELECT"),
        ("approval_requests", "INSERT"),
        ("approval_requests", "UPDATE"),
        ("approval_decisions", "SELECT"),
        ("approval_decisions", "INSERT"),
        ("dead_letters", "SELECT"),
        ("dead_letters", "INSERT"),
        ("spend", "SELECT"),
        ("spend", "INSERT"),
        ("spend", "UPDATE"),
        ("spend_month", "SELECT"),
        ("spend_month", "INSERT"),
        ("spend_month", "UPDATE"),
        ("kill_switch", "SELECT"),
        ("kill_switch", "INSERT"),
        ("kill_switch", "UPDATE"),
        ("tick_state", "SELECT"),
        ("tick_state", "INSERT"),
        ("tick_state", "UPDATE"),
        ("audit_entries", "SELECT"),
        ("audit_entries", "INSERT"),
        ("audit_checkpoints", "SELECT"),
        ("audit_checkpoints", "INSERT"),
        ("audit_outbox", "SELECT"),
        ("audit_outbox", "INSERT"),
        ("audit_outbox", "DELETE"),
        ("tool_calls", "SELECT"),
        ("tool_calls", "INSERT"),
        ("redaction_maps", "SELECT"),
        ("redaction_maps", "INSERT"),
        ("redaction_maps", "UPDATE"),
        ("approval_decisions_seq_seq", "USAGE"),
        ("dead_letters_seq_seq", "USAGE"),
    },
    "portal": {
        (name, "SELECT")
        for name in (
            "runs",
            "plans",
            "gate_decisions",
            "approval_requests",
            "approval_decisions",
            "audit_entries",
            "audit_checkpoints",
        )
    },
    "purge": {("tool_calls", "DELETE"), ("redaction_maps", "DELETE")},
}
HAND_PURGE_COLUMNS = {
    ("runs", "run_id"),
    ("runs", "state"),
    ("runs", "updated_at"),
    ("tool_calls", "call_id"),
    ("tool_calls", "run_id"),
    ("tool_calls", "created_at"),
    ("redaction_maps", "run_id"),
    ("redaction_maps", "updated_at"),
}


def _from_grants() -> tuple[dict[str, set], set]:
    runtime, portal, purge, cols = set(), set(), set(), set()
    for name, g in GRANTS.items():
        for right in (r.strip() for r in g.runtime.split(",") if r.strip()):
            runtime.add((name, right))
        if g.portal:
            portal.add((name, "SELECT"))
        for right in (r.strip() for r in g.purge.split(",") if r.strip()):
            purge.add((name, right))
        for col in g.purge_cols:
            cols.add((name, col))
    return {"runtime": runtime, "portal": portal, "purge": purge}, cols


def test_the_hand_written_map_equals_grants():
    """A change to `GRANTS` must touch this table too: the oracle's expected set is the hand table, not the code's map."""
    rights, cols = _from_grants()
    assert rights == HAND_TABLE_RIGHTS
    assert cols == HAND_PURGE_COLUMNS


def test_the_hand_map_check_fails_when_the_hand_table_is_wrong():
    rights, _ = _from_grants()
    wrong = {k: set(v) for k, v in HAND_TABLE_RIGHTS.items()}
    wrong["runtime"].add(("runs", "DELETE"))
    assert rights != wrong


# --- 2. a case: its own database and roles ----------------------------------------------------------------------------


def _leftovers(admin) -> list[str]:
    """What an earlier killed run left on the server, each with the statement that cleans it."""
    out: list[str] = []
    for (name,) in admin.execute(
        "SELECT spcname FROM pg_catalog.pg_tablespace WHERE spcname ~ '^hadavin_test_'"
    ):
        out.append(f"DROP TABLESPACE {name};")
    for (name,) in admin.execute(
        "SELECT datname FROM pg_catalog.pg_database WHERE datname ~ %s", (_DB_RE,)
    ):
        out.append(f"DROP DATABASE {name} WITH (FORCE);")
    for (param,) in admin.execute(
        "SELECT DISTINCT p.parname FROM pg_catalog.pg_parameter_acl p WHERE p.paracl IS NOT NULL "
        "AND p.paracl::text ~ %s",
        ("(^\\{|,)(=|hadavin_test_m[0-9]+_)",),
    ):
        out.append(f"REVOKE SET ON PARAMETER {param} FROM PUBLIC;  -- and from the test roles")
    for (name,) in admin.execute(
        "SELECT rolname FROM pg_catalog.pg_roles WHERE rolname ~ %s", (_ROLE_RE,)
    ):
        out.append(f"DROP ROLE {name};")
    return out


def _guard(admin, when: str) -> None:
    left = _leftovers(admin)
    if left:
        pytest.fail(
            f"the server holds test leftovers at the {when} of the session; clean them first:\n"
            + "\n".join(left),
            pytrace=False,
        )


@pytest.fixture(scope="session", autouse=True)
def cluster_leftover_guard():
    if not DSN:
        yield
        return
    admin = psycopg.connect(DSN, autocommit=True)
    try:
        _guard(admin, "start")
        yield
        _guard(admin, "end")
    finally:
        admin.close()


class Case:
    """One database, its roles and the oracle. Roles: n (a named role), f (a fresh role that stands for everyone:
    it holds nothing of its own), t (a third role), g (a group), m (the migration role), o (another role)."""

    def __init__(self, admin_dsn: str) -> None:
        _COUNTER[0] += 1
        self.tag = f"{PREFIX}{_COUNTER[0]}"
        self.db_name = self.tag
        self.role = {k: f"{self.tag}_{k}" for k in "nftgmo"}
        self.admin = psycopg.connect(admin_dsn, autocommit=True)
        self.exclusive = False
        self.tablespaces: list[str] = []
        self.parameters: list[str] = []
        self.db = None
        self.oracle = None
        self._dsn = admin_dsn

    def start(self) -> None:
        row = self.admin.execute(
            "SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = session_user"
        ).fetchone()
        if not row or not row[0]:
            pytest.fail(
                "the oracle needs a superuser login in HADAVIN_TEST_PG_DSN (SET SESSION AUTHORIZATION needs it); "
                "this is a failure, not a skip",
                pytrace=False,
            )
        self.admin.execute("SELECT pg_advisory_lock_shared(%s)", (_LOCK_KEY,))
        for r in self.role.values():
            self.admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(r)))
        self.admin.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(self.db_name))
        )
        self.db = psycopg.connect(make_conninfo(self._dsn, dbname=self.db_name), autocommit=True)
        self.oracle = Oracle(self.db)
        self._baseline()

    def _baseline(self) -> None:
        """Schemas `s` and `s2`, one object of every kind in `s`, and nothing granted: everyone's default rights on
        the database, the language and the type are taken away first, so that an effect on them is visible."""
        run = self.db.execute
        run("CREATE EXTENSION file_fdw")
        run("CREATE SCHEMA s")
        run("CREATE SCHEMA s2")
        run(f"CREATE SCHEMA {SCRATCH}")
        run("CREATE TABLE s.t (a int PRIMARY KEY, b int)")
        run("CREATE VIEW s.v AS SELECT a, b FROM s.t")
        run("CREATE MATERIALIZED VIEW s.m AS SELECT a, b FROM s.t")
        run("CREATE SEQUENCE s.q")
        run("CREATE FUNCTION s.f(int) RETURNS int LANGUAGE sql AS 'SELECT 1'")
        run("CREATE PROCEDURE s.p(int) LANGUAGE sql AS ''")
        run("CREATE TYPE s.typ AS ENUM ('x')")
        run("CREATE SERVER srv FOREIGN DATA WRAPPER file_fdw")
        run("CREATE FOREIGN TABLE s.ft (a int) SERVER srv OPTIONS (filename '/dev/null')")
        run("SELECT pg_catalog.lo_create(70001)")
        run("REVOKE EXECUTE ON FUNCTION s.f(int) FROM PUBLIC")
        run("REVOKE EXECUTE ON PROCEDURE s.p(int) FROM PUBLIC")
        run("REVOKE USAGE ON TYPE s.typ FROM PUBLIC")
        run("REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC")
        run(
            sql.SQL("REVOKE TEMPORARY ON DATABASE {} FROM PUBLIC").format(
                sql.Identifier(self.db_name)
            )
        )
        run("REVOKE ALL ON FOREIGN DATA WRAPPER file_fdw FROM PUBLIC")
        run(
            "GRANT USAGE ON SCHEMA s TO " + self.role["g"]
        )  # the group may reach the schema; it holds no object right

    def facts(self, who: str, **extras):
        res = self.oracle.can(self.role[who], "s", **extras)
        res2 = self.oracle.can(self.role[who], "s2", **extras)
        return res.facts | res2.facts, res.inconclusive + res2.inconclusive

    def close(self) -> None:
        errors: list[str] = []
        try:
            if self.db is not None:
                self.db.close()
            self.admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(self.db_name)
                )
            )
            for param in self.parameters:
                for r in [*self.role.values(), "PUBLIC"]:
                    self.admin.execute(
                        sql.SQL("REVOKE SET ON PARAMETER {} FROM {}").format(
                            sql.Identifier(param), sql.SQL(r)
                        )
                    )
            for ts in self.tablespaces:
                self.admin.execute(
                    sql.SQL("DROP TABLESPACE IF EXISTS {}").format(sql.Identifier(ts))
                )
            for r in self.role.values():
                self.admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                self.admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))
        except psycopg.Error as exc:
            errors.append(str(exc))
        finally:
            self.admin.close()
        if errors:
            pytest.fail("a case could not clean up: " + "; ".join(errors), pytrace=False)


@pytest.fixture
def case():
    c = Case(DSN)
    try:
        c.start()
        yield c
    finally:
        c.close()


# --- 3. every effect, applied raw, must be seen -----------------------------------------------------------------------
# (id, statements as the superuser, probed role key, fact that must appear, extras for the oracle)
# {n} {f} {t} {g} {m} {o} are the role names of the case; {db} is the database.

T_ = "table"
EFFECTS = [
    ("E01-named", ["GRANT SELECT ON s.t TO {n}"], "n", (T_, "s.t", "SELECT")),
    ("E01-everyone", ["GRANT SELECT ON s.t TO PUBLIC"], "f", (T_, "s.t", "SELECT")),
    ("E01-third", ["GRANT SELECT ON s.t TO {t}"], "t", (T_, "s.t", "SELECT")),
    ("E02-insert", ["GRANT INSERT ON s.t TO {n}"], "n", (T_, "s.t", "INSERT")),
    ("E02-update", ["GRANT UPDATE ON s.t TO {n}"], "n", (T_, "s.t", "UPDATE")),
    ("E02-delete", ["GRANT DELETE ON s.t TO {n}"], "n", (T_, "s.t", "DELETE")),
    ("E02-delete-everyone", ["GRANT DELETE ON s.t TO PUBLIC"], "f", (T_, "s.t", "DELETE")),
    (
        "E02-through-group",
        ["GRANT DELETE ON s.t TO {g}", "GRANT {g} TO {n}"],
        "n",
        (T_, "s.t", "DELETE"),
    ),
    ("E03-truncate", ["GRANT TRUNCATE ON s.t TO PUBLIC"], "f", (T_, "s.t", "TRUNCATE")),
    ("E03-references", ["GRANT REFERENCES ON s.t TO PUBLIC"], "f", (T_, "s.t", "REFERENCES")),
    ("E03-trigger", ["GRANT TRIGGER ON s.t TO PUBLIC"], "f", (T_, "s.t", "TRIGGER")),
    (
        "E04-column-select",
        ["GRANT SELECT (a) ON s.t TO PUBLIC"],
        "f",
        ("column", "s.t.a", "SELECT"),
    ),
    ("E05-column-update", ["GRANT UPDATE (b) ON s.t TO {t}"], "t", ("column", "s.t.b", "UPDATE")),
    (
        "E06-sequence-usage",
        ["GRANT USAGE ON SEQUENCE s.q TO {n}"],
        "n",
        ("sequence", "s.q", "USAGE"),
    ),
    (
        "E07-sequence-update",
        ["GRANT UPDATE ON SEQUENCE s.q TO PUBLIC"],
        "f",
        ("sequence", "s.q", "UPDATE"),
    ),
    (
        "E07-sequence-select",
        ["GRANT SELECT ON SEQUENCE s.q TO PUBLIC"],
        "f",
        ("sequence", "s.q", "SELECT"),
    ),
    ("E08-view", ["GRANT SELECT ON s.v TO PUBLIC"], "f", (T_, "s.v", "SELECT")),
    ("E08-matview", ["GRANT SELECT ON s.m TO PUBLIC"], "f", (T_, "s.m", "SELECT")),
    ("E09-foreign-table", ["GRANT SELECT ON s.ft TO PUBLIC"], "f", (T_, "s.ft", "SELECT")),
    (
        "E10-function-named",
        ["GRANT EXECUTE ON FUNCTION s.f(int) TO {n}"],
        "n",
        ("function", "s.f(integer)", "EXECUTE"),
    ),
    (
        "E11-function-everyone",
        ["GRANT EXECUTE ON FUNCTION s.f(int) TO PUBLIC"],
        "f",
        ("function", "s.f(integer)", "EXECUTE"),
    ),
    (
        "E14-procedure",
        ["GRANT EXECUTE ON PROCEDURE s.p(int) TO {n}"],
        "n",
        ("function", "s.p(integer)", "EXECUTE"),
    ),
    ("E15-create-named", ["GRANT CREATE ON SCHEMA s TO {n}"], "n", ("schema", "s", "CREATE")),
    ("E15-create-everyone", ["GRANT CREATE ON SCHEMA s TO PUBLIC"], "f", ("schema", "s", "CREATE")),
    (
        "E16-schema-grant-option",
        ["GRANT USAGE ON SCHEMA s TO {n} WITH GRANT OPTION"],
        "n",
        ("schema", "s", "GRANT OPTION"),
    ),
    (
        "E17-create-other-schema",
        ["GRANT CREATE ON SCHEMA s2 TO {n}"],
        "n",
        ("schema", "s2", "CREATE"),
    ),
    (
        "E18-create-database",
        ["GRANT CREATE ON DATABASE {db} TO {n}"],
        "n",
        ("database", "", "CREATE"),
    ),
    (
        "E18-create-database-everyone",
        ["GRANT CREATE ON DATABASE {db} TO PUBLIC"],
        "f",
        ("database", "", "CREATE"),
    ),
    (
        "E19-temporary",
        ["GRANT TEMPORARY ON DATABASE {db} TO {n}"],
        "n",
        ("database", "", "TEMPORARY"),
    ),
    ("E20-type", ["GRANT USAGE ON TYPE s.typ TO {n}"], "n", ("type", "s.typ", "USAGE")),
    (
        "E21-language",
        ["GRANT USAGE ON LANGUAGE plpgsql TO {n}"],
        "n",
        ("language", "plpgsql", "USAGE"),
    ),
    (
        "E22-large-object-select",
        ["GRANT SELECT ON LARGE OBJECT 70001 TO PUBLIC"],
        "f",
        ("large object", "70001", "SELECT"),
    ),
    (
        "E22-large-object-update",
        ["GRANT SELECT, UPDATE ON LARGE OBJECT 70001 TO {n}"],
        "n",
        ("large object", "70001", "UPDATE"),
    ),
    (
        "E23-foreign-server",
        ["GRANT USAGE ON FOREIGN SERVER srv TO {n}"],
        "n",
        ("foreign server", "srv", "USAGE"),
    ),
    (
        "E23-wrapper",
        ["GRANT USAGE ON FOREIGN DATA WRAPPER file_fdw TO {n}"],
        "n",
        ("foreign data wrapper", "file_fdw", "USAGE"),
    ),
    (
        "E26-map-grant-option",
        ["GRANT SELECT ON s.t TO {n} WITH GRANT OPTION"],
        "n",
        (T_, "s.t", "GRANT OPTION"),
    ),
    ("E28-owner-table", ["ALTER TABLE s.t OWNER TO {n}"], "n", (T_, "s.t", "OWNER")),
    (
        "E29-group-inherit",
        ["GRANT SELECT ON s.t TO {g}", "GRANT {g} TO {n}"],
        "n",
        (T_, "s.t", "SELECT"),
    ),
    (
        "E30-group-set-only",
        ["GRANT SELECT ON s.t TO {g}", "GRANT {g} TO {n} WITH INHERIT FALSE, SET TRUE"],
        "n",
        (T_, "s.t", "SELECT"),
    ),
    ("E31-pg-read-all-data", ["GRANT pg_read_all_data TO {n}"], "n", (T_, "s.t", "SELECT")),
    (
        "E32-flag-via-group",
        ["ALTER ROLE {g} CREATEROLE", "GRANT {g} TO {n}"],
        "n",
        ("role", "{g}", "rolcreaterole"),
    ),
    ("E33-flag-on-named", ["ALTER ROLE {n} CREATEDB"], "n", ("role", "{n}", "rolcreatedb")),
    (
        "E38-grant-option-holder",
        [
            "GRANT USAGE ON SCHEMA s TO {t}",
            "GRANT DELETE ON s.t TO {t} WITH GRANT OPTION",
            "SET SESSION AUTHORIZATION {t}",
            "GRANT DELETE ON s.t TO {n}",
            "RESET SESSION AUTHORIZATION",
        ],
        "n",
        (T_, "s.t", "DELETE"),
    ),
    (
        "E39-membership-by-admin",
        [
            "GRANT SELECT ON s.t TO {g}",
            "GRANT USAGE ON SCHEMA s TO {t}",
            "GRANT {g} TO {t} WITH ADMIN OPTION",
            "SET SESSION AUTHORIZATION {t}",
            "GRANT {g} TO {n}",
            "RESET SESSION AUTHORIZATION",
        ],
        "n",
        (T_, "s.t", "SELECT"),
    ),
]


def _fmt(case: Case, text: str) -> str:
    return text.format(db=case.db_name, **case.role)


def _fact(case: Case, fact: tuple[str, str, str]) -> tuple[str, str, str]:
    return (fact[0], _fmt(case, fact[1]), fact[2])


@needs_pg
@pytest.mark.parametrize("effect", EFFECTS, ids=[e[0] for e in EFFECTS])
def test_the_oracle_sees_every_effect_applied_raw(case, effect):
    """Sensitivity control: the case is judged before and after one raw effect; the new fact must appear after and not
    before, and no attempt may be inconclusive."""
    eid, statements, who, expected = effect
    expected = _fact(case, expected)
    before, inconclusive_before = case.facts(who, servers=["srv"], wrappers=["file_fdw"])
    assert inconclusive_before == [], f"the oracle cannot see this attempt: {inconclusive_before}"
    assert expected not in before, f"{eid}: the fact is already there before the effect"
    for s in statements:
        case.db.execute(_fmt(case, s))
    after, inconclusive_after = case.facts(who, servers=["srv"], wrappers=["file_fdw"])
    assert inconclusive_after == [], f"the oracle cannot see this attempt: {inconclusive_after}"
    assert expected in after, (
        f"{eid}: the oracle does not see the effect; new facts: {sorted(after - before)}"
    )


DEFAULT_RIGHT_EFFECTS = [
    # (id, who sets the default, statement, probed role, fact on the fresh object)
    (
        "E34-named-one-schema",
        "m",
        "ALTER DEFAULT PRIVILEGES FOR ROLE {m} IN SCHEMA s GRANT SELECT ON TABLES TO {n}",
        "n",
        (T_, "s.hadavin_oracle_fresh_t", "SELECT"),
    ),
    (
        "E35-everyone-sequences-all-schemas",
        "m",
        "ALTER DEFAULT PRIVILEGES FOR ROLE {m} GRANT USAGE ON SEQUENCES TO PUBLIC",
        "f",
        ("sequence", "s.hadavin_oracle_fresh_q", "USAGE"),
    ),
    (
        "E36-set-by-another-role",
        "o",
        "ALTER DEFAULT PRIVILEGES FOR ROLE {o} IN SCHEMA s GRANT SELECT ON TABLES TO {n}",
        "n",
        (T_, "s.hadavin_oracle_fresh_t", "SELECT"),
    ),
]


@needs_pg
@pytest.mark.parametrize("effect", DEFAULT_RIGHT_EFFECTS, ids=[e[0] for e in DEFAULT_RIGHT_EFFECTS])
def test_the_oracle_sees_a_default_right_by_making_a_fresh_object(case, effect):
    """Default rights, seen by behaviour only: the oracle makes a fresh object as the role that set the default and
    tries the probed role on it. Before the effect the fresh object gives the probed role nothing."""
    eid, creator, statement, who, expected = effect
    before = case.oracle.can_create_fresh(case.role[creator], case.role[who], "s")
    assert before.inconclusive == []
    assert expected not in before.facts
    case.db.execute(_fmt(case, statement))
    after = case.oracle.can_create_fresh(case.role[creator], case.role[who], "s")
    assert after.inconclusive == []
    assert expected in after.facts, f"{eid}: not seen; facts: {sorted(after.facts)}"


@needs_pg
@pytest.mark.parametrize("kind", ["tablespace", "parameter"])
def test_the_oracle_sees_a_server_wide_right_and_the_case_cleans_up(case, kind):
    """A tablespace and a parameter right belong to the whole server: the case takes the exclusive lock first, makes
    them, and removes them in its cleanup. (The session guard fails the session if one is left.)"""
    case.admin.execute("SELECT pg_advisory_unlock_shared(%s)", (_LOCK_KEY,))
    case.admin.execute("SELECT pg_advisory_lock(%s)", (_LOCK_KEY,))
    if kind == "tablespace":
        ts = f"hadavin_test_ts_{case.tag}"
        case.admin.execute("SET allow_in_place_tablespaces = on")
        case.admin.execute(sql.SQL("CREATE TABLESPACE {} LOCATION ''").format(sql.Identifier(ts)))
        case.tablespaces.append(ts)
        extras = {"tablespaces": [ts]}
        fact = ("tablespace", ts, "CREATE")
        effect = sql.SQL("GRANT CREATE ON TABLESPACE {} TO PUBLIC").format(sql.Identifier(ts))
        who = "f"
    else:
        param = "log_statement"
        case.parameters.append(param)
        extras = {"parameters": [param]}
        fact = ("parameter", param, "SET")
        effect = sql.SQL("GRANT SET ON PARAMETER {} TO {}").format(
            sql.Identifier(param), sql.Identifier(case.role["n"])
        )
        who = "n"
    before, inc = case.facts(who, **extras)
    assert inc == [] and fact not in before
    case.admin.execute(effect)
    after, inc = case.facts(who, **extras)
    assert inc == [], f"the oracle cannot see this attempt: {inc}"
    assert fact in after
    case.admin.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_KEY,))


@needs_pg
def test_a_clean_case_shows_no_right_for_a_fresh_role(case):
    """The control without an effect: a fresh role that nothing was granted to may do nothing on the objects of the
    schema `s` beyond what everyone holds on every server (the baseline); a right on an object of `s` would be a
    mistake of the oracle itself."""
    facts, inconclusive = case.facts("f", servers=["srv"], wrappers=["file_fdw"])
    assert inconclusive == [], f"the oracle cannot see this attempt: {inconclusive}"
    on_objects = {
        f
        for f in facts
        if f[0] in {"table", "sequence", "column", "function", "type", "large object"}
    }
    assert on_objects == set(), sorted(on_objects)
    assert not [f for f in facts if f[0] == "role"]


# --- 4. rights the oracle cannot see by behaviour (measured on PostgreSQL 16.15) --------------------------------------
# `verify` judges these rights like any other; the oracle cannot confirm them, so no generated effect uses them. Each
# row is shown here with the measured answer, so a server that changes it makes this test fail and the row is revisited.


@needs_pg
def test_an_update_right_on_a_large_object_alone_is_not_visible_by_behaviour(case):
    """Writing opens the object for reading as well, so UPDATE without SELECT is refused (42501); the oracle sees UPDATE
    only together with SELECT (effect E22-large-object-update). Measured: `lo_open(oid, INV_WRITE)` as a role that holds
    only UPDATE gives "permission denied for large object"."""
    case.db.execute(_fmt(case, "GRANT UPDATE ON LARGE OBJECT 70001 TO {n}"))
    facts, _ = case.facts("n")
    assert ("large object", "70001", "UPDATE") not in facts


@needs_pg
def test_a_write_to_a_view_that_is_not_updatable_is_inconclusive_for_the_oracle(case):
    """INSERT on a view that is not auto-updatable fails with 55000 before the privilege check, so the oracle can never
    class it: it is "inconclusive" (never "allowed"), which is why the generator does not use it as an effect."""
    case.db.execute("CREATE VIEW s.v2 AS SELECT DISTINCT a FROM s.t")
    case.db.execute(_fmt(case, "GRANT INSERT ON s.v2 TO {n}"))
    kind, detail = case.oracle.attempt(
        case.role["n"],
        "INSERT INTO s.v2 DEFAULT VALUES",
        scaffold=["GRANT USAGE ON SCHEMA s TO " + case.role["n"]],
    )
    assert kind == "inconclusive" and detail.startswith("55000"), (kind, detail)


# --- 6. the outcome-counting matrix through `migrate()` (reduced; the generated matrix is commit 5) ---------------------
# Every cell is one effect, brought by one carrier, with or without role arguments, and judged by the three outcomes of
# ticket 1.3: (i) `migrate` refuses and keeps nothing; (ii) `migrate` returns and reports excess rights (exit 5 through
# the command line: `AppliedNotVerifiedError` here); (iii) `migrate` returns and the database holds no excess right.
# "applied with excess: 0" is the count that must hold for every cell that returns. The tables below are written by hand;
# `test_the_matrix_has_exactly_the_planned_cells` counts them.

# (id, statement, True when the run repairs it by itself if it is given the role arguments)
O_EFFECTS = [
    ("O01-select-other", "GRANT SELECT ON audit_entries TO {other}", False),
    ("O02-select-everyone", "GRANT SELECT ON audit_entries TO PUBLIC", False),
    ("O03-column-other", "GRANT SELECT (seq) ON audit_entries TO {other}", False),
    ("O04-sequence-other", "GRANT USAGE ON SEQUENCE approval_decisions_seq_seq TO {other}", False),
    (
        "O05-function-other",
        "GRANT EXECUTE ON FUNCTION hadavin_audit_append_only() TO {other}",
        False,
    ),
    ("O06-delete-runtime", "GRANT DELETE ON audit_entries TO {rt}", True),
]
O_CARRIERS = ["C1-plain-file", "C2-dynamic-sql", "C12-by-hand-then-migrate"]
O_VARIANTS = ["no-roles", "with-roles"]
O_CONTROLS = ["K-clean-no-roles", "K-clean-with-roles"]


def _cells() -> list[tuple[str, str, str]]:
    return [(e[0], c, v) for e in O_EFFECTS for c in O_CARRIERS for v in O_VARIANTS]


def test_the_matrix_has_exactly_the_planned_cells():
    cells = _cells()
    total = len(cells) + len(O_CONTROLS)
    print(
        f"matrix cells: {len(O_EFFECTS)} effects x {len(O_CARRIERS)} carriers x {len(O_VARIANTS)} variants = "
        f"{len(cells)}; controls {len(O_CONTROLS)}; total {total}"
    )
    assert (len(O_EFFECTS), len(O_CARRIERS), len(O_VARIANTS)) == (6, 3, 2)
    assert len(cells) == 36 and len(set(cells)) == 36
    assert len(O_CONTROLS) == 2 and total == 38
    assert [e[0] for e in O_EFFECTS] == sorted(e[0] for e in O_EFFECTS)


def _kept_nothing(text) -> bool:
    """The refusal says the run kept nothing: at step 2 "Nothing was changed. No file ran.", later "The whole run is
    rolled back"."""
    text = str(text)
    return "Nothing was changed." in text or "The whole run is rolled back" in text


@pytest.fixture
def ocell():
    """(dsn scoped to a fresh empty schema of the shared test database, schema name); the schema is dropped afterwards."""
    if not DSN:
        pytest.skip("HADAVIN_TEST_PG_DSN not set")
    import uuid

    schema = f"hadavin_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield make_conninfo(DSN, options=f"-c search_path={schema}"), schema
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _has(db_role: str, schema: str, table: str, right: str) -> bool:
    with psycopg.connect(DSN, autocommit=True) as db:
        return db.execute(
            "SELECT has_table_privilege(%s, %s, %s)",
            (db_role, f"{schema}.{table}", right),
        ).fetchone()[0]


def _no_excess_rights(schema: str, other: str, rt: str | None) -> list[str]:
    """What is wrong in the schema afterwards, read from the access lists with no help from `verify`: a right for the
    other role or for everyone on the table, the column or the sequence the effects touch, or a right for the runtime
    role that the grant map does not give. [] means "applied with excess: 0"."""
    found: list[str] = []
    with psycopg.connect(DSN, autocommit=True) as db:
        for who in (other, "public"):
            for table in ("audit_entries",):
                for right in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES"):
                    if db.execute(
                        "SELECT has_table_privilege(%s, %s, %s)",
                        (who, f"{schema}.{table}", right),
                    ).fetchone()[0]:
                        found.append(f"{who} {right} on {table}")
            if db.execute(
                "SELECT has_column_privilege(%s, %s, 'seq', 'SELECT')",
                (who, f"{schema}.audit_entries"),
            ).fetchone()[0]:
                found.append(f"{who} SELECT (seq) on audit_entries")
            if db.execute(
                "SELECT has_sequence_privilege(%s, %s, 'USAGE')",
                (who, f"{schema}.approval_decisions_seq_seq"),
            ).fetchone()[0]:
                found.append(f"{who} USAGE on approval_decisions_seq_seq")
            if db.execute(
                "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
                (who, f"{schema}.hadavin_audit_append_only()"),
            ).fetchone()[0]:
                found.append(f"{who} EXECUTE on hadavin_audit_append_only")
        if (
            rt
            and db.execute(
                "SELECT has_table_privilege(%s, %s, 'DELETE')", (rt, f"{schema}.audit_entries")
            ).fetchone()[0]
        ):
            found.append(f"{rt} DELETE on audit_entries")
    return found


@pytest.mark.parametrize("cell", _cells(), ids=["/".join(c) for c in _cells()])
@needs_pg
def test_every_matrix_cell_ends_in_one_of_the_three_outcomes(cell, ocell, monkeypatch, tmp_path):
    """One cell, through `migrate()`. Expected by rule: with no role arguments every effect names a role the run does not
    know, so the result is (i): refused, nothing kept (the carrier by hand is refused before any file: "No file
    ran"). With the role arguments, an effect on the runtime role's own rights is repaired by step 4 and the run
    returns with no excess right (iii). The outcome (ii) must never be the answer to a mistake the run could see."""
    from hadavin_sdk import errors

    # on a head that has no such outcome the class is one nothing raises (the old-head proof of ticket 7.9 relies on this)
    AppliedNotVerifiedError = getattr(errors, "AppliedNotVerifiedError", None) or type(
        "AppliedNotVerifiedError", (Exception,), {}
    )
    ConfigError = errors.ConfigError
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    eid, carrier, variant = cell
    effect = next(e for e in O_EFFECTS if e[0] == eid)
    dsn, schema = ocell
    import uuid

    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    statement = effect[1].format(other=other, rt=rt)
    repaired = effect[2] and variant == "with-roles"
    try:
        if carrier == "C1-plain-file":
            tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": statement + ";\n"})
        elif carrier == "C2-dynamic-sql":
            tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": tp._dynamic(statement)})
        else:
            assert mig.migrate(dsn, **roles) == tp.REAL  # a clean run first
            with mig.connect(dsn) as db:  # then the effect by hand, as the owner of the tables
                db.execute(statement)
        outcome = None
        try:
            applied = mig.migrate(dsn, **roles)
            outcome = "iii" if not _no_excess_rights(schema, other, rt if roles else None) else "ii"
            assert applied is not None
        except AppliedNotVerifiedError:
            outcome = "ii"
        except ConfigError as e:
            outcome = "i"
            assert _kept_nothing(e), str(e)
            if carrier.startswith("C12"):
                assert "No file ran" in str(e), str(e)
        expected = "iii" if repaired else "i"
        assert outcome == expected, f"{cell}: outcome {outcome}, expected {expected}"
        if outcome == "iii":
            assert _no_excess_rights(schema, other, rt) == [], "applied with excess: not 0"
    finally:
        tp._drop_roles(other, rt)


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
def test_the_clean_control_returns_with_no_excess_right(variant, ocell, monkeypatch, tmp_path):
    """The control with no effect: the run goes through and "applied with excess: 0" holds, so a cell that refuses is
    refused because of its effect and not because of the setup."""
    import uuid

    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        assert mig.migrate(dsn, **roles) == tp.REAL
        assert _no_excess_rights(schema, other, rt if roles else None) == []
        assert mig.migrate(dsn, **roles) == []
    finally:
        tp._drop_roles(other, rt)
