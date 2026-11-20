"""G0: `runmap.is_masked`, the check-only twin of `redact_text` (ticket G, section G0; invariants G0-I1 to I6)."""

from __future__ import annotations

import copy
import random
from urllib.parse import quote

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # the documented AWS example key, built from parts
TOKEN = "s3cr3t" + "VALUE9xQ2"  # a fake, built from parts (as tests/test_k5_classes.py)
IP = "10.0.0.5"

HIDDEN = {
    "full-width letter": "Ａ" + KEY[1:],
    "zero-width space": KEY[:2] + "\u200b" + KEY[2:],
    "backslash-u escape": "\\u0041" + KEY[1:],
    "percent-encoding": "%41" + KEY[1:],
    "percent-encoded key": "password%3D" + TOKEN,
}


def _run_map() -> runmap.RunMap:
    """A run map that already holds values, with a warm redactor cache (as a real run's map has)."""
    mapping = runmap.RunMap()
    runmap.redact_text(f"host {IP} key {KEY}", mapping)
    runmap.redact_text("warm the cache", mapping)
    assert mapping.redact_cache
    return mapping


def _frozen(mapping: runmap.RunMap):
    return dict(mapping), {k: id(v) for k, v in mapping.items()}, copy.copy(mapping.redact_cache)


def _check(text: str, mapping: runmap.RunMap) -> bool:
    """is_masked, with G0-I1 asserted on every call: map equal, same value objects, cache untouched."""
    before, ids, cache = _frozen(mapping)
    cache_id = id(mapping.redact_cache)
    result = runmap.is_masked(text, mapping)
    assert result is True or result is False  # G0-I5: a bool and nothing else
    assert dict(mapping) == before
    assert {k: id(v) for k, v in mapping.items()} == ids
    assert id(mapping.redact_cache) == cache_id and mapping.redact_cache == cache
    assert all(mapping.redact_cache[k] is cache[k] for k in cache)
    return result


def test_plain_clean_text_is_masked():
    assert _check("the deploy finished, nothing to report", _run_map()) is True
    assert runmap.is_masked("the deploy finished", {}) is True
    assert runmap.is_masked("", {}) is True


def test_a_secret_is_not_masked():
    assert _check(f"password={TOKEN}", _run_map()) is False
    assert runmap.is_masked(f"key {KEY}", {}) is False
    assert runmap.is_masked("peer 10.9.9.9 refused", {}) is False


@pytest.mark.parametrize("spelling", HIDDEN.values(), ids=HIDDEN.keys())
def test_a_secret_behind_a_layer_is_not_masked(spelling):
    assert _check(f"line {spelling} end", _run_map()) is False
    assert runmap.is_masked(f"line {spelling} end", {}) is False  # and not known to the map either


def test_a_second_copy_of_a_value_already_in_the_map_is_not_masked():
    """The map would NOT grow here: only the placeholder count shows it (kills 'drop the _held clause')."""
    mapping = _run_map()
    assert IP in mapping.values()
    assert _check(f"seen again from {IP}", mapping) is False
    assert _check(f"<IPV4_1> and once more {IP}", mapping) is False
    hidden = quote(KEY, safe="")[:-1] + "%" + format(ord(KEY[-1]), "02X")  # a known value, encoded
    assert _check(f"line {hidden} end", mapping) is False


def test_text_holding_only_placeholders_of_the_map_is_masked():
    mapping = _run_map()
    assert _check(" ".join(mapping), mapping) is True
    assert (
        _check(f"host {next(iter(mapping))} was down twice: {next(iter(mapping))}", mapping) is True
    )


def test_a_placeholder_that_is_not_in_the_map_is_masked():
    """Decision Q4 (F-review-1.md): the judge, evals and replay check with an empty map."""
    assert _check("host <IPV4_99> was down", _run_map()) is True
    assert runmap.is_masked("host <IPV4_1> and <SECRET_3>", {}) is True


def test_cleaning_alone_does_not_make_a_text_unmasked():
    """G0-I2: the rule never compares the texts (NUL removal and NFKC change a text without masking)."""
    mapping = _run_map()
    assert _check("café ＡＢＣ with a NUL\x00 inside", mapping) is True
    assert _check("a b\u200bc 50%25 done &amp; dusted", mapping) is True


