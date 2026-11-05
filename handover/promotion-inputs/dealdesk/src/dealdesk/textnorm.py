"""Text normalisation for scans (injection screen, quote-text names, egress), built on the core text fold (`core_copy/textnorm.py`, core PR #50, see
CORE_COPIES.md): NFKD/NFKC, invisible and combining characters dropped, every Unicode space a space, every decimal digit an ASCII digit, Cyrillic/Greek/
Armenian look-alike letters mapped to Latin. Two views, because dropping format characters glues words ('approved<ZWSP>now') while replacing them with a
space splits words ('Brookfield<SHY>Hollow'): name scans test BOTH. Callers bound the length first (`limits.Limits`); `fold` is linear."""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from dealdesk.core_copy.textnorm import fold
from dealdesk.errors import Malformed

MAX_SCAN_CHARS = 20_000  # hard ceiling for any scan; the intake limits (10k) are lower
_SPACEY = {"Cf", "Cc", "Mn", "Me", "Zl", "Zp"}


def views(text: object) -> tuple[str, str]:
    """(glued, spaced), both folded, casefolded, whitespace collapsed. A non-string is an empty view; an over-long string is Malformed."""
    if not isinstance(text, str):
        return "", ""
    if len(text) > MAX_SCAN_CHARS:
        raise Malformed("text too long to scan")
    return _views(text)


@lru_cache(maxsize=65536)
def _views(text: str) -> tuple[str, str]:
    spaced = "".join(" " if unicodedata.category(ch) in _SPACEY else ch for ch in text)
    return fold(text, casefold=True, collapse_ws=True), fold(spaced, casefold=True, collapse_ws=True)


INJECTION = (
    "ignore previous", "ignore all previous", "ignore the above", "disregard", "system prompt", "you are now", "new instructions",
    "mark as approved", "mark this approved", "auto-approve", "auto approve", "already approved", "approved by", "skip approval",
    "bypass", "override", "do not tell", "reveal", "developer message", "jailbreak", "act as", "pre-approved", "pre approved",
)  # fmt: skip


def injection_flags(text: object) -> list[str]:
    """R-DEALDESK-050: warn-only screen (never decides). Matches on the folded view, with and without spaces, so format characters, look-alike letters
    and spaced-out letters ('i g n o r e') cannot hide a phrase."""
    v = views(text)[0]
    squashed = v.replace(" ", "")
    return sorted(p for p in INJECTION if p in v or p.replace(" ", "") in squashed)
