"""Hidden items: characters and escape sequences a reader does not see, removed once, before anything else reads the text.

A *hidden item* is one member of the classes "removed" or "space-like" below, or one whole escape sequence (the colour
codes a terminal prints, a window-title command, ...). They are not shown on a screen, yet one in the middle of a key cut
the key in two for every pattern of the redactor. `strip` gives the two readings of a text the choke point works with:

* the *joined reading*: every run of removed items deleted, every space-like item turned into one space. Values are
  FOUND in it.
* the *spaced reading*: the same, except that where a run of removed items has a word character (letter, digit,
  underscore) directly on both sides, one space is left in its place, because on main such an item acted as a word
  boundary and a text like `user` + BEL + a key stays masked. Placeholders are put into it.

A *run* is a longest stretch of removed items (single characters and whole escape sequences) with nothing else between.
Ignorable characters (zero-width characters, variation selectors, ...) are neither removed nor word characters: they stay
in the text, are ignored for MATCHING only (`IGNORABLE_RE`, used by `runmap.canonical`), and split a run.

The escape-sequence reader is ONE left-to-right state machine; it never looks more than one character ahead, so it is
linear (the PR H ticket, section 4.1, holds the complete state table; the test oracle `tests/hidden_oracle.py` is a
second, hand-written implementation of the same table). It does not imitate a terminal: cursor movement, overstrike and
erase sequences are removed, never played.

This module imports nothing from the package (standard library `re` and `unicodedata` only), so every layer can use it.
Standards the grammar follows (read from memory, the standards text was not reachable): ECMA-48 (control characters and
control sequences), ECMA-35 (short escape sequences), Unicode Annex 44 (Default_Ignorable_Code_Point).
"""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

# ---- the classes (PR H ticket, section 3) --------------------------------------------------------------------------


def _chars(*spans: tuple[int, int]) -> frozenset[str]:
    return frozenset(chr(c) for lo, hi in spans for c in range(lo, hi + 1))


# C0 except tab, line feed, carriage return and the four space-like ones; DEL; C1 except U+0085. ESC, CAN and SUB are
# members. In all: 55 single characters.
REMOVED_CHARS: frozenset[str] = _chars(
    (0x00, 0x08), (0x0E, 0x1B), (0x7F, 0x7F), (0x80, 0x84), (0x86, 0x9F)
)
# White space of the kinds that are also line breaks to some readers: turned into one U+0020. In all: 9.
SPACE_LIKE: frozenset[str] = _chars((0x0B, 0x0C), (0x1C, 0x1F), (0x85, 0x85), (0x2028, 0x2029))

_ESC, _CAN, _SUB, _BEL, _ST = "\x1b", "\x18", "\x1a", "\x07", "\x9c"
_C1_CSI = "\x9b"
_C1_STRING = {
    "\x9d": True,
    "\x90": False,
    "\x98": False,
    "\x9e": False,
    "\x9f": False,
}  # True = OSC (ends at BEL too)
_ESC_STRING = {"]": True, "P": False, "X": False, "^": False, "_": False}
# C0 characters dropped INSIDE a control sequence without ending it: every C0 except ESC, CAN, SUB, LF and CR; and DEL.
_CSI_DROP = _chars(
    (0x00, 0x09), (0x0B, 0x0C), (0x0E, 0x17), (0x19, 0x19), (0x1C, 0x1F), (0x7F, 0x7F)
)

# The first character of any hidden item (a candidate; the state machine decides what the item is), and of a SEQUENCE
# item only (an item that starts with ESC or a C1 opener: what `strip_sequences` removes).
_ANY = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]")
ANY = _ANY  # public name: `ANY.search(text)` is None when the text holds no removed or space-like item
_SEQ_ANY = re.compile(r"[\x1b\x90\x98\x9b\x9d-\x9f]")
_CSI_PARAMS = re.compile(r"[\x30-\x3f]*([\x20-\x2f]*)")
_CSI_INTER = re.compile(r"()[\x20-\x2f]*")
# where a string sequence can end: ST, CAN, SUB, BEL (OSC only), ESC, a line end
_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\x9c\n\r]")
_STRING_END = re.compile(r"[\x18\x1a\x1b\x9c\n\r]")

