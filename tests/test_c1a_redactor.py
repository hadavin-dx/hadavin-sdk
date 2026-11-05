"""C1a: the redactor kind (MaskSession, RedactionError, RegexRedactor) and its wiring (table, config, hash, lint).

Modules added by C1a are imported INSIDE each test, so on the base commit every test fails on its own (FAIL-BEFORE)
and not at collection. Fake secrets only: example.com, an IBAN from the public examples, keys built from parts.
This file holds ASCII only: other characters are written as \\u escapes.
"""

from __future__ import annotations

import copy
import pickle
import random
import sys
import threading
import time
import traceback
from collections import ChainMap, UserDict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import MappingProxyType

import pytest
import yaml

from tests.conftest import make_cfg, qualify

IBAN = "GB82WEST12345698765432"  # the public example IBAN
KEY = "sk-" + "a" * 30
# The hash `config_hash` gave the fixture agent on main 6608146, before C1a: a qualified.jsonl line made then.
OLD_FIXTURE_HASH = "3ac5b7c34e7a0d7750a75adcd4642364be70af601e8078ee6b46c0dfb0f1be9e"
# REGEX_VERSION -> sha256 over the whole source of guard/redact.py and guard/redactor.py (regex_fingerprint()).
# Any edit of either file changes it: bump REGEX_VERSION and add the new row. That includes core PR #50's changes
# to redact.py. This is intended: a changed masking rule means every agent needs a new gate run.
PINNED = {
    "2": "cf49c02575a87cb77eccd28dbb7f0b27255bfbe16217614989e60f207645b5b4",
}


def kit():
    from hadavin_sdk.guard.redactor import MaskSession, RedactionError, RegexRedactor

    return RegexRedactor(), MaskSession(), RedactionError


def _redact_mod():
    """guard.redact the module (guard/__init__ exports a function of the same name)."""
    import hadavin_sdk.guard.redactor  # noqa: F401 - loads both modules

    return sys.modules["hadavin_sdk.guard.redact"]


def code_of(fn, *args) -> str:
    from hadavin_sdk.guard.redactor import RedactionError

    with pytest.raises(RedactionError) as info:
        fn(*args)
    return info.value.code


# ------------------------------------------------------------------------------------------ input rules

BAD_BYTES = [
    b"hello\x00world",
    b"%PDF-1.7\n1 0 obj",
    b"\x89PNG\r\n\x1a\n....",
    b"\xff\xd8\xff\xe0\x00\x10JFIF",
    b"GIF89a\x01\x00",
    b"GIF87a\x01\x00",
    b"PK\x03\x04\x14\x00",
    b"caf\xe9 invoice",  # cp1252, not UTF-8
    b"\xff\xfe\xfa",
    b"\x80",
    b"\xef\xbb\xbf%PDF-1.7",  # a BOM in front of a signature
    b"\xef\xbb\xbf\xef\xbb\xbf\x89PNG",
]
BAD_TEXT = [
    "text with a lone surrogate \ud800",
    "%PDF-1.7 pasted as text",
    "NUL \x00 inside",
    "\ufeff%PDF-1.7 behind a BOM",
    "\ufeff\ufeffPK\x03\x04",
]


@pytest.mark.parametrize("raw", BAD_BYTES, ids=lambda x: repr(x)[:24])
def test_unsupported_bytes_refused_by_decode_input_and_by_mask(raw):
    from hadavin_sdk.guard.redactor import decode_input

    r, s, _ = kit()
    assert code_of(decode_input, raw) == "unsupported_input"
    assert (
        code_of(r.mask, raw, s) == "unsupported_input"
    )  # mask takes str: bytes go through decode_input first
    assert code_of(r.find, raw) == "unsupported_input"
    assert s.counts == {}  # nothing was learned from a refused input


@pytest.mark.parametrize("raw", [*BAD_TEXT, 12345, None, ["a"]], ids=lambda x: repr(x)[:24])
def test_unsupported_text_refused(raw):
    r, s, _ = kit()
    assert code_of(r.mask, raw, s) == "unsupported_input"
    assert code_of(r.find, raw) == "unsupported_input"
    assert s.counts == {}


def test_bom_is_stripped_once_or_twice_and_utf8_accepted():
    from hadavin_sdk.guard.redactor import decode_input

    r, s, _ = kit()
    assert decode_input("\ufeff\ufeffhello caf\u00e9".encode()) == "hello caf\u00e9"
    assert decode_input("\ufeffhi") == "hi"
    assert r.mask("\ufeff\ufeffhello", s) == "hello"


def test_oversize_refused_before_decoding_or_encoding():
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor, decode_input

    r, s = RegexRedactor(max_doc_chars=100), MaskSession()
    assert len(r.mask("a " * 50, s)) == 100  # exactly at the cap is accepted
    assert code_of(r.mask, "a " * 50 + "b", s) == "too_large"
    assert code_of(r.find, "a " * 50 + "b") == "too_large"
    assert code_of(decode_input, b"a " * 50 + b"b", 100) == "too_large"
    assert code_of(decode_input, b"x " * 1000, 100) == "too_large"
    big = (
        "\ud800" * 101
    )  # too large AND not encodable: the size is judged first (no encode of a huge string)
    assert code_of(r.mask, big, s) == "too_large"


def test_token_and_line_caps_are_settings_and_refuse():
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor

    r, s = RegexRedactor(max_token_chars=10, max_line_chars=25), MaskSession()
    assert (
        r.mask("a" * 10 + " " + "b" * 10, s) == "a" * 10 + " " + "b" * 10
    )  # a line of 21, tokens of 10
    assert code_of(r.mask, "a" * 11, s) == "too_large"
    assert code_of(r.mask, "a b " * 7, s) == "too_large"  # a line of 28
    assert (
        r.mask("a b " * 6 + "\n" + "a b " * 6, s) == "a b " * 6 + "\n" + "a b " * 6
    )  # two lines of 24
    assert code_of(r.find, "a" * 11) == "too_large"


