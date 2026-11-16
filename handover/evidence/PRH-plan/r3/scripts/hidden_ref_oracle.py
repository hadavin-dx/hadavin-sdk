"""Reference oracle for PR H rev 3 (ticket section 4.1 grammar, section 3 classes, glue rule).

Written by the ticket author from the rev-3 grammar table, standard library only (no `re`, no hadavin_sdk), so a
property test can compare `hadavin_sdk.guard.hidden` against it. The builder copies it to `tests/hidden_oracle.py`
unchanged except for the module docstring. Run `python hidden_ref_oracle.py PERL_RANGE_FILE` for the self-check.
Every control or invisible character is written as an escape; the file holds none literally.
"""

from __future__ import annotations

import random
import sys
import unicodedata

ESC, BEL, CAN, SUB, ST_C1, LF, CR = "\x1b", "\x07", "\x18", "\x1a", "\x9c", "\n", "\r"

# ---- classes (section 3) -------------------------------------------------------------------------------------
REMOVED = frozenset(
    [chr(c) for c in range(0x00, 0x09)]
    + [chr(c) for c in range(0x0E, 0x1C)]
    + ["\x7f"]
    + [chr(c) for c in range(0x80, 0x85)]
    + [chr(c) for c in range(0x86, 0xA0)]
)
SPACE_LIKE = frozenset(["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x1f", "\x85", " ", " "])
LINE_END = frozenset([LF, CR])
C1_CSI = "\x9b"
C1_STRING = {"\x9d": "osc", "\x90": "dcs", "\x98": "sos", "\x9e": "pm", "\x9f": "apc"}
ESC_STRING = {"]": "osc", "P": "dcs", "X": "sos", "^": "pm", "_": "apc"}
SEQ_OPENERS = frozenset([ESC, C1_CSI, *C1_STRING])  # items that start a "sequence" item (strip_sequences scope)
# C0 characters that are dropped inside a CSI without ending it (ESC, CAN, SUB, LF, CR excluded)
CSI_DROP = frozenset(
    [chr(c) for c in range(0x00, 0x0A)]
    + ["\x0b", "\x0c"]
    + [chr(c) for c in range(0x0E, 0x18)]
    + ["\x19"]
    + [chr(c) for c in range(0x1C, 0x20)]
    + ["\x7f"]
)

# ---- ignorable set (section 1, rule written out; no Unicode data file needed) --------------------------------
# Other_Default_Ignorable_Code_Point plus Variation_Selector ranges (Unicode 15.0/15.1, from memory, cross-checked
# against perl 5.38.2's Unicode 15.0.0 property by this script), then every category Cf code point, minus the
# exclusions of the derivation rule (White_Space has no Cf member; U+FFF9..FFFB; U+13430..1343F; the
# Prepended_Concatenation_Mark characters).
OTHER_DI_AND_VS = (
    (0x034F, 0x034F), (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180D), (0x180F, 0x180F),
    (0x2065, 0x2065), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8),
    (0xE0000, 0xE0000), (0xE0002, 0xE001F), (0xE0080, 0xE0FFF),
)  # fmt: skip
EXCLUDED = (
    (0xFFF9, 0xFFFB), (0x13430, 0x1343F), (0x0600, 0x0605), (0x06DD, 0x06DD), (0x070F, 0x070F),
    (0x0890, 0x0891), (0x08E2, 0x08E2), (0x110BD, 0x110BD), (0x110CD, 0x110CD),
)  # fmt: skip


def derive_ignorable() -> frozenset[int]:
    out: set[int] = set()
    for a, b in OTHER_DI_AND_VS:
        out.update(range(a, b + 1))
    out.update(c for c in range(0x110000) if unicodedata.category(chr(c)) == "Cf")
    for a, b in EXCLUDED:
        out.difference_update(range(a, b + 1))
    return frozenset(out)


