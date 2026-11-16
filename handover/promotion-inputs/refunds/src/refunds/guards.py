"""Blast-radius controls (purpose-and-blast-radius rule (2), (3), (5)); pure and injectable-clock so they are testable against the fakes in stage 1.

RateCap     read-only role: per-agent request-rate (token bucket) and connection caps, so the AI cannot slow or lock production.
ReadLog     every read of client data is logged (who, what fields, why, row count); ids are hashed, no PII values; exportable for the client.
egress_check  outbound customer replies, DEFENCE IN DEPTH only (the real control is that customer drafts are harness templates with typed slots):
            only the verified customer's address, no unlisted link/host/domain, no attachment, no bank/IBAN pattern. Ideographic dots and the usual
            defanging ("[.]", "(dot)", " dot ", " . ") are folded back to "."; a spaced IBAN and a bare IPv4 address are caught. A scheme-bearing reference with no dotted host (`ftp://intranet/x`, a protocol-relative `//host`, a UNC `\\\\host\\share`, the special-scheme forms `http:\\\\h\\x`, `http:/h`, `http:h`) or ANY `scheme:` glued to a letter or symbol (`ms-excel:x`, `skype:x`, `tg:x`, `cid:x`; not `Time 10:30`, `Ref:12` or `Note: x`; `allowed_schemes` defaults to mailto) is an unlisted link unless listed; a curated list (data, javascript, tel, sms ...) also catches the forms with a digit after the colon. A protocol-relative `//host` is caught even in markdown or HTML (`(//intranet/x)`, `href=//intranet`). US routing/account numbers and a UK sort code are caught only next to their keyword or as `NN-NN-NN`; a bare digit string is not. Unicode (IDN) and punycode hosts are checked after IDNA folding and on a view that KEEPS accents and the exact letters, so a look-alike or accented host (`shop.ex\u00e1mple`, Cyrillic or Greek letters) is never an allow-listed `shop.example`; fullwidth letters fold to ASCII as a browser does; the allow-lists are compared case-folded. NOT covered: look-alike
            letters in prose words (a look-alike HOST is a Unicode host and is caught unless listed), spelled-out hosts in other languages, and a dot followed directly by a space ("evil. example",
            indistinguishable from the end of a sentence, so only a dot, one space and a LOWERCASE word is read as a host). ("Thanks. Regards" is prose.) A space BEFORE the dot ("evil .example") IS folded and caught. Input that is not text, or
            longer than config.EGRESS_MAX_TEXT, is refused unscanned (TEXT_NOT_STRING, TEXT_TOO_LONG); every pattern is bounded, so a scan is linear.
LIBRARY ONLY IN STAGE 1: nothing in desk.py or writegate.py calls egress_check, RateCap or ReadLog (stage 1 sends no outbound reply and makes no live read),
            so these blast-radius controls are tested functions, not enforced on a running path. Wiring them is a stage-2 exit item.
The governed write path moved to writegate.py (it needs the store, the verifier and the identity table).
No function here changes a schema, a permission or a credential: none exists, and identities.py grants no agent identity such an action.
"""

from __future__ import annotations

import hashlib
import math
import re
import threading
from dataclasses import dataclass, field
from urllib.parse import unquote

from refunds.config import EGRESS_MAX_TEXT
from refunds.identity import same_verified_address
from refunds.purposes import PURPOSE
from refunds.textnorm import normalise, normalise_keep_case, normalise_keep_marks

URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
# every repeat below is BOUNDED (RFC label/address lengths), so no scan is quadratic in the text: an unbounded label repeat or `[\w.+-]+@` retried
# from every start position took seconds on 20,000 characters of "a-" (tests/test_review8.py times it)
_M = "\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f"  # combining marks: part of a label, so an accent can never split a host
DOMAIN = re.compile(
    rf"(?<![\w{_M}-])(?:[\w{_M}-]{{1,63}}\.){{1,10}}(?:xn--[a-z0-9-]{{2,59}}|[^\W\d_][\w{_M}-]{{1,62}})(?![\w{_M}-])(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)  # Unicode (IDN) labels, a last label that STARTS with a letter and takes every word character after it (so 'shop.example1' and 'shop.example_evil' are whole hosts, never 'shop.example'), punycode TLDs; NO host may continue to the right ("shop.example_evil.com" is one host, not "shop.example")
# an IBAN, contiguous or spaced: "GB29 NWBK 6016 1331 9268 19"
BANK = re.compile(r"(?i)\b[A-Z]{2}\d{2}(?:[ -]?[A-Z0-9]{2,4}){3,8}\b")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?:/[^\s<>\"']*)?")
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}")
KEY = re.compile(r"[0-9a-f]{64}")
# a scheme-bearing reference with no dot in it: "ftp://intranet/x", "data:text/html,...", "javascript:...", a protocol-relative "//intranet/x".
# (mailto: is left to EMAIL: the address inside is checked against the verified one.) Bounded repeats, no nested quantifier.
_DANGEROUS_SCHEMES = (
    "data", "javascript", "vbscript", "file", "tel", "sms", "blob", "about", "ms-msdt", "search-ms", "sip", "sips", "intent",
    "view-source", "ldap", "jar", "resource", "chrome", "smb", "ssh", "magnet", "mms", "itms", "gopher",
)  # fmt: skip
_DANGEROUS = r"|".join(r"\s?".join(w) for w in _DANGEROUS_SCHEMES)  # one space or TAB/LF/CR may split a scheme word
# WHATWG URL parsing strips TAB, LF and CR anywhere inside a URL and leading/trailing C0 controls and spaces, so "ja<TAB>vascript:" and "ftp ://x"
# must not slip past; "java script:" is not a browser scheme but is refused anyway (over-matching is the safe side for a DENY).
# The special schemes (http, https, ftp, ws, wss) also accept a BACKSLASH, one slash or no slash after the colon: "http:\\intranet\x", "http:/intranet",
# "http:intranet". A UNC path "\\host\share" is a reference too. Any other scheme is caught only with "//" or from the curated list above.
SCHEME = re.compile(
    r"(?i)(?<![a-z0-9])[a-z][a-z0-9+.-]{1,20}\s?://[^\s<>\"']+"
    r"|(?<![a-z0-9])(?:https?|ftps?|wss?)\s?:[\\/]*[^\s<>\"'\\/:][^\s<>\"']*"
    r"|(?<![a-z0-9])(?:" + _DANGEROUS + r")\s?:[^\s<>\"']+"
    r"|(?<![\w:/.-])//[^\s<>\"']+"
    r"|(?<![\w\\])\\\\[^\s<>\"']+"
)
# ANY other `scheme:` glued to a letter or symbol ("ms-excel:x", "msteams:x", "skype:x", "tg:x", "cid:x", "vscode:x") is a reference too; a digit after the colon
# ("Time 10:30", "Ref:12") is not, a space after the colon is prose. Schemes in `allowed_schemes` (default: mailto, whose address is checked as an address) pass.
ANY_SCHEME = re.compile(r"(?i)(?<![a-z0-9])([a-z][a-z0-9+.-]{1,30})\s?:(?![\s\d])[^\s<>\"']+")
BANK_DETAILS = re.compile(
    r"(?i)\b(?:routing|aba|account(?: number| no\.?)?|acct|sort[ -]?code|swift|bic)\b[^\n]{0,30}?\d[\d -]{5,}|\b\d{2}-\d{2}-\d{2}\b"
)  # US routing / account numbers and a UK sort code, only next to their keyword (a bare digit string is an order number as often as a bank detail)


def _percent_decode(s: str) -> tuple[str, bool]:
    """Decode percent-escapes to a fixpoint (at most 4 rounds): `evil%2eexample`, `%252e` (double) and mixed-case `%2E` all become the dot a browser
    sees. Returns (decoded, stable); not stable = still changing after 4 rounds (nested encoding on purpose)."""
    for _ in range(4):
        d = unquote(s)
        if d == s:
            return s, True
        s = d
    return s, unquote(s) == s


_BAD_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")
_HOSTISH = re.compile(r"[^\W\d_]\.[^\W\d_]")


def _undecodable_host_token(text: str) -> bool:
    """A whitespace-delimited token that looks like a host (letter dot letter) and holds a `%` that is not an escape: it cannot be decoded, so it is refused.
    Token by token with two linear searches (a single regex with two open-ended runs would be quadratic on a long run without spaces)."""
    return any("%" in t and _BAD_ESCAPE.search(t) is not None and _HOSTISH.search(t) is not None for t in text.split())


def _hostkey(h: str) -> str:
    """Comparison form of a host or link: case-folded, no trailing dot, IDNA (punycode) for Unicode hosts, so 'bücher.example' and its xn-- form are one host."""
    h = h.strip().casefold().rstrip(".")
    try:
        return h.encode("idna").decode("ascii")
    except UnicodeError:
        return h


