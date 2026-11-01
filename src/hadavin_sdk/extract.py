"""Structured extraction: validate, one retry with the validator's errors, then a dead letter.

R85: a retry names the failing field path and error type only. A pydantic message or input can quote the offending
value, which is document content, so it never reaches the retry prompt, the dead letter or a log.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import BaseModel, ValidationError

from hadavin_sdk.llm.common import json_in_text, loads_bounded
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import DeadLetter, Reply

_ASK = "Extract the fields from the attached document. Answer with JSON matching the schema only."
_RETRY = (
    "Your previous reply was invalid: {errors}. Reply again with only the corrected JSON object."
)
_MAX_ERRORS = 10  # per attempt, so a hostile reply cannot grow the retry prompt or the dead letter


@dataclass
class Valid:
    data: BaseModel
    replies: list[Reply] = field(default_factory=list)

    @property
    def cost_usd(self) -> Decimal:
        return sum((r.cost_usd for r in self.replies), Decimal(0))


def _parse(reply: Reply) -> object:
    if reply.tool_calls:
        return reply.tool_calls[0].input
    try:
        return loads_bounded(reply.text)
    except json.JSONDecodeError:
        found = json_in_text(reply.text)  # fenced, or after a sentence (R82)
        if found is None:
            raise
        return found


# JSON-schema keywords whose value is a schema, a list of schemas or a map of schemas. Anything else (`default`,
# `examples`, `const`, `enum`) is data and is never walked: a default of {"properties": None} is not a schema.
_SCHEMA = (
    "items",
    "additionalProperties",
    "not",
    "if",
    "then",
    "else",
    "contains",
    "propertyNames",
)
_SCHEMAS = ("prefixItems", "anyOf", "oneOf", "allOf")
_SCHEMA_MAPS = ("$defs", "definitions", "patternProperties")


def _field_names(node: object, out: set[str]) -> set[str]:
    """Every property name in a JSON schema: the only strings an error path may show (a dict key in a path
    would be document content)."""
    if not isinstance(node, dict):
        return out
    props = node.get("properties")
    if isinstance(props, dict):
        out.update(k for k in props if isinstance(k, str))
        for v in props.values():
            _field_names(v, out)
    for k in _SCHEMA:
        _field_names(node.get(k), out)
    for k in _SCHEMAS:
        if isinstance(node.get(k), list):
            for v in node[k]:
                _field_names(v, out)
    for k in _SCHEMA_MAPS:
        if isinstance(node.get(k), dict):
            for v in node[k].values():
                _field_names(v, out)
    return out


def safe_errors(exc: Exception, names: set[str]) -> str:
    """Field path and error type only; never pydantic's ``msg``, ``input`` or ``ctx``."""
    if isinstance(exc, ValidationError):
        return "; ".join(
            ".".join(p if isinstance(p, str) and p in names else "*" for p in e["loc"])
            + f": {e['type']}"
            for e in exc.errors(include_input=False, include_url=False)[:_MAX_ERRORS]
        )
    if isinstance(exc, json.JSONDecodeError):
        return "reply is not JSON"
    return "reply is invalid"


def extract(
    llm: LLM,
    document: bytes,
    schema: type[BaseModel],
    *,
    run_id: str,
    route: str,
    system: str = "",
) -> Valid | DeadLetter:
    schema_json = schema.model_json_schema()
    names = _field_names(schema_json, set())
    messages = [{"role": "user", "content": _ASK}]
    replies: list[Reply] = []
    errors: list[str] = []
    for _attempt in range(2):
        reply = llm.chat(
            messages,
            system=system,
            route=route,
            documents=[document],
            output_schema=schema_json,
        )
        replies.append(reply)
        try:
            return Valid(schema.model_validate(_parse(reply)), replies)
        except (
            ValidationError,
            ValueError,
            RecursionError,
        ) as exc:  # JSONDecodeError is a ValueError
            errors.append(f"{exc.__class__.__name__}: {safe_errors(exc, names)}")
            # The model's own invalid reply is not echoed back (it may quote the document, which is attached
            # again on every call): R85's corrective turn carries the error only.
            # One user turn (some providers reject two in a row): the ask, then the sanitized failure summary.
            messages = [
                {"role": "user", "content": f"{_ASK}\n\n{_RETRY.format(errors=errors[-1])}"}
            ]
    return DeadLetter(run_id=run_id, reason="extract_invalid", errors=errors)
