"""K3 in pilot and prod: fail-closed loading and the pilot build path (the App test needs HADAVIN_TEST_PG_DSN)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.audit import signer as signer_mod
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.models import RunState
from hadavin_sdk.registry import load_registry
from tests.conftest import qualify
from tests.test_k3_pilot import NONE_CONTRACT, PROPOSE, ScriptedLLM, reply

S = RunState
AGENT = {
    "id": "ito-agent",
    "status": "live",
    "data_class": "internal",
    "model_route": "default",
    "prompt_file": "prompts/ito.md",
    "scope_allowed": ["restart_service"],
    "max_steps": 4,
    "budget_usd": {"daily": "1.00", "monthly": "10.00"},
    "levels": {"restart_service": "shadow"},
    "max_run_usd": "0.50",
}


def pilot_cfg(tmp_path: Path, *, env="pilot", agent=None, contract=None, config=None) -> Path:
    """A pilot config with real kinds only (nothing is contacted until `build`)."""
    root = tmp_path / "pilot"
    for sub in ("actions", "prompts", "golden", "inputs"):
        (root / sub).mkdir(parents=True)
    (root / "prompts" / "ito.md").write_text("You triage incidents.\n", encoding="utf-8")
    signer_mod.generate_key(root / "audit-key.pem", root / "audit-key.pub", None, base=root)
    cfg = {
        "environment": env,
        "routes": {
            "default": {
                "model_id": "fake-model",
                "input_usd_per_mtok": "3.00",
                "output_usd_per_mtok": "15.00",
                "max_tokens": 1024,
            }
        },
        "backends": {
            "secrets": {"kind": "mounted_file", "dir": "secrets"},
            "store": {
                "kind": "postgres",
                "dsn_secret_name": "pg-dsn",
                "purge_dsn_secret_name": "pg-purge",
            },
            "audit": {"kind": "chain"},
            "signer": {"kind": "ed25519_local", "private_key_path": "audit-key.pem"},
            "llm": {"kind": "openai_compat", "base_url": "https://llm.example/v1"},
            "detector": [{"kind": "regex", "threshold": 0.5}],
            "channel": {
                "kind": "slack",
                "channel_id": "C0TEST",
                "signing_secret_name": "slack-sign",
                "bot_token_secret_name": "slack-token",
            },
        },
        "golden_dir": "golden",
        "inputs_dir": "inputs",
        "evidence": {"restored_hash_key_secret_name": "restored-key"},
        **(config or {}),
    }
    contract = {**NONE_CONTRACT, **(contract or {})}
    agent = {k: v for k, v in {**AGENT, **(agent or {})}.items() if v is not None}
    (root / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (root / "agents.yaml").write_text(yaml.safe_dump([agent]), encoding="utf-8")
    (root / "principals.yaml").write_text(
        yaml.safe_dump([{"id": "svc:ito", "kind": "service", "rights": ["restart_service"]}]),
        encoding="utf-8",
    )
    (root / "actions" / "restart_service.yaml").write_text(
        yaml.safe_dump(contract), encoding="utf-8"
    )
    return root


def test_k3_pilot_config_loads(tmp_path):
    assert load_registry(load_config(pilot_cfg(tmp_path))).agents["ito-agent"].levels


def test_k3_http_refused_in_pilot(tmp_path):
    http = {
        "target_system": "records",
        "executor": {"kind": "http", "operation": "POST /x", "secret_name": "client-token"},
        "verify_check": "m:f",
        "chain_id": "c",
        "rollback": "m:g",
    }
    cfg = pilot_cfg(
        tmp_path,
        contract=http,
        config={"systems": {"records": {"base_url": "https://r.example"}}, "check_modules": ["m"]},
    )
    (cfg / "chains.yaml").write_text(
        yaml.safe_dump([{"id": "c", "steps": [{"approver_ids": ["u"], "timeout_s": 5}]}]),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="executor http is not available in pilot or prod"):
        load_registry(load_config(cfg))


def test_k3_missing_level_refused(tmp_path):
    cfg = pilot_cfg(tmp_path, agent={"levels": None})
    with pytest.raises(ConfigError, match="levels is required in pilot and prod"):
        load_registry(load_config(cfg))


def test_k3_levels_must_cover_every_action_in_pilot(tmp_path):
    cfg = pilot_cfg(tmp_path, agent={"levels": {}})
    with pytest.raises(ConfigError, match="levels must list restart_service"):
        load_registry(load_config(cfg))


def test_k3_suggest_refused_without_evidence(tmp_path):
    cfg = pilot_cfg(tmp_path, agent={"levels": {"restart_service": "suggest"}})
    with pytest.raises(ConfigError, match="cannot load before K6 and K8"):
        load_registry(load_config(cfg))


def test_k3_missing_run_budget_refused_in_pilot(tmp_path):
    cfg = pilot_cfg(tmp_path, agent={"max_run_usd": None})
    with pytest.raises(ConfigError, match="max_run_usd is required in pilot and prod"):
        load_registry(load_config(cfg))


def test_k3_confidential_agent_refused_in_pilot(tmp_path):
    cfg = pilot_cfg(tmp_path, agent={"data_class": "confidential"})
    with pytest.raises(ConfigError, match="data_class confidential is not available until Phase 3"):
        load_registry(load_config(cfg))


def test_k3_read_only_contract_refused_in_pilot(tmp_path):
    cfg = pilot_cfg(tmp_path, contract={"risk_class": "read_only"})
    with pytest.raises(ConfigError, match="a read_only action is a tool"):
        load_registry(load_config(cfg))


def test_k3_request_tracker_key_refused_in_pilot(tmp_path):
    cfg = pilot_cfg(tmp_path, config={"provisioning": {"kind": "terraform"}})
    with pytest.raises(ConfigError, match="key 'provisioning' is not available until Phase 2"):
        load_config(cfg)


def _spy(dsn: str, resolved: list[str]) -> FakeSecretProvider:
    """A secret provider that records every name read."""
    values = {
        "slack-token": "t",
        "slack-sign": "s",
        "pg-dsn": dsn,
        "pg-purge": dsn,
        "restored-key": "r" * 16,
    }

    class Spy(FakeSecretProvider):
        def get(self, name):
            resolved.append(name)
            return super().get(name)

    return Spy(values)


def test_k3_pilot_app_has_no_executor(tmp_path):
    """A pilot App has no Executor and resolves no client-system secret; shadow and abstain cards are posted."""
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        cfg = pilot_cfg(tmp_path)
        qualify(load_registry(load_config(cfg)), "ito-agent")
        resolved: list[str] = []
        spy = _spy(dsn, resolved)

        channel = FakeChannel()
        app = app_mod.build(
            cfg,
            ["ito-agent"],
            secrets=spy,
            channel=channel,
            llm=ScriptedLLM(reply(PROPOSE), reply()),
        )
        assert app.executor is None
        assert app.runtime.hooks.execute is None and app.runtime.hooks.verify is None
        assert sorted(set(resolved)) == [
            "pg-dsn",
            "pg-purge",
            "restored-key",
            "slack-sign",
            "slack-token",
        ]
        run = app.runtime.handle("ito-agent", "svc:ito", b"checkout is down")
        assert (run.state, run.reason_code) == (S.NO_ACTION, "shadow")
        assert app.runtime.handle("ito-agent", "svc:ito", b"all quiet").state == S.NO_ACTION
        assert [c.text.split("\n")[0] for c in channel.cards] == [
            "Agent's view: not checked, do not run",
            "Agent abstained: here is what it looked at",
        ]
        assert app.audit.verify().ok
        app.store._db.close()
