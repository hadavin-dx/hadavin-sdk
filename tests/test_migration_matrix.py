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
import uuid
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
O_EFFECTS += [
    ("O07-everyone-delete-runs", "GRANT DELETE ON runs TO PUBLIC", False),  # E02, everyone
    ("O08-everyone-truncate-runs", "GRANT TRUNCATE ON runs TO PUBLIC", False),  # E03
    ("O09-everyone-column-select", "GRANT SELECT (seq) ON audit_entries TO PUBLIC", False),  # E04
    ("O10-third-column-update", "GRANT UPDATE (state) ON runs TO {other}", False),  # E05
    (
        "O11-everyone-setval",
        "GRANT UPDATE ON SEQUENCE dead_letters_seq_seq TO PUBLIC",
        False,
    ),  # E07
    ("O12-grant-option", "GRANT SELECT ON runs TO {other} WITH GRANT OPTION", False),  # E26
    ("O13-create-on-schema-other", "GRANT CREATE ON SCHEMA {schema} TO {other}", False),  # E15
    (
        "O14-usage-with-grant-option",
        "GRANT USAGE ON SCHEMA {schema} TO {other} WITH GRANT OPTION",
        False,
    ),  # E16
    ("O15-create-on-schema-everyone", "GRANT CREATE ON SCHEMA {schema} TO PUBLIC", False),  # E15
    (
        "O16-default-right-named",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {other}",
        False,
    ),  # E34
    (
        "O17-default-right-everyone",
        "ALTER DEFAULT PRIVILEGES GRANT USAGE ON SEQUENCES TO PUBLIC",
        False,
    ),  # E35
    ("O18-select-third-tool-calls", "GRANT SELECT ON tool_calls TO {other}", False),  # E37
]
# Batch 3e: effects of objects OUTSIDE the map (a table, a sequence, a view, a function, a procedure, a type that the package
# does not make), made and given away inside one statement text, so that every carrier can bring them. The carriers that
# hide the text from the text rules (C2, C3 as a function, C4, C6, C7) make the object during the run.
O_EFFECTS += [
    (
        "O19-select-on-a-table-outside-the-map-named",
        "CREATE TABLE zz_t (a int); GRANT SELECT ON zz_t TO {rt}",
        False,
    ),  # E01
    (
        "O20-select-on-a-table-outside-the-map-everyone",
        "CREATE TABLE zz_t (a int); GRANT SELECT ON zz_t TO PUBLIC",
        False,
    ),  # E01
    (
        "O21-usage-on-a-sequence-outside-the-map-named",
        "CREATE SEQUENCE zz_q; GRANT USAGE ON SEQUENCE zz_q TO {rt}",
        False,
    ),  # E06
    (
        "O22-select-on-a-view-outside-the-map-everyone",
        "CREATE VIEW zz_v AS SELECT 1 AS a; GRANT SELECT ON zz_v TO PUBLIC",
        False,
    ),  # E08
    (
        "O23-execute-on-a-function-named",
        "CREATE FUNCTION zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'; GRANT EXECUTE ON FUNCTION zz_f() TO {rt}",
        False,
    ),  # E10
    (
        "O24-function-of-the-family-left-callable-by-everyone",
        "CREATE FUNCTION hadavin_zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        False,
    ),  # E11
    (
        "O25-security-definer-function-in-the-schema-of-the-run",
        "CREATE FUNCTION hadavin_zz_d() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
        False,
    ),  # E12
    (
        "O26-execute-on-a-procedure-named",
        "CREATE PROCEDURE zz_p() LANGUAGE sql AS 'SELECT 1'; GRANT EXECUTE ON PROCEDURE zz_p() TO {rt}",
        False,
    ),  # E14
    (
        "O27-usage-on-a-type-named",
        "CREATE TYPE zz_ty AS (a int); GRANT USAGE ON TYPE zz_ty TO {rt}",
        False,
    ),  # E20
    # E22 (batch 4b): a plain role may make a large object of its own and give rights on it, so it is an effect of the
    # run (ticket fact 28), not only a state made by hand; `{lo}` is the number of the large object of this test process
    (
        "O28-select-on-a-large-object-everyone",
        "SELECT lo_create({lo}); GRANT SELECT ON LARGE OBJECT {lo} TO PUBLIC",
        False,
    ),  # E22
    (
        "O29-select-on-a-large-object-named",
        "SELECT lo_create({lo}); GRANT SELECT ON LARGE OBJECT {lo} TO {rt}",
        False,
    ),  # E22
]
LO_NUMBER = (
    3_000_000_000 + os.getpid() % 1_000_000
)  # one large object per test process, unlinked after every cell


def _effect_text(effect: tuple, other: str, rt: str, schema: str) -> str:
    """The statement of an effect for one cell: the single place that fills the names in."""
    return effect[1].format(other=other, rt=rt, schema=schema, lo=LO_NUMBER)


# C10 (ticket 7.4): the object lives in ANOTHER schema that the migration role owns (made by the superuser and handed to the
# plain role; everyone may use it, so the rights are judged and not the schema's USAGE). `{o}` is that schema. Only the
# effects of objects outside the map exist there: a map table lives in the schema of the run only (empty by logic).
C10_STATEMENTS = {
    # O13-O16 (round 15): a right on ANOTHER schema than the schema of the run (`{o}` in place of the schema of the run)
    "O13-create-on-schema-other": "GRANT CREATE ON SCHEMA {o} TO {rt}",
    "O14-usage-with-grant-option": "GRANT USAGE ON SCHEMA {o} TO {rt} WITH GRANT OPTION",
    "O15-create-on-schema-everyone": "GRANT CREATE ON SCHEMA {o} TO PUBLIC",
    "O16-default-right-named": "ALTER DEFAULT PRIVILEGES IN SCHEMA {o} GRANT SELECT ON TABLES TO {rt}",
    "O17-default-right-everyone": "ALTER DEFAULT PRIVILEGES IN SCHEMA {o} GRANT USAGE ON SEQUENCES TO PUBLIC",
    "O19-select-on-a-table-outside-the-map-named": "CREATE TABLE {o}.zz_t (a int); GRANT SELECT ON {o}.zz_t TO {rt}",
    "O20-select-on-a-table-outside-the-map-everyone": "CREATE TABLE {o}.zz_t (a int); GRANT SELECT ON {o}.zz_t TO PUBLIC",
    "O21-usage-on-a-sequence-outside-the-map-named": "CREATE SEQUENCE {o}.zz_q; GRANT USAGE ON SEQUENCE {o}.zz_q TO {rt}",
    "O22-select-on-a-view-outside-the-map-everyone": "CREATE VIEW {o}.zz_v AS SELECT 1 AS a; GRANT SELECT ON {o}.zz_v TO PUBLIC",
    "O23-execute-on-a-function-named": "CREATE FUNCTION {o}.zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'; GRANT EXECUTE ON FUNCTION {o}.zz_f() TO {rt}",
    "O24-function-of-the-family-left-callable-by-everyone": "CREATE FUNCTION {o}.hadavin_zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
    "O25-security-definer-function-in-the-schema-of-the-run": "CREATE FUNCTION {o}.hadavin_zz_d() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
    "O26-execute-on-a-procedure-named": "CREATE PROCEDURE {o}.zz_p() LANGUAGE sql AS 'SELECT 1'; GRANT EXECUTE ON PROCEDURE {o}.zz_p() TO {rt}",
    "O27-usage-on-a-type-named": "CREATE TYPE {o}.zz_ty AS (a int); GRANT USAGE ON TYPE {o}.zz_ty TO {rt}",
}
# Ticket 7.4 decides C10 per effect: a named role is judged in every schema; everyone is judged on kinds where everyone holds
# nothing by default (a table, a view); NOT PROMISED for everyone on an ordinary function of another
# schema (the check of the default execute right looks at the schema of the run only; measured: a SECURITY DEFINER function
# of another schema is found anyway).
C10_NAMED = {
    "O13-create-on-schema-other",
    "O14-usage-with-grant-option",
    "O19-select-on-a-table-outside-the-map-named",
    "O21-usage-on-a-sequence-outside-the-map-named",
    "O23-execute-on-a-function-named",
    "O26-execute-on-a-procedure-named",
    "O27-usage-on-a-type-named",
}
C10_EVERYONE = {
    "O15-create-on-schema-everyone",
    "O17-default-right-everyone",
    "O20-select-on-a-table-outside-the-map-everyone",
    "O22-select-on-a-view-outside-the-map-everyone",
    # measured: a SECURITY DEFINER function in another schema that everyone may execute IS found (E13); the reading query
    # takes every definer function, whatever its schema
    "O25-security-definer-function-in-the-schema-of-the-run",
}
C10_NOT_PROMISED = {"O24-function-of-the-family-left-callable-by-everyone"}

# Carriers whose file text is built from the effect (C1, C2) or whose effect runs inside the run as a trigger, a deferred
# trigger or a rule on the ledger (C4, C6, C7), or is done by hand before the run (C12).
O_CARRIERS = [
    "C1-plain-file",
    "C2-dynamic-sql",
    "C3-sql-function",
    "C4-ledger-trigger",
    "C5-trigger-on-a-map-table",
    "C6-deferred-ledger-trigger",
    "C7-ledger-rule",
    "C10-another-schema",
    "C11-temporary-table-named-like-a-catalog-table",
    "C12-by-hand-then-migrate",
]
O_VARIANTS = ["no-roles", "with-roles"]
O_CONTROLS = ["K-clean-no-roles", "K-clean-with-roles"]


# --- the tables of the matrix (batch 4b): every pair that is not a generated cell is a row with its reason -----------------
# A cell is (effect, carrier, variant). The matrix is every effect x every carrier x both variants, minus the pairs of table 2.
# Table 2: pairs that are empty by logic, one written reason per effect (round 15: the reason is the true one for each effect,
# and the list of effect ids is written out; the count test compares it with the effects that have no C10 statement).
# O13-O16 are built under C10 (a right on another schema, a default right limited to another schema): they are not here.
_MAP_REASON = (
    "the map's own object lives in the schema of the run only; aimed at another schema the same statement fails (measured "
    "on PostgreSQL 16.15: %s), and an equally named object made there by hand is the case of effects O19 to O27"
)
_NO_RELATION = _MAP_REASON % 'ERROR 42P01 relation "<schema>.<name>" does not exist'
_C10_EMPTY_REASONS: dict[str, str] = {
    "O01-select-other": _NO_RELATION,
    "O02-select-everyone": _NO_RELATION,
    "O03-column-other": "a column of a map table: " + _NO_RELATION,
    "O04-sequence-other": "a sequence of the map: " + _NO_RELATION,
    "O05-function-other": "the one function of the map: "
    + _MAP_REASON % "ERROR 42883 function <schema>.<name>() does not exist",
    "O06-delete-runtime": _NO_RELATION,
    "O07-everyone-delete-runs": _NO_RELATION,
    "O08-everyone-truncate-runs": _NO_RELATION,
    "O09-everyone-column-select": "a column of a map table: " + _NO_RELATION,
    "O10-third-column-update": "a column of a map table: " + _NO_RELATION,
    "O11-everyone-setval": "a sequence of the map: " + _NO_RELATION,
    "O12-grant-option": _NO_RELATION,
    "O18-select-third-tool-calls": _NO_RELATION,
    "O28-select-on-a-large-object-everyone": 'a large object has no schema; measured: GRANT ... ON LARGE OBJECT <schema>.<number> is a syntax error at or near "<schema>"',
    "O29-select-on-a-large-object-named": 'a large object has no schema; measured: GRANT ... ON LARGE OBJECT <schema>.<number> is a syntax error at or near "<schema>"',
}
O_EMPTY_BY_LOGIC: dict[tuple[str, str], str] = {
    (eid, "C10-another-schema"): why for eid, why in _C10_EMPTY_REASONS.items()
}


def _cells() -> list[tuple[str, str, str]]:
    return [
        (e[0], c, v)
        for e in O_EFFECTS
        for c in O_CARRIERS
        for v in O_VARIANTS
        if (e[0], c) not in O_EMPTY_BY_LOGIC
    ]


# Table 3: cells whose expected end is "the run returns" (outcome iii) although a right was given. Each row is a promise
# the matrix does NOT make (ticket 1.3), pinned so that a change of the rule shows up as a failing test.
# The key is (effect, carrier or "any", variant or "any").
O_PINNED_RETURNS: dict[tuple[str, str, str], str] = {
    ("O29-select-on-a-large-object-named", "any", "no-roles"): (
        "a right on a large object for a role that no argument names: without role arguments the run judges everyone but "
        "no named role (the same pin as X22n)"
    ),
    ("O24-function-of-the-family-left-callable-by-everyone", "C10-another-schema", "any"): (
        "a function of the package in ANOTHER schema left callable by everyone: the check of the default execute right "
        "looks at the schema of the run only (ticket 7.4, not promised)"
    ),
}


def test_c10_every_effect_with_a_statement_is_in_one_set_or_is_the_one_refused_default_right():
    """The three sets are a partition of the written statements: a statement that is in none of them has no decision in the
    ticket (7.4), and one in two of them is decided twice."""
    assert (
        not (C10_NAMED & C10_EVERYONE)
        and not (C10_NAMED & C10_NOT_PROMISED)
        and not (C10_EVERYONE & C10_NOT_PROMISED)
    )
    decided = C10_NAMED | C10_EVERYONE | C10_NOT_PROMISED
    # O16 (a default right of a named role limited to another schema) is the one statement outside the three sets: its
    # cells end refused in both variants (no pinned return in O_PINNED_RETURNS), so it needs no named/everyone split.
    assert set(C10_STATEMENTS) - decided == {"O16-default-right-named"}
    assert decided <= set(C10_STATEMENTS)


for _eid in sorted(C10_NAMED):
    O_PINNED_RETURNS[(_eid, "C10-another-schema", "no-roles")] = (
        "a right of a named role on an object of another schema, with no role argument: no role is named, so none is "
        "judged (the decision of B5)"
    )


for _eid in ("O13-create-on-schema-other", "O15-create-on-schema-everyone"):
    O_PINNED_RETURNS[(_eid, "C9-login-differs-from-the-role", "any")] = (
        "a right on the schema of the run given by the migration role that owns it: step 4 takes it back (the same grantor "
        "revokes it), so the run returns and the schema's access list is as before (checked in the cell)"
    )


def _pinned_reason(eid: str, carrier: str, variant: str) -> str | None:
    for key in (
        (eid, carrier, variant),
        (eid, "any", variant),
        (eid, carrier, "any"),
        (eid, "any", "any"),
    ):
        if key in O_PINNED_RETURNS:
            return O_PINNED_RETURNS[key]
    return None


def _expected_outcome(eid: str, carrier: str, variant: str) -> str:
    """The one rule that says how a cell ends (used by the cell test, the second-carrier tests and the count test).
    (i) refused and nothing kept; (iii) the run returns with no excess right. Rule: every effect is refused, except the
    pinned rows of table 3 and an effect on the runtime role's own rights, which step 4 repairs when it runs (a deferred
    trigger acts after step 4, so C6 is never repaired)."""
    if carrier == "C1-plain-file" and _step_zero_map()[eid]:
        return "i"  # the text rules stop the plain file before any connection: nothing ran
    if _pinned_reason(eid, carrier, variant):
        return "iii"
    effect = next(e for e in O_EFFECTS if e[0] == eid)
    repaired = effect[2] and variant == "with-roles"
    return "iii" if repaired and carrier != "C6-deferred-ledger-trigger" else "i"


# The text rules (`check_grants`, `check_ledger`) read a plain file before any connection. Which effects a plain file stops
# at step 0 is computed, not written: see `_text_rules_refuse` (a run with the connection patched away; no server needed).
from hadavin_sdk.store import migrate as _mig_at_import

_SHIPPED_FILES = _mig_at_import._migration_files  # taken at import, before any test plants a file


def _text_rules_refuse(statement: str, *_unused) -> bool:
    """True when the text rules refuse the plain file `statement` before any connection. It uses its own patch scope and its
    own folder, so the calling test is not changed (a run with the connection patched away needs no server)."""
    import tempfile

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    class _PassedStepZero(Exception):
        pass

    def _stop(*_a, **_k):
        raise _PassedStepZero

    with pytest.MonkeyPatch.context() as mp, tempfile.TemporaryDirectory() as tmp:
        mp.setattr(
            mig, "_migration_files", _SHIPPED_FILES
        )  # not the files another test has planted
        tp._with_files(mp, Path(tmp), {"0006_effect.sql": statement + ";\n"})
        mp.setattr(mig, "connect", _stop)
        try:
            mig.migrate("host=none")
        except _PassedStepZero:
            return False
        except errors.ConfigError as e:
            assert "migrations are inconsistent" in str(e), str(e)
            return True
    raise AssertionError("migrate neither refused at step 0 nor reached the connection")


def _plain_file_statement(effect: tuple) -> str:
    return _effect_text(
        effect, "hadavin_test_mx_aaaaaaaa", "hadavin_test_mxr_aaaaaaaa", "hadavin_test_schema"
    )


