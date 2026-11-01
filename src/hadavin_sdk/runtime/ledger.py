"""Ledger helpers: copy on read, snapshot under the lock, audit before write, capped refusal audits.

Vendor-neutral and stdlib only; ``append`` is any callable that writes one audit event and raises on failure."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any


def copy_deep(o: Any) -> Any:
    """A JSON-shaped deep copy: a reader never holds a handle on live ledger data."""
    return json.loads(json.dumps(o))


def json_keys_ok(o: Any) -> bool:
    """True if every dict key anywhere in ``o`` is a string and no tuple or set is present. Check this BEFORE a
    JSON round trip: a tuple key raises there and an int key is silently turned into a string."""
    if isinstance(o, dict):
        return all(type(k) is str and json_keys_ok(v) for k, v in o.items())
    if isinstance(o, list):
        return all(json_keys_ok(v) for v in o)
    return not isinstance(o, (tuple, set, frozenset))


class Ledger:
    """A dict of rows with one lock: ``snapshot`` copies under the lock (iterating the live dict while a writer
    inserts raises RuntimeError), ``write_after_audit`` writes the audit event first and the row only if that
    succeeded (a failed audit write writes nothing)."""

    def __init__(self) -> None:
        self.rows: dict[str, Any] = {}
        self.lock = threading.Lock()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {k: copy_deep(v) for k, v in self.rows.items()}

    def write_after_audit(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None:
        with self.lock:
            append(kind, key=key)
            self.rows[key] = copy_deep(row)


class CappedAudit:
    """For events an outsider can make at will (a refused attempt): at most ``cap`` rows per kind per bucket
    (for example a UTC day); the first one past it writes a single ``audit_suppressed`` row and the rest are
    only counted. Never use it for an event that guards an action. ``deny`` never raises."""

    def __init__(self, append: Callable[..., Any], cap: int) -> None:
        self._append, self._cap = append, cap
        self._n: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()

    def append(self, kind: str, bucket: str, **fields: Any) -> bool:
        with self._lock:
            n = self._n[(kind, bucket)] = self._n.get((kind, bucket), 0) + 1
        if n > self._cap:
            if n == self._cap + 1:
                self._append("audit_suppressed", suppressed_kind=kind, bucket=bucket)
            return False
        self._append(kind, **fields)
        return True

    def deny(self, kind: str, bucket: str, **fields: Any) -> None:
        try:
            self.append(kind, bucket, **fields)
        except Exception:  # noqa: BLE001, S110 - the refusal itself is what matters
            pass
