"""Capped audit for events an outsider can cause at will (a refused attempt).

At most ``cap`` rows per (tenant, kind, bucket) (a bucket is for example a UTC day); the first event past the cap
writes ONE ``audit_suppressed`` row (retried on the next suppressed event if that write failed) and the rest are only
counted, and the count is readable (``suppressed``). Counters are per tenant and only the current bucket of each
(tenant, kind) is kept, so memory is bounded by tenants x kinds. Never use it for an event that guards an action:
those are written strictly before the action.

``append`` is any callable ``append(kind, **fields)``; ``sink_append`` adapts an ``AuditSink`` (whose methods take an
``AuditEvent``)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from hadavin_sdk.models import AuditEvent


def sink_append(
    sink: Any, run_id: str, domain: str, principal: str = "?", source: str = "gate"
) -> Callable[..., Any]:
    """Adapt an ``AuditSink`` to ``append(kind, **fields)``. Fields other than ``object_ref`` / ``error_code`` are dropped
    (an ``AuditEvent`` carries hashes and codes only, never payload text)."""

    def append(kind: str, **fields: Any) -> Any:
        return sink.write_outcome(
            AuditEvent(
                run_id=run_id,
                domain=domain,
                operation=kind,
                principal=principal,
                source=source,
                object_ref=str(fields.get("object_ref") or fields.get("key") or "-"),
                decision="deny",
                result="refused",
                error_code=fields.get("error_code"),
            )
        )

    return append


class CappedAudit:
    def __init__(self, append: Callable[..., Any], cap: int) -> None:
        if not (isinstance(cap, int) and cap >= 1):
            raise ValueError("cap must be an int >= 1")
        self._append, self._cap = append, cap
        self._lock = threading.Lock()
        self._n: dict[
            tuple[str, str], tuple[str, int, bool]
        ] = {}  # (tenant, kind) -> (bucket, count, marker written)

    def append(self, tenant: str, kind: str, bucket: str, **fields: Any) -> bool:
        with self._lock:
            b, n, marked = self._n.get((tenant, kind), (bucket, 0, False))
            if b != bucket:
                b, n, marked = bucket, 0, False
            n += 1
            self._n[(tenant, kind)] = (b, n, marked)
            over, need_marker = n > self._cap, n > self._cap and not marked
        if over:
            if need_marker:
                self._append("audit_suppressed", tenant=tenant, suppressed_kind=kind, bucket=bucket)
                with self._lock:
                    cur = self._n[(tenant, kind)]
                    if cur[0] == bucket:
                        self._n[(tenant, kind)] = (cur[0], cur[1], True)
            return False
        self._append(kind, tenant=tenant, **fields)
        return True

    def deny(self, tenant: str, kind: str, bucket: str, **fields: Any) -> None:
        """``append`` that never raises: a failed audit write must not turn a refusal into another error."""
        try:
            self.append(tenant, kind, bucket, **fields)
        except Exception:  # noqa: BLE001, S110 - the refusal itself is what matters
            pass

    def suppressed(self, tenant: str, kind: str) -> int:
        with self._lock:
            _, n, _ = self._n.get((tenant, kind), ("", 0, False))
            return max(0, n - self._cap)