# What the ticket plans (7.3, 7.4) and this matrix does not build, as rows with the reason (nothing is "known and moved on":
# each row names what would be needed). Printed by the count test.
O_SERVER_REFUSED_EFFECTS: dict[str, str] = {
    "E09": "a right on a foreign table or foreign server: the plain role cannot create one (needs a foreign data wrapper owned by an administrator)",
    "E13": "EXECUTE on a function of another owner: the plain role cannot grant on what it does not own",
    "E23 E24 E25": "a tablespace, a parameter, a foreign server: only an administrator can grant on them",
    "E29 E30 E31 E32 E33 E36 E38 E39": "memberships, role flags, a default right set by another role, a right granted by another role: CREATEROLE or another login is needed",
}
# Effects built under carrier C12 only (made by the administrator, then `migrate`): table `X_EFFECTS`.
# Effects whose variant (O) (the plain role owns the database) is built in `test_variant_o_...`; the variants below are not.
O_NOT_BUILT: dict[str, str] = {
    "E21 under variant (C)": "USAGE on a language needs a trusted language that an extension makes; measured: this server has no trusted-language extension (pg_language holds internal, c, sql, plpgsql only), so there is nothing to grant on",
    "E19-E21 under variants (T) and (U)": "the same reason: (T) and (U) need a trusted-language extension",
}
# Where the code is LESS strict than the ticket, said plainly (round 15). Printed by the count test; the real-server cells for
# both values of the switch are `test_o8_a_schema_owned_outside_the_family_at_the_start_is_refused_only_with_the_switch_on`.
O_DEVIATIONS_FROM_THE_TICKET: dict[str, str] = {
    "E28-schema, owner outside the family, at the start of the run (ticket rule O8)": "a schema that a role outside the family owns before the run starts is ACCEPTED while the switch is OFF (the shipped default); the ticket says refuse. ON refuses it and keeps nothing. The choice is the lead's question q-p3a2-o8-schema-owner. A schema owned by a role of the family's group is control K8 (fourth form); a named role that takes the schema over during the run is refused (test_e28_...)",
}
# Table 3 also holds pairs that are not promised in carrier C12, see `X_NOT_PROMISED_BOTH_VARIANTS`.
O_NOT_PROMISED = {
    "E27": "a table owned by a group with a second member: a control, not a promise (control K7)",
    "X01t X11 X12": "a table owned by a role outside the family and a right on it held by a third role (ticket 1.4): not judged; a function of another application callable by everyone (3.4 line 3): not judged; a SECURITY DEFINER function of another application: nobody outside the package may call it, not judged",
}
O_NOT_BUILT_CARRIERS: dict[str, str] = {}
O_NOT_BUILT_CONTROLS: dict[str, str] = {}
# Controls built as their own tests, not as generated cells (each states why in its docstring): K4, K9, the clean control of C9,
# K2, K5, K6, K7, and K8 in its four forms (three refusals and the one that returns). K1 and K10 are counted in
# `O_CONTROLS` and `O_CONTROLS_BUILT` x variants.
OWN_CONTROL_TESTS = {  # test name -> number of controls it holds
    "test_control_k4_a_named_role_with_a_live_temporary_table": 1,
    "test_control_k9_a_run_with_no_pending_file_and_other_role_arguments_changes_nothing": 1,
    "test_c9_control_a_clean_run_under_a_login_that_differs_from_the_role_returns": 1,
    "test_control_k2_the_schema_of_the_run_is_public_with_the_servers_own_access_list": 1,
    "test_control_k5_a_database_owned_by_the_migration_role": 1,
    "test_control_k6_a_database_owned_by_a_group_with_only_the_migration_role_as_member": 1,
    "test_control_k7_a_database_owned_by_a_group_with_a_second_member": 1,
    "test_control_k10_every_relation_kind_with_its_row_type_is_not_an_excess": len(
        O_VARIANTS
    ),  # one per variant
    "test_control_k8_the_hand_over_is_refused_in_three_forms": 3,
    "test_control_k8_fourth_form_the_group_owns_the_schema_of_the_run_and_the_run_returns": 1,
}
CONTROLS_AS_OWN_TESTS = sum(OWN_CONTROL_TESTS.values())


_STEP_ZERO_CACHE: dict[str, bool] = {}


def _step_zero_map() -> dict[str, bool]:
    """effect id -> True when the text rules refuse the plain file of that effect before any connection (computed once, with
    the connection patched away, so no server is needed)."""
    if not _STEP_ZERO_CACHE:
        for effect in O_EFFECTS:
            _STEP_ZERO_CACHE[effect[0]] = _text_rules_refuse(_plain_file_statement(effect))
    return _STEP_ZERO_CACHE


def test_the_matrix_has_exactly_the_planned_cells():
    cells = _cells()
    possible = len(O_EFFECTS) * len(O_CARRIERS) * len(O_VARIANTS)
    empty = len(O_EMPTY_BY_LOGIC) * len(O_VARIANTS)
    step0 = _step_zero_map()
    c1_step0 = [e for e, refused in step0.items() if refused]
    step0_cells = len(c1_step0) * len(
        O_VARIANTS
    )  # only carrier C1 writes the effect in the open (see _WRITTEN_IN_THE_OPEN)
    reach_the_data_checks = len(cells) - step0_cells
    pinned_returns = sum(1 for c in cells if _expected_outcome(*c) == "iii")
    refused = len(cells) - pinned_returns
    # the second-carrier tests, each computed from its own parameter list
    controls = len(O_CONTROLS) + len(O_CONTROLS_BUILT) * len(O_VARIANTS) + CONTROLS_AS_OWN_TESTS
    pre_existing = len(X_EFFECTS) * len(O_VARIANTS)
    total = (
        len(cells)
        + controls
        + len(C6B_CELLS)
        + pre_existing
        + len(C8_CELLS)
        + len(C8_SCHEMA_CELLS)
        + len(C9_CELLS)
        + len(C13_CELLS)
        + len(VARIANT_O_CELLS)
    )
    print(
        f"matrix: {len(O_EFFECTS)} effects x {len(O_CARRIERS)} carriers x {len(O_VARIANTS)} variants = {possible}; "
        f"empty by logic {empty} ({len(O_EMPTY_BY_LOGIC)} pairs x {len(O_VARIANTS)}); generated cells {len(cells)} "
        f"(= {possible} - {empty}); of them ended at step 0 by the text rules, nothing ran: {step0_cells} "
        f"({len(c1_step0)} effects x {len(O_VARIANTS)}, carrier C1 only); reach the data checks: {reach_the_data_checks}; "
        f"expected refused {refused}; expected to return (pinned, table 3) {pinned_returns}"
    )
    print(
        f"other carriers: C6b {len(C6B_CELLS)}; C8 {len(C8_CELLS)} + {len(C8_SCHEMA_CELLS)} (schema as member); C9 {len(C9_CELLS)}; C13 {len(C13_CELLS)}; "
        f"variant (O) {len(VARIANT_O_CELLS)}; "
        f"pre-existing (C12, administrator) {len(X_EFFECTS)} x {len(O_VARIANTS)} = {pre_existing}; controls {controls}; "
        f"compositions {COMPOSITION_COUNT} (seed {COMPOSITION_SEED}); total cells and controls {total}"
    )
    for ids, why in O_SERVER_REFUSED_EFFECTS.items():
        print(f"server refuses it to a plain role (C12 only), effects {ids}: {why}")
    for key, why in O_NOT_BUILT.items():
        print(f"NOT BUILT, {key}: {why}")
    for ids, why in O_DEVIATIONS_FROM_THE_TICKET.items():
        print(f"DEVIATION FROM THE TICKET, {ids}: {why}")
    for ids, why in O_NOT_PROMISED.items():
        print(f"not promised, {ids}: {why}")
    for ids, why in O_NOT_BUILT_CARRIERS.items():
        print(f"NOT BUILT, carrier {ids}: {why}")
    for ids, why in O_NOT_BUILT_CONTROLS.items():
        print(f"NOT BUILT, control {ids}: {why}")
    # the numbers are computed from the tables, so each assert compares two different computations
    assert len(cells) == len(set(cells)) == possible - empty
    # written out, not derived from the table it checks: the effects that are empty at C10 are exactly these, each with a
    # reason, and together with the effects that have a C10 statement they are every effect
    assert set(_C10_EMPTY_REASONS) == {
        "O01-select-other", "O02-select-everyone", "O03-column-other", "O04-sequence-other", "O05-function-other",
        "O06-delete-runtime", "O07-everyone-delete-runs", "O08-everyone-truncate-runs", "O09-everyone-column-select",
        "O10-third-column-update", "O11-everyone-setval", "O12-grant-option",
        "O18-select-third-tool-calls", "O28-select-on-a-large-object-everyone", "O29-select-on-a-large-object-named",
    }  # fmt: skip
    assert set(_C10_EMPTY_REASONS) | set(C10_STATEMENTS) == {e[0] for e in O_EFFECTS}
    assert not set(_C10_EMPTY_REASONS) & set(C10_STATEMENTS)
    assert all(len(why) > 40 for why in _C10_EMPTY_REASONS.values()), (
        "every empty pair needs a written reason"
    )
    assert len(set(_C10_EMPTY_REASONS.values())) > 1, (
        "one reason for every pair is how r15 found a false one"
    )
    assert all(c in O_CARRIERS for _, c in O_EMPTY_BY_LOGIC) and {
        e for e, _ in O_EMPTY_BY_LOGIC
    } <= {e[0] for e in O_EFFECTS}
    assert not set(C10_STATEMENTS) & {e for e, _ in O_EMPTY_BY_LOGIC}
    assert len(C6B_CELLS) == len(O_EFFECTS) * len(O_VARIANTS)
    assert all(len(w) > 40 for w in C8_EMPTY_BY_LOGIC.values()) and all(
        len(w) > 40 for w in C13_EMPTY_BY_LOGIC.values()
    ), "every empty pair of C8 and C13 needs a written reason"
    assert all(name in globals() for name in OWN_CONTROL_TESTS), (
        "a control that the count lists is not defined"
    )
    assert len(C8_CELLS) == len(C8_OBJECT) * len(O_VARIANTS) and len(C9_CELLS) == len(
        O_EFFECTS
    ) * len(O_VARIANTS)
    assert len(C13_CELLS) == (
        len(C13_FORMS) + len(C13_TABLE_EFFECTS) + len(C13_OTHER_MOVES) + len(C13_SCHEMA_EFFECTS) + 1
    ) * len(O_VARIANTS)
    assert len(VARIANT_O_CELLS) == len(VARIANT_O_EFFECTS) * len(VARIANT_O_CARRIERS) * len(
        O_VARIANTS
    )
    # a floor on the cells that really test the data checks: step 0 may stop the plain file only; the other nine carriers
    # hide the effect from the text rules, so at least this share of all cells must reach the checks
    assert reach_the_data_checks >= len(cells) - len(O_EFFECTS) * len(O_VARIANTS), (
        reach_the_data_checks,
        len(cells),
    )
    assert set(c1_step0) <= {e[0] for e in O_EFFECTS}
    assert _WRITTEN_IN_THE_OPEN == ("C1-plain-file",)
    assert [e[0] for e in O_EFFECTS] == sorted(e[0] for e in O_EFFECTS)
    assert len({e[0] for e in O_EFFECTS}) == len(O_EFFECTS)
    # every pinned row names a real effect, carrier and variant
    for eid, carrier, variant in O_PINNED_RETURNS:
        assert (
            eid in {e[0] for e in O_EFFECTS}
            and carrier in [*O_CARRIERS, "C9-login-differs-from-the-role", "any"]
            and variant in [*O_VARIANTS, "any"]
        )
    # no row of the ticket is left out unlisted: the ids built (generated, or pre-existing under C12) plus the ids of the
    # tables cover E01 to E39
    planned = {f"E{n:02d}" for n in range(1, 40)}
    generated = {
        "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E10", "E11", "E12", "E14", "E15", "E16", "E20",
        "E22", "E26", "E34", "E35", "E37",
    }  # fmt: skip
    pre_existing_ids = {e[1] for e in X_EFFECTS}
    listed = {w for key in O_SERVER_REFUSED_EFFECTS for w in key.split()} | {"E27"}
    unaccounted = planned - generated - pre_existing_ids - listed
    # the effects of the (O) variant are built as their own cells, listed here so that nothing is built unlisted
    unaccounted -= {e for _, e, *_ in VARIANT_O_EFFECTS}
    assert unaccounted == set(), sorted(unaccounted)
    assert generated <= planned and pre_existing_ids <= planned
    # table 1 is checked against what the matrix built: an id the server refuses must not also be a generated cell
    assert not {w for key in O_SERVER_REFUSED_EFFECTS for w in key.split()} & generated


def _kept_nothing(text) -> bool:
    """The refusal says the run kept nothing: at step 2 "Nothing was changed. No file ran.", later "The whole run is
    rolled back"."""
    text = str(text)
    return (
        "Nothing was changed." in text
        or "The whole run is rolled back" in text
        or "migrations are inconsistent"
        in text  # step 0: refused by the text rules before it connects, no file ran
    )


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
    """What is wrong in the schema afterwards, read from the access lists with no help from `verify`: any right for the
    other role or for everyone on a table, a column, a sequence, the function or the schema itself (CREATE, or USAGE
    with the grant option), and, for the runtime role, any right the grant map does not give it. [] means "applied with
    excess: 0"."""
    found: list[str] = []
    table_rights = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
    column_rights = ("SELECT", "INSERT", "UPDATE", "REFERENCES")
    with psycopg.connect(DSN, autocommit=True) as db:
        columns: dict[str, list[str]] = {}
        for rel, col in db.execute(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = %s",
            (schema,),
        ).fetchall():
            columns.setdefault(rel, []).append(col)
        for who in (other, "public"):
            for name, g in GRANTS.items():
                if g.kind == "sequence":
                    for right in ("USAGE", "SELECT", "UPDATE"):
                        if db.execute(
                            "SELECT has_sequence_privilege(%s, %s, %s)",
                            (who, f"{schema}.{name}", right),
                        ).fetchone()[0]:
                            found.append(f"{who} {right} on {name}")
                    continue
                for right in table_rights:
                    if db.execute(
                        "SELECT has_table_privilege(%s, %s, %s)", (who, f"{schema}.{name}", right)
                    ).fetchone()[0]:
                        found.append(f"{who} {right} on {name}")
                for col in columns.get(name, []):
                    for right in column_rights:
                        if db.execute(
                            "SELECT has_column_privilege(%s, %s, %s, %s)",
                            (who, f"{schema}.{name}", col, right),
                        ).fetchone()[0]:
                            found.append(f"{who} {right} ({col}) on {name}")
            if db.execute(
                "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
                (who, f"{schema}.hadavin_audit_append_only()"),
            ).fetchone()[0]:
                found.append(f"{who} EXECUTE on hadavin_audit_append_only")
            for right in ("CREATE", "USAGE WITH GRANT OPTION"):
                if db.execute(
                    "SELECT has_schema_privilege(%s, %s, %s)", (who, schema, right)
                ).fetchone()[0]:
                    found.append(f"{who} {right} on the schema")
        if rt:
            for name, g in GRANTS.items():
                if g.kind == "sequence":
                    continue
                wanted = {r.strip() for r in g.runtime.split(",") if r.strip()}
                for right in table_rights:
                    if (
                        right not in wanted
                        and db.execute(
                            "SELECT has_table_privilege(%s, %s, %s)",
                            (rt, f"{schema}.{name}", right),
                        ).fetchone()[0]
                    ):
                        found.append(f"{rt} {right} on {name}")
    return found


_LEDGER_CARRIERS = ("C4-ledger-trigger", "C6-deferred-ledger-trigger", "C7-ledger-rule")


def _split(statement: str) -> str:
    """The statement as an SQL expression of pieces of three characters joined with `||`, so that no word is whole in the
    file text and the text rules (which read words) cannot read it; the server joins the pieces when the function runs."""
    pieces = [statement[i : i + 3] for i in range(0, len(statement), 3)]
    return " || ".join("'" + piece.replace("'", "''") + "'" for piece in pieces)


def _split_function(statement: str) -> str:
    """C2: a function that runs the effect from two string pieces, and the call."""
    return (
        "CREATE OR REPLACE FUNCTION hadavin_test_dyn_runner() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE {_split(statement)}; END $$;\nSELECT hadavin_test_dyn_runner();\n"
    )


# C3: a function whose body is a string of SQL (language sql) runs the effect; the file is the function and the call. The SQL
# function is made by dynamic SQL from pieces of three characters (batch 4b), so the text rules, which read words, cannot read
# the effect and the cell reaches the checks of the data. C11: a temporary table named like a catalog table is made first (the
# run must read the catalogs by their full names), then the effect by dynamic SQL. Only carrier C1 writes the effect in the open.
_WRITTEN_IN_THE_OPEN = ("C1-plain-file",)
# The text rules refuse a temporary table written in the open, so it is made by dynamic SQL with the words split.
_TEMP_LIKE_CATALOG = (
    "CREATE OR REPLACE FUNCTION hadavin_test_mktemp() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
    "EXECUTE 'CRE' || 'ATE TEM' || 'PORARY TAB' || 'LE pg_class (oid int, relname text, relacl text)'; END $$;\n"
    "SELECT hadavin_test_mktemp();\n"
)