class RateCap:
    """Token bucket on an injectable clock in SECONDS: capacity = max_per_s, refill = max_per_s per second. A boundary burst cannot double the rate and a
    backwards clock never refills. A NaN, infinite or non-numeric timestamp, a reading above MAX_ABS_S (a clock in milliseconds), and a step of more than MAX_JUMP_S in
    either direction (a far-future or far-past reading) is refused (counted as throttled and in `rejected_clock`) and never stored, so one bad reading cannot freeze the bucket; after a REAL
    idle longer than MAX_JUMP_S the operator calls `reset_clock(now_s)`. A clock in the wrong unit whose readings stay below MAX_ABS_S cannot be
    detected and makes the cap that many times too loose or too strict: the unit is part of the contract. Connections are capped separately with an
    ownership token: `acquire` returns a token (or None at the cap) and `release(token)` frees that slot once; a second release of the same token, or
    of a foreign one, changes nothing. (The unowned connect/disconnect counters were removed: a double disconnect under-counted and let a caller exceed
    the cap.)"""

    MAX_JUMP_S = 86_400.0  # largest accepted step between two readings, in either direction
    MAX_ABS_S = 1e11  # largest accepted reading (about 3,000 years of seconds): a clock in milliseconds or microseconds is refused at once

    def __init__(self, max_per_s: int, max_connections: int) -> None:
        for name, v, lo in (("max_per_s", max_per_s, 1), ("max_connections", max_connections, 0)):
            if not isinstance(v, int) or isinstance(v, bool) or v < lo:
                raise ValueError(f"{name} must be an integer >= {lo}")
        self.max_per_s, self.max_connections = max_per_s, max_connections
        self._tokens, self._last = float(max_per_s), None
        self.connections, self.throttled, self.accepted, self.rejected_clock = 0, 0, 0, 0
        self._live: set[object] = set()
        self._lock = threading.Lock()  # check-then-decrement must be atomic: two threads must not spend one token twice

    def allow(self, now_s: float) -> bool:
        with self._lock:
            if isinstance(now_s, bool) or not isinstance(now_s, (int, float)) or not math.isfinite(now_s):
                self.throttled += 1
                self.rejected_clock += 1
                return False
            if abs(now_s) > self.MAX_ABS_S or (self._last is not None and abs(now_s - self._last) > self.MAX_JUMP_S):
                self.throttled += 1
                self.rejected_clock += 1
                return False
            if self._last is not None and now_s > self._last:
                self._tokens = min(float(self.max_per_s), self._tokens + (now_s - self._last) * self.max_per_s)
            self._last = now_s if self._last is None else max(self._last, now_s)
            if self._tokens < 1.0:
                self.throttled += 1
                return False
            self._tokens -= 1.0
            self.accepted += 1
            return True

    def reset_clock(self, now_s: float) -> None:
        """Operator action after a real idle longer than MAX_JUMP_S (or after fixing a clock): adopt `now_s` as the last reading, keep the tokens."""
        if isinstance(now_s, bool) or not isinstance(now_s, (int, float)) or not math.isfinite(now_s):
            raise ValueError("now_s must be a finite number of seconds")
        with self._lock:
            self._last = float(now_s)

    def acquire(self) -> object | None:
        """A connection slot with an ownership token, or None when the cap is reached."""
        with self._lock:
            if self.connections >= self.max_connections:
                return None
            tok = object()
            self._live.add(tok)
            self.connections += 1
            return tok

    def release(self, token: object) -> bool:
        """Free the slot of `token` once; False (and no change) for an unknown or already released token."""
        with self._lock:
            if token not in self._live:
                return False
            self._live.discard(token)
            self.connections -= 1
            return True


@dataclass
class ReadLog:
    entries: list = field(default_factory=list)

    def read(self, identity: str, port: str, fields: list[str], ref: str, why: str, rows: int, now: str) -> None:
        unknown = [f for f in fields if f not in PURPOSE]
        if unknown:
            raise PermissionError(f"field outside any stated purpose: {unknown}")
        self.entries.append(
            {
                "who": identity,
                "port": port,
                "fields": sorted(fields),
                "why": why,
                "rows": rows,
                "ref_sha256": hashlib.sha256(ref.encode()).hexdigest()[:16],
                "at": now,
            }
        )

    def export_for_client(self) -> list:
        return [dict(e) for e in self.entries]


