"""Output safety (A-11): one function, applied at every output sink (CLI cells, SQL, errors, anything printed).

Database values and model text are untrusted: a value can carry terminal control sequences (erase a line,
print a fake "all checks passed", open a link). `clean` removes complete ANSI/OSC sequences whole, then turns
every remaining control, C1, DEL, bidi or format character into visible escape text, so an attack is visible
rather than silently deleted. Hashes are computed over the raw values before cleaning; only display text is cleaned.
"""

from __future__ import annotations

import re

# ESC [ params intermediates final-byte   |   ESC ] ... BEL or ESC \ (string terminator)
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")

# Bidi and format characters (same set as the validator pre-filter).
_FORMAT_RANGES = (
    (0x00AD, 0x00AD), (0x061C, 0x061C), (0x180E, 0x180E), (0x200B, 0x200F), (0x2028, 0x202E),
    (0x2060, 0x2064), (0x2066, 0x2069), (0xFEFF, 0xFEFF), (0xE0000, 0xE007F),
)  # fmt: skip


def is_forbidden(ch: str, *, keep_whitespace: bool = True) -> bool:
    """True for a character that must never reach a terminal or a statement: C0 controls (except newline and tab
    when `keep_whitespace`), DEL, C1 controls, bidi and format characters."""
    o = ord(ch)
    if o < 0x20:
        return not (keep_whitespace and ch in "\n\t")
    return o == 0x7F or 0x80 <= o <= 0x9F or any(a <= o <= b for a, b in _FORMAT_RANGES)


def _visible(ch: str) -> str:
    o = ord(ch)
    return f"\\x{o:02x}" if o < 0x100 else f"\\u{o:04x}"


def clean(value: object, *, cell: bool = False) -> str:
    """Display-safe text. `cell=True` also folds newline and tab to one space (table cells)."""
    text = _ANSI.sub("", str(value))
    out = []
    for ch in text:
        if cell and ch in "\n\t":
            out.append(" ")
        elif is_forbidden(ch):
            out.append(_visible(ch))
        else:
            out.append(ch)
    return "".join(out)
