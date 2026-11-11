"""PR H, WP1: unit tests of `hadavin_sdk.guard.hidden` against an independent oracle (`tests/hidden_oracle.py`, written
from the ticket's state table and sharing no code with the module), the exact character classes, the ignorable table and
its data file. There is no old behaviour to compare with, so this file is not run on main."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import re
import unicodedata
from pathlib import Path

import pytest

from hadavin_sdk.guard import hidden
from tests import hidden_oracle as oracle
from tests.fixtures.timing import is_superlinear
from tests.test_prh_spans import Gen

ROOT = Path(__file__).resolve().parents[1]
RANGE_FILE = ROOT / "tests" / "fixtures" / "default_ignorable_perl5382_unicode1500.txt"
RANGE_FILE_SHA256 = "b14f5d758ff48a8c5e5c92e45d6aa48856db50d732103077435fa4a40aa457f6"
ESC, BEL = "\x1b", "\x07"


def _file_points() -> frozenset[int]:
    return oracle.read_range_file(str(RANGE_FILE))


IGN = _file_points()


def oracle_readings(text: str) -> tuple[str, str]:
    return oracle.readings(text, IGN)


# ---- the reader against the oracle ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "text", "joined"), oracle.GRAMMAR_ROWS, ids=[r[0] for r in oracle.GRAMMAR_ROWS]
)
def test_grammar_row(name, text, joined):
    """One row of the state table: the joined reading is the written one, and the same text at the start, in the
    middle and at the end of a longer text reads as the oracle reads it."""
    assert hidden.strip(text)[0] == joined, name
    assert oracle_readings(text)[0] == joined, name
    for wrapped in (
        text + " tail",
        "head " + text,
        "head " + text + " tail",
        "head\n" + text + "\ntail",
    ):
        assert hidden.strip(wrapped) == oracle_readings(wrapped), (name, wrapped)


@pytest.mark.parametrize(
    ("text", "joined", "spaced"), oracle.GLUE_TABLE, ids=[r[0] for r in oracle.GLUE_TABLE]
)
def test_glue_row(text, joined, spaced):
    assert hidden.strip(text) == (joined, spaced)
    assert oracle_readings(text) == (joined, spaced)


def test_glue_is_the_same_object_when_equal():
    j, s = hidden.strip("ab" + BEL + "-cd")
    assert j == s
    assert j is s
    plain = "no hidden item here\tat all\n"
    j, s = hidden.strip(plain)
    assert j is plain
    assert s is plain


OPENERS = [
    ESC + "[",
    ESC + "]",
    ESC + "P",
    ESC + "X",
    ESC + "^",
    ESC + "_",
    ESC + "(",
    ESC + "#",
    ESC,
    "\x9b",
    "\x9d",
    "\x90",
    "\x98",
    "\x9e",
    "\x9f",
]
TERMINATORS = [
    "",
    "m",
    BEL,
    ESC + "\\",
    "\x9c",
    "\x18",
    "\x1a",
    "\n",
    "\r",
    ESC + "[0m",
    "\u00e9",
    "B",
    "8",
]


def test_nested_and_aborted_openers_equal_the_oracle():
    cases = 0
    for a in OPENERS:
        for b in OPENERS:
            for t in TERMINATORS:
                for glue in ("", "ab", " "):
                    text = "x" + a + glue + b + t + "y"
                    assert hidden.strip(text) == oracle_readings(text), ascii(text)
                    assert hidden.strip_sequences(text) == oracle.readings(text, IGN, True)[1], (
                        ascii(text)
                    )
                    cases += 1
    assert cases == len(OPENERS) ** 2 * len(TERMINATORS) * 3


ALPHABET = (
    sorted(oracle.REMOVED | oracle.SPACE_LIKE)
    + list("[]P^_X\\(#7Mc0;m q?ab_-\u00e9")
    + [ESC] * 6
    + ["\u200b", "\u034f", "\u3164", "\n", "\t"]
)


def _random_texts(count: int):
    g = Gen(20261111)
    for _ in range(count):
        yield "".join(ALPHABET[g.below(len(ALPHABET))] for _ in range(g.between(0, 24)))


def test_random_equals_oracle():
    n = 0
    for text in _random_texts(20_000):
        assert hidden.strip(text) == oracle_readings(text), ascii(text)
        n += 1
    assert n == 20_000


def test_strip_sequences_equals_oracle():
    for text in _random_texts(20_000):
        assert hidden.strip_sequences(text) == oracle.readings(text, IGN, True)[1], ascii(text)


def test_idempotent():
    for text in _random_texts(5_000):
        joined, spaced = hidden.strip(text)
        assert hidden.strip(joined)[0] == joined, ascii(text)
        assert hidden.strip(spaced)[1] == spaced, ascii(text)
        assert not any(c in hidden.REMOVED_CHARS or c in hidden.SPACE_LIKE for c in joined + spaced)
        once = hidden.strip_sequences(text)
        assert hidden.strip_sequences(once) == once, ascii(text)


def test_strip_sequences_scope():
    """Only items that start with ESC or a C1 opener; every other control character stays as written."""
    assert hidden.strip_sequences("a" + BEL + "b\x00c\x85d\x9ce") == "a" + BEL + "b\x00c\x85d\x9ce"
    assert hidden.strip_sequences("a" + ESC + "[0mb") == "a b"
    assert hidden.strip_sequences("a" + ESC) == "a"  # a lone ESC is removed
    assert hidden.strip_sequences("a\x9b") == "a"  # a lone C1 CSI opener too
    assert hidden.strip_sequences("a" + ESC + "[0m" + BEL + ESC + "[1mb") == "a" + BEL + "b"


def test_unterminated_opener_repeated_is_linear():
    for unit in (ESC + "]ab", ESC + "[ab", ESC + "(ab", "\x9dab", ESC + "Pab"):

        def measure(text: str) -> float:
            import time

            start = time.process_time()
            hidden.strip(text)
            return time.process_time() - start

        assert not is_superlinear(measure, unit, 50_000, 200_000), ascii(unit)


# ---- the classes ---------------------------------------------------------------------------------------------------


def _cp(*spans: tuple[int, int]) -> frozenset[str]:
    out: set[str] = set()
    for lo, hi in spans:
        out.update(chr(c) for c in range(lo, hi + 1))
    return frozenset(out)


def test_classes_exact():
    """Section 3, typed out again as code-point lists: 55 removed characters, 9 space-like ones."""
    removed = _cp(
        (0x0000, 0x0008), (0x000E, 0x001B), (0x007F, 0x007F), (0x0080, 0x0084), (0x0086, 0x009F)
    )
    space_like = _cp((0x000B, 0x000C), (0x001C, 0x001F), (0x0085, 0x0085), (0x2028, 0x2029))
    assert len(removed) == 55
    assert len(space_like) == 9
    assert hidden.REMOVED_CHARS == removed
    assert hidden.SPACE_LIKE == space_like
    assert hidden.REMOVED_CHARS == oracle.REMOVED
    assert hidden.SPACE_LIKE == oracle.SPACE_LIKE
    assert not hidden.REMOVED_CHARS & hidden.SPACE_LIKE
    for kept in (
        "\t",
        "\n",
        "\r",
        " ",
        "\u00a0",
        "\u3000",
    ):  # tab, line ends and the other spaces are untouched
        assert kept not in hidden.REMOVED_CHARS
        assert kept not in hidden.SPACE_LIKE
        assert hidden.strip("a" + kept + "b") == ("a" + kept + "b",) * 2
    assert hidden.strip("a\x0bb")[0] == "a b"
    assert hidden.strip("a\u2028b")[0] == "a b"


# ---- the ignorable table and its data file -------------------------------------------------------------------------


def _all_cf_above_ascii() -> set[int]:
    return {c for c in range(0x80, 0x110000) if unicodedata.category(chr(c)) == "Cf"}


def test_ignorable_equals_file_and_rule():
    """The pinned file, the rule written out in the ticket (over `unicodedata`) and the module's own ranges agree over
    all 1,114,112 code points. On a Python whose Unicode version is not one of the two the rule was checked on, the
    rule must still derive every pinned code point (and the new ones are printed); with
    HADAVIN_REQUIRE_PINNED_UNIDATA=1 (CI sets it) that case is a failure."""
    in_module = {c for lo, hi in hidden.IGNORABLE_RANGES for c in range(lo, hi + 1)}
    assert in_module == set(IGN)
    assert len(IGN) == 4174
    derived = oracle.derive_ignorable()
    if unicodedata.unidata_version in ("15.0.0", "15.1.0"):
        assert derived == IGN
    else:
        print("unidata", unicodedata.unidata_version, "new code points:", sorted(derived - IGN))
        assert IGN <= derived
        assert os.environ.get("HADAVIN_REQUIRE_PINNED_UNIDATA") != "1", (
            "the pinned Unicode data (15.0.0 / 15.1.0) is not what this Python carries"
        )
    # the character class is the file plus every category Cf character above U+007F (what main already dropped)
    everything = "".join(map(chr, range(0x110000)))
    by_class = {ord(m) for m in hidden.IGNORABLE_RE.findall(everything)}
    assert by_class == set(IGN) | _all_cf_above_ascii()
    assert all(
        hidden.is_ignorable(chr(c)) for c in (0xAD, 0x200B, 0x200C, 0xFE0F, 0x34F, 0x3164, 0xE0001)
    )
    assert not any(
        hidden.is_ignorable(c) for c in ("a", " ", "\t", "\x1b", "\u0301", "\u00e9", "_")
    )
    assert hidden.UNICODE_DATA_VERSION == "15.0.0"


def test_range_file_hash():
    assert hashlib.sha256(RANGE_FILE.read_bytes()).hexdigest() == RANGE_FILE_SHA256
    listed = (ROOT / "tests" / "fixtures" / "reference_material_sha256.txt").read_text(
        encoding="utf-8"
    )
    assert RANGE_FILE_SHA256 not in listed  # that file is a deny-list of course material


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_default_ignorable", ROOT / "tools" / "gen_default_ignorable.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_prints_the_literal_and_the_file():
    gen = _load_generator()
    literal = gen.format_literal(gen.parse_range_file(RANGE_FILE.read_text(encoding="ascii")))
    expected = "IGNORABLE_RANGES: tuple[tuple[int, int], ...] = (\n" + "".join(
        f"    (0x{a:04X}, 0x{b:04X}),\n" for a, b in hidden.IGNORABLE_RANGES
    )
    assert literal == expected + ")\n"
    assert literal in (ROOT / "src" / "hadavin_sdk" / "guard" / "hidden.py").read_text(
        encoding="utf-8"
    )
    rebuilt = gen.format_ranges(gen.merge(sorted(IGN)))
    assert rebuilt.encode("ascii") == RANGE_FILE.read_bytes()


# ---- independence --------------------------------------------------------------------------------------------------


def test_oracle_imports_nothing():
    source = (ROOT / "tests" / "hidden_oracle.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import|from)\s+hadavin_sdk", source, re.MULTILINE)
    assert not re.search(r"^\s*import\s+re\b", source, re.MULTILINE)
    assert source.isascii()
    assert not any(
        unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") and c != "\n" for c in source
    )


def test_hidden_module_imports_nothing_from_the_package():
    tree = ast.parse(
        (ROOT / "src" / "hadavin_sdk" / "guard" / "hidden.py").read_text(encoding="utf-8")
    )
    modules = {
        n.module if isinstance(n, ast.ImportFrom) else a.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for a in (n.names if isinstance(n, ast.Import) else [None])
    }
    assert modules == {"__future__", "re", "unicodedata"}


def test_gate_set_holds_removed_and_space_like():
    """The approval gate keeps its own set of control characters (no edit in PR H). It holds every removed and every
    space-like character except U+2028 and U+2029, which it does not hold today (reported, not changed)."""
    from hadavin_sdk.approvals import gate

    missing = (hidden.REMOVED_CHARS | hidden.SPACE_LIKE) - gate._CONTROL_CHARS
    assert missing == {"\u2028", "\u2029"}


def test_strip_consuming():
    """The consuming reading (`hidden.strip_consuming`) takes the final byte of an nF, Fp, Fe or Fs sequence, a letter or
    digit too; the ordinary reading keeps it (D-029). `tput sgr0` writes ESC ( B."""
    esc = "\x1b"
    key = "AKIA" + "IOSFODNN7EXAMPLE"
    cut = key[:4] + esc + "(B" + esc + "[m" + key[4:]
    assert hidden.strip_consuming(cut)[0] == key
    assert hidden.strip(cut)[0] == key[:4] + "(B" + key[4:]
    assert hidden.strip_consuming("a" + esc + "e" + "b")[0] == "ab"
    assert hidden.strip("a" + esc + "e" + "b")[0] == "aeb"
    assert hidden.strip_consuming("plain text") == ("plain text", "plain text")
