"""A small row store with copy-on-read, snapshot iteration and audit-before-write.

Not the migration ledger (``store.migrate``): this is a keyed set of JSON-shaped rows a control keeps (holds,
reservations, approvals). Rules it enforces so callers cannot get them wrong:

* a row is validated and copied FIRST (string keys only, no NaN/Infinity, JSON-serialisable), so a bad row fails
  before anything is audited;
* the audit event is written BEFORE the row exists, and a failed audit write inserts nothing;
* the audit write (I/O) runs OUTSIDE the lock: the key is reserved under the lock, the lock is released for the
  audit call, and the row is inserted (or the reservation dropped) afterwards, so an audit callback may call
  ``snapshot`` without deadlock and a slow audit store never blocks readers;
* readers get copies (``get``, ``snapshot``); the rows themselves are private;
* ``update_audited`` / ``delete_audited`` follow the same order (a hold becomes released; a row is removed);
* scope: ONE store holds ONE collection (one tenant, one kind of row): create one per tenant. ``max_rows`` bounds it, ``max_key_chars``
  (default 256) bounds a key, ``max_row_bytes`` (default 65,536 bytes of ASCII-escaped JSON; the row is walked first with a lower-bound count, so an oversized row is refused after about that much work and a huge string costs a length check; ``None`` opts out)
  bounds a row and ``max_total_bytes`` (default 64 MiB of the same plus the keys, ``None`` opts out) bounds the whole store (``StoreFull``); a ``None`` limit needs ``allow_unbounded=True``: a key and a
  row come from outside, and the key goes into the audit event. ``snapshot`` copies every row under the lock (O(rows)): do not call it per
  request on a large store.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any, Protocol


class DuplicateKey(KeyError):
    """The key is already stored."""


class KeyPending(Exception):
    """Another caller is writing this key right now (its audit write has not finished): retry, do not treat the key as stored."""


class StoreFull(Exception):
    pass


def json_keys_ok(o: Any, _depth: int = 0) -> bool:
    """True if every dict key anywhere in ``o`` is a string and no tuple or set is present. A tuple key raises in a
    JSON round trip and an int key is silently turned into a string, so check BEFORE copying."""
    if _depth > 100:
        return False  # too deep to be a row
    if isinstance(o, dict):
        return all(type(k) is str and json_keys_ok(v, _depth + 1) for k, v in o.items())
    if isinstance(o, list):
        return all(json_keys_ok(v, _depth + 1) for v in o)
    return not isinstance(o, (tuple, set, frozenset))


def _walk(o: Any, budget: list[int], depth: int = 0) -> None:
    """Validate the shape of a row and spend ``budget`` (a lower bound of its JSON size: a string costs its length, a key its length, every
    node a few bytes) while walking, so a row over the cap is refused after about ``max_bytes`` of work, and a huge string costs one length
    check, not an encoding. Raises ``ValueError``."""
    if depth > 100:
        raise ValueError("a row is nested too deep")
    if isinstance(o, dict):
        budget[0] -= 2
        for k, v in o.items():
            if type(k) is not str:
                raise ValueError("a row may hold only string keys and no tuple or set")
            budget[0] -= len(k) + 4
            if budget[0] < 0:
                raise ValueError("a row is over max_row_bytes")
            _walk(v, budget, depth + 1)
    elif isinstance(o, list):
        budget[0] -= 2
        for v in o:
            budget[0] -= 1
            if budget[0] < 0:
                raise ValueError("a row is over max_row_bytes")
            _walk(v, budget, depth + 1)
    elif isinstance(o, (tuple, set, frozenset)):
        raise ValueError("a row may hold only string keys and no tuple or set")  # noqa: TRY004 - the contract is ValueError
    elif isinstance(o, str):
        budget[0] -= len(o) + 2
    else:
        budget[0] -= 4
    if budget[0] < 0:
        raise ValueError("a row is over max_row_bytes")


def _validated(o: Any, max_bytes: int | None, key: str = "") -> tuple[Any, int]:
    """(the deep copy, its size in bytes: ASCII-escaped JSON text plus the key). The walk above refuses an oversized row after bounded work
    (about ``max_bytes``, the string lengths counted without encoding them); the exact size is then taken from the encoded text, which is at
    most six times the walk's bound, so the encoding work is bounded too."""
    _walk(o, [max_bytes if max_bytes is not None else 1 << 62])
    try:
        text = json.dumps(o, allow_nan=False)
    except (TypeError, RecursionError) as e:
        raise ValueError(f"row is not JSON-serialisable: {type(e).__name__}") from e
    except ValueError as e:
        raise ValueError(f"row is not JSON-serialisable: {type(e).__name__}") from e
    if max_bytes is not None and len(text) > max_bytes:
        raise ValueError("a row is over max_row_bytes")
    return json.loads(text), len(text) + len(key)


