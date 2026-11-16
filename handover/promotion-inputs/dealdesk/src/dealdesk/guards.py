"""Blast-radius controls (blast radius (2), (3), (5); R-DEALDESK-092): read-only role caps, read log, egress check.
RateCap     token bucket on an injectable clock (a boundary burst cannot double the rate; a backwards clock never refills) + a connection cap.
ReadLog     every read of client data: who, fields, why, rows, hashed ref; a field outside any stated purpose is refused.
egress_check  outbound replies/quotes: only the requester's directory address, listed links/hosts/attachments, no bank pattern; text normalised first."""

from __future__ import annotations

import hashlib
import re
import threading
from dataclasses import dataclass, field

from dealdesk.core_copy.textnorm import AllowVerdict, allow_equal
from dealdesk.purposes import CODE_PURPOSE, PURPOSE
from dealdesk.textnorm import views

URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
DOMAIN = re.compile(r"(?i)\b(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<>\"']*)?")
BANK = re.compile(r"(?i)\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


class RateCap:
    def __init__(self, max_per_s: int, max_connections: int) -> None:
        self.max_per_s, self.max_connections = max_per_s, max_connections
        self._tokens, self._last = float(max_per_s), None
        self.connections, self.throttled, self.accepted = 0, 0, 0
        self._lock = threading.Lock()

    def allow(self, now_s: float) -> bool:
        with self._lock:
            if self._last is not None and now_s > self._last:
                self._tokens = min(float(self.max_per_s), self._tokens + (now_s - self._last) * self.max_per_s)
            self._last = now_s if self._last is None else max(self._last, now_s)
            if self._tokens < 1.0:
                self.throttled += 1
                return False
            self._tokens -= 1.0
            self.accepted += 1
            return True

    def connect(self) -> bool:
        with self._lock:
            if self.connections >= self.max_connections:
                return False
            self.connections += 1
            return True

    def disconnect(self) -> None:
        with self._lock:
            self.connections = max(0, self.connections - 1)


@dataclass
class ReadLog:
    entries: list = field(default_factory=list)

    def read(self, identity: str, port: str, fields: list[str], ref: str, why: str, rows: int, now: str) -> None:
        unknown = [f for f in fields if f not in PURPOSE and f not in CODE_PURPOSE]
        if unknown:
            raise PermissionError(f"field outside any stated purpose: {unknown}")
        self.entries.append({"who": identity, "port": port, "fields": sorted(fields), "why": why, "rows": rows,
                             "ref_sha256": hashlib.sha256(ref.encode()).hexdigest()[:16], "at": now})  # fmt: skip

    def export_for_client(self) -> list:
        return [dict(e) for e in self.entries]


MAX_EGRESS_CHARS = 4096


def egress_check(text: object, recipient: object, requester_email: str | None, allowed_links: frozenset = frozenset(), attachments: tuple = (),
                 allowed_attachments: frozenset = frozenset(), allowed_hosts: frozenset = frozenset()) -> list[str]:  # fmt: skip
    """Violations of the outbound policy (empty = pass). FAIL CLOSED: a non-string or over-long text is itself a violation. The text is folded first
    (core text fold: format characters cannot split a link, look-alike Cyrillic/Greek letters become Latin), so a look-alike domain is still a domain."""
    if not isinstance(text, str):
        return ["TEXT_NOT_STRING"]
    if len(text) > MAX_EGRESS_CHARS:
        return ["TEXT_TOO_LONG"]
    v = []
    if not requester_email or not isinstance(recipient, str):
        v.append("RECIPIENT_NOT_REQUESTER")
    else:
        verdict = allow_equal(recipient, requester_email)  # core ALLOW decision: only an identical string allows
        if verdict is AllowVerdict.LOOKALIKE:
            v.append("RECIPIENT_LOOKALIKE")
        elif verdict is AllowVerdict.VARIANT:
            v.append("RECIPIENT_VARIANT")  # case, width or whitespace only: refused, reported as a variant not a spoof
        elif verdict is not AllowVerdict.EQUAL:
            v.append("RECIPIENT_NOT_REQUESTER")
    view = views(text)[0]
    for u in URL.findall(view):
        if u.rstrip(".,;)") not in allowed_links:
            v.append("UNLISTED_LINK")
    no_urls = EMAIL.sub(" ", URL.sub(" ", view))
    for d in DOMAIN.findall(no_urls):
        if d.split("/")[0].casefold().rstrip(".") not in allowed_hosts and d.rstrip(".,;)") not in allowed_links:
            v.append("UNLISTED_LINK")
    for e in EMAIL.findall(view):
        if not requester_email or e.casefold() != requester_email.casefold():
            v.append("UNLISTED_ADDRESS")
    if BANK.search(view.upper().replace(" ", "")) or BANK.search(view.upper()):
        v.append("BANK_PATTERN")
    v += ["UNLISTED_ATTACHMENT" for a in attachments if a not in allowed_attachments]
    return sorted(set(v))