def _sql_function(statement: str) -> str:
    """C3: an SQL-language function whose body is the effect; made by dynamic SQL so that no word is whole in the file."""
    body = f"CREATE OR REPLACE FUNCTION hadavin_test_sqlfn() RETURNS void LANGUAGE sql AS $b$ {statement} $b$"
    return (
        "CREATE OR REPLACE FUNCTION hadavin_test_mksql() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE {_split(body)}; "
        # the function is the carrier's own, so it must not be left callable by everyone (that would be a second effect)
        f"EXECUTE {_split('REVOKE ALL ON FUNCTION hadavin_test_sqlfn() FROM PUBLIC')}; END $$;\n"
        "SELECT hadavin_test_mksql();\nSELECT hadavin_test_sqlfn();\n"
    )


def _map_table_trigger_files(statement: str) -> dict[str, str]:
    """C5: file 1 makes a statement-level trigger on the map table `runs` (by dynamic SQL, so the text rules do not read it);
    file 2 is a plain `DELETE FROM runs`, which fires the trigger (a statement trigger fires on zero rows) and so runs the
    effect in a LATER file than the one that made the trigger."""
    text = (
        "CREATE OR REPLACE FUNCTION hadavin_test_eff5() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE {_split(statement)}; RETURN NULL; END $$;\n"
        "CREATE OR REPLACE FUNCTION hadavin_test_mk5() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        "EXECUTE 'CRE' || 'ATE TRIGGER hadavin_test_trg5 AFTER DELETE ON runs FOR EACH STATEMENT "
        "EXECUTE FUNCTION hadavin_test_eff5()'; END $$;\nSELECT hadavin_test_mk5();\n"
    )
    return {"0006_trigger.sql": text, "0007_fire.sql": "DELETE FROM runs;\n"}


def _ledger_file(carrier: str, statement: str, tag: str = "") -> str:
    """A file whose effect runs when the runner writes its own row in the ledger `schema_migrations`: an AFTER INSERT
    trigger (C4), a constraint trigger that is deferred to the end (C6), a rule (C7). The function runs the effect as the
    migration role. The text rules refuse a trigger or a rule written in the open, so the object is made by dynamic SQL
    (the file's own statements are only the function and the call)."""
    if carrier == "C7-ledger-rule":
        make = "CREATE RULE hadavin_test_rule AS ON INSERT TO schema_migrations DO ALSO SELECT hadavin_test_eff()"
        returns, tail = "int", "RETURN 1;"
    else:
        kind = "CONSTRAINT TRIGGER" if carrier.startswith("C6") else "TRIGGER"
        timing = " DEFERRABLE INITIALLY DEFERRED" if carrier.startswith("C6") else ""
        make = (
            f"CREATE {kind} hadavin_test_trg AFTER INSERT ON schema_migrations{timing} FOR EACH ROW "
            "EXECUTE FUNCTION hadavin_test_eff()"
        )
        returns, tail = "trigger", "RETURN NULL;"
    text = (
        f"CREATE OR REPLACE FUNCTION hadavin_test_eff() RETURNS {returns} LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE {_split(statement)}; {tail} END $$;\n"
        # the word is split so that the text rules cannot read it (ticket 7.4, C2)
        "CREATE OR REPLACE FUNCTION hadavin_test_mk() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE 'CRE' || 'ATE {make[7:].replace(chr(39), chr(39) * 2)}'; END $$;\nSELECT hadavin_test_mk();\n"
    )
    for name in ("hadavin_test_eff", "hadavin_test_rule", "hadavin_test_trg", "hadavin_test_mk"):
        text = text.replace(
            name, name + tag
        )  # the names of one file differ from another's in a composition
    return text


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
    statement = _effect_text(effect, other, rt, schema)
    try:
        if carrier == "C1-plain-file":
            tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": statement + ";\n"})
        elif carrier == "C2-dynamic-sql":
            tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": _split_function(statement)})
        elif carrier == "C3-sql-function":
            tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": _sql_function(statement)})
        elif carrier == "C11-temporary-table-named-like-a-catalog-table":
            tp._with_files(
                monkeypatch,
                tmp_path,
                {
                    "0006_temp.sql": _TEMP_LIKE_CATALOG,
                    "0007_effect.sql": _split_function(statement),
                },
            )
        elif carrier == "C10-another-schema":
            from tests.fixtures import migration_role as helper

            other_schema = schema + "_o"
            with psycopg.connect(DSN, autocommit=True) as admin:
                helper.ensure_plain_role(admin)
                admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(other_schema)))
                admin.execute(
                    sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                        sql.Identifier(other_schema), sql.Identifier(helper.PLAIN_ROLE)
                    )
                )
                admin.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(
                        sql.Identifier(other_schema)
                    )
                )
            c10_statement = C10_STATEMENTS[eid].format(
                o=sql.Identifier(other_schema).as_string(), rt=rt
            )
            tp._with_files(
                monkeypatch, tmp_path, {"0006_effect.sql": _split_function(c10_statement)}
            )
        elif carrier == "C5-trigger-on-a-map-table":
            tp._with_files(monkeypatch, tmp_path, _map_table_trigger_files(statement))
        elif carrier in _LEDGER_CARRIERS:
            tp._with_files(
                monkeypatch, tmp_path, {"0006_effect.sql": _ledger_file(carrier, statement)}
            )
        else:
            assert mig.migrate(dsn, **roles) == tp.REAL  # a clean run first
            with mig.connect(dsn) as db:  # then the effect by hand, as the owner of the tables
                db.execute(statement)
        outcome = None
        detail = ""
        try:
            applied = mig.migrate(dsn, **roles)
            outcome = "iii" if not _no_excess_rights(schema, other, rt if roles else None) else "ii"
            assert applied is not None
        except AppliedNotVerifiedError:
            outcome = "ii"
        except ConfigError as e:
            outcome = "i"
            detail = str(e)
            assert _kept_nothing(e), str(e)
            # Only the plain file may be stopped by the text rules at step 0; every other carrier hides its statement from
            # them, so its refusal must come from the checks of the data (else the cell proves nothing about them).
            assert carrier in _WRITTEN_IN_THE_OPEN or "migrations are inconsistent" not in str(e), (
                str(e)
            )
            if (
                carrier == "C1-plain-file"
            ):  # the text rules stop it at step 0 exactly when the static count says so
                assert ("migrations are inconsistent" in str(e)) == _step_zero_map().get(
                    eid, False
                ), (
                    f"{cell}: step 0 {'did' if 'migrations are inconsistent' in str(e) else 'did not'} stop it; "
                    f"the static classification says {_step_zero_map().get(eid)}"
                )
            if carrier.startswith("C12"):
                assert "No file ran" in str(e), str(e)
        expected = _expected_outcome(eid, carrier, variant)
        assert outcome == expected, (
            f"{cell}: outcome {outcome}, expected {expected}; {detail[:600]}"
        )
        if outcome == "iii" and carrier != "C10-another-schema":
            assert _no_excess_rights(schema, other, rt) == [], "applied with excess: not 0"
    finally:
        if carrier == "C10-another-schema":
            with psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema + "_o")
                    )
                )
        _forget_default_rights(dsn)
        tp._drop_roles(other, rt)


@needs_pg
def test_c5_the_trigger_of_a_later_file_really_runs_the_effect(ocell, monkeypatch, tmp_path):
    """Sensitivity of the carrier: the refusal names the other role that the trigger gave a right, so the cells of C5 end in
    (i) because the effect ran in file 2 and was found, and not for another reason."""
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, _schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        tp._with_files(
            monkeypatch,
            tmp_path,
            _map_table_trigger_files(f"GRANT SELECT ON audit_entries TO {other}"),
        )
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn)
        assert other in str(seen.value), str(seen.value)[:400]
    finally:
        tp._drop_roles(other, rt)


# C9 (ticket 7.4): the login differs from the role. The DSN logs in as L and carries `options=-c role=M`, so every statement of
# the run, and the check after the commit, runs as M. Batch 4b: every one of the effects (not two cells) x both variants; each
# ends as `_expected_outcome` says, so the switch does not hide any effect. The login runs the effect by dynamic SQL (C2 form).
C9_CARRIER = "C9-login-differs-from-the-role"
C9_CELLS = [(e[0], v) for e in O_EFFECTS for v in O_VARIANTS]


def _case_names(case: Case) -> dict[str, str]:
    """The role names of a `case` for the effect texts: `other` is the third role, `rt` the named runtime role."""
    return {"other": case.role["o"], "rt": case.role["n"], "schema": APP}


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("effect_id, variant", C9_CELLS, ids=[f"{e}/C9/{v}" for e, v in C9_CELLS])
def test_c9_a_login_that_differs_from_the_role_is_judged_like_the_role(
    effect_id, variant, case, monkeypatch, tmp_path
):
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp
    from tests.fixtures import migration_role as helper

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    _migration_login(case)
    login = "hadavin_test_lg_" + uuid.uuid4().hex[:8]
    case.admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(login)))
    case.admin.execute(
        sql.SQL("GRANT {} TO {}").format(sql.Identifier(case.role["m"]), sql.Identifier(login))
    )
    helper.set_login_password(case.db, login)
    dsn = helper.login_dsn(
        make_conninfo(
            case._dsn,
            dbname=case.db_name,
            options=f"-c search_path={APP} -c role={case.role['m']}",
        ),
        login,
    )
    roles = {"runtime_role": case.role["n"]} if variant == "with-roles" else {}
    expected = _expected_outcome(effect_id, C9_CARRIER, variant)
    try:
        tp._with_files(
            monkeypatch,
            tmp_path,
            {
                "0006_effect.sql": _split_function(
                    effect[1].format(lo=LO_NUMBER, **_case_names(case))
                )
            },
        )
        try:
            mig.migrate(dsn, **roles)
            outcome = "iii"
        except errors.ConfigError as e:
            outcome = "i"
            assert _kept_nothing(e) and "migrations are inconsistent" not in str(e), str(e)[:400]
        assert outcome == expected, (
            f"{effect_id}/C9/{variant}: outcome {outcome}, expected {expected}"
        )
        if outcome == "iii" and effect_id.startswith(
            ("O13", "O15")
        ):  # nothing is left of the right
            left = case.db.execute(
                "SELECT has_schema_privilege(%s, %s, 'CREATE'), has_schema_privilege('public', %s, 'CREATE')",
                (case.role["o"], APP, APP),
            ).fetchone()
            assert left == (False, False), (
                f"{effect_id}/C9/{variant}: the right is still there: {left}"
            )
    finally:
        case.admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(login)))
        case.admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(login)))


@needs_pg
@pytest.mark.real_connect
def test_c9_control_a_clean_run_under_a_login_that_differs_from_the_role_returns(case):
    """The clean control of C9: no effect; the run returns, keeps the switch and a second run has nothing pending."""
    from hadavin_sdk.store import migrate as mig
    from tests.fixtures import migration_role as helper

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    _migration_login(case)
    login = "hadavin_test_lg_" + uuid.uuid4().hex[:8]
    case.admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(login)))
    case.admin.execute(
        sql.SQL("GRANT {} TO {}").format(sql.Identifier(case.role["m"]), sql.Identifier(login))
    )
    helper.set_login_password(case.db, login)
    dsn = helper.login_dsn(
        make_conninfo(
            case._dsn, dbname=case.db_name, options=f"-c search_path={APP} -c role={case.role['m']}"
        ),
        login,
    )
    try:
        assert mig.migrate(dsn, runtime_role=case.role["n"]) == [
            p.stem for p in mig._migration_files()
        ]
        assert mig.migrate(dsn, runtime_role=case.role["n"]) == []
    finally:
        case.admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(login)))
        case.admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(login)))


@needs_pg
@pytest.mark.real_connect
def test_control_k2_the_schema_of_the_run_is_public_with_the_servers_own_access_list(case):
    """K2: the run uses `public`, whose access list is the server's own (USAGE for everyone). That default is not an excess."""
    from hadavin_sdk.store import migrate as mig

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case, "public")
    assert mig.migrate(dsn, runtime_role=case.role["n"]) == [p.stem for p in mig._migration_files()]
    assert mig.migrate(dsn, runtime_role=case.role["n"]) == []


# C8 (ticket 7.4, fact 14): the object is made a member of an extension the migration role owns, then the effect. `citext` is a
# trusted extension, so a plain role that holds CREATE on the database may make it (a `case`: the real plain login, which
# holds CREATE on the database: variant (C)). The extension is made by dynamic SQL. The object is not skipped for being an
# extension member. Batch 4b: every effect that has an object to add (the object of the effect: a map object, or the one the
# effect makes); each ends as `_expected_outcome` says. Effects with no object that can be a member are empty by logic.
C8_CARRIER = "C8-extension-member"
C8_OBJECT = {
    "O01-select-other": "TABLE audit_entries",
    "O02-select-everyone": "TABLE audit_entries",
    "O03-column-other": "TABLE audit_entries",
    "O04-sequence-other": "SEQUENCE approval_decisions_seq_seq",
    "O05-function-other": "FUNCTION hadavin_audit_append_only()",
    "O06-delete-runtime": "TABLE audit_entries",
    "O07-everyone-delete-runs": "TABLE runs",
    "O08-everyone-truncate-runs": "TABLE runs",
    "O09-everyone-column-select": "TABLE audit_entries",
    "O10-third-column-update": "TABLE runs",
    "O11-everyone-setval": "SEQUENCE dead_letters_seq_seq",
    "O12-grant-option": "TABLE runs",
    "O18-select-third-tool-calls": "TABLE tool_calls",
    "O19-select-on-a-table-outside-the-map-named": "TABLE zz_t",
    "O20-select-on-a-table-outside-the-map-everyone": "TABLE zz_t",
    "O21-usage-on-a-sequence-outside-the-map-named": "SEQUENCE zz_q",
    "O22-select-on-a-view-outside-the-map-everyone": "VIEW zz_v",
    "O23-execute-on-a-function-named": "FUNCTION zz_f()",
    "O24-function-of-the-family-left-callable-by-everyone": "FUNCTION hadavin_zz_f()",
    "O25-security-definer-function-in-the-schema-of-the-run": "FUNCTION hadavin_zz_d()",
    "O26-execute-on-a-procedure-named": "PROCEDURE zz_p()",
    "O27-usage-on-a-type-named": "TYPE zz_ty",
}
_C8_DEFAULT = 'a default right is not an object; measured: ALTER EXTENSION ... ADD DEFAULT PRIVILEGES is a syntax error at or near "DEFAULT"'
_C8_LO = 'a large object cannot be added to an extension; measured: ALTER EXTENSION ... ADD LARGE OBJECT is a syntax error at or near "LARGE"'
C8_EMPTY_BY_LOGIC = {
    "O16-default-right-named": _C8_DEFAULT,
    "O17-default-right-everyone": _C8_DEFAULT,
    "O28-select-on-a-large-object-everyone": _C8_LO,
    "O29-select-on-a-large-object-named": _C8_LO,
}
C8_CELLS = [(e, v) for e in C8_OBJECT for v in O_VARIANTS]


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("effect_id, variant", C8_CELLS, ids=[f"{e}/C8/{v}" for e, v in C8_CELLS])
def test_c8_an_object_that_is_an_extension_member_is_still_judged(
    effect_id, variant, case, monkeypatch, tmp_path
):
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    roles = {"runtime_role": case.role["n"]} if variant == "with-roles" else {}
    text = effect[1].format(lo=LO_NUMBER, **_case_names(case))
    first, _, rest = text.partition("; ")
    if (
        effect_id in C10_STATEMENTS
    ):  # the effect makes the object: make it, add it, then the rest of the effect
        statements = [first, f"ALTER EXTENSION citext ADD {C8_OBJECT[effect_id]}"] + (
            [rest] if rest else []
        )
    else:  # a map object exists from the shipped files; add it, then the effect
        statements = [f"ALTER EXTENSION citext ADD {C8_OBJECT[effect_id]}", text]
    statements.insert(0, "CREATE EXTENSION citext")
    tp._with_files(
        monkeypatch,
        tmp_path,
        {"0006_member.sql": "".join(_split_function(st) for st in statements)},
    )
    expected = _expected_outcome(effect_id, C8_CARRIER, variant)
    try:
        mig.migrate(dsn, **roles)
        outcome = "iii"
    except errors.ConfigError as e:
        outcome = "i"
        assert _kept_nothing(e) and "migrations are inconsistent" not in str(e), str(e)[:500]
    assert outcome == expected, f"{effect_id}/C8/{variant}: outcome {outcome}, expected {expected}"


