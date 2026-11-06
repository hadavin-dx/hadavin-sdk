"""The look-alike table and its generator (``tools/gen_confusables.py``): the checked-in table is the generator's output for the pinned data.

Properties only, so a test holds on every interpreter. The two tests that regenerate the table read the small-capital NAMES of this
interpreter: they run on Unicode 15.0.0 (Python 3.12) and 15.1.0 (Python 3.13), where the output was compared with the checked-in table
and is identical, and skip (reason printed by ``-rs``) on any other version. The assertions a mutant must
trip carry a message; ``tests/textnorm_mutants.py`` names a fragment of it.
"""

import hashlib
import importlib.util
import re
import unicodedata
from pathlib import Path

import pytest

from hadavin_sdk.guard import _confusables, textnorm
from hadavin_sdk.guard.textnorm import fold

ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "tools" / "gen_confusables.py"


# The Unicode versions on which the generator was run in this package and gave the checked-in table byte for byte (3.13: 15.1.0, the
# pin; 3.12: 15.0.0, the small-capital names are the same). Another version is not asserted: it is skipped, loudly (``-rs``).
CHECKED_VERSIONS = frozenset({"15.0.0", "15.1.0"})


def _skip_unless_checked_version():
    if unicodedata.unidata_version not in CHECKED_VERSIONS:
        pytest.skip(
            f"the small-capital rule reads this interpreter's character names and Unicode {unicodedata.unidata_version} was never "
            f"compared with the checked-in table (checked: {sorted(CHECKED_VERSIONS)}); regenerate only on Unicode "
            + _confusables.DATA_UNICODEDATA
        )


def _load(name):
    spec = importlib.util.spec_from_file_location(name, GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_table_is_generated_from_the_unicode_data_and_every_value_is_ascii():
    src = GEN_PATH.read_text(encoding="utf-8")
    assert _confusables.DATA_SHA256 in src, (
        "the generator pins another sha256 than the generated file"
    )
    # whole-script and rare look-alikes the first, curated table missed
    named = {0x13AA: "A", 0x13A0: "D", 0x10E7: "y", 0x5D5: "l", 0xA4D0: "B", 0x2C82: "B", 0x269: "i", 0x1C0: "l", 0x237: "j", 0x192: "f",
             0x1D00: "A", 0x299: "B", 0x1D05: "D", 0x1D07: "E", 0xA730: "F", 0x262: "G", 0x29C: "H", 0x1D0A: "J", 0x1D0B: "K", 0x29F: "L",
             0x1D0D: "M", 0x274: "N", 0x1D18: "P", 0x280: "R", 0x1D1B: "T"}  # fmt: skip
    for cp, latin in named.items():
        assert fold(chr(cp)) == latin, f"named look-alike U+{cp:04X} is not folded to {latin}"
    assert (
        fold("".join(map(chr, (0x13A0, 0x13AA, 0x13A2)))) == "DAT"
    )  # a name written entirely in Cherokee
    assert (
        fold(chr(0x406)) == "I" and fold(chr(0x399)) == "I"
    )  # upper-case sources whose prototype is l read as I
    assert _confusables.ENTRIES == len(_confusables.TABLE), "ENTRIES is not the size of the table"
    assert len(_confusables.TABLE) >= 600
    for cp, v in _confusables.TABLE.items():
        assert v.isascii() and re.fullmatch("[A-Za-z0-9]+", v), (hex(cp), v)
        assert cp >= 0x80 and unicodedata.normalize("NFKC", chr(cp)) == chr(cp), hex(
            cp
        )  # only code points the fold can see
    assert dict(textnorm._TABLE) == _confusables.TABLE
    assert len(textnorm._LOOKALIKES) == len(_confusables.TABLE)


def test_no_table_source_is_in_a_dropped_category_or_unassigned():
    """The table holds only sources ASSIGNED in Unicode 15.1: the generator drops, on the pinned interpreter, every source that is
    unassigned (Cn) or in a dropped category, so no entry can be dead. Asserted (the count is 0 on Unicode 15.0.0 and 15.1.0, both
    supported interpreters); on a newer interpreter a failure would be a signal to regenerate, not noise."""
    unassigned = [cp for cp in _confusables.TABLE if unicodedata.category(chr(cp)) == "Cn"]
    assert not unassigned, (
        f"{len(unassigned)} table sources are unassigned: {[hex(c) for c in unassigned[:5]]}"
    )
    for cp in _confusables.TABLE:
        category = unicodedata.category(chr(cp))
        assert category not in textnorm._DROP_CATEGORIES, (hex(cp), category)
    assert "Unicode 15.1 only" in (_confusables.__doc__ or ""), (
        "the notice does not say the sources are those of Unicode 15.1"
    )
    assert "MUST NOT BE REMOVED" in (_confusables.__doc__ or ""), (
        "the notice does not say it travels with copies"
    )


def test_the_generator_refuses_an_unpinned_file_and_is_deterministic(tmp_path):
    gen = _load("gen_confusables")
    bad = tmp_path / "confusables.txt"
    bad.write_text("0430 ;\t0061 ;\tMA\t# x\n", encoding="utf-8")
    assert gen.main(["gen", str(bad)]) == 1, "the generator accepted an unpinned file"
    tab, nl = chr(9), chr(10)
    assert gen.build("0406 ;" + tab + "006C ;" + tab + "MA" + nl)[0x406] == "I", (
        "capital I prototype read as l"
    )  # an upper-case source with prototype l reads as I
    assert gen.build("0456 ;" + tab + "0069 ;" + tab + "MA" + nl)[0x456] == "i"
    table = gen.build(
        "0430 ;\t0061 ;\tMA\t# x\n13AA ;\t0041 ;\tMA\t# y\n0021 ;\t0049 ;\tMA\t# ascii source\n05AD ;\t0021 ;\tMA\t# punctuation target\n"
    )
    assert table[0x430] == "a" and table[0x13AA] == "A", "a data row is not in the table"
    assert 0x21 not in table, "an ASCII source was accepted"
    assert 0x05AD not in table, "a punctuation target was accepted"
    assert 0x1D00 in table, "the small capital rule is missing"


def test_the_generator_writes_the_digest_and_the_longest_value_it_built():
    gen = _load("gen_confusables_digest")
    data = (ROOT / "tools" / "data" / "confusables.txt").read_bytes()
    _skip_unless_checked_version()
    table = gen.build(data.decode("utf-8"))
    lines = "".join(f"{cp:06X}:{table[cp]}\n" for cp in sorted(table))
    assert gen.table_digest(table) == hashlib.sha256(lines.encode("utf-8")).hexdigest()
    assert gen.table_digest(table) == _confusables.TABLE_DIGEST
    assert max(len(v) for v in table.values()) == _confusables.MAX_VALUE_LEN


def test_the_generator_reproduces_the_checked_in_table_offline():
    gen = _load("gen_confusables2")
    data = (ROOT / "tools" / "data" / "confusables.txt").read_bytes()
    assert (
        gen.DEFAULT_INPUT.read_bytes() == data
    )  # the generator reads the vendored file by default
    assert hashlib.sha256(data).hexdigest() == gen.PINNED_SHA256 == _confusables.DATA_SHA256, (
        "the vendored data file is not the pinned one"
    )
    _skip_unless_checked_version()
    assert gen.build(data.decode("utf-8")) == _confusables.TABLE
