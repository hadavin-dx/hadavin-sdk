"""Capped audit for events an outsider can cause at will (a refused attempt).

At most ``cap`` rows per (tenant, kind, bucket) (a bucket is for example a UTC day); the first event past the cap writes ONE
``audit_suppressed`` row and the rest are only counted (``suppressed()``). The marker write is reserved under the lock before it is
written and rolled back, with a growing back-off, if it fails (no duplicate marker, no I/O on every suppressed event). Memory is
bounded: at most ``max_keys`` (tenant, kind) counters, one bucket each, and at most ``max_kinds`` distinct kinds (further kinds share the
kind ``*``); when the table is full, a new key shares the overflow counter of its kind, which no real tenant name can collide with and
whose marker names the tenant ``*``. A tenant name (after the escaping below) and a kind are clipped to 64 characters, an object reference or
key to 128 and an error code to 96; ``sink_append`` redacts every one of them first (``_clip``), because an outsider chooses them and the
audit is append-only. The counters of the two GREATEST buckets are kept (buckets sort: a late event of the previous bucket, as at midnight, neither resets
nor bypasses a counter; a bucket older than both is suppressed and never evicts a newer one); older ones are purged once per bucket change,
not on every new key. ``max_keys`` counts the counters of ONE bucket (the table of each kept bucket), so a key flood on day N cannot send day N+1 tenants to
the overflow counter. Control characters are replaced by spaces, only the first limit + 1024 characters of a value are redacted, and a value the
redactor refuses is written as ``(details withheld; len=N; sha8=...)``. The cap is per process: N workers allow N x cap rows.
Never use it for an event that guards an action; those are written strictly before the action (``intent=True`` uses
``write_intent`` and raises ``AuditUnavailable``).

``append`` is any callable ``append(kind, **fields)``; ``sink_append`` adapts an ``AuditSink``. The ``AuditEvent`` model has no tenant,
bucket or suppressed-kind field, so they are encoded in ``object_ref`` ("tenant|key", with ``%`` and ``|`` in the tenant escaped as ``%25`` and ``%7C``) and ``error_code`` ("kind@bucket", or
"suppressed_kind@bucket" on the marker). The model carries hashes and codes only, never payload text.
"""

from __future__ import annotations

import functools
import hashlib
import threading
from collections.abc import Callable
from typing import Any

from hadavin_sdk.guard.runmap import RedactionError, redact_bounded
from hadavin_sdk.models import AuditEvent

_TENANT_MAX = 64
_KIND_MAX = 64
_REF_MAX = 128  # an object reference or key, after redaction
_CODE_MAX = 96  # an error code ("kind@bucket")
_OVERFLOW = None  # tenant part of the overflow key: a real tenant name is always a string


_PRE_MARGIN = 1024  # characters kept beyond the limit before redaction, so a secret that straddles the limit is redacted whole
_CTRL = {
    c: " " for c in (*range(32), *range(127, 160), 0x2028, 0x2029)
}  # C0, C1, line and paragraph separators


@functools.lru_cache(maxsize=4096)
def _redact_head(head: str, limit: int, n: int, digest: str) -> str:
    try:
        return redact_bounded(head, {})[0][:limit]
    except RedactionError:  # too large or too deep: say that, with a way to tell two hostile values apart, and no content
        return f"(details withheld; len={n}; sha8={digest})"


def _clip(value: Any, limit: int) -> str:
    """The text for an append-only audit field: control characters (C0, C1, line and paragraph separators) become spaces; only the first
    ``limit`` + 1024 characters are ever redacted (what lies beyond ``limit`` is dropped anyway, so a secret that straddles the cut can never show), THEN the result is clipped to ``limit``. A value the redactor refuses becomes ``(details withheld; len=N; sha8=...)``, where
    ``sha8`` is the first 8 hex digits of the SHA-256 of the raw text (no content). Outsider-chosen text never reaches the audit whole."""
    text = value if isinstance(value, str) else str(value)
    n = len(text)
    head = text[: limit + _PRE_MARGIN].translate(_CTRL)
    digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:8]
    return _redact_head(head, limit, n, digest)


def _name(tenant: Any) -> str:
    """The tenant as the audit shows it: ``_clip`` of the name (redacted BEFORE the clip to 64), a non-string by its ``repr``."""
    return _clip(tenant if isinstance(tenant, str) else repr(tenant), _TENANT_MAX)


def _key_name(tenant: Any) -> str:
    """The tenant (or bucket) as a counter key: the name as it is (a name is data; redacting it would merge numeric ids), a non-string by its
    ``repr``, the first 64 characters (names equal in those 64 share a counter, as documented). The key is never audited, so no fragment of
    a secret is shown through it; the audit shows ``_name``."""
    text = tenant if isinstance(tenant, str) else repr(tenant)
    return text[:_TENANT_MAX]


