"""Step B, ESCALATION E5, round 5b: hostile-review Major 4, Major 5 and Nits 11 and 15. No database.

Major 4: reset_credential_ref (the login that can clear a stop) must never be a secret the runtime reads.
Major 5: a reset that finds the switch still ON must not steer the operator to reset again blindly.
Nit 11: a connection lost while the reset ran does not prove "nothing was changed".
Nit 15: two different secret NAMES that hold the same login are the same login."""

from __future__ import annotations

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.secret_name import canonical_secret_name, collides
from tests.conftest import make_cfg, qualify
from tests.k5_support import TOOL, edit_config, k5_cfg
from tests.test_stop_state_unit import Audit, StoreStub, _postgres

REF = "reset-login"
ALIAS = "Reset.Login"  # folds to REF


class Provider:
    def get(self, name):
        return "v" * 40


def _build(cfg_dir):
    qualify(load_registry(load_config(cfg_dir)))
    return app_mod.build(cfg_dir, ["test-agent"], secrets=Provider())


def _with_ref(monkeypatch, cfg_dir, ref=REF):
    monkeypatch.setattr(
        type(load_config(cfg_dir).backends.store), "reset_credential_ref", ref, raising=False
    )


# --- Major 4 ------------------------------------------------------------------------------------------------------


def test_collides_folds_both_sides():
    assert collides("Reset.Login", ["x", "reset-login"])
    assert not collides("reset-login", ["x", "reset-login2"])
    assert not collides("reset-login", [])


def _channel(cfg):
    edit_config(
        cfg,
        lambda d: d["backends"].update(channel={"kind": "fake", "signing_secret_name": ALIAS}),
    )
    return cfg


def _llm_key(cfg):
    edit_config(
        cfg,
        lambda d: (
            d.update(made_up_data_only=True),
            d["backends"].update(
                llm={
                    "kind": "openai_compat",
                    "base_url": "https://x.test",
                    "api_key_secret_name": ALIAS,
                }
            ),
        ),
    )
    return cfg


def _restored(cfg):
    edit_config(cfg, lambda d: d.update(evidence={"restored_hash_key_secret_name": ALIAS}))
    return cfg


def _tool(cfg):
    return k5_cfg(cfg.parent, tools=[{**TOOL, "secret_names": [ALIAS]}])


def _tool_ca(cfg):
    return k5_cfg(cfg.parent, tools=[{**TOOL, "ca_secret_name": ALIAS, "ca_file": None}])


def _executor(cfg):
    edit_config(cfg, lambda d: None)
    return cfg


def _sender(cfg):
    edit_config(
        cfg,
        lambda d: d.update(
            triggers={
                "tenant": "acme",
                "senders": {
                    "alpha": {
                        "secret_names": [ALIAS],
                        "agent_id": "test-agent",
                        "principal_id": "svc:test-agent",
                    }
                },
            }
        ),
    )
    return cfg


@pytest.mark.parametrize(
    "setup", [_channel, _llm_key, _restored, _tool, _sender], ids=lambda f: f.__name__
)
def test_a_secret_the_runtime_reads_that_folds_to_the_reset_ref_stops_the_start(
    tmp_path, monkeypatch, setup
):
    cfg = setup(make_cfg(tmp_path))
    _with_ref(monkeypatch, cfg)
    with pytest.raises(ConfigError) as caught:
        _build(cfg)
    assert "reset_credential_ref" in str(caught.value) or "senders" in str(caught.value)
    assert REF not in str(caught.value) and ALIAS not in str(caught.value)


def test_the_executor_secret_may_not_be_the_reset_ref(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    _with_ref(monkeypatch, cfg, "FIXTURE_TOKEN")
    with pytest.raises(ConfigError, match="reset_credential_ref"):
        _build(cfg)


def test_an_unrelated_reset_ref_starts(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    _with_ref(monkeypatch, cfg)
    assert _build(cfg) is not None


# --- Major 5 ------------------------------------------------------------------------------------------------------


def test_a_reset_that_finds_the_switch_on_does_not_say_reset_again(capsys):
    when = now()
    store = StoreStub(read=KillSwitch(on=True, by="ops:during", ts=when))
    limits = Limits(store, Audit(), None)
    assert cli.kill_switch(limits, "reset", "user:op") == 2
    out, err = capsys.readouterr()
    assert "reset again" not in err
    assert "ops:during" in err and when.isoformat() in err
    assert "colleague" in err and "stop reason" in err and "before resetting again" in err
    assert "kill switch OFF" not in out + err


def test_a_reset_that_finds_the_switch_on_with_no_known_setter_still_warns(capsys):
    store = StoreStub(read=KillSwitch(on=True, by=None))
    assert cli.kill_switch(Limits(store, Audit(), None), "reset", "user:op") == 2
    err = capsys.readouterr().err
    assert "colleague" in err and "stop reason" in err and "None" not in err


# --- Nit 11 -------------------------------------------------------------------------------------------------------


def test_a_connection_lost_at_the_clear_does_not_claim_nothing_was_changed(capsys):
    store = StoreStub(set_error=ConnectionResetError("gone"))
    assert cli.kill_switch(Limits(store, Audit(), None), "reset", "user:op") == 4
    err = capsys.readouterr().err
    assert "kill switch NOT reset: the store is unreachable." in err
    assert "Nothing was changed" not in err
    assert "may or may not" in err


# --- Nit 15 -------------------------------------------------------------------------------------------------------


def test_a_reset_ref_holding_the_same_login_under_another_name_is_refused(
    tmp_path, monkeypatch, capsys
):
    cfg = _postgres(make_cfg(tmp_path), "other-name")
    real = cli.make
    calls = []

    def fake(capability, settings, *a, **k):
        if capability == "secrets":
            return FakeSecretProvider(
                {"pg-dsn": "postgresql://same/db", "other-name": "postgresql://same/db"}
            )
        calls.append(capability)
        return real(capability, settings, *a, **k)

    monkeypatch.setattr(cli, "make", fake)
    code = cli.main(["--config", str(cfg), "limits", "reset", "--by", "user:op"])
    err = capsys.readouterr().err
    assert code == 2 and calls == []
    assert err.startswith("refused: backends.store.reset_credential_ref") and "same login" in err
    assert "postgresql://same" not in err
    assert canonical_secret_name("other-name") != canonical_secret_name("pg-dsn")


def test_a_release_ref_holding_the_runtime_login_under_another_name_is_refused(
    tmp_path, monkeypatch, capsys
):
    from datetime import date

    cfg = load_config(_postgres(make_cfg(tmp_path)))
    store = cfg.backends.store.model_copy(update={"release_credential_ref": "rel-name"})
    cfg = cfg.model_copy(update={"backends": cfg.backends.model_copy(update={"store": store})})
    monkeypatch.setattr(
        cli,
        "make",
        lambda cap, *a, **k: (
            FakeSecretProvider({"pg-dsn": "postgresql://x/db", "rel-name": "postgresql://x/db"})
            if cap == "secrets"
            else pytest.fail("built a store")
        ),
    )
    assert cli.release_expired_cmd(cfg, "a", date(2025, 1, 31), "u") == 2
    assert "same login" in capsys.readouterr().err
