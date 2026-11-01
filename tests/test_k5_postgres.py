"""K5 on a real Postgres (CI's service; skipped without HADAVIN_TEST_PG_DSN): the migration, the grants, JSONB, the
purge SQL and a whole run, which every other K5 test runs on the in-memory store only."""

from __future__ import annotations

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.cards import Delivery
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.config import load_config
from hadavin_sdk.guard import RegexDetector
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import RunState
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import evidence
from hadavin_sdk.runtime.agent_loop import Hooks, Runtime
from tests.conftest import qualify
from tests.contracts.kinds.store_postgres import pg_schema
from tests.fixtures import k5_tools
from tests.k5_support import SECRETS, ScriptLLM, k5_cfg


@pytest.fixture
def pg_store():
    for dsn in pg_schema(runtime=True):  # the runtime role: only the rights migrate granted
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        yield store
        store._db.close()


def test_a_whole_tooled_run_on_postgres(tmp_path, pg_store):
    k5_tools.RESULTS["app"] = (
        "ERROR upstream 10.0.0.5; mail ops@example.test; revision 17 \x00 failed"
    )
    cfg = load_config(k5_cfg(tmp_path))
    reg = load_registry(cfg)
    qualify(reg)
    audit = LocalDirSink(cfg.backends.audit.dir)
    hooks = Hooks(
        post_card=lambda card: Delivery(ok=True),
        toolbox=app_mod._toolbox(cfg, reg, SECRETS),
        validate_proposal=evidence.make_validator(pg_store),
    )
    llm = ScriptLLM(
        [{"tool": "app"}, {"tool": "app"}, {"propose": {"host": "<IPV4_1>", "revision": "17"}}]
    )
    rt = Runtime(
        reg,
        pg_store,
        audit,
        llm,
        RegexDetector(0.5),
        Limits(pg_store, audit, reg),
        ["test-agent"],
        hooks,
    )
    run = rt.handle("test-agent", "svc:test-agent", b"checkout is down at 10.0.0.5")
    assert (run.state, run.reason_code) == (RunState.NO_ACTION, "shadow")
    rows = pg_store.list_tool_calls(run.run_id)
    assert [r.call_id for r in rows] == [f"{run.run_id}:1", f"{run.run_id}:2"]  # fixed order
    assert "\x00" not in rows[0].output  # a NUL would have failed the insert
    assert pg_store.get_redaction_map(run.run_id)["<IPV4_1>"] == "10.0.0.5"
    assert pg_store.get_plan(run.run_id).inputs == {"host": "<IPV4_1>", "revision": "17"}
