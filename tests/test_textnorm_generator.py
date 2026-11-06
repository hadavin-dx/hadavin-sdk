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

from hadavin_sdk import defaults
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
    # whole-script and rare look-alikes the first, curated table missed (not here, because the 15.1.0 data does not list them: U+2C82 Coptic Vida, U+0237 dotless j, U+0192 f with hook)
    named = {0x13AA: "A", 0x13A0: "D", 0x10E7: "y", 0x5D5: "l", 0xA4D0: "B", 0x269: "i", 0x1C0: "l",
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
    assert len(_confusables.TABLE) >= 500
    for cp, v in _confusables.TABLE.items():
        assert v.isascii() and re.fullmatch("[A-Za-z0-9]+", v), (hex(cp), v)
        assert cp >= 0x80 and unicodedata.normalize("NFKC", chr(cp)) == chr(cp), hex(
            cp
        )  # only code points the fold can see
    assert dict(textnorm._TABLE) == _confusables.TABLE
    assert len(textnorm._LOOKALIKES) == len(_confusables.TABLE)


def test_no_table_source_is_in_a_dropped_category():
    """No entry can be dead: the generator leaves out every source in a category the fold drops, and the notice travels with copies."""
    for cp in _confusables.TABLE:
        category = unicodedata.category(chr(cp))
        assert category not in textnorm._DROP_CATEGORIES - {"Cn"}, (hex(cp), category)
    assert "MUST NOT BE REMOVED" in (_confusables.__doc__ or ""), (
        "the notice does not say it travels with copies"
    )
    assert _confusables.DATA_VERSION == defaults.TEXTNORM_PINNED_UNIDATA == "15.1.0", (
        "the table data is not the Unicode version of the pin"
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


def test_the_name_rules_of_the_generator_read_the_letter_and_digit_forms():
    """Each Unicode-name rule of the generator, by itself, on a table built from NO data row (the rules do not need the data file)."""
    gen = _load("gen_confusables_rules")
    table = gen.build("")
    assert table.get(0x1F150) == "A" and table.get(0x1F169) == "Z", (
        "the negative circled letters are not read as their letter"
    )
    assert table.get(0x1F170) == "A" and table.get(0x1F189) == "Z", (
        "the negative squared letters are not read as their letter"
    )
    assert table.get(0x1F1E6) == "A" and table.get(0x1F1FF) == "Z", (
        "the regional indicator letters are not read as their letter"
    )
    assert table.get(0x1F1A5) == "d", "the squared small letter d is not read as d"
    assert table.get(0x2776) == "1" and table.get(0x2780) == "1" and table.get(0x278A) == "1", (
        "the circled digits are not read as their digit"
    )
    assert table.get(0x24FF) == "0" and table.get(0x24FE) == "10" and table.get(0x277F) == "10", (
        "the negative circled zero and the circled ten are not read"
    )
    assert table.get(0x126) == "H" and table.get(0x127) == "h", (
        "a letter with a stroke is not read as its letter in its own case"
    )
    assert table.get(0x1D0C) == "L" and table.get(0x29B) == "G", (
        "a small capital with a mark is not read as its capital letter"
    )
    data = gen.build("028B ;\t0075 ;\tMA\t# the small v with hook is read as u by the data\n")
    assert data.get(0x28B) == "u" and data.get(0x1B2) == "U", (
        "a capital follows the other-case form that the data already reads"
    )
    assert gen.name_rule_value("NEGATIVE CIRCLED DIGIT ZERO") == "0"
    assert gen.name_rule_value("CIRCLED IDEOGRAPH ONE") is None, (
        "a name rule read an ideograph as a digit"
    )


def test_the_generator_refuses_any_other_unicode_version_before_it_looks_at_the_hash(tmp_path):
    gen = _load("gen_confusables_version")
    real = (ROOT / "tools" / "data" / "confusables.txt").read_bytes()
    assert real.count(b"# Version: 15.1.0") == 1
    assert gen.check_input(real) is None, "the vendored file is refused"
    other = real.replace(b"# Version: 15.1.0", b"# Version: 18.0.0")
    problem = gen.check_input(other)
    assert problem and "Unicode version 18.0.0" in problem and "15.1.0" in problem, (
        "an other Unicode version is not refused by its version"
    )  # the hash would differ too, but the message must name the version
    bad_date = real.replace(b"# Date: 2023-08-11", b"# Date: 2026-08-06")
    assert "dated 2026-08-06" in (gen.check_input(bad_date) or ""), "an other date is accepted"
    assert "is not the pinned" in (gen.check_input(real + b"\n#") or ""), (
        "an edited file is accepted"
    )
    out = tmp_path / "confusables.txt"
    out.write_bytes(other)
    assert gen.main(["gen", str(out)]) == 1, "main accepted an other Unicode version"
    assert gen.PINNED_VERSION == defaults.TEXTNORM_PINNED_UNIDATA


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
    built = gen.build(data.decode("utf-8"))
    assert built == _confusables.TABLE, "the generator output differs from the checked-in table"
    assert built[0x4CF] == "l", "the Cyrillic palochka no longer reads as l"


def test_a_supplement_entry_is_never_overridden_by_a_name_rule_and_the_data_wins_over_the_supplement(
    monkeypatch,
):
    """p1a6-007: the supplement is merged into the table BEFORE the name rules run, so a name rule (``setdefault``) cannot override it. The
    supplement entry here is the small h with a stroke (U+0127), which the name rule would read as ``h``; the supplement says ``z``. And
    a data line for the same code point beats the supplement."""
    gen = _load("gen_confusables_supplement")
    assert gen.name_rule_value(unicodedata.name(chr(0x127))) == "h", (
        "the name rule no longer reads U+0127"
    )
    monkeypatch.setattr(gen, "SUPPLEMENT", {0x127: "z"})
    assert gen.build("").get(0x127) == "z", "a name rule overrode a supplement entry"
    data = "0127 ;\t0079 ;\tMA\t# the data reads it as y\n"
    assert gen.build(data).get(0x127) == "y", "the supplement overrode a data line"
    monkeypatch.setattr(gen, "SUPPLEMENT", {})
    assert gen.build("").get(0x127) == "h", "the name rule does not fire without the supplement"


def test_the_generator_docstring_does_not_claim_that_the_size_rule_reads_the_longest_value():
    """p1a6-003: ``MAX_VALUE_LEN`` is written beside the table and compared with it by a test; ``textnorm.py`` does not read it (its size rule
    weighs every character from the table itself), and the generator no longer says it does."""
    gen_src = GEN_PATH.read_text(encoding="utf-8")
    assert "which the size rule" not in gen_src and "does not read it" in gen_src
    assert "MAX_VALUE_LEN" not in Path(textnorm.__file__).read_text(encoding="utf-8")
