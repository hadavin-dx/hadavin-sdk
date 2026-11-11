"""Generate ``src/hadavin_sdk/guard/_confusables.py`` from the Unicode UTS #39 ``confusables.txt`` (the MA table) and
``src/hadavin_sdk/guard/_scripts.py`` from the Unicode ``Scripts.txt`` (the script of every code point), both of the SAME Unicode version
as the interpreter pin ``defaults.TEXTNORM_PINNED_UNIDATA`` (15.1.0).

Run (stdlib only; offline: the data files are vendored in ``tools/data/``, Unicode License v3, the notice is in each file and in the
generated headers; unicode.org serves only the "latest" URL, there is no versioned one, hence the copies and the pins):

    python tools/gen_confusables.py                      # reads tools/data/confusables.txt and tools/data/Scripts.txt
    python tools/gen_confusables.py other.txt            # the look-alike data from another file: refused unless it has the pinned
                                                         # version and sha256 (the scripts file is always the vendored one)

WHERE THE 15.1.0 FILES CAME FROM (read on 2026-11-06): ``confusables.txt`` is the file at
https://www.unicode.org/Public/security/15.1.0/confusables.txt, fetched by the project lead on 2026-11-06 (718,291 bytes); the same
bytes (same sha256) are in the Unicode Consortium's ``unicodetools`` repository (``data/security/15.1.0/``) and in the ICU source tree at
the tags ``release-74-1``, ``release-74-2`` and ``release-75-1``. ``Scripts.txt`` is ``unicodetools/data/ucd/15.1.0/Scripts.txt``
(not compared with a download from unicode.org: UNVERIFIED against that site; its header names Scripts-15.1.0.txt, dated 2023-07-28).

Why the version is checked: a look-alike table of another Unicode version than the interpreter's data maps code points the interpreter
does not know (or misses ones it does). The generator refuses a data file whose ``# Version:`` line is not the pin, BEFORE it looks at
the hash, so the message names the mismatch; a changed pin is a reviewed change of ``defaults.TEXTNORM_PINNED_UNIDATA``, the two
``PINNED_*`` blocks below and the generated files in one commit.

Two constants are written beside the table: ``TABLE_DIGEST`` (the SHA-256 of the table, see ``table_digest``) and ``MAX_VALUE_LEN`` (the
longest table value, which the size rule of ``guard/textnorm.py`` reads). ``_scripts.py`` carries ``SCRIPTS_DIGEST`` the same way (see
``scripts_digest``).

Python dependency: the small-capital rule reads character NAMES from the running interpreter's ``unicodedata``; the checked-in output was
generated with Python 3.13.3 / Unicode 15.1.0 (``DATA_UNICODEDATA`` in the generated file). Another interpreter may add entries; the
checked-in file is the artifact. REGENERATION LIMIT: regenerate only on the pinned Unicode version (``defaults.TEXTNORM_PINNED_UNIDATA``,
15.1.0); another interpreter can add or drop small-capital entries (and the test that compares the output with the checked-in file runs
only on the versions where that comparison was checked: 15.0.0 and 15.1.0, which give the identical table). The ``tbl=`` digest of
``FOLD_VERSION`` is the only tripwire for a table that changed through the interpreter.

The input must have the pinned version and sha256 below (UTS #39 15.1.0, dated 2023-08-11, 17:46:40 GMT; Scripts 15.1.0, dated
2023-07-28, 16:01:07 GMT); another file is refused, so a changed table is a reviewed change: update the pin and the generated file in the
same commit. Licence: Unicode License v3 (data files may be copied and used with the copyright notice, which the generated file carries).

Selection rules (all explicit, nothing hand-curated):
  * entries of the MA ("mixed-script, any-case") table only;
  * the SOURCE is one non-ASCII code point that survives the fold's earlier steps (NFKC leaves it unchanged, its category is not
    dropped, EXCEPT an unassigned one (Cn): the fold applies the table to a Cn source before the drop, so the entry is kept; on the pinned
    interpreter the data and the interpreter agree and there is none, on an older interpreter the code points added in 15.1.0 are Cn);
  * the TARGET is entirely ASCII letters and digits (punctuation prototypes are left out on purpose: the fold keeps separators for
    the amount and date patterns);
  * SUPPLEMENT (below, explicit, 16 entries, never overrides the data): letters that read as a Latin letter but that UTS #39 does
    not list as MA (Cyrillic ka em te en ve ze, Greek kappa tau chi eta mu omega epsilon, Latin o/l/d with stroke). They
    were added by a design review and are pinned by tests/fixtures/textnorm_vectors.json;
  * NAME RULE: a code point named ``LATIN LETTER SMALL CAPITAL X`` or ``LATIN SMALL CAPITAL X`` (X one letter) maps to the capital X.
    UTS #39 lists only a few small capitals; the rest read as the capital letter, and the rule is by Unicode name, not by hand. The
    names come from the running interpreter's ``unicodedata`` (recorded in the generated header); data and supplement win over it;
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
PINNED_SCRIPTS_VERSION = "15.1.0"
PINNED_SCRIPTS_DATE = "2023-07-28, 16:01:07 GMT"
PINNED_SCRIPTS_SHA256 = "0eacb65169ae6eb1d399cd70826b3da15fff19f6f586eecf819b70c83b1d9b32"
SUPPLEMENT: dict[int, str] = {
    0x43A: "k", 0x43C: "m", 0x442: "t", 0x43D: "h", 0x432: "b", 0x437: "3",
    0x3BA: "k", 0x3C4: "t", 0x3C7: "x", 0x3B7: "n", 0x3BC: "u", 0x3C9: "w", 0x3B5: "e",
    0xF8: "o", 0x142: "l", 0x111: "d",
}  # fmt: skip
# OVERRIDES (explicit, one entry, DOES override the data): the UTS #39 15.1.0 data reads the Cyrillic small palochka U+04CF as ``i``
# (the 18.0.0 data read it as ``l``). The attack that matters is the stroke for an ``l`` (the "apple" and "paypal" spoofs, pinned by
# tests/fixtures/textnorm_vectors.json and corpus row r101), so ``identity_key`` keeps reading it as ``l``; ``scan_keyset`` joins ``l`` and
# ``i`` in one class, so the ``i`` reading is found there too. Remove the entry only with those rows.
OVERRIDES: dict[int, str] = {0x4CF: "l"}
DROPPED = frozenset(
    {"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs"}
)  # the dropped categories except Cn (see the selection rules)
NEUTRAL_SCRIPTS = frozenset(
    {"Common", "Inherited"}
)  # not written to _scripts.py: a code point with no entry is script-neutral
DEFAULT_INPUT = Path(__file__).resolve().parent / "data" / "confusables.txt"
DEFAULT_SCRIPTS_INPUT = Path(__file__).resolve().parent / "data" / "Scripts.txt"
OUT = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk" / "guard" / "_confusables.py"
OUT_SCRIPTS = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk" / "guard" / "_scripts.py"
_SMALL_CAP = re.compile(r"LATIN (?:LETTER )?SMALL CAPITAL ([A-Z])")
_LINE = re.compile(r"^([0-9A-F]{4,6})\s*;\s*([0-9A-F ]+?)\s*;\s*MA\b")
_SCRIPT_LINE = re.compile(r"^([0-9A-F]{4,6})(?:\.\.([0-9A-F]{4,6}))?\s*;\s*([A-Za-z_]+)\s*#")
_HEADER = (
    '"""GENERATED by tools/gen_confusables.py from Unicode UTS #39 confusables.txt (MA table), version {ver}, dated {date},\n'
    "sha256 {sha}; small-capital names from Python unicodedata {uni}. Do not edit; change the generator and regenerate.\n\n"
    "(c) 1991-2026 Unicode, Inc. Used under the Unicode License v3 (https://www.unicode.org/terms_of_use.html). The data file itself\n"
    "carries the notice (c) 2023 Unicode, Inc. Unicode is a registered trademark of Unicode, Inc.\n"
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
_SCRIPTS_HEADER = (
    '"""GENERATED by tools/gen_confusables.py from Unicode Scripts.txt, version {ver}, dated {date}, sha256 {sha}.\n'
    "Do not edit; change the generator and regenerate. The script of every code point that is not Common or Inherited (those two, and\n"
    "every code point the file does not list, are script-neutral and have no entry).\n\n"
    "(c) 1991-2026 Unicode, Inc. Used under the Unicode License v3 (https://www.unicode.org/terms_of_use.html). The data file itself\n"
    "carries the notice (c) 2023 Unicode, Inc. Unicode is a registered trademark of Unicode, Inc.\n"
    '"""\n\n'
    'DATA_SHA256 = "{sha}"\n'
    'DATA_VERSION = "{ver}"\n'
    'DATA_DATE = "{date}"\n'
    "ENTRIES = {n}\n"
    'SCRIPTS_DIGEST = "{digest}"\n\n'
    "# the scripts in the order of the first column of RANGES' third field\n"
    "SCRIPT_NAMES: tuple[str, ...] = (\n{names})\n\n"
    "# (first code point, last code point, index into SCRIPT_NAMES), sorted, not overlapping\n"
    "RANGES: tuple[tuple[int, int, int], ...] = (\n"
)


