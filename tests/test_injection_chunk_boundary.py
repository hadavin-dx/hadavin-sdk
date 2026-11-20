"""A phrase hidden behind padding that is aimed at a chunk boundary of the injection check (G1 fix round 1, finding B2).

A text over the fold's size rule is read in pieces. `_holds` counted the a-z letters of every FOLD view (a full-width or Cyrillic
look-alike letter counts as a letter there) while the raw squash of `_score` keeps only ASCII a-z, so look-alike padding made `_holds` accept
a split point that the raw view cannot prove: `ignore` + padding + `previousinstructions` was found by the old whole-text read and missed.
The phrase and the padding are built from parts."""

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import injection

_HEAD = "ig" + "nore"
_TAIL = "previous" + "instruc" + "tions"
_PADDINGS = {
    "fullwidth": "ａ",  # full-width a
    "cyrillic": "а",  # Cyrillic a
}


_FILLER = "the quick brown fox jumps over a lazy dog "


def _filler(n: int) -> str:
    return (_FILLER * (n // len(_FILLER) + 1))[:n]


def _built(pad_char: str, pad_len: int) -> str:
    """The text: filler, the head, `pad_len` padding characters ending exactly on the first chunk boundary, the tail, filler to the length that
    forces the chunked read."""
    boundary = defaults.TEXTNORM_INJECTION_CHUNK_CHARS
    before = boundary - pad_len - len(_HEAD)
    text = _filler(before) + _HEAD + pad_char * pad_len + _TAIL
    return text + _filler(defaults.TEXTNORM_MAX_CHARS + 1000 - len(text))


@pytest.mark.parametrize("kind", sorted(_PADDINGS))
@pytest.mark.parametrize("pad_len", [1030, 1100, 2000])
def test_padding_aimed_at_the_first_boundary_does_not_hide_the_phrase(kind, pad_len):
    text = _built(_PADDINGS[kind], pad_len)
    assert len(text) > defaults.TEXTNORM_MAX_CHARS
    verdict = injection.injection_check(injection.RegexDetector(0.5), text, "t")
    assert verdict.flagged is True, "the phrase behind padding was not found"


@pytest.mark.parametrize("kind", sorted(_PADDINGS))
def test_the_same_text_without_the_phrase_is_not_flagged(kind):
    text = _built(_PADDINGS[kind], 1030).replace(_HEAD, "t" * len(_HEAD))
    verdict = injection.injection_check(injection.RegexDetector(0.5), text, "t")
    assert verdict.flagged is False