def test_over_the_cap_raises_input_too_large_and_writes_nothing():
    mapping = _run_map()
    before = _frozen(mapping)
    with pytest.raises(runmap.InputTooLarge):
        runmap.is_masked("a" * (defaults.MAX_REDACT_CHARS + 1), mapping)
    with pytest.raises(runmap.InputTooLarge):  # the cap is on the work: NFKC expands U+FDFA to 18
        runmap.is_masked("ﷺ" * (defaults.MAX_REDACT_CHARS // 4), mapping)
    assert _frozen(mapping) == before


def test_nested_too_deep_raises_too_deep():
    deep = "%41" + KEY[1:]
    for _ in range(defaults.SCRUB_MAX_LAYERS + 2):
        deep = quote(deep, safe="")
    mapping = _run_map()
    with pytest.raises(runmap.TooDeep):
        _check(deep, mapping)


def test_a_failing_redactor_raises_redaction_error_and_never_returns_true(monkeypatch):
    """G0-I6: fail closed. The error names a type, never the text."""

    def boom(*args, **kwargs):
        raise ValueError(f"leaky {TOKEN}")

    monkeypatch.setattr(runmap, "redact", boom)
    with pytest.raises(runmap.RedactionError) as caught:
        runmap.is_masked("anything", {})
    assert caught.value.args == ("ValueError",)
    assert caught.value.__cause__ is None and TOKEN not in repr(caught.value)


def test_the_redactor_gets_a_private_copy_of_the_cache_never_the_callers(monkeypatch):
    """Kills 'pass the caller's cache': no redact() call made by is_masked gets the run's cache object,
    and the warm state is reused (the copy holds the same built objects)."""
    seen = []
    real = runmap.redact

    def spy(text, **kwargs):
        seen.append(kwargs.get("_cache"))
        return real(text, **kwargs)

    monkeypatch.setattr(runmap, "redact", spy)
    mapping = _run_map()
    seen.clear()
    assert _check(f"plain and \\u0041 escaped {IP} and 10.9.9.9", mapping) is False
    assert seen and all(c is not None and c is not mapping.redact_cache for c in seen)
    assert seen[0]["map"] != mapping.redact_cache["map"]  # the private copy took the scan's writes
    seen.clear()
    assert _check("nothing here", mapping) is True
    assert seen[0]["state"] is mapping.redact_cache["state"]  # reused, not rebuilt


def test_a_plain_dict_and_a_run_map_give_the_same_answer():
    for text, expected in [
        ("", True),
        ("plain", True),
        ("<IPV4_1> down", True),
        (f"{IP} down", False),
    ]:
        plain, run = {"<IPV4_1>": IP}, runmap.RunMap({"<IPV4_1>": IP})
        for mapping in (plain, run, {}, runmap.RunMap()):
            result = runmap.is_masked(text, mapping)
            assert isinstance(result, bool)
            assert result is expected
        assert (
            plain == {"<IPV4_1>": IP} and dict(run) == {"<IPV4_1>": IP} and run.redact_cache == {}
        )


# --- correction 2 of the G review: the placeholder COUNT is not enough ----------------------------------------------
UUID_A = "3f2b8c1e-9a4d-4e7b-8c21-" + "5d6e7f8a9b0c"
UUID_B = "7a1c9e2d-4b3f-4c8a-9d10-" + "1e2f3a4b5c6d"


def test_a_placeholder_plus_more_text_whose_whole_value_is_already_in_the_map_is_not_masked():
    """A real fail-open under the count rule (verified 2026-11-20): the redactor swaps `<UUID_1>.rest` for
    the placeholder of the whole value; the map does not grow and the count stays 1."""
    mapping = runmap.RunMap()
    runmap.redact_text(f"id {UUID_A} password={UUID_A}.more77", mapping)
    text = "password=<UUID_1>.more77"
    assert _held_count(text) == 1
    probe = runmap.RunMap(mapping)
    swapped = runmap.redact_text(text, probe)
    assert (
        probe == mapping and _held_count(swapped) == 1 and "more77" not in swapped
    )  # the count rule's blind spot
    assert _check(text, mapping) is False


def test_two_placeholders_that_merge_into_one_are_not_masked():
    """A real fail-open under the count rule (`<=`): the count goes DOWN from 2 to 1, the map is equal."""
    mapping = runmap.RunMap()
    runmap.redact_text(f"ids {UUID_A} {UUID_B} password={UUID_A}-{UUID_B}x9", mapping)
    text = "password=<UUID_1>-<UUID_2>x9"
    probe = runmap.RunMap(mapping)
    merged = runmap.redact_text(text, probe)
    assert probe == mapping and _held_count(text) == 2 and _held_count(merged) == 1
    assert _check(text, mapping) is False
    assert _check(merged, mapping) is True


def _held_count(text: str) -> int:
    return len(runmap.PLACEHOLDER.findall(text))


def test_it_accepts_a_read_only_mapping():
    from types import MappingProxyType

    frozen = MappingProxyType({"<IPV4_1>": IP})
    assert runmap.is_masked("host <IPV4_1> down", frozen) is True
    assert runmap.is_masked(f"host {IP} down", frozen) is False


def test_fail_before_the_same_texts_through_redact_text_do_change_the_map():
    """FAIL-BEFORE: redact_text, the only function before G0, rewrites the map for the same inputs."""
    for text in [
        f"password={TOKEN}",
        f"line {HIDDEN['percent-encoding']} end",
        "peer 10.9.9.9 refused",
    ]:
        checked, written = {}, {}
        assert runmap.is_masked(text, checked) is False and checked == {}
        runmap.redact_text(text, written)
        assert written != {}
    mapping = _run_map()
    cache_map = dict(mapping.redact_cache["map"])
    runmap.redact_text("peer 10.9.9.9 refused", mapping)
    runmap.redact_text("again", mapping)
    assert mapping.redact_cache["map"] != cache_map  # and redact_text does write the cache


# --- G0-I3: the round trip, over the secret shapes the redact tests already use -----------------------------------

FILLER = [
    "ERROR",
    "upstream",
    "refused",
    "retry",
    "at",
    "from",
    "deploy",
    "ok",
    "line",
    "café",
    "50%",
]
VALUES = [
    KEY,
    f"password={TOKEN}",
    f"api_key={TOKEN}x",
    IP,
    "10.9.9.9",
    "10.0.0.6",
    "user_id=abc123",
    "ops@example.com",
    "http://10.0.0.5/health",
]
LAYERS = [
    lambda s: s,
    lambda s: s,
    lambda s: quote(s, safe=""),
    lambda s: s[0] + "\u200b" + s[1:],
    lambda s: f"\\u{ord(s[0]):04x}" + s[1:],
    lambda s: f"&#{ord(s[0])};" + s[1:],
    lambda s: chr(ord(s[0]) + 0xFEE0) + s[1:] if s[0].isalnum() else s,
]


def _random_text(rng: random.Random) -> str:
    parts = []
    for _ in range(rng.randint(1, 8)):
        if rng.random() < 0.5:
            parts.append(rng.choice(FILLER))
        else:
            parts.append(rng.choice(LAYERS)(rng.choice(VALUES)))
    return rng.choice([" ", " ", "\n", "; "]).join(parts)


@pytest.mark.parametrize("untrusted", [False, True], ids=["redact_text", "redact_untrusted"])
def test_round_trip_what_redact_text_returns_is_masked(untrusted):
    """After `x = redact_text(t, m)`, `is_masked(x, m)` is True; and whenever `is_masked(t, m)` is True,
    `redact_text(t, m)` leaves m equal. A seeded loop (hypothesis is not installed)."""
    rng = random.Random(20261120)  # noqa: S311 - a test fixture generator, not a secret
    redact = runmap.redact_untrusted if untrusted else runmap.redact_text
    mapping = runmap.RunMap()
    failures = []
    for i in range(300):
        if i % 25 == 0:
            mapping = runmap.RunMap()  # a fresh run now and then: small and large maps both
        text = _random_text(rng)
        was_masked = runmap.is_masked(text, mapping)
        before = dict(mapping)
        out = redact(text, mapping)
        if was_masked and not untrusted and dict(mapping) != before:
            failures.append(("masked, yet the map grew", i))
        if not _check(out, mapping):
            failures.append(("the output is not masked", i))
        if not _check(out, runmap.RunMap(mapping)):
            failures.append(("the output is not masked for an equal map", i))
    assert failures == []  # indexes only: a failing text is never printed
