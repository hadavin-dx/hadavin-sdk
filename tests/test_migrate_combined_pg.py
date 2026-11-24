"""Fixes on the combined branch (review round 3 of lead-b-migrate, MINOR 5 and MINOR 3).

MINOR 5: `migrate` refuses at its start when a name it knows (the ledger, a relation of the grant map, a `hadavin_*`
function) resolves outside `current_schema()`: this schema lacks the object and another schema of the search_path has
one of that name. Before, a bare lookup read the other schema's object and a migration file or `_seed_limits` could
change it.

MINOR 3: a database that applied an EARLIER draft of 0011 (the file as it was at git ref 2cadbb3b0, kept as
`fixtures/0011_money_definer_draft_2cadbb3b0.sql`) has no `hadavin_expired_holds`. While the draft warning is open the
warning names the missing function and the command; once the changed file is accepted, migrate refuses by name.

Real PostgreSQL, throwaway schemas and logins. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from tests.test_migrate_hazard_pg import _made_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

HOLDS = "hadavin_expired_holds(integer)"
DRAFT = Path(__file__).parent / "fixtures" / "0011_money_definer_draft_2cadbb3b0.sql"
ELSEWHERE = "names of the store resolve outside the schema this connection uses"


@pytest.fixture(name="w")
def world():
    yield from _made_world()


def _roles(w) -> dict:
    return {
        "runtime_role": w.runtime,
        "portal_role": w.portal,
        "purge_role": w.purge,
        "reset_role": w.reset,
        "caps_role": w.caps,
    }


def _path(w, *schemas: str) -> str:
    return make_conninfo(w.dsn, options="-c search_path=" + ",".join(schemas))


def _decoy(w, part: str) -> str:
    w.new_schema(part)
    return f"sb_{part}_{w.sfx}"


def _relations_in(w, schema: str) -> int:
    return w.run(
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s",
        (schema,),
    )[0][0]


def _refused(dsn: str, **kw) -> str:
    with pytest.raises(ConfigError) as caught:
        mig.migrate(dsn, **kw)
    return str(caught.value)


# --- MINOR 5: one early refusal for a known name that resolves into another schema -----------------------------------


def decoy_function_later_scenario(w):
    """Our schema lacks the function, a LATER schema of the path has the same signature: refused, the decoy untouched
    (a bare lookup would pin, grant on and report the decoy's function)."""
    decoy = _decoy(w, "dl")
    w.do(
        f"CREATE FUNCTION {decoy}.{HOLDS} RETURNS integer LANGUAGE sql AS 'SELECT 1'"
    )  # names are ours: lower-case hex
    w.do(f"DROP FUNCTION {w.schema}.{HOLDS}")
    before = w.run(
        "SELECT proacl::text, proconfig::text FROM pg_proc WHERE oid = %s::regprocedure",
        (f"{decoy}.{HOLDS}",),
    )
    text = _refused(_path(w, w.schema, decoy), **_roles(w))
    assert ELSEWHERE in text and HOLDS in text and "Nothing was changed" in text
    assert (
        w.run(
            "SELECT proacl::text, proconfig::text FROM pg_proc WHERE oid = %s::regprocedure",
            (f"{decoy}.{HOLDS}",),
        )
        == before
    )


def decoy_table_later_scenario(w):
    """The same for a relation: `hadavin_limits` is missing here and a later schema has a table of that name. A bare
    `INSERT INTO hadavin_limits` would write our limits into the other schema's table."""
    decoy = _decoy(w, "dt")
    w.do(f"CREATE TABLE {decoy}.hadavin_limits (name TEXT PRIMARY KEY, value NUMERIC)")
    w.do(f"DROP TABLE {w.schema}.hadavin_limits")
    text = _refused(_path(w, w.schema, decoy), **_roles(w))
    assert ELSEWHERE in text and "hadavin_limits" in text
    assert (
        w.run(sql.SQL("SELECT count(*) FROM {}.hadavin_limits").format(sql.Identifier(decoy)))[0][0]
        == 0
    )


def decoy_earlier_scenario(w):
    """An EARLIER schema of the path that holds nothing of ours is `current_schema()`; every bare name still finds the
    install of the later schema. Refused before the ledger is created: nothing is made in the earlier schema."""
    decoy = _decoy(w, "de")
    text = _refused(_path(w, decoy, w.schema), **_roles(w))
    assert ELSEWHERE in text and "schema_migrations" in text and repr(decoy) in text
    assert _relations_in(w, decoy) == 0


def test_a_function_missing_here_and_present_in_a_later_schema_is_refused_at_the_start(w):
    decoy_function_later_scenario(w)


def test_a_table_missing_here_and_present_in_a_later_schema_is_refused_at_the_start(w):
    decoy_table_later_scenario(w)


def test_an_earlier_schema_without_the_store_is_refused_and_nothing_is_created_in_it(w):
    decoy_earlier_scenario(w)


def test_a_later_schema_is_no_refusal_while_every_name_resolves_here(w):
    """Not a false refusal: the later schema holds objects of our names, and so does ours (ours win)."""
    decoy = _decoy(w, "ok")
    w.do(f"CREATE TABLE {decoy}.spend (x INT)")
    w.do(f"CREATE FUNCTION {decoy}.{HOLDS} RETURNS integer LANGUAGE sql AS 'SELECT 1'")
    assert mig.migrate(_path(w, w.schema, decoy), **_roles(w)) == []


def test_a_first_install_into_an_empty_schema_passes_the_early_check(w):
    fresh = w.new_schema("fi")
    assert "0011_money_definer" in mig.migrate(fresh, no_roles=True)


# --- MINOR 3: a database that holds an earlier draft of 0011 -----------------------------------------------------------


def _install_with_the_earlier_0011_draft(dsn: str) -> None:
    """By hand, what a migrate of that time did: every file as it is now, 0011 as it was at 2cadbb3b0, and a ledger row
    with the checksum of what ran."""
    with psycopg.connect(dsn) as db:
        mig._ensure_ledger(db)
        for path in mig._migration_files():
            text, digest = mig._read_migration(DRAFT if path.stem == "0011_money_definer" else path)
            db.execute(text)
            db.execute(
                "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                (path.stem, digest),
            )


def earlier_draft_scenario(w):
    fresh = w.new_schema("od")
    _install_with_the_earlier_0011_draft(fresh)
    assert w.run("SELECT to_regprocedure(%s) IS NULL", (f"sb_od_{w.sfx}.{HOLDS}",)) == [
        (True,)
    ]  # the premise: that draft made no such function
    # the draft warning is open: no refusal, and the note names the function and the command
    notes: list[str] = []
    assert mig.migrate(fresh, no_roles=True, notes=notes) == []
    (note,) = [n for n in notes if HOLDS in n]
    assert "do NOT exist" in note and "--reset-draft 0011_money_definer" in note
    assert "docs/migration-checksums.md" in note
    # the changed file is accepted although the database does not match it: refused by name, and rolled back
    text = _refused(fresh, no_roles=True, accept_changed_draft=("0011_money_definer",))
    assert HOLDS in text and "--reset-draft" in text and "do not exist" in text
    notes = []
    assert mig.migrate(fresh, no_roles=True, notes=notes) == []
    assert any(
        HOLDS in n for n in notes
    )  # the acceptance was not recorded: the warning is still open


def test_a_database_with_an_earlier_0011_draft_is_told_the_missing_function_and_the_command(w):
    earlier_draft_scenario(w)


def test_the_cli_prints_the_missing_function_of_an_earlier_draft(w, monkeypatch, capsys, cfg_dir):
    """The operator sees it: the note goes to stdout through the same `notes` list as the other migrate notes."""
    from hadavin_sdk import cli
    from tests.test_step_b_e7_round4 import _cli_cfg

    fresh = w.new_schema("oc")
    _install_with_the_earlier_0011_draft(fresh)
    _cli_cfg(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 0
    out = capsys.readouterr().out
    assert HOLDS in out and "--reset-draft 0011_money_definer" in out
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--no-roles",
        "--accept-changed-draft",
        "0011_money_definer",
    ]
    assert cli.main(argv) == 2
    assert HOLDS in capsys.readouterr().err


def test_the_earlier_draft_fixture_is_the_file_without_the_function():
    text = DRAFT.read_text(encoding="utf-8")
    assert "hadavin_expired_holds" not in text and "hadavin_cap_matches" in text
    assert "hadavin_expired_holds" in (mig.MIGRATIONS / "0011_money_definer.sql").read_text(
        encoding="utf-8"
    )