# r16 group 2: a SCHEMA can be an extension member (`ALTER EXTENSION x ADD SCHEMA s` is valid; measured on PostgreSQL 16 as the
# superuser). The right on the schema of the run is then given while the schema is a member, so that a check that skips
# extension members would miss it. Two forms of the setup: the printed one (the schema is owned by an administrator: the
# server refuses the membership to the migration role) and the one where the migration role owns the schema of the run.
C8_SCHEMA_EFFECTS = (
    "O13-create-on-schema-other",
    "O14-usage-with-grant-option",
    "O15-create-on-schema-everyone",
)
C8_SCHEMA_OWNERS = ("administrator-owns-the-schema", "migration-role-owns-the-schema")
C8_SCHEMA_CELLS = [
    (e, o, v) for e in C8_SCHEMA_EFFECTS for o in C8_SCHEMA_OWNERS for v in O_VARIANTS
]


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize(
    "effect_id, owner, variant",
    C8_SCHEMA_CELLS,
    ids=[f"{e}/C8/{o}/{v}" for e, o, v in C8_SCHEMA_CELLS],
)
def test_c8_the_schema_of_the_run_as_an_extension_member_is_still_judged(
    effect_id, owner, variant, case, monkeypatch, tmp_path
):
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    if owner == "migration-role-owns-the-schema":
        case.db.execute(
            sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                sql.Identifier(APP), sql.Identifier(case.role["m"])
            )
        )
    roles = {"runtime_role": case.role["n"]} if variant == "with-roles" else {}
    text = effect[1].format(lo=LO_NUMBER, **_case_names(case))
    # the extension lives in its own schema: a schema cannot be added to an extension that is in it
    statements = [
        "CREATE SCHEMA zz_ext",
        "CREATE EXTENSION citext SCHEMA zz_ext",
        f"ALTER EXTENSION citext ADD SCHEMA {APP}",
        text,
    ]
    tp._with_files(
        monkeypatch,
        tmp_path,
        {"0006_member.sql": "".join(_split_function(st) for st in statements)},
    )
    kept = (
        "SELECT (SELECT count(*) FROM pg_catalog.pg_namespace WHERE nspname = 'zz_ext'), "
        "(SELECT count(*) FROM pg_catalog.pg_extension WHERE extname = 'citext')"
    )
    if owner == "administrator-owns-the-schema":
        # measured on PostgreSQL 16: the server itself refuses the membership to a role that does not own the schema, and
        # the run stops with the server's own error and keeps nothing (the extension and its schema are rolled back)
        with pytest.raises(
            psycopg.errors.InsufficientPrivilege, match="must be owner of schema app"
        ):
            mig.migrate(dsn, **roles)
        assert case.db.execute(kept).fetchone() == (0, 0), (
            "the refused run kept the extension or its schema"
        )
        return
    with pytest.raises(errors.ConfigError) as caught:
        mig.migrate(dsn, **roles)
    text = str(caught.value)
    assert _kept_nothing(text) and "migrations are inconsistent" not in text, text[:500]
    assert case.db.execute(kept).fetchone() == (0, 0), (
        "the refused run kept the extension or its schema"
    )
    assert _C8_SCHEMA_FINDING[effect_id] in text, (
        f"{effect_id}: the schema is an extension member and the refusal must still name the right: {text[:500]}"
    )


_C8_SCHEMA_FINDING = {
    "O13-create-on-schema-other": "has CREATE on the schema of the run",
    "O14-usage-with-grant-option": "may pass USAGE on to others",
    "O15-create-on-schema-everyone": "everyone (PUBLIC) has CREATE on the schema of the run",
}


def test_c13_every_effect_has_a_table_to_move_or_a_reason_it_has_none():
    ids = {e[0] for e in O_EFFECTS}
    built = (
        set(C13_TABLE_EFFECTS)
        | set(C13_OTHER_MOVES)
        | set(C13_SCHEMA_EFFECTS)
        | {C13_FUNCTION_EFFECT}
    )
    assert built | set(C13_EMPTY_BY_LOGIC) == ids
    assert not built & set(C13_EMPTY_BY_LOGIC)
    assert all(len(why) > 40 for why in C13_EMPTY_BY_LOGIC.values())


def test_c8_every_effect_has_an_object_or_a_reason_it_has_none():
    ids = {e[0] for e in O_EFFECTS}
    built = set(C8_OBJECT) | set(C8_SCHEMA_EFFECTS)
    assert built | set(C8_EMPTY_BY_LOGIC) == ids and not built & set(C8_EMPTY_BY_LOGIC)


@needs_pg
@pytest.mark.real_connect
def test_c9_a_table_owned_by_the_login_is_the_familys_own_so_a_third_role_right_on_it_is_refused(
    case,
):
    """Carrier C9, the family of a login that differs from the role (round 15, Issue 6). The DSN logs in as L and switches to
    the migration role M; L is part of the family (it can act as M). A table in the schema of the run that L owns, with a
    right for a third role (no role argument names it), is a table of the family: refused before any file runs (rule O1),
    keeping nothing. With the right revoked the run returns. Killed by V107 (L not counted in the family: the table would
    be 'another application's' and the right is not judged)."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp  # noqa: F401
    from tests.fixtures import migration_role as helper

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    _migration_login(case)
    login = "hadavin_test_lg_" + uuid.uuid4().hex[:8]
    case.admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(login)))
    case.admin.execute(
        sql.SQL("GRANT {} TO {}").format(sql.Identifier(case.role["m"]), sql.Identifier(login))
    )
    helper.set_login_password(case.db, login)
    dsn = helper.login_dsn(
        make_conninfo(
            case._dsn,
            dbname=case.db_name,
            options=f"-c search_path={APP} -c role={case.role['m']}",
        ),
        login,
    )
    third = case.role["o"]
    try:
        case.db.execute(sql.SQL("CREATE TABLE {}.zz_login (a int)").format(sql.Identifier(APP)))
        case.db.execute(
            sql.SQL("ALTER TABLE {}.zz_login OWNER TO {}").format(
                sql.Identifier(APP), sql.Identifier(login)
            )
        )
        case.db.execute(
            sql.SQL("GRANT SELECT ON {}.zz_login TO {}").format(
                sql.Identifier(APP), sql.Identifier(third)
            )
        )
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn)
        text = str(seen.value)
        assert _kept_nothing(text) and third in text and f"{APP}.zz_login" in text, (
            f"the right of the third role {third} on {APP}.zz_login (a table the login owns) must be refused and named: "
            f"{text[:500]}"
        )
        case.db.execute(
            sql.SQL("REVOKE SELECT ON {}.zz_login FROM {}").format(
                sql.Identifier(APP), sql.Identifier(third)
            )
        )
        assert mig.migrate(dsn) == [p.stem for p in mig._migration_files()]
    finally:
        case.db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(login)))
        case.admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(login)))


# K10 (fact 33): a file makes one object of every relation kind a plain role can make (a standalone type is no relation: its
# default PUBLIC USAGE is an excess and is refused, see the C1 cells of the type effect). Each has a row type that PUBLIC may use
# by default; that is not an excess right and the run must return with no excess for named roles and for everyone.
@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
def test_control_k10_every_relation_kind_with_its_row_type_is_not_an_excess(
    variant, ocell, monkeypatch, tmp_path
):
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        kinds = [
            "CREATE TABLE zz_table (a int)",
            "CREATE TABLE zz_part (a int) PARTITION BY RANGE (a)",
            "CREATE TABLE zz_part_1 PARTITION OF zz_part FOR VALUES FROM (0) TO (10)",
            "CREATE VIEW zz_view AS SELECT 1 AS a",
            "CREATE MATERIALIZED VIEW zz_matview AS SELECT 1 AS a",
            "CREATE SEQUENCE zz_seq",
            "CREATE INDEX zz_idx ON zz_table (a)",
        ]
        body = "".join(_split_function(k) for k in kinds)
        tp._with_files(monkeypatch, tmp_path, {"0006_kinds.sql": body})
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        assert mig.migrate(dsn, **roles) == tp.REAL + ["0006_kinds"]
        assert _no_excess_rights(schema, other, rt if roles else None) == []
        assert mig.migrate(dsn, **roles) == []
    finally:
        tp._drop_roles(other, rt)


# C13 (ticket 7.4): move and recreate. A map table is moved to another schema (or renamed) and a table of the same name is made
# again; the role that is not allowed anything holds a right on the moved table, which now lies outside the map. The map is
# matched by schema, name and kind, so the moved table is judged like any table outside the map: outcome (i), nothing kept.
C13_FORMS = {
    "move-to-another-schema": (
        "ALTER TABLE spend SET SCHEMA {o}x;\nCREATE TABLE spend (a int);\nGRANT SELECT ON {o}x.spend TO {who};\n"
    ),
    "plain-rename": "ALTER TABLE spend RENAME TO spend_old;\nCREATE TABLE spend (a int);\nGRANT SELECT ON spend_old TO {who};\n",
}


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
@pytest.mark.parametrize("form", list(C13_FORMS))
def test_c13_a_map_table_moved_or_renamed_and_made_again_is_refused_and_nothing_is_kept(
    form, variant, ocell, monkeypatch, tmp_path
):
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    from tests.fixtures import migration_role as helper

    moved_to = schema + "_m"
    tp._create_roles(other, rt)
    try:
        with psycopg.connect(DSN, autocommit=True) as admin:
            helper.ensure_plain_role(admin)
            admin.execute(
                sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                    sql.Identifier(moved_to), sql.Identifier(helper.PLAIN_ROLE)
                )
            )
            admin.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(moved_to))
            )
        text = (
            C13_FORMS[form]
            .replace("{o}x", sql.Identifier(moved_to).as_string())
            .replace("{who}", rt if variant == "with-roles" else "PUBLIC")
        )
        tp._with_files(monkeypatch, tmp_path, {"0006_move.sql": text})
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn, **roles)
        assert "inconsistent" not in str(seen.value), str(seen.value)[:400]
        with psycopg.connect(DSN, autocommit=True) as admin:
            kept = admin.execute(
                "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = %s AND c.relname = 'spend_old'",
                (schema,),
            ).fetchone()[0]
        assert kept == 0
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(moved_to))
            )
        tp._drop_roles(other, rt)


# C13, every effect that is a right on a table (batch 4b): the table is renamed and a table of the old name is made again, and
# the effect is run on the moved table (the name in the effect is replaced by the new name). Every right on the moved table (everyone, the
# named role, a third role) is refused like a right on any table of the family outside the map. Effects that are not a right on a table have nothing to move.
# The ledger table `audit_entries` has a trigger, and renaming a table that has one is refused as a trigger change (another rule,
# not the one under test), so the effects of `audit_entries` are run on the moved table `runs` instead (its column `state`
# stands for `seq`): the rule under test is the same, a right on a table outside the map.
C13_TABLE_EFFECTS = {
    "O01-select-other": "runs",
    "O02-select-everyone": "runs",
    "O03-column-other": "runs",
    "O06-delete-runtime": "runs",
    "O07-everyone-delete-runs": "runs",
    "O08-everyone-truncate-runs": "runs",
    "O09-everyone-column-select": "runs",
    "O10-third-column-update": "runs",
    "O12-grant-option": "runs",
    "O18-select-third-tool-calls": "tool_calls",
}
# Every reason below carries the text the real server answered (r16 groups 1 and 2: a reason that stays is the server's own
# answer, never a thought). `test_every_empty_reason_is_the_answer_of_a_real_server` runs each statement and compares.
_MOVED_OBJECT_REASON = (
    "the object the file makes itself can be moved (measured on PostgreSQL 16.15: ALTER ... SET SCHEMA runs without an "
    "error for a table, a sequence, a view, a function, a procedure and a type), but it is then an object of another schema, "
    "which the C10 cell of the same effect judges"
)
C13_EMPTY_BY_LOGIC: dict[str, str] = {
    "O16-default-right-named": 'a default right has no object to move; measured: ALTER DEFAULT PRIVILEGES ... SET SCHEMA is a syntax error at or near "SET"',
    "O17-default-right-everyone": 'a default right has no object to move; measured: ALTER DEFAULT PRIVILEGES ... SET SCHEMA is a syntax error at or near "SET"',
    **{
        e: _MOVED_OBJECT_REASON
        for e in (
            "O19-select-on-a-table-outside-the-map-named",
            "O20-select-on-a-table-outside-the-map-everyone",
            "O21-usage-on-a-sequence-outside-the-map-named",
            "O22-select-on-a-view-outside-the-map-everyone",
            "O23-execute-on-a-function-named",
            "O24-function-of-the-family-left-callable-by-everyone",
            "O25-security-definer-function-in-the-schema-of-the-run",
            "O26-execute-on-a-procedure-named",
            "O27-usage-on-a-type-named",
        )
    },
    "O28-select-on-a-large-object-everyone": 'a large object has no schema; measured: ALTER LARGE OBJECT ... SET SCHEMA is a syntax error at or near "SET"',
    "O29-select-on-a-large-object-named": 'a large object has no schema; measured: ALTER LARGE OBJECT ... SET SCHEMA is a syntax error at or near "SET"',
}
# r16 group 2: C13 for the map objects that are not tables. Measured on PostgreSQL 16.15: a sequence made by BIGSERIAL cannot
# be moved alone ("cannot move an owned sequence into another schema") but it moves WITH its table (`ALTER TABLE ... SET
# SCHEMA`), and a function can be moved (`ALTER FUNCTION ... SET SCHEMA`), so these effects do have something to move.
# effect -> (the move and recreate text, the right on the moved object); `{m}` is the schema it moves to
C13_OTHER_MOVES = {
    "O04-sequence-other": (
        "ALTER TABLE approval_decisions SET SCHEMA {m}; CREATE TABLE approval_decisions (seq BIGSERIAL PRIMARY KEY); ",
        "GRANT USAGE ON SEQUENCE {m}.approval_decisions_seq_seq TO {rt}",
        "approval_decisions_seq_seq",
    ),
    "O11-everyone-setval": (
        "ALTER TABLE dead_letters SET SCHEMA {m}; CREATE TABLE dead_letters (seq BIGSERIAL PRIMARY KEY); ",
        "GRANT UPDATE ON SEQUENCE {m}.dead_letters_seq_seq TO PUBLIC",
        "dead_letters_seq_seq",
    ),
}


C13_OTHER_MOVES_THAT_RETURN = {("O04-sequence-other", "no-roles")}


C13_SCHEMA_EFFECTS = [
    "O13-create-on-schema-other",
    "O14-usage-with-grant-option",
    "O15-create-on-schema-everyone",
]
C13_FUNCTION_EFFECT = "O05-function-other"  # measured: refused by the trigger rule (see its test), so it has no right to judge

C13_CELLS = (
    [(f, v) for f in C13_FORMS for v in O_VARIANTS]
    + [(e, v) for e in C13_TABLE_EFFECTS for v in O_VARIANTS]
    + [(e, v) for e in C13_OTHER_MOVES for v in O_VARIANTS]  # r16 group 2
    + [(e, v) for e in C13_SCHEMA_EFFECTS for v in O_VARIANTS]
    + [(C13_FUNCTION_EFFECT, v) for v in O_VARIANTS]
)


# --- r16 groups 1 and 2: every empty-by-logic reason is the answer of a real server --------------------------------------------
# (carrier, effect) -> (statement run as the superuser in the scratch database of a `case`, sqlstate or None for "no error",
# text the server's message must contain). `s` and `s2` exist in the scratch database; `s2` stands for "another schema".
_MAP_NAMES = {
    "O01-select-other": "GRANT SELECT ON s2.audit_entries TO PUBLIC",
    "O02-select-everyone": "GRANT SELECT ON s2.audit_entries TO PUBLIC",
    "O03-column-other": "GRANT SELECT (seq) ON s2.audit_entries TO PUBLIC",
    "O04-sequence-other": "GRANT USAGE ON SEQUENCE s2.approval_decisions_seq_seq TO PUBLIC",
    "O06-delete-runtime": "GRANT DELETE ON s2.audit_entries TO PUBLIC",
    "O07-everyone-delete-runs": "GRANT DELETE ON s2.runs TO PUBLIC",
    "O08-everyone-truncate-runs": "GRANT TRUNCATE ON s2.runs TO PUBLIC",
    "O09-everyone-column-select": "GRANT SELECT (seq) ON s2.audit_entries TO PUBLIC",
    "O10-third-column-update": "GRANT UPDATE (state) ON s2.runs TO PUBLIC",
    "O11-everyone-setval": "GRANT UPDATE ON SEQUENCE s2.dead_letters_seq_seq TO PUBLIC",
    "O12-grant-option": "GRANT SELECT ON s2.runs TO PUBLIC WITH GRANT OPTION",
    "O18-select-third-tool-calls": "GRANT SELECT ON s2.tool_calls TO PUBLIC",
}
EMPTY_PROBES: dict[tuple[str, str], tuple[str, str | None, str]] = {
    **{("C10-another-schema", e): (st, "42P01", "does not exist") for e, st in _MAP_NAMES.items()},
    ("C10-another-schema", "O05-function-other"): (
        "GRANT EXECUTE ON FUNCTION s2.hadavin_audit_append_only() TO PUBLIC", "42883", "does not exist",
    ),
    **{
        ("C10-another-schema", e): ("GRANT SELECT ON LARGE OBJECT s2.70001 TO PUBLIC", "42601", 'syntax error at or near "s2"')
        for e in ("O28-select-on-a-large-object-everyone", "O29-select-on-a-large-object-named")
    },
    **{
        (C8_CARRIER, e): ("ALTER EXTENSION file_fdw ADD DEFAULT PRIVILEGES", "42601", 'syntax error at or near "DEFAULT"')
        for e in ("O16-default-right-named", "O17-default-right-everyone")
    },
    **{
        (C8_CARRIER, e): ("ALTER EXTENSION file_fdw ADD LARGE OBJECT 70001", "42601", 'syntax error at or near "LARGE"')
        for e in ("O28-select-on-a-large-object-everyone", "O29-select-on-a-large-object-named")
    },
    **{
        ("C13-move-and-recreate", e): ("ALTER DEFAULT PRIVILEGES IN SCHEMA s SET SCHEMA s2", "42601", 'syntax error at or near "SET"')
        for e in ("O16-default-right-named", "O17-default-right-everyone")
    },
    **{
        ("C13-move-and-recreate", e): ("ALTER LARGE OBJECT 70001 SET SCHEMA s2", "42601", 'syntax error at or near "SET"')
        for e in ("O28-select-on-a-large-object-everyone", "O29-select-on-a-large-object-named")
    },
    ("C13-move-and-recreate", "O19-select-on-a-table-outside-the-map-named"): ("CREATE TABLE s.zz_t (a int); ALTER TABLE s.zz_t SET SCHEMA s2", None, ""),
    ("C13-move-and-recreate", "O21-usage-on-a-sequence-outside-the-map-named"): ("CREATE SEQUENCE s.zz_q; ALTER SEQUENCE s.zz_q SET SCHEMA s2", None, ""),
    ("C13-move-and-recreate", "O22-select-on-a-view-outside-the-map-everyone"): ("CREATE VIEW s.zz_v AS SELECT 1 AS a; ALTER VIEW s.zz_v SET SCHEMA s2", None, ""),
    ("C13-move-and-recreate", "O23-execute-on-a-function-named"): ("CREATE FUNCTION s.zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'; ALTER FUNCTION s.zz_f() SET SCHEMA s2", None, ""),
    ("C13-move-and-recreate", "O26-execute-on-a-procedure-named"): ("CREATE PROCEDURE s.zz_p() LANGUAGE sql AS ''; ALTER PROCEDURE s.zz_p() SET SCHEMA s2", None, ""),
    ("C13-move-and-recreate", "O27-usage-on-a-type-named"): ("CREATE TYPE s.zz_ty AS (a int); ALTER TYPE s.zz_ty SET SCHEMA s2", None, ""),
}  # fmt: skip
# the effects whose moved object is the same kind as another effect's: the one probe of the kind stands for the rest
for _e, _like in (
    (
        "O20-select-on-a-table-outside-the-map-everyone",
        "O19-select-on-a-table-outside-the-map-named",
    ),
    ("O24-function-of-the-family-left-callable-by-everyone", "O23-execute-on-a-function-named"),
    ("O25-security-definer-function-in-the-schema-of-the-run", "O23-execute-on-a-function-named"),
):
    EMPTY_PROBES[("C13-move-and-recreate", _e)] = EMPTY_PROBES[("C13-move-and-recreate", _like)]


def _empty_pairs() -> dict[tuple[str, str], str]:
    pairs = {(c, e): why for (e, c), why in O_EMPTY_BY_LOGIC.items()}
    pairs.update({(C8_CARRIER, e): why for e, why in C8_EMPTY_BY_LOGIC.items()})
    pairs.update({("C13-move-and-recreate", e): why for e, why in C13_EMPTY_BY_LOGIC.items()})
    return pairs


def test_every_empty_pair_has_a_probe_and_its_reason_carries_the_measured_text():
    pairs = _empty_pairs()
    assert set(pairs) == set(EMPTY_PROBES), (
        f"an empty pair without a probe, or a probe without an empty pair: {set(pairs) ^ set(EMPTY_PROBES)}"
    )
    for key, why in pairs.items():
        assert "measured" in why or "ALTER ... SET SCHEMA runs without an error" in why, (
            f"{key}: the reason is not the server's answer: {why}"
        )


@needs_pg
def test_every_empty_reason_is_the_answer_of_a_real_server(case):
    """Each statement of the table runs on a real server, as the superuser, in a scratch database. A reason that says
    "the server refuses it" must be refused with that sqlstate and text; one that says "it runs" must run without an error."""
    from hadavin_sdk.store import migrate as mig  # noqa: F401  (the server version is printed with the result)

    version = case.db.execute("SHOW server_version").fetchone()[0]
    failures = []
    for key, (statement, state, text) in sorted(EMPTY_PROBES.items()):
        try:
            for part in statement.split("; "):
                case.db.execute(part)
        except psycopg.Error as exc:
            if state is None:
                failures.append(
                    f"{key}: expected no error, the server {version} said {exc.sqlstate} {exc}"
                )
            elif exc.sqlstate != state or text not in exc.diag.message_primary:
                failures.append(
                    f"{key}: expected {state} with {text!r}, the server {version} said {exc.sqlstate} {exc.diag.message_primary!r}"
                )
        else:
            if state is not None:
                failures.append(
                    f"{key}: expected {state}, the server {version} ran it without an error"
                )
        for undo in (
            "DROP TABLE IF EXISTS s.zz_t, s2.zz_t", "DROP SEQUENCE IF EXISTS s.zz_q, s2.zz_q",
            "DROP VIEW IF EXISTS s.zz_v, s2.zz_v", "DROP FUNCTION IF EXISTS s.zz_f(), s2.zz_f()",
            "DROP PROCEDURE IF EXISTS s.zz_p(), s2.zz_p()", "DROP TYPE IF EXISTS s.zz_ty, s2.zz_ty",
        ):  # fmt: skip
            case.db.execute(undo)
    assert not failures, "\n".join(failures)


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
@pytest.mark.parametrize("effect_id", list(C13_TABLE_EFFECTS))
def test_c13_every_right_on_a_moved_table_is_judged_like_one_outside_the_map(
    effect_id, variant, ocell, monkeypatch, tmp_path
):
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    table = C13_TABLE_EFFECTS[effect_id]
    tp._create_roles(other, rt)
    try:
        original = (
            _effect_text(effect, other, rt, schema)
            .replace("audit_entries", "runs")
            .replace("(seq)", "(state)")
        )
        grant = re.sub(rf"\b{table}\b", f"{table}_old", original)
        text = (
            f"ALTER TABLE {table} RENAME TO {table}_old;\nCREATE TABLE {table} (a int);\n{grant};\n"
        )
        tp._with_files(monkeypatch, tmp_path, {"0006_move.sql": text})
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        # measured on PostgreSQL 16.15: the moved table is owned by the migration role, so it is a table of the family
        # outside the map, and every right on it (everyone, the named role, the third role) is refused in both variants
        try:
            mig.migrate(dsn, **roles)
            outcome = "iii"
        except errors.ConfigError as e:
            outcome = "i"
            assert _kept_nothing(e) and "migrations are inconsistent" not in str(e), str(e)[:400]
            # the refusal is about the right on the moved table, not about another rule
            assert f"{table}_old" in str(e), (
                f"{effect_id}/C13/{variant}: the refusal does not name the moved table: {e}"[:600]
            )
        assert outcome == "i", f"{effect_id}/C13/{variant}: {outcome}"
    finally:
        _forget_default_rights(dsn)
        tp._drop_roles(other, rt)


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
@pytest.mark.parametrize("effect_id", list(C13_OTHER_MOVES))
def test_c13_a_sequence_or_function_moved_out_of_the_map_is_judged_like_one_outside_the_map(
    effect_id, variant, ocell, monkeypatch, tmp_path
):
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp
    from tests.fixtures import migration_role as helper

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    moved_to = schema + "_m"
    move, grant, name = C13_OTHER_MOVES[effect_id]
    tp._create_roles(other, rt)
    try:
        with psycopg.connect(DSN, autocommit=True) as admin:
            helper.ensure_plain_role(admin)
            admin.execute(
                sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                    sql.Identifier(moved_to), sql.Identifier(helper.PLAIN_ROLE)
                )
            )
            admin.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(moved_to))
            )
        m = sql.Identifier(moved_to).as_string()
        text = (move + grant).replace("{m}", m).replace("{rt}", rt)
        tp._with_files(monkeypatch, tmp_path, {"0006_move.sql": _split_function(text)})
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        if (effect_id, variant) in C13_OTHER_MOVES_THAT_RETURN:
            # the decision of B5, the same pin as carrier C10: the right is the named runtime role's and no role is named
            assert mig.migrate(dsn, **roles)[-1] == "0006_move"
            return
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn, **roles)
        message = str(seen.value)
        assert _kept_nothing(message) and "inconsistent" not in message, message[:500]
        assert moved_to in message and name in message, (
            f"{effect_id}/C13/{variant}: the refusal must name the moved object in the other schema: {message[:600]}"
        )
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(moved_to))
            )
        tp._drop_roles(other, rt)


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
@pytest.mark.parametrize("effect_id", C13_SCHEMA_EFFECTS)
def test_c13_the_schema_of_the_run_renamed_and_made_again_is_refused_by_the_server(
    effect_id, variant, ocell, monkeypatch, tmp_path
):
    """The move and recreate of the schema of the run itself (r16 group 2, measured on PostgreSQL 16.15): the migration role
    may not rename the schema, so the server stops the file with its own error and the run keeps nothing."""
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    dsn, schema = ocell
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    old = schema + "_old"
    try:
        q = sql.Identifier(schema).as_string()
        qo = sql.Identifier(old).as_string()
        right = _effect_text(effect, other, rt, schema).replace(q.strip('"'), old)
        text = f"ALTER SCHEMA {q} RENAME TO {qo}; CREATE SCHEMA {q}; {right}"
        tp._with_files(monkeypatch, tmp_path, {"0006_move.sql": _split_function(text)})
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        with pytest.raises(
            psycopg.errors.InsufficientPrivilege, match="permission denied for database"
        ):
            mig.migrate(dsn, **roles)
        with psycopg.connect(DSN, autocommit=True) as admin:
            assert admin.execute(
                "SELECT count(*) FROM pg_catalog.pg_namespace WHERE nspname = %s", (old,)
            ).fetchone() == (0,), "the refused run kept the renamed schema"
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(old)))
        tp._drop_roles(other, rt)


@needs_pg
def test_c13_the_function_of_the_map_moved_is_refused_by_the_trigger_rule_before_any_right_is_judged(
    ocell, monkeypatch, tmp_path
):
    """O05 under C13 (r16 group 2): the function can be moved, but four triggers of the package call it, so the move is
    refused as a trigger change (another rule); no right on the moved function is ever judged. Measured text pinned."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp
    from tests.fixtures import migration_role as helper

    dsn, schema = ocell
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    moved_to = schema + "_m"
    try:
        with psycopg.connect(DSN, autocommit=True) as admin:
            helper.ensure_plain_role(admin)
            admin.execute(
                sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                    sql.Identifier(moved_to), sql.Identifier(helper.PLAIN_ROLE)
                )
            )
            admin.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(moved_to))
            )
        m = sql.Identifier(moved_to).as_string()
        text = (
            f"ALTER FUNCTION hadavin_audit_append_only() SET SCHEMA {m}; "
            "CREATE FUNCTION hadavin_audit_append_only() RETURNS int LANGUAGE sql AS 'SELECT 1'; "
            f"GRANT EXECUTE ON FUNCTION {m}.hadavin_audit_append_only() TO {rt}"
        )
        tp._with_files(monkeypatch, tmp_path, {"0006_move.sql": _split_function(text)})
        with pytest.raises(
            errors.ConfigError, match=r"changed a trigger: .*changed: definition"
        ) as seen:
            mig.migrate(dsn, runtime_role=rt)
        assert "hadavin_audit_append_only" not in str(seen.value).split("changed a trigger")[0]
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(moved_to))
            )
        tp._drop_roles(other, rt)