def test_cap_defaults_match_between_settings_and_module():
    from hadavin_sdk.backends.table import RegexRedactorSettings
    from hadavin_sdk.guard import redactor as mod

    s = RegexRedactorSettings(kind="regex")
    assert (s.max_doc_chars, s.max_token_chars, s.max_line_chars, s.max_session_values) == (
        mod.DEFAULT_MAX_DOC_CHARS,
        mod.DEFAULT_MAX_TOKEN_CHARS,
        mod.DEFAULT_MAX_LINE_CHARS,
        mod.DEFAULT_MAX_SESSION_VALUES,
    )
    assert (s.max_token_chars, s.max_line_chars) == (8192, 20_000)


def test_session_value_cap_refuses_without_absorbing():
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor

    r, s = RegexRedactor(max_session_values=3), MaskSession()
    assert (
        r.mask("a1@example.com a2@example.com a3@example.com", s) == "<EMAIL_1> <EMAIL_2> <EMAIL_3>"
    )
    assert code_of(r.mask, "a4@example.com", s) == "too_large"
    assert s.counts == {"EMAIL": 3}
    assert r.mask("a1@example.com again", s) == "<EMAIL_1> again"  # the session still works


def _units(n: int = 190_000) -> dict[str, str]:
    def rep(unit: str) -> str:
        return (unit * (n // len(unit) + 1))[:n]

    return {
        "equals": "=" * n,
        "dashes": "-" * n,
        "spaces": " " * n,
        "equals_spaced": rep("= "),
        "equals_word": rep("=" * 2000 + " "),
        "dash_digits": rep("1-" * 1000 + " "),
        "password_equals": rep("password" + "=" * 2000 + " "),
        "emails": " ".join(f"u{i}@example.com" for i in range(5000)),
        "ibans": " ".join(f"GB82WEST1234569876{i:04d}" for i in range(5000)),
        "comb": " ".join("a" * i + "Z" for i in range(1, 600))[:n],
        "curl": rep("curl "),
        "redis-cli": rep("redis-cli "),
        "mysql -p": rep("mysql -p"),
        "docker login": rep("docker login "),
        "htpasswd": rep("htpasswd "),
        "ldap": rep("ldap"),
        "cookie:[": rep("cookie:[ "),
        "a.": rep("a."),
        "a-": rep("a-"),
        "a+": rep("a+"),
        "=a": rep("=a"),
        "eq8000": rep("=" * 8000 + " "),
        "dash8000": rep("1-" * 4000 + " "),
        "dot8000": rep("a." * 4000 + " "),
        "plus8000": rep("a+" * 4000 + " "),
    }


def _wrapped(text: str, width: int = 19_990) -> str:
    return "\n".join(text[i : i + width] for i in range(0, len(text), width))


# Stated budget for one 190,000-character shape on a slow CI runner. Measured on the laptop: 0 to 16 s.
BUDGET_S = 60.0


@pytest.mark.parametrize("shape", sorted(_units()))
def test_redos_bounded_time_and_only_too_large_refuses(shape):
    """Each shape, as one line (over the line cap: must be refused as too_large at once) and wrapped into lines
    under the cap (must be masked, or refused as too_large, inside the budget). Any other code is a failure."""
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    text = _units()[shape]
    assert len(text) <= 190_000
    for variant in (text, _wrapped(text)):
        t0 = time.perf_counter()
        try:
            out = r.mask(variant, s)
            r.check(out, s)
        except RedactionError as exc:
            assert exc.code == "too_large", exc.code
        assert time.perf_counter() - t0 < BUDGET_S


def test_unwrapped_long_line_is_refused_at_once():
    r, s, _ = kit()
    t0 = time.perf_counter()
    assert code_of(r.mask, "curl " * 38_000, s) == "too_large"
    assert code_of(r.mask, "=" * 190_000, s) == "too_large"
    assert time.perf_counter() - t0 < 2


def test_many_distinct_values_in_a_full_document_bounded():
    r, s, _ = kit()
    text = "\n".join(f"u{i}@example.com GB82WEST1234569876{i:04d}" for i in range(4000))[:200_000]
    t0 = time.perf_counter()
    out = r.mask(text, s)
    assert time.perf_counter() - t0 < BUDGET_S
    assert sum(s.counts.values()) >= 4000
    assert "example.com" not in out


# ------------------------------------------------------------------------------------------ marks


def test_forged_and_foreign_marks_refused():
    r, s, _ = kit()
    assert code_of(r.mask, "hello <EMAIL_9>", s) == "forged_mark"  # never issued
    assert code_of(r.mask, "<CUSTOM_1> and text", s) == "forged_mark"
    other = kit()[1]
    foreign = r.mask("write to bob@example.com", other)  # issued by ANOTHER session
    assert foreign == "write to <EMAIL_1>"
    assert code_of(r.mask, foreign, s) == "forged_mark"
    assert s.counts == {}


@pytest.mark.parametrize(
    "text",
    [
        "<\x1b[0mEMAIL_9>",
        "<EMAIL_9\x1b[0m>",
        "<\x1b]0;title\x07EMAIL_9>",
        "<\x1b[0mEMAIL_1>",  # EMAIL_1 IS issued, but the token only exists once the escape is stripped
        "<EMAIL_1\x1b[0m>",
    ],
    ids=lambda t: repr(t)[:30],
)
def test_marks_hidden_behind_escape_sequences_are_forged(text):
    r, s, _ = kit()
    assert r.mask("first@example.com", s) == "<EMAIL_1>"
    assert code_of(r.mask, text, s) == "forged_mark"
    assert s.counts == {"EMAIL": 1}


def test_output_never_carries_a_mark_the_session_did_not_issue():
    import re

    from hadavin_sdk.guard import redactor as mod

    r, s, _ = kit()
    for text in ("<EMAIL\u200b_9> zero width inside a mark", "<EMAIL_\u2060 9>", "x <EMAIL%5F9> y"):
        out = r.mask(text, s)
        assert not re.search(r"<[A-Z][A-Z0-9]*_\d+>", out)  # inert text, not a mark
    assert mod.REGEX_VERSION == "2"


def test_final_output_is_rescanned_for_unissued_marks(monkeypatch):
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    r.mask("keep@example.com", s)
    before = s._snapshot()
    real = _redact_mod()._Redactor.sweep

    def planting(self, out):
        return real(self, out) + " <EMAIL_77>"

    monkeypatch.setattr(_redact_mod()._Redactor, "sweep", planting)
    with pytest.raises(RedactionError) as info:
        r.mask(
            "dropped@example.com", s
        )  # the engine places EMAIL_2 before the rescan refuses the output
    assert info.value.code == "forged_mark"
    assert s._snapshot() == before  # nothing was absorbed
    monkeypatch.undo()
    assert (
        r.mask("new@example.com", s) == "<EMAIL_2>"
    )  # the engine was reset: numbering intact, no gap


def test_mark_next_to_raw_value_still_masked():
    r, s, _ = kit()
    assert r.mask("dave@example.com", s) == "<EMAIL_1>"
    out = r.mask("<EMAIL_1> and carol@example.com", s)
    assert "carol" not in out and "example.com" not in out
    assert out == "<EMAIL_1> and <EMAIL_2>"


def test_marks_are_stable_and_append_only():
    r, s, _ = kit()
    a = r.mask("bob@example.com then ann@example.com", s)
    b = r.mask("ann@example.com, bob@example.com and new@example.com", s)
    assert a == "<EMAIL_1> then <EMAIL_2>"
    assert b == "<EMAIL_2>, <EMAIL_1> and <EMAIL_3>"
    assert s.counts == {"EMAIL": 3}


def test_value_in_a_later_text_is_masked_by_the_earlier_mark():
    r, s, _ = kit()
    r.mask(f"key {KEY}", s)
    assert r.mask(f"again {KEY}", s) == "again <APIKEY_1>"
    assert r.mask(f"zz{KEY}qq", s) == "zz<APIKEY_1>qq"  # a secret: every copy, glued or not


def test_cross_session_marks_are_a_caller_invariant():
    """The mark text is fixed (<KIND_n>), so it carries no session identity. Two sessions that issued the same number
    for different values cannot be told apart. This test documents the limit; C1b must keep one session per run
    (BL-core-c1a-004)."""
    r, a, _ = kit()
    b = kit()[1]
    r.mask("alice@example.com", a)
    r.mask("zed@example.com", b)
    assert (
        r.mask("<EMAIL_1> hi", b) == "<EMAIL_1> hi"
    )  # accepted, and now means a different value in a and b
    assert a._snapshot()["<EMAIL_1>"] != b._snapshot()["<EMAIL_1>"]


# ------------------------------------------------------------------------------------------ dict keys


@dataclass
class _Box:
    inner: object


def test_mark_and_pii_keys_refused_everywhere():
    from pydantic import BaseModel

    from hadavin_sdk.guard.redactor import RedactionError, refuse_unsafe_keys

    class Model(BaseModel):
        payload: dict

    refuse_unsafe_keys(
        {"fine": {"also": [1, {"ok": "<EMAIL_1> as a VALUE is not a key"}]}, "n": None}
    )
    bad = {
        "mark": {"<EMAIL_1>": 1},
        "nested": {"a": {"b": [{"<IBAN_3>": 2}]}},
        "list": [{"x": 1}, {"<PHONE_1>": 0}],
        "pii": {"jane.doe@example.com": 1},
        "pii nested": [{"a": ({"b": {IBAN: 1}},)}],
        "proxy": MappingProxyType({"jane.doe@example.com": 1}),
        "userdict": UserDict({"<EMAIL_1>": 1}),
        "chainmap": ChainMap({"ok": 1}, {"jane.doe@example.com": 1}),
        "bytes key": {b"jane.doe@example.com": 1},
        "tuple key": {("jane.doe@example.com", 1): 1},
        "ansi mark": {"<\x1b[0mEMAIL_9>": 1},
        "dataclass": _Box({"jane.doe@example.com": 1}),
        "model": Model(payload={"jane.doe@example.com": 1}),
        "set and tuple": [frozenset({1, 2}), ({"<EMAIL_1>": 1},)],
    }
    for name, value in bad.items():
        with pytest.raises(RedactionError) as info:
            refuse_unsafe_keys(value)
        assert info.value.code in {"forged_mark", "unsupported_input"}, name
    assert code_of(refuse_unsafe_keys, {"<EMAIL_1>": 1}) == "forged_mark"
    assert code_of(refuse_unsafe_keys, {"jane.doe@example.com": 1}) == "unsupported_input"
    assert code_of(refuse_unsafe_keys, {b"\xff\xfe": 1}) == "unsupported_input"


def test_key_walk_survives_cycles_and_refuses_runaway_depth():
    from hadavin_sdk.guard.redactor import refuse_unsafe_keys

    loop: list = [{"ok": 1}]
    loop.append(loop)
    refuse_unsafe_keys(loop)  # returns: no infinite walk
    d: dict = {"a": 1}
    d["self"] = d
    refuse_unsafe_keys(d)
    deep: object = {"x": 1}
    for _ in range(150):
        deep = [deep]
    assert code_of(refuse_unsafe_keys, deep) == "too_large"


# ------------------------------------------------------------------------------------------ session


def test_session_is_private_and_cannot_be_copied():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    assert "bob" not in repr(s) and "example" not in repr(s)
    assert not hasattr(s, "mapping") and not hasattr(s, "__dict__")
    for fn in (
        pickle.dumps,
        copy.copy,
        copy.deepcopy,
        lambda x: x.__getstate__(),
        lambda x: (
            x.__reduce__()
        ),  # each guard on its own: they back each other up under pickle and copy
        lambda x: x.__copy__(),
        lambda x: x.__deepcopy__({}),
    ):
        with pytest.raises(TypeError):
            fn(s)
    assert s.issued("<EMAIL_1>") and not s.issued("<EMAIL_2>")


def test_session_refuses_to_renumber_or_reassign():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    assert s._absorb({"<EMAIL_1>": "someone-else@example.com"}) is False
    assert s._absorb({}) is False  # dropping a mark is a change too
    assert s._snapshot() == {"<EMAIL_1>": "bob@example.com"}
    assert s._absorb({"<EMAIL_1>": "bob@example.com", "<EMAIL_2>": "x@example.com"}) is True


def test_session_close_forgets_values_and_the_pattern_cache():
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    r.mask(
        "zed.person@example.com and zed.person@example.com_x", s
    )  # the glued copy is found by the sweep
    r.check("nothing here", s)  # builds the cache of originals in guard.redact
    redact = _redact_mod()
    assert redact._standalone.cache_info().currsize > 0
    s.close()
    assert redact._standalone.cache_info().currsize == 0
    assert s._snapshot() == {} and s.counts == {}
    r.check("zed.person@example.com", s)  # a closed session knows nothing
    with pytest.raises(RedactionError):
        r.mask("<EMAIL_1>", s)


def test_two_threads_with_colliding_new_values_get_distinct_marks(monkeypatch):
    redact = _redact_mod()
    real = redact._Redactor.find

    inside = {"now": 0, "max": 0}
    guard = threading.Lock()

    def slow(self, text):
        with guard:
            inside["now"] += 1
            inside["max"] = max(inside["max"], inside["now"])
        out = real(self, text)
        time.sleep(0.05)  # widens the window: two unlocked threads are inside together
        with guard:
            inside["now"] -= 1
        return out

    monkeypatch.setattr(redact._Redactor, "find", slow)
    r, s, _ = kit()
    barrier = threading.Barrier(2)
    results, errors = {}, []

    def work(name, text):
        barrier.wait()
        try:
            results[name] = r.mask(text, s)
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc).__name__ + ":" + getattr(exc, "code", ""))

    threads = [
        threading.Thread(target=work, args=("a", "alpha.one@example.com")),
        threading.Thread(target=work, args=("b", "beta.two@example.com")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert inside["max"] == 1  # the read-modify-write of the session is one critical section
    assert {results["a"], results["b"]} == {"<EMAIL_1>", "<EMAIL_2>"}
    snap = s._snapshot()
    assert (
        snap[results["a"]] == "alpha.one@example.com"
        and snap[results["b"]] == "beta.two@example.com"
    )
    assert s.counts == {"EMAIL": 2}


def test_eight_threads_fifty_values_each_no_crosstalk():
    r, s, _ = kit()
    errors, outs = [], {}
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            s.counts  # noqa: B018 - must never raise while others write
            r.check("nothing to find", s)
            time.sleep(
                0.01
            )  # a polite reader: the point is that it never sees a half-written session

    def work(t):
        try:
            for i in range(50):
                value = f"t{t}.v{i}@example.com"
                outs[(t, i)] = (value, r.mask(f"see {value} now", s))
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(getattr(exc, "code", exc)))

    watcher = threading.Thread(target=reader)
    watcher.start()
    threads = [threading.Thread(target=work, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stop.set()
    watcher.join()
    assert errors == []
    snap = s._snapshot()
    assert len(snap) == 400 and s.counts == {"EMAIL": 400}
    for value, out in outs.values():
        mark = out.removeprefix("see ").removesuffix(" now")
        assert snap[mark] == value  # every mark means the value it was handed out for


# ------------------------------------------------------------------------------------------ errors


def _frames_of(err):
    tb = err.__traceback__
    while tb is not None:
        yield tb.tb_frame
        tb = tb.tb_next


def _assert_no_raw_text(err, *needles):
    assert err.__cause__ is None and err.__context__ is None and err.__suppress_context__ is True
    for frame in _frames_of(err):
        if not frame.f_code.co_filename.replace(chr(92), "/").endswith("guard/redactor.py"):
            continue  # the test's own frame legitimately holds its inputs
        shown = repr(frame.f_locals)
        for needle in needles:
            assert needle not in shown, (frame.f_code.co_name, needle)


def test_redaction_error_carries_only_its_code():
    from hadavin_sdk.guard.redactor import CODES, RedactionError

    assert set(CODES) == {
        "unsupported_input",
        "too_large",
        "forged_mark",
        "self_check_failed",
        "internal",
    }
    assert RedactionError("made up").code == "internal"  # an unknown code cannot be carried
    r, s, _ = kit()
    secret = "carol@example.com"  # noqa: S105 - a fake address, not a password
    with pytest.raises(RedactionError) as info:
        r.mask(f"{secret} <EMAIL_7>", s)
    e = info.value
    assert (str(e), e.code, e.args) == ("forged_mark", "forged_mark", ("forged_mark",))
    assert secret not in repr(e) and secret not in str(e.args)
    assert "".join(traceback.format_exception(e)).count(secret) == 0


def test_every_raise_site_has_no_context_cause_or_raw_locals(monkeypatch):
    from hadavin_sdk.guard.redactor import RedactionError, decode_input, refuse_unsafe_keys

    secret = "carol.private@example.com"  # noqa: S105 - a fake address
    r, s, _ = kit()
    r.mask(f"known {secret}", s)
    cases = {
        "decode utf8": lambda: decode_input(b"\xff" + secret.encode()),
        "decode type": lambda: decode_input(object()),
        "decode surrogate": lambda: decode_input(secret + "\ud800"),
        "mask forged": lambda: r.mask(secret + " <EMAIL_9>", s),
        "mask unsupported": lambda: r.mask(secret + "\x00", s),
        "mask too large": lambda: r.mask(secret + " " + "a" * 300_000, s),
        "mask bytes": lambda: r.mask(secret.encode(), s),
        "check": lambda: r.check(f"leak {secret}", s),
        "find": lambda: r.find(secret + "\x00"),
        "keys": lambda: refuse_unsafe_keys({secret: 1}),
    }
    for call in cases.values():
        with pytest.raises(RedactionError) as info:
            call()
        _assert_no_raw_text(info.value, secret)
    redact = _redact_mod()

    def boom(self, text):
        raise ValueError(f"{secret} leaked in an exception message")

    monkeypatch.setattr(redact._Redactor, "find", boom)
    with pytest.raises(RedactionError) as info:
        r.mask(f"hello {secret}", s)
    assert info.value.code == "internal"
    _assert_no_raw_text(info.value, secret)
    assert secret not in "".join(traceback.format_exception(info.value))


def test_protocol_has_no_put_back():
    from hadavin_sdk.guard.redactor import Redactor, RegexRedactor

    r = RegexRedactor()
    assert isinstance(r, Redactor)
    assert (r.name, r.version) == ("regex", "2")
    assert not hasattr(r, "put_back") and "put_back" not in vars(Redactor)
    assert r.find(f"mail bob@example.com and {IBAN}") == ["EMAIL", "IBAN"]
    assert r.find("nothing sensitive here") == []


def test_public_api_is_small():
    from hadavin_sdk.guard import redactor as mod

    assert set(mod.__all__) == {
        "REGEX_VERSION",
        "MaskSession",
        "RedactionError",
        "Redactor",
        "RegexRedactor",
        "decode_input",
        "refuse_unsafe_keys",
    }


# ------------------------------------------------------------------------------------------ check


def test_check_finds_a_leftover_original():
    r, s, RedactionError = kit()
    masked = r.mask(f"bob@example.com {KEY} {IBAN}", s)
    assert masked == "<EMAIL_1> <APIKEY_1> <IBAN_1>"
    for leak in ("bob@example.com", KEY, IBAN, f"x {KEY}y"):
        with pytest.raises(RedactionError) as info:
            r.check(f"fine <EMAIL_1> {leak}", s)
        assert info.value.code == "self_check_failed"
    r.check("fine <EMAIL_1> and nothing else", s)  # and a clean text passes


def test_check_sees_a_value_planted_after_masking():
    r, s, RedactionError = kit()
    masked = r.mask("hello bob@example.com", s)
    with pytest.raises(RedactionError):
        r.check(masked + " " + "bob@example.com", s)  # a real check: the planted original is found


def test_check_is_case_sensitive_whole_token_and_four_plus_chars():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    r.check("BOB@EXAMPLE.COM", s)  # case-sensitive, like _sweep
    r.check("xbob@example.comy", s)  # an identifier must stand alone to count
    assert s._absorb(
        {**s._snapshot(), "<TENANT_1>": "abc"}
    )  # 3 characters: never required to be absent
    r.check("abc", s)
    assert s._absorb({**s._snapshot(), "<TENANT_2>": "abcd"})  # exactly 4: required
    assert code_of(r.check, "see abcd here", s) == "self_check_failed"
    r.check("see ABCD here", s)  # case-sensitive


def test_original_equal_to_mark_text_no_selfcheck_failure():
    # TENANT value "EMAIL_1" is the text inside the mark <EMAIL_1>; check must split on marks like _sweep does.
    r, s, _ = kit()
    masked = r.mask("tenant_id=EMAIL_1 and bob@example.com", s)
    assert masked == "tenant_id=<TENANT_1> and <EMAIL_1>"
    r.check(masked, s)
    assert r.mask(masked, s) == masked
    assert (
        code_of(r.check, "tenant is EMAIL_1 here", s) == "self_check_failed"
    )  # the bare original IS a leak


def test_check_failure_message_has_no_value():
    r, s, RedactionError = kit()
    r.mask("bob@example.com", s)
    with pytest.raises(RedactionError) as info:
        r.check("bob@example.com", s)
    assert "bob" not in repr(info.value) and "bob" not in str(info.value)


def test_check_cache_follows_the_mapping():
    r, s, _ = kit()
    r.check("anything", s)
    r.mask("late.one@example.com", s)  # the session grew after the last check
    assert code_of(r.check, "late.one@example.com", s) == "self_check_failed"


# ------------------------------------------------------------------------------------------ fuzz

_VALUES = (
    lambda rng, n: f"user{n}@example.com",
    lambda rng, n: ["GB82WEST12345698765432", "DE89370400440532013000", "NL91ABNA0417164300"][
        n % 3
    ],
    lambda rng, n: (
        "sk-" + "".join(rng.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(30))
    ),
    lambda rng, n: "4111 1111 1111 1111",
    lambda rng, n: f"10.{rng.randrange(256)}.{rng.randrange(256)}.{rng.randrange(1, 255)}",
)
_FILLER = [
    "hello",
    "order",
    "status",
    "pending",
    "refund",
    "invoice",
    "please",
    "check",
    "the",
    "amount",
    "again",
    "thanks",
]


def _case(rng: random.Random) -> tuple[str, list[str]]:
    parts, values = [], []
    for _ in range(rng.randrange(1, 12)):
        if rng.random() < 0.4:
            value = rng.choice(_VALUES)(rng, rng.randrange(6))
            values.append(value)
            parts.append(value)
        else:
            parts.append(rng.choice(_FILLER))
    return " ".join(parts), values


def _restore(masked: str, s) -> str:
    for mark, original in sorted(s._snapshot().items(), key=lambda kv: -len(kv[0])):
        masked = masked.replace(mark, original)
    return masked


def fuzz_corpus() -> list[tuple[str, list[str]]]:
    rng = random.Random(20261105)  # noqa: S311 - a repeatable test corpus
    return [_case(rng) for _ in range(1000)]


def test_fuzz_masking_oracle():
    """Oracle = documented coverage only: contiguous email, valid IBAN, card, API key, IPv4 are gone; the rest of
    the text is untouched (restoring the marks gives the source back); masking twice is a no-op; and a value
    planted back into the output is found by check."""
    from hadavin_sdk.guard.redactor import RedactionError

    t0 = time.perf_counter()
    r = kit()[0]
    planted = 0
    for text, values in fuzz_corpus():
        s = kit()[1]
        masked = r.mask(text, s)
        for v in values:
            assert v not in masked, (text, v)
        assert _restore(masked, s) == text
        assert r.mask(masked, s) == masked  # idempotent on this corpus
        if values and len(values[0]) >= 4:
            with pytest.raises(RedactionError):
                r.check(masked + " " + values[0], s)
            planted += 1
    assert planted > 300
    assert time.perf_counter() - t0 < 20


@pytest.mark.xfail(
    strict=True,
    reason="spaced IBAN is not masked by the regex kind (listed as NOT masked in the redactor.py docstring and the "
    "CHANGELOG). Expires 2027-02-01: by then the kind masks it or this xfail is replaced by a written decision.",
)
def test_spaced_iban_is_masked():
    r, s, _ = kit()
    masked = r.mask("pay GB82 WEST 1234 5698 7654 32 now", s)
    assert "GB82" not in masked and "WEST" not in masked


def test_spaced_iban_xfail_has_not_expired():
    assert datetime.now(UTC).date() < date(2027, 2, 1), (
        "decide the spaced IBAN: mask it, or write the decision down"
    )


def test_documented_misses_are_listed_in_the_module_docstring():
    from hadavin_sdk.guard import redactor as mod

    doc = " ".join(mod.__doc__.split())
    for phrase in (
        "spaced or lower-case or hyphenated IBAN",
        "names in free prose",
        "bob@example.com_x",
        "soft-hyphen",
        "%40",
        "&#64;",
        "base64",
        "full-width",
        "line-wrapped",
        "images and",
        "unsupported_input",
        "too_large",
        "split by the caller",
        "BL-core-c1a-004",
    ):
        assert phrase in doc, phrase


# ------------------------------------------------------------------------------------------ version pins


def test_any_source_change_forces_a_version_bump():
    from hadavin_sdk.guard.redactor import REGEX_VERSION, regex_fingerprint

    assert REGEX_VERSION in PINNED, "new REGEX_VERSION: add its fingerprint row to PINNED"
    assert regex_fingerprint() == PINNED[REGEX_VERSION], (
        "guard/redact.py or guard/redactor.py changed: bump REGEX_VERSION, then pin regex_fingerprint() (this "
        "includes core PR #50's changes to redact.py: intended, every agent needs a new gate run)"
    )


def test_fingerprint_covers_the_helpers_not_only_patterns_and_sweep(monkeypatch):
    import inspect

    from hadavin_sdk.guard import redactor as mod

    base = mod.regex_fingerprint()
    redact = _redact_mod()
    real = inspect.getsource

    def edited(helper_name):
        def fake(module):
            src = real(module)
            if module is redact:
                src = src.replace(helper_name, helper_name + "_x", 1)
            return src

        return fake

    for helper in (
        "_NOT_A_VALUE",
        "_KEPT_HOST",
        "def strip_ansi",
        "def _mask",
        "def find",
        "def sweep",
    ):
        monkeypatch.setattr(mod.inspect, "getsource", edited(helper))
        assert mod.regex_fingerprint() != base, helper
    monkeypatch.setattr(
        mod.inspect,
        "getsource",
        lambda m: real(m).replace("MAX_KEY_DEPTH = 100", "MAX_KEY_DEPTH = 99"),
    )
    assert mod.regex_fingerprint() != base
    monkeypatch.setattr(
        mod.inspect,
        "getsource",
        lambda m: real(m).replace("DEFAULT_MAX_TOKEN_CHARS = 8192", "DEFAULT_MAX_TOKEN_CHARS = 1"),
    )
    assert mod.regex_fingerprint() != base


# ------------------------------------------------------------------------------------------ wiring


def test_table_has_the_redactor_capability():
    from hadavin_sdk.backends.table import ALLOWED, DEFAULTS, TABLE

    caps = list(TABLE)
    assert caps.index("llm") < caps.index("redactor") < caps.index("detector")
    assert TABLE["redactor"]["regex"].neutral is True
    assert ALLOWED["redactor"] == frozenset()
    assert DEFAULTS["redactor"] == "regex"


def test_redactor_settings_and_factory(tmp_path):
    from pydantic import ValidationError

    from hadavin_sdk.backends import make
    from hadavin_sdk.config import ConfigError, parse_backends

    must = {
        "audit": {"kind": "local_dir", "dir": "a"},
        "llm": {"kind": "fake", "recorded_dir": "r"},
    }

    def parse(**extra):
        return parse_backends({**must, **extra}, tmp_path)

    default = parse()
    assert default.redactor.kind == "regex" and default.redactor.max_doc_chars == 200_000
    assert default.explicit == frozenset({"audit", "llm"}) and "redactor" not in default.explicit
    named = parse(
        redactor={
            "kind": "regex",
            "max_doc_chars": 50,
            "max_token_chars": 7,
            "max_line_chars": 9,
            "max_session_values": 4,
        }
    )
    assert "redactor" in named.explicit
    built = make("redactor", named.redactor)
    assert (
        built.name,
        built.max_doc_chars,
        built.max_token_chars,
        built.max_line_chars,
        built.max_session_values,
    ) == (
        "regex",
        50,
        7,
        9,
        4,
    )
    assert "redactor" in parse(redactor="regex").explicit
    with pytest.raises(ConfigError, match="unknown kind"):
        parse(redactor="other")
    for bad in (
        {"max_doc_chars": 0},
        {"max_doc_chars": 1_000_001},
        {"max_token_chars": 0},
        {"max_line_chars": -1},
        {"max_session_values": 0},
        {"typo": 1},
    ):
        with pytest.raises(ConfigError):
            parse(redactor={"kind": "regex", **bad})
    with pytest.raises(ValidationError):
        type(default.redactor)(kind="other")


def registry_of(root):
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    return load_registry(load_config(root))


def set_backends(root, **extra):
    path = root / "config.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["backends"].update(extra)
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")


def test_config_hash_changes_with_redactor_version(tmp_path, monkeypatch):
    from hadavin_sdk.guard.redactor import RegexRedactor

    reg = registry_of(make_cfg(tmp_path))
    h1 = reg.config_hash("test-agent")
    monkeypatch.setattr(RegexRedactor, "version", "3")
    assert reg.config_hash("test-agent") != h1
    monkeypatch.undo()
    assert reg.config_hash("test-agent") == h1


@pytest.mark.parametrize(
    "setting", ["max_doc_chars", "max_token_chars", "max_line_chars", "max_session_values"]
)
def test_config_hash_changes_with_non_default_redactor_settings(tmp_path, setting):
    base = registry_of(make_cfg(tmp_path / "a")).config_hash("test-agent")
    same = make_cfg(tmp_path / "b")
    set_backends(same, redactor={"kind": "regex"})  # named, but all defaults
    assert registry_of(same).config_hash("test-agent") == base
    other = make_cfg(tmp_path / "c")
    set_backends(other, redactor={"kind": "regex", setting: 1000})
    assert registry_of(other).config_hash("test-agent") != base


def test_old_qualified_line_rejected(tmp_path):
    from hadavin_sdk.runtime.agent_loop import Unqualified, assert_qualified

    reg = registry_of(make_cfg(tmp_path))
    qualify(reg)
    assert_qualified(reg, "test-agent")  # a line written now is accepted
    assert reg.config_hash("test-agent") != OLD_FIXTURE_HASH
    path = reg.config.root / "qualified.jsonl"
    path.write_text(
        path.read_text(encoding="utf-8").replace(reg.config_hash("test-agent"), OLD_FIXTURE_HASH),
        encoding="utf-8",
    )
    with pytest.raises(
        Unqualified
    ):  # a line from before masking is part of the hash needs one new gate run
        assert_qualified(reg, "test-agent")


def pilot_config(tmp_path, env="pilot", redactor=None):
    """The K3 pilot config (it names the redactor), with the redactor entry replaced or removed."""
    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(tmp_path, env=env)
    path = root / "config.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    del cfg["backends"]["redactor"]
    if redactor is not None:
        cfg["backends"]["redactor"] = redactor
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return root


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_pilot_config_without_redactor_refused(tmp_path, env):
    from hadavin_sdk.config import ConfigError, load_config

    with pytest.raises(ConfigError, match=r"redactor: not named"):
        load_config(pilot_config(tmp_path, env=env))


def test_pilot_config_with_redactor_named_loads(tmp_path):
    from hadavin_sdk.config import load_config

    cfg = load_config(pilot_config(tmp_path, redactor={"kind": "regex"}))
    assert "redactor" in cfg.backends.explicit
    cfg = load_config(pilot_config(tmp_path / "bare", redactor="regex"))
    assert cfg.backends.redactor.kind == "regex"


def test_dev_config_without_redactor_still_loads(tmp_path):
    from hadavin_sdk.config import load_config

    assert load_config(make_cfg(tmp_path)).backends.redactor.kind == "regex"


def write_contract_with(root, name="create_draft_record", **extra):
    path = root / "actions" / f"{name}.yaml"
    body = yaml.safe_load(path.read_text(encoding="utf-8"))
    body.update(extra)
    path.write_text(yaml.safe_dump(body), encoding="utf-8")


def test_contract_with_restorable_refused_until_c1f(tmp_path):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    write_contract_with(root, restorable={"to": ["EMAIL"]})
    with pytest.raises(ConfigError, match=r"restorable.*C1f"):
        registry_of(root)


def test_restorable_is_a_deferred_key_everywhere():
    from hadavin_sdk import deferred

    assert deferred.DEFERRED_KEYS["restorable"] == "ticket C1f"
    assert deferred.key_problems("agents.yaml", {"id": "a", "restorable": {}})
    assert deferred.key_problems("config.yaml", {"restorable": {}})


# ------------------------------------------------------------------------------------------ trusted-text lint

PROSE = [
    "Dear Customer,",
    "Customer name: as printed on the invoice",
    "Never repeat the password: say you cannot share it.",
    "The user id: the numeric id of the account holder.",
    "Pay no more than up to 999999999999 units.",
    "Write the amount, the currency and the supplier name.",
    "Answer in the language of the customer. Use the marks like <EMAIL_1> exactly as given.",
    "See https://docs.example.com/guide and host api.corp.internal for the manual.",
]
REAL = {
    "email": "Ask ops.lead@example.com about it.",
    "iban": f"Pay to {IBAN} only.",
    "apikey": f"Use the key {KEY} for the call.",
    "password value": "password: Zx9wq7Lm4pTv",
    "card": "Card 4111 1111 1111 1111 is a test card.",
}


def prompt_path(root):
    return root / "prompts" / "test-agent.md"


@pytest.mark.parametrize("line", PROSE)
def test_ordinary_prose_passes_the_lint(tmp_path, line):
    root = make_cfg(tmp_path)
    p = prompt_path(root)
    p.write_text(p.read_text(encoding="utf-8") + "\n" + line + "\n", encoding="utf-8")
    write_contract_with(root, description=line)  # create_draft_record is in scope
    registry_of(root)


@pytest.mark.parametrize("name", sorted(REAL))
def test_real_values_in_a_prompt_are_refused_with_file_and_line_but_not_the_text(tmp_path, name):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    p = prompt_path(root)
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text("\n".join([*lines, REAL[name]]) + "\n", encoding="utf-8")
    with pytest.raises(ConfigError) as info:
        registry_of(root)
    msg = str(info.value)
    assert (
        "test-agent" in msg and "prompts/test-agent.md" in msg and f"line {len(lines) + 1}" in msg
    )
    for fragment in ("ops.lead", "example.com", IBAN, KEY, "Zx9wq7Lm4pTv", "4111"):
        assert fragment not in msg


def test_contract_text_and_schema_with_pii_refused(tmp_path):
    from hadavin_sdk.config import ConfigError

    schema_enum = {
        "type": "object",
        "properties": {"to": {"type": "string", "enum": ["erin@example.com"]}},
    }
    schema_int = {
        "type": "object",
        "properties": {"n": {"type": "integer", "enum": [4111111111111111]}},
    }
    schema_named_pattern = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "enum": ["erin@example.com"]}
        },  # a property NAMED pattern
    }
    schema_default = {
        "type": "object",
        "properties": {"to": {"type": "string", "default": "erin@example.com"}},
    }
    for where, extra in (
        ("description", {"description": f"Pay to {IBAN} only."}),
        ("expected_outcome", {"expected_outcome": "a mail to dana@example.com exists"}),
        ("idempotency_header", {"idempotency_header": "X-Key-dana@example.com"}),
        ("input_schema", {"input_schema": schema_enum}),
        ("input_schema", {"input_schema": schema_int}),
        ("input_schema", {"input_schema": schema_named_pattern}),
        ("input_schema", {"input_schema": schema_default}),
    ):
        root = make_cfg(tmp_path / f"{where}-{len(list(tmp_path.iterdir()))}")
        write_contract_with(root, **extra)
        with pytest.raises(ConfigError, match=f"action create_draft_record: {where}") as info:
            registry_of(root)
        assert "example.com" not in str(info.value) and IBAN not in str(info.value)
        assert "4111111111111111" not in str(info.value)


