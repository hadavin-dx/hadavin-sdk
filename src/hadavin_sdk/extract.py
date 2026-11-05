"""Structured extraction: validate, one retry with the validator's errors, then a dead letter."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import BaseModel, ValidationError

from hadavin_sdk.guard.safe_message import safe_message, safe_str
from hadavin_sdk.llm.protocol import LLM
from hadavin_sdk.models import DeadLetter, Reply

_ASK = "Extract the fields from the attached document. Answer with JSON matching the schema only."


# Error types whose message is fixed text (it never quotes the input). Every other type is reported by its
# type name alone: value_error / assertion_error / union_tag_invalid / *_parsing quote what the model wrote.
_FIXED_TEXT = frozenset(
    {
        "missing",
        "extra_forbidden",
        "int_parsing",
        "int_type",
        "float_parsing",
        "float_type",
        "string_type",
        "bool_type",
        "bool_parsing",
        "list_type",
        "dict_type",
        "none_required",
        "decimal_parsing",
        "decimal_type",
    }
)


def _declared(model: type[BaseModel], seen: set[type] | None = None) -> set[str]:
    """Every field name and alias the model (and the models nested in its annotations) declares."""
    seen = seen if seen is not None else set()
    if model in seen:
        return set()
    seen.add(model)
    names: set[str] = set()
    for name, info in model.model_fields.items():
        names.add(name)
        if info.alias:
            names.add(info.alias)
        stack = [info.annotation]
        while stack:
            ann = stack.pop()
            if isinstance(ann, type) and issubclass(ann, BaseModel):
                names |= _declared(ann, seen)
            stack.extend(getattr(ann, "__args__", ()) or ())
    return names


def _where(loc: tuple[object, ...], declared: set[str]) -> str:
    """The error path with every part that is not a declared field name or an index replaced by [key]:
    dict keys and extra field names come from the model's own output."""
    parts = [str(p) if isinstance(p, int) or p in declared else "[key]" for p in loc]
    return ".".join(parts) or "(root)"


def _failure(exc: Exception, schema: type[BaseModel] | None = None) -> str:
    """Why validation failed, for DeadLetter.errors and the retry prompt: where and what kind, never a value
    (pydantic's `input_value`, `msg` and `loc` can quote the model's output: a name, an address, an amount)."""
    if isinstance(exc, ValidationError):
        declared = _declared(schema) if schema is not None else set()
        found = exc.errors(include_input=False, include_url=False)
        parts = [
            f"{_where(e['loc'], declared)}: {e['msg'] if e['type'] in _FIXED_TEXT else e['type']}"
            for e in found
        ]
        return "ValidationError: " + safe_str("; ".join(parts), 300)
    if isinstance(exc, json.JSONDecodeError):
        return f"JSONDecodeError: {safe_str(exc.msg, 100)} at position {exc.pos}"
    # Any other ValueError or a RecursionError: class name only (built-in text is withheld).
    return safe_message(exc, 300)


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
    return json.loads(reply.text)


def extract(
    llm: LLM,
    document: bytes,
    schema: type[BaseModel],
    *,
    run_id: str,
    route: str,
    system: str = "",
) -> Valid | DeadLetter:
    messages = [{"role": "user", "content": _ASK}]
    replies: list[Reply] = []
    errors: list[str] = []
    for _attempt in range(2):
        reply = llm.chat(
            messages,
            system=system,
            route=route,
            documents=[document],
            output_schema=schema.model_json_schema(),
        )
        replies.append(reply)
        try:
            return Valid(schema.model_validate(_parse(reply)), replies)
        # A JSONDecodeError is a ValueError; 100000 open brackets raise RecursionError.
        except (ValidationError, ValueError, RecursionError) as exc:
            errors.append(_failure(exc, schema))
            messages = [
                *messages,
                {"role": "assistant", "content": reply.text or "(tool call)"},
                {"role": "user", "content": f"That failed validation: {errors[-1]}. Try again."},
            ]
    return DeadLetter(run_id=run_id, reason="extract_invalid", errors=errors)
