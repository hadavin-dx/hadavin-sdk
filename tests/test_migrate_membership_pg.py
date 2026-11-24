"""`migrate` refuses a role it was not told about that can BECOME a named role through a role membership (review
round 2, MAJOR-3), and resolves its money lookups in the schema the store uses (NIT-2).

The per-role checks follow inherited rights only (`has_function_privilege`, `has_table_privilege`). A member WITHOUT
inheritance holds nothing today and can `SET ROLE` to the named role; from PostgreSQL 16 a SET-only member can too,
the holder of the ADMIN option can grant the role to itself, and a member of such a role gets there through the
chain. Every named role that holds money, cap or stop rights is walked (caps, runtime, portal, purge, release; the
reset role is walked by the stop check, same query). Real PostgreSQL, throwaway schema and logins. Needs
HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from tests.test_migrate_hazard_pg import _made_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

KINDS = ["caps", "runtime", "portal", "purge", "release"]


@pytest.fixture(name="w")
def world():
    yield from _made_world()


def _v16(w) -> bool:
    return w.run("SELECT current_setting('server_version_num')::int >= 160000")[0][0]


def _named(w, kind: str) -> tuple[str, dict]:
    """(the named role of that kind, the extra migrate arguments it needs). The world has no release role: make one."""
    if kind == "release":
        role = w.new_role("rl")
        return role, {"release_role": role}
    return getattr(w, kind), {}


def _refusal(w, **kw) -> str:
    with pytest.raises(ConfigError) as caught:
        w.migrate(**kw)
    return str(caught.value)


def _line(other: str, kind: str, role: str) -> str:
    return f"role {other} (not named in this command) can become the {kind} role {role}"


def _can_set_role(w, login: str, role: str) -> bool:
    with w.as_(login) as db:
        try:
            db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))
        except errors.InsufficientPrivilege:
            return False
        return db.execute("SELECT current_user").fetchone()[0] == role


@pytest.mark.parametrize("kind", KINDS)
def test_a_member_without_inheritance_of_a_named_role_is_refused_by_name(w, kind):
    role, kw = _named(w, kind)
    assert w.migrate(**kw) == []
    other = w.new_role("mb", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", role, other)
    assert _can_set_role(
        w, other, role
    )  # the path is real: it holds nothing, and becomes the named role
    text = _refusal(w, **kw)
    assert _line(other, kind, role) in text and "Revoke the membership" in text
    w.grant("REVOKE {} FROM {}", role, other)
    assert w.migrate(**kw) == []


def test_the_member_without_inheritance_of_the_caps_role_could_set_a_cap(w):
    """The scenario of the finding, end to end: the unnamed login holds no EXECUTE, becomes the caps role, sets a cap."""
    other = w.new_role("mc", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", w.caps, other)
    set_cap = "hadavin_set_cap(text, numeric, numeric, text)"
    assert not w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (other, set_cap))[0][0]
    with w.as_(other) as db:
        db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(w.caps)))
        db.execute("SELECT hadavin_set_cap('agent-x', 1, 2, 'user:x')")
    assert w.run("SELECT count(*) FROM hadavin_caps WHERE agent_id = 'agent-x'")[0][0] == 1
    assert _line(other, "caps", w.caps) in _refusal(w)


@pytest.mark.parametrize("kind", KINDS)
def test_a_set_only_member_of_a_named_role_is_refused_by_name(w, kind):
    if not _v16(w):
        pytest.skip(
            "the SET option of a membership exists from PostgreSQL 16; below 16 every membership can SET ROLE"
        )
    role, kw = _named(w, kind)
    other = w.new_role("so")
    w.grant("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE", role, other)
    assert _can_set_role(w, other, role)
    assert _line(other, kind, role) in _refusal(w, **kw)
    w.grant("REVOKE {} FROM {}", role, other)
    assert w.migrate(**kw) == []


@pytest.mark.parametrize("kind", KINDS)
def test_a_member_of_a_member_is_refused_and_both_are_named(w, kind):
    role, kw = _named(w, kind)
    middle, far = w.new_role("m1", "NOLOGIN NOINHERIT"), w.new_role("m2", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", role, middle)
    w.grant("GRANT {} TO {}", middle, far)
    text = _refusal(w, **kw)
    assert _line(middle, kind, role) in text and _line(far, kind, role) in text
    w.grant(
        "REVOKE {} FROM {}", role, middle
    )  # the chain is cut at the named role: nobody reaches it
    assert w.migrate(**kw) == []


@pytest.mark.parametrize("kind", KINDS)
def test_the_holder_of_the_admin_option_on_a_named_role_is_refused_by_name(w, kind):
    """It can grant the named role to itself (or to anyone). From 16 the option stands alone (no INHERIT, no SET)."""
    role, kw = _named(w, kind)
    other = w.new_role("ad", "LOGIN NOINHERIT")
    if _v16(w):
        w.grant("GRANT {} TO {} WITH ADMIN TRUE, INHERIT FALSE, SET FALSE", role, other)
        assert not _can_set_role(w, other, role)  # not a member that can act today: only the option
    else:
        w.grant("GRANT {} TO {} WITH ADMIN OPTION", role, other)
    assert _line(other, kind, role) in _refusal(w, **kw)
    w.grant("REVOKE {} FROM {}", role, other)
    assert w.migrate(**kw) == []


def test_a_member_of_the_reset_role_keeps_the_stop_refusal_text(w):
    """The reset role is walked by the stop check (the same query), which runs first and names the member."""
    other = w.new_role("rm", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", w.reset, other)
    text = _refusal(w)
    assert "roles other than the reset role could clear a stop" in text and other in text


def test_the_walk_of_a_named_role_does_not_list_holders_of_stop_rights(w):
    """Without `stop_grants` the only seed is the role asked about: the reset role (it holds UPDATE on kill_switch)
    is not a role that can become the caps role."""
    with w.admin() as db:
        assert mig._can_become(db, w.caps, stop_grants=False) == []
        assert w.reset not in mig._can_become(db, w.runtime, stop_grants=False)


def test_a_temporary_table_does_not_hide_a_writer_of_a_money_table(w):
    """NIT-2: a temporary relation is searched before the schema. The writer check must read OUR `spend`."""
    writer = w.new_role("tw", "NOLOGIN")
    w.grant("GRANT INSERT ON spend TO {}", writer)
    with psycopg.connect(w.scoped, autocommit=True) as db:
        assert f"role {writer} can INSERT spend" in mig._money_table_writers(db)
        db.execute("CREATE TEMP TABLE spend (x int)")
        shadow = db.execute(
            "SELECT relnamespace::regnamespace::text FROM pg_class WHERE oid = to_regclass('spend')"
        ).fetchone()[0]
        assert shadow.startswith("pg_temp")  # the bare name now resolves to the temporary table
        assert f"role {writer} can INSERT spend" in mig._money_table_writers(db)


def test_the_executor_check_reads_the_function_of_the_stores_schema(w):
    """NIT-2, the function half, the positive side: an unnamed executor of OUR function is still found with
    temporary objects and a later schema in the path. The unqualified lookup is caught by the next test."""
    runner = w.new_role("tx", "NOLOGIN")
    set_cap = "hadavin_set_cap(text, numeric, numeric, text)"
    w.grant(f"GRANT EXECUTE ON FUNCTION {set_cap} TO {{}}", runner)
    w.new_schema("lt")
    with psycopg.connect(w.scoped, autocommit=True) as db:
        db.execute(f"SET search_path = {w.schema}, sb_lt_{w.sfx}")
        db.execute("CREATE TEMP TABLE hadavin_set_cap (x int)")
        found = mig._unnamed_money_executors(db, [w.runtime, w.portal, w.purge, w.reset, w.caps])
    assert f"role {runner} (not named in this command) can run {set_cap}" in found


HOLDS = "hadavin_expired_holds(integer)"


def test_the_executor_check_skips_a_function_this_schema_lacks_and_a_later_schema_has(w):
    """Review round 3, MINOR 2: the function is missing in the store's schema (a database that holds an earlier 0011
    draft) and a later schema of the search_path holds one with the same signature, runnable by PUBLIC like every new
    function. A bare lookup resolves to THAT function and reports its executors (a false refusal that names another
    application's function); the qualified lookup finds nothing and skips."""
    w.new_schema("lf")
    decoy = f"sb_lf_{w.sfx}"
    w.do(f"CREATE FUNCTION {decoy}.{HOLDS} RETURNS integer LANGUAGE sql AS 'SELECT 1'")
    w.do(f"DROP FUNCTION {w.schema}.{HOLDS}")
    both = make_conninfo(w.dsn, options=f"-c search_path={w.schema},{decoy}")
    with psycopg.connect(both, autocommit=True) as db:
        found_in = db.execute(
            "SELECT n.nspname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
            "WHERE p.oid = to_regprocedure(%s)",
            (HOLDS,),
        ).fetchone()[0]
        assert found_in == decoy  # the premise: the bare name leads to the other schema
        found = mig._unnamed_money_executors(db, [w.runtime, w.portal, w.purge, w.reset, w.caps])
    assert not [line for line in found if "hadavin_expired_holds" in line], found


def creator_scenario(w):
    """Review round 3, MINOR 1. From PostgreSQL 16 a login with CREATEROLE that is not a superuser gets the ADMIN
    option on every role it creates, granted by the bootstrap superuser. migrate refuses it and says what to do; the
    creating login cannot end the refusal itself; a superuser can."""
    creator = w.new_role("mk", "LOGIN CREATEROLE")
    made = f"sb_mr_{w.sfx}"
    as_creator = w.dsn_of(creator, w.dsn)
    with psycopg.connect(as_creator, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(made)))
    w.roles.insert(0, made)  # dropped before its creator
    text = _refusal(w, release_role=made)
    assert _line(creator, "release", made) in text
    assert "only a superuser can take it away" in text
    assert "create them again as the login that owns the tables" in text
    superuser = w.run("SELECT current_user")[0][0]
    revoke = sql.SQL("REVOKE ADMIN OPTION FOR {} FROM {}").format(
        sql.Identifier(made), sql.Identifier(creator)
    )
    with psycopg.connect(as_creator, autocommit=True) as db:
        db.execute(revoke)  # no error and no effect: the grant is not the creator's
        with pytest.raises(errors.InsufficientPrivilege):
            db.execute(revoke + sql.SQL(" GRANTED BY {}").format(sql.Identifier(superuser)))
    assert _line(creator, "release", made) in _refusal(w, release_role=made)
    w.grant("REVOKE ADMIN OPTION FOR {} FROM {}", made, creator)  # the superuser's REVOKE
    assert w.migrate(release_role=made) == []