# C6b (ticket 7.4, facts 4 and 39): a deferred constraint trigger that defers itself again. Its first firing is at step 5
# (`SET CONSTRAINTS ALL IMMEDIATE`) and puts the trigger back in the deferred state; its second firing is at the COMMIT, after
# every check before it, so the effect cannot be stopped. The ticket's answer is outcome (ii): `migrate` returns the applied
# state and says what is wrong (`AppliedNotVerifiedError`, exit 5), found by the check after the commit.
def _redefer_files(statement: str) -> dict[str, str]:
    """The table and the trigger function are made beforehand (see `_make_the_redefer_parts`); the file makes the trigger and
    the first row inside a function body, so the text rules see neither."""
    runs = " ".join(
        f"EXECUTE '{part[:3]}' || '{part[3:]}';"
        for part in (
            (
                "CREATE CONSTRAINT TRIGGER hadavin_test_late_t AFTER INSERT ON hadavin_test_q DEFERRABLE INITIALLY DEFERRED "
                "FOR EACH ROW EXECUTE FUNCTION hadavin_test_late()"
            ),
            "INSERT INTO hadavin_test_q VALUES (1)",
        )
    )
    return {
        "0006_late.sql": "CREATE OR REPLACE FUNCTION hadavin_test_late_runner() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"{runs} END $$;\nSELECT hadavin_test_late_runner();\n"
    }


def _make_the_redefer_parts(schema: str, statement: str) -> None:
    from tests.fixtures import migration_role as helper

    with psycopg.connect(DSN, autocommit=True) as adm:
        helper.ensure_plain_role(adm)
        s = sql.Identifier(schema)
        adm.execute(sql.SQL("CREATE TABLE {}.hadavin_test_q (i int)").format(s))
        adm.execute(
            sql.SQL(
                "CREATE FUNCTION {0}.hadavin_test_late() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN "
                "IF NEW.i = 1 THEN EXECUTE 'SET CONSTR' || 'AINTS ALL DEFERRED'; "
                "INSERT INTO {0}.hadavin_test_q VALUES (2); ELSE "
            ).format(s)
            + sql.SQL("EXECUTE " + _split(statement) + ";")
            + sql.SQL(" END IF; RETURN NULL; END $f$")
        )
        adm.execute(
            sql.SQL("GRANT ALL ON {}.hadavin_test_q TO {}").format(
                s, sql.Identifier(helper.PLAIN_ROLE)
            )
        )


C6B_CELLS = [(e[0], v) for e in O_EFFECTS for v in O_VARIANTS]


# What the check after the commit must name for each effect (ticket 7.1 (ii): each excess with its object, its role and its
# kind of right): (object, who, right). `who` is "other" (the third role), "rt" (the named runtime role) or "everyone". An
# empty object is a right on the schema of the run or a default right. A finding about another object (the pre-made table
# `hadavin_test_q` or the trigger function of the carrier) does not satisfy a cell.
C6B_FINDING = {
    "O01-select-other": ("audit_entries", "other", "SELECT"),
    "O02-select-everyone": ("audit_entries", "everyone", "SELECT"),
    "O03-column-other": ("audit_entries", "other", "SELECT"),
    "O04-sequence-other": ("approval_decisions_seq_seq", "other", "USAGE"),
    "O05-function-other": ("hadavin_audit_append_only", "other", "EXECUTE"),
    "O06-delete-runtime": ("audit_entries", "rt", "DELETE"),
    "O07-everyone-delete-runs": ("runs", "everyone", "DELETE"),
    "O08-everyone-truncate-runs": ("runs", "everyone", "TRUNCATE"),
    "O09-everyone-column-select": ("audit_entries", "everyone", "SELECT"),
    "O10-third-column-update": ("runs", "other", "UPDATE"),
    "O11-everyone-setval": ("dead_letters_seq_seq", "everyone", "UPDATE"),
    "O12-grant-option": ("runs", "other", "SELECT"),
    "O13-create-on-schema-other": ("", "other", "CREATE"),
    "O14-usage-with-grant-option": ("", "other", "USAGE"),
    "O15-create-on-schema-everyone": ("", "everyone", "CREATE"),
    "O16-default-right-named": ("", "other", "SELECT"),
    "O17-default-right-everyone": ("", "everyone", "USAGE"),
    "O18-select-third-tool-calls": ("tool_calls", "other", "SELECT"),
    "O19-select-on-a-table-outside-the-map-named": ("zz_t", "rt", "SELECT"),
    "O20-select-on-a-table-outside-the-map-everyone": ("zz_t", "everyone", "SELECT"),
    "O21-usage-on-a-sequence-outside-the-map-named": ("zz_q", "rt", "USAGE"),
    "O22-select-on-a-view-outside-the-map-everyone": ("zz_v", "everyone", "SELECT"),
    "O23-execute-on-a-function-named": ("zz_f", "rt", "EXECUTE"),
    "O24-function-of-the-family-left-callable-by-everyone": ("hadavin_zz_f", "everyone", "EXECUTE"),
    "O25-security-definer-function-in-the-schema-of-the-run": (
        "hadavin_zz_d",
        "everyone",
        "EXECUTE",
    ),
    "O26-execute-on-a-procedure-named": ("zz_p", "rt", "EXECUTE"),
    "O27-usage-on-a-type-named": ("zz_ty", "rt", "USAGE"),
    "O28-select-on-a-large-object-everyone": (str(LO_NUMBER), "everyone", "SELECT"),
    "O29-select-on-a-large-object-named": (str(LO_NUMBER), "rt", "SELECT"),
}


def _names_the_finding(
    problems, text: str, effect_id: str, variant: str, other: str, rt: str, schema: str
) -> bool:
    """True when one finding has the object, the role and the kind of right of the effect (see C6B_FINDING)."""
    obj, who, right = C6B_FINDING[effect_id]
    role_name = {"other": other, "rt": rt}.get(who)
    for p in problems:
        if (p.obj or "") != obj and not (obj == "" and (p.obj or "") == ""):
            continue
        if p.right != right:
            continue
        if who == "everyone":
            ok = str(p.role).startswith("everyone")
        elif who == "rt" and variant == "no-roles":
            ok = True  # nobody named the role: the finding is about the same object and right, for everyone or the role
        else:
            ok = p.role == role_name
        if ok:
            return True
    return False