_DOTS = str.maketrans({"。": ".", "．": ".", "｡": ".", "․": ".", "‧": "."})
_DEFANG = re.compile(
    r"\s*[\[({<]\s*(?:dot|\.)\s*[\])}>]\s*|(?<=\w)\s+dot\s+(?=[a-z])|(?<=\w) \. (?=[a-z]{2,})|(?<=\w) \.(?=[a-z]{2,})",
    re.IGNORECASE,
)


_SPACED_DOT = re.compile(
    r"(?<=[a-z0-9])\.\s+(?=[a-z]{2,})"
)  # a dot, whitespace, a LOWERCASE word: prose capitalises a new sentence


def _defang(text: str) -> str:
    return _DEFANG.sub(".", text.translate(_DOTS))


def egress_check(
    text: str,
    recipient: str,
    verified_email: str | None,
    allowed_links: frozenset = frozenset(),
    attachments: tuple = (),
    allowed_attachments: frozenset = frozenset(),
    allowed_hosts: frozenset = frozenset(),
    allowed_schemes: frozenset = frozenset({"mailto"}),
) -> list[str]:
    """Violations of the outbound-reply egress policy (empty list = pass). Only the verified customer's own address may receive a reply. The text is
    normalised first (zero-width characters cannot split a link) and bare domains ('evil.example/pay') are caught, not only URLs with a scheme."""
    if not isinstance(text, str) or not isinstance(recipient, str):
        return ["TEXT_NOT_STRING"]  # typed and fail-closed, never a TypeError
    if len(text) > EGRESS_MAX_TEXT:
        return ["TEXT_TOO_LONG"]
    v = []
    if not verified_email or not same_verified_address(recipient, verified_email):
        v.append("RECIPIENT_NOT_VERIFIED_CUSTOMER")
    # normalise FIRST (tabs, newlines, NBSP, zero-width characters and runs of spaces collapse to one space), keeping case, then join
    clean = _defang(normalise(_SPACED_DOT.sub(".", normalise_keep_case(text))))
    # the ALLOW decision on a host or link is made on BOTH views: `clean` (accents dropped, so a trick cannot hide a host) and `raw` (accents and exact
    # letters kept, so `shop.ex\u00e1mple` is never `shop.example`); a host that is not listed in EITHER view is a violation
    raw = _defang(_SPACED_DOT.sub(".", normalise_keep_marks(text)))
    links = {
        x.casefold() for x in allowed_links
    }  # the allow-lists are compared case-folded (a configured link with capitals still matches)
    hosts = {_hostkey(x) for x in allowed_hosts}
    emails = EMAIL.findall(clean)
    views = []
    for base in (clean, raw):
        dec, stable = _percent_decode(base)
        if not stable or _undecodable_host_token(dec):
            v.append("UNLISTED_LINK")  # nested or undecodable percent-encoding in a host-looking token
        views += [base] if dec == base else [base, dec]
    for view in views:
        for u in URL.findall(view):
            if u.rstrip(".,;)").casefold() not in links:
                v.append("UNLISTED_LINK")
        for u in SCHEME.findall(URL.sub(" ", view)):
            if u.rstrip(".,;)").casefold() not in links:
                v.append("UNLISTED_LINK")
        for m in ANY_SCHEME.finditer(URL.sub(" ", view)):
            if m.group(1).casefold() not in allowed_schemes and m.group(0).rstrip(".,;)").casefold() not in links:
                v.append("UNLISTED_LINK")
        no_urls = EMAIL.sub(" ", SCHEME.sub(" ", URL.sub(" ", view)))
        for ip in IPV4.findall(no_urls):
            if ip.split("/")[0] not in hosts and ip.rstrip(".,;)").casefold() not in links:
                v.append("UNLISTED_LINK")
        for d in DOMAIN.findall(no_urls):
            if _hostkey(d.split("/")[0]) not in hosts and d.rstrip(".,;)").casefold() not in links:
                v.append("UNLISTED_LINK")
    for e in emails:
        if verified_email is None or not same_verified_address(e, verified_email):
            v.append("UNLISTED_ADDRESS")
    for a in attachments:
        if a not in allowed_attachments:
            v.append("UNLISTED_ATTACHMENT")
    if BANK.search(clean) or BANK_DETAILS.search(clean):
        v.append("BANK_PATTERN")
    return sorted(set(v))


def region_ok(region: str, agreed_regions: frozenset) -> bool:
    """purpose-and-blast-radius rule (4): data leaves the agreed region only if the region is listed in the client's config."""
    return region in agreed_regions