def _tenant_ref(tenant: Any) -> str:
    """The tenant part of ``object_ref``: redacted and clipped, ``%`` and ``|`` escaped, the ESCAPED text at most ``_TENANT_MAX`` characters
    (an escape is never cut in the middle)."""
    out, n = [], 0
    for ch in _name(tenant):
        e = "%25" if ch == "%" else "%7C" if ch == "|" else ch
        if n + len(e) > _TENANT_MAX:
            break
        out.append(e)
        n += len(e)
    return "".join(out)


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
        tenant = _tenant_ref(fields.get("tenant") or "-")
        ref = _clip(fields.get("object_ref") or fields.get("key") or "-", _REF_MAX)
        kind = _clip(kind, _KIND_MAX)
        bucket = _clip(fields.get("bucket") or "", _KIND_MAX)
        sk = _clip(fields.get("suppressed_kind") or "", _KIND_MAX)
        code = fields.get("error_code") or (
            f"{sk}@{bucket}" if sk else (f"{kind}@{bucket}" if bucket else None)
        )
        event = AuditEvent(
            run_id=run_id, domain=domain, operation=kind, principal=principal, source=source, object_ref=f"{tenant}|{ref}",
            decision=decision, result=result, error_code=_clip(code, _CODE_MAX) if code else None,
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
        # (tenant or None for overflow, kind, bucket) -> [bucket, count, marker written, marker failures, suppressed events to skip before the next marker try]
        self._n: dict[tuple[str | None, str, str], list[Any]] = {}
        self._kinds: set[str] = set()
        self._buckets: list[
            str
        ] = []  # the two GREATEST buckets seen (ascending): their counters are kept
        self._cnt: dict[
            str, int
        ] = {}  # bucket -> number of counters in it (max_keys counts the CURRENT bucket only)

    def _slot(
        self, tenant: str, kind: str, bucket: str
    ) -> tuple[tuple[str | None, str, str], list[Any]]:
        # a new bucket: keep the two GREATEST (buckets sort: a UTC day is ISO text), drop the counters of the rest, once. A bucket older
        # than both kept ones is stale: its events are suppressed, not written (it never evicts a newer one, so d1, d2, d3, d1 cannot reset anything).
        stale = False
        if bucket not in self._buckets:
            kept = sorted([*self._buckets, bucket])[-2:]
            stale = bucket not in kept
            if not stale:
                self._buckets = kept
                self._n = {k: v for k, v in self._n.items() if k[2] in kept}
                self._cnt = dict.fromkeys(kept, 0)
                for k in self._n:
                    self._cnt[k[2]] += 1
        if kind not in self._kinds:
            if len(self._kinds) >= self._max_kinds:
                kind = "*"
            else:
                self._kinds.add(kind)
        key: tuple[str | None, str, str] = (tenant, kind, bucket)
        if stale:
            # a transient counter that is already over the cap and has its marker "written": the event is suppressed, nothing is stored
            return key, [bucket, self._cap, True, 0, 0]
        if key not in self._n and self._cnt.get(bucket, 0) >= self._max_keys:
            key = (
                _OVERFLOW,
                kind,
                bucket,
            )  # one shared counter per kind (the table of THIS bucket is full)
        slot = self._n.get(key)
        if slot is None:
            slot = self._n[key] = [bucket, 0, False, 0, 0]
            self._cnt[bucket] = self._cnt.get(bucket, 0) + 1
        return key, slot

    def append(self, tenant: str, kind: str, bucket: str, /, **fields: Any) -> bool:
        # a non-string tenant is a name, not a TypeError
        shown, tenant = _name(tenant), _key_name(tenant)
        bucket = _key_name(bucket)  # a long bucket is hashed in the key like a long tenant
        kind = _clip(kind, _KIND_MAX)
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
                        tenant="*" if key[0] is _OVERFLOW else shown,
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
        self._append(kind, **{**safe, "tenant": shown})
        return True

    def deny(self, tenant: str, kind: str, bucket: str, /, **fields: Any) -> None:
        """``append`` that never raises: a failed audit write must not turn a refusal into another error."""
        try:
            self.append(tenant, kind, bucket, **fields)
        except Exception:  # noqa: BLE001, S110 - the refusal itself is what matters
            pass

    def suppressed(self, tenant: str, kind: str, bucket: str | None = None) -> int:
        """Events past the cap for THIS tenant and kind in ``bucket`` (default: the latest bucket seen); 0 for a tenant never seen (or one
        that shares the overflow counter: ask ``overflow_suppressed``), and 0 for a bucket that is not one of the two greatest kept."""
        return self._count((_key_name(tenant), _clip(kind, _KIND_MAX)), bucket)

    def overflow_suppressed(self, kind: str, bucket: str | None = None) -> int:
        """Events past the cap on the shared overflow counter of ``kind`` (all tenants that did not get a counter of their own)."""
        return self._count((_OVERFLOW, _clip(kind, _KIND_MAX)), bucket)

    def _count(self, key: tuple[str | None, str], bucket: str | None) -> int:
        with self._lock:
            if bucket is None:
                if not self._buckets:
                    return 0
                bucket = self._buckets[-1]  # the current (greatest) bucket
            else:
                bucket = _key_name(bucket)
            slot = self._n.get((*key, bucket))
            if slot is None and key[0] is not _OVERFLOW and key[1] not in self._kinds:
                slot = self._n.get(
                    (key[0], "*", bucket)
                )  # a kind past max_kinds is counted under "*"
            return 0 if slot is None else max(0, slot[1] - self._cap)
