"""The inbound ledger, receiving side (AK-G2-a): keys, the sender-id check and `Inbox.receive`.

A message that should start work is written to the store as a saved message record (a receipt) BEFORE the sender is
answered (write-ahead). Same sender id and same text again: nothing new happens (duplicate). Same sender id and other
text: the first stays untouched and the new one becomes a refused row without its text (id reuse). Only keyed hashes of
the sender's id and text are stored in the receipt; the text itself lives in its own table.

Neutral: no vendor import. Time comes from the injected clock, never from the store. Demo stage only; see the AK-G2
pilot gate.
"""

from __future__ import annotations

import hashlib
import hmac
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from hadavin_sdk.defaults import INBOUND_MAX_REUSE_ROWS, INBOUND_MAX_SENDER_ID_CHARS
from hadavin_sdk.models import INBOUND_NAME, InboundReceipt, now
from hadavin_sdk.store.protocol import InboundStore

ReceiveOutcome = Literal["new", "duplicate", "id_reuse", "id_reuse_capped", "busy"]

_KEY_LABEL = b"hadavin-inbound-key-v1"
_CHECK_LABEL = b"hadavin-inbound-key-check-v1"


class InboundKeyChanged(RuntimeError):
    """The inbound key differs from the one the ledger was written with. The message names tenant, source and both
    fingerprints (never a key); inbound stops until a person acknowledges the change."""


def tenant_key(*parts: str) -> str:
    """One string for several names, length-prefixed so that no two different lists give the same string
    (`("a", "bc")` and `("ab", "c")` differ; five parts never equal three)."""
    return "".join(f"{len(p.encode('utf-8'))}:{p}" for p in parts)


def derive_key(restored_key: bytes | None) -> bytes | None:
    """The inbound key, derived from the existing restored-hash key (no new secret). None = demo without a key."""
    if restored_key is None:
        return None
    return hmac.new(restored_key, _KEY_LABEL, hashlib.sha256).digest()


def _h(key: bytes | None, data: bytes) -> str:
    """Keyed hash (HMAC-SHA256) with a key, plain SHA-256 without one (demo: guessable, stated)."""
    if key:
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    return hashlib.sha256(data).hexdigest()


def body_hash(key: bytes | None, body: bytes) -> str:
    return _h(key, body)


def delivery_key(key: bytes | None, tenant: str, source: str, sender_id: str) -> str:
    return _h(key, tenant_key(tenant, source, sender_id).encode("utf-8"))


def reuse_key(key: bytes | None, tenant: str, source: str, sender_id: str, body_sha256: str) -> str:
    return _h(key, tenant_key(tenant, source, sender_id, "reuse", body_sha256).encode("utf-8"))


def run_id_for(delivery_key: str, generation: int) -> str:
    """The run id of one message and generation: `run-` + 28 hex characters of the delivery key + 4 of the generation."""
    if not 0 <= generation <= 65535:
        raise ValueError("generation must be 0..65535")
    return "run-" + delivery_key[:28] + format(generation, "04x")


def item_id_for(delivery_key: str) -> str:
    return "inb-" + delivery_key[:32]


def key_check_for(key: bytes | None) -> str:
    """A 16-hex fingerprint of the inbound key: reveals nothing about it, safe in a log line, shows only WHETHER it changed."""
    return _h(key, _CHECK_LABEL)[:16]


def check_sender_id(x: object) -> str:
    """The sender's message id: a real `str` (no subclass), 1 to 256 characters, no control, format, surrogate,
    private-use or unassigned character (Unicode category starting with C). The message names no value."""
    if type(x) is not str:
        raise ValueError("sender id: must be a string")
    if not 1 <= len(x) <= INBOUND_MAX_SENDER_ID_CHARS:
        raise ValueError("sender id: wrong length")
    if any(unicodedata.category(c).startswith("C") for c in x):
        raise ValueError("sender id: holds a control or invisible character")
    return x


@dataclass(frozen=True)
class InboundSource:
    """One inbound address, bound to exactly one tenant, one readers list, one agent and one principal."""

    name: str  # the ledger name
    tenant: str
    readers: frozenset[str]
    agent_id: str
    principal_id: str
    max_open: int = 1000
    stuck_s: float = 60

    def __post_init__(self) -> None:
        if not INBOUND_NAME.fullmatch(self.name) or not INBOUND_NAME.fullmatch(self.tenant):
            raise ValueError("inbound source: bad name or tenant")
        if not self.readers:
            raise ValueError("inbound source: readers must not be empty")
        if self.max_open < 1 or self.stuck_s < 1:
            raise ValueError("inbound source: max_open and stuck_s must be at least 1")


class Inbox:
    """Receives messages into the ledger. `hkey` is the inbound key (None only in demo)."""

    def __init__(
        self,
        store: InboundStore,
        *,
        hkey: bytes | None = None,
        clock: Callable[[], datetime] = now,
    ) -> None:
        self.store = store
        self.hkey = hkey
        self.clock = clock
        self.key_check = key_check_for(hkey)

    def receive(self, source: InboundSource, sender_id: str, body: bytes) -> ReceiveOutcome:
        check_sender_id(sender_id)  # the choke point: before any store call
        if not isinstance(body, bytes | bytearray):
            raise ValueError("body must be bytes")
        body = bytes(body)
        t = self.clock()
        dkey = delivery_key(self.hkey, source.tenant, source.name, sender_id)
        sha = body_hash(self.hkey, body)
        rec = InboundReceipt(
            tenant=source.tenant,
            source=source.name,
            readers=source.readers,
            delivery_key=dkey,
            body_sha256=sha,
            key_check=self.key_check,
            generation=0,
            run_id=run_id_for(dkey, 0),
            received_at=t,
            updated_at=t,
        )
        result = self.store.receive_inbound(
            rec, body, max_reuse=INBOUND_MAX_REUSE_ROWS, max_open=source.max_open
        )  # re-read of the key check on EVERY receive: no cache
        if result == "key_changed":
            raise InboundKeyChanged(
                f"inbound key changed for {source.tenant}/{source.name}: this program's check is {self.key_check}"
            )
        if result in ("new", "duplicate", "busy"):
            return result
        # "conflict": same sender id, other text. Write a refused row (no text) keyed by the reuse key.
        reuse = InboundReceipt(
            tenant=source.tenant,
            source=source.name,
            readers=source.readers,
            delivery_key=reuse_key(self.hkey, source.tenant, source.name, sender_id, sha),
            body_sha256=sha,
            key_check=self.key_check,
            run_id=None,
            state="refused",
            reason="id_reuse",
            reuse_of=dkey,
            received_at=t,
            updated_at=t,
        )
        again = self.store.receive_inbound(
            reuse, None, max_reuse=INBOUND_MAX_REUSE_ROWS, max_open=source.max_open
        )
        if again == "key_changed":
            raise InboundKeyChanged(
                f"inbound key changed for {source.tenant}/{source.name}: this program's check is {self.key_check}"
            )
        return "id_reuse_capped" if again == "conflict_capped" else "id_reuse"
