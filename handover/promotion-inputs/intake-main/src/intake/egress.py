"""Egress check on everything that leaves the system (purpose-limit (3)). ALLOWLIST ONLY: the text is normalised first (the look-alike fold of core PR #50 via `textfold`, NFKC, fullwidth and ideographic dots, defanged dots such as [.] (.) and the word
dot, zero-width and soft hyphens removed), then ANYTHING that looks like an address, a scheme, a data: URI, a protocol-relative link, an IP or a dotted host is refused unless it is exactly on
the allowlist (empty today). The recipient must be the verified sender; no other address; no non-ASCII local part or host; no attachment unless allowlisted. A clean result goes to a clerk, who
sends it; the real defence is that a reply is built from templates (`clip_param`), so this check is a second layer."""

from __future__ import annotations

import re

from .textfold import fold_text

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_SCHEME = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://\S+|\bdata:\S+|\bmailto:\S+|(?<!\S)//\S+")
_HOST = re.compile(r"(?i)\b(?:[a-z0-9-]+\.)+[a-z][a-z0-9-]+(?:/\S*)?")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\S*)?")


def _normalise(body: str) -> str:
    t = fold_text(body)  # look-alike letters (Cyrillic, Greek ...) become Latin, invisible and format characters are dropped, NFKC
    t = t.replace(chr(0x3002), ".").replace(chr(0xFF0E), ".").replace(chr(0xFF61), ".")
    t = re.sub(r"[\[(\{]\s*(?:\.|dot)\s*[\])\}]", ".", t, flags=re.I)
    return re.sub(r"(?i)\s+dot\s+", ".", t)


def check_egress(
    *,
    recipient: str | None,
    verified_sender: str | None,
    body: str,
    attachments=(),
    reply_to: str | None = None,
    allowed_hosts=(),
    allowed_attachments=(),
) -> list[str]:
    out: list[str] = []
    if not isinstance(body, str):
        return ["body is not text"]
    if recipient is not None and (verified_sender is None or not recipient.isascii() or recipient.lower() != verified_sender.lower()):
        out.append("recipient is not the verified sender")
    if recipient is not None and reply_to and reply_to.lower() == recipient.lower() and reply_to.lower() != (verified_sender or "").lower():
        out.append("Reply-To used as a recipient")
    text = _normalise(body)
    allowed = {h.lower() for h in allowed_hosts}
    seen: set[str] = set()
    for addr in EMAIL.findall(text):
        seen.add(addr.lower())
        if addr.lower() != (verified_sender or "").lower():
            out.append(f"unlisted address in the body: {addr}")
    # A token may pass only when it IS an allowed host, a seen address, or exactly the local part or the domain of a seen address (the host regex
    # also matches the pieces of an address). Substring matching let a link that merely CONTAINED the verified address through.
    seen_parts = set(seen)
    for a in seen:
        seen_parts.update(a.partition("@")[::2])
    for pat in (_SCHEME, _IP, _HOST):
        for m in pat.finditer(text):
            tok = m.group(0).rstrip(".,;:)")
            low = tok.lower()
            if low in allowed or low in seen_parts:
                continue
            if re.fullmatch(r"\d+(?:\.\d+)+", tok) and not _IP.fullmatch(tok):
                continue  # a decimal number such as 2.75 or 10.5.1
            out.append(f"unlisted link or host in the body: {tok}")
    if any(ord(c) > 127 for c in body) and re.search(r"[^\x00-\x7f]+@|@[^\s]*[^\x00-\x7f]", body):
        out.append("non-ASCII address in the body")
    for att in attachments:
        if att not in allowed_attachments:
            out.append(f"unlisted attachment: {att}")
    return out
