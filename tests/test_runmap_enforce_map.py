"""`runmap.enforce_map`: replace the values a run map already holds, and nothing else (ORDER 007; the mask step
of the model gate). Added to guard/runmap.py for step F; the replace itself is the redactor's own sweep."""

from __future__ import annotations

import copy
from types import MappingProxyType

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # the documented AWS example key, built from parts
TOKEN = "s3cr3t" + "VALUE9xQ2"  # a fake, built from parts
IP = "10.0.0.5"


def _run_map() -> runmap.RunMap:
    mapping = runmap.RunMap()
    runmap.redact_untrusted(
        f"ERROR user_id=abc123 at {IP} password={TOKEN} peer 10.0.0.50", mapping
    )
    assert dict(mapping) == {
        "<TENANT_1>": "abc123",
        "<IPV4_1>": IP,
        "<SECRET_1>": TOKEN,
        "<IPV4_2>": "10.0.0.50",
    }
    return mapping


def _enforce(text: str, mapping) -> str:
    """enforce_map with its promises asserted on every call: map and cache untouched, a str, idempotent."""
    before = dict(mapping)
    cache = copy.copy(getattr(mapping, "redact_cache", None))
    out = runmap.enforce_map(text, mapping)
    assert isinstance(out, str)
    assert dict(mapping) == before
    if cache is not None:
        assert mapping.redact_cache == cache and all(
            mapping.redact_cache[k] is cache[k] for k in cache
        )
    assert runmap.enforce_map(out, mapping) == out  # doing it twice changes nothing more
    return out


def test_every_raw_copy_of_a_known_value_gets_its_existing_placeholder():
    mapping = _run_map()
    out = _enforce(f"ref abc123, host {IP}, token {TOKEN}, again {IP}", mapping)
    assert out == "ref <TENANT_1>, host <IPV4_1>, token <SECRET_1>, again <IPV4_1>"


def test_a_text_with_no_raw_copy_comes_back_equal():
    mapping = _run_map()
    for text in [
        "",
        "plain text",
        "host <IPV4_1> and <SECRET_1>",
        "caf\u00e9 \uff21 50% &amp; done",
    ]:
        assert _enforce(text, mapping) == text
    assert _enforce(f"key {KEY} at 10.9.9.9", {}) == f"key {KEY} at 10.9.9.9"


def test_nothing_new_is_found_no_pattern_is_run():
    """Detection is the producers' work: a secret that is in no map is left as written."""
    mapping = _run_map()
    text = f"key {KEY} peer 10.9.9.9 password=hunter2"
    assert _enforce(text, mapping) == text


def test_placeholders_already_present_are_untouched_also_ones_the_map_does_not_hold():
    mapping = runmap.RunMap({"<TENANT_1>": "UUID_1", "<IPV4_1>": IP})
    text = "<UUID_1> and <IPV4_9> and <IPV4_1>"
    assert _enforce(text, mapping) == text  # no replace inside a placeholder token
    assert _enforce("id UUID_1 here", mapping) == "id <TENANT_1> here"


def test_an_original_that_is_a_substring_of_another_is_replaced_whole_longest_first():
    mapping = _run_map()  # 10.0.0.5 is a prefix of 10.0.0.50
    assert _enforce("a 10.0.0.50 b 10.0.0.5 c", mapping) == "a <IPV4_2> b <IPV4_1> c"
    nested = {"<SECRET_1>": TOKEN, "<SECRET_2>": TOKEN + "-tail77"}
    assert _enforce(f"x {TOKEN}-tail77 y {TOKEN} z", nested) == "x <SECRET_2> y <SECRET_1> z"


def test_a_secret_is_replaced_in_every_copy_an_identifier_only_where_it_stands_alone():
    """The redactor's own sweep rule, the one producer output already follows."""
    mapping = _run_map()
    assert _enforce(f"tok{TOKEN}9", mapping) == "tok<SECRET_1>9"
    assert _enforce("xabc1234 and abc123.", mapping) == "xabc1234 and <TENANT_1>."


def test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced():
    """Only the spelling held in the map: full-width, zero-width and escaped copies are the pattern
    redactor's work (redact_text), not this function's."""
    mapping = _run_map()
    for hidden in ["\uff11\uff10.0.0.5", "10.0\u200b.0.5", "10%2E0.0.5", "abc&#49;23"]:
        assert _enforce(f"host {hidden} end", mapping) == f"host {hidden} end"


def test_it_never_writes_the_map_or_the_cache_and_takes_a_read_only_mapping():
    mapping = _run_map()
    runmap.redact_text("warm the cache", mapping)
    assert mapping.redact_cache
    _enforce(f"host {IP}", mapping)
    frozen = MappingProxyType({"<IPV4_1>": IP})
    assert runmap.enforce_map(f"host {IP}", frozen) == "host <IPV4_1>"


def test_a_value_added_to_the_map_later_is_replaced_in_text_masked_earlier():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(f"alert: session ref abc123, upstream {IP}", mapping)
    assert "abc123" in doc and _enforce(doc, mapping) == doc
    runmap.redact_untrusted("ERROR user_id=abc123 refused", mapping)
    assert _enforce(doc, mapping) == "alert: session ref <TENANT_1>, upstream <IPV4_1>"


def test_over_the_cap_raises_input_too_large():
    with pytest.raises(runmap.InputTooLarge):
        runmap.enforce_map("a" * (defaults.MAX_REDACT_CHARS + 1), {})
    assert (
        runmap.enforce_map("a" * defaults.MAX_REDACT_CHARS, {}) == "a" * defaults.MAX_REDACT_CHARS
    )


@pytest.mark.parametrize(
    "bad", [{"<A_1>": 5}, {5: "x"}, {"<A_1>": None}], ids=["int-value", "int-key", "none"]
)
def test_a_bad_map_is_a_redaction_error_that_names_a_type_only(bad):
    with pytest.raises(runmap.RedactionError) as caught:
        runmap.enforce_map(f"x 5 {TOKEN}", bad)
    assert caught.value.__cause__ is None and TOKEN not in repr(caught.value)
    assert caught.value.args[0].isidentifier()


def test_a_text_that_is_not_a_str_raises():
    for bad in (None, 5, b"bytes"):
        with pytest.raises((TypeError, runmap.RedactionError)):
            runmap.enforce_map(bad, {"<IPV4_1>": IP})
