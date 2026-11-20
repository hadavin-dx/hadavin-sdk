"""E5 (hostile review, Major 3 second half): a migrate run that names no role skipped the stop-state check and
exited 0, so an upgraded database whose runtime login kept old rights was never looked at. A run that names no
role is now refused unless `no_roles=True` (CLI `--no-roles`) says so on purpose."""

from __future__ import annotations

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import yaml

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig


def _no_db(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("connected")

    monkeypatch.setattr(mig, "connect", boom)


def test_a_migrate_that_names_no_role_is_refused_before_connecting(monkeypatch):
    _no_db(monkeypatch)
    with pytest.raises(ConfigError, match="--no-roles"):
        mig.migrate("postgresql://unused")


def test_the_explicit_flag_gets_past_the_refusal(monkeypatch):
    class Stop(Exception):
        pass

    def stop(*a, **k):
        raise Stop

    monkeypatch.setattr(mig, "connect", stop)
    with pytest.raises(Stop):  # past the refusal, at the connect
        mig.migrate("postgresql://unused", no_roles=True)


def test_no_roles_together_with_a_role_is_refused(monkeypatch):
    _no_db(monkeypatch)
    with pytest.raises(ConfigError, match="no_roles"):
        mig.migrate("postgresql://unused", runtime_role="rt", no_roles=True)


def _cfg(cfg_dir, monkeypatch):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")


def test_the_cli_refuses_a_plain_migrate_and_accepts_no_roles(cfg_dir, monkeypatch, capsys):
    _cfg(cfg_dir, monkeypatch)
    seen = []
    monkeypatch.setattr(
        "hadavin_sdk.store.migrate.migrate", lambda dsn, **kw: seen.append(kw) or []
    )
    assert cli.main(["--config", str(cfg_dir), "migrate"]) == 2
    assert "--no-roles" in capsys.readouterr().err and seen == []
    assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 0
    assert seen[0]["no_roles"] is True
