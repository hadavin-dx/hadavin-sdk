"""The text rules of ``pathguard``: no file system is asked here. The refusal type, the byte limits, and the rules that read
only the text of a name or a path (R1 to R7 and R12 for one name; R4 and R5 for a whole path).

Split from ``pathguard`` by responsibility: this file decides from text alone; ``pathguard`` asks the operating system
(resolve, links, containment) and is the one entry point callers import. Nothing outside ``pathguard`` imports this file.
"""

from __future__ import annotations

import re
from pathlib import PurePath

from hadavin_sdk.errors import ConfigError

MAX_COMPONENT_BYTES = 255  # one name, in UTF-8 bytes (the usual file system limit)
# ``atomic_write`` adds 22 bytes (".<name>.<16 hex>.tmp"): the longest name it can write
MAX_WRITE_NAME_BYTES = MAX_COMPONENT_BYTES - 22
# a whole path, in UTF-8 bytes: PATH_MAX is 4096 counting the closing NUL, so 4095 is the longest path and 4096 is refused
MAX_PATH_BYTES = 4095

# COM and LPT also come with the superscript digits 1, 2, 3 (escapes)
_DIGITS = "0123456789\u00b9\u00b2\u00b3"
_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", "CLOCK$"}
    | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in _DIGITS}
)
# Characters that hide or reorder printed text: one named range per line, built with ``chr()``. A test and a mutant each.
CONTROL_RANGES = (
    ("C0 controls and NUL", 0x0000, 0x001F),
    ("DEL and C1 controls", 0x007F, 0x009F),
    ("soft hyphen", 0x00AD, 0x00AD),
    ("combining grapheme joiner", 0x034F, 0x034F),
    ("Arabic letter mark", 0x061C, 0x061C),
    ("Hangul fillers", 0x115F, 0x1160),
    ("Khmer inherent vowels", 0x17B4, 0x17B5),
    ("Mongolian vowel separator", 0x180E, 0x180E),
    ("zero-width and direction marks", 0x200B, 0x200F),
    ("line and paragraph separators and bidirectional embeddings", 0x2028, 0x202E),
    ("word joiner, invisible operators, isolates and deprecated format characters", 0x2060, 0x206F),
    ("braille blank", 0x2800, 0x2800),
    ("Hangul filler", 0x3164, 0x3164),
    ("variation selectors", 0xFE00, 0xFE0F),
    ("byte order mark", 0xFEFF, 0xFEFF),
    ("halfwidth Hangul filler", 0xFFA0, 0xFFA0),
    ("interlinear annotation", 0xFFF9, 0xFFFB),
    ("musical symbol format characters", 0x1D173, 0x1D17A),
    ("tag characters", 0xE0000, 0xE007F),
    ("variation selectors supplement", 0xE0100, 0xE01EF),
)
_CONTROL = re.compile(
    "["
    + "".join(f"{re.escape(chr(lo))}-{re.escape(chr(hi))}" for _, lo, hi in CONTROL_RANGES)
    + "]"
)
# Characters Windows does not allow in a file name (the colon is R3). Refused on every system, as PathRefused.
_WINDOWS_INVALID = re.compile(r'[<>"|?*]')


class PathRefused(ConfigError):
    """A path or name was refused. ``rule`` is R1 to R13. The text names the argument and the problem, never the value."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule

    def __reduce__(self) -> tuple[type, tuple[str, str]]:
        return (PathRefused, (self.rule, str(self)))  # so copy and pickle keep the rule


def refuse(rule: str, what: str, text: str) -> PathRefused:
    return PathRefused(rule, f"{what}: {text}")


def name_bytes(text: str) -> int:
    """The length of ``text`` in UTF-8 bytes, the unit of every limit here. A lone surrogate counts 3 bytes (it would be
    refused later as unencodable, so counting it as 3 over-refuses and never under-refuses)."""
    return len(text.encode("utf-8", errors="surrogatepass"))


def check_name(name: str, what: str) -> None:
    """Rules R1 to R7 for one name (a single path component)."""
    if not isinstance(name, str):
        raise refuse("R1", what, "not a plain name")
    if name in ("", ".", ".."):
        raise refuse("R1", what, "not a plain name")
    if _CONTROL.search(name):
        raise refuse("R4", what, "contains a control character")
    if "/" in name or "\\" in name:
        raise refuse("R2", what, "contains a separator")
    if ":" in name:
        raise refuse("R3", what, "contains a colon")
    if _WINDOWS_INVALID.search(name):
        raise refuse("R12", what, "contains a character Windows does not allow")
    if name_bytes(name) > MAX_COMPONENT_BYTES:
        raise refuse("R5", what, "too long")
    if name[-1] in ". ":
        raise refuse("R6", what, "ends with a dot or space")
    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:
        raise refuse("R7", what, "reserved device name")


def check_text(text: str, what: str) -> None:
    """R4 for a whole path text, then R5 in bytes: the whole text and each name in it (the system stops at 255 bytes per
    name, so a longer name in any position would make a later ``is_file`` raise). Text only: no file system call."""
    if _CONTROL.search(text):
        raise refuse("R4", what, "contains a control character")
    if name_bytes(text) > MAX_PATH_BYTES or any(
        name_bytes(p) > MAX_COMPONENT_BYTES for p in PurePath(text).parts
    ):
        raise refuse("R5", what, "too long")