def table_digest(table: dict[int, str]) -> str:
    """SHA-256 (64 hex) of the table as lines ``f"{cp:06X}:{value}\\n"`` in ascending code point order, UTF-8. ``textnorm.FOLD_VERSION``
    carries its first 12 characters; ``tests/test_textnorm.py`` serialises the table the same way on its own and compares."""
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def scripts_digest(ranges: list[tuple[int, int, str]]) -> str:
    """SHA-256 (64 hex) of the script ranges as lines ``f"{first:06X}-{last:06X}:{script}\\n"`` in ascending order, UTF-8."""
    lines = "".join(f"{a:06X}-{b:06X}:{name}\n" for a, b, name in sorted(ranges))
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


def check_input(
    raw: bytes, *, pinned_version: str, pinned_date: str, pinned_sha256: str, label: str
) -> str | None:
    """None when ``raw`` is the pinned data file; otherwise the reason it is refused. The checks, in this order: the ``# Version:`` line
    is the interpreter pin (``defaults.TEXTNORM_PINNED_UNIDATA``) and the generator's own pin; the ``# Date:`` line is the pinned date;
    the SHA-256 is the pinned one."""
    text = raw.decode("utf-8", "replace")
    ver = re.search(r"^# (?:Version: |Scripts-)(\S+?)(?:\.txt)?$", text, re.MULTILINE)
    version = ver[1] if ver else "?"
    unidata = pinned_unidata()
    if version != unidata or pinned_version != unidata:
        return (
            f"refused: {label} has version {version}, the generator pins {pinned_version}, "
            f"and the interpreter pin is {unidata}: they must all be the same Unicode version"
        )
    date = re.search(r"^# Date: (.+)$", text, re.MULTILINE)
    if (date[1].strip() if date else "?") != pinned_date:
        return f"refused: {label} is dated {date[1].strip() if date else '?'}, the pin is {pinned_date}"
    sha = hashlib.sha256(raw).hexdigest()
    if sha != pinned_sha256:
        return f"refused: sha256 {sha} is not the pinned {pinned_sha256}"
    return None


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
    for cp in range(0x80, 0x20000):
        m = _SMALL_CAP.fullmatch(unicodedata.name(chr(cp), ""))
        ch = chr(cp)
        if (
            m
            and unicodedata.normalize("NFKC", ch) == ch
            and unicodedata.category(ch) not in DROPPED
        ):
            out.setdefault(cp, m[1])
    sup = {
        cp: v for cp, v in SUPPLEMENT.items() if unicodedata.normalize("NFKC", chr(cp)) == chr(cp)
    }  # a key the fold can reach
    ovr = {
        cp: v for cp, v in OVERRIDES.items() if unicodedata.normalize("NFKC", chr(cp)) == chr(cp)
    }
    return {**sup, **out, **ovr}


