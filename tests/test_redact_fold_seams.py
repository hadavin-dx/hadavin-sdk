"""Seams of the fold scan (P2d-1): lone surrogates, the error rule and the exact-str rule for `fold`."""

import importlib

import pytest

from hadavin_sdk.guard import runmap, textnorm

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
redact = redact_mod.redact


@pytest.fixture
def clean_char_cache():
    redact_mod._char_class.cache_clear()
    yield
    redact_mod._char_class.cache_clear()


def test_surr_1_a_lone_surrogate_leaves_no_clear_address_and_raises_only_a_redaction_error():
    text = "a" + "\ud800" + "b josé@exemple.fr"
    for call in (lambda: redact(text).text, lambda: runmap.redact_text(text, {})):
        try:
            out = call()
        except runmap.RedactionError:
            continue
        assert "exemple.fr" not in out, out


def test_err_1_a_fold_error_refuses_in_redact_text_and_passes_through_redact(
    monkeypatch, clean_char_cache
):
    assert hasattr(redact_mod, "fold")

    def too_long(*_a, **_k):
        raise textnorm.TextTooLong("x")

    monkeypatch.setattr(redact_mod, "fold", too_long)
    with pytest.raises(runmap.RedactionError) as info:
        runmap.redact_text("mail josé@exemple.fr", {})
    assert info.value.args == ("TextTooLong",)
    with pytest.raises(textnorm.TextnormError):
        redact("mail josé@exemple.fr")
    # the alias build folds the stored non-ASCII values: its error travels the same way
    with pytest.raises(textnorm.TextnormError):
        redact("plain ascii text", mapping={"<NAME_1>": "Josée Martín"})
    with pytest.raises(runmap.RedactionError) as info2:
        runmap.redact_text("plain ascii text", {"<NAME_1>": "Josée Martín"})
    assert info2.value.args == ("TextTooLong",)


def test_seam_2_fold_is_called_with_exact_str_only(monkeypatch, clean_char_cache):
    class S(str):
        pass

    assert hasattr(redact_mod, "fold")
    seen = []
    real = redact_mod.fold

    def spy(x, **k):
        seen.append(x)
        return real(x, **k)

    monkeypatch.setattr(redact_mod, "fold", spy)
    redact(S("mail josé@exemple.fr"))
    assert len(seen) >= 2
    assert any(len(x) == 1 for x in seen) and any(len(x) > 1 for x in seen)
    assert all(type(x) is str for x in seen), [type(x) for x in seen]


def test_seam_3_a_str_subclass_is_masked_like_the_plain_text():
    class S(str):
        pass

    plain = redact("mail josé@exemple.fr and key AKIAIOSFODNN7EXAMPLE")
    sub = redact(S("mail josé@exemple.fr and key AKIAIOSFODNN7EXAMPLE"))
    assert sub.text == plain.text and sub.mapping == plain.mapping
    assert runmap.redact_text(S("mail josé@exemple.fr"), {}) == "mail <EMAIL_1>"
