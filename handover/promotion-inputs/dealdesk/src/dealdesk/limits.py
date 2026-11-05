"""Input size limits and per-message deadline: documented defaults in ONE place (inbound ledger and load profile: one message must not freeze the process).
Applied at Inbox.receive (before the ack), again in the handler, and at every decision field. Linear-time scanners (gate_rules) keep the cost of a
message at the cap bounded; the deadline bounds an unexpectedly slow dependency."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    max_message_bytes: int = 65_536  # whole JSON message incl. attachments
    max_text_chars: int = 10_000  # requester text
    max_attachments: int = 10
    max_attachment_chars: int = 10_000  # per attachment, screened only
    max_clauses: int = 20
    max_id_chars: int = 128  # message ids, approval ids, person ids, key ids, hashes
    handler_deadline_s: float = 10.0  # per message; on expiry the row is dead-lettered with reason `deadline`

    def __post_init__(self) -> None:
        for f in (
            "max_message_bytes",
            "max_text_chars",
            "max_attachments",
            "max_attachment_chars",
            "max_clauses",
            "max_id_chars",
        ):
            v = getattr(self, f)
            if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                raise ValueError(f"{f} must be a positive int")
        if not isinstance(self.handler_deadline_s, int | float) or self.handler_deadline_s <= 0:
            raise ValueError("handler_deadline_s must be positive")


DEFAULT_LIMITS = Limits()
