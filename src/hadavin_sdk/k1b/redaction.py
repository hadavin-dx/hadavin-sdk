"""Redaction before the model: every string of a case bundle is masked, then the case runs on the masked copy.

Uses the runtime's one choke point (``guard.runmap.redact_text``: NFKC, invisible characters, JSON escapes and the size
cap, then the studio redactor): ONE placeholder namespace per case, so a value
found in any alert field, log line, k8s record or runbook chunk is masked in all of them, and the model still
sees that two lines name the same host (``<HOST_1>`` stays ``<HOST_1>``). The placeholder map lives in this
call's memory only: it is never returned, written to the outputs, sent to the audit sink or logged. Only the
count of distinct values masked per class leaves this module, never a value.

Left unchanged on purpose, so citations and queries still resolve:
* evidence IDs (``logs/001.jsonl#2``) are built from file names and positions, not from content;
* file names; the values of ``service``, ``kind`` and ``fault_type`` are redacted like any other text (a plain word
  passes the redactor unchanged), so a secret planted there is masked;
* any string that is exactly a UTC timestamp (``parse_ts``), and every number.

What this does NOT catch (``LIMITS``): the redactor is pattern-based. A name in free text ("Acme asked ..."), an
internal project name, a ticket number, a value in an unusual format, or a secret no pattern matches reaches the
model. Treat redaction as a strong first
filter, not as proof that no client data leaves.
"""

from __future__ import annotations

import base64
import dataclasses
import re
from collections import Counter
from collections.abc import Callable
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b.bundle import Bundle, parse_ts

SCHEME = (
    "every text value and every key of the alert, metrics, logs, deploys, Kubernetes records and runbooks is "
    "masked with the studio redactor (pattern based; one placeholder per distinct value, per case) before the "
    "model or the injection screen sees it; file names, evidence IDs, timestamps and numbers are kept"
)
LIMITS = (
    "The redactor is pattern based. It does not catch names in free text, customer or project names, ticket "
    "numbers, values in unusual formats, or anything no pattern matches, and it does not mask the values of the "
    "values the patterns do not know. Masking is a first filter, not proof that no client "
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


MASKED = "<SECRET_REDACTED>"
# A key (or an env entry's `name`) that says its value is a credential. Word boundaries: `author` and `tokens_used` are not.
SENSITIVE_KEY = re.compile(
    r"(^|[_.\-\s])(pass(word|wd|phrase)?|secret|token|api[_-]?key|authorization|credentials?|private[_-]?key|bearer)($|[_.\-\s])",
    re.IGNORECASE,
)


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def sensitive(key: object) -> bool:
    """Does a key (or an env entry's name) say its value is a credential? camelCase is split first (`clientSecret`,
    `accessToken`, `dbPassword` read as `client_secret` ...)."""
    return isinstance(key, str) and SENSITIVE_KEY.search(_CAMEL.sub("_", key)) is not None


def _pair(key: str, value: str, f: Callable[[str], str]) -> str:
    """A value whose key names a credential, redacted WITH its key (`password=hunter2`), so the redactor's key=value
    patterns see it. A Kubernetes Secret value is base64: its decoded text is tried too. If the redactor still leaves
    the value as it was, the value is masked whole: a value under a credential key never reaches the model."""
    spellings = [value]
    try:
        spellings.append(base64.b64decode(value, validate=True).decode("utf-8"))
    except ValueError:  # bad base64 (`binascii.Error`) and bytes that are not UTF-8 (`UnicodeDecodeError`) are both ValueErrors
        pass
    for text in spellings:
        masked = f(f"{key}={text}")
        if masked != f"{key}={text}":
            return masked[len(key) + 1 :] if masked.startswith(key + "=") else masked
    f(value)
    return MASKED


def _walk(
    obj: Any, f: Callable[[str], str], key: str | None = None, secret_data: bool = False
) -> Any:
    """Every string is redacted, at any depth: no key exempts a value. `key` is the parent key, so a value under a
    credential key (or under a Kubernetes Secret's data) and an env entry `{"name": "DB_PASSWORD", "value": ...}` are
    redacted together with the key that names them."""
    sens = secret_data or sensitive(key)  # inherited by everything nested under a credential key
    if isinstance(obj, str):
        if parse_ts(obj) is not None:
            return obj
        if key is not None and sens:
            return _pair(key, obj, f)
        return f(obj)
    if isinstance(obj, int | float) and not isinstance(obj, bool) and sens:
        return MASKED  # a number under a credential key (a PIN, a numeric token) is a value too
    if isinstance(obj, dict):
        name = obj.get("name")
        named = sensitive(name)
        secret = obj.get("kind") == "Secret"
        out: dict[Any, Any] = {}
        for k, v in obj.items():
            if k == "value" and named and isinstance(v, str):
                out[_key(k, f)] = _pair(str(name), v, f)
            elif secret and k in ("data", "stringData") and isinstance(v, dict):
                out[_key(k, f)] = {_key(kx, f): _walk(vx, f, str(kx), True) for kx, vx in v.items()}
            else:
                out[_key(k, f)] = _walk(v, f, k, sens)
        return out
    if isinstance(obj, list):
        return [_walk(v, f, key, secret_data) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, f, key, secret_data) for v in obj)
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
    """The masked copy of one bundle and the distinct values masked per class. EVERY string goes through
    `tools.redact_layered` (the runtime's choke point for tool results: NFKC, invisible characters, JSON escapes, the
    size cap, percent, entity and base64-free layers to a fixed point, marker neutralising) with ONE
    map: pass 1 builds the map over the whole bundle, pass 2 masks with the complete map (a value found in a later
    record is masked in the earlier ones). The map is dropped here; a string over the cap raises `InputTooLarge`."""
    mapping = runmap.RunMap()

    total = 0

    def mask(s: str) -> str:
        nonlocal total
        total += len(s)
        if total > 2 * defaults.MAX_BUNDLE_CHARS:  # pass 1 and pass 2 both count
            raise runmap.InputTooLarge("InputTooLarge")
        try:
            return runmap.redact_untrusted(s, mapping)
        except runmap.TooDeep:  # nested deeper than the cap: not shown
            return MASKED

    _apply(b, mask)  # pass 1: find every value
    total = 0
    out = _apply(b, mask)  # pass 2: mask with the whole map
    return out, Counter(_kind(p) for p in mapping)
