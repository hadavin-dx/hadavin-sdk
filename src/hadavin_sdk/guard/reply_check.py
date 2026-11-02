"""Outbound reply-text check: defence in depth for text that goes to ONE verified recipient (the real control is a template
with typed slots, so no free text reaches a person). Returns typed violations; never raises.

Not to be confused with `guard.egress.egress_check` (one host or URL against an allow-list) or the digit-budget output check in
`guard.egress_text`: this one answers "may this reply name a link, host, address, attachment or bank number the recipient
was not given?".

How text is read: `guard.textnorm.fold` (hidden characters dropped, look-alike letters from other scripts mapped to Latin,
casefold, collapse whitespace), then the usual defanging ("[.]", "(dot)", " dot ", " . ", " .x") is undone. Allow-lists are
folded the SAME way before comparing (an allowed link with capitals or accents matches). Addresses are compared EXACTLY
(`guard.identity_text.exact_key`), never through the over-matching fold, so a reply to `jose@x` is not accepted as `jos\u00e9@x`.
A host-like token that still holds a non-ASCII letter in the ORIGINAL text is `NON_ASCII_HOST` whatever it folds to (a
Cyrillic `\u0435` in `\u0435xample.com` would otherwise fold to an allowed host); punycode (`xn--`) hosts are matched as ASCII.
`allowed_patterns` (regex strings, at most 256 characters each, linear patterns only) remove caller-known shapes such as
`invoice-\\d+\\.pdf` or ticket ids before the domain, bank and IPv4 scans. Every repeat in the built-in patterns is bounded
(RFC 1035 label and address lengths), and the text is length-capped first, so a scan is linear.
Not covered: look-alikes outside the `guard.textnorm` table. A dot, one space and a lowercase word ("evil. example") is read as a host (`join_spaced_dots`); a capitalised word after a dot is a new sentence.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from hadavin_sdk.guard.identity_text import exact_key, lookalike_of, same_recipient
from hadavin_sdk.guard.textnorm import FILLERS, fold

# RFC 1035 label length 63, at most 10 labels, TLD 2-24 letters or an A-label (punycode); RFC 5321 local part 64.
DOMAIN = re.compile(
    r"(?i)\b(?:[a-z0-9-]{1,63}\.){1,10}(?:xn--[a-z0-9-]{1,59}|[a-z]{2,24})(?:/[^\s<>\"']*)?"
)
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}")
URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?:/[^\s<>\"']*)?")
IBAN = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[ \-]?[A-Za-z0-9]{4}){3,}"
)  # the one bank-number shape
UNICODE_HOST = re.compile(r"[\w-]{1,63}(?:\.[\w-]{1,63}){1,10}")
_DOTS = str.maketrans({"\u3002": ".", "\uff0e": ".", "\uff61": ".", "\u2024": ".", "\u2027": "."})
_DEFANG = re.compile(
    r"\s*[\[({<]\s*(?:dot|\.)\s*[\])}>]\s*|(?<=\w)\s+dot\s+(?=[a-z])|(?<=\w) \. (?=[a-z]{2,})|(?<=\w) \.(?=[a-z]{2,})",
    re.IGNORECASE,
)
_SPACED_DOT = re.compile(r"(?<=[a-z0-9])\. (?=[a-z]{2,})")  # dot, one space, a LOWERCASE word
_HIDDEN = frozenset({"Cc", "Cf", "Zl", "Zp", "Co", "Cs", "Cn"})


class Violation(StrEnum):
    TEXT_NOT_STRING = "TEXT_NOT_STRING"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    RECIPIENT_NOT_VERIFIED = "RECIPIENT_NOT_VERIFIED"
    RECIPIENT_LOOKALIKE = "RECIPIENT_LOOKALIKE"
    UNLISTED_LINK = "UNLISTED_LINK"
    UNLISTED_ADDRESS = "UNLISTED_ADDRESS"
    UNLISTED_ATTACHMENT = "UNLISTED_ATTACHMENT"
    NON_ASCII_HOST = "NON_ASCII_HOST"
    BANK_PATTERN = "BANK_PATTERN"


@dataclass(frozen=True)
class ReplyPolicy:
    max_text: int = 20_000
    allowed_links: frozenset[str] = frozenset()
    allowed_hosts: frozenset[str] = frozenset()
    allowed_attachments: frozenset[str] = frozenset()
    allowed_patterns: tuple[str, ...] = ()
    join_spaced_dots: bool = (
        True  # 'evil. example' reads as 'evil.example'; prose capitalises a new sentence
    )

    def __post_init__(self) -> None:
        if not (
            isinstance(self.max_text, int)
            and not isinstance(self.max_text, bool)
            and self.max_text > 0
        ):
            raise ValueError("max_text must be a positive int")
        for p in self.allowed_patterns:
            if not isinstance(p, str) or not 0 < len(p) <= 256:
                raise ValueError("an allowed pattern is a regex string of 1-256 characters")
            try:
                re.compile(p)
            except re.error as exc:
                raise ValueError(f"allowed pattern does not compile: {exc}") from None

    def folded(self, items: frozenset[str]) -> dict[str, frozenset[str]]:
        """folded form -> the literal (safe) spellings of the listed entries that fold to it. A candidate found in the folded text is allowed only if one of
        its listed spellings is also in the text as written."""
        out: dict[str, set[str]] = {}
        for i in items:
            out.setdefault(_view(i).rstrip("."), set()).add(_safe_view(i).rstrip("."))
        return {k: frozenset(v) for k, v in out.items()}


def _view(text: str) -> str:
    return _DEFANG.sub(".", fold(text, casefold=True, collapse_ws=True).translate(_DOTS))


def _safe_view(text: str) -> str:
    """The text as written (NFKC, case, whitespace; NO look-alike mapping and NO hidden-character removal), defanged. An ALLOW-listed link or host counts
    only if it appears in THIS view too: the folded view equates look-alikes and hidden-character variants with the real thing, which is right for DENY
    scanning and wrong for ALLOW."""
    t = " ".join(unicodedata.normalize("NFKC", text).casefold().split()).translate(_DOTS)
    return _DEFANG.sub(".", t)


def _visible(text: str) -> str:
    """The text as typed, minus invisible characters (NOT the over-matching fold): NFC + casefold, for exact address compares."""
    kept = "".join(
        " " if c in "\n\r\t" else c
        for c in text
        if c in "\n\r\t" or (unicodedata.category(c) not in _HIDDEN and c not in FILLERS)
    )
    return unicodedata.normalize("NFC", kept).casefold()


def reply_violations(
    text: object,
    recipient: object,
    verified_recipient: object,
    *,
    policy: ReplyPolicy | None = None,
    attachments: tuple[str, ...] = (),
) -> list[str]:
    p = policy or ReplyPolicy()
    if not isinstance(text, str) or not isinstance(recipient, str):
        return [Violation.TEXT_NOT_STRING]
    if len(text) > p.max_text:
        return [Violation.TEXT_TOO_LONG]
    v: set[str] = set()
    want = exact_key(verified_recipient)
    if want is None or not same_recipient(recipient, verified_recipient):
        v.add(Violation.RECIPIENT_NOT_VERIFIED)
        if lookalike_of(recipient, verified_recipient):
            v.add(Violation.RECIPIENT_LOOKALIKE)
    links, hosts = p.folded(p.allowed_links), p.folded(p.allowed_hosts)
    joined = _SPACED_DOT.sub(".", text) if p.join_spaced_dots else text
    clean, safe = _view(joined), _safe_view(joined)

    def allowed(candidate: str, listing: dict[str, frozenset[str]]) -> bool:
        # ALLOW needs the literal spelling of a listed entry in the text as written, not only the folded form
        return any(s in safe for s in listing.get(candidate, ()))

    for u in URL.findall(clean):
        if not allowed(u.rstrip(".,;)"), links):
            v.add(Violation.UNLISTED_LINK)
    no_urls = EMAIL.sub(" ", URL.sub(" ", clean))
    for pat in p.allowed_patterns:
        no_urls = re.sub(pat, " ", no_urls, flags=re.IGNORECASE)
    for ip in IPV4.findall(no_urls):
        if not (allowed(ip.split("/")[0], hosts) or allowed(ip.rstrip(".,;)"), links)):
            v.add(Violation.UNLISTED_LINK)
    for d in DOMAIN.findall(no_urls):
        host = d.split("/")[0].rstrip(".")
        if not (allowed(host, hosts) or allowed(d.rstrip(".,;)"), links)):
            v.add(Violation.UNLISTED_LINK)
    seen = _visible(text)
    for e in EMAIL.findall(seen):
        if exact_key(e) != want:
            v.add(Violation.UNLISTED_ADDRESS)
    for h in UNICODE_HOST.findall(seen):
        if any(not c.isascii() and c.isalpha() for c in h):
            v.add(Violation.NON_ASCII_HOST)
    if any(a not in p.allowed_attachments for a in attachments):
        v.add(Violation.UNLISTED_ATTACHMENT)
    bank_view = clean
    for pat in p.allowed_patterns:
        bank_view = re.sub(pat, " ", bank_view, flags=re.IGNORECASE)
    if IBAN.search(bank_view):
        v.add(Violation.BANK_PATTERN)
    return sorted(v)
