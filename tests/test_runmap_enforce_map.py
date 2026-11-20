"""`runmap.enforce_map`: replace the values a run map already holds, and nothing else (ORDER 007; the mask step
of the model gate). Added to guard/runmap.py for step F; the replace itself is the redactor's own sweep."""

from __future__ import annotations

import copy
import sys
import threading
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


# --- lead review round 1: the traps of the enforce build (B1) ---------------------------------------------------


def test_a_placeholder_inserted_in_this_pass_is_not_rewritten_by_a_later_shorter_original():
    """Trap 2. The redactor's sweep replaces value after value inside one stretch of text and does not set
    aside the placeholders it has just written: a shorter known value that is a piece of such a placeholder
    (`SECRET`, `UUID_1`, `IPV4`) and also occurs raw in the same stretch was replaced INSIDE it
    (`<<SECRET_1>_2>`, seen 2026-11-20 before the fix). enforce_map sweeps such values afterwards."""
    cases = [
        ({"<SECRET_2>": TOKEN, "<SECRET_1>": "SECRET"}, f"a {TOKEN} b SECRET c", "a <SECRET_2> b <SECRET_1> c"),
        ({"<UUID_1>": TOKEN, "<TENANT_1>": "UUID_1"}, f"a {TOKEN} b UUID_1 c", "a <UUID_1> b <TENANT_1> c"),
        ({"<IPV4_1>": IP, "<TENANT_1>": "IPV4"}, f"a {IP} b IPV4 c", "a <IPV4_1> b <TENANT_1> c"),
        # two held-back values, one a piece of the other's placeholder
        (
            {"<SECRET_1>": TOKEN, "<TENANT_7>": "SECRET_1", "<SECRET_3>": "TENANT"},
            f"{TOKEN} SECRET_1 TENANT",
            "<SECRET_1> <TENANT_7> <SECRET_3>",
        ),
        # a whole placeholder token of the map held as a value: the token in the text is never touched
        ({"<IPV4_1>": IP, "<SECRET_1>": "<IPV4_1>"}, f"x {IP} y", "x <IPV4_1> y"),
    ]  # fmt: skip
    for mapping, text, expected in cases:
        out = _enforce(text, mapping)
        assert out == expected, "a placeholder inserted in this pass was rewritten"
        assert _enforce(text, runmap.RunMap(mapping)) == expected
        assert "<<" not in out and ">_" not in out


