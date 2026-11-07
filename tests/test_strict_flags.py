"""A safety switch must not change state from loose input: "yes", 1, "true" and "on" are not the YAML value `true`.

Every boolean field a config, an action contract or a tool manifest can set is a strict bool (`StrictBool`): only a real
YAML `true` or `false` loads. A flag whose safe value is True (redaction on, the label hold on) must not be turned off by
"no", 0, "false" or "off" either. The structural row lists every bool field in the package; a new loose one fails it,
so it gets decided: strict, or a reviewed entry in INTERNAL with a reason.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import typing
from pathlib import Path

import pytest
import yaml
from pydantic import BaseModel, ValidationError

import hadavin_sdk
from hadavin_sdk.actions.contract import ActionContract
from hadavin_sdk.backends.table import PostgresSettings, S3ObjectLockSettings
from hadavin_sdk.config import ConfigError, load_config
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
        with pytest.raises((ConfigError, ValidationError)):
            load(cfg_dir, value)


# Bool fields that are internal records (written by the code, not set by an operator's file). Loose input never
# reaches them from a config; they are not safety switches. Reviewed: add a field here with a reason, or make it strict.
INTERNAL = {
    "hadavin_sdk.models.GateRun.green": "a stored gate result, written by the gate",
    "hadavin_sdk.models.KillSwitch.on": "stored kill-switch state, written by the store",
    "hadavin_sdk.models.RunResult.retryable": "a run outcome, written by the runtime",
    "hadavin_sdk.models.ToolCallRecord.error": "a tool call row, written by the runtime",
    "hadavin_sdk.models.Verdict.flagged": "a detector's verdict, written by the detector",
    "hadavin_sdk.replay_records.ReplayRecord.green": "a replay record, written by the replay",
    "hadavin_sdk.backends.table.OpenAICompatSettings.max_completion_tokens": (
        "an API-compatibility knob (which token-limit field name to send), not a safety switch"
    ),
}


def _has_bool(annotation) -> bool:
    return annotation is bool or any(_has_bool(a) for a in typing.get_args(annotation))


def _loose_bool_fields() -> list[str]:
    classes: set[type] = set()
    for info in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
        try:
            module = importlib.import_module(info.name)
        except (
            ImportError,
            AttributeError,
        ):  # an optional cloud module without its extra installed
            continue
        classes |= {
            c
            for _, c in inspect.getmembers(module, inspect.isclass)
            if issubclass(c, BaseModel) and c.__module__ == module.__name__
        }
    out = []
    for cls in classes:
        for name, field in cls.model_fields.items():
            strict = any(getattr(m, "strict", False) for m in field.metadata)
            if _has_bool(field.annotation) and not strict:
                out.append(f"{cls.__module__}.{cls.__name__}.{name}")
    return sorted(out)


def test_every_bool_field_is_strict_or_reviewed_internal():
    loose = _loose_bool_fields()
    inherited = {
        f for f in loose if f.rsplit(".", 1)[1] == "retention_ack"
    }  # subclasses repeat the base field
    unknown = [f for f in loose if f not in INTERNAL and f not in inherited]
    assert unknown == [], (
        f"loose bool fields (make them StrictBool or list them in INTERNAL): {unknown}"
    )
    assert not (set(INTERNAL) - set(loose)), "INTERNAL names a field that is no longer a loose bool"
