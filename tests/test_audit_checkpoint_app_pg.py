"""`app.build` and the checkpoint login (ticket A-audit-rights): the three start-up refusals come before any secret
is read and leave no checkpoint connection open, and a demo or dev start with a signer but no checkpoint login warns
loudly. Needs HADAVIN_TEST_PG_DSN; skipped without it."""

from __future__ import annotations

import logging
import os

import pytest
import yaml

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import qualify
from tests.contracts.kinds.store_postgres import CHECKPOINT_DSN, PURGE_DSN, pg_schema
from tests.test_k3_pilot import ScriptedLLM
from tests.test_k3_pilot_env import pilot_cfg

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


class _Spy(FakeSecretProvider):
    def __init__(self, values, resolved):
        super().__init__(values)
        self.resolved = resolved

    def get(self, name):
        self.resolved.append(name)
        return super().get(name)


def _edit(cfg, **store):
    path = cfg / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for k, v in store.items():
        if v is None:
            data["backends"]["store"].pop(k, None)
        else:
            data["backends"]["store"][k] = v
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _build(cfg, secrets, monkeypatch):
    made: list = []
    real = app_mod.make

    def spy_make(capability, *a, **kw):
        out = real(capability, *a, **kw)
        made.append((capability, out))
        return out

    monkeypatch.setattr(app_mod, "make", spy_make)
    qualify(load_registry(load_config(cfg)), "ito-agent")
    try:
        app = app_mod.build(
            cfg,
            ["ito-agent"],
            secrets=secrets,
            channel=FakeChannel(),
            llm=ScriptedLLM(),
            allow_test_doubles=True,
        )
    except ConfigError as exc:
        return made, exc, None
    return made, None, app


def _values(dsn):
    return {
        "slack-token": "t",
        "slack-sign": "s",
        "pg-dsn": dsn,
        "pg-purge": PURGE_DSN[dsn],
        "pg-checkpoint": CHECKPOINT_DSN[dsn],
        "restored-key": "r" * 16,
    }


@pytest.mark.parametrize(
    ("name", "match"),
    [
        ("../pg-checkpoint", "path-shaped"),
        ("pg-dsn", "same secret"),
        ("pg-purge", "same secret"),
        ("release-ref", "same secret"),
        ("reset-ref", "same secret"),
        ("caps-ref", "same secret"),
    ],
)
def test_a_bad_checkpoint_secret_name_is_refused_before_any_secret_is_read(
    tmp_path, monkeypatch, name, match
):
    for dsn in pg_schema(runtime=True):
        cfg = pilot_cfg(tmp_path)
        _edit(
            cfg,
            checkpoint_dsn_secret_name=name,
            release_credential_ref="release-ref",
            reset_credential_ref="reset-ref",
            caps_credential_ref="caps-ref",
        )
        resolved: list[str] = []
        made, exc, app = _build(cfg, _Spy(_values(dsn), resolved), monkeypatch)
        assert app is None and match in str(exc)
        assert resolved == []
        assert [c for c, _ in made if c != "secrets"] == []  # no store, so no connection


def test_the_same_login_under_two_names_is_refused_and_closes_the_checkpoint_connection(
    tmp_path, monkeypatch
):
    for dsn in pg_schema(runtime=True):
        cfg = pilot_cfg(tmp_path)
        values = {**_values(dsn), "pg-checkpoint": dsn}  # the runtime's own DSN under another name
        made, exc, app = _build(cfg, _Spy(values, []), monkeypatch)
        assert app is None
        stores = [s for c, s in made if c == "store"]
        assert len(stores) == 3  # runtime, purge, checkpoint: the last one was opened and refused
        assert stores[-1]._db.closed
        assert "same database login" in str(exc)
        for s in stores[:2]:
            s._db.close()


def test_a_demo_start_with_a_signer_and_no_checkpoint_login_warns_once_and_starts(tmp_path, caplog):
    for dsn in pg_schema(runtime=True):
        cfg = pilot_cfg(tmp_path, env="demo")
        _edit(cfg, checkpoint_dsn_secret_name=None)
        path = cfg / "config.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["made_up_data_only"] = True
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        qualify(load_registry(load_config(cfg)), "ito-agent")
        values = _values(dsn)
        with caplog.at_level(logging.WARNING, logger="hadavin_sdk.app"):
            app = app_mod.build(
                cfg,
                ["ito-agent"],
                secrets=FakeSecretProvider(values),
                channel=FakeChannel(),
                llm=ScriptedLLM(),
                allow_test_doubles=True,
            )
        try:
            hits = [r for r in caplog.records if "checkpoint_dsn_secret_name" in r.getMessage()]
            assert len(hits) == 1 and hits[0].levelno == logging.WARNING
            assert "--checkpoint-role" in hits[0].getMessage()
        finally:
            app.store._db.close()
            app.purge_store._db.close()
