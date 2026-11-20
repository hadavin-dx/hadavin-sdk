"""E15: an entity- or percent-spelled placeholder. Pins the accepted, fail-safe behaviour."""

import pytest

from hadavin_sdk.guard import runmap

SPELLINGS = ["&lt;IPV4_1&gt;", "%3CIPV4_1%3E", "&#60;IPV4_1&#62;"]
KEYED = {"<IPV4_1>": "10.0.0.1", "<SECRET_1>": "sk-realsecret0123456789abcd"}


@pytest.mark.parametrize("spelled", SPELLINGS)
def test_untrusted_spelling_is_left_as_typed_and_never_restores(spelled):
    mapping = dict(KEYED)
    out = runmap.redact_untrusted(spelled, mapping)
    assert out == spelled  # not decoded into a placeholder shape
    assert runmap.restore_text(out, mapping) == spelled  # nothing substituted
    assert "10.0.0.1" not in out


@pytest.mark.parametrize("spelled", SPELLINGS)
def test_model_written_spelling_decodes_to_a_placeholder_the_model_could_type(spelled):
    mapping = dict(KEYED)
    out = runmap.redact_text(spelled, mapping)
    assert out == "<IPV4_1>"
    assert mapping == KEYED  # no new entry, nothing forged into the map
    # same result as the model typing the placeholder itself: no extra reach
    assert runmap.restore_text(out, mapping) == runmap.restore_text("<IPV4_1>", mapping)


@pytest.mark.parametrize("spelled", ["&lt;SECRET_1&gt;", "%3CSECRET_1%3E", "<SECRET_1>"])
@pytest.mark.parametrize("fn", [runmap.redact_text, runmap.redact_untrusted])
def test_secret_placeholder_never_restores_in_any_spelling(spelled, fn):
    mapping = dict(KEYED)
    out = fn(spelled, mapping)
    assert "sk-realsecret" not in runmap.restore_text(out, mapping)
    assert "sk-realsecret" not in runmap.enforce_map(out, mapping)


@pytest.mark.parametrize("spelled", SPELLINGS)
def test_unknown_key_restores_to_nothing(spelled):
    for m in ({}, {"<IPV4_9>": "10.9.9.9"}):
        mapping = dict(m)
        out = runmap.redact_text(spelled, mapping)
        assert runmap.restore_text(out, mapping) == out == "<IPV4_1>"
