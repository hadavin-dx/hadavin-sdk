"""Capped audit for events an outsider can cause at will (a refused attempt).

At most ``cap`` rows per (tenant, kind, bucket) (a bucket is for example a UTC day); the first event past the cap writes ONE
``audit_suppressed`` row and the rest are only counted (``suppressed()``). The marker write is reserved under the lock before it is
written and rolled back, with a growing back-off, if it fails (no duplicate marker, no I/O on every suppressed event). Memory is
bounded: at most ``max_keys`` (tenant, kind) counters, one bucket each, and at most ``max_kinds`` distinct kinds (further kinds share the
kind ``*``); when the table is full, a new key shares the overflow counter of its kind, which no real tenant name can collide with and
whose marker names the tenant ``*``. A tenant name and a kind are clipped to 64 characters. Stale buckets are purged once per bucket
change, not on every new key. The cap is per process: N workers allow N x cap rows.
Never use it for an event that guards an action; those are written strictly before the action (``intent=True`` uses
``write_intent`` and raises ``AuditUnavailable``).

``append`` is any callable ``append(kind, **fields)``; ``sink_append`` adapts an ``AuditSink``. The ``AuditEvent`` model has no tenant,
bucket or suppressed-kind field, so they are encoded in ``object_ref`` ("tenant|key", with ``%`` and ``|`` in the tenant escaped as ``%25`` and ``%7C``) and ``error_code`` ("kind@bucket", or
"suppressed_kind@bucket" on the marker). The model carries hashes and codes only, never payload text.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from hadavin_sdk.models import AuditEvent

_TENANT_MAX = 64
_KIND_MAX = 64
_OVERFLOW = None  # tenant part of the overflow key: a real tenant name is always a string


def sink_append(
    sink: Any,
    run_id: str,
    domain: str,
    principal: str = "?",
    source: str = "gate",
    *,
    decision: str | None = "deny",
    result: str | None = "refused",
    intent: bool = False,
) -> Callable[..., Any]:
    """Adapt an ``AuditSink`` to ``append(kind, **fields)``. ``intent=True`` writes with ``write_intent`` (audit-before-write: raises
    ``AuditUnavailable``); otherwise ``write_outcome`` (never raises, queues in the outbox). ``decision`` and ``result`` are parameters
    (a hold creation is not a refusal)."""

    def append(kind: str, **fields: Any) -> Any:
        tenant = (
            str(fields.get("tenant") or "-")[:_TENANT_MAX].replace("%", "%25").replace("|", "%7C")
        )
        ref = str(fields.get("object_ref") or fields.get("key") or "-")
        bucket = str(fields.get("bucket") or "")
        sk = str(fields.get("suppressed_kind") or "")
        code = fields.get("error_code") or (
            f"{sk}@{bucket}" if sk else (f"{kind}@{bucket}" if bucket else None)
        )
        event = AuditEvent(
            run_id=run_id, domain=domain, operation=kind, principal=principal, source=source, object_ref=f"{tenant}|{ref}",
            decision=decision, result=result, error_code=code,
        )  # fmt: skip
        return sink.write_intent(event) if intent else sink.write_outcome(event)

    return append


class CappedAudit:
    def __init__(
        self, append: Callable[..., Any], cap: int, *, max_keys: int = 10_000, max_kinds: int = 64
    ) -> None:
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be an int >= 1")
        if type(max_keys) is not int or max_keys < 1:
            raise ValueError("max_keys must be an int >= 1")
        if type(max_kinds) is not int or max_kinds < 1:
            raise ValueError("max_kinds must be an int >= 1")
        self._append, self._cap, self._max_keys, self._max_kinds = append, cap, max_keys, max_kinds
        self._lock = threading.Lock()
        # (tenant or None for overflow, kind) -> [bucket, count, marker written, marker failures, suppressed events to skip before the next marker try]
        self._n: dict[tuple[str | None, str], list[Any]] = {}
        self._kinds: set[str] = set()
        self._bucket: str | None = None  # the bucket the last purge ran for

    def _slot(
        self, tenant: str, kind: str, bucket: str
    ) -> tuple[tuple[str | None, str], list[Any]]:
        if bucket != self._bucket:  # a new bucket: drop every counter of an old one, once
            self._n = {k: v for k, v in self._n.items() if v[0] == bucket}
            self._bucket = bucket
        if kind not in self._kinds:
            if len(self._kinds) >= self._max_kinds:
                kind = "*"
            else:
                self._kinds.add(kind)
        key: tuple[str | None, str] = (tenant[:_TENANT_MAX], kind)
        if key not in self._n and len(self._n) >= self._max_keys:
            key = (_OVERFLOW, kind)  # one shared counter per kind
        slot = self._n.get(key)
        if slot is None:  # a counter of an older bucket was purged above
            slot = self._n[key] = [bucket, 0, False, 0, 0]
        return key, slot

    def append(self, tenant: str, kind: str, bucket: str, /, **fields: Any) -> bool:
        kind = str(kind)[:_KIND_MAX]
        with self._lock:
            key, slot = self._slot(tenant, kind, bucket)
            slot[1] += 1
            over = slot[1] > self._cap
            need_marker = False
            if over and not slot[2]:
                if slot[4] > 0:
                    slot[4] -= 1  # back off after a failed marker write
                else:
                    slot[2], need_marker = True, True  # reserved under the lock: no second writer
        if over:
            if need_marker:
                try:
                    self._append(
                        "audit_suppressed",
                        tenant="*" if key[0] is _OVERFLOW else tenant[:_TENANT_MAX],
                        suppressed_kind=key[1],
                        bucket=bucket,
                    )
                except Exception:
                    with self._lock:
                        slot[2], slot[3] = False, slot[3] + 1
                        slot[4] = min(2 ** slot[3], 1024)
                    raise
            return False
        safe = {
            ("field_" + k if k in ("kind", "tenant") else k): v for k, v in fields.items()
        }  # reserved names are renamed, never collide
        self._append(kind, **{**safe, "tenant": tenant[:_TENANT_MAX]})
        return True

    def deny(self, tenant: str, kind: str, bucket: str, /, **fields: Any) -> None:
        """``append`` that never raises: a failed audit write must not turn a refusal into another error."""
        try:
            self.append(tenant, kind, bucket, **fields)
        except Exception:  # noqa: BLE001, S110 - the refusal itself is what matters
            pass

    def suppressed(self, tenant: str, kind: str, bucket: str | None = None) -> int:
        """Events past the cap for THIS tenant and kind in the current bucket; 0 for a tenant never seen (or one that shares the overflow
        counter: ask ``overflow_suppressed``), and 0 if ``bucket`` is given and is not the current one."""
        return self._count((tenant[:_TENANT_MAX], str(kind)[:_KIND_MAX]), bucket)

    def overflow_suppressed(self, kind: str, bucket: str | None = None) -> int:
        """Events past the cap on the shared overflow counter of ``kind`` (all tenants that did not get a counter of their own)."""
        return self._count((_OVERFLOW, str(kind)[:_KIND_MAX]), bucket)

    def _count(self, key: tuple[str | None, str], bucket: str | None) -> int:
        with self._lock:
            slot = self._n.get(key)
            if slot is None and key[0] is not _OVERFLOW and key[1] not in self._kinds:
                slot = self._n.get((key[0], "*"))  # a kind past max_kinds is counted under "*"
            if slot is None or (bucket is not None and slot[0] != bucket):
                return 0
            return max(0, slot[1] - self._cap)