def copy_row(o: Any, max_bytes: int | None = None) -> Any:
    """A validated JSON-shaped deep copy. Raises ``ValueError`` for non-string keys, tuples, sets, NaN or Infinity, and for a row whose
    JSON text (ASCII-escaped, as ``json.dumps`` writes it) is over ``max_bytes`` (when given)."""
    return _validated(o, max_bytes)[0]


class RowStoreLike(Protocol):
    def put_audited(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None: ...
    def get(self, key: str) -> Any: ...
    def keys(self) -> list[str]: ...
    def snapshot(self) -> dict[str, Any]: ...


DEFAULT_MAX_ROWS = (
    100_000  # one collection of one tenant; ``max_rows=None`` is the explicit opt-out
)
DEFAULT_MAX_KEY_CHARS = 256
DEFAULT_MAX_ROW_BYTES = (
    65_536  # ASCII-escaped JSON bytes; ``max_row_bytes=None`` is the explicit opt-out
)
DEFAULT_MAX_TOTAL_BYTES = 67_108_864  # 64 MiB of ASCII-escaped JSON in one store; ``max_total_bytes=None`` is the explicit opt-out


class RowStore:
    def __init__(
        self,
        max_rows: int | None = DEFAULT_MAX_ROWS,
        *,
        allow_unbounded: bool = False,
        max_key_chars: int = DEFAULT_MAX_KEY_CHARS,
        max_row_bytes: int | None = DEFAULT_MAX_ROW_BYTES,
        max_total_bytes: int | None = DEFAULT_MAX_TOTAL_BYTES,
    ) -> None:
        unbounded_ok = allow_unbounded or None not in (max_rows, max_row_bytes, max_total_bytes)
        if not unbounded_ok:
            raise ValueError(
                "a store without a limit needs allow_unbounded=True (the opt-out has a name)"
            )
        if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
            raise ValueError("max_rows must be None or an int >= 1")
        if type(max_key_chars) is not int or max_key_chars < 1:
            raise ValueError("max_key_chars must be an int >= 1")
        if max_row_bytes is not None and (type(max_row_bytes) is not int or max_row_bytes < 2):
            raise ValueError("max_row_bytes must be None or an int >= 2")
        if max_total_bytes is not None and (
            type(max_total_bytes) is not int or max_total_bytes < 2
        ):
            raise ValueError("max_total_bytes must be None or an int >= 2")
        self._max_key_chars, self._max_row_bytes = max_key_chars, max_row_bytes
        self._max_total_bytes = max_total_bytes
        self._sizes: dict[str, int] = {}  # key -> bytes of the stored row
        self._reserved: dict[str, int] = {}  # key -> bytes added by the write in flight
        self._total = 0  # bytes of all stored rows
        self._rows: dict[str, Any] = {}
        self._pending: set[str] = set()
        self._lock = threading.Lock()
        self._max_rows = max_rows

    def _write_audited(
        self, op: str, append: Callable[..., Any], kind: str, key: str, row: Any
    ) -> None:
        if type(key) is not str or not key:
            raise ValueError("a key is a non-empty string")
        if len(key) > self._max_key_chars:
            raise ValueError("a key is over max_key_chars")
        # validate and copy first
        clean, size = _validated(row, self._max_row_bytes, key) if op != "delete" else (None, 0)
        with self._lock:
            if key in self._pending:
                raise KeyPending(key)
            if op == "put" and key in self._rows:
                raise DuplicateKey(key)
            if op != "put" and key not in self._rows:
                raise KeyError(key)
            if (
                op == "put"
                and self._max_rows is not None
                and len(self._rows) + len(self._pending) >= self._max_rows
            ):
                raise StoreFull(key)
            delta = size - self._sizes.get(key, 0)
            if (
                op != "delete"
                and self._max_total_bytes is not None
                and self._total + sum(self._reserved.values()) + delta > self._max_total_bytes
            ):
                raise StoreFull(key)
            self._pending.add(key)
            self._reserved[key] = max(delta, 0)
        try:
            append(kind, key=key)  # audit before the write; raises -> nothing is changed
            with self._lock:
                if op == "delete":
                    del self._rows[key]
                    self._total -= self._sizes.pop(key, 0)
                else:
                    self._rows[key] = clean
                    self._total += size - self._sizes.get(key, 0)
                    self._sizes[key] = size
        finally:
            with self._lock:
                self._pending.discard(key)
                self._reserved.pop(key, None)

    def put_audited(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None:
        self._write_audited("put", append, kind, key, row)

    def update_audited(self, append: Callable[..., Any], kind: str, key: str, row: Any) -> None:
        self._write_audited("update", append, kind, key, row)

    def delete_audited(self, append: Callable[..., Any], kind: str, key: str) -> None:
        self._write_audited("delete", append, kind, key, None)

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
