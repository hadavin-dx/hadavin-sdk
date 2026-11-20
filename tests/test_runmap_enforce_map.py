"""`runmap.enforce_map`: replace the values a run map already holds, and nothing else (ORDER 007; the mask step
of the model gate). Added to guard/runmap.py for step F; the replace itself is the redactor's own sweep."""

from __future__ import annotations

import copy
import importlib
import sys
import threading
from types import MappingProxyType, SimpleNamespace

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

redact_module = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # `guard.redact` the name is the function

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
    """enforce_map with its promises asserted on every call: map and cache untouched, a str, idempotent
    (`enforce_map(enforce_map(x)) == enforce_map(x)`). Every test of this file that gets a text back goes
    through here; the only direct calls are the ones that must raise and the reader threads of the smoke test."""
    before = dict(mapping)
    cache = copy.copy(getattr(mapping, "redact_cache", None))
    out = runmap.enforce_map(text, mapping)
    assert isinstance(out, str)
    assert dict(mapping) == before
    if cache is not None:
        assert mapping.redact_cache == cache and all(
            mapping.redact_cache[k] is cache[k] for k in cache
        )
    assert runmap.enforce_map(out, mapping) == out, "enforce_map is not idempotent"
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
    assert _enforce(f"host {IP}", frozen) == "host <IPV4_1>"


def test_a_value_added_to_the_map_later_is_replaced_in_text_masked_earlier():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(f"alert: session ref abc123, upstream {IP}", mapping)
    assert "abc123" in doc and _enforce(doc, mapping) == doc
    runmap.redact_untrusted("ERROR user_id=abc123 refused", mapping)
    assert _enforce(doc, mapping) == "alert: session ref <TENANT_1>, upstream <IPV4_1>"


def test_over_the_cap_raises_input_too_large():
    """The enforce step has its own cap (E1): the redaction cap times the growth factor."""
    with pytest.raises(runmap.InputTooLarge):
        runmap.enforce_map("a" * (runmap.ENFORCE_MAX_CHARS + 1), {})
    assert _enforce("a" * defaults.MAX_REDACT_CHARS, {}) == "a" * defaults.MAX_REDACT_CHARS


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