def test_regex_pattern_keyword_in_schema_is_not_linted(tmp_path):
    root = make_cfg(tmp_path)
    write_contract_with(
        root,
        input_schema={
            "type": "object",
            "properties": {"to": {"type": "string", "pattern": "[a-z]+@example[.]com"}},
        },
    )
    registry_of(root)


def test_only_what_a_live_agent_can_use_is_linted(tmp_path):
    root = make_cfg(tmp_path)
    write_contract_with(
        root, name="send_email", description="Mail dana@example.com"
    )  # not in test-agent scope
    agents = yaml.safe_load((root / "agents.yaml").read_text(encoding="utf-8"))
    assert "send_email" not in agents[0]["scope_allowed"], (
        "fixture changed: pick a contract outside the scope"
    )
    registry_of(root)  # a contract no live agent can use is not read
    agents[0]["status"] = "draft"
    (root / "agents.yaml").write_text(yaml.safe_dump(agents), encoding="utf-8")
    prompt_path(root).write_text("Mail dana@example.com\n", encoding="utf-8")
    registry_of(root)  # a draft agent's prompt is not read


def test_bom_or_non_utf8_prompt_is_a_config_error(tmp_path):
    from hadavin_sdk.config import ConfigError

    for name, raw in (("bom", b"\xef\xbb\xbfYou help.\n"), ("latin1", b"You help. caf\xe9\n")):
        root = make_cfg(tmp_path / name)
        prompt_path(root).write_bytes(raw)
        with pytest.raises(ConfigError, match="prompts/test-agent.md") as info:
            registry_of(root)
        assert "UnicodeDecodeError" not in str(info.value)


def test_clean_fixture_config_passes_the_lint(tmp_path):
    registry_of(make_cfg(tmp_path))


def test_lint_kind_table():
    r = kit()[0]
    assert r.lint("a@example.com") == ["EMAIL"]
    assert r.lint("password: say") == [] and r.lint("password: Zx9wq7Lm4pTv") == ["SECRET"]
    assert (
        r.lint("host api.corp.internal ip 10.1.2.3 uuid 123e4567-e89b-12d3-a456-426614174000") == []
    )
    assert code_of(r.lint, b"bytes") == "unsupported_input"
