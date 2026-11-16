"""Demo-local name escaping for refused file names, on top of the pinned core module ``safe_text`` (which stays a byte copy; see CORE_COPIES.md).

``safe_name`` differs from ``safe_text.clean`` in what a file name needs: it never strips escape sequences (the ESC byte is shown as visible text, so
ESC followed by "[2K" cannot collide with a name without it), it also treats lone surrogates, invisible and look-alike code points and every kind of
space as forbidden, it writes code points above U+FFFF as eight-digit escapes, and it doubles a literal backslash so that the text of an escape ("backslash x1b")
cannot be typed into a real name to look like an ESC byte. The result always encodes to UTF-8. A cut (``limit``) never splits an escape.
Promotion request for core (ledger-ready): add these extra ranges and an ``escape_ansi`` option to core ``safe_text``; then delete this module."""

from __future__ import annotations

from . import safe_text

# invisible, look-alike and space-like code points that core safe_text does not cover
_EXTRA = (
    (0x00A0, 0x00A0),
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x2000, 0x200A),
    (0x202F, 0x202F),
    (0x205F, 0x205F),
    (0x2065, 0x2065),
    (0x206A, 0x206F),
    (0x2800, 0x2800),
    (0x3000, 0x3000),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xFFF9, 0xFFFC),
    (0xE0100, 0xE01EF),
    (0xD800, 0xDFFF),
)


def is_forbidden(ch: str) -> bool:
    o = ord(ch)
    return safe_text.is_forbidden(ch, keep_whitespace=False) or any(a <= o <= b for a, b in _EXTRA)


def _visible(ch: str) -> str:
    o = ord(ch)
    return f"\\x{o:02x}" if o < 0x100 else f"\\u{o:04x}" if o < 0x10000 else f"\\U{o:08x}"


def safe_name(value: object, limit: int | None = None) -> str:
    """The value with every forbidden character shown as visible escape text and every backslash doubled; nothing is removed. With ``limit`` the
    result is cut before the piece that would pass it and ends in three dots."""
    out: list[str] = []
    size = 0
    for ch in str(value):
        piece = "\\\\" if ch == "\\" else _visible(ch) if is_forbidden(ch) else ch
        if limit is not None and size + len(piece) > limit:
            out.append("...")
            break
        out.append(piece)
        size += len(piece)
    return "".join(out)
