"""Action contracts (``actions/<id>.yaml``) and the effective risk class."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hadavin_sdk.models import RiskClass

_ORDER: list[RiskClass] = ["read_only", "reversible", "sign_off"]


class NoneExecutor(BaseModel):
    """Shadow-only contract: nothing can run it."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["none"]


class ManualExecutor(BaseModel):
    """A posted fix a person runs themselves (built in K8; refused at load until then)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["manual"]
    command_template: str
    undo_command_template: str
    go_window_s: int = 600
    client_wait_s: int = 3600


class HttpExecutor(BaseModel):
    """Hadavin-run execution (Phase 2): refused in pilot and prod, kept in dev for the slice-1 tests."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["http"]
    operation: str  # "METHOD /path/{field}"
    lookup_operation: str | None = None
    secret_name: str


ExecutorSpec = Annotated[NoneExecutor | ManualExecutor | HttpExecutor, Field(discriminator="kind")]
_LABEL = re.compile(r"[a-z0-9_-]{1,40}")


class ActionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    version: int
    description: str
    input_schema: dict[str, Any]
    risk_class: RiskClass
    targets_production: bool
    changes_spend: bool
    # http: a key of config.systems. none and manual: a plain label, never looked up.
    target_system: str
    executor: ExecutorSpec
    idempotency_header: str = "Idempotency-Key"
    verify_check: str | None = None
    rollback: str | None = None
    rollback_test: str | None = None
    undo_test: str | None = None  # manual: a pytest id that renders the undo command
    chain_id: str | None = None
    expected_outcome: str

    @model_validator(mode="after")
    def _fields_per_kind(self) -> ActionContract:
        kind = self.executor.kind
        if kind != "http" and not _LABEL.fullmatch(self.target_system):
            raise ValueError("target_system must be a label [a-z0-9_-]{1,40} for none and manual")
        if kind == "none":
            return self
        if self.chain_id is None:
            raise ValueError(f"executor {kind} needs chain_id")
        if kind == "http" and self.verify_check is None:
            raise ValueError("executor http needs verify_check")
        if kind == "manual":
            if self.verify_check is None or self.undo_test is None:
                raise ValueError("executor manual needs verify_check and undo_test")
            if self.rollback is not None or self.rollback_test is not None:
                raise ValueError("executor manual must not set rollback or rollback_test")
        return self


def effective_class(contract: ActionContract, data_class: str) -> RiskClass:
    """Raise one level per risk flag; a reversible action with no rollback is sign_off. Never lowers."""
    level = _ORDER.index(contract.risk_class)
    # Hadavin executes nothing for none and manual, so those two raises wait for Phase 2 (K3, V5-B2).
    if contract.executor.kind == "http":
        level += contract.targets_production + contract.changes_spend
    level += data_class in {"confidential", "restricted"}
    cls = _ORDER[min(level, 2)]
    spec = contract.executor
    # An undo is what makes a reversible action reversible: the rollback (http) or the undo command (manual).
    # A none contract executes nothing, so its declared class is shown as is.
    undo = spec.undo_command_template if spec.kind == "manual" else contract.rollback
    if cls == "reversible" and spec.kind != "none" and undo is None:
        cls = "sign_off"
    return cls


_TYPES = {"string": str, "integer": int, "boolean": bool, "object": dict, "array": list}
_KEYWORDS = {
    "type",
    "enum",
    "maxLength",
    "minLength",
    "pattern",
    "properties",
    "required",
    "additionalProperties",
}


def schema_problems(schema: Any, where: str = "input_schema") -> list[str]:
    """Load-time check: only the subset ``schema_errors`` understands, so a contract can't crash the gate."""
    if not isinstance(schema, dict):
        return [f"{where}: must be a mapping"]
    out = [f"{where}: unsupported keyword {k}" for k in schema if k not in _KEYWORDS]
    t = schema.get("type")
    if "type" in schema and (not isinstance(t, str) or t not in _TYPES):
        out.append(f"{where}: unsupported type {t!r} (use string for numbers)")
    if "pattern" in schema:
        try:
            if not isinstance(schema["pattern"], str):
                raise TypeError
            re.compile(schema["pattern"])
        except (re.error, TypeError):
            out.append(f"{where}: bad pattern")
    for key in ("maxLength", "minLength"):
        v = schema.get(key)
        if key in schema and (not isinstance(v, int) or isinstance(v, bool) or v < 0):
            out.append(f"{where}: {key} must be a non-negative integer")
    if "enum" in schema and not isinstance(schema["enum"], list):
        out.append(f"{where}: enum must be a list")
    req = schema.get("required", [])
    if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
        out.append(f"{where}: required must be a list of names")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        out.append(f"{where}: additionalProperties must be true or false")
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        return [*out, f"{where}: properties must be a mapping"]
    for k, sub in props.items():
        out += schema_problems(sub, f"{where}.{k}")
    return out


def schema_errors(schema: dict[str, Any], value: Any) -> list[str]:
    """Small JSON-Schema subset: object/required/properties/additionalProperties, type, maxLength, pattern, enum.

    ponytail: subset only; swap for the jsonschema package if a contract needs more keywords.
    """
    errs: list[str] = []
    want = schema.get("type")
    if (
        want
        and not isinstance(value, _TYPES[want])
        or (want == "integer" and isinstance(value, bool))
    ):
        return [f"expected {want}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append("not in enum")
    if isinstance(value, str):
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append("too long")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append("too short")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errs.append("pattern mismatch")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errs += [f"missing {k}" for k in schema.get("required", []) if k not in value]
        if schema.get("additionalProperties") is False:
            errs += [f"unexpected {k}" for k in value if k not in props]
        for k, sub in props.items():
            if k in value:
                errs += [f"{k}: {e}" for e in schema_errors(sub, value[k])]
    return errs