# ---- the ignorable characters (Unicode Default_Ignorable_Code_Point) -----------------------------------------------
# Unicode 15.0.0, from perl 5.38.2; the same code points as the `regex` package 2026.9.29 and as the derivation rule
# of the ticket (4,174 code points). The data file is `tests/fixtures/default_ignorable_perl5382_unicode1500.txt` and
# this literal is printed from it by `tools/gen_default_ignorable.py`; a test pins both. The Unicode licence check of
# that file is OPEN (the licence text could not be fetched on 2026-11-11).
UNICODE_DATA_VERSION = "15.0.0"
IGNORABLE_RANGES: tuple[tuple[int, int], ...] = (
    (0x00AD, 0x00AD),
    (0x034F, 0x034F),
    (0x061C, 0x061C),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)


def _ignorable_class() -> str:
    """One regular-expression character class: the ranges above plus every category Cf code point above U+007F (that
    is what main's `canonical` already dropped; 32 of them are not in the property, for example U+0600..U+0605). Every
    Cf character of Unicode lies in planes 0, 1 and 14, so only those are scanned (about 20 ms at import instead of
    100 ms); a test derives the set over all 1,114,112 code points and compares."""
    points = {c for lo, hi in IGNORABLE_RANGES for c in range(lo, hi + 1)}
    for plane in (range(0x80, 0x20000), range(0xE0000, 0xF0000)):
        points.update(c for c in plane if unicodedata.category(chr(c)) == "Cf")
    spans: list[list[int]] = []
    for c in sorted(points):
        if spans and spans[-1][1] == c - 1:
            spans[-1][1] = c
        else:
            spans.append([c, c])
    return "[" + "".join(rf"\U{a:08x}-\U{b:08x}" for a, b in spans) + "]"


IGNORABLE_RE = re.compile(_ignorable_class())


def is_ignorable(ch: str) -> bool:
    """True for one ignorable character (the same set as `IGNORABLE_RE`)."""
    return IGNORABLE_RE.match(ch) is not None


def _is_word(ch: str) -> bool:
    """A word character (letter, digit, underscore) that is not ignorable: the neighbour test of the glue rule."""
    return (ch.isalnum() or ch == "_") and IGNORABLE_RE.match(ch) is None


is_word = _is_word  # public name: the redactor's gap pattern puts a space only between two such characters


# ---- the reader -----------------------------------------------------------------------------------------------------


def _csi_end(text: str, k: int) -> int:
    """The end of a control sequence whose body starts at `k`, in the order ECMA-48 gives: parameter bytes (0x30-0x3F), then
    intermediate bytes (0x20-0x2F), then one final byte (0x40-0x7E) that is part of the item. A parameter byte after an
    intermediate byte is out of order: the item ends BEFORE it and that byte is read afresh as text (a letter or digit
    after `ESC [` and a space is the start of a value, and main kept it). CAN or SUB abort the sequence and go with it;
    a dropped C0 character or DEL is part of the item and the sequence goes on; anything else (a line end, ESC, a C1 or
    non-ASCII character) ends the item BEFORE that character, which is then read afresh. The end of the text ends it."""
    n = len(text)
    inter = False
    while k < n:
        run = (_CSI_INTER if inter else _CSI_PARAMS).match(text, k)
        if run is not None:
            inter = inter or bool(run.group(1))
            k = run.end()
        if k >= n:
            return n
        c = text[k]
        if "@" <= c <= "~" or c == _CAN or c == _SUB:
            return k + 1
        if c in _CSI_DROP:
            k += 1
            continue
        return k
    return n


def _string_end(text: str, k: int, osc: bool) -> int:
    """The end of a string sequence (OSC, DCS, SOS, PM, APC) whose payload starts at `k`. It ends, together with its
    terminator, at ST (U+009C or ESC backslash), CAN, SUB or, for an OSC only, BEL. It ends BEFORE an ESC that is not
    followed by a backslash (another sequence starts) and before a line end (the line end is kept), and at the end of
    the text: so a string that never ends blanks the rest of its line and no more."""
    m = (_STRING_END_OSC if osc else _STRING_END).search(text, k)
    if m is None:
        return len(text)
    c = m.group()
    if c == _ESC:
        return m.end() + 1 if text.startswith("\\", m.end()) else m.start()
    if c in "\n\r":
        return m.start()
    return m.end()