def read_range_file(path: str) -> frozenset[int]:
    out: set[int] = set()
    with open(path, encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            a, _, b = line.partition("..")
            out.update(range(int(a, 16), int(b or a, 16) + 1))
    return frozenset(out)


def to_ranges(points: frozenset[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for c in sorted(points):
        if out and out[-1][1] == c - 1:
            out[-1] = (out[-1][0], c)
        else:
            out.append((c, c))
    return out


# ---- the reader (section 4.1 grammar, rev 3) ------------------------------------------------------------------
# tokens: ("text", ch) | ("space", ch) | ("ign", ch) | ("removed", raw, kind) where kind is "single" or "seq"


def _is_ignorable(ch: str, ign: frozenset[int]) -> bool:
    return ord(ch) in ign or (ord(ch) > 0x7F and unicodedata.category(ch) == "Cf")


def tokens(text: str, ign: frozenset[int] = frozenset()):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == ESC:
            j = i + 1
            d = text[j] if j < n else ""
            if d == "[":
                k = _csi_end(text, j + 1)
                yield ("removed", text[i:k], "seq")
                i = k
                continue
            if d in ESC_STRING:
                k = _string_end(text, j + 1, ESC_STRING[d])
                yield ("removed", text[i:k], "seq")
                i = k
                continue
            if d and 0x20 <= ord(d) <= 0x2F:  # nF: intermediates, then one final 0x30-0x7E
                k = j
                while k < n and 0x20 <= ord(text[k]) <= 0x2F:
                    k += 1
                if k < n and 0x30 <= ord(text[k]) <= 0x7E:
                    yield ("removed", text[i : k + 1], "seq")
                    i = k + 1
                else:  # no final byte: only the ESC goes; the intermediates are read afresh as text
                    yield ("removed", ESC, "seq")
                    i = j
                continue
            if d and 0x30 <= ord(d) <= 0x7E:  # Fp, Fe, Fs (and a stray ESC backslash)
                yield ("removed", text[i : j + 1], "seq")
                i = j + 1
                continue
            yield ("removed", ESC, "seq")  # lone ESC; the next character is read afresh
            i = j
            continue
        if c == C1_CSI:
            k = _csi_end(text, i + 1)
            yield ("removed", text[i:k], "seq")
            i = k
            continue
        if c in C1_STRING:
            k = _string_end(text, i + 1, C1_STRING[c])
            yield ("removed", text[i:k], "seq")
            i = k
            continue
        if c in REMOVED:
            yield ("removed", c, "single")
        elif c in SPACE_LIKE:
            yield ("space", c)
        elif ign and _is_ignorable(c, ign):
            yield ("ign", c)
        else:
            yield ("text", c)
        i += 1


def _csi_end(text: str, k: int) -> int:
    """CSI body from k. Returns the index after the item (the item starts at the opener). On abort by a
    character that is read afresh (line end, ESC, C1, anything outside 0x20-0x7E that is not a dropped C0),
    the item ends BEFORE that character."""
    n = len(text)
    while k < n:
        o = ord(text[k])
        if 0x20 <= o <= 0x3F:
            k += 1
        elif 0x40 <= o <= 0x7E:
            return k + 1
        elif text[k] in (CAN, SUB):
            return k + 1  # aborted: what was read and the CAN/SUB are dropped
        elif text[k] in CSI_DROP:
            k += 1  # dropped, the sequence continues
        else:
            return k  # aborted; this character is read afresh
    return k


def _string_end(text: str, k: int, kind: str) -> int:
    """Index after the string item started before k. Ends: ST (ESC backslash or U+009C), BEL for OSC, CAN, SUB
    (all removed with the string); a line end or an ESC not followed by a backslash ends it BEFORE that character
    (read afresh); the end of the text."""
    n = len(text)
    while k < n:
        c = text[k]
        if c == ST_C1 or c in (CAN, SUB) or (kind == "osc" and c == BEL):
            return k + 1
        if c == ESC:
            if k + 1 < n and text[k + 1] == "\\":
                return k + 2
            return k
        if c in LINE_END:
            return k
        k += 1
    return k


def _word(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def readings(text: str, ign: frozenset[int] = frozenset(), sequences_only: bool = False) -> tuple[str, str]:
    """(joined, spaced). With sequences_only: only items that start with ESC or a C1 opener are removed; other
    single controls and space-like characters stay as text (the `strip_sequences` reading is `spaced`)."""
    toks = list(tokens(text, ign))
    if sequences_only:
        toks = [
            t if not (t[0] == "removed" and t[2] == "single") and t[0] != "space" else ("text", t[1])
            for t in toks
        ]
    joined: list[str] = []
    spaced: list[str] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t[0] != "removed":
            ch = " " if t[0] == "space" else t[1]
            joined.append(ch)
            spaced.append(ch)
            i += 1
            continue
        j = i
        while j < len(toks) and toks[j][0] == "removed":
            j += 1
        left = toks[i - 1] if i > 0 else None
        right = toks[j] if j < len(toks) else None
        if left and right and left[0] == "text" and right[0] == "text" and _word(left[1]) and _word(right[1]):
            spaced.append(" ")
        i = j
    return "".join(joined), "".join(spaced)


# ---- self-check ------------------------------------------------------------------------------------------------
GLUE_TABLE = [  # (input, joined, spaced) - section 4.1 glue table
    ("ab" + BEL + "cd", "abcd", "ab cd"),
    ("ab" + BEL + BEL + "cd", "abcd", "ab cd"),
    ("ab" + ESC + "[0m" + ESC + "[1m" + "cd", "abcd", "ab cd"),
    ("ab" + BEL + "​" + BEL + "cd", "ab​cd", "ab​cd"),
    ("ab" + BEL + "-cd", "ab-cd", "ab-cd"),
    ("ab" + BEL + " cd", "ab cd", "ab cd"),
    ("ab" + "\x0c" + BEL + "cd", "ab cd", "ab cd"),
    ("ab" + "\x00" + "cd", "abcd", "ab cd"),
    (ESC + "[0mab", "ab", "ab"),
    ("ab\\" + LF + "cd", "ab\\" + LF + "cd", "ab\\" + LF + "cd"),
]
GRAMMAR_ROWS = [  # (name, input, joined) - section 4.1 grammar table, one row per terminator and state
    ("csi", "a" + ESC + "[1;31mb", "ab"),
    ("csi c1", "a" + C1_CSI + "0mb", "ab"),
    ("csi final 0x7E", "a" + ESC + "[2~b", "ab"),
    ("csi final 0x40", "a" + ESC + "[2@b", "ab"),
    ("csi private+intermediate", "a" + ESC + "[?25l" + ESC + "[1 qb", "ab"),
    ("csi c0 inside dropped", "a" + ESC + "[0" + BEL + "mb", "ab"),
    ("csi del inside dropped", "a" + ESC + "[0\x7fmb", "ab"),
    ("csi tab inside dropped", "a" + ESC + "[0\tmb", "ab"),
    ("csi CAN abort", "a" + ESC + "[12" + CAN + "mb", "amb"),
    ("csi SUB abort", "a" + ESC + "[12" + SUB + "mb", "amb"),
    ("csi LF abort", "a" + ESC + "[12" + LF + "mb", "a" + LF + "mb"),
    ("csi ESC abort", "a" + ESC + "[12" + ESC + "[0mb", "ab"),
    ("csi non-ASCII abort", "a" + ESC + "[12éb", "aéb"),
    ("csi end of text", "a" + ESC + "[12", "a"),
    ("osc BEL", "a" + ESC + "]0;t" + BEL + "b", "ab"),
    ("osc ST", "a" + ESC + "]0;t" + ESC + "\\b", "ab"),
    ("osc C1 ST", "a" + ESC + "]0;t" + ST_C1 + "b", "ab"),
    ("osc C1 opener", "a\x9d0;t" + BEL + "b", "ab"),
    ("osc CAN", "a" + ESC + "]0;t" + CAN + "b", "ab"),
    ("osc never ended, line end kept", "a" + ESC + "]0;t" + LF + "line two", "a" + LF + "line two"),
    ("osc never ended, CR kept", "a" + ESC + "]0;t" + CR + "x", "a" + CR + "x"),
    ("osc ended by ESC not backslash", "a" + ESC + "]0;t" + ESC + "[0mb", "ab"),
    ("osc end of text", "a" + ESC + "]0;title", "a"),
    ("dcs BEL is body", "a" + ESC + "Pq" + BEL + "x" + ESC + "\\b", "ab"),
    ("dcs C1", "a\x90q pay\x9cb", "ab"),
    ("sos pm apc", "a" + ESC + "Xs" + ESC + "\\" + ESC + "^p" + ESC + "\\" + ESC + "_a" + ESC + "\\b", "ab"),
    ("c1 csi inside string is body", "a" + ESC + "]0;" + C1_CSI + "t" + BEL + "b", "ab"),
    ("nF", "a" + ESC + "(Bb", "ab"),
    ("nF two intermediates", "a" + ESC + "#!8b", "ab"),
    ("nF no final", "a" + ESC + "(" + LF + "b", "a(" + LF + "b"),
    ("Fp", "a" + ESC + "7b", "ab"),
    ("Fe", "a" + ESC + "Mb", "ab"),
    ("Fs", "a" + ESC + "cb", "ab"),
    ("lone ESC at end", "a" + ESC, "a"),
    ("lone ESC before non-ASCII", "a" + ESC + "é", "aé"),
    ("lone ESC before LF", "a" + ESC + LF + "b", "a" + LF + "b"),
    ("ESC ESC [0m", "a" + ESC + ESC + "[0mb", "ab"),
    ("stray ST C1", "a" + ST_C1 + "b", "ab"),
]


def main() -> int:
    print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version)
    rc = 0
    print("REMOVED", len(REMOVED), "SPACE_LIKE", len(SPACE_LIKE), "overlap", len(REMOVED & SPACE_LIKE))
    if (len(REMOVED), len(SPACE_LIKE)) != (55, 9):
        rc = 1
    ign = derive_ignorable()
    print("derived ignorable", len(ign), "ranges", len(to_ranges(ign)))
    if len(sys.argv) > 1:
        perl = read_range_file(sys.argv[1])
        print("perl file", len(perl), "equal to derived:", perl == ign, "only perl", len(perl - ign), "only derived", len(ign - perl))
        rc |= perl != ign
    print("ranges:", " ".join(f"{a:04X}..{b:04X}" for a, b in to_ranges(ign)))
    for x, j, s in GLUE_TABLE:
        gj, gs = readings(x, ign)
        ok = (gj, gs) == (j, s)
        rc |= not ok
        print("glue", "PASS" if ok else "FAIL", ascii(x), ascii(gj), ascii(gs))
    for name, x, j in GRAMMAR_ROWS:
        gj, _ = readings(x, ign)
        ok = gj == j
        rc |= not ok
        print("grammar", "PASS" if ok else "FAIL", name, ascii(x), "->", ascii(gj))
    # properties over random strings: idempotent; joined holds no removed / space-like; spaced has no doubled glue
    alpha = sorted(REMOVED | SPACE_LIKE) + list("[]P^_X\\(#7Mc0;m q?ab_-é") + [ESC] * 6 + ["​", "͏", LF, "\t"]
    rnd = random.Random(20261111)
    bad = 0
    for _ in range(20000):
        x = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 24)))
        j, s = readings(x, ign)
        if readings(j, ign)[0] != j or readings(s, ign)[1] != s:
            bad += 1
        if any(c in REMOVED or c in SPACE_LIKE for c in j + s):
            bad += 1
        sq = readings(x, ign, sequences_only=True)[1]
        if readings(sq, ign, sequences_only=True)[1] != sq or any(c in SEQ_OPENERS for c in sq):
            bad += 1
    print("random 20000: property failures", bad)
    rc |= bad != 0
    # linear: an unterminated opener repeated (the O(n^2) shape the readiness review named)
    import time

    for unit in (ESC + "]", ESC + "[", ESC + "(", "\x9d"):
        t = []
        for n in (50_000, 200_000):
            x = (unit + "ab") * (n // (len(unit) + 2))
            a = time.process_time()
            readings(x, ign)
            t.append(time.process_time() - a)
        print("linear", ascii(unit), "50k %.3fs 200k %.3fs ratio %.2f" % (t[0], t[1], t[1] / max(t[0], 1e-3)))
    print("SELFCHECK", "PASS" if rc == 0 else "FAIL")
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
