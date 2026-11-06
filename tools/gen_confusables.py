"""Generate ``src/hadavin_sdk/guard/_confusables.py`` from the Unicode UTS #39 ``confusables.txt`` (the MA table) of the SAME Unicode
version as the interpreter pin ``defaults.TEXTNORM_PINNED_UNIDATA`` (15.1.0).

Run (stdlib only; offline: the data file is vendored in ``tools/data/confusables.txt``, Unicode License v3, the notice is in the file
and in the generated header):

    python tools/gen_confusables.py                      # reads tools/data/confusables.txt
    python tools/gen_confusables.py other.txt            # refused unless it has the pinned version, date and sha256

WHERE THE 15.1.0 FILE CAME FROM (one statement, read on 2026-11-06): the project lead fetched it on 2026-11-06 from
https://www.unicode.org/Public/security/15.1.0/confusables.txt (718,291 bytes). That the bytes equal the Unicode Consortium's upload is
checked by comparing the pinned sha256 below with a fresh download of that URL, which only a person with network access can do; the
same bytes (same sha256) are said to be in the Unicode Consortium's ``unicodetools`` repository (``data/security/15.1.0/``) and in the ICU
source tree at the tags ``release-74-1``, ``release-74-2`` and ``release-75-1`` (not checked by this package).

Why the version is checked: a look-alike table of another Unicode version than the interpreter's data maps code points the interpreter
does not know (or misses ones it does). The generator refuses a data file whose ``# Version:`` line is not the pin, BEFORE it looks at
the hash, so the message names the mismatch; a changed pin is a reviewed change of ``defaults.TEXTNORM_PINNED_UNIDATA``, the
``PINNED_*`` constants below and the generated file in one commit (moving the pin, for example to Python 3.14, is a data migration).

Two constants are written beside the table: ``TABLE_DIGEST`` (the SHA-256 of the table, see ``table_digest``) and ``MAX_VALUE_LEN`` (the
longest table value; a test compares it with the table. ``guard/textnorm.py`` does not read it: its size rule weighs every character from the table itself).

Python dependency: the name rules (below) read character NAMES from the running interpreter's ``unicodedata``; the checked-in output was
generated with Python 3.13.x / Unicode 15.1.0 (``DATA_UNICODEDATA`` in the generated file) and is the artifact. The test that compares the
output with the checked-in file runs on 15.0.0 (Python 3.12) and 15.1.0 (Python 3.13), which give the identical table.

The input must have the pinned version, date and sha256 below (UTS #39 15.1.0, dated 2023-08-11, 17:46:40 GMT); another file is refused,
so a changed table is a reviewed change. Licence: Unicode License v3 (data files may be copied and used with the copyright notice, which
the generated file carries).

Selection rules (all explicit, nothing hand-curated):
  * entries of the MA ("mixed-script, any-case") table only;
  * the SOURCE is one non-ASCII code point that survives the fold's earlier steps (NFKC leaves it unchanged, its category is not
    dropped), so the entry can actually fire;
  * the TARGET is entirely ASCII letters and digits (punctuation prototypes are left out on purpose: the fold keeps separators for
    the amount and date patterns);
  * SUPPLEMENT (below, explicit, 16 entries, never overrides the data): letters that read as a Latin letter but that UTS #39 does
    not list as MA (Cyrillic ka em te en ve ze, Greek kappa tau chi eta mu omega epsilon, Latin o/l/d with stroke). They
    were added by a design review and are pinned by tests/fixtures/textnorm_vectors.json;
  * NAME RULES (by Unicode character name, never by hand; data and supplement win over them; only a code point that no earlier
    fold step changes, that is NFKD- and NFKC-stable and whose category is kept, can fire):
      - ``LATIN LETTER SMALL CAPITAL X``, ``LATIN SMALL CAPITAL X`` and ``LATIN SMALL CAPITAL LETTER X`` (X one letter, optionally ``WITH`` a
        mark) read as the capital X (UTS #39 lists only a few);
      - ``NEGATIVE CIRCLED LATIN CAPITAL LETTER X``, ``NEGATIVE SQUARED LATIN CAPITAL LETTER X``, ``CROSSED NEGATIVE SQUARED LATIN CAPITAL
        LETTER P`` and ``REGIONAL INDICATOR SYMBOL LETTER X`` read as the capital X, ``SQUARED LATIN SMALL LETTER D`` as d (NFKC maps
        the other squared letters and the circled letters, not these);
      - ``LATIN CAPITAL LETTER X WITH <mark>`` and ``LATIN SMALL LETTER X WITH <mark>`` (X one letter: H with stroke, B with hook, ...)
        read as X in the case of the name;
      - ``[DINGBAT] [NEGATIVE|DOUBLE] CIRCLED [SANS-SERIF] DIGIT|NUMBER <ZERO..NINE|TEN>`` read as that digit (ten as ``10``; NFKC maps the
        plain circled digits, not these).
    NAME RULES COVER: small capitals, negative circled and negative squared letters, the crossed negative squared P, regional indicator letters, the squared small d, Latin letters with a stroke, hook or similar mark, and the circled, negative circled, double circled and sans-serif digits and numbers (0 to 10); the circled numbers 11 to 20 are read by NFKC, the negative circled numbers 11 to 20 are not read (a named gap).
    The names come from the running interpreter's ``unicodedata`` (recorded in the generated header; 15.0.0 and 15.1.0 give one table).
  * the prototype of capital I, Greek Iota and Cyrillic I in the data is lower-case ``l``; an UPPER-case source with prototype ``l``
    is written as ``I`` (what a reader sees), every other source keeps its prototype.
"""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

