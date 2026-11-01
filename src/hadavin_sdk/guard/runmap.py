"""The run's one redaction map (K5, design 6.3, M14, R2, R6).

One map per run, started at intake (empty until K4) and continued for the document and every tool result, so a
value always gets the same placeholder and a placeholder never restores to a different value. Only **identifier
kinds** are ever stored or restored; secret and regulated kinds are placeholdered for the model but their originals
live in memory for the run and nowhere else.

Pure functions over a plain ``dict[str, str]`` (placeholder -> original). Stdlib and the studio redactor only.
"""

from __future__ import annotations

import re
from typing import Any

from hadavin_sdk.guard.redact import redact

# Identifier kinds a fix or a read may need back (M14): the spec list plus the other identifier kinds the
# redactor emits (IPV6 beside IPV4, hostnames, UUIDs, GCP and Azure resource ids). Anything not listed (every
# secret kind, every regulated kind, and any kind added later) is NOT stored: an allowlist fails safe.
STORED_KINDS = frozenset(
    {
        "ARN",
        "ACCOUNTID",
        "TENANT",
        "EMAIL",
        "MAC",
        "IPV4",
        "IPV6",
        "NAME",
        "ADDRESS",
        "PHONE",
        "HOSTNAME",
        "UUID",
        "GCPRESOURCE",
        "AZURERESOURCE",
    }
)
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9]*)_(\d+)>")


class RedactionError(RuntimeError):
    """The redactor failed: nothing may be sent to the model."""


def kind_of(placeholder: str) -> str:
    return placeholder.strip("<>").rsplit("_", 1)[0]


def storable(mapping: dict[str, str]) -> dict[str, str]:
    """The part of a run's map that may be stored and restored: identifier kinds only."""
    return {p: v for p, v in mapping.items() if kind_of(p) in STORED_KINDS}


def redact_text(text: str, mapping: dict[str, str]) -> str:
    """Redact `text` with the run's map, continuing it in place. Any failure is a RedactionError."""
    try:
        result = redact(text, mapping=mapping)
    except Exception as exc:  # noqa: BLE001 - whatever the redactor raised, nothing is sent
        raise RedactionError(type(exc).__name__) from None
    mapping.clear()
    mapping.update(result.mapping)
    return result.text


def redact_value(value: Any, mapping: dict[str, str]) -> Any:
    """`redact_text` over every string (and dict key) inside a JSON-shaped value."""
    if isinstance(value, str):
        return redact_text(value, mapping)
    if isinstance(value, dict):
        return {
            (redact_text(k, mapping) if isinstance(k, str) else k): redact_value(v, mapping)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_value(v, mapping) for v in value]
    return value


def restore_text(text: str, mapping: dict[str, str]) -> str:
    """One pass, only stored kinds: a restored value is never expanded again, a secret kind never restored."""
    allowed = storable(mapping)
    return PLACEHOLDER.sub(lambda m: allowed.get(m.group(0), m.group(0)), text)


def restore_value(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return restore_text(value, mapping)
    if isinstance(value, dict):
        return {k: restore_value(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [restore_value(v, mapping) for v in value]
    return value


def has_placeholder(value: Any) -> bool:
    """True if any string in the value still holds a ``<KIND_n>`` placeholder (so it could not be restored)."""
    if isinstance(value, str):
        return PLACEHOLDER.search(value) is not None
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(has_placeholder(v) for v in value)
    return False
