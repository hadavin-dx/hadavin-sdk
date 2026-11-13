"""K3 in pilot and prod: fail-closed loading and the pilot build path (the App test needs HADAVIN_TEST_PG_DSN)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.audit import signer as signer_mod
from hadavin_sdk.backends import factory as factory_mod
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


# What a build of `pilot_cfg` asks the factory for (capability -> kinds).
PILOT_KINDS = {
    "secrets": {"mounted_file"},
    "signer": {"ed25519_local"},
    "anchor": {"none"},
    "store": {"postgres"},
    "audit": {"chain"},
    "llm": {"openai_compat"},
    "detector": {"regex"},
    "channel": {"slack"},
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


class Call(NamedTuple):
    """One call of the factory function `make`, as the seam below saw it."""

    capability: str
    settings: Any  # the settings object the caller handed to the factory
    provider: Any  # the secret provider handed on (None for the secrets backend itself)
    available: dict[
        str, Any
    ]  # the other objects handed on, by name (store, signer, anchor, routes, llm)
    result: Any  # what the call returned to the build

    @property
    def kind(self) -> str:
        return self.settings.kind


def plant_test_backends(monkeypatch, *, module=app_mod, store=None, **objects) -> list[Call]:
    """The ONE seam for a test that needs test objects on the real pilot or prod build path, where
    `build(secrets=, channel=, llm=, ...)` is refused. The factory function `make` of `module` (the app, or the
    command line) is wrapped: for a capability named in `objects` it returns that object (None is an object: it
    plants "no signer"); for the store, when the factory `store` is given, it returns `store()` (a new one per call:
    the app asks twice when a purge DSN is configured); every other capability goes to the real factory. The config
    keeps its real kinds.

    Returns the list of calls the build made (`Call`), so a test can assert what was asked: which settings, which
    secret provider, which other objects (the objects themselves, by name), and what each call returned."""
    calls: list[Call] = []

    def wrapper(capability, settings, provider=None, **available):
        if capability in objects:
            result = objects[capability]
        elif capability == "store" and store is not None:
            result = store()
        else:
            result = factory_mod.make(capability, settings, provider, **available)
        calls.append(Call(capability, settings, provider, dict(available), result))
        return result

    monkeypatch.setattr(module, "make", wrapper)
    return calls


def asked(calls: list[Call], provider) -> dict[str, set[str]]:
    """capability -> the kinds the build asked the factory for; every call after the secrets backend must hand on
    `provider`."""
    for call in calls:
        if call.capability != "secrets":
            assert call.provider is provider, (
                f"{call.capability} {call.kind}: built with another secret provider"
            )
    out: dict[str, set[str]] = {}
    for call in calls:
        out.setdefault(call.capability, set()).add(call.kind)
    return out


# What `app.build` hands the factory beside the settings and the secret provider (capability -> names).
HANDED_ON = {
    "secrets": (),
    "signer": (),
    "anchor": (),
    "store": (),
    "audit": ("anchor", "signer", "store"),
    "llm": ("routes",),
    "detector": ("llm",),
    "channel": ("store",),
}


def assert_asked_as_configured(calls: list[Call], cfg) -> None:
    """Every call carried the settings object of the loaded config `cfg` for its capability (the second store call:
    the same settings with the purge DSN in place of the runtime DSN) and the other objects `HANDED_ON` names. Each
    object handed on IS the one an earlier call returned: the store handed to the audit and to the channel is what
    the FIRST store call returned (the runtime store, never the purge store), and likewise the signer, the anchor
    and the model client; `routes` is the config's own."""
    b = cfg.backends
    first: dict[str, Any] = {}
    stores = 0
    for call in calls:
        assert tuple(sorted(call.available)) == HANDED_ON[call.capability], (
            f"{call.capability}: handed on {sorted(call.available)}"
        )
        for name, handed in call.available.items():
            if name == "routes":
                assert handed == cfg.routes, "the model client got other routes"
            else:
                assert name in first and handed is first[name], (
                    f"{call.capability}: the {name} handed on is not the one the first {name} call returned"
                )
        if call.capability == "detector":
            assert call.settings in b.detector
        elif call.capability == "store":
            stores += 1
            want = b.store
            if stores == 2:
                want = b.store.model_copy(
                    update={
                        "dsn_secret_name": b.store.purge_dsn_secret_name,
                        "purge_dsn_secret_name": None,
                    }
                )
            assert call.settings == want, f"store call {stores}: {call.settings}"
        else:
            assert call.settings == getattr(b, call.capability), (
                f"{call.capability}: other settings"
            )
        first.setdefault(call.capability, call.result)
    assert calls[0].capability == "secrets" and calls[0].provider is None


def test_k3_pilot_app_has_no_executor(tmp_path, monkeypatch):
    """A pilot App has no Executor and resolves no client-system secret; shadow and abstain cards are posted."""
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        cfg = pilot_cfg(tmp_path)
        qualify(load_registry(load_config(cfg)), "ito-agent")
        resolved: list[str] = []
        spy = _spy(dsn, resolved)

        channel = FakeChannel()
        calls = plant_test_backends(
            monkeypatch, secrets=spy, channel=channel, llm=ScriptedLLM(reply(PROPOSE), reply())
        )
        # hold_run_ids= is a production hook: a pilot build accepts it
        app = app_mod.build(cfg, ["ito-agent"], hold_run_ids=lambda: frozenset())
        # the build asked the factory for the configured real kinds, with the one provider
        assert asked(calls, spy) == PILOT_KINDS
        assert_asked_as_configured(calls, load_config(cfg))
        runtime_store = next(c.result for c in calls if c.capability == "store")
        assert app.store is runtime_store
        for capability in ("audit", "channel"):
            (call,) = [c for c in calls if c.capability == capability]
            assert call.available["store"] is runtime_store, f"{capability} got another store"
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