def _item_end(text: str, i: int, consume: bool = False) -> int:
    """The end of the sequence item that starts with ESC or a C1 opener at `i` (ground state of the table). With `consume`
    the final byte of an nF, Fp, Fe or Fs sequence always goes with it, a letter or digit too (the ticket grammar, the
    reading of a terminal; `strip_consuming`)."""
    c = text[i]
    n = len(text)
    if c == _C1_CSI:
        return _csi_end(text, i + 1)
    if c != _ESC:
        return _string_end(text, i + 1, _C1_STRING[c])
    j = i + 1
    if j >= n:
        return j
    d = text[j]
    if d == "[":
        return _csi_end(text, j + 1)
    if d in _ESC_STRING:
        return _string_end(text, j + 1, _ESC_STRING[d])
    if (
        "\x20" <= d <= "\x2f"
    ):  # nF: intermediates, then one final byte 0x30-0x7E (kept as text when a letter or digit, D-026)
        k = j
        while k < n and "\x20" <= text[k] <= "\x2f":
            k += 1
        if k < n and "\x30" <= text[k] <= "\x7e" and (consume or not text[k].isalnum()):
            # D-026 (as built): a letter or digit after the intermediates is not a final byte here: it may be the start of a
            # value (ESC, space, then a key), and the intermediates may be part of it (a dash in an id). Only the ESC goes.
            return k + 1
        return i + 1  # no final byte, or a letter or digit: only the ESC goes
    if "\x30" <= d <= "\x7e":  # Fp, Fe, Fs (and a stray ESC backslash)
        # A digit or lower-case letter stays as text, as in main (`ESC e` + `yJ...` keeps the `e` of a token); an upper-case
        # letter is a C1 function (ESC `M` moves the cursor up) and goes, as in main: it is ambiguous with the first letter of
        # a value, which main loses too (D-026 gave the same rule for the last byte of an nF sequence).
        return j if (d.isalnum() and not d.isupper() and not consume) else j + 1
    return i + 1  # a lone ESC; the next character is read afresh


def _scan(text: str, sequences_only: bool, consume: bool = False) -> tuple[str, str]:
    """(joined, spaced) of `text`; the same object twice when they are equal. With `sequences_only` only the items
    that start with ESC or a C1 opener are hidden items: every other character stays as written."""
    pattern = _SEQ_ANY if sequences_only else _ANY
    found = pattern.search(text)
    if found is None:
        return text, text
    n = len(text)
    joined: list[str] = []
    spaced: list[str] = []
    glued = False
    i = 0
    last = ""  # the last character written; the left neighbour of a run
    left_word = False
    in_run = False
    while True:
        start = found.start() if found is not None else n
        if start > i:  # plain text up to the next candidate
            if in_run:
                if left_word and _is_word(text[i]):
                    spaced.append(" ")
                    glued = True
                in_run = False
            piece = text[i:start]
            joined.append(piece)
            spaced.append(piece)
            last = piece[-1]
        if found is None:
            break
        c = text[start]
        if c in SPACE_LIKE and not sequences_only:
            in_run = (
                False  # a space-like item is not a text character, so no glue on either side of it
            )
            joined.append(" ")
            spaced.append(" ")
            last = " "
            i = start + 1
        else:
            end = (
                _item_end(text, start, consume)
                if (c == _ESC or c == _C1_CSI or c in _C1_STRING)
                else start + 1
            )
            if not in_run:
                in_run = True
                left_word = _is_word(last) if last else False
            i = end
        found = pattern.search(text, i)
    out_joined = "".join(joined)
    return out_joined, "".join(spaced) if glued else out_joined


def strip(text: str) -> tuple[str, str]:
    """The joined and the spaced reading of `text` (see the module text). One pass, linear. When the text holds no
    removed or space-like item it is returned untouched, twice (the same object); ignorable characters are not handled
    here. Idempotent."""
    return _scan(text, False)


def strip_consuming(text: str) -> tuple[str, str]:
    """The joined and spaced reading when every escape sequence takes its final byte, a letter or digit too (`ESC ( B`,
    `ESC e`): what a terminal does. Main-compatible `strip` keeps such a letter (D-026, D-029) because it may start a
    value; this reading is searched as one more reading, so a value cut by `tput sgr0` (`ESC ( B ESC [ m`) is found."""
    return _scan(text, False, True)


def strip_sequences(text: str) -> str:
    """Only the escape sequences removed (an item that starts with ESC or a C1 opener: U+009B, U+009D, U+0090, U+0098,
    U+009E, U+009F, and a lone ESC); every other character stays as written. A space is left where a run of them stood
    between two word characters. Idempotent."""
    return _scan(text, True)[1]


def sequence_readings(text: str, consume: bool = False) -> tuple[str, str]:
    """The joined and the spaced reading of `text` with ONLY the escape sequences removed (the same two readings as
    `strip`, for the callers that read sequences and nothing else). With `consume` every sequence takes its final byte, a
    letter or digit too (`ESC ( B`), as in `strip_consuming`. The same object twice when they are equal."""
    return _scan(text, True, consume)


