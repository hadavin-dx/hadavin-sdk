"""The agent's answer: one strict JSON object, parsed without any leniency.

Valid shapes: (a) ``not_sure`` true and ``causes`` empty; (b) ``not_sure`` false or absent and one or more
causes, each with at least one evidence id. Anything else (both, neither, wrong types, extra keys, fenced or
surrounded text, empty ``evidence_ids``) is unreadable and returns ``None``; the scorer counts it as a Miss.
More than 3 causes parse fine; only the first 3 are scored.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    ValidationError,
    model_validator,
)

SCORED_CAUSES = 3

DIAGNOSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "causes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "fault_type": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
                "required": ["service", "fault_type", "evidence_ids"],
                "additionalProperties": False,
            },
        },
        "not_sure": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["causes"],
    "additionalProperties": False,
}


Name = Annotated[StrictStr, Field(min_length=1)]


class Cause(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    service: Name
    fault_type: Name
    evidence_ids: list[Name]

    @model_validator(mode="after")
    def _has_evidence(self) -> Cause:
        if not self.evidence_ids:
            raise ValueError("a cause needs at least one evidence id")
        return self


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    causes: list[Cause]
    not_sure: StrictBool = False
    reason: StrictStr = ""

    @model_validator(mode="after")
    def _one_form(self) -> Diagnosis:
        if self.not_sure == bool(self.causes):  # both, or neither
            raise ValueError("either not_sure with no causes, or causes without not_sure")
        return self

    @property
    def scored(self) -> list[Cause]:
        """The first 3 causes: the only ones scored and citation-checked."""
        return self.causes[:SCORED_CAUSES]


def parse_diagnosis(value: Any) -> Diagnosis | None:
    """A tool-call input (already a dict) to a Diagnosis, or ``None`` when unreadable."""
    if not isinstance(value, dict):
        return None
    try:
        return Diagnosis.model_validate(value, strict=True)
    except ValidationError:
        return None


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("duplicate key")
        out[key] = val
    return out


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-finite number {name}")


def parse_diagnosis_text(text: str) -> Diagnosis | None:
    """Reply text to a Diagnosis. The text must be exactly one JSON object: a code fence, extra prose,
    duplicate keys or NaN make it unreadable (``None``). Deliberately stricter than ``llm.common.json_in_text``."""
    try:
        obj = json.loads(
            text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant
        )
    except (ValueError, RecursionError):
        return None
    return parse_diagnosis(obj)
