"""The independent checker of the diagnostics tests: ``leaks`` (a DENY check on canaries) and ``grammar_ok`` (an exact grammar).

``leaks`` knows nothing about the grammar and ``grammar_ok`` nothing about canaries. The text fold of ``guard/textnorm.py`` is used
here only as a DENY check (over-matching is the safe side); nothing in ``src/`` calls it for this purpose. ``leaks_literal`` is the
weaker lower bound used by one test (``test_strict_oracle_is_a_superset``); it never replaces ``leaks``.
"""

from __future__ import annotations

import html
import re
import unicodedata
import urllib.parse

from hadavin_sdk.guard.textnorm import TextnormError, scan_keyset

_ESCAPES = (
    re.compile(r"\\x([0-9a-fA-F]{2})"),
    re.compile(r"\\u([0-9a-fA-F]{4})"),
    re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}"),
    re.compile(r"%u([0-9a-fA-F]{4})"),
    re.compile(r"=([0-9A-F]{2})"),
)
_PERCENT_DEPTH = 4

_KIND = r"[A-Za-z0-9_.]{1,80}"
_FACT = r" [a-z_]{1,30}=-?[A-Za-z0-9_.-]{1,120}"
GRAMMAR_A = re.compile(
    rf"{_KIND}: diag_v=1 code=[a-z_]{{1,40}} step=[a-z_]{{1,30}} at=(?:-|[A-Za-z0-9_./-]{{1,120}}:[0-9]{{1,7}}) "
    rf"fp=[0-9a-f]{{8}}(?:{_FACT}){{0,12}}"
)
_TYPE = r"[a-z_]{1,17}"
GRAMMAR_V = re.compile(rf"{_TYPE}(?:; {_TYPE}){{0,4}}(?:; \+[0-9]{{1,7}} more)?")


def grammar_ok(output: str, kind: str = "A") -> bool:
    """The output is pure ASCII and matches the whole grammar for its kind: ``"A"`` (a rendered line) or ``"V"`` (validation text)."""
    if type(output) is not str or not output.isascii():
        return False
    pattern = GRAMMAR_A if kind == "A" else GRAMMAR_V
    return pattern.fullmatch(output) is not None


def _decode(pattern: re.Pattern[str], text: str) -> str:
    return pattern.sub(lambda m: chr(int(m.group(1), 16)), text)


def views(output: str) -> list[str]:
    """The text and its decoded views: HTML entities, percent-decoding to depth 4, backslash escapes and quoted-printable."""
    found = [output, html.unescape(output)]
    text = output
    for _ in range(_PERCENT_DEPTH):
        text = urllib.parse.unquote(text)
        found.append(text)
    for pattern in _ESCAPES:
        found.append(_decode(pattern, output))
    found.append(html.unescape(text))
    return found


def leaks(output: str, canaries: tuple[str, ...]) -> bool:
    """True if a key of a canary is inside a key of the output or of a decoded view of it. A ``TextnormError`` counts as a leak."""
    try:
        wanted = [k for c in canaries for k in scan_keyset(c)]
        for view in views(output):
            keys = scan_keyset(view)
            if any(w in k for w in wanted for k in keys):
                return True
    except TextnormError:
        return True
    return False


def _literal_key(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).casefold()
    return "".join(ch for ch in folded if ch.isalnum() and unicodedata.category(ch) != "Mn")


def leaks_literal(output: str, canaries: tuple[str, ...]) -> bool:
    """The lower bound: NFKD, case fold, letters and digits only, plain substring. Standard library only."""
    keys = [_literal_key(c) for c in canaries]
    return any(k and k in _literal_key(v) for k in keys for v in views(output))
