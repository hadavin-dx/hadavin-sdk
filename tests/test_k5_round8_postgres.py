"""K5-core round 8, N8: with a purge DSN configured, the app deletes evidence only through the purge identity."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import load_config
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick as tick_mod
from tests.conftest import qualify
from tests.contracts.kinds.store_postgres import PURGE_DSN, pg_schema
from tests.test_k3_pilot_env import FakeChannel, ScriptedLLM, pilot_cfg


def test_the_app_deletes_evidence_only_through_the_purge_identity(tmp_path):
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        pytest.skip("HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)")
    for dsn in pg_schema(runtime=True):
        cfg = pilot_cfg(tmp_path)
        path = cfg / "config.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["backends"]["store"]["purge_dsn_secret_name"] = "pg-" + "purge"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        qualify(load_registry(load_config(cfg)), "ito-agent")
        secrets = FakeSecretProvider(
            {"slack-token": "t", "slack-sign": "s", "pg-dsn": dsn, "pg-purge": PURGE_DSN[dsn]}
        )
        app = app_mod.build(
            cfg, ["ito-agent"], secrets=secrets, channel=FakeChannel(), llm=ScriptedLLM()
        )
        assert app.purge_store is not app.store
        with pytest.raises(Exception, match="rivilege|ermission|denied|navailable"):
            app.store.purge_tool_calls(datetime.now(UTC), keep_run_ids=frozenset())
        tick_mod.purge_evidence(
            tick_mod.TickContext(app, datetime.now(UTC))
        )  # the purge identity can
        app.store._db.close()
        app.purge_store._db.close()
