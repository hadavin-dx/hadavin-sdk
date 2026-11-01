"""A refusal as an audit event, in a no-PII form: a code, the caller's identity LABEL (or "?") and the business key (or "-"); never request
content. Every refusal path calls this so "refused" is as visible as "applied"."""

from __future__ import annotations

import re

from hadavin_sdk.models import AuditEvent

_LABEL = re.compile(r"[a-z0-9_.-]{1,40}")


def label(identity: object) -> str:
    return identity if isinstance(identity, str) and _LABEL.fullmatch(identity) else "?"


def refusal_event(
    run_id: str, domain: str, code: str, identity: object, key: str | None = None
) -> AuditEvent:
    return AuditEvent(
        run_id=run_id, domain=domain, operation="refused", principal=label(identity), source="gate", object_ref=key or "-",
        decision="deny", result="refused", error_code=code,
    )  # fmt: skip
