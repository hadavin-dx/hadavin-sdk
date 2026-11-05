"""The verbose log and the per-item trace (design WP2c B5 (e), B6). DAY-1 STUB: P7 fills it in.

Only the shapes of the public names are real. ``_write`` is the one place a sink write can fail; ``_sink_write`` holds the single ``except Exception``
handler the broad-catch pin counts (a failed write gives ``mask_failed`` before any call and is never wrapped around a ledger call). A stub that
raises ``NotImplementedError`` is passed through untouched so a package coding against the stub fails loudly.
"""

from __future__ import annotations

from typing import Any

from .selfcheck_codes import SelfCheckFailed

FULL_TEXT_ALLOWED = True  # this demo only; a client build sets it to False


def _write(sink: Any, row: Any) -> bool:
    raise NotImplementedError


def _sink_write(sink: Any, row: Any) -> bool:
    try:
        return _write(sink, row)
    except NotImplementedError:  # stub only: remove with the real body
        raise
    except Exception:
        raise SelfCheckFailed("mask_failed") from None


class Run:
    """One per process: ``run_id``, the current ``segment`` and the log level."""

    def __init__(self, level: str) -> None:
        raise NotImplementedError

    def close(self) -> int:
        raise NotImplementedError


class Tracer:
    """One per item: ``mask_done``, ``row`` and ``close`` (that item's check (e))."""

    def __init__(self, run: Run, item_ref: str, key: bytes, sink: Any = None) -> None:
        raise NotImplementedError

    def mask_done(self, masked: Any, key: bytes) -> None:
        raise NotImplementedError

    def row(self, *args: Any, **kw: Any) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


def format_rows(rows: Any) -> list[str]:
    raise NotImplementedError


def masked_request(s: Any, item_id: int, tier: str) -> str:
    raise NotImplementedError