def test_stated_limit_partial_overlap_leaves_a_tail():
    """Trap 3, STATED LIMIT. `abcd` and `cdef` are both known and the text holds `abcdef`: neither contains
    the other, so only one can be replaced and the rest of the other stays readable. Which one: the longer,
    and for equal length the one that comes first in the map."""
    assert _enforce("abcdef", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}) == "<SECRET_1>ef"
    assert _enforce("abcdef", {"<SECRET_2>": "cdef", "<SECRET_1>": "abcd"}) == "ab<SECRET_2>"
    assert _enforce("abcdefg", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdefg"}) == "ab<SECRET_2>"
    # two identifiers: each is touched by a letter of the other, so NEITHER is replaced in the overlap ...
    identifiers = {"<TENANT_1>": "abcd", "<TENANT_2>": "cdef"}
    assert _enforce("abcdef", identifiers) == "abcdef"
    # ... while each standalone copy still is
    assert _enforce("abcdef abcd cdef", identifiers) == "abcdef <TENANT_1> <TENANT_2>"


def test_seed_entries_of_the_map_are_harmless():
    """Trap 6. approvals/channel.py seeds a map with `"<IPV4_1>": "\\0seed<IPV4_1>"` so a number is never
    reused. Such an original holds a placeholder token, so it can never be found in the text between
    tokens: nothing is replaced for it, real entries beside it still work, nothing raises."""
    mapping = runmap.RunMap(
        {"<IPV4_1>": "\0seed<IPV4_1>", "<SECRET_4>": "\0seed<SECRET_4>", "<IPV4_2>": IP}
    )
    text = f"host <IPV4_1> token <SECRET_4> raw {IP} and the word seed, also \0seed<IPV4_1>"
    assert _enforce(text, mapping) == text.replace(IP, "<IPV4_2>")
    only_seeds = {"<IPV4_1>": "\0seed<IPV4_1>"}
    assert _enforce(f"host <IPV4_1> raw {IP}", only_seeds) == f"host <IPV4_1> raw {IP}"


def test_pin_the_callers_cache_is_never_written_even_when_the_patterns_must_be_rebuilt():
    """Trap 4. The sweep writes the cache it is given whenever it has to rebuild (a cache that is empty or
    older than the map), so enforce_map must hand it a private copy."""
    stale = runmap.RunMap()
    runmap.redact_text(f"host {IP}", stale)
    dict.__setitem__(stale, "<SECRET_1>", TOKEN)  # the cache is now older than the map
    empty = runmap.RunMap({"<IPV4_1>": IP})  # never used: an empty cache
    late = runmap.RunMap({"<SECRET_2>": TOKEN, "<SECRET_1>": "SECRET"})  # the held-back path
    for mapping in (stale, empty, late):
        cache, snapshot = mapping.redact_cache, copy.copy(mapping.redact_cache)
        text = f"host {IP} token {TOKEN} SECRET"
        assert (
            runmap.enforce_map(text, mapping) != text
        )  # something was replaced: the patterns were built
        assert mapping.redact_cache is cache, "the caller's cache was replaced"
        assert cache == snapshot and all(cache[k] is snapshot[k] for k in snapshot), (
            "the caller's cache was written"
        )


# --- lead review round 1: STATED LIMITS, each checked against redact._sweep ----------------------------------------


def test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept():
    """`redact._sweep`: under 3 characters, never. A secret kind of 4 characters or more, every copy. Any
    other value (an identifier kind, or a 3-character secret): not when it is all digits and under 6
    characters, not when it is a common word (any letter case)."""
    not_swept = [
        ({"<SECRET_1>": "ab"}, "x ab y"),
        ({"<TENANT_1>": "ab"}, "x ab y"),
        ({"<SECRET_1>": "123"}, "x 123 y"),  # a 3-character secret follows the identifier rule
        ({"<SECRET_1>": "dev"}, "x dev y"),
        ({"<TENANT_1>": "12345"}, "x 12345 y"),
        ({"<IPV4_1>": "8080"}, "port 8080 open"),
        ({"<TENANT_1>": "prod"}, "x prod y"),
        ({"<TENANT_1>": "Prod"}, "x Prod y"),
        ({"<HOSTNAME_1>": "web"}, "the web tier"),
    ]
    for mapping, text in not_swept:
        assert _enforce(text, mapping) == text, mapping
    swept = [
        ({"<SECRET_1>": "abc"}, "x abc y", "x <SECRET_1> y"),
        ({"<SECRET_1>": "12345"}, "x 12345 y", "x <SECRET_1> y"),  # a secret of 4+: digits do not exempt it
        ({"<SECRET_1>": "prod"}, "x prod y reprod", "x <SECRET_1> y re<SECRET_1>"),  # nor a common word
        ({"<TENANT_1>": "123456"}, "x 123456 y", "x <TENANT_1> y"),
        ({"<TENANT_1>": "abc"}, "x abc y", "x <TENANT_1> y"),
    ]  # fmt: skip
    for mapping, text, expected in swept:
        assert _enforce(text, mapping) == expected, mapping


def test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept():
    """`redact._replace_standalone`: an identifier is replaced only where no ASCII letter or digit touches
    it. An underscore, a dash, a dot or a letter outside ASCII beside it does not protect it."""
    mapping = {"<TENANT_1>": "abc123"}
    assert _enforce("xabc123 abc1234 9abc123 abc123z", mapping) == "xabc123 abc1234 9abc123 abc123z"
    assert (
        _enforce("abc123_ -abc123- .abc123. \u00e9abc123", mapping)
        == "<TENANT_1>_ -<TENANT_1>- .<TENANT_1>. \u00e9<TENANT_1>"
    )
    assert _enforce("x123456 1234567", {"<TENANT_1>": "123456"}) == "x123456 1234567"
    secret = {"<SECRET_1>": TOKEN}  # a secret is replaced in every copy
    assert _enforce(f"x{TOKEN}9", secret) == "x<SECRET_1>9"


# --- lead review round 1, M4: redact_text never empties the live map ----------------------------------------------

LINES = [
    "ERROR user_id=tenant{i}x at 10.{a}.{b}.7 refused",
    "mail from user{i}@example.com about 172.16.{a}.{b}",
    "caf\u00e9 \uff21 password=pw{i}Zq9x{a}{b} &amp; 50%",
    "plain text number {i}",
    "see <IPV4_1> and <EMAIL_9> and <IPV4_{i}>",
]


def test_m4_redact_text_only_ever_adds_to_the_map():
    """What dropping `clear()` rests on: after every call each entry the map held is still there, under the
    same placeholder, with the same value and in the same position; new entries come after them."""
    for start in ({}, {"<EMAIL_5>": "a@example.com"}, {"<IPV4_3>": "10.9.9.9", "<IPV4_1>": IP}):
        for untrusted in (False, True):
            mapping = runmap.RunMap(start)
            for i in range(60):
                before = list(mapping.items())
                text = LINES[i % len(LINES)].format(i=i, a=i % 7, b=i % 5)
                (runmap.redact_untrusted if untrusted else runmap.redact_text)(text, mapping)
                assert list(mapping.items())[: len(before)] == before, (
                    "an entry was removed or re-keyed"
                )
            assert len(mapping) > len(start)


def test_m4_redact_text_never_empties_the_map_on_the_way():
    """Deterministic: a map that refuses to be emptied. With `mapping.clear()` in redact_text this raises."""

    class NeverEmptied(runmap.RunMap):
        def clear(self):
            raise AssertionError("the live map was emptied during a write")

    mapping = NeverEmptied({"<IPV4_1>": IP})
    assert runmap.redact_text("peer 10.9.9.9 refused", mapping) == "peer <IPV4_2> refused"
    assert dict(mapping) == {"<IPV4_1>": IP, "<IPV4_2>": "10.9.9.9"}


def test_m4_a_reader_thread_never_sees_a_known_key_missing_during_many_writes():
    """The gate reads the run's live map from another thread (k1b runs the call in a thread). While one
    thread writes the map many times, a reader copying it never finds a known key gone, and enforcing a
    known value never returns it raw."""
    mapping = runmap.RunMap()
    runmap.redact_text(f"host {IP} token password={TOKEN}", mapping)
    known = dict(mapping)
    assert known == {"<IPV4_1>": IP, "<SECRET_1>": TOKEN}
    stop, missing, raw, errors = threading.Event(), [], [], []

    def read() -> None:
        try:
            while not stop.is_set():
                snapshot = dict(mapping)
                if any(snapshot.get(k) != v for k, v in known.items()):
                    missing.append(len(snapshot))
                if runmap.enforce_map(f"host {IP}", mapping) != "host <IPV4_1>":
                    raw.append(1)
        except Exception as exc:  # noqa: BLE001 - reported below, by type only
            errors.append(type(exc).__name__)

    interval = sys.getswitchinterval()
    sys.setswitchinterval(
        1e-6
    )  # switch threads as often as possible: the widest chance to see a gap
    readers = [threading.Thread(target=read, daemon=True) for _ in range(2)]
    try:
        for t in readers:
            t.start()
        for i in range(400):
            runmap.redact_text(f"peer 10.{i % 250}.{i // 250}.9 user_id=tenant{i}x", mapping)
    finally:
        stop.set()
        for t in readers:
            t.join(30)
        sys.setswitchinterval(interval)
    assert not any(t.is_alive() for t in readers)
    assert errors == [] and missing == [] and raw == []
    assert len(mapping) > 400
