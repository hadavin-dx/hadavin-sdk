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
import binascii
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
    "numbers, values in unusual formats, or anything else no pattern matches. A value under a key that names a "
    "credential, and every entry of a Kubernetes Secret, is always masked under its own key. The same value is "
    "also masked where it is repeated elsewhere in the case only when all of this holds: it is a text of 4 to "
    "255 characters directly under that key; it is made of printable ASCII characters and white space; it does "
    "not hold both kinds of quote mark; no part of it is something another pattern masks (an e-mail address, a "
    "host name, a key); and the copy is spelled the same way. An entry of a Secret under a key that does not "
    "name a credential is masked elsewhere only when it also has at least 8 characters and is not all digits or "
    "one lower-case word. Not masked where repeated: longer or shorter values, numbers, values nested deeper "
    "under a credential key, values with control or other special characters, and copies in another spelling "
    "(base64, capitals, wrapped over lines). A setting about a credential (a key that ends in enabled, policy, "
    "count, expiry and the like) is shown only when its value is a yes or no word, a number or a time. Masking "
    "is a first filter, not proof that no client data reached the model."
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
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SPLIT = re.compile(r"[_.\-\s]+")
_TRAILING_DIGITS = re.compile(r"(?<=[a-z])[0-9]+$")
CREDENTIAL_WORDS = frozenset(
    [
        "pass",
        "password",
        "passwords",
        "passwd",
        "pwd",
        "passphrase",
        "secret",
        "secrets",
        "token",
        "apikey",
        "apikeys",
        "authorization",
        "auth",
        "credential",
        "credentials",
        "bearer",
        "session",
        "sessionid",
        "jsessionid",
        "phpsessid",
        "sessid",
    ]
)
GLUED_ENDINGS = (
    "password", "passwd", "pwd", "passphrase", "secret", "token", "apikey", "secretkey", "accesskey",
    "privatekey", "sessionid", "sessid",
)  # fmt: skip
# (word before, word): `api_key`, `client-key-data`, `connect.sid`
WORD_PAIRS = frozenset(
    {
        (q, k)
        for q in ["api", "private", "access", "secret", "signing", "encryption", "account"]
        for k in ("key", "keys")
    }
    | {("key", "data"), ("cert", "data"), ("certificate", "data"), ("connect", "sid")}
)
COUNT_WORDS_BEFORE_TOKENS = frozenset(
    ["max", "min", "input", "output", "prompt", "completion", "total", "cached"]
)
SETTING_WORDS = frozenset(
    [
        "enabled",
        "disabled",
        "required",
        "policy",
        "length",
        "count",
        "age",
        "days",
        "ttl",
        "expiry",
        "expires",
    ]
)
SETTING_VALUE = re.compile(r"(?i)true|false|yes|no|on|off|none|[0-9]{1,10}[smhdw]?")


def _key_words(key: str) -> list[str]:
    return [_TRAILING_DIGITS.sub("", w) for w in _SPLIT.split(_CAMEL.sub("_", key).lower()) if w]


def sensitive(key: object) -> bool:
    """Does a key (or the name of a named entry) say its value is a credential?

    The key is cut into words (at camelCase, `_`, `.`, `-` and white space; lower case; digits at the end of a word
    dropped). It is a credential key when a word is in `CREDENTIAL_WORDS`, ends with one of `GLUED_ENDINGS`, forms a
    pair of `WORD_PAIRS` with the word before it, or is `tokens` (unless it is a count: `max_tokens`, `tokens_used`).
    There is no exception by the last word: a key the older rule accepted is still accepted. Cost, accepted on purpose:
    keys such as `auth_method` or `session_duration`, and env entries named `PWD`, `OLDPWD` or ending in `pwd`, are
    masked although they hold no login secret."""
    if not isinstance(key, str):
        return False
    words = _key_words(key)
    for i, w in enumerate(words):
        before = words[i - 1] if i else ""
        after = words[i + 1] if i + 1 < len(words) else ""
        if w in CREDENTIAL_WORDS or w.endswith(GLUED_ENDINGS) or (before, w) in WORD_PAIRS:
            return True
        if w == "tokens" and before not in COUNT_WORDS_BEFORE_TOKENS and after != "used":
            return True
    return False


def _setting_key(key: object) -> bool:
    """A credential key whose last word says the entry is a setting ABOUT a credential (`..._policy_enabled`)."""
    return sensitive(key) and _key_words(str(key))[-1] in SETTING_WORDS


def _setting_value(obj: Any) -> bool:
    """The only values shown under a setting key: a bool, None, a number, a timestamp, a short on/off word or count."""
    if obj is None or isinstance(obj, bool | int | float):
        return True
    return isinstance(obj, str) and (
        parse_ts(obj) is not None or SETTING_VALUE.fullmatch(obj) is not None
    )


FALLBACK_KEY = "secret"
MAX_SPELLING_CHARS = 255
MIN_REGISTER_CHARS = 8
MAX_REGISTERED_ENTRIES = (
    256  # per `data` / `stringData` of one Secret; later entries get the fixed mask
)
_PLAIN_CHARS = frozenset(chr(c) for c in range(0x21, 0x7F)) - frozenset(";&,\"'")
_SAFE_KEY = re.compile(r"[A-Za-z0-9_.\-]{1,60}")
_ONE_LOWER_WORD = re.compile(r"[a-z]+")
_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")