PINNED_VERSION = "15.1.0"  # must equal defaults.TEXTNORM_PINNED_UNIDATA (a test checks it)
PINNED_DATE = "2023-08-11, 17:46:40 GMT"
PINNED_SHA256 = "8289f833e4cf78fde56b2080dc0e42934ef5182c9c3f4dd1fbdf2bced69fd5ed"
SUPPLEMENT: dict[int, str] = {
    0x43A: "k", 0x43C: "m", 0x442: "t", 0x43D: "h", 0x432: "b", 0x437: "3",
    0x3BA: "k", 0x3C4: "t", 0x3C7: "x", 0x3B7: "n", 0x3BC: "u", 0x3C9: "w", 0x3B5: "e",
    0xF8: "o", 0x142: "l", 0x111: "d",
}  # fmt: skip
# OVERRIDES (explicit, one entry, DOES override the data): the UTS #39 15.1.0 data reads the Cyrillic small palochka U+04CF as ``i``
# (the 18.0.0 data read it as ``l``, and so did the table before fix4). The attack that matters is the stroke for an ``l`` (the "apple"
# and "paypal" spoofs, pinned by tests/fixtures/textnorm_vectors.json and corpus row r101), so the table keeps reading it as ``l``. The
# same entry is in the P1b branch. Remove it only together with those rows.
OVERRIDES: dict[int, str] = {0x4CF: "l"}
DROPPED = frozenset(
    {"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs"}
)  # the dropped categories (not Cn: an unassigned source is kept, so the output does not depend on the interpreter's Unicode version)
DEFAULT_INPUT = Path(__file__).resolve().parent / "data" / "confusables.txt"
OUT = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk" / "guard" / "_confusables.py"
_DIGIT_WORDS = {
    "ZERO": "0", "ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4",
    "FIVE": "5", "SIX": "6", "SEVEN": "7", "EIGHT": "8", "NINE": "9", "TEN": "10",
}  # fmt: skip
# The Unicode-name rules (see "NAME RULES" in the module docstring): each is a full match on the character name; the second item says
# how the letter or digit is written (``"upper"``, ``"lower"``, ``"digit"``, or ``"case"``: the capital or small word of the name).
_NAME_RULES: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), how)
    for pattern, how in (
        (r"LATIN (?:LETTER )?SMALL CAPITAL (?:LETTER )?([A-Z])(?: WITH .+)?", "upper"),
        (r"(?:CROSSED )?NEGATIVE (?:CIRCLED|SQUARED) LATIN CAPITAL LETTER ([A-Z])", "upper"),
        (r"SQUARED LATIN SMALL LETTER ([A-Z])", "lower"),
        (r"REGIONAL INDICATOR SYMBOL LETTER ([A-Z])", "upper"),
        (r"LATIN (?:CAPITAL|SMALL) LETTER ([A-Z]) WITH .+", "case"),
        (
            r"(?:DINGBAT )?(?:NEGATIVE |DOUBLE )?CIRCLED (?:SANS-SERIF )?(?:DIGIT|NUMBER) ("
            + "|".join(_DIGIT_WORDS)
            + ")",
            "digit",
        ),
    )
)


