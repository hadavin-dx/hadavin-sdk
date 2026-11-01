"""A small row store with copy-on-read, snapshot iteration and audit-before-write.

Not the migration ledger (``store.migrate``): this is a keyed set of JSON-shaped rows a control keeps (holds,
reservations, approvals). Rules it enforces so callers cannot get them wrong:

* a row is validated and copied FIRST (string keys only, no NaN/Infinity, JSON-serialisable), so a bad row fails
  before anything is audited;
* the audit event is written BEFORE the row exists, and a failed audit write inserts nothing;
* the audit write (I/O) runs OUTSIDE the lock: the key is reserved under the lock, the lock is released for the
  audit call, and the row is inserted (or the reservation dropped) afterwards, so an audit callback may call
  ``snapshot`` without deadlock and a slow audit store never blocks readers;
* readers get copies (``get``, ``snapshot``); the rows themselves are private.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any, Protocol


class DuplicateKey(KeyError):
    pass


def json_keys_ok(o: Any) -> bool:
    """True if every dict key anywhere in ``o`` is a string and no tuple or set is present. A tuple key raises in a
    JSON round trip and an int key is silently turned into a string, so check BEFORE copying."""
    if isinstance(o, dict):
        return all(type(k) is str and json_keys_ok(v) for k, v in o.items())
    if isinstance(o, list):
        return all(json_keys_ok(v) for v in o)
    return not isinstance(o, (tuple, set, frozenset))


def copy_row(o: Any) -> Any:
    """A validated JSON-shaped deep copy. Raises ``ValueError`` for non-string keys, tuples, sets, NaN or Infinity."""
    if not json_keys_ok(o):
        raise ValueError("a row may hold only string keys and no tuple or set")
    try:
        return json.loads(json.dumps(o, allow_nan=False))
    except (TypeError, ValueError) as e:
        raise ValueError(f"row is not JSON-serialisable: {type(e).__name__}") from e


class RowStoreLike(Protocol):
    def put_audited(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None: ...
    def get(self, key: str) -> Any: ...
    def keys(self) -> list[str]: ...
    def snapshot(self) -> dict[str, Any]: ...


class RowStore:
    def __init__(self) -> None:
        self._rows: dict[str, Any] = {}
        self._pending: set[str] = set()
        self._lock = threading.Lock()

    def put_audited(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None:
        if type(key) is not str or not key:
            raise ValueError("a key is a non-empty string")
        clean = copy_row(row)  # validate and copy first
        with self._lock:
            if key in self._rows or key in self._pending:
                raise DuplicateKey(key)
            self._pending.add(key)
        try:
            append(kind, key=key)  # audit before the write; raises -> nothing is inserted
            with self._lock:
                self._rows[key] = clean
        finally:
            with self._lock:
                self._pending.discard(key)

    def get(self, key: str) -> Any:
        with self._lock:
            return copy_row(self._rows[key])

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._rows)

    def snapshot(self) -> dict[str, Any]:
        """Copies of every row, taken under the lock."""
        with self._lock:
            return {k: copy_row(v) for k, v in self._rows.items()}
