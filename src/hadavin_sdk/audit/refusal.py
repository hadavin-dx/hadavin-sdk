"""A refusal as an audit event, in a form that cannot carry caller-controlled content.

Every field that can come from a caller (the identity label, the business key, the code) passes an allow-list; anything
that does not match is replaced by `h:` plus a SHA-256 prefix of it, so the log still tells two different callers apart
without holding their text (an e-mail address, a newline, a 10 KB string). Use `refusal_fields` with
`audit.capped.CappedAudit.deny` (one capped row per kind and bucket, then a single `audit_suppressed` row) so a caller
cannot grow the log at will, or `refusal_event` to write one event directly.
"""

from __future__ import annotations

import hashlib
import re

from hadavin_sdk.models import AuditEvent

_LABEL = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_KEY = re.compile(r"[A-Za-z0-9_.:-]{1,128}")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")


def _safe(value: object, rx: re.Pattern[str]) -> str:
    if isinstance(value, str) and rx.fullmatch(value):
        return value
    raw = value if isinstance(value, str) else f"<{type(value).__name__}>"
    return "h:" + hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16]


def label(identity: object) -> str:
    return _safe(identity, _LABEL)


def refusal_fields(code: object, identity: object, key: object = None) -> dict[str, str]:
    """`error_code`, `object_ref` and `principal`, each safe to write."""
    return {
        "error_code": _safe(code, _CODE),
        "object_ref": "-" if key is None else _safe(key, _KEY),
        "principal": label(identity),
    }


def refusal_event(
    run_id: str, domain: str, code: object, identity: object, key: object = None
) -> AuditEvent:
    f = refusal_fields(code, identity, key)
    return AuditEvent(
        run_id=_safe(run_id, _KEY),
        domain=_safe(domain, _LABEL),
        operation="refused",
        principal=f["principal"],
        source="gate",
        object_ref=f["object_ref"],
        decision="deny",
        result="refused",
        error_code=f["error_code"],
    )
