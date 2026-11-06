"""Config for the stop state: the limits block, the pilot refusals, and credential refs the runtime never reads."""

from __future__ import annotations

import pytest
import yaml

from hadavin_sdk import defaults
from hadavin_sdk.config import ConfigError, LimitsSettings, load_config
from tests.test_k3_pilot_env import pilot_cfg


def test_defaults_and_validation_of_the_limits_block():
    s = LimitsSettings()
    assert s.max_open_stop_requests == defaults.KILL_SWITCH_MAX_OPEN_STOP_REQUESTS
    assert s.migrate_lock_timeout_ms == defaults.KILL_SWITCH_MIGRATE_LOCK_TIMEOUT_MS
    assert s.key_id == "k1"
    for bad in (
        {"max_open_stop_requests": 0},
        {"max_open_stop_requests": True},
        {"max_open_stop_requests": "5"},
        {"migrate_lock_timeout_ms": 0},  # 0 means "no timeout" to PostgreSQL
        {"migrate_lock_timeout_ms": 1.5},
        {"key_id": "bad id"},
        {"key_id": "k1\n"},
        {"key_id": ""},
        {"unknown_key": 1},
    ):
        with pytest.raises(ValueError):
            LimitsSettings(**bad)


def test_pilot_refuses_a_postgres_store_without_a_stop_credential(tmp_path):
    root = pilot_cfg(tmp_path)
    path = root / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["backends"]["store"]["stop_credential_ref"]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="stop_credential_ref is required"):
        load_config(root)


def test_credential_refs_are_not_secret_names_the_runtime_resolves():
    """The runtime resolves every field ending in `_secret_name` at start-up; the stop and reset logins must not
    be among them (the app would hold the operator's credential), while the label key must be."""
    from hadavin_sdk.backends.table import PostgresSettings

    fields = set(PostgresSettings.model_fields) | set(LimitsSettings.model_fields)
    assert {"stop_credential_ref", "reset_credential_ref"} <= fields
    assert not {
        f for f in ("stop_credential_ref", "reset_credential_ref") if f.endswith("_secret_name")
    }
    assert "label_key_secret_name" in LimitsSettings.model_fields
