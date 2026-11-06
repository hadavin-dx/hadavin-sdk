"""Keyed labels for people and processes: the audit trail and the stop tables never hold a typed name.

A label is `id:<key_id>:<32 hex digits of HMAC-SHA256 under the label key>`. The hash gives privacy, not
authenticity: whoever holds the key can compute the label of any name (`limits whois NAME`), and a name typed by
a caller is not proof of who called.
"""

from __future__ import annotations

import hashlib
import hmac
import re

# `re.fullmatch` everywhere: Python's `$` accepts a trailing newline, PostgreSQL's does not.
KEY_ID_PATTERN = r"[A-Za-z0-9_-]{1,32}"
LABEL_PATTERN = rf"id:{KEY_ID_PATTERN}:[0-9a-f]{{32}}"
_KEY_ID = re.compile(KEY_ID_PATTERN)
_LABEL = re.compile(LABEL_PATTERN)
# Used by a stop when the key is unreadable (a stop is never refused for a key problem).
NOKEY_LABEL = "id:nokey:" + "0" * 32
UNIDENTIFIED = "unidentified"


def valid_key_id(key_id: object) -> bool:
    return isinstance(key_id, str) and _KEY_ID.fullmatch(key_id) is not None


def is_label(text: object) -> bool:
    return isinstance(text, str) and _LABEL.fullmatch(text) is not None


def keyed_hex(key: bytes, text: str) -> str:
    """32 hex digits of HMAC-SHA256(key, text). Lone surrogates are encoded, not replaced, so two different
    names never share bytes."""
    return hmac.new(key, text.encode("utf-8", "surrogatepass"), hashlib.sha256).hexdigest()[:32]


def mask_principal(principal: object, key: bytes, key_id: str) -> str:
    """The label of ANY principal. Never raises on its input: a non-string is turned into text, an empty one
    becomes `unidentified`. `key_id` must already be valid (checked at configuration time)."""
    text = principal if isinstance(principal, str) else str(principal)
    return f"id:{key_id}:{keyed_hex(key, text or UNIDENTIFIED)}"
