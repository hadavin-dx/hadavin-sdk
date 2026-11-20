"""`runmap.undo` composes a base letter with its combining marks again (G1 fix round 1, finding B1).

The fold made `runmap.canonical` per character (index fidelity for replacement), and `nfkc` (used by `undo` in every
round) called it, so `undo` stopped composing: a handed-out secret stored precomposed and shown decomposed was no
longer scrubbed. The expected values are literals (what main's `undo` returned)."""

import unicodedata

import pytest

from hadavin_sdk import tools as tools_mod
from hadavin_sdk.guard import runmap


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


# built from parts so the file holds no literal credential
_NAME = "Mü" + "ller"
_VIET = "Việ" + "t" + "Ấn"  # stacked marks: e + dot below + circumflex, A + circumflex + acute
_HANGUL = "한" + "글"  # two precomposed syllables
_JAMO = "한글"  # the same two syllables as conjoining jamo


@pytest.mark.parametrize("precomposed", [_NAME, _VIET, _HANGUL, "café-" + "Pw1"])
def test_undo_of_nfd_input_is_the_precomposed_text(precomposed):
    assert _nfd(precomposed) != precomposed or precomposed == "".join(precomposed)
    assert runmap.undo(_nfd(precomposed)) == precomposed
    assert runmap.undo(precomposed) == precomposed
    assert runmap.nfkc(_nfd(precomposed)) == precomposed


def test_undo_joins_hangul_jamo():
    assert runmap.undo(_JAMO) == _HANGUL


def test_undo_composes_inside_an_escape_layer():
    assert runmap.undo("%" + "4" + "1" + _nfd(_NAME)) == "A" + _NAME


def test_undo_still_drops_format_characters():
    assert runmap.undo("pa​ss⁠word") == "password"
    assert runmap.undo("ＡＢ") == "AB"


_SECRET = "Mü" + "ller-" + "Zq7" + "Rt2" + "xK9"


def test_handed_out_secret_shown_decomposed_is_scrubbed():
    out = tools_mod.prepare_output("login " + _nfd(_SECRET) + " ok", {}, 1000, [_SECRET])
    assert "Zq7" not in out
    assert tools_mod.MARKER in out


def test_handed_out_secret_shown_as_hangul_jamo_is_scrubbed():
    secret = _HANGUL + "-" + "Zq7" + "Rt2" + "xK9"
    shown = _JAMO + "-" + "Zq7" + "Rt2" + "xK9"
    out = tools_mod.prepare_output("login " + shown + " ok", {}, 1000, [secret])
    assert "Zq7" not in out
    assert tools_mod.MARKER in out


def test_strip_fragment_recognises_a_cut_tail_with_a_decomposed_front():
    forms = sorted(tools_mod._secret_forms(_SECRET))
    front = _nfd(_SECRET)[:9]  # decomposed: the cut leaves the front of the secret
    text = "start " + front + tools_mod.TRUNCATED
    out = tools_mod._strip_fragment(text, forms)
    assert out == "start " + tools_mod.TRUNCATED
