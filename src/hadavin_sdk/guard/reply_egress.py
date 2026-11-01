"""Outbound reply-text egress check: defence in depth (the real control is template-only drafts with typed slots).

Returns typed violations, never raises: non-text input is `TEXT_NOT_STRING`, text longer than `max_text` is `TEXT_TOO_LONG` (refused
unscanned). Every pattern repeat is bounded (RFC label and address lengths), so a scan is linear in the text: an unbounded `[\\w.+-]+@`
or `(?:[a-z0-9-]+\\.)+` retried from every start position takes seconds on 20,000 characters. Ideographic dots and the usual defanging
("[.]", "(dot)", " dot ", " . ", " .x") are folded back to "." before scanning. Not covered: look-alike letters from other scripts.
Distinct from `guard.egress.egress_check`, which checks one host or URL against an allow-list.
"""

from __future__ import annotations

import re

from hadavin_sdk.guard.identity_fold import fold

MAX_TEXT = 20_000
URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
DOMAIN = re.compile(r"(?i)\b(?:[a-z0-9-]{1,63}\.){1,10}[a-z]{2,24}(?:/[^\s<>\"']*)?")
EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}")
BANK = re.compile(r"(?i)\b[A-Z]{2}\d{2}(?:[ -]?[A-Z0-9]{2,4}){3,8}\b")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?:/[^\s<>\"']*)?")
_DOTS = str.maketrans({"\u3002": ".", "\uff0e": ".", "\uff61": ".", "\u2024": ".", "\u2027": "."})
_DEFANG = re.compile(
    r"\s*[\[({<]\s*(?:dot|\.)\s*[\])}>]\s*|(?<=\w)\s+dot\s+(?=[a-z])|(?<=\w) \. (?=[a-z]{2,})|(?<=\w) \.(?=[a-z]{2,})",
    re.IGNORECASE,
)


def reply_violations(
    text: object,
    recipient: object,
    verified_email: str | None,
    allowed_links: frozenset[str] = frozenset(),
    allowed_hosts: frozenset[str] = frozenset(),
    attachments: tuple[str, ...] = (),
    allowed_attachments: frozenset[str] = frozenset(),
    max_text: int = MAX_TEXT,
) -> list[str]:
    if not isinstance(text, str) or not isinstance(recipient, str):
        return ["TEXT_NOT_STRING"]
    if len(text) > max_text:
        return ["TEXT_TOO_LONG"]
    v: list[str] = []
    if not verified_email or fold(recipient) != fold(verified_email):
        v.append("RECIPIENT_NOT_VERIFIED_CUSTOMER")
    clean = _DEFANG.sub(".", fold(text).translate(_DOTS))
    for u in URL.findall(clean):
        if u.rstrip(".,;)") not in allowed_links:
            v.append("UNLISTED_LINK")
    no_urls = EMAIL.sub(" ", URL.sub(" ", clean))
    for ip in IPV4.findall(no_urls):
        if ip.split("/")[0] not in allowed_hosts and ip.rstrip(".,;)") not in allowed_links:
            v.append("UNLISTED_LINK")
    for d in DOMAIN.findall(no_urls):
        if (
            d.split("/")[0].casefold().rstrip(".") not in allowed_hosts
            and d.rstrip(".,;)") not in allowed_links
        ):
            v.append("UNLISTED_LINK")
    for e in EMAIL.findall(clean):
        if not verified_email or fold(e) != fold(verified_email):
            v.append("UNLISTED_ADDRESS")
    v += ["UNLISTED_ATTACHMENT" for a in attachments if a not in allowed_attachments]
    if BANK.search(clean):
        v.append("BANK_PATTERN")
    return sorted(set(v))