def name_rule_value(name: str) -> str | None:
    """The ASCII letter or digit(s) the character NAME says (the first rule that matches wins), or None."""
    for pattern, how in _NAME_RULES:
        m = pattern.fullmatch(name)
        if not m:
            continue
        if how == "digit":
            return _DIGIT_WORDS[m[1]]
        if how == "case":
            return m[1].lower() if name.startswith("LATIN SMALL ") else m[1]
        return m[1].lower() if how == "lower" else m[1]
    return None


_LINE = re.compile(r"^([0-9A-F]{4,6})\s*;\s*([0-9A-F ]+?)\s*;\s*MA\b")
_HEADER = (
    '"""GENERATED by tools/gen_confusables.py from Unicode UTS #39 confusables.txt (MA table), version {ver}, dated {date},\n'
    "sha256 {sha}; character names from Python unicodedata {uni}. Do not edit; change the generator and regenerate.\n\n"
    "Copyright \u00a9 1991-2026 Unicode, Inc. Used under the Unicode License v3 (https://www.unicode.org/terms_of_use.html). The data\n"
    "file itself carries the line \u201c# \u00a9 2023 Unicode\u00ae, Inc.\u201d. Unicode is a registered trademark of Unicode, Inc.\n"
    "THIS NOTICE MUST NOT BE REMOVED OR SHORTENED when this file is copied.\n"
    '"""\n\n'
    'DATA_SHA256 = "{sha}"\n'
    'DATA_VERSION = "{ver}"\n'
    'DATA_DATE = "{date}"\n'
    'DATA_UNICODEDATA = "{uni}"\n'
    "ENTRIES = {n}\n"
    'TABLE_DIGEST = "{digest}"\n'
    "MAX_VALUE_LEN = {maxlen}\n\n"
    "# code point -> ASCII letters/digits\n"
    "TABLE: dict[int, str] = {{\n"
)


def table_digest(table: dict[int, str]) -> str:
    """SHA-256 (64 hex) of the table as lines ``f"{cp:06X}:{value}\\n"`` in ascending code point order, UTF-8. ``textnorm.FOLD_VERSION``
    carries its first 12 characters; ``tests/test_textnorm.py`` serialises the table the same way on its own and compares."""
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def pinned_unidata() -> str:
    """The interpreter pin of the fold, ``defaults.TEXTNORM_PINNED_UNIDATA`` (read from the source tree next to this tool)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        from hadavin_sdk import (
            defaults,  # the tool runs from a checkout; the import is local on purpose
        )

        return defaults.TEXTNORM_PINNED_UNIDATA
    finally:
        sys.path.pop(0)


def check_input(raw: bytes) -> str | None:
    """None when ``raw`` is the pinned data file; otherwise the reason it is refused. The checks, in this order: the ``# Version:`` line
    is the interpreter pin (``defaults.TEXTNORM_PINNED_UNIDATA``) and the generator's own pin (any other Unicode version is refused);
    the ``# Date:`` line is the pinned date; the SHA-256 is the pinned one."""
    text = raw.decode("utf-8", "replace")
    ver = re.search(r"^# Version: (\S+)", text, re.MULTILINE)
    version = ver[1] if ver else "?"
    unidata = pinned_unidata()
    if version != unidata or PINNED_VERSION != unidata:
        return (
            f"refused: the data file has Unicode version {version}, the generator pins {PINNED_VERSION}, "
            f"and the interpreter pin is {unidata}: they must all be the same Unicode version"
        )
    date = re.search(r"^# Date: (.+)$", text, re.MULTILINE)
    if (date[1].strip() if date else "?") != PINNED_DATE:
        return f"refused: the data file is dated {date[1].strip() if date else '?'}, the pin is {PINNED_DATE}"
    sha = hashlib.sha256(raw).hexdigest()
    if sha != PINNED_SHA256:
        return f"refused: sha256 {sha} is not the pinned {PINNED_SHA256}"
    return None