def test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders():
    """Trap 3, closed by G9 (E10). `abcd` and `cdef` are both known and the text holds `abcdef`: neither contains the other, so the sweep
    replaces one and the other's rest stood readable (`<SECRET_1>ef`, `ab<SECRET_2>`: the stated limit pinned here before G9). The text read
    back with the map's placeholders put back still holds the other value across the placeholder; the gate may not add an entry, so the
    readable rest is replaced by the EXISTING placeholder of the value that covers it: `<SECRET_1><SECRET_2>` whatever the map order. The map
    is not written (`_enforce` asserts it) and nothing readable is left. The same for an earlier call's output read with a value learned
    since. A held-back value is not in the main sweep's map, so its rest stays HERE; the gate's net finds it (`held_value_left`)."""
    assert (
        _enforce("abcdef", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("abcdef", {"<SECRET_2>": "cdef", "<SECRET_1>": "abcd"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("abcdefg", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdefg"}) == "<SECRET_1><SECRET_2>"
    )
    assert (
        _enforce("x <SECRET_1>ef y", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
        == "x <SECRET_1><SECRET_2> y"
    )
    # two identifiers: each is touched by a letter of the other, so NEITHER is replaced in the overlap, and read back neither stands alone
    identifiers = {"<TENANT_1>": "abcd", "<TENANT_2>": "cdef"}
    assert _enforce("abcdef", identifiers) == "abcdef"
    # ... while each standalone copy still is
    assert _enforce("abcdef abcd cdef", identifiers) == "abcdef <TENANT_1> <TENANT_2>"
    # the held-back value `SECRET_1` (8 characters) loses to the shorter `ET_1zz9` (7) in the sweep; the net sees the rest
    held_back = {"<SECRET_1>": "SECRET_1", "<SECRET_2>": "ET_1zz9"}
    assert _enforce("SECRET_1zz9", held_back) == "SECR<SECRET_2>"
    assert runmap.held_value_left("SECR<SECRET_2>", runmap.snapshot(held_back))
    assert _enforce("SECRET_1 zz9", held_back) == "<SECRET_1> zz9"


def test_trap3_an_overlap_of_two_identifiers_is_masked_with_their_placeholders():
    """G9, L-D1 (CHANGED in G9 v3, design M4): a readable character covered only by an identifier is replaced by that identifier's EXISTING
    placeholder: no refusal (v2 refused the text, and which pair refused depended on the map order), the map is not written. Restored,
    the shared part of the two identifiers appears twice (a stated limit of the gate, model_gate's docstring). A secret and an identifier
    give the same text in either map order."""
    identifiers = {"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"}
    assert _enforce("acme-prod-01-eu", identifiers) == "<TENANT_1><TENANT_2>"
    assert _enforce("acme-prod-01 and prod-01-eu", identifiers) == "<TENANT_1> and <TENANT_2>"
    for m in (
        {"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"},
        {"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"},
    ):
        assert _enforce("x ab-cd-ef y", m) == "x <SECRET_1><TENANT_1> y", m


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
        out = runmap.enforce_map(text, mapping)
        assert out != text  # something was replaced: the patterns were built
        assert runmap.enforce_map(out, mapping) == out
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
        ({"<SECRET_1>": "web"}, "x web y"),
        ({"<TENANT_1>": "12345"}, "x 12345 y"),
        ({"<IPV4_1>": "8080"}, "port 8080 open"),
        ({"<TENANT_1>": "admin"}, "x admin y"),
        ({"<TENANT_1>": "Admin"}, "x Admin y"),
        ({"<HOSTNAME_1>": "web"}, "the web tier"),
    ]
    for mapping, text in not_swept:
        assert _enforce(text, mapping) == text, mapping
    swept = [
        ({"<SECRET_1>": "abc"}, "x abc y", "x <SECRET_1> y"),
        ({"<SECRET_1>": "12345"}, "x 12345 y", "x <SECRET_1> y"),  # a secret of 4+: digits do not exempt it
        ({"<SECRET_1>": "admin"}, "x admin y sysadmin", "x <SECRET_1> y sys<SECRET_1>"),  # nor a common word
        ({"<TENANT_1>": "123456"}, "x 123456 y", "x <TENANT_1> y"),
        ({"<TENANT_1>": "abc"}, "x abc y", "x <TENANT_1> y"),
    ]  # fmt: skip
    for mapping, text, expected in swept:
        assert _enforce(text, mapping) == expected, mapping


def test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept():
    """`redact._replace_standalone`: an identifier is replaced only where no ASCII letter or digit touches
    it. An underscore, a dash, a dot or a letter outside ASCII beside it does not protect it. A PHONE value: only
    a digit beside it protects it (ticket G8, `redact._joins`)."""
    mapping = {"<TENANT_1>": "abc123"}
    assert _enforce("xabc123 abc1234 9abc123 abc123z", mapping) == "xabc123 abc1234 9abc123 abc123z"
    assert (
        _enforce("abc123_ -abc123- .abc123. \u00e9abc123", mapping)
        == "<TENANT_1>_ -<TENANT_1>- .<TENANT_1>. \u00e9<TENANT_1>"
    )
    assert _enforce("x123456 1234567", {"<TENANT_1>": "123456"}) == "x123456 1234567"
    phone = "415" + "555" + "0132"
    assert (
        _enforce(f"build{phone} x{phone}_ 7{phone}", {"<PHONE_1>": phone})
        == f"build<PHONE_1> x<PHONE_1>_ 7{phone}"
    )
    secret = {"<SECRET_1>": TOKEN}  # a secret is replaced in every copy
    assert _enforce(f"x{TOKEN}9", secret) == "x<SECRET_1>9"


# --- lead review round 2 --------------------------------------------------------------------------------------------

IDENT = "abc123" + "xyz9"  # an identifier value, built from parts
SHORT = "Zq" + "9x"  # a short secret value, built from parts


def _one_sweep(text: str, mapping: dict[str, str]) -> str:
    """What enforce_map returned before the fix: the redactor's sweep, once."""
    return runmap._Redactor(mapping, None).sweep(text)


def test_mj2_an_identifier_glued_to_a_shorter_secret_is_replaced_too():
    """MJ2, the reviewer's trace. One sweep skips the identifier (the secret's first letter touches it),
    then replaces the secret: the identifier is left raw and standing alone. Reproduced 2026-11-20 on the
    code before the fix: the first call returned `abc123xyz9<SECRET_1>`, a second `<TENANT_1><SECRET_1>`."""
    mapping = {"<TENANT_1>": IDENT, "<SECRET_1>": SHORT}
    once = _one_sweep(IDENT + SHORT, mapping)
    assert once == IDENT + "<SECRET_1>"  # FAIL-BEFORE: one sweep is not a fixed point
    assert _one_sweep(once, mapping) == "<TENANT_1><SECRET_1>"
    out = _enforce(IDENT + SHORT, mapping)
    assert out == "<TENANT_1><SECRET_1>", "a known identifier was left raw beside a placeholder"
    assert IDENT not in out and SHORT not in out
    assert _enforce(IDENT + SHORT, runmap.RunMap(mapping)) == out  # the cached path
    assert _enforce(f"a {SHORT}{IDENT}{SHORT} b {IDENT}x", mapping) == (
        f"a <SECRET_1><TENANT_1><SECRET_1> b {IDENT}x"  # a letter that stays keeps the stated limit
    )
    # the same shape with a held-back value (a piece of a placeholder of the map) as the identifier
    late = {"<TENANT_1>": "SECRET", "<SECRET_1>": SHORT}
    assert _enforce("SECRET" + SHORT, late) == "<TENANT_1><SECRET_1>"


def _chain(n: int) -> tuple[dict[str, str], str]:
    """n identifiers glued in a row before a secret, the longest first, each ending in a dot: every sweep
    frees exactly one of them (the last one still glued to a raw neighbour), so n + 2 sweeps are needed."""
    names = ["t" + str(i) * (2 * (n - i) + 2) + "." for i in range(n)]
    mapping = {f"<TENANT_{i + 1}>": name for i, name in enumerate(names)}
    mapping["<SECRET_1>"] = SHORT
    return mapping, "".join(names) + SHORT


def test_mj2_a_chain_settles_within_the_cap_and_is_refused_past_it():
    """The sweep is repeated while the text changes, `ENFORCE_MAX_SWEEPS` times at most. A longer chain is
    refused (fail closed: the gate makes no call), never returned half replaced."""
    assert runmap.ENFORCE_MAX_SWEEPS == 4  # small and constant
    mapping, text = _chain(
        2
    )  # sweeps: the secret, identifier 2, identifier 1, then one that finds nothing
    assert _enforce(text, mapping) == "<TENANT_1><TENANT_2><SECRET_1>"
    for n in (3, 6):
        mapping, text = _chain(n)
        with pytest.raises(runmap.RedactionError) as caught:
            runmap.enforce_map(text, mapping)
        assert caught.value.args == ("NotSettled",), "a text that was still changing was returned"
        assert caught.value.__cause__ is None and not isinstance(caught.value, runmap.InputTooLarge)


def test_m_new_1_a_map_of_many_short_values_builds_one_redactor_and_none_per_value(monkeypatch):
    """m-new-1. A hostile document can plant many short values that are pieces of a placeholder token (`ID`,
    `1`, `T`, `_1`, `>`): the sweep never replaces them, so they are not held back, and a call costs one
    sweep with the run's built patterns, not one substring test and one redactor per value."""
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    pieces = ["ID", "T", "EN", "AN", "_", "<", ">", "<T", "1>"]
    for i in range(1, 2001):
        dict.__setitem__(
            mapping, f"<TENANT_{i}>", f"{pieces[i % len(pieces)]}{i}"[:2] if i % 2 else str(i)
        )
    assert (
        len(mapping) == 2001 and len(set(mapping.values())) < 2001
    )  # short, many of them the same
    runmap.redact_text("warm the cache", mapping)
    built = []
    real = runmap._Redactor

    def counting(known, cache=None, deadline=None):
        built.append((len(known), cache is not None))
        return real(known, cache, deadline)

    monkeypatch.setattr(runmap, "_Redactor", counting)
    monkeypatch.setattr(
        runmap, "ENFORCE_MAX_HELD", 10**6
    )  # the cap would hide what this test is about
    text = f"ID T EN 1 7 1999 host {IP} <TENANT_7>"
    assert _enforce(text, mapping) == "ID T EN 1 7 1999 host <IPV4_1> <TENANT_7>"
    assert set(built) == {(2001, True)}, "a redactor was built for a value the sweep never replaces"
    # a value the sweep CAN replace and that is a piece of a token is still held back (one redactor for it)
    dict.__setitem__(mapping, "<SECRET_1>", "TENANT")
    built.clear()
    assert _enforce(f"TENANT host {IP}", mapping) == "<SECRET_1> host <IPV4_1>"
    assert sorted(set(built)) == [(1, True), (2001, True)]


def test_m_new_1_enforce_map_has_the_redactors_time_budget(monkeypatch):
    """m-new-1, ORDER 007 item 3: past `defaults.REDACT_BUDGET_S` the call fails closed (InputTooLarge)."""
    mapping = {"<IPV4_1>": IP}
    clock = iter([0.0, defaults.REDACT_BUDGET_S + 0.5])
    fake_time = SimpleNamespace(monotonic=lambda: next(clock), thread_time=lambda: 0.0)
    monkeypatch.setattr(runmap, "time", fake_time)
    # the redactor reads its own `time`: without this a pytest-xdist worker that has already used more than
    # REDACT_BUDGET_S of CPU makes the second call below fail on the real thread clock (flaky under -n)
    monkeypatch.setattr(redact_module, "time", fake_time)
    with pytest.raises(runmap.InputTooLarge) as caught:
        runmap.enforce_map(f"host {IP}", mapping)
    assert caught.value.args == ("InputTooLarge",), "the time budget was not checked"
    clock = iter([0.0, defaults.REDACT_BUDGET_S - 0.5, defaults.REDACT_BUDGET_S - 0.4])
    assert runmap.enforce_map(f"host {IP}", mapping) == "host <IPV4_1>"


def test_m_new_2_stated_limit_a_map_key_that_is_not_a_genuine_placeholder_is_not_protected():
    """m-new-2. The held-back test no longer asks for the shape of a genuine key (the `fullmatch` is gone):
    every sweepable value that is a piece of any key of the map is held back. Run 2026-11-20: that does NOT
    protect a key that is not a genuine placeholder (`<host_1>`, lower case), because no sweep sets such a
    token aside (`redact._PLACEHOLDER` is upper case only): the value `host` is replaced inside it, held
    back or not. STATED LIMIT: the placeholder is damaged, no raw value is shown, the result is stable.
    The redactor only ever writes genuine keys, so a run's own map does not have this shape."""
    mapping = {"<host_1>": IP, "<acct_2>": "host"}
    out = _enforce(f"a {IP} b host c", mapping)
    assert out == "a <<acct_2>_1> b <acct_2> c"
    assert IP not in out
    genuine = {"<HOST_1>": IP, "<ACCT_2>": "HOST"}  # the same map with genuine keys is protected
    assert _enforce(f"a {IP} b HOST c", genuine) == "a <HOST_1> b <ACCT_2> c"


def test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced():
    """m-new-3. The sweep sets every placeholder-shaped token aside first, so such a value never lies in one
    stretch of text. (The redactor stores a value that holds placeholders with them restored, so its own
    entries do not have this shape; a seeded or foreign map can.)"""
    mapping = {"<SECRET_1>": "ab<X_1>cd9", "<IPV4_1>": IP}
    assert _enforce(f"see ab<X_1>cd9 at {IP}", mapping) == "see ab<X_1>cd9 at <IPV4_1>"


def test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder():
    """m-new-3. `ABC_1` is known; written as `<ABC_1>` it has the shape of a placeholder and is left."""
    mapping = {"<TENANT_1>": "ABC_1", "<SECRET_1>": TOKEN}
    assert _enforce("id <ABC_1> and ABC_1", mapping) == "id <ABC_1> and <TENANT_1>"
    assert (
        _enforce(f"<{TOKEN}>", mapping) == "<<SECRET_1>>"
    )  # not token-shaped: replaced as anywhere


def test_stated_limit_a_copy_split_by_nul_characters_is_not_found():
    """m-new-3. enforce_map does not clean the text (`redact_text` does): a copy with a NUL between its
    characters, which is what a UTF-16 document read as UTF-8 holds, passes as written."""
    mapping = {"<SECRET_1>": TOKEN, "<IPV4_1>": IP}
    split = chr(0).join(TOKEN)
    assert _enforce(f"token {split} end", mapping) == f"token {split} end"
    as_read = TOKEN.encode("utf-16-le").decode("utf-8", "replace")
    assert TOKEN not in as_read and _enforce(as_read, mapping) == as_read
    assert (
        _enforce(f"{TOKEN}{chr(0)}{IP}", mapping) == f"<SECRET_1>{chr(0)}<IPV4_1>"
    )  # whole copies are


def test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass():
    """E2 (design review cb-M3). Reproduced 2026-11-20 on the plain sweep: the value `hunter2pass` is replaced,
    then the value `>abc` is found ACROSS the end of the placeholder just written: `<SECRET_1<SECRET_2>`. No raw
    value is shown, but the put-back breaks. Fixed in `enforce_map`: a value that begins with the tail of a
    placeholder (or ends with the head of one) is held back and swept after, when placeholders are set aside."""
    first, second = "hunter2" + "pass", ">abc"
    mapping = {"<SECRET_1>": first, "<SECRET_2>": second}
    assert (
        _one_sweep(first + "abc " + second, mapping) == "<SECRET_1<SECRET_2> <SECRET_2>"
    )  # FAIL-BEFORE
    out = _enforce(first + "abc " + second, mapping)
    assert out == "<SECRET_1>abc <SECRET_2>" and "<SECRET_1<" not in out, (
        "a placeholder was cut open"
    )
    # mirror: a value ending with the head of a placeholder
    tail = "xyz<"
    mirror = {"<SECRET_1>": first, "<SECRET_2>": tail}
    assert (
        _one_sweep("xyz" + first + " " + tail, mirror) == "<SECRET_2>SECRET_1> <SECRET_2>"
    )  # FAIL-BEFORE
    assert _enforce("xyz" + first + " " + tail, mirror) == "xyz<SECRET_1> <SECRET_2>"
    # the value is still replaced where it stands on its own, in both shapes
    assert _enforce(f"a {second} b {first}", mapping) == "a <SECRET_2> b <SECRET_1>"
    assert _enforce(f"a {tail} b {first}", mirror) == "a <SECRET_2> b <SECRET_1>"
    # longer shapes: the tail of a long key, the head of a long key
    long_tail = {"<SECRET_1>": first, "<SECRET_2>": "ECRET_1>q9"}
    assert _enforce(first + "q9 ECRET_1>q9", long_tail) == "<SECRET_1>q9 <SECRET_2>"
    head = {"<SECRET_1>": first, "<SECRET_2>": "zz<SEC"}
    assert _enforce("zz" + first + " zz<SEC", head) == "zz<SECRET_1> <SECRET_2>"


def test_e2_the_edge_value_stays_stable_with_the_cached_path_and_a_runmap():
    first = "hunter2" + "pass"
    mapping = runmap.RunMap({"<SECRET_1>": first, "<SECRET_2>": ">abc"})
    assert _enforce(first + "abc >abc", mapping) == "<SECRET_1>abc <SECRET_2>"


def test_e1_the_growth_factor_covers_the_longest_placeholder():
    """The factor of `ENFORCE_GROWTH_FACTOR` is derived, not guessed: a value is replaced from 3 characters
    on, and the longest placeholder the redactor writes is `<` + its longest label + `_` + 5 digits + `>`."""
    redact = importlib.import_module("hadavin_sdk.guard.redact")
    longest = max(len(label) for label in redact._LABELS) + len("<_99999>")
    assert longest / 3 <= runmap.ENFORCE_GROWTH_FACTOR, longest
    assert runmap.ENFORCE_MAX_CHARS == runmap.ENFORCE_GROWTH_FACTOR * defaults.MAX_REDACT_CHARS
    assert runmap.ENFORCE_MAX_OUT_CHARS == runmap.ENFORCE_GROWTH_FACTOR * runmap.ENFORCE_MAX_CHARS


def test_e1_a_document_near_the_cap_of_short_values_is_not_refused_after_masking():
    """E1 (design review cb-M2), the real producer path. `redact_untrusted` on about 0.9 of the cap of repeated
    `1.1.1.1 ` returns a text LONGER than the cap (each 8 characters become `<IPV4_1> `: 9). The gate used to
    apply the redaction cap to that text and refused it on every call (FAIL-BEFORE: `_within_cap`)."""
    n = int(defaults.MAX_REDACT_CHARS * 0.9)
    text = ("1.1.1.1 " * (n // 8 + 1))[:n]
    mapping = runmap.RunMap()
    produced = runmap.redact_untrusted(text, mapping)
    assert (
        len(produced) > defaults.MAX_REDACT_CHARS
    )  # masking made it longer than the redaction cap
    with pytest.raises(runmap.InputTooLarge):
        runmap._within_cap(produced)  # what the gate did before: a false refusal
    try:
        enforced = runmap.enforce_map(produced, mapping)
    except runmap.InputTooLarge:
        raise AssertionError("a document near the cap was refused after masking") from None
    assert enforced == produced  # byte-identical, nothing refused
    # raw copies in a text of that size are replaced too
    raw = "peer 1.1.1.1 " * (n // 13)
    out = _enforce(raw, mapping)
    assert "1.1.1.1" not in out and out.count("<IPV4_1>") == n // 13


def test_e1_the_enforce_cap_is_a_hard_bound():
    mapping = {"<IPV4_1>": IP}
    over = "x" * (runmap.ENFORCE_MAX_CHARS + 1)
    with pytest.raises(runmap.InputTooLarge) as caught:
        runmap.enforce_map(over, mapping)
    assert caught.value.args == ("InputTooLarge",) and caught.value.__cause__ is None
    assert (
        runmap.enforce_map("x" * runmap.ENFORCE_MAX_CHARS, mapping)
        == "x" * runmap.ENFORCE_MAX_CHARS
    )


def test_e1_a_sweep_that_grows_past_the_output_bound_is_refused(monkeypatch):
    monkeypatch.setattr(runmap, "ENFORCE_MAX_OUT_CHARS", 20)
    with pytest.raises(runmap.InputTooLarge):
        runmap.enforce_map(f"{IP} {IP} {IP}", {"<IPV4_1>": IP})


def test_e5_one_original_under_two_placeholders_follows_the_stronger_rule():
    """E5. The redactor keeps the first placeholder's rule for an original held twice. An identifier kind
    listed first made the copy glued to a letter pass although the same value is a secret kind below it."""
    value = "Zq9x" + "Lm4w"
    mapping = {"<TENANT_1>": value, "<SECRET_1>": value}
    assert _one_sweep(f"a{value}b", mapping) == f"a{value}b"  # FAIL-BEFORE: the weaker rule won
    out = _enforce(f"a{value}b {value}", mapping)
    assert out == "a<SECRET_1>b <SECRET_1>" and value not in out, "the weaker rule won"
    swapped = {"<SECRET_1>": value, "<TENANT_1>": value}
    assert _enforce(f"a{value}b", swapped) == "a<SECRET_1>b"


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


def test_m4_smoke_a_reader_thread_never_sees_a_known_key_missing_during_many_writes():
    """SMOKE TEST, not a proof: it depends on thread timing and can pass with the fault present. The
    certain checks are `test_m4_redact_text_never_empties_the_map_on_the_way` (deterministic) and mutant R3
    of tests/gate_mutants.py, which is pinned to that test. The gate reads the run's live map from another thread (k1b runs the call in a thread). While one
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


# --- review round 2, code reviewer M4: the snapshot is consistent while the writer is between two writes ----------


class _HookedCache(dict):
    """The redactor writes `cache["map"]` and then `cache["state"]`, and the run's map is updated after both
    (`redact_text`). A reader in between sees the NEW cache map with the OLD map and state: the deterministic case
    a probabilistic thread test cannot pin."""

    def __init__(self, on_map) -> None:
        super().__init__()
        self.on_map = on_map

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        if key == "map":
            self.on_map()


def test_r2_m4_a_reader_between_the_cache_write_and_the_map_update_sees_a_whole_snapshot():
    mapping = runmap.RunMap()
    runmap.redact_text(f"host {IP}", mapping)
    seen: list[str] = []
    mapping.redact_cache = _HookedCache(
        lambda: seen.append(runmap.enforce_map(f"host {IP} token {TOKEN}", mapping))
    )
    runmap.redact_text(f"password={TOKEN}", mapping)  # the writer: learns TOKEN
    assert seen, "the hook did not run"
    # TOKEN is not in the map yet at that moment: only the old value is replaced, nothing is half built or raw-old
    assert seen[0] == f"host <IPV4_1> token {TOKEN}"
    mapping.redact_cache = {}
    assert runmap.enforce_map(f"host {IP} token {TOKEN}", mapping) == (
        "host <IPV4_1> token <SECRET_1>"
    )


# --- round 4 (design review round 3 M1, M2, M3; code review round 3 M2, N7) ----------------------------------------


def test_r3_m2_the_calls_deadline_is_passed_into_every_sweep_of_the_redactor(monkeypatch):
    """Design M2: `_Redactor.sweep(out, deadline)` takes a `time.thread_time()` value; `enforce_map` gives it the
    budget's CPU deadline, for the main sweep and nothing else is unchecked."""
    seen: list[object] = []
    real = runmap._Redactor.sweep

    def spy(self, out, deadline=None):
        seen.append(deadline)
        return real(self, out, deadline)

    monkeypatch.setattr(runmap._Redactor, "sweep", spy)
    mapping = _run_map()
    snap = runmap.snapshot(mapping)
    assert runmap.enforce_map(f"host {IP}", snap) == "host <IPV4_1>"
    assert seen and all(isinstance(d, float) and d == snap.budget.cpu_deadline for d in seen[-1:])
    assert snap.budget.cpu_deadline <= __import__("time").thread_time() + defaults.REDACT_BUDGET_S


def test_r3_m2_a_deadline_already_past_stops_the_sweep_itself(monkeypatch):
    monkeypatch.setattr(
        runmap.EnforceBudget, "check", lambda self: None
    )  # only the sweep can refuse
    mapping = _run_map()
    monkeypatch.setattr(runmap.defaults, "REDACT_BUDGET_S", -1.0)
    with pytest.raises(runmap.InputTooLarge):
        runmap.enforce_map(f"host {IP} and more text", mapping)


def test_r3_m2_the_map_is_capped_at_snapshot_with_a_code_not_a_hang(monkeypatch):
    monkeypatch.setattr(runmap, "ENFORCE_MAX_ENTRIES", 5)
    five = runmap.RunMap({f"<IPV4_{i}>": f"10.0.0.{i + 10}" for i in range(1, 6)})
    assert runmap.snapshot(five)
    five["<IPV4_6>"] = "10.0.0.99"
    with pytest.raises(runmap.InputTooLarge):
        runmap.snapshot(five)
    with pytest.raises(runmap.InputTooLarge):
        runmap.enforce_map("text", five)


def test_r3_m2_late_is_the_old_definition_in_one_pass():
    """`late` (held back): the sweep replaces it and it is a piece of a key or an edge value. The old test was
    `original in "\\n".join(keys)` per value; the new one dismisses a value by its characters first and looks each
    spelling up once. Same result on a mixed map, with a non-ASCII value whose FOLDED spelling is a piece of a key."""
    mapping = {
        "<SECRET_1>": "ECRET_1",  # piece of a key
        "<SECRET_2>": TOKEN,  # not
        "<SECRET_3>": ">abcdef",  # edge (head)
        "<SECRET_4>": "xyz<",  # edge (tail)
        "<TENANT_1>": "UUID_1",  # piece of a key
        "<TENANT_2>": "abc123",
        "<TENANT_3>": "\uff34\uff25\uff2e\uff21\uff2e\uff34",  # full-width TENANT: its fold is a piece
        "<SECRET_5>": "ab",  # never swept (under 3)
        "<UUID_1>": "ID_1>",  # edge and piece of a key
    }
    tokens = "\n".join(mapping)
    from hadavin_sdk.guard.redact import _sweep

    old = {
        ph
        for ph, original in mapping.items()
        if (original in tokens or runmap._is_edge_value(original))
        and _sweep(ph, original) is not None
    }
    new = set(runmap._late_values(mapping))
    assert new == old | {"<TENANT_3>"}, "only the alias rule may add to the old definition"


def test_r3_m1_one_step_per_text_and_per_value_that_occurs_not_per_held_value():
    """Design M1: the steps of a call are one per text and one per held-back value that really occurs in a text."""
    mapping = runmap.RunMap({f"<SECRET_{i}>": f"ECRET_{i}>x" for i in range(1, 301)})
    mapping["<IPV4_1>"] = IP
    snap = runmap.snapshot(mapping)
    start = snap.budget.steps
    for _ in range(50):
        try:
            out = runmap.enforce_map(f"host {IP}", snap)
        except runmap.InputTooLarge:
            raise AssertionError(
                "a step was spent per held-back value: the budget ran out"
            ) from None
        assert out == "host <IPV4_1>"
    assert start - snap.budget.steps <= 50 * 2, "a step was spent per held-back value"
    before = snap.budget.steps
    assert runmap.enforce_map("a ECRET_7>x b", snap) == "a <SECRET_7> b"
    assert 1 <= before - snap.budget.steps <= 4


def test_r3_m2_a_built_state_kept_in_the_callers_holder_is_reused_and_the_runs_cache_is_not_written(
    monkeypatch,
):
    builds: list[int] = []
    real = runmap._Redactor._build

    def counting(self):
        builds.append(len(self.mapping))
        return real(self)

    monkeypatch.setattr(runmap._Redactor, "_build", counting)
    mapping = runmap.RunMap({"<IPV4_1>": IP, "<SECRET_1>": TOKEN, "<SECRET_2>": "ECRET_1>x"})
    holder: dict = {}
    runmap.snapshot(mapping, holder)
    assert set(holder) == {"first", "check"} and mapping.redact_cache == {}
    assert sorted(builds) == [
        2,
        2,
    ]  # the main sweep (the held-back value left out), the net's finder (2 secrets)
    builds.clear()
    runmap.snapshot(mapping, holder)
    assert builds == [], "the state was not reused: the redactors had to build"
    mapping["<IPV4_2>"] = "10.0.0.6"
    runmap.snapshot(mapping, holder)
    assert builds == [3] and holder["first"][0] == {
        "<IPV4_1>": IP,
        "<SECRET_1>": TOKEN,
        "<IPV4_2>": "10.0.0.6",
    }
    builds.clear()
    runmap.snapshot(mapping)  # no holder: nothing is kept, so it builds again
    assert builds, "a call with no holder reused something"


def test_r3_c_m2_a_non_ascii_value_and_its_folded_spelling_do_not_cut_each_others_placeholder():
    """Code review round 3, M2 (reproduced: `a <<TENANT_1>_1> b <TENANT_1> c`): the redactor sweeps the folded
    spelling of a non-ASCII value in the same pass, and a spelling that is a piece of the value's own placeholder
    cut it. Each spelling of a held-back value is its own item now, longest first."""
    wide = "\uff34\uff25\uff2e\uff21\uff2e\uff34"  # full-width TENANT
    mapping = runmap.RunMap({"<TENANT_1>": wide})
    assert _enforce(f"a {wide} b TENANT c", mapping) == "a <TENANT_1> b <TENANT_1> c"
    wide_word = "\uff33\uff25\uff23\uff32\uff25\uff34"  # full-width SECRET
    mapping = runmap.RunMap({"<SECRET_1>": wide_word})
    assert _enforce(f"a {wide_word} b SECRET c", mapping) == "a <SECRET_1> b <SECRET_1> c"


def test_r3_n7_stated_limit_digits_of_any_script_count_as_digits_and_as_placeholder_digits():
    """Code review round 3, N7: `str.isdigit()` and `\\d` take digits of every script. The limit text says 'all
    digits': that means Arabic-Indic and full-width digits too. A value of such digits under 6 characters is never
    swept as an identifier, and `<NAME_` followed by such a digit and `>` is placeholder-shaped (set aside)."""
    arabic = "\u0661\u0662\u0663\u0664"  # four Arabic-Indic digits
    mapping = runmap.RunMap({"<TENANT_1>": arabic, "<TENANT_2>": "1234"})
    assert _enforce(f"id {arabic} and 1234", mapping) == f"id {arabic} and 1234"
    shaped = "<XYZW_\u0663>"
    mapping = runmap.RunMap({"<SECRET_1>": "XYZW_\u0663"})
    assert (
        _enforce(f"see {shaped}", mapping) == f"see {shaped}"
    )  # the sweep sets it aside (the gate's net refuses)
