"""A keyed hash for audit labels (stdlib only).

An audit row must not carry an outsider's raw text or a name, yet two different principals must stay two different labels and the same
principal must keep ONE label across processes and restarts. That needs a key that outlives the process: the deployment gives one
(``bytes``, read from its secrets kind) to ``StopGate(label_key=...)`` and ``CappedAudit(label_key=...)``. Without it the labels use a
random key of THIS process (a fallback that is logged once as a warning): distinct inside the process, unstable across processes, and
not reversible by hashing a dictionary.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import threading

_log = logging.getLogger(__name__)
_lock = threading.Lock()
_fallback: bytes | None = None


def fallback_key() -> bytes:
    """The random key of this process; the first use logs a warning that labels are not stable across processes."""
    global _fallback
    with _lock:
        if _fallback is None:
            _fallback = os.urandom(32)
            _log.warning(
                "audit labels use a per-process key (no label_key given): the same principal gets another label in another process"
            )
        return _fallback


def keyed_hex(value: str, digits: int, key: bytes | None = None) -> str:
    """The first ``digits`` hex digits of HMAC-SHA256(key, value); ``key`` is the deployment key, or the per-process fallback."""
    return hmac.new(
        key or fallback_key(), value.encode("utf-8", "replace"), hashlib.sha256
    ).hexdigest()[:digits]
