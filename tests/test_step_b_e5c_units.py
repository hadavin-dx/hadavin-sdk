"""E5c (review 6): R6-3 (InsufficientPrivilege of ALTER ROLE becomes a ConfigError naming the role), R6-4 (refusal
text, the options parser, identifier quoting), R6-2 (the CLI shows what changed on stderr). No database needed
except where marked."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
import yaml
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import postgres as pg

# ---- R6-3 -----------------------------------------------------------------------------------------------------


class _Res:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return self.rows


class _Db:
    """A connection that has a role-wide decoy row and refuses every ALTER."""

    def execute(self, stmt, params=None):
        if isinstance(stmt, sql.Composable):
            raise errors.InsufficientPrivilege("permission denied to alter role")
        if "pg_db_role_setting" in stmt:
            return _Res([(16400, "rt", None, "search_path=other_app")])
        return _Res([("app", "db")])


def test_alter_role_without_the_privilege_is_a_config_error_naming_the_role():
    with pytest.raises(ConfigError, match="rt") as err:
        mig.check_role_settings(_Db(), ["rt"])
    assert "CREATEROLE" in str(err.value) and "ADMIN OPTION" in str(err.value)


# ---- R6-4 -----------------------------------------------------------------------------------------------------


def test_the_pin_parser_reads_a_path_with_a_space_after_the_comma():
    dsn = make_conninfo("postgresql://u@h/d", options="-c search_path=app, public")
    assert pg.expected_schemas(dsn, None) == ["app", "public"]


def test_the_pin_parser_stops_at_the_next_option_and_reads_escaped_spaces():
    dsn = make_conninfo("postgresql://u@h/d", options="-c search_path=app -c statement_timeout=5")
    assert pg.expected_schemas(dsn, None) == ["app"]
    dsn = make_conninfo("postgresql://u@h/d", options=r"-c search_path=app,\ public")
    assert pg.expected_schemas(dsn, None) == ["app", "public"]


def test_a_quoted_path_keeps_capitals_and_doubled_quotes():
    dsn = make_conninfo("postgresql://u@h/d", options='-c search_path="Sb_Mixed""Q"')
    assert pg.expected_schemas(dsn, None) == ['Sb_Mixed"Q']


def test_the_refusal_says_how_to_pin_and_that_db_schema_is_the_expected_schema():
    class Conn:
        def execute(self, stmt, params=None):
            return _Res([("decoy", ["decoy"])])

    with pytest.raises(ConfigError) as err:
        pg.verify_schema(Conn(), ["app"])
    text = str(err.value)
    assert "options=-c search_path=" in text and "ALTER ROLE" in text
    assert "EXPECTED" in text
    assert "set backends.store.db_schema," not in text


# ---- R6-2: the CLI shows what changed -----------------------------------------------------------------------------


def test_the_cli_prints_what_migrate_changed_on_stderr(cfg_dir, monkeypatch, capsys):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")

    def fake(dsn, **kw):
        kw["on_role_change"]("role rt in database d: search_path 'x' -> 'app'")
        return []

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", fake)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--runtime-role", "rt"]) == 0
    assert "search_path 'x' -> 'app'" in capsys.readouterr().err


def test_a_config_error_of_migrate_exits_2(cfg_dir, monkeypatch, capsys):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")

    def fake(dsn, **kw):
        raise ConfigError("cannot alter role rt")

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", fake)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--runtime-role", "rt"]) == 2
    assert "rt" in capsys.readouterr().err


# ---- R6-4: identifier quoting (needs a server) ------------------------------------------------------------------

needs_pg = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"), reason="HADAVIN_TEST_PG_DSN not set"
)


@needs_pg
def test_the_privilege_probe_resolves_a_schema_with_capitals_and_a_quote():
    schema = 'Sb_Mixed"Q'
    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            db.execute(
                sql.SQL("CREATE TABLE {}.kill_switch (x int)").format(sql.Identifier(schema))
            )
            assert mig._holds(db, "postgres", schema, "kill_switch", "SELECT") is True
        finally:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