@needs_pg
@pytest.mark.parametrize(
    "effect_id, variant", C6B_CELLS, ids=[f"{e}/C6b/{v}" for e, v in C6B_CELLS]
)
def test_c6b_a_trigger_that_defers_itself_again_is_applied_and_reported(
    effect_id, variant, ocell, monkeypatch, tmp_path
):
    """Outcome (ii) for every effect: the run returns what it applied and reports the excess it found afterwards
    (`AppliedNotVerifiedError`), never a silent return and never a refusal that keeps nothing (the effect is already
    committed when it is found). Batch 4b: the report must NAME this effect's object, role and kind of right (C6B_FINDING),
    so a finding about something else (the carrier's own table or function) does not satisfy the cell."""
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    effect = next(e for e in O_EFFECTS if e[0] == effect_id)
    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    try:
        _make_the_redefer_parts(schema, _effect_text(effect, other, rt, schema))
        tp._with_files(monkeypatch, tmp_path, _redefer_files(effect[1]))
        if _pinned_reason(
            effect_id, "C6b", variant
        ):  # a right that is not judged: nothing to report
            mig.migrate(dsn, **roles)
        else:
            with pytest.raises(errors.AppliedNotVerifiedError) as seen:
                mig.migrate(dsn, **roles)
            assert _names_the_finding(
                seen.value.problems, str(seen.value), effect_id, variant, other, rt, schema
            ), (
                f"{effect_id}/C6b/{variant}: no finding names the object, role and right of the effect "
                f"{C6B_FINDING[effect_id]}: {[(p.kind, p.obj, p.role, p.right) for p in seen.value.problems]}"
            )
    finally:
        _forget_default_rights(dsn)
        tp._drop_roles(other, rt)


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
def test_c6b_control_a_trigger_that_defers_itself_again_and_changes_nothing_returns(
    variant, ocell, monkeypatch, tmp_path
):
    """The no-op control of C6b (C5 has one): the same trigger and the same pre-made table, but the effect is `SELECT 1`.
    The run returns normally and reports nothing, so a C6b cell that is refused with `AppliedNotVerifiedError` is refused
    for its effect and not for the carrier's own parts."""
    import uuid

    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    try:
        _make_the_redefer_parts(schema, "SELECT 1")
        tp._with_files(monkeypatch, tmp_path, _redefer_files("SELECT 1"))
        assert mig.migrate(dsn, **roles) == [*tp.REAL, "0006_late"]
    finally:
        tp._drop_roles(other, rt)


def _forget_default_rights(dsn: str) -> None:
    """A default right for everyone on sequences (E35) belongs to no schema, so dropping the schema does not remove it;
    take it away so that the next cell starts as the first one did."""
    from hadavin_sdk.store import migrate as mig

    with mig.connect(dsn) as db:
        me = db.execute("SELECT current_user").fetchone()[0]
    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {} REVOKE USAGE ON SEQUENCES FROM PUBLIC"
            ).format(sql.Identifier(me))
        )
        # the large object of E22 (a right on it names a role, which would stop the role from being dropped)
        admin.execute(
            "SELECT lo_unlink(oid) FROM pg_largeobject_metadata WHERE oid = %s", (LO_NUMBER,)
        ).fetchall()


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


# Controls K2 to K12 of ticket 7.4 (K1 is the control above), as far as the shared test database lets them be built. Each
# one must end in outcome (iii): the run returns and "applied with excess: 0" holds, with and without role arguments, so a
# refusal in a cell is a refusal of its effect and not of its set-up. `setup` runs as the superuser before the run and
# `undo` after it; `{x}` is the name of a second schema of another application.
O_CONTROLS_BUILT = {
    "K3-another-applications-schema": (
        [
            "CREATE SCHEMA {x}",
            "CREATE TABLE {x}.t (a int)",
            "REVOKE ALL ON {x}.t FROM PUBLIC",
            "CREATE FUNCTION {x}.f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
            "REVOKE ALL ON FUNCTION {x}.f() FROM PUBLIC",
            "CREATE TYPE {x}.ty AS (a int)",
            "REVOKE ALL ON TYPE {x}.ty FROM PUBLIC",
        ],
        "DROP SCHEMA {x} CASCADE",
    ),
    "K11-family-security-definer-function-only-its-owner-may-call": (
        [
            "CREATE SCHEMA {x}",
            "CREATE FUNCTION {x}.hadavin_audit_append_only() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
            "REVOKE ALL ON FUNCTION {x}.hadavin_audit_append_only() FROM PUBLIC",
        ],
        "DROP SCHEMA {x} CASCADE",
    ),
    "K12-family-function-in-another-schema-callable-by-everyone": (
        [
            "CREATE SCHEMA {x}",
            "CREATE FUNCTION {x}.hadavin_audit_append_only() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        ],
        "DROP SCHEMA {x} CASCADE",
    ),
}


@needs_pg
@pytest.mark.parametrize("variant", O_VARIANTS)
@pytest.mark.parametrize("control", sorted(O_CONTROLS_BUILT))
def test_the_other_clean_controls_return_with_no_excess_right(
    control, variant, ocell, monkeypatch, tmp_path
):
    import uuid

    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    x = "hadavin_test_x_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    setup, undo = O_CONTROLS_BUILT[control]
    try:
        with psycopg.connect(DSN, autocommit=True) as admin:
            for text in setup:
                admin.execute(text.format(x=x))
        roles = {"runtime_role": rt} if variant == "with-roles" else {}
        assert mig.migrate(dsn, **roles) == tp.REAL
        assert _no_excess_rights(schema, other, rt if roles else None) == []
        assert mig.migrate(dsn, **roles) == []
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(undo.format(x=x))
        tp._drop_roles(other, rt)


@needs_pg
def test_control_k4_a_named_role_with_a_live_temporary_table(ocell):
    """K4: a session of the named role holds a temporary table while the run goes through."""
    import uuid

    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        with psycopg.connect(DSN, autocommit=True) as live:
            live.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(other)))
            live.execute("CREATE TEMPORARY TABLE hadavin_test_live_temp (a int)")
            assert mig.migrate(dsn, runtime_role=rt) == tp.REAL
            assert _no_excess_rights(schema, other, rt) == []
    finally:
        tp._drop_roles(other, rt)


@needs_pg
def test_control_k9_a_run_with_no_pending_file_and_other_role_arguments_changes_nothing(ocell):
    """K9: after a clean run with no role arguments, a run with no pending file is given the runtime role: it returns, and
    nothing is left with excess."""
    import uuid

    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        assert mig.migrate(dsn) == tp.REAL
        assert mig.migrate(dsn, runtime_role=rt) == []
        assert _no_excess_rights(schema, other, rt) == []
    finally:
        tp._drop_roles(other, rt)


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("variant", O_VARIANTS)
def test_e28_a_named_role_owns_the_schema_of_the_run_is_refused_and_no_file_runs(variant, case):
    """E28, schema form (outcome i), carrier C12. It needs the real plain migration login: the shared-database cells run
    `migrate` through a helper that hands the schema to the plain role at every connect, which would undo the state. The
    runtime role owns the schema of the run after one clean run; the next run with the role arguments is refused before
    any file runs and keeps nothing; with none, nobody named the role, so the run returns (pinned, like the seven cells)."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    rt = case.role["n"]
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    assert mig.migrate(dsn, **roles) == [p.stem for p in mig._migration_files()]
    case.db.execute(
        sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(APP), sql.Identifier(rt))
    )
    if (
        variant == "no-roles"
    ):  # a role nobody named is not judged (the decision of B5 above, X_NAMED_ROLE_EFFECTS)
        assert mig.migrate(dsn) == []
        return
    with pytest.raises(errors.ConfigError) as seen:
        mig.migrate(dsn, **roles)
    text = str(seen.value)
    assert (
        "before any migration file ran" in text
        and "No file ran" in text
        or "Nothing was changed" in text
    ), text


# Controls K5 to K8 of ticket 7.4 need a database of their own and the real plain migration login (a `case`). Each must end in
# outcome (iii): the run returns, a second run has nothing pending, and nothing is reported as applied with excess.
def _control_with_a_case(case, monkeypatch, tmp_path, setup: list[str], file_text: str | None):
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    names = {
        "db": sql.Identifier(case.db_name).as_string(),
        "m": sql.Identifier(case.role["m"]).as_string(),
        "g": sql.Identifier(case.role["g"]).as_string(),
        "o": sql.Identifier(case.role["o"]).as_string(),
        "n": sql.Identifier(case.role["n"]).as_string(),
        "schema": sql.Identifier(APP).as_string(),
    }
    for text in setup:
        case.db.execute(text.format(**names))
    if file_text is not None:
        tp._with_files(monkeypatch, tmp_path, {"0006_hand_over.sql": file_text.format(**names)})
    applied = mig.migrate(dsn, runtime_role=case.role["n"])
    assert applied == [p.stem for p in mig._migration_files()]
    assert mig.migrate(dsn, runtime_role=case.role["n"]) == []


@needs_pg
@pytest.mark.real_connect
def test_control_k5_a_database_owned_by_the_migration_role(case, monkeypatch, tmp_path):
    _control_with_a_case(case, monkeypatch, tmp_path, ["ALTER DATABASE {db} OWNER TO {m}"], None)


@needs_pg
@pytest.mark.real_connect
def test_control_k6_a_database_owned_by_a_group_with_only_the_migration_role_as_member(
    case, monkeypatch, tmp_path
):
    _control_with_a_case(
        case, monkeypatch, tmp_path, ["GRANT {g} TO {m}", "ALTER DATABASE {db} OWNER TO {g}"], None
    )


@needs_pg
@pytest.mark.real_connect
def test_control_k7_a_database_owned_by_a_group_with_a_second_member(case, monkeypatch, tmp_path):
    """K7 (E27): the group that owns the database has a second member; documents that this is not a promise."""
    _control_with_a_case(
        case,
        monkeypatch,
        tmp_path,
        ["GRANT {g} TO {m}", "GRANT {g} TO {o}", "ALTER DATABASE {db} OWNER TO {g}"],
        None,
    )


@needs_pg
@pytest.mark.real_connect
def test_control_k8_the_hand_over_is_refused_in_three_forms(case, monkeypatch, tmp_path):
    """K8 of the ticket (a file hands a map table to a group the migration role belongs to, "allowed since O5 is struck"): in
    three forms it does not end in outcome (iii) on this head (a fourth form, the group owning the schema of the run,
    does: the next test). Each of the three measured: (1) written in the open, the text rules refuse it at
    step 0 ("an object may not be handed to another role by a migration file"); (2) made by dynamic SQL, the server refuses it
    because the new owner holds no CREATE on the schema (a file error, 42501, raised as it is); (3) the same, after an
    administrator gave the group CREATE on the schema, the run refuses the state before any file runs. The three are pinned as
    three refusals; the ticket line K8 is met by the fourth form (see the next test)."""
    import psycopg.errors as pge

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    g, m = case.role["g"], case.role["m"]
    case.db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(g), sql.Identifier(m)))
    in_the_open = "ALTER TABLE spend OWNER TO " + sql.Identifier(g).as_string() + ";\n"
    with pytest.MonkeyPatch.context() as mp:
        tp._with_files(mp, tmp_path, {"0006_hand_over.sql": in_the_open})
        with pytest.raises(errors.ConfigError, match="may not be handed to another role"):
            mig.migrate(dsn, runtime_role=case.role["n"])
    dynamic = _split_function("ALTER TABLE spend OWNER TO " + sql.Identifier(g).as_string())
    with pytest.MonkeyPatch.context() as mp:
        tp._with_files(mp, tmp_path, {"0006_hand_over.sql": dynamic})
        with pytest.raises(pge.InsufficientPrivilege):
            mig.migrate(dsn, runtime_role=case.role["n"])
        case.db.execute(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(APP), sql.Identifier(g)
            )
        )
        with pytest.raises(errors.ConfigError, match="before any migration file ran"):
            mig.migrate(dsn, runtime_role=case.role["n"])


@needs_pg
@pytest.mark.real_connect
def test_control_k8_fourth_form_the_group_owns_the_schema_of_the_run_and_the_run_returns(
    case, monkeypatch, tmp_path
):
    """K8 of the ticket, fourth form (round 14, Issue 7; the reviewers named it and it was not measured before): the group
    that the migration role belongs to OWNS the schema of the run, and a file (dynamic SQL, so the text rules do not stop
    it) hands the map table `spend` to that group. The server allows it (the group owns the schema, so it may create in
    it, and the migration role is a member). MEASURED: the run returns with every file applied, a second run has nothing
    pending, and the table is owned by the group. So K8 CAN end in outcome (iii) in this form; the earlier statement
    "K8 cannot end in (iii)" held only for the three forms of the test above. This is the documented non-promise of
    ticket 1.4 (a role the migration role belongs to is part of its family); it is also the `q-p3a2-o8-schema-owner`
    behaviour: a schema owned from the start by a role outside the family is accepted (Issue 2)."""
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    g, m = case.role["g"], case.role["m"]
    case.db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(g), sql.Identifier(m)))
    case.db.execute(
        sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(APP), sql.Identifier(g))
    )
    dynamic = _split_function("ALTER TABLE spend OWNER TO " + sql.Identifier(g).as_string())
    with pytest.MonkeyPatch.context() as mp:
        tp._with_files(mp, tmp_path, {"0006_hand_over.sql": dynamic})
        applied = mig.migrate(dsn, runtime_role=case.role["n"])
        assert applied == [p.stem for p in mig._migration_files()]
        assert mig.migrate(dsn, runtime_role=case.role["n"]) == []
    owner = case.db.execute(
        "SELECT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname = 'spend'",
        (APP,),
    ).fetchone()[0]
    assert owner == g, "the table was not handed to the group: the cell tests nothing"


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("switch", [True, False], ids=["switch-on", "switch-off"])
def test_o8_a_schema_owned_outside_the_family_at_the_start_is_refused_only_with_the_switch_on(
    switch, case, monkeypatch, tmp_path
):
    """Rule O8, real server, round 15 (Issue 2). A role OUTSIDE the migration role family (`o`, nobody named it) owns the
    schema of the run before the run starts, and one new file is pending. Switch ON (the strict reading of ticket rule O8):
    `migrate` refuses, keeps nothing (the file did not run and is still pending). Switch OFF (the shipped default, which is
    LESS strict than the ticket until the lead answers q-p3a2-o8-schema-owner): the file runs and `migrate` returns.
    Killed by V102 (switch ignored). The switch is patched here, so the default is pinned elsewhere (V101 is killed by
    test_the_strict_reading_of_rule_o8_is_off_by_default)."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    shipped = [p.stem for p in mig._migration_files()]
    assert mig.migrate(dsn) == shipped  # a clean run first, as the migration role owns the schema
    outsider = case.role["o"]
    case.db.execute(
        sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(APP), sql.Identifier(outsider))
    )
    tp._with_files(
        monkeypatch, tmp_path, {"0006_o8.sql": _split_function("CREATE TABLE zz_o8 (a int)")}
    )
    monkeypatch.setattr(
        mig, "ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START", switch
    )
    if switch:
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn)
        text = str(seen.value)
        assert _kept_nothing(text), text[:500]
        assert f"{outsider} is owned by {outsider}" in text and "No file ran" in text, text[:500]
        monkeypatch.setattr(
            mig, "ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START", False
        )
        # nothing was kept: the same file is still pending and now runs
        assert mig.migrate(dsn) == ["0006_o8"]
    else:
        assert mig.migrate(dsn) == ["0006_o8"]
    assert case.db.execute("SELECT to_regclass(%s)", (f"{APP}.zz_o8",)).fetchone()[0] is not None
    assert mig.migrate(dsn) == []


# --- 7. the shipped files give each role exactly the map (ticket 7.7) --------------------------------------------------

APP = "app"  # the schema of the run in the 7.7 test and in the matrix


def _migration_login(case: Case, schema: str = APP) -> str:
    """Make the migration role of the case the way the printed SQL makes it (a plain login that may create in the
    schema and pass USAGE on) and give it a password. Returns its connection string, which uses `schema` first."""
    from hadavin_sdk.store import migrate as mig
    from tests.fixtures import migration_role as helper

    m = case.role["m"]
    case.admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(m)))
    if schema != "public":
        case.db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    printed = mig.PLAIN_MIGRATION_ROLE_SQL.replace("migration_role", m).replace(
        "<schema>", sql.Identifier(schema).as_string()
    )
    case.db.execute(printed)
    case.db.execute(
        sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
            sql.Identifier(case.db_name), sql.Identifier(m)
        )
    )
    helper.set_login_password(case.db, m)
    return helper.login_dsn(
        make_conninfo(case._dsn, dbname=case.db_name, options=f"-c search_path={schema}"), m
    )


_REFERENCES_NO_KEY = re.compile(r"^\('table', '[^']+', 'REFERENCES'\): 42830 ")


def _hand_facts(case: Case, role: str, schema: str) -> set[tuple[str, str, str]]:
    """What the hand-written table says `role` (runtime, portal or purge) may do, as oracle facts. A right on a whole
    table is also a right on each of its columns, and the oracle lists both."""
    out: set[tuple[str, str, str]] = {
        ("schema", schema, "USAGE")
    }  # `migrate` lets each role reach the schema
    for name, right in HAND_TABLE_RIGHTS[role]:
        kind = "sequence" if name.endswith("_seq_seq") else "table"
        out.add((kind, f"{schema}.{name}", right))
        if kind == "table" and right in {"SELECT", "INSERT", "UPDATE"}:
            for (col,) in case.db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s",
                (schema, name),
            ).fetchall():
                out.add(("column", f"{schema}.{name}.{col}", right))
    if role == "purge":
        for name, col in HAND_PURGE_COLUMNS:
            out.add(("column", f"{schema}.{name}.{col}", "SELECT"))
    return out