def _follow_case_partner(ch: str, value: str | None, listed: dict[int, str]) -> str | None:
    """A name rule never splits a capital from its small letter: when the data or the supplement already reads the other-case form of ``ch``
    as another letter (UTS #39 reads the small v with hook U+028B as ``u``), ``ch`` is read as that letter in its own case."""
    if value is None:
        return None
    for partner in {ch.lower(), ch.upper()} - {ch}:
        read = listed.get(ord(partner)) if len(partner) == 1 else None
        if read and read.casefold() != value.casefold():
            return read.upper() if ch.isupper() else read.lower()
    return value


def build(text: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for line in text.splitlines():
        m = _LINE.match(line)
        if not m:
            continue
        src = int(m[1], 16)
        dst = "".join(chr(int(h, 16)) for h in m[2].split())
        ch = chr(src)
        if src < 0x80 or not re.fullmatch(r"[A-Za-z0-9]+", dst):
            continue
        if unicodedata.normalize("NFKC", ch) != ch or unicodedata.category(ch) in DROPPED:
            continue
        if dst == "l" and unicodedata.category(ch) == "Lu":
            dst = "I"
        out[src] = dst
    sup = {
        cp: v for cp, v in SUPPLEMENT.items() if unicodedata.normalize("NFKC", chr(cp)) == chr(cp)
    }  # a key the fold can reach
    out = {
        **sup,
        **out,
    }  # the data wins over the supplement; both are in ``out`` BEFORE the name rules, so no name rule overrides either
    listed = dict(out)  # what the data and the supplement say, before any name rule
    for cp in range(0x80, 0x20000):
        ch = chr(cp)
        value = name_rule_value(unicodedata.name(ch, ""))
        value = _follow_case_partner(ch, value, listed)
        if (
            value
            and unicodedata.normalize("NFKD", ch) == ch
            and unicodedata.normalize("NFKC", ch) == ch
            and unicodedata.category(ch) not in DROPPED
        ):
            out.setdefault(cp, value)
    ovr = {
        cp: v for cp, v in OVERRIDES.items() if unicodedata.normalize("NFKC", chr(cp)) == chr(cp)
    }
    return {**out, **ovr}


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print(__doc__)
        return 2
    raw = Path(argv[1] if len(argv) == 2 else DEFAULT_INPUT).read_bytes()
    problem = check_input(raw)
    if problem:
        print(problem)
        return 1
    text = raw.decode("utf-8")
    table = build(text)
    body = "".join(f'    0x{cp:04X}: "{table[cp]}",\n' for cp in sorted(table))
    OUT.write_text(
        _HEADER.format(
            ver=PINNED_VERSION,
            uni=unicodedata.unidata_version,
            date=PINNED_DATE,
            sha=hashlib.sha256(raw).hexdigest(),
            n=len(table),
            digest=table_digest(table),
            maxlen=max(len(v) for v in table.values()),
        )
        + body
        + "}\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT} with {len(table)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
