"""A safety switch must not change state from loose input: "yes", 1, "true" and "on" are not the YAML value `true`.

Every boolean field of every pydantic model in the package is a strict bool (`StrictBool`): only a real `true` or `false`
loads. That covers what an operator writes (config, contracts, tool manifests) and the records read back from files or
the store (`qualified.jsonl`, the replay file, store rows), because a hand-edited line saying `"green": "yes"` must not
qualify an agent. A flag whose safe value is True (redaction on, the label hold on) must not be turned off by "no", 0,
"false" or "off" either. The structural row lists every bool field of every model class defined at the top level of a
package module and fails on a loose one, and fails when a module cannot be imported. It does not see dataclasses,
TypedDicts or model classes created inside a function.
"""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import types
import typing
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel, ValidationError

import hadavin_sdk
from hadavin_sdk.actions.contract import ActionContract
from hadavin_sdk.backends.table import OpenAICompatSettings, PostgresSettings, S3ObjectLockSettings
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.models import GateRun, KillSwitch, RunResult, ToolCallRecord, Verdict
from hadavin_sdk.replay_records import FILE as REPLAY_FILE
from hadavin_sdk.replay_records import ReplayRecord, read_records
from hadavin_sdk.runtime.agent_loop import qualified_runs
from hadavin_sdk.tools import ToolSpec
from tests.k5_support import TOOL
from tests.k5_support import _edit as _edit_file
from tests.test_stage_names import ANCHOR

FIXTURE_ACTION = Path(__file__).parent / "fixtures" / "config" / "actions" / "lookup_record.yaml"
ON_VALUES = ["yes", 1, "true", "on"]  # none of these may switch a flag on
OFF_VALUES = ["no", 0, "false", "off"]  # none of these may switch a default-True flag off


def _config(cfg_dir: Path, path: tuple[str, ...], value) -> None:
    def put(d):
        node = d
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value

    _edit_file(cfg_dir / "config.yaml", put)
    load_config(cfg_dir)


def _contract(field: str, value):
    return ActionContract.model_validate(
        {**yaml.safe_load(FIXTURE_ACTION.read_text("utf-8")), field: value}
    )


# (id, loose values, the real value that must load, loader(value)); the loader raises on a loose value
FLAGS = [
    ("made_up_data_only", ON_VALUES, True, lambda c, v: _config(c, ("made_up_data_only",), v)),
    (
        "allow_insecure_loopback",
        ON_VALUES,
        True,
        lambda c, v: _config(c, ("allow_insecure_loopback",), v),
    ),
    ("k1b.redact", OFF_VALUES, False, lambda c, v: _config(c, ("k1b", "redact"), v)),
    (
        "retention.hold_labelled",
        OFF_VALUES,
        False,
        lambda c, v: _config(c, ("retention", "hold_labelled"), v),
    ),
    (
        "anchor.retention_ack",
        ON_VALUES,
        True,
        lambda c, v: S3ObjectLockSettings.model_validate({**ANCHOR, "retention_ack": v}),
    ),
    (
        "store.iam_auth",
        ON_VALUES,
        True,
        lambda c, v: PostgresSettings.model_validate(
            {
                "kind": "postgres",
                "dsn_secret_name": "madeup-dsn",
                "iam_auth": v,
                "region": "madeup-region-1",
            }
        ),
    ),
    (
        "openai_compat.max_completion_tokens",
        ON_VALUES,
        True,
        lambda c, v: OpenAICompatSettings.model_validate(
            {
                "kind": "openai_compat",
                "base_url": "https://llm.example/v1",
                "max_completion_tokens": v,
            }
        ),
    ),
    ("tool.cluster_http", ON_VALUES, True, lambda c, v: ToolSpec(**{**TOOL, "cluster_http": v})),
    (
        "contract.targets_production",
        OFF_VALUES,
        False,
        lambda c, v: _contract("targets_production", v),
    ),
    ("contract.changes_spend", OFF_VALUES, False, lambda c, v: _contract("changes_spend", v)),
]


@pytest.mark.parametrize(("flag", "loose", "real", "load"), FLAGS, ids=[f[0] for f in FLAGS])
def test_a_safety_flag_loads_only_from_a_real_bool(cfg_dir, flag, loose, real, load):
    load(cfg_dir, real)  # control: the real bool loads, so a refusal below is about the loose value
    for value in loose:
        with pytest.raises((ConfigError, ValidationError)) as err:
            load(cfg_dir, value)
        # refused as a type error on the field, not for some other reason
        assert "valid boolean" in str(err.value), f"{flag}={value!r}: {err.value}"