@needs_pg
@pytest.mark.real_connect
def test_the_shipped_files_give_each_role_exactly_the_map(case):
    """Ticket 7.7. In an empty case database, as a plain migration role made by the printed SQL, `migrate` runs the five
    shipped files with the three role arguments. Direction 1: each of the three roles can do every operation of the
    hand-written table. Direction 2: nothing else works for it (what a fresh role can do before the run, the baseline,
    apart), and the fresh role that stands for everyone gains nothing. A second run with no pending file gives the same
    answers."""
    from hadavin_sdk.store import migrate as mig

    # a database as it is made (not the stripped baseline of the sensitivity controls): everyone may use plpgsql
    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    roles = {"runtime": case.role["n"], "portal": case.role["t"], "purge": case.role["o"]}
    # B4 of batch 3e: direction 2 covers every schema and object of the database, but not the server-wide tablespaces and settings (`s` and `s2` hold one object of every kind,
    # `public` is the server's own, the foreign server and wrapper and the large object are the database's), and the
    # database-level rights of every role; the schemas `s` and `s2` are reachable by everyone so that their objects can be tried
    for other_schema in ("s", "s2"):
        case.db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(other_schema))
        )
    assert {"public", "s", "s2", APP} <= set(case.oracle.schemas()) | {APP}, case.oracle.schemas()
    before = {k: case.oracle.can_everywhere(case.role[k]).facts for k in "nftom"}
    applied = mig.migrate(
        dsn,
        runtime_role=roles["runtime"],
        portal_role=roles["portal"],
        purge_role=roles["purge"],
    )
    assert applied == [p.stem for p in mig._migration_files()]

    def judge(when: str) -> None:
        for kind, who in (("runtime", "n"), ("portal", "t"), ("purge", "o")):
            res = case.oracle.can_everywhere(case.role[who])
            # The one thing the oracle cannot see by behaviour here: REFERENCES on a table with no unique key (the
            # server refuses the test statement for that reason, whatever the right). Anything else it cannot see fails.
            unseen = [x for x in res.inconclusive if not _REFERENCES_NO_KEY.match(str(x))]
            assert unseen == [], f"{when}: the oracle cannot see {unseen}"
            want = _hand_facts(case, kind, APP)
            missing = want - res.facts
            assert not missing, f"{when}: {kind} cannot do {sorted(missing)}"
            extra = res.facts - want - before[who]
            assert not extra, f"{when}: {kind} can also do {sorted(extra)}"
        res = case.oracle.can_everywhere(case.role["f"])
        extra = res.facts - before["f"]
        assert not extra, f"{when}: everyone can also do {sorted(extra)}"
        assert not any(f[0] == "database" for f in res.facts), (
            f"{when}: everyone holds a database-level right: {sorted(f for f in res.facts if f[0] == 'database')}"
        )

    judge("after the first run")
    assert (
        mig.migrate(
            dsn,
            runtime_role=roles["runtime"],
            portal_role=roles["portal"],
            purge_role=roles["purge"],
        )
        == []
    )
    judge("after the second run")


@needs_pg
@pytest.mark.real_connect
def test_direction_2_sees_an_extra_right_on_an_object_outside_the_schema_of_the_run(case):
    """B4 sensitivity: a right for the fresh role on a table of ANOTHER schema, and a database-level right, are seen by the
    all-schema oracle, and the one-schema oracle of the first version of the test does not see the first of them. The
    oracle reaches every schema and the database-level rights of this database; tablespaces and server settings belong to
    the whole server, not to one database, and are not looked at."""
    case.db.execute("GRANT USAGE ON SCHEMA s TO PUBLIC")
    f = case.role["f"]
    base = case.oracle.can_everywhere(f).facts
    case.db.execute(sql.SQL("GRANT SELECT ON s.t TO {}").format(sql.Identifier(f)))
    case.db.execute(
        sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
            sql.Identifier(case.db_name), sql.Identifier(f)
        )
    )
    seen = case.oracle.can_everywhere(f).facts - base
    assert ("table", "s.t", "SELECT") in seen and ("database", "", "CREATE") in seen, sorted(seen)
    # the one-schema stand-in can fail both ways: looking at the schema that holds the planted right it DOES see it (so the
    # assert below is not true for a reason other than the oracle's reach), looking at another schema it does not
    assert ("table", "s.t", "SELECT") in case.oracle.can(f, "s").facts, (
        "the one-schema oracle must see a right in its own schema"
    )
    assert ("table", "s.t", "SELECT") not in case.oracle.can(f, "s2").facts, (
        "the one-schema oracle of the first version of the test must not see a right planted in another schema"
    )


# --- 8. seeded compositions: two or three effects in one run, each brought by its own carrier -------------------------------
COMPOSITION_SEED = 20261112
COMPOSITION_COUNT = 200
_COMPOSITION_CARRIERS = ("C1-plain-file", "C2-dynamic-sql", "C4-ledger-trigger", "C7-ledger-rule")


class _Seeded:
    """A small repeatable number generator (a linear congruential one) for the fixed seed; nothing here is secret."""

    def __init__(self, seed: int) -> None:
        self.state = seed

    def below(self, n: int) -> int:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return (self.state >> 33) % n

    def sample(self, items: tuple[str, ...], k: int) -> list[str]:
        left = list(items)
        return [left.pop(self.below(len(left))) for _ in range(k)]


# B8 of batch 3e. Written in the open (carrier C1), these five effects are refused at step 0 by the text rules ("migrations
# are inconsistent": a GRANT on a place outside the map, an ALTER DEFAULT PRIVILEGES), so a composition that holds one
# would prove nothing about the checks of the data. Measured on the first 200 compositions (log
# B-P3a2-3e-b8-probe.log): 35 of 200 were stopped at step 0, 165 reached the data checks (the first try left out O14, which a second run found: 14 more). `_compositions` never gives
# these effects to C1, so every composition reaches the data checks (the test below asserts it, through the refusal text).
_TEXT_REFUSED_IN_THE_OPEN = frozenset(
    {
        "O14-usage-with-grant-option",
        "O13-create-on-schema-other",
        "O15-create-on-schema-everyone",
        "O16-default-right-named",
        "O17-default-right-everyone",
    }
)


def _compositions() -> list[list[tuple[str, str]]]:
    """200 lists of 2 or 3 (effect id, carrier) pairs with different carriers, from a fixed seed. The repaired effect (O06)
    is left out: a composition is expected to be refused by the rule, never repaired."""
    rng = _Seeded(COMPOSITION_SEED)
    pool = [
        e[0] for e in O_EFFECTS if not e[2] and int(e[0][1:3]) <= 18
    ]  # the first 18 effects; see B8
    out = []
    for _ in range(COMPOSITION_COUNT):
        size = 2 + rng.below(2)
        carriers = rng.sample(_COMPOSITION_CARRIERS, size)
        pairs = []
        for c in carriers:
            eid = pool[rng.below(len(pool))]
            while c == "C1-plain-file" and eid in _TEXT_REFUSED_IN_THE_OPEN:
                eid = pool[
                    rng.below(len(pool))
                ]  # take another effect: this one never reaches the checks of the data
            pairs.append((eid, c))
        out.append(pairs)
    return out


def test_the_compositions_are_the_planned_200_with_different_carriers():
    comps = _compositions()
    print(f"compositions: {len(comps)} (seed {COMPOSITION_SEED})")
    assert len(comps) == COMPOSITION_COUNT == 200
    assert all(2 <= len(c) <= 3 and len({x[1] for x in c}) == len(c) for c in comps)
    assert len({tuple(c) for c in comps}) > 150, "the seed must give a wide spread"
    # B8: a plain file never carries an effect that the text rules refuse at step 0
    assert not [
        c for c in comps for e, k in c if k == "C1-plain-file" and e in _TEXT_REFUSED_IN_THE_OPEN
    ]


@needs_pg
@pytest.mark.parametrize("n", range(COMPOSITION_COUNT), ids=lambda n: f"comp{n:03d}")
def test_every_composition_of_effects_is_refused_and_keeps_nothing(n, ocell, monkeypatch, tmp_path):
    """Two or three effects, each by its own carrier and in its own file, in one run: the rule says the run is refused and
    keeps nothing (outcome i), whichever role arguments it has; no composition hides one effect behind another."""
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    ConfigError = errors.ConfigError
    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    roles = {"runtime_role": rt} if n % 2 else {}
    files = {}
    try:
        for i, (eid, carrier) in enumerate(_compositions()[n]):
            effect = next(e for e in O_EFFECTS if e[0] == eid)
            statement = _effect_text(effect, other, rt, schema)
            if carrier == "C1-plain-file":
                text = statement + ";\n"
            elif carrier == "C2-dynamic-sql":
                text = _split_function(statement).replace(
                    "hadavin_test_dyn_runner", f"hadavin_test_dyn_runner{i}"
                )
            else:
                text = _ledger_file(carrier, statement, tag=str(i))
            files[f"{6 + i:04d}_effect{i}.sql"] = text
        tp._with_files(monkeypatch, tmp_path, files)
        outcome = None
        try:
            outcome = "returned"
            mig.migrate(dsn, **roles)
        except (ConfigError, errors.AppliedNotVerifiedError) as e:
            outcome = e
        assert isinstance(outcome, ConfigError), f"{_compositions()[n]}: {outcome!r}"
        assert _kept_nothing(outcome), str(outcome)
        assert "The check after the commit" not in str(outcome)
        # B8: the refusal comes from the checks of the data, never from the text rules of step 0
        assert "migrations are inconsistent" not in str(outcome), f"{_compositions()[n]}: {outcome}"
    finally:
        _forget_default_rights(dsn)
        tp._drop_roles(other, rt)


# --- 8b. variant (O): the migration role owns the database (batch 4b) ----------------------------------------------------------
# Ticket 7.4 variants: (P) the plain fixture (the migration role owns only the schema of the run), (O) the migration role owns
# the database, (C) it holds CREATE on the database (what `_migration_login` always gives it). Under (O) a plain role can itself
# give CREATE on the database, TEMPORARY on the database or CREATE on a schema it makes, so E17, E18 and E19 are effects of the
# run and not only states made by an administrator (they stay in `X_EFFECTS` for the plain fixture). (id, effect, statement,
# whether the right is for everyone). `{n}` is the named runtime role. E19 for everyone is the server's own default and is
# not judged (ticket 6), so it has no row.
VARIANT_O_EFFECTS = [
    (
        "V17n-create-on-a-new-schema-named",
        "E17",
        "CREATE SCHEMA zz_s; GRANT CREATE ON SCHEMA zz_s TO {n}",
        False,
    ),
    (
        "V17e-create-on-a-new-schema-everyone",
        "E17",
        "CREATE SCHEMA zz_s; GRANT CREATE ON SCHEMA zz_s TO PUBLIC",
        True,
    ),
    ("V18n-create-on-the-database-named", "E18", "GRANT CREATE ON DATABASE {db} TO {n}", False),
    (
        "V18e-create-on-the-database-everyone",
        "E18",
        "GRANT CREATE ON DATABASE {db} TO PUBLIC",
        True,
    ),
    (
        "V19n-temporary-on-the-database-named",
        "E19",
        "GRANT TEMPORARY ON DATABASE {db} TO {n}",
        False,
    ),
]
VARIANT_O_CARRIERS = ("C1-plain-file", "C2-dynamic-sql")
VARIANT_O_CELLS = [
    (e[0], c, v) for e in VARIANT_O_EFFECTS for c in VARIANT_O_CARRIERS for v in O_VARIANTS
]


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("cell", VARIANT_O_CELLS, ids=["/".join(c) for c in VARIANT_O_CELLS])
def test_variant_o_the_database_owner_gives_a_right_on_the_database_or_a_new_schema(
    cell, case, monkeypatch, tmp_path
):
    """E17, E18, E19 as effects of the run when the migration role owns the database. Rule: a right for everyone is refused
    in both variants; a right of the named role is refused when the role is named and, with no role argument, nobody named
    it, so the run returns (the pinned decision of B5, like the X17, X18, X19 cells)."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    eid, carrier, variant = cell
    effect = next(e for e in VARIANT_O_EFFECTS if e[0] == eid)
    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case)
    case.db.execute(
        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
            sql.Identifier(case.db_name), sql.Identifier(case.role["m"])
        )
    )
    statement = effect[2].format(n=case.role["n"], db=sql.Identifier(case.db_name).as_string())
    text = statement + ";\n" if carrier == "C1-plain-file" else _split_function(statement)
    roles = {"runtime_role": case.role["n"]} if variant == "with-roles" else {}
    expected = "i" if effect[3] or variant == "with-roles" else "iii"
    stopped_at_step_0 = carrier == "C1-plain-file" and _text_rules_refuse(statement)
    if (
        stopped_at_step_0
    ):  # the text rules refuse it before any connection; nothing ran (counted in the CHANGELOG)
        expected = "i"
    tp._with_files(monkeypatch, tmp_path, {"0006_effect.sql": text})
    try:
        mig.migrate(dsn, **roles)
        outcome = "iii"
    except errors.ConfigError as e:
        outcome = "i"
        assert _kept_nothing(e), str(e)[:400]
        assert ("migrations are inconsistent" in str(e)) == stopped_at_step_0, str(e)[:400]
    assert outcome == expected, f"{cell}: outcome {outcome}, expected {expected}"


@needs_pg
@pytest.mark.real_connect
def test_o8_switch_on_the_public_schema_is_family_owned_only_when_the_database_owner_is_the_migration_role(
    case, monkeypatch, tmp_path
):
    """Variant (O) and rule O8 together (round 15, Issue 6). The schema of the run is `public`, which PostgreSQL 16 gives to
    the built-in role `pg_database_owner`, that is, to whoever owns the database. With the strict switch ON: while an
    administrator owns the database the schema is owned outside the family and the run is refused, keeping nothing; once the
    migration role owns the database the same schema is the family's own and the run returns. Killed by V108 (a database
    owned by a role of the family is not seen as the family's)."""
    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig

    case.db.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
    dsn = _migration_login(case, schema="public")
    monkeypatch.setattr(
        mig, "ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START", True
    )
    with pytest.raises(errors.ConfigError) as seen:
        mig.migrate(dsn)
    text = str(seen.value)
    assert _kept_nothing(text) and "pg_database_owner" in text, (
        f"an administrator-owned database makes `public` owned outside the family: the strict switch must refuse it: {text[:500]}"
    )
    case.db.execute(
        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
            sql.Identifier(case.db_name), sql.Identifier(case.role["m"])
        )
    )
    assert mig.migrate(dsn) == [p.stem for p in mig._migration_files()], (
        "the database is owned by the migration role, so `public` is the family's own and the strict switch must accept it"
    )