def build_scripts(text: str) -> list[tuple[int, int, str]]:
    """The ranges of Scripts.txt that name a script other than Common and Inherited, sorted by first code point. Adjacent ranges of one
    script are merged, so the output does not depend on how the data file splits its lines."""
    ranges: list[tuple[int, int, str]] = []
    for line in text.splitlines():
        m = _SCRIPT_LINE.match(line)
        if not m or m[3] in NEUTRAL_SCRIPTS:
            continue
        ranges.append((int(m[1], 16), int(m[2] or m[1], 16), m[3]))
    ranges.sort()
    merged: list[tuple[int, int, str]] = []
    for a, b, name in ranges:
        if merged and merged[-1][2] == name and merged[-1][1] + 1 == a:
            merged[-1] = (merged[-1][0], b, name)
        else:
            merged.append((a, b, name))
    return merged


def _header_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    return m[1].strip() if m else "?"


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    if len(argv) > 2:
        print(__doc__)
        return 2
    if unicodedata.unidata_version != PINNED_VERSION:
        print(
            f"refused: this interpreter has Unicode data {unicodedata.unidata_version}, the pin is {PINNED_VERSION}; "
            "regenerate only on an interpreter with the pinned data (the small-capital rule reads this interpreter's character names)"
        )
        return 1
    raw = Path(argv[1] if len(argv) == 2 else DEFAULT_INPUT).read_bytes()
    problem = check_input(
        raw,
        pinned_version=PINNED_VERSION,
        pinned_date=PINNED_DATE,
        pinned_sha256=PINNED_SHA256,
        label="the look-alike data file",
    )
    if problem:
        print(problem)
        return 1
    raw_scripts = DEFAULT_SCRIPTS_INPUT.read_bytes()
    problem = check_input(
        raw_scripts,
        pinned_version=PINNED_SCRIPTS_VERSION,
        pinned_date=PINNED_SCRIPTS_DATE,
        pinned_sha256=PINNED_SCRIPTS_SHA256,
        label="the scripts data file",
    )
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
    ranges = build_scripts(raw_scripts.decode("utf-8"))
    names = sorted({name for _, _, name in ranges})
    index = {name: i for i, name in enumerate(names)}
    OUT_SCRIPTS.write_text(
        _SCRIPTS_HEADER.format(
            ver=PINNED_SCRIPTS_VERSION,
            date=PINNED_SCRIPTS_DATE,
            sha=hashlib.sha256(raw_scripts).hexdigest(),
            n=len(ranges),
            digest=scripts_digest(ranges),
            names="".join(f'    "{n}",\n' for n in names),
        )
        + "".join(f"    (0x{a:04X}, 0x{b:04X}, {index[name]}),\n" for a, b, name in ranges)
        + ")\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT_SCRIPTS} with {len(ranges)} ranges of {len(names)} scripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
