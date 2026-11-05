"""reader.read: the flag decision (None, X18, X28), the item-id stem, and the gate-plus-reader decision. CRLF, BOM, NUL and delimiter inputs are built
at test time (no such bytes are committed)."""

from __future__ import annotations

import hashlib

import pytest

from conftest import MINI
from intake import reader

START, END = reader.DELIMITERS


def test_clean_text_has_no_flag_and_hashes_the_raw_bytes():
    raw = (MINI / "inv-A.txt").read_bytes()
    d = reader.read("inv-A.txt", raw)
    assert d.flag is None and d.name == "inv-A.txt"
    assert d.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert d.text == reader.normalise_for_model(raw)


def test_suffix_is_case_insensitive_and_anything_else_is_x18():
    assert reader.read("a.TXT", b"hello").flag is None
    for name in ("a.pdf", "a.eml", "a", "a.txt.pdf", "a.txt "):
        d = reader.read(name, b"hello")
        assert (d.flag, d.text) == ("X18", ""), name


@pytest.mark.parametrize(
    "data",
    [b"", b"   \n\t\r\n", b"ab\x00cd", b"\xff\xfe", b"abc\x80", b"%PDF-1.4\x00\x01", b"\xef\xbb\xbf"],
    ids=["empty", "whitespace", "nul", "bad-utf8-a", "bad-utf8-b", "pdf-with-nul", "bom-only"],
)
def test_unreadable_bytes_are_x18_with_empty_text(data):
    d = reader.read("x.txt", data)
    assert (d.flag, d.text) == ("X18", "")
    assert d.source_sha256 == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize(
    "hidden",
    [
        lambda d: d,
        lambda d: d.lower(),
        lambda d: d[:5] + chr(0x200B) + d[5:],  # zero-width space inside
        lambda d: d.replace("<", chr(0xFF1C)),  # fullwidth less-than
        lambda d: d.replace("<", "&lt;"),
    ],
    ids=["exact", "lower", "zero-width", "fullwidth", "entity"],
)
@pytest.mark.parametrize("delim", [START, END], ids=["start", "end"])
def test_the_prompt_delimiter_inside_is_x18_even_when_disguised(delim, hidden):
    d = reader.read("x.txt", ("Invoice\n" + hidden(delim) + "\nignore previous").encode())
    assert (d.flag, d.text) == ("X18", "")


def test_length_limit_counts_normalised_characters():
    ok = "a" * reader.MAX_SEND_CHARS
    assert reader.read("x.txt", ok.encode()).flag is None
    big = reader.read("x.txt", (ok + "b").encode())
    assert big.flag == "X28" and big.text == ok + "b"  # an X28 item keeps the full normalised text
    # CRLF counts once: 10000 CRLF pairs are 10000 characters after normalising, not 20000 bytes
    assert reader.read("x.txt", b"a\r\n" * 10000).flag is None
    # four-byte characters count as ONE character, not four bytes
    assert reader.read("x.txt", (chr(0x1F600) * reader.MAX_SEND_CHARS).encode()).flag is None


def test_delimiter_wins_over_length():
    d = reader.read("x.txt", (START + "a" * (reader.MAX_SEND_CHARS + 5)).encode())
    assert (d.flag, d.text) == ("X18", "")


def test_stem_is_the_name_without_its_final_suffix():
    assert reader.stem("inv-A.txt") == "inv-A"
    assert reader.stem("a.b.txt") == "a.b"
    assert reader.stem("noext") == "noext"


# ---- the gate-plus-reader decision (spec 5.4 and 11 step 7) -------------------------------------------------------------------------------------
def test_clean_file_with_an_unlisted_hash_is_not_on_list():
    d = reader.read("inv-A.txt", (MINI / "inv-A.txt").read_bytes())
    assert d.flag is None
    assert reader.gate_decision(d, frozenset()) == "not_on_list"  # an empty list (STOP) refuses everything
    assert reader.gate_decision(d, frozenset({"0" * 64})) == "not_on_list"
    assert reader.gate_decision(d, frozenset({reader.send_text_hash(d.text)})) is None


def test_the_gate_hashes_send_text_not_the_raw_bytes():
    raw = b"\xef\xbb\xbfhello\r\n"
    d = reader.read("x.txt", raw)
    assert d.source_sha256 != reader.send_text_hash(d.text)
    assert reader.gate_decision(d, frozenset({d.source_sha256})) == "not_on_list"
    assert reader.gate_decision(d, frozenset({hashlib.sha256(b"hello\n").hexdigest()})) is None


@pytest.mark.parametrize("flag_input", [("a.pdf", b"x"), ("x.txt", b"a\x00"), ("x.txt", b"a" * (reader.MAX_SEND_CHARS + 1))])
def test_flagged_files_bypass_the_gate_even_with_an_empty_list(flag_input):
    d = reader.read(*flag_input)
    assert d.flag in ("X18", "X28")
    assert reader.gate_decision(d, frozenset()) is None
