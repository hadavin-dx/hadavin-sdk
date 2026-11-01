"""Redaction before the model: every string of a case bundle is masked, then the case runs on the masked copy.

Uses the studio's one redactor (``guard.redact.redact_many``): ONE placeholder namespace per case, so a value
found in any alert field, log line, k8s record or runbook chunk is masked in all of them, and the model still
sees that two lines name the same host (``<HOST_1>`` stays ``<HOST_1>``). The placeholder map lives in this
call's memory only: it is never returned, written to the outputs, sent to the audit sink or logged. Only the
count of distinct values masked per class leaves this module, never a value.

Left unchanged on purpose, so citations and queries still resolve:
* evidence IDs (``logs/001.jsonl#2``) are built from file names and positions, not from content;
* file names, and the values of the structural keys in ``STRUCTURAL_KEYS`` (service, kind, fault type,
  timestamps: the vocabulary the Cause List uses);
* any string that is exactly a UTC timestamp (``parse_ts``), and every number.

What this does NOT catch (``LIMITS``): the redactor is pattern-based. A name in free text ("Acme asked ..."), an
internal project name, a ticket number, a value in an unusual format, or a secret no pattern matches reaches the
model. Structural keys are not masked even if a value there is sensitive. Treat redaction as a strong first
filter, not as proof that no client data leaves.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any

from hadavin_sdk.guard.redact import redact_many
from hadavin_sdk.k1b.bundle import Bundle, parse_ts

# Only the Cause List vocabulary and timestamps: everything else (names, queries, labels, severity, ids inside
# records) is masked. The snapshot and the model both work on the masked copy, so masked names still match.
STRUCTURAL_KEYS = frozenset({"service", "fault_type", "kind", "ts", "as_of"})
SCHEME = (
    "every text value and every key of the alert, metrics, logs, deploys, Kubernetes records and runbooks is "
    "masked with the studio redactor (pattern based; one placeholder per distinct value, per case) before the "
    "model or the injection screen sees it; file names, evidence IDs, timestamps, numbers and the values of the "
    "service, kind and fault_type keys are kept"
)
LIMITS = (
    "The redactor is pattern based. It does not catch names in free text, customer or project names, ticket "
    "numbers, values in unusual formats, or anything no pattern matches, and it does not mask the values of the "
    "structural keys (service, kind, fault type). Masking is a first filter, not proof that no client "
    "data reached the model."
)
KINDS_NOTE = "Counts are distinct values masked per class (EMAIL, IPV4, ARN, ...), summed over the cases; no values."


def _kind(placeholder: str) -> str:
    return placeholder.strip("<>").rsplit("_", 1)[0]


def _key(k: Any, f: Callable[[str], str]) -> Any:
    """Dict keys can hold data too ({"bob@example.com": ...}); plain schema words pass the redactor unchanged."""
    return f(k) if isinstance(k, str) and k not in SCHEMA_WORDS else k


# The record and alert field names the tools read; they are never data, so they are not run through the redactor.
SCHEMA_WORDS = frozenset(
    {
        "title",
        "summary",
        "severity",
        "service_label",
        "fired_by",
        "labels",
        "ts",
        "level",
        "message",
        "service",
        "version",
        "kind",
        "name",
        "as_of",
        "spec",
        "events",
        "reason",
        "query",
        "points",
        "value",
    }
)


def _walk(obj: Any, f: Callable[[str], str], key: str | None = None) -> Any:
    if isinstance(obj, str):
        return obj if key in STRUCTURAL_KEYS or parse_ts(obj) is not None else f(obj)
    if isinstance(obj, dict):
        return {_key(k, f): _walk(v, f, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(v, f, key) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, f, key) for v in obj)
    return obj


def _pairs(items: tuple[tuple[str, Any], ...], f: Callable[[str], str]) -> tuple[Any, ...]:
    """(file, content) pairs: the file name stays, the content is walked."""
    return tuple((rel, _walk(content, f)) for rel, content in items)


def _apply(b: Bundle, f: Callable[[str], str]) -> Bundle:
    return dataclasses.replace(
        b,
        alert=_walk(b.alert, f),
        metrics=_pairs(b.metrics, f),
        logs=_pairs(b.logs, f),
        deploys=_walk(b.deploys, f),
        k8s=_pairs(b.k8s, f),
        runbooks=_pairs(b.runbooks, f),
    )


def redact_bundle(b: Bundle) -> tuple[Bundle, Counter[str]]:
    """The masked copy of one bundle and the distinct values masked per class. The map is dropped here."""
    found: list[str] = []
    _apply(
        b, lambda s: found.append(s) or s
    )  # pass 1: gather every maskable string, in a fixed order
    masked, mapping = redact_many(found)
    it: Iterator[str] = iter(masked)
    out = _apply(b, lambda s: next(it))  # pass 2: put the masked strings back in the same order
    return out, Counter(_kind(p) for p in mapping)