def _attempts(key: str, text: str, credential: bool) -> list[tuple[str, str]]:
    """(key to write, quote) for one spelling of a value, in the order tried."""
    if not text or len(text) > MAX_SPELLING_CHARS:
        return []
    if not credential and (
        len(text) < MIN_REGISTER_CHARS or text.isdigit() or _ONE_LOWER_WORD.fullmatch(text)
    ):
        return []
    if all(c in _PLAIN_CHARS for c in text):
        own = [(key, "")] if credential and _SAFE_KEY.fullmatch(key) else []
        return [*own, (FALLBACK_KEY, "")]
    quote = next((q for q in ('"', "'") if q not in text), None)
    return [(FALLBACK_KEY, quote)] if quote else []


def _accepted(key: str, text: str, credential: bool, f: Callable[[str], str]) -> str | None:
    for k, quote in _attempts(key, text, credential):
        masked = f(f"{k}={quote}{text}{quote}")
        if not masked.startswith(k + "="):
            continue
        part = masked[len(k) + 1 :]
        if quote:
            if len(part) < 2 or part[0] != quote or part[-1] != quote:
                continue
            part = part[1:-1]
        if _ONLY_PLACEHOLDERS.fullmatch(part):
            return part
    return None


def _pair(key: str, value: str, f: Callable[[str], str], known_secret: bool = False) -> str:
    """A value whose key names a credential, or an entry of a Kubernetes Secret (`known_secret`).

    The value is written to the redactor behind a key word (its own key when both are plain, else the word `secret`
    and a quote mark), so the redactor's key=value rules see it; the decoded text of a base64 value is tried too. The
    result is taken ONLY when it is that key, `=` and nothing but placeholders; a result that merely changed is not
    taken. Otherwise the whole value becomes `MASKED`. So a value under a credential key reaches the model only as
    placeholders or as the fixed mask, never partly masked.

    Masked where it is repeated elsewhere in the case only within the limits of `LIMITS`: a text of 4 to 255
    characters directly under the key, printable ASCII and white space, not both kinds of quote mark, no part that
    another pattern masks, and a copy spelled the same way. One exception to the masking is made before this function
    is called: a text that is exactly a UTC timestamp is shown as written (`_walk`)."""
    credential = sensitive(key)
    if not credential and not known_secret:
        f(value)
        return MASKED
    spellings = [value]
    try:
        spellings.append(base64.b64decode(value, validate=True).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError):
        pass
    result = None
    for text in spellings:
        got = _accepted(key, text, credential, f)
        if got is None:
            continue
        result = got
        if not known_secret:
            return result
    if result is not None:
        return result
    f(value)
    return MASKED


def _named(obj: dict) -> tuple[Any, Any]:
    """(name, the key that holds the value) of an entry shaped {name|key: ..., value: ...}, in any letter case."""
    nk = next((k for k in obj if isinstance(k, str) and k.lower() in ("name", "key")), None)
    vk = next((k for k in obj if isinstance(k, str) and k.lower() == "value"), None)
    if nk is None or vk is None or not sensitive(obj[nk]):
        return None, None
    return obj[nk], vk


def _walk_dict(
    obj: dict, f: Callable[[str], str], sens: bool, known_secret: bool, secret: bool
) -> dict[Any, Any]:
    """One dict. `secret`: this dict is a Kubernetes Secret, or the `spec` of a record whose kind is Secret (a bundle's
    k8s record has exactly the keys kind, name, as_of, spec, events, so the Secret's `data` sits under `spec`)."""
    name, value_key = _named(obj)
    out: dict[Any, Any] = {}
    for k, v in obj.items():
        if value_key is not None and k == value_key:
            out[_key(k, f)] = _walk(v, f, str(name), sens, known_secret)
        elif secret and k in ("data", "stringData") and isinstance(v, dict):
            out[_key(k, f)] = {
                _key(kx, f): _walk(vx, f, str(kx), True, i < MAX_REGISTERED_ENTRIES)
                for i, (kx, vx) in enumerate(v.items())
            }
        elif secret and k in ("data", "stringData"):
            # not a map (a malformed Secret): still the content of a Secret, so every text and number in it gets the
            # fixed mask; nothing of it is registered
            out[_key(k, f)] = _walk(v, f, str(k), True, False)
        elif secret and k == "spec" and isinstance(v, dict):
            out[_key(k, f)] = _walk_dict(v, f, sens, known_secret, True)
        else:
            out[_key(k, f)] = _walk(v, f, k, sens, known_secret)
    return out


def _walk(
    obj: Any,
    f: Callable[[str], str],
    key: str | None = None,
    secret_data: bool = False,
    known_secret: bool = False,
) -> Any:
    """Every string is redacted, at any depth: no key exempts a value. `key` is the parent key (or the name of a named
    entry), `secret_data` says the value sits under a credential key or in a Secret, `known_secret` that it is an entry
    of a Secret's `data` / `stringData` (only those and values directly under a credential key are registered)."""
    own = sensitive(key)
    sens = secret_data or own
    if own and not secret_data and _setting_key(key) and _setting_value(obj):
        return obj
    if isinstance(obj, str):
        if parse_ts(obj) is not None:
            return obj
        if key is not None and sens:
            return _pair(key, obj, f, known_secret)
        return f(obj)
    if isinstance(obj, int | float) and not isinstance(obj, bool) and sens:
        return MASKED
    if isinstance(obj, dict):
        return _walk_dict(obj, f, sens, known_secret, obj.get("kind") == "Secret")
    if isinstance(obj, list):
        return [_walk(v, f, key, sens, known_secret) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, f, key, sens, known_secret) for v in obj)
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