def test_a_named_role_made_by_a_createrole_login_is_refused_and_only_a_superuser_can_end_it(w):
    if not _v16(w):
        pytest.skip(
            "from PostgreSQL 16 the creating login holds the ADMIN option on the role it made; below 16 no such grant exists"
        )
    creator_scenario(w)


def test_named_roles_made_by_the_login_that_owns_the_tables_pass_without_a_superuser(w):
    """The documented way on a managed database service: one login without superuser rights owns the schema and the
    tables and creates the six named roles. It holds the ADMIN option on each and is not refused: the owner of the
    tables is outside the membership walk."""
    if not _v16(w):
        pytest.skip(
            "from PostgreSQL 16 the creating login holds the ADMIN option on the role it made; below 16 no such grant exists"
        )
    owner = w.new_role("ow", "LOGIN CREATEROLE")
    schema = f"sb_ow_{w.sfx}"
    w.do(f"CREATE SCHEMA {schema} AUTHORIZATION {owner}")
    w.schemas.append(schema)
    kinds = ("runtime", "portal", "purge", "reset", "release", "caps")
    names = {f"{k}_role": f"sb_o{k[:3]}_{w.sfx}" for k in kinds}
    with psycopg.connect(w.dsn_of(owner, w.dsn), autocommit=True) as db:
        for name in names.values():
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
            w.roles.insert(0, name)  # dropped before the owner
        assert not db.execute(
            "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"
        ).fetchone()[0]
    as_owner = make_conninfo(w.dsn, user=owner, options=f"-c search_path={schema}")
    assert "0011_money_definer" in mig.migrate(as_owner, **names)
    assert mig.migrate(as_owner, **names) == []