GATE_RUN = {
    "agent_id": "madeup-agent",
    "model_id": "madeup-model",
    "prompt_sha256": "0" * 64,
    "config_hash": "1" * 64,
    "golden_sha256": "2" * 64,
    "n": 3,
    "passed": 3,
    "pass_rate": 1.0,
    "threshold": 0.9,
    "green": True,
    "ts": "2026-01-01T00:00:00Z",
}
REPLAY = {
    "agent_id": "madeup-agent",
    "config_hash": "1" * 64,
    "model_id": "madeup-model",
    "prompt_sha256": "0" * 64,
    "bundle_sha256": "3" * 64,
    "k": 3,
    "pass_k": 1.0,
    "pass_rate": 1.0,
    "threshold": 0.9,
    "green": True,
    "ts": "2026-01-01T00:00:00Z",
}
TOOL_CALL = {
    "call_id": "r1:1",
    "run_id": "r1",
    "tool": "madeup_tool",
    "inputs": {},
    "output": "made up",
    "output_sha256": "4" * 64,
}
RECORDS = [  # (model, valid fields, bool field): records read back from files and the store
    (GateRun, GATE_RUN, "green"),
    (ReplayRecord, REPLAY, "green"),
    (KillSwitch, {}, "on"),
    (Verdict, {"flagged": False, "score": 0.0, "backend": "madeup"}, "flagged"),
    (RunResult, {"outcome": "failed"}, "retryable"),
    (ToolCallRecord, TOOL_CALL, "error"),
]


@pytest.mark.parametrize(("model", "fields", "name"), RECORDS, ids=[r[0].__name__ for r in RECORDS])
@pytest.mark.parametrize("value", ["yes", 1, "true", "on", "no", 0])
def test_a_record_loads_a_bool_only_from_a_real_bool(model, fields, name, value):
    model.model_validate({**fields, name: True})  # control
    with pytest.raises(ValidationError) as err:
        model.model_validate({**fields, name: value})
    assert "valid boolean" in str(err.value)


def test_a_hand_edited_gate_line_cannot_qualify_an_agent(tmp_path):
    """The choke point of qualification: a `qualified.jsonl` line with `"green": "yes"` is refused, not read as green."""
    line = json.dumps({**GATE_RUN, "green": "yes"})
    (tmp_path / "qualified.jsonl").write_text(line + "\n", encoding="utf-8")
    registry = types.SimpleNamespace(config=types.SimpleNamespace(root=tmp_path))
    with pytest.raises(ConfigError, match="not a gate run"):
        qualified_runs(registry)


def test_a_hand_edited_replay_line_cannot_qualify_an_agent(tmp_path):
    (tmp_path / REPLAY_FILE).write_text(
        json.dumps({**REPLAY, "green": "yes"}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="not a replay record"):
        read_records(tmp_path)


def _has_bool(annotation) -> bool:
    return annotation is bool or any(_has_bool(a) for a in typing.get_args(annotation))


def _loose_bool_fields() -> tuple[list[str], list[str]]:
    """(loose bool fields, modules that could not be imported) over every model class at the top level of a module."""
    classes: set[type] = set()
    unimportable = []
    for info in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
        try:
            module = importlib.import_module(info.name)
        except (ImportError, AttributeError, SyntaxError) as exc:  # reported below, never skipped
            unimportable.append(f"{info.name}: {type(exc).__name__}: {exc}")
            continue
        classes |= {
            c
            for _, c in inspect.getmembers(module, inspect.isclass)
            if issubclass(c, BaseModel) and c.__module__ == module.__name__
        }
    loose = []
    for cls in classes:
        for name, field in cls.model_fields.items():
            strict = any(getattr(m, "strict", False) for m in field.metadata)
            if _has_bool(field.annotation) and not strict:
                loose.append(f"{cls.__module__}.{cls.__name__}.{name}")
    return sorted(loose), unimportable


def test_every_bool_field_is_strict_and_every_module_imports():
    loose, unimportable = _loose_bool_fields()
    assert unimportable == [], (
        f"modules that cannot be imported (install with --all-extras): {unimportable}"
    )
    assert loose == [], f"loose bool fields (make them StrictBool): {loose}"
