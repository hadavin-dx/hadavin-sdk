"""How `runmap.redact_text` and `redact_untrusted` write the run's map, and what they do with their own output.

Moved here from tests/test_runmap_is_masked.py when `runmap.is_masked` was deleted (lead review round 2, m7: no
caller in src). Kept: the tests that are not about that function. The seeded text generator below is also a
corpus of tests/test_redact_idempotent_property.py; both now take it from tests/redact_corpus_support.py.
The tests that `redact_text` never empties the live map are in tests/test_runmap_enforce_map.py (M4)."""

from __future__ import annotations

import random

import pytest

from hadavin_sdk.guard import runmap
from tests.redact_corpus_support import IP, KEY, LOOKALIKES, TOKEN
from tests.redact_corpus_support import random_text as _random_text


def test_redact_text_writes_the_map_and_the_cache_it_was_given():
    """The write that `enforce_map` must never do: `redact_text` continues the caller's map in place and
    rebuilds the run's pattern cache when the map has grown."""
    mapping = runmap.RunMap()
    runmap.redact_text(f"host {IP} key {KEY}", mapping)
    runmap.redact_text("warm the cache", mapping)
    held, cache_map = dict(mapping), dict(mapping.redact_cache["map"])
    assert held and cache_map == held
    for text in [f"password={TOKEN}", "%41" + KEY[1:] + "x", "peer 10.9.9.9 refused"]:
        written: dict[str, str] = {}
        runmap.redact_text(text, written)
        assert written != {}
    runmap.redact_text("peer 10.9.9.9 refused", mapping)
    runmap.redact_text("again", mapping)
    assert list(mapping.items())[: len(held)] == list(held.items()) and len(mapping) > len(held)
    assert mapping.redact_cache["map"] != cache_map


def test_m8_a_mapping_whose_cache_attribute_raises_is_a_redaction_error_in_both_functions():
    """Lead review round 1, minor m8: the cache read is inside the fail-closed part."""

    class Exotic(dict):
        @property
        def redact_cache(self):
            raise OSError(f"cache backend down {TOKEN}")

    for call in (runmap.redact_text, runmap.enforce_map):
        with pytest.raises(runmap.RedactionError) as caught:
            call(f"host {IP}", Exotic({"<IPV4_1>": IP}))
        assert caught.value.args == ("OSError",) and caught.value.__cause__ is None


def test_recorded_the_untrusted_hook_on_already_redacted_text_escapes_its_real_placeholders():
    """Changed by G7 follow-up, 2026-11-20 (guard/redact.py `_mask` leaves a value made only of escaped
    look-alikes and genuine placeholders alone). `neutralise_untrusted` still escapes the genuine
    placeholders of a text that is already redacted, but the escaped token after `password=` is no longer
    masked as a new secret: no junk map entry. Before the fix the second pass gave `<SECRET_2>`."""
    mapping = runmap.RunMap()
    out = runmap.redact_untrusted(f"password={TOKEN} at {IP}", mapping)
    assert out == "password=<SECRET_1> at <IPV4_1>"
    held = dict(mapping)
    assert (
        runmap.redact_text(out, mapping) == out and dict(mapping) == held
    )  # trusted: a fixed point
    second = runmap.RunMap(mapping)
    again = runmap.redact_untrusted(out, second)
    assert again == "password=‹SECRET_1› at ‹IPV4_1›"
    assert dict(second) == held  # nothing new was learned from the escaped tokens


def test_round_trip_redact_untrusted_learns_nothing_new_from_its_own_output():
    """The seeded loop with placeholder look-alikes in the text: a second `redact_untrusted` pass over the
    first pass's output adds no entry to the run's map (it only escapes the placeholders), and no value the
    map holds as a secret comes back raw. Indexes only: a failing text is never printed."""
    rng = random.Random(7)  # noqa: S311 - a test fixture generator, not a secret
    mapping = runmap.RunMap()
    failures = []
    for i in range(300):
        if i % 25 == 0:
            mapping = runmap.RunMap()
        text = _random_text(rng) + " " + rng.choice(LOOKALIKES) + " " + _random_text(rng)
        out = runmap.redact_untrusted(text, mapping)
        held = dict(mapping)
        again = runmap.redact_untrusted(out, mapping)
        if dict(mapping) != held:
            failures.append(("the map grew", i))
        if KEY in again or TOKEN in again:
            failures.append(("a secret came back", i))
    assert failures == []


@pytest.mark.parametrize("spelling", LOOKALIKES[:3], ids=["html-entity", "backslash-u", "percent"])
def test_shape_a_an_escaped_lookalike_in_untrusted_text_comes_back_as_written(spelling):
    """Run 2026-11-20, confirmed: redact_untrusted returns the text as written (the decoded view is
    neutralised before it is redacted) and learns nothing; a second pass is the same."""
    mapping = runmap.RunMap()
    text = f"see {spelling} here"
    out = runmap.redact_untrusted(text, mapping)
    assert out == text and dict(mapping) == {}
    assert runmap.redact_untrusted(out, mapping) == text and dict(mapping) == {}


class _WriteWatched(runmap.RunMap):
    """A run map that fails on every way of removing an entry and, in `update`, checks that what is written still
    holds every earlier key with its value (m-new-5: the old test caught a literal `clear()` only)."""

    def clear(self):
        raise AssertionError("the live map was emptied during a write (clear)")

    def pop(self, *args):
        raise AssertionError("an entry was removed during a write (pop)")

    def popitem(self):
        raise AssertionError("an entry was removed during a write (popitem)")

    def __delitem__(self, key):
        raise AssertionError("an entry was removed during a write (__delitem__)")

    def update(self, *args, **kwargs):
        incoming = dict(*args, **kwargs)
        for key, value in dict(self).items():
            assert incoming.get(key) == value, (
                "an earlier entry was dropped or changed by the write"
            )
        super().update(incoming)


@pytest.mark.parametrize("call", [runmap.redact_text, runmap.redact_untrusted])
def test_a_write_never_removes_or_changes_an_earlier_entry_by_any_route(call):
    """Deterministic: every removal route raises, and `update` sees the full old content. A mutant that clears,
    pops, deletes, or writes a changed earlier value fails here (tests/gate_mutants.py R3, R3b)."""
    mapping = _WriteWatched({"<IPV4_1>": IP})
    assert call("peer 10.9.9.9 refused", mapping) == "peer <IPV4_2> refused"
    assert dict(mapping) == {"<IPV4_1>": IP, "<IPV4_2>": "10.9.9.9"}
    assert call(f"again {IP} and password={TOKEN}", mapping).startswith("again <IPV4_1>")
    assert list(mapping)[:2] == ["<IPV4_1>", "<IPV4_2>"] and len(mapping) == 3


def test_the_hook_does_not_hide_a_real_value():
    """Moved from the is_masked file: the untrusted hook escapes look-alikes, it never hides a real value."""
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    out = runmap.redact_untrusted(f"see &lt;ID_5&gt; at {IP} key {KEY}", mapping)
    assert IP not in out and KEY not in out and "&lt;ID_5&gt;" in out
    pct = runmap.redact_untrusted(
        "line " + "%41" + KEY[1:] + " end", runmap.RunMap({"<IPV4_1>": IP})
    )
    assert KEY[1:] not in pct