_CHAR_TABLE = {**dict.fromkeys(map(ord, REMOVED_CHARS)), **dict.fromkeys(map(ord, SPACE_LIKE), " ")}
_SPACE_TABLE = dict.fromkeys(map(ord, SPACE_LIKE), " ")
_REMOVED_RUN = re.compile("[" + "".join(re.escape(c) for c in sorted(REMOVED_CHARS)) + "]+")


def strip_characters(text: str) -> str:
    """The *character reading*: every removed character deleted ON ITS OWN (an escape sequence is not read as one, so the
    text a sequence would swallow and the letter after an ESC stay), every space-like character one space. It is what
    main's callers saw. The redactor searches it as one more reading and uses it only when it shows a value the
    grammar's reading cannot and hides none the grammar's reading holds (PR H, no step back from main). Idempotent."""
    return text.translate(_CHAR_TABLE) if _ANY.search(text) else text


def _gap(m: re.Match[str]) -> str:
    """One space for a run of removed characters with a word character directly on both sides, else nothing."""
    s, a, b = m.string, m.start(), m.end()
    return " " if a and b < len(s) and _is_word(s[a - 1]) and _is_word(s[b]) else ""


def characters_readings(text: str) -> tuple[str, str]:
    """The joined and the spaced *character reading* (see `strip_characters`): the joined one is `strip_characters`; in the
    spaced one a space stands where a run of removed characters had a word character directly on both sides (the same glue
    rule as `strip`, so `user` + BEL + a key stays two words). The same object twice when they are equal; idempotent."""
    if _ANY.search(text) is None:
        return text, text
    spread = text.translate(_SPACE_TABLE)
    joined = _REMOVED_RUN.sub("", spread)
    spaced = _REMOVED_RUN.sub(_gap, spread)
    return joined, joined if spaced == joined else spaced


def leaves_text(text: str) -> bool:
    """Does the character reading (`strip_characters`) show text that the grammar's reading removes, other than the one
    letter or digit after an ESC? True for the body of a control sequence (`[0m`, `]0;title`, `(B`): there the character
    reading is not a copy of the grammar's reading with a letter put back, so it must not stand in for it as a result. One
    pass over the escape items, linear."""
    i, n = 0, len(text)
    while (m := _SEQ_ANY.search(text, i)) is not None:
        k = m.start()
        end = _item_end(text, k)
        body = text[k + 1 : end]
        if body and not (len(body) == 1 and body.isalnum()):
            return True
        i = max(end, k + 1)
        if i >= n:
            break
    return False


class Readings(NamedTuple):
    """Every reading of one text that a searcher must look in. `readings` is where the redactor (the original text and
    each decoded view that holds a hidden item) and the scrub of handed-out secrets (`tools._scrub`) take them from. Three
    places still read a text with `strip` on their own, for a different purpose: `runmap` strips a decoded view before the
    pass over it, `tools._scrub` strips its own result once to check it, and `Redactor.find` (public `redact()`) reads only
    escape sequences (`sequence_readings`); all use the same `_scan`, so they agree:

    * `joined`, `spaced`: the grammar's two readings (`strip`);
    * `characters`, `characters_spaced`: every removed character deleted on its own, no sequence read, without and with the
      glue space (`characters_readings`, what main saw);
    * `consuming_joined`, `consuming_spaced`: the two readings when every escape sequence takes its final byte, a letter
      or digit too (`strip_consuming`, what a terminal does: `ESC ( B`).

    A reading that equals another is the SAME object, so a caller finds the distinct ones with `distinct`."""

    joined: str
    spaced: str
    characters: str
    characters_spaced: str
    consuming_joined: str
    consuming_spaced: str

    def distinct(self) -> tuple[str, ...]:
        """The readings that differ from each other, in the order above."""
        return tuple(dict.fromkeys(self))


def readings(text: str) -> Readings:
    """All readings of `text` (see `Readings`). A text with no hidden item is the one reading five times. The consuming
    readings differ from the grammar's only where an escape character starts a sequence, so a text without ESC does not
    pay for a second scan."""
    joined, spaced = strip(text)
    if joined is text:
        return Readings(text, text, text, text, text, text)
    cj, cs = strip_consuming(text) if _ESC in text else (joined, spaced)
    chars, chars_spaced = characters_readings(text)
    return Readings(joined, spaced, chars, chars_spaced, cj, cs)