# --- 9. states an administrator makes before the run (carrier C12), for the kinds a plain migration role cannot make ----------
# (id, ticket effect, statements the superuser runs, statements that put the shared test database back). `{schema}` is the
# schema of the run, `{db}` the test database, `{other}` and `{rt}` the two roles of the cell, `{flag}` a role with a flag.
X_EFFECTS = [
    (
        "X17-create-on-another-schema",
        "E17",
        ["GRANT CREATE ON SCHEMA public TO {rt}"],
        ["REVOKE CREATE ON SCHEMA public FROM {rt}"],
    ),
    (
        "X18-create-on-database",
        "E18",
        ["GRANT CREATE ON DATABASE {db} TO {rt}"],
        ["REVOKE CREATE ON DATABASE {db} FROM {rt}"],
    ),
    (
        "X19-temporary-on-database",
        "E19",
        ["GRANT TEMPORARY ON DATABASE {db} TO {rt}"],
        ["REVOKE TEMPORARY ON DATABASE {db} FROM {rt}"],
    ),
    (
        "X22-large-object-for-everyone",
        "E22",
        ["SELECT lo_create(70777)", "GRANT SELECT ON LARGE OBJECT 70777 TO PUBLIC"],
        ["SELECT lo_unlink(70777)"],
    ),
    (
        "X28-named-role-owns-a-table",
        "E28",
        ["ALTER TABLE {schema}.runs OWNER TO {rt}"],
        [],
    ),
    (
        "X22n-large-object-for-a-named-role",
        "E22",
        ["SELECT lo_create(70778)", "GRANT SELECT ON LARGE OBJECT 70778 TO {rt}"],
        ["SELECT lo_unlink(70778)"],
    ),
    (
        "X28f-named-role-owns-a-function",
        "E28",
        [
            "CREATE FUNCTION {schema}.zz_of() RETURNS int LANGUAGE sql AS 'SELECT 1'",
            "ALTER FUNCTION {schema}.zz_of() OWNER TO {rt}",
        ],
        [],
    ),
    (
        "X31-built-in-role-member",
        "E31",
        ["GRANT pg_read_all_data TO {rt}"],
        ["REVOKE pg_read_all_data FROM {rt}"],
    ),
    (
        "X32-member-of-a-role-with-a-flag",
        "E32",
        ["CREATE ROLE {flag} NOLOGIN CREATEROLE", "GRANT {flag} TO {rt}"],
        [],
    ),
    ("X33-flag-on-the-named-role", "E33", ["ALTER ROLE {rt} CREATEDB"], []),
    # The "everyone" halves of E17, E18 and E36: no role argument is needed to judge them (the promise names a named role
    # AND everyone, ticket 1.3), so these two variants of the same state are both refused.
    (
        "X17e-create-on-another-schema-for-everyone",
        "E17",
        ["GRANT CREATE ON SCHEMA public TO PUBLIC"],
        ["REVOKE CREATE ON SCHEMA public FROM PUBLIC"],
    ),
    (
        "X18e-create-on-database-for-everyone",
        "E18",
        ["GRANT CREATE ON DATABASE {db} TO PUBLIC"],
        ["REVOKE CREATE ON DATABASE {db} FROM PUBLIC"],
    ),
    (
        "X36e-default-right-for-everyone-set-by-another-role",
        "E36",
        [
            "ALTER DEFAULT PRIVILEGES FOR ROLE {other} IN SCHEMA {schema} GRANT SELECT ON TABLES TO PUBLIC"
        ],
        [],
    ),
    # Batch 3e, effects of the ticket list that an administrator makes in the schema of the run (objects outside the map)
    # or in the cluster, brought by carrier C12. `{flag}` is also used as the unique part of the names of cluster objects.
    (
        "X01n-select-on-a-table-outside-the-map-named",
        "E01",
        ["CREATE TABLE {schema}.zz_t (a int)", "GRANT SELECT ON {schema}.zz_t TO {rt}"],
        [],
    ),
    (
        "X01e-select-on-a-table-outside-the-map-everyone",
        "E01",
        ["CREATE TABLE {schema}.zz_t (a int)", "GRANT SELECT ON {schema}.zz_t TO PUBLIC"],
        [],
    ),
    (
        "X01t-select-on-a-table-outside-the-map-third-role",
        "E01",
        ["CREATE TABLE {schema}.zz_t (a int)", "GRANT SELECT ON {schema}.zz_t TO {other}"],
        [],
    ),
    (
        "X06-usage-on-a-sequence-outside-the-map",
        "E06",
        ["CREATE SEQUENCE {schema}.zz_q", "GRANT USAGE ON SEQUENCE {schema}.zz_q TO {rt}"],
        [],
    ),
    (
        "X08-select-on-a-view-outside-the-map-everyone",
        "E08",
        ["CREATE VIEW {schema}.zz_v AS SELECT 1 AS a", "GRANT SELECT ON {schema}.zz_v TO PUBLIC"],
        [],
    ),
    (
        "X08m-select-on-a-materialized-view-outside-the-map-everyone",
        "E08",
        [
            "CREATE MATERIALIZED VIEW {schema}.zz_m AS SELECT 1 AS a",
            "GRANT SELECT ON {schema}.zz_m TO PUBLIC",
        ],
        [],
    ),
    (
        "X09-select-on-a-foreign-table-everyone",
        "E09",
        [
            "CREATE FOREIGN DATA WRAPPER {flag}_w",
            "CREATE SERVER {flag}_s FOREIGN DATA WRAPPER {flag}_w",
            "CREATE FOREIGN TABLE {schema}.zz_ft (a int) SERVER {flag}_s",
            "GRANT SELECT ON {schema}.zz_ft TO PUBLIC",
        ],
        [
            "DROP FOREIGN TABLE IF EXISTS {schema}.zz_ft",
            "DROP SERVER IF EXISTS {flag}_s",
            "DROP FOREIGN DATA WRAPPER IF EXISTS {flag}_w",
        ],
    ),
    (
        "X13-security-definer-function-of-another-owner-in-another-schema-for-everyone",
        "E13",
        [
            "CREATE SCHEMA {oschema}",
            "GRANT USAGE ON SCHEMA {oschema} TO PUBLIC",
            "CREATE FUNCTION {oschema}.zz_d() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
            "ALTER FUNCTION {oschema}.zz_d() OWNER TO {other}",
        ],
        ["DROP SCHEMA IF EXISTS {oschema} CASCADE"],
    ),
    (
        "X38-a-map-right-granted-by-a-grant-option-holder",
        "E38",
        [
            "GRANT DELETE ON {schema}.runs TO {other} WITH GRANT OPTION",
            "GRANT USAGE ON SCHEMA {schema} TO {other}",
            "SET ROLE {other}",
            "GRANT DELETE ON {schema}.runs TO {rt}",
            "RESET ROLE",
        ],
        [
            "REVOKE ALL ON {schema}.runs FROM {other} CASCADE",
            "REVOKE ALL ON SCHEMA {schema} FROM {other}",
        ],
    ),
    (
        "X39-a-built-in-membership-granted-by-a-createrole-role",
        "E39",
        [
            "ALTER ROLE {other} CREATEROLE",
            "GRANT pg_read_all_data TO {other} WITH ADMIN OPTION",
            "SET ROLE {other}",
            "GRANT pg_read_all_data TO {rt}",
            "RESET ROLE",
        ],
        ["REVOKE pg_read_all_data FROM {other} CASCADE", "ALTER ROLE {other} NOCREATEROLE"],
    ),
    (
        "X10-execute-on-a-function-named",
        "E10",
        [
            "CREATE FUNCTION {schema}.zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
            "GRANT EXECUTE ON FUNCTION {schema}.zz_f() TO {rt}",
        ],
        [],
    ),
    (
        "X11-function-left-callable-by-everyone",
        "E11",
        ["CREATE FUNCTION {schema}.hadavin_zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'"],
        [],
    ),
    (
        "X12-security-definer-function-in-the-schema-of-the-run",
        "E12",
        [
            "CREATE FUNCTION {schema}.zz_d() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'",
            "REVOKE ALL ON FUNCTION {schema}.zz_d() FROM PUBLIC",
        ],
        [],
    ),
    (
        "X12f-the-package-trigger-function-made-security-definer",
        "E12",
        ["ALTER FUNCTION {schema}.hadavin_audit_append_only() SECURITY DEFINER"],
        [],
    ),
    (
        "X14-execute-on-a-procedure-named",
        "E14",
        [
            "CREATE PROCEDURE {schema}.zz_p() LANGUAGE sql AS 'SELECT 1'",
            "GRANT EXECUTE ON PROCEDURE {schema}.zz_p() TO {rt}",
        ],
        [],
    ),
    (
        "X20-usage-on-a-type-named",
        "E20",
        ["CREATE TYPE {schema}.zz_ty AS (a int)", "GRANT USAGE ON TYPE {schema}.zz_ty TO {rt}"],
        [],
    ),
    (
        "X21-usage-on-a-language-named",
        "E21",
        ["GRANT USAGE ON LANGUAGE plpgsql TO {rt}"],
        ["REVOKE USAGE ON LANGUAGE plpgsql FROM {rt}"],
    ),
    (
        "X23-usage-on-a-foreign-server-named",
        "E23",
        [
            "CREATE FOREIGN DATA WRAPPER {flag}_w",
            "CREATE SERVER {flag}_s FOREIGN DATA WRAPPER {flag}_w",
            "GRANT USAGE ON FOREIGN SERVER {flag}_s TO {rt}",
        ],
        ["DROP SERVER IF EXISTS {flag}_s", "DROP FOREIGN DATA WRAPPER IF EXISTS {flag}_w"],
    ),
    (
        "X24-create-on-a-tablespace-everyone",
        "E24",
        ["GRANT CREATE ON TABLESPACE pg_default TO PUBLIC"],
        ["REVOKE CREATE ON TABLESPACE pg_default FROM PUBLIC"],
    ),
    (
        "X25-set-on-a-parameter-named",
        "E25",
        ["GRANT SET ON PARAMETER work_mem TO {rt}"],
        ["REVOKE SET ON PARAMETER work_mem FROM {rt}"],
    ),
    (
        "X29-member-of-a-group-with-rights-inheriting",
        "E29",
        [
            "CREATE ROLE {flag} NOLOGIN",
            "GRANT DELETE ON {schema}.runs TO {flag}",
            "GRANT {flag} TO {rt}",
        ],
        ["REVOKE ALL ON {schema}.runs FROM {flag}"],
    ),
    (
        "X30-member-of-a-group-with-rights-not-inheriting-but-may-switch",
        "E30",
        [
            "CREATE ROLE {flag} NOLOGIN",
            "GRANT DELETE ON {schema}.runs TO {flag}",
            "GRANT {flag} TO {rt} WITH INHERIT FALSE, SET TRUE",
        ],
        ["REVOKE ALL ON {schema}.runs FROM {flag}"],
    ),
    (
        "X36-default-right-set-by-another-role",
        "E36",
        [
            "ALTER DEFAULT PRIVILEGES FOR ROLE {other} IN SCHEMA {schema} GRANT SELECT ON TABLES TO {rt}"
        ],
        [],
    ),
]


# The effects that are about the NAMED role only (the runtime role of the run). With no role argument no role is named, so
# the role of the cell is a third role that nobody asked `migrate` to judge. DECISION (B5 of batch 3e, written up in the PR
# notes for the lead): `migrate` does NOT refuse these states (one cell each, 18 in all: see
# `test_the_pre_existing_cells_are_counted`) without role arguments, and the cells pin that. Reasons:
# (1) the promise table (ticket 1.3) and the ticket line "with no role arguments [the named roles] are empty, and the
# subject side still judges everyone" promise named roles and everyone, nothing about a third role's flags, memberships or
# database rights; (2) a refusal would judge every role of the cluster, so any database that has a superuser or a role with
# CREATEDB (every real one) would be refused whatever the arguments, because no argument names those roles and so none
# could end the refusal. The matching "everyone"
# forms (X17e, X18e, X36e) run in both variants and are refused. X28 is not in this set: a package table owned by a third
# role is refused by the owner rule (O8) in both variants.
X_NAMED_ROLE_EFFECTS = {
    "X17-create-on-another-schema",
    "X18-create-on-database",
    "X19-temporary-on-database",
    "X31-built-in-role-member",
    "X32-member-of-a-role-with-a-flag",
    "X33-flag-on-the-named-role",
    "X36-default-right-set-by-another-role",
    # batch 3e: the other named-role effects of the ticket list, made by an administrator
    "X01n-select-on-a-table-outside-the-map-named",
    "X06-usage-on-a-sequence-outside-the-map",
    "X10-execute-on-a-function-named",
    "X14-execute-on-a-procedure-named",
    "X20-usage-on-a-type-named",
    "X21-usage-on-a-language-named",
    "X23-usage-on-a-foreign-server-named",
    "X25-set-on-a-parameter-named",
    "X39-a-built-in-membership-granted-by-a-createrole-role",
    "X22n-large-object-for-a-named-role",
    "X28f-named-role-owns-a-function",
}
# Measured on PostgreSQL 16.15 (log B-P3a2-3e-xnew.log) and pinned here as NOT JUDGED, in both variants; each needs the lead
# or the owner to say whether the promise should grow (the ticket's table of promises, 1.3, is the reference):
# - X01t: a table owned by a role outside the family (made here by the administrator) with a right held by a third role (ticket
#   1.4): not judged. The promised case is different and is run on a server by
#   `test_a_third_role_right_on_a_table_the_family_owns_is_refused_with_no_role_argument`: a table the family owns, a right
#   of a third role, no role argument: refused (O1);
# - X11: a function that is not the package's, left callable by everyone (ticket 3.4 line 3): not judged, because PostgreSQL
#   gives every function EXECUTE to everyone by default, so a refusal would refuse every schema that holds any function;
# - X12: a SECURITY DEFINER function that is not the package's, which nobody but its owner may call: not judged; the package's
#   own trigger function made SECURITY DEFINER IS refused (X12f).
X_NOT_PROMISED_BOTH_VARIANTS = {
    "X01t-select-on-a-table-outside-the-map-third-role",
    "X11-function-left-callable-by-everyone",
    "X12-security-definer-function-in-the-schema-of-the-run",
}
X_WORDING_GAP: set[str] = (
    set()
)  # B6: the owner refusal now says "No file ran." too, so no cell is a gap of wording


def test_the_pre_existing_cells_are_counted():
    cells = [(e[0], v) for e in X_EFFECTS for v in O_VARIANTS]
    unnamed = [(e, v) for e, v in cells if v == "no-roles" and e in X_NAMED_ROLE_EFFECTS]
    print(
        f"pre-existing (C12) cells: {len(X_EFFECTS)} effects x 2 variants = {len(cells)}; of them {len(unnamed)} are a state of "
        f"a role nobody named (no role argument): pinned as 'returns normally', see the decision above; the other "
        f"{len(cells) - len(unnamed)} are refused with 'No file ran'; wording gaps: {sorted(X_WORDING_GAP)}"
    )
    returned = len(unnamed) + len(O_VARIANTS) * len(X_NOT_PROMISED_BOTH_VARIANTS)
    print(
        f"of the {len(cells)} cells, {returned} return normally (pinned: {len(unnamed)} named-role states with no role argument and {len(O_VARIANTS) * len(X_NOT_PROMISED_BOTH_VARIANTS)} not-judged states) and {len(cells) - returned} are refused"
    )
    assert (len(X_EFFECTS), len(cells), len(unnamed), returned) == (36, 72, 18, 24)
    assert len({e[0] for e in X_EFFECTS}) == 36
    assert len(X_NAMED_ROLE_EFFECTS) == 18 and X_NAMED_ROLE_EFFECTS <= {e[0] for e in X_EFFECTS}
    assert X_NOT_PROMISED_BOTH_VARIANTS <= {e[0] for e in X_EFFECTS}
    assert not X_NOT_PROMISED_BOTH_VARIANTS & X_NAMED_ROLE_EFFECTS
    assert X_WORDING_GAP == set()


@needs_pg
def test_a_third_role_right_on_a_table_the_family_owns_is_refused_with_no_role_argument(ocell):
    """The promised case that X01t is not (batch 4b, on a real server): the table is owned by the family (the migration
    files made it), a third role that no argument names holds a right on it, and `migrate` is called with no role argument.
    It is refused before any file runs (rule O1) and names the table and the role. Killed by V104 (the third-role refusal
    removed). The case beside it, the same right on a table that a role OUTSIDE the family owns, is the pre-existing cell
    X01t (`test_a_state_made_before_the_run_is_refused_and_no_file_runs`): not judged, the run returns; it is not part of
    this test."""
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    try:
        assert mig.migrate(dsn) == tp.REAL
        with mig.connect(dsn) as db:  # as the owner: the right is given by the family's own login
            db.execute(
                sql.SQL("GRANT SELECT ON {}.runs TO {}").format(
                    sql.Identifier(schema), sql.Identifier(other)
                )
            )
        with pytest.raises(errors.ConfigError) as seen:
            mig.migrate(dsn)
        text = str(seen.value)
        assert "No file ran" in text and other in text and f"{schema}.runs" in text, (
            f"the refusal must name the third role {other} and the table {schema}.runs: {text[:500]}"
        )
    finally:
        tp._drop_roles(other, rt)


X_CELLS = [(e, v) for e in X_EFFECTS for v in O_VARIANTS]


@needs_pg
@pytest.mark.parametrize("effect, variant", X_CELLS, ids=[f"{e[0]}/{v}" for e, v in X_CELLS])
def test_a_state_made_before_the_run_is_refused_and_no_file_runs(effect, variant, ocell):
    """Carrier C12 for the effects only a superuser can make: the run goes through once, the administrator makes the
    state, and the next `migrate` (with or without the role arguments) is refused before any file runs and keeps nothing.
    The rule gives (i) for every one of them; the cell ends the shared database as it found it."""
    import uuid

    from hadavin_sdk import errors
    from hadavin_sdk.store import migrate as mig
    from tests import test_migration_postgres as tp

    eid, _, make, undo = effect
    dsn, schema = ocell
    other = "hadavin_test_mx_" + uuid.uuid4().hex[:8]
    rt = "hadavin_test_mxr_" + uuid.uuid4().hex[:8]
    flag = "hadavin_test_mxf_" + uuid.uuid4().hex[:8]
    tp._create_roles(other, rt)
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    with psycopg.connect(DSN, autocommit=True) as admin:
        db_name = admin.execute("SELECT current_database()").fetchone()[0]
    names = {
        "schema": sql.Identifier(schema).as_string(),
        "db": sql.Identifier(db_name).as_string(),
    }
    names.update(other=other, rt=rt, flag=flag, oschema=sql.Identifier(schema + "_o").as_string())
    outcome = None
    try:
        assert mig.migrate(dsn, **roles) == tp.REAL
        with psycopg.connect(DSN, autocommit=True) as admin:
            for statement in make:
                admin.execute(statement.format(**names))
        try:
            outcome = "returned"
            mig.migrate(dsn, **roles)
        except (errors.ConfigError, errors.AppliedNotVerifiedError) as e:
            outcome = e
        if eid in X_NOT_PROMISED_BOTH_VARIANTS:
            assert outcome == "returned", (
                f"{eid}/{variant}: not promised, so not refused: {outcome!r}"
            )
        elif variant == "no-roles" and eid in X_NAMED_ROLE_EFFECTS:
            assert outcome == "returned", (
                f"{eid}/{variant}: a role nobody named is not judged: {outcome!r}"
            )
        else:
            assert isinstance(outcome, errors.ConfigError), f"{eid}/{variant}: {outcome!r}"
            assert "No file ran" in str(outcome), str(outcome)
            assert _kept_nothing(outcome), str(outcome)
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            for statement in undo:
                admin.execute(statement.format(**names))
            _drop_flag_role(admin, flag)
        tp._drop_roles(other, rt)


def _drop_flag_role(admin, flag: str) -> None:
    admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(flag)))
