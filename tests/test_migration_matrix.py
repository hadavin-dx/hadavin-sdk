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
]
# C10 (ticket 7.4): the object lives in ANOTHER schema that the migration role owns (made by the superuser and handed to the
# plain role; everyone may use it, so the rights are judged and not the schema's USAGE). `{o}` is that schema. Only the
# effects of objects outside the map exist there: a map table lives in the schema of the run only (empty by logic).
C10_STATEMENTS = {
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
    "O19-select-on-a-table-outside-the-map-named",
    "O21-usage-on-a-sequence-outside-the-map-named",
    "O23-execute-on-a-function-named",
    "O26-execute-on-a-procedure-named",
    "O27-usage-on-a-type-named",
}
C10_EVERYONE = {
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


def _cells() -> list[tuple[str, str, str]]:
    return [
        (e[0], c, v)
        for e in O_EFFECTS
        for c in O_CARRIERS
        for v in O_VARIANTS
        if c != "C10-another-schema"
        or e[0] in C10_STATEMENTS  # a map table lives only in the schema of the run
    ]


# What the ticket plans (7.3, 7.4) and this matrix does not build, written as tables so that the count test prints them and
# nobody reads the matrix as the full one. Each line says why. (Batch 3e built every effect but E27 and the carriers C3, C5,
# C6b, C10 and C11; the carriers below are the ones still missing, with the reason a cell cannot or has not been built.)
# Table 1: effects that a plain migration role cannot make (the server refuses it, ticket fact 20), so they exist under the
# carrier C12 only, in the table of pre-existing states `X_EFFECTS` (36 rows x 2 variants).
O_SERVER_REFUSED_EFFECTS = {
    "E09 E13 E22 E23 E24 E25": "a foreign table or server, a function of another owner, a large object, a tablespace, a parameter: the plain role cannot grant on them",
    "E17 E18 E19 E21 E28-schema": "CREATE on another schema or the database, TEMPORARY on the database, USAGE on a language, a schema owned by another role: the plain role holds no right to give them",
    "E29 E30 E31 E32 E33 E36 E38 E39": "memberships, role flags, a default right set by another role, a right granted by another role: CREATEROLE or another login is needed",
}
# Table 2: pairs that are empty by logic. A carrier that runs inside the run (C1 to C4, C6, C7, C11) acts as the plain
# migration role, so every effect of table 1 is empty under it.
O_EMPTY_BY_LOGIC = "every effect of table 1 x every carrier but C12 (a plain migration role cannot do it, so no file, trigger, rule or function can)"
# Table 3: not promised, or a control rather than an effect.
O_NOT_PROMISED = {
    "E27": "a table owned by a group with a second member: a control, not a promise (control K7)",
    "X01t X11 X12": "a right of a third role on a table outside the map; a function of another application left callable by everyone; a SECURITY DEFINER function of another application: pinned as returning normally in both variants",
}
# The carriers still missing and the controls still missing, each with the reason; the lead decides the next round.
O_NOT_BUILT_CARRIERS = {
    "C8": "an object made a member of an extension the migration role owns: needs a trusted extension and CREATE on the database for a plain role (ticket fact 14)",
    "C9": "a login that differs from the role (`options=-c role=M`): needs a second login; not built in batch 3e (time box)",
    "C13": "move a map table to another schema and recreate it: not built in batch 3e (time box)",
}
O_NOT_BUILT_CONTROLS = {
    "K2": "the schema of the run is `public` with the server's own access list: needs a database of its own (a `case`)",
    "K10": "every relation kind with its row type (fact 33): not built in batch 3e (time box)",
}


def test_the_matrix_has_exactly_the_planned_cells():
    cells = _cells()
    controls = (
        len(O_CONTROLS) + len(O_CONTROLS_BUILT) * len(O_VARIANTS) + 2 + 4
    )  # K1, K3/K11/K12 x 2, K4, K9, and the four real-login controls K5, K6, K7, K8 (K8 pinned as three refusals)
    total = len(cells) + controls
    print(
        f"matrix cells: {len(O_EFFECTS)} effects x {len(O_CARRIERS)} carriers x {len(O_VARIANTS)} variants minus the "
        f"{len(O_EFFECTS) - len(C10_STATEMENTS)} map-table effects under C10 = {len(cells)}; C6b {len(C6B_CELLS)}; "
        f"pre-existing (C12, superuser) {len(X_EFFECTS)} x 2 = {2 * len(X_EFFECTS)}; controls {controls}; "
        f"total {total + len(C6B_CELLS) + 2 * len(X_EFFECTS)}; compositions {COMPOSITION_COUNT} (seed {COMPOSITION_SEED})"
    )
    for ids, why in O_SERVER_REFUSED_EFFECTS.items():
        print(f"table 1, server refuses it to a plain role, C12 only, effects {ids}: {why}")
    print(f"table 2, empty by logic: {O_EMPTY_BY_LOGIC}")
    for ids, why in O_NOT_PROMISED.items():
        print(f"table 3, not promised, {ids}: {why}")
    for ids, why in O_NOT_BUILT_CARRIERS.items():
        print(f"NOT BUILT, carrier {ids}: {why}")
    for ids, why in O_NOT_BUILT_CONTROLS.items():
        print(f"NOT BUILT, control {ids}: {why}")
    assert (len(O_EFFECTS), len(O_CARRIERS), len(O_VARIANTS), len(C10_STATEMENTS)) == (27, 10, 2, 9)
    assert len(cells) == 27 * 10 * 2 - (27 - 9) * 2 == 504 and len(set(cells)) == 504
    assert len(C6B_CELLS) == 54
    assert controls == 14 and len(O_CONTROLS_BUILT) == 3 and total == 518
    assert len(X_EFFECTS) == 36
    assert [e[0] for e in O_EFFECTS] == sorted(e[0] for e in O_EFFECTS)
    # no row of the ticket is left out unlisted: the ids built (generated, or pre-existing under C12) plus the ids of the
    # tables cover E01 to E39
    planned = {f"E{n:02d}" for n in range(1, 40)}
    generated = {
        "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E10", "E11", "E12", "E14", "E15", "E16", "E20",
        "E26", "E34", "E35", "E37",
    }  # fmt: skip
    pre_existing = {e[1] for e in X_EFFECTS}
    listed = {w.split("-")[0] for key in O_SERVER_REFUSED_EFFECTS for w in key.split()} | {"E27"}
    assert planned - generated - pre_existing - listed == set(), sorted(
        planned - generated - pre_existing - listed
    )
    assert generated <= planned and pre_existing <= planned


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


# C3: a function whose body is a string of SQL (language sql) runs the effect; the file is the function and the call. The
# body is written in the open (an SQL body cannot join pieces), so, like C1, the text rules may stop it at step 0.
# C11: a temporary table named like a catalog table is made first (the run must read the catalogs by their full names).
_WRITTEN_IN_THE_OPEN = (
    "C1-plain-file",
    "C3-sql-function",
    "C11-temporary-table-named-like-a-catalog-table",
)
# The text rules refuse a temporary table written in the open, so it is made by dynamic SQL with the words split.
_TEMP_LIKE_CATALOG = (
    "CREATE OR REPLACE FUNCTION hadavin_test_mktemp() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
    "EXECUTE 'CRE' || 'ATE TEM' || 'PORARY TAB' || 'LE pg_class (oid int, relname text, relacl text)'; END $$;\n"
    "SELECT hadavin_test_mktemp();\n"
)


def _sql_function(statement: str) -> str:
    return (
        f"CREATE OR REPLACE FUNCTION hadavin_test_sqlfn() RETURNS void LANGUAGE sql AS $$ {statement} $$;\n"
        "SELECT hadavin_test_sqlfn();\n"
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
    statement = effect[1].format(other=other, rt=rt, schema=schema)
    repaired = effect[2] and variant == "with-roles"
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
                {"0006_temp.sql": _TEMP_LIKE_CATALOG, "0007_effect.sql": statement + ";\n"},
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
            if carrier.startswith("C12"):
                assert "No file ran" in str(e), str(e)
        # step 4 repairs only what exists when it runs; a deferred trigger acts after it
        expected = "iii" if repaired and carrier != "C6-deferred-ledger-trigger" else "i"
        if carrier == "C10-another-schema":
            expected = (
                "i"
                if eid in C10_EVERYONE or (eid in C10_NAMED and variant == "with-roles")
                else "iii"  # not promised, or a named role that no argument names (the decision of B5)
            )
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


@needs_pg
@pytest.mark.parametrize(
    "effect_id, variant", C6B_CELLS, ids=[f"{e}/C6b/{v}" for e, v in C6B_CELLS]
)
def test_c6b_a_trigger_that_defers_itself_again_is_applied_and_reported(
    effect_id, variant, ocell, monkeypatch, tmp_path
):
    """Outcome (ii) for every effect: the run returns what it applied and reports the excess it found afterwards
    (`AppliedNotVerifiedError`), never a silent return and never a refusal that keeps nothing (the effect is already
    committed when it is found)."""
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
        _make_the_redefer_parts(schema, effect[1].format(other=other, rt=rt, schema=schema))
        tp._with_files(monkeypatch, tmp_path, _redefer_files(effect[1]))
        with pytest.raises(errors.AppliedNotVerifiedError):
            mig.migrate(dsn, **roles)
    finally:
        _forget_default_rights(dsn)
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
def test_control_k8_cannot_end_in_iii_the_hand_over_is_refused_in_every_form(
    case, monkeypatch, tmp_path
):
    """K8 of the ticket (a file hands a map table to a group the migration role belongs to, "allowed since O5 is struck") does
    not exist as an outcome (iii) on this head; three forms, each measured: (1) written in the open, the text rules refuse it at
    step 0 ("an object may not be handed to another role by a migration file"); (2) made by dynamic SQL, the server refuses it
    because the new owner holds no CREATE on the schema (a file error, 42501, raised as it is); (3) the same, after an
    administrator gave the group CREATE on the schema, the run refuses the state before any file runs. The control is therefore
    pinned as three refusals; the lead or the owner decides whether the ticket line is struck."""
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


# --- 7. the shipped files give each role exactly the map (ticket 7.7) --------------------------------------------------

APP = "app"  # the schema of the run in the 7.7 test and in the matrix


def _migration_login(case: Case, schema: str = APP) -> str:
    """Make the migration role of the case the way the printed SQL makes it (a plain login that may create in the
    schema and pass USAGE on) and give it a password. Returns its connection string, which uses `schema` first."""
    from hadavin_sdk.store import migrate as mig
    from tests.fixtures import migration_role as helper

    m = case.role["m"]
    case.admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(m)))
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
    # B4 of batch 3e: direction 2 covers every schema and object of the database (`s` and `s2` hold one object of every kind,
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
    all-schema oracle, and the one-schema oracle of the first version of the test does not see the first of them."""
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
    one_schema = case.oracle.can(
        f, "s2"
    ).facts  # a stand-in for the one schema the old test looked at
    assert ("table", "s.t", "SELECT") not in one_schema


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
            statement = effect[1].format(other=other, rt=rt, schema=schema)
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
# notes for the lead): `migrate` does NOT refuse these seven states without role arguments, and the cells pin that. Reasons:
# (1) the promise table (ticket 1.3) and the ticket line "with no role arguments [the named roles] are empty, and the
# subject side still judges everyone" promise named roles and everyone, nothing about a third role's flags, memberships or
# database rights; (2) a refusal would judge every role of the cluster, so any database that has a superuser or a role with
# CREATEDB (every real one) would be refused for ever, with no role argument that could end it. The matching "everyone"
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
# Measured on PostgreSQL 16.15 (log B-P3a2-3e-xnew.log) and pinned here as NOT PROMISED, in both variants; each needs the
# lead or the owner to say whether the promise should grow (the ticket's table of promises, 1.3, is the reference):
# - a right of a THIRD role (one that no argument names) on a table outside the map (E01 third role): rights of a role
#   nobody named are not promised;
# - a function left callable by everyone that is not a function of the package (X11), and a SECURITY DEFINER function that is
#   not a function of the package (X12): PostgreSQL gives every function EXECUTE to everyone by default, so a refusal would
#   refuse every schema that holds any function; the package's own trigger function made SECURITY DEFINER IS refused (X12f).
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
    assert (len(X_EFFECTS), len(cells), len(unnamed)) == (36, 72, 18)
    assert len({e[0] for e in X_EFFECTS}) == 36
    assert len(X_NAMED_ROLE_EFFECTS) == 18 and X_NAMED_ROLE_EFFECTS <= {e[0] for e in X_EFFECTS}
    assert X_NOT_PROMISED_BOTH_VARIANTS <= {e[0] for e in X_EFFECTS}
    assert not X_NOT_PROMISED_BOTH_VARIANTS & X_NAMED_ROLE_EFFECTS
    assert X_WORDING_GAP == set()


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
