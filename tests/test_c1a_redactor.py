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
    "3": "b6f14928116966da993a5c97e2271a64db4261f44209654c1556c7fe04d48f39",
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


# Stated budget for one 190,000-character shape on a slow CI runner. Measured on the laptop: 0 to 16 s.
BUDGET_S = 60.0


def test_many_distinct_values_in_a_full_document_bounded():
    r, s, _ = kit()
    text = "\n".join(f"u{i}@example.com GB82WEST1234569876{i:04d}" for i in range(2000))[:200_000]
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


def test_final_output_is_rescanned_for_unissued_marks(monkeypatch):
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    r.mask("keep@example.com", s)
    before = s.snapshot()
    real = _redact_mod()._Redactor.sweep

    def planting(self, out):
        return real(self, out) + " <EMAIL_77>"

    monkeypatch.setattr(_redact_mod()._Redactor, "sweep", planting)
    with pytest.raises(RedactionError) as info:
        r.mask(
            "dropped@example.com", s
        )  # the engine places EMAIL_2 before the rescan refuses the output
    assert info.value.code == "forged_mark"
    assert s.snapshot() == before  # nothing was absorbed
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


# ------------------------------------------------------------------------------------------ dict keys


@dataclass
class _Box:
    inner: object


# ------------------------------------------------------------------------------------------ session


def test_session_refuses_to_renumber_or_reassign():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    assert s.absorb({"<EMAIL_1>": "someone-else@example.com"}) is False
    assert s.absorb({}) is False  # dropping a mark is a change too
    assert s.snapshot() == {"<EMAIL_1>": "bob@example.com"}
    assert s.absorb({"<EMAIL_1>": "bob@example.com", "<EMAIL_2>": "x@example.com"}) is True


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
    snap = s.snapshot()
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
    assert s.absorb(
        {**s.snapshot(), "<TENANT_1>": "abc"}
    )  # 3 characters: never required to be absent
    r.check("abc", s)
    assert s.absorb({**s.snapshot(), "<TENANT_2>": "abcd"})  # exactly 4: required
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
    for mark, original in sorted(s.snapshot().items(), key=lambda kv: -len(kv[0])):
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
        lambda m: real(m).replace("DEFAULT_MAX_TOKEN_CHARS = 1024", "DEFAULT_MAX_TOKEN_CHARS = 1"),
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
    monkeypatch.setattr(RegexRedactor, "version", "99")
    assert reg.config_hash("test-agent") != h1
    monkeypatch.undo()
    assert reg.config_hash("test-agent") == h1


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


def test_clean_fixture_config_passes_the_lint(tmp_path):
    registry_of(make_cfg(tmp_path))


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


def _wrapped(text: str, width: int) -> str:
    return "\n".join(text[i : i + width] for i in range(0, len(text), width))


# Stated budget for one 190,000-character shape on a slow CI runner. Measured on the laptop at the default limits:
# 0.9 s (ordinary text) to about 3.3 s (the worst shape). Documented in the redactor.py docstring and the CHANGELOG.
BUDGET_S = 20.0


@pytest.mark.parametrize("shape", sorted(_units()))
def test_redos_bounded_time_and_only_too_large_refuses(shape):
    """Each shape as one line (over the line cap: refused at once), wrapped into 9,990-character lines (over the work
    budget: refused, or processed) and into 300-character lines (processed). Only `too_large` is an acceptable
    refusal; any other code (internal, self_check_failed) is a failure; every call finishes inside the budget."""
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    text = _units()[shape]
    assert len(text) <= 190_000
    for variant in (text, _wrapped(text, 9_990), _wrapped(text, 300)):
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


# ====================================================================================== batch 3 (round-2 reviews)

ESC = "\x1b"
C1 = chr(0x9B)
NESTED = ESC + "[" + ESC + "[0m0m"  # one strip pass leaves ESC[0m behind
NESTED_C1 = C1 + C1 + "0m0m"


def test_cap_defaults_match_between_settings_and_module():
    from pydantic import ValidationError

    from hadavin_sdk.backends.table import RegexRedactorSettings
    from hadavin_sdk.guard import redactor as mod

    s = RegexRedactorSettings(kind="regex")
    got = (
        s.max_doc_chars,
        s.max_token_chars,
        s.max_line_chars,
        s.max_work,
        s.max_session_values,
        s.max_walk_items,
    )
    assert got == (
        mod.DEFAULT_MAX_DOC_CHARS,
        mod.DEFAULT_MAX_TOKEN_CHARS,
        mod.DEFAULT_MAX_LINE_CHARS,
        mod.DEFAULT_MAX_WORK,
        mod.DEFAULT_MAX_SESSION_VALUES,
        mod.DEFAULT_MAX_WALK_ITEMS,
    )
    assert got == (200_000, 1024, 10_000, 100_000_000, 5000, 20_000)
    for name, bound in mod.BOUNDS.items():  # the settings model enforces the same upper bounds
        RegexRedactorSettings(kind="regex", **{name: bound})
        with pytest.raises(ValidationError):
            RegexRedactorSettings(kind="regex", **{name: bound + 1})


@pytest.mark.parametrize("bad", [0, -1, True, "5", 1.5, 10**12])
def test_constructor_validates_every_limit(bad):
    from hadavin_sdk.config import ConfigError
    from hadavin_sdk.guard import redactor as mod

    for name in mod.BOUNDS:
        with pytest.raises(ConfigError, match=name):
            mod.RegexRedactor(**{name: bad})
    mod.RegexRedactor(**dict(mod.BOUNDS))  # the upper bounds themselves are fine


def test_work_budget_refuses_what_the_line_cap_alone_would_pass():
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor

    r, s = RegexRedactor(max_work=100), MaskSession()
    assert r.mask("a" * 10, s) == "a" * 10  # 10 squared = 100 = the budget
    assert code_of(r.mask, "a" * 11, s) == "too_large"
    assert code_of(r.mask, "\n".join(["abcde"] * 5), s) == "too_large"  # 5 lines of 25 = 125
    assert r.mask("\n".join(["abcde"] * 4), s) == "\n".join(["abcde"] * 4)  # 100


def test_full_session_refuses_before_any_pattern_runs(monkeypatch):
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor

    r, s = RegexRedactor(max_session_values=3), MaskSession()
    assert (
        r.mask("a1@example.com a2@example.com a3@example.com", s) == "<EMAIL_1> <EMAIL_2> <EMAIL_3>"
    )
    redact = _redact_mod()
    ran = []
    real = redact._Redactor.find
    monkeypatch.setattr(redact._Redactor, "find", lambda self, t: ran.append(1) or real(self, t))
    assert (
        code_of(r.mask, "a4@example.com", s) == "too_large"
    )  # a session at its limit refuses further masking
    assert ran == []  # decided before find/sweep
    assert s.counts == {"EMAIL": 3}
    big = RegexRedactor(max_session_values=3)
    s2 = MaskSession()
    assert (
        code_of(big.mask, " ".join(f"b{i}@example.com" for i in range(10)), s2) == "too_large"
    )  # and after
    assert s2.counts == {}


@pytest.mark.parametrize(
    "text",
    [
        "<\x1b[0mEMAIL_9>",
        "<EMAIL_9\x1b[0m>",
        "<\x1b]0;title\x07EMAIL_9>",
        "<\x1b[0mEMAIL_1>",  # EMAIL_1 IS issued, but the token only exists once the escape is removed
        "<EMAIL_1\x1b[0m>",
        "<EMAIL_9" + NESTED + ">",  # nested: one strip pass leaves ESC[0m
        "<EMAIL_1" + NESTED + ">",
        "<EMAIL_9" + NESTED_C1 + ">",
        "<EM" + ESC + "[" + ESC + "[" + ESC + "[0m0m0mAIL_9>",
    ],
    ids=lambda t: repr(t)[:34],
)
def test_marks_hidden_behind_escape_sequences_are_forged(text):
    r, s, _ = kit()
    assert r.mask("first@example.com", s) == "<EMAIL_1>"
    assert code_of(r.mask, text, s) == "forged_mark"
    assert s.counts == {"EMAIL": 1}


def test_nested_escapes_are_removed_to_a_fixpoint_and_masking_is_stable():
    r, s, _ = kit()
    for text in (
        "x" + NESTED + "y",
        "x" + NESTED_C1 + "y",
        ESC + "[" + ESC + "[" + ESC + "[0m0m0m tail",
        "AKIA"
        + NESTED
        + "IOSFODNN7EXAMPLE tail",  # a value split by an invisible escape is masked as one value
    ):
        out = r.mask(text, s)
        assert ESC not in out and C1 not in out
        assert r.mask(out, s) == out  # stable: a second pass changes nothing
    assert r.mask("AKIA" + NESTED + "IOSFODNN7EXAMPLE tail", s).endswith(" tail")
    assert "IOSFODNN7EXAMPLE" not in r.mask("AKIA" + NESTED + "IOSFODNN7EXAMPLE tail", s)
    deep = (ESC + "[") * 30 + "0m" * 30
    assert (
        code_of(r.mask, deep, s) == "unsupported_input"
    )  # more than MAX_STRIP_PASSES passes of nesting
    assert code_of(r.find, deep) == "unsupported_input"


def test_output_marks_all_issued_after_odd_inputs():
    import re

    r, s, _ = kit()
    zw = chr(0x200B)
    for text in (
        "<EMAIL" + zw + "_9> zero width inside a mark",
        "<EMAIL%5F9> percent",
        "&lt;EMAIL_9&gt; entity",
        "x <EMAIL_9" + chr(0xFF1E) + " full-width bracket",
    ):
        out = r.mask(text, s)
        assert not re.search(
            r"<[A-Z][A-Z0-9]*_\d+>", out
        )  # inert text, not a mark; C1b must not decode it either


def test_cross_session_marks_are_not_told_apart_c1b_must_not_share_sessions():
    """NOT a guard: the mark text carries no session identity (fixed shape <KIND_n>), so a foreign session's colliding
    mark is accepted. This test pins the limit so nobody mistakes the forged-mark check for session binding. The
    obligation is C1b's: one MaskSession per run context, never shared; contract test test_two_threads_two_runs_no_crosstalk."""
    r, a, _ = kit()
    b = kit()[1]
    r.mask("alice@example.com", a)
    r.mask("zed@example.com", b)
    assert r.mask("<EMAIL_1> hi", b) == "<EMAIL_1> hi"
    assert a.snapshot()["<EMAIL_1>"] != b.snapshot()["<EMAIL_1>"]


# ------------------------------------------------------------------------------------------ dict keys


def test_unsafe_keys_refused_everywhere():
    from pydantic import BaseModel

    from hadavin_sdk.guard.redactor import RedactionError, refuse_unsafe_keys

    class Model(BaseModel):
        payload: dict

    r = kit()[0]
    refuse_unsafe_keys(
        {"fine": {"also": [1, {"ok": "<EMAIL_1> as a VALUE is not a key"}]}, "n": None}, r
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
        "nested ansi mark": {"<EMAIL_9" + NESTED + ">": 1},
        "nested ansi key": {"AKIA" + NESTED + "IOSFODNN7EXAMPLE": 1},
        "dataclass": _Box({"jane.doe@example.com": 1}),
        "model": Model(payload={"jane.doe@example.com": 1}),
        "set and tuple": [frozenset({1, 2}), ({"<EMAIL_1>": 1},)],
    }
    for name, value in bad.items():
        with pytest.raises(RedactionError) as info:
            refuse_unsafe_keys(value, r)
        assert info.value.code in {"forged_mark", "unsupported_input"}, name
    assert code_of(refuse_unsafe_keys, {"<EMAIL_1>": 1}, r) == "forged_mark"
    assert code_of(refuse_unsafe_keys, {"<EMAIL_9" + NESTED + ">": 1}, r) == "forged_mark"
    assert code_of(refuse_unsafe_keys, {"jane.doe@example.com": 1}, r) == "unsupported_input"
    assert (
        code_of(refuse_unsafe_keys, {"AKIA" + NESTED + "IOSFODNN7EXAMPLE": 1}, r)
        == "unsupported_input"
    )
    assert code_of(refuse_unsafe_keys, {b"\xff\xfe": 1}, r) == "unsupported_input"


def test_uuid_ip_host_and_mac_keys_are_allowed():
    """Decision (BL-core-c1a-026): only mark-shaped keys and the lint kinds (PII, secrets) are refused; a tool result
    keyed by an id is normal and its VALUES are masked."""
    from hadavin_sdk.guard.redactor import refuse_unsafe_keys

    r = kit()[0]
    refuse_unsafe_keys(
        {
            "123e4567-e89b-12d3-a456-426614174000": 1,
            "10.1.2.3": 2,
            "api.corp.internal": 3,
            "00:1A:2B:3C:4D:5E": 4,
            "Customer": 5,
        },
        r,
    )


def test_many_models_each_checked_even_when_ids_are_reused():
    """A model_dump() result is a temporary; its id() can be reused by the next one. The walk keeps every object alive."""
    from pydantic import BaseModel

    from hadavin_sdk.guard.redactor import RedactionError, refuse_unsafe_keys

    class Model(BaseModel):
        payload: dict

    r = kit()[0]
    models = [Model(payload={f"k{i}": i}) for i in range(200)]
    models.insert(57, Model(payload={"jane.doe@example.com": 1}))
    with pytest.raises(RedactionError) as info:
        refuse_unsafe_keys(models, r)
    assert info.value.code == "unsupported_input"
    models = [Model(payload={"jane.doe@example.com": 1}), Model(payload={"a": 1})]
    with pytest.raises(RedactionError):
        refuse_unsafe_keys(models, r)
    for first in range(40):  # and with the email model in every position of a short list
        short = [Model(payload={"a": i}) for i in range(5)]
        short[first % 5] = Model(payload={"jane.doe@example.com": 1})
        with pytest.raises(RedactionError):
            refuse_unsafe_keys(short, r)


def test_objects_that_cannot_be_walked_are_refused_not_skipped():
    from hadavin_sdk.guard.redactor import refuse_unsafe_keys

    class Plain:
        def __init__(self):
            self.payload = {"jane.doe@example.com": 1}

    class PydanticV1Like:
        def dict(self):
            return {"jane.doe@example.com": 1}

    r = kit()[0]
    data = {"jane.doe@example.com": 1}
    for name, value in {
        "generator": (k for k in [data]),
        "iterator": iter([data]),
        "map": map(dict, [data]),
        "keys view": data.keys(),
        "values view": {"a": data}.values(),
        "items view": {"a": data}.items(),
        "plain class": Plain(),
        "v1-like model": PydanticV1Like(),
        "object": object(),
    }.items():
        assert code_of(refuse_unsafe_keys, value, r) == "unsupported_input", name


def test_key_walk_item_cap_and_configured_limits():
    from hadavin_sdk.guard.redactor import RegexRedactor, refuse_unsafe_keys

    r = RegexRedactor(max_walk_items=50)
    refuse_unsafe_keys({f"k{i}": i for i in range(40)}, r)
    assert code_of(refuse_unsafe_keys, {f"k{i}": i for i in range(100)}, r) == "too_large"
    assert code_of(refuse_unsafe_keys, [{} for _ in range(100)], r) == "too_large"
    small = RegexRedactor(
        max_doc_chars=10
    )  # the configured redactor's limits apply to bytes keys too
    assert code_of(refuse_unsafe_keys, {b"a" * 11: 1}, small) == "too_large"
    assert code_of(refuse_unsafe_keys, {"a" * 11: 1}, small) == "too_large"


def test_key_walk_survives_cycles_and_refuses_runaway_depth():
    from hadavin_sdk.guard.redactor import refuse_unsafe_keys

    r = kit()[0]
    loop: list = [{"ok": 1}]
    loop.append(loop)
    refuse_unsafe_keys(loop, r)  # returns: no infinite walk
    d: dict = {"a": 1}
    d["self"] = d
    refuse_unsafe_keys(d, r)
    deep: object = {"x": 1}
    for _ in range(150):
        deep = [deep]
    assert code_of(refuse_unsafe_keys, deep, r) == "too_large"


# ------------------------------------------------------------------------------------------ session


def test_session_public_api_for_a_second_kind():
    r, s, _ = kit()
    assert s.issue("EMAIL", "a@example.com") == "<EMAIL_1>"
    assert s.issue("EMAIL", "a@example.com") == "<EMAIL_1>"  # same value, same mark
    assert s.issue("EMAIL", "b@example.com") == "<EMAIL_2>"
    assert s.issue("IBAN", IBAN) == "<IBAN_1>"
    assert (s.original_of("<EMAIL_2>"), s.original_of("<EMAIL_9>")) == ("b@example.com", None)
    assert s.size == 3 and s.issued("<IBAN_1>")
    assert isinstance(s.snapshot(), dict) and s.absorb(
        {**s.snapshot(), "<EMAIL_3>": "c@example.com"}
    )
    # and the regex kind keeps working on a session another writer changed
    assert r.mask("a@example.com d@example.com", s) == "<EMAIL_1> <EMAIL_4>"
    assert s.lock is not s.exclusive and isinstance(s.cache, dict)


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
        lambda x: x.__copy__(),
        lambda x: x.__deepcopy__({}),
    ):
        with pytest.raises(TypeError):
            fn(s)
    assert s.issued("<EMAIL_1>") and not s.issued("<EMAIL_2>")


def test_close_forgets_originals_in_every_cache_poisons_the_session_and_is_a_context_manager():
    import re

    from hadavin_sdk.guard.redactor import MaskSession, RedactionError

    redact = _redact_mod()

    def in_re_cache(word):
        keys = [k for name in ("_cache", "_cache2") for k in getattr(re, name, {})]
        return any(word in str(k) for k in keys)

    r = kit()[0]
    with MaskSession() as s:
        r.mask("zedperson@example.com and zedperson@example.com_x", s)
        r.mask(
            "second.one@example.com", s
        )  # the sweep now compiles finders that hold the originals
        assert in_re_cache("zedperson") and redact._standalone.cache_info().currsize > 0
    assert s.closed
    assert not in_re_cache("zed.person") and redact._standalone.cache_info().currsize == 0
    assert s.snapshot() == {} and s.counts == {}
    for call in (
        lambda: r.mask("new@example.com", s),
        lambda: r.check("x", s),
        lambda: s.issue("EMAIL", "n@example.com"),
    ):
        with pytest.raises(
            RedactionError
        ) as info:  # no silent restart of the numbering: <EMAIL_1> would be someone else
            call()
        assert info.value.code == "internal"
    assert s.absorb({"<EMAIL_1>": "n@example.com"}) is False


def test_sessionless_calls_leave_no_originals_in_the_caches():
    import re

    from hadavin_sdk.guard.redactor import RedactionError, refuse_unsafe_keys

    redact = _redact_mod()
    r = kit()[0]

    def clean():
        keys = [k for name in ("_cache", "_cache2") for k in getattr(re, name, {})]
        return redact._standalone.cache_info().currsize == 0 and not any(
            "zedprivate" in str(k) for k in keys
        )

    text = "zedprivate@example.com tail zedprivate@example.com_x"
    r.find(text)
    assert clean(), "find"
    r.lint(text)
    assert clean(), "lint"
    with pytest.raises(RedactionError):
        refuse_unsafe_keys({"zedprivate@example.com": 1}, r)
    assert clean(), "refuse_unsafe_keys"


def test_check_counts_and_issued_do_not_wait_for_a_running_mask(monkeypatch):
    redact = _redact_mod()
    real = redact._Redactor.find
    inside, release = threading.Event(), threading.Event()

    def slow(self, text):
        out = real(self, text)
        inside.set()
        release.wait(5)
        return out

    monkeypatch.setattr(redact._Redactor, "find", slow)
    r, s, _ = kit()
    r.mask("known.one@example.com", s)
    worker = threading.Thread(target=lambda: r.mask("slow.two@example.com", s))
    worker.start()
    assert inside.wait(5)
    t0 = time.perf_counter()
    assert s.counts == {"EMAIL": 1} and s.issued("<EMAIL_1>") and s.size == 1
    r.check("nothing here", s)
    waited = time.perf_counter() - t0
    release.set()
    worker.join()
    assert (
        waited < 1.0
    )  # the mask was blocked inside find for up to 5 s; none of these waited for it
    assert s.counts == {"EMAIL": 2}


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
    assert inside["max"] == 1  # masks of one session run one after another (the numbering needs it)
    assert {results["a"], results["b"]} == {"<EMAIL_1>", "<EMAIL_2>"}
    snap = s.snapshot()
    assert (
        snap[results["a"]] == "alpha.one@example.com"
        and snap[results["b"]] == "beta.two@example.com"
    )
    assert s.counts == {"EMAIL": 2}


# ------------------------------------------------------------------------------------------ errors


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
        "mask closed": lambda: r.mask(secret, _closed_session()),
        "check": lambda: r.check(f"leak {secret}", s),
        "find": lambda: r.find(secret + "\x00"),
        "lint": lambda: r.lint(secret + "\x00"),
        "keys": lambda: refuse_unsafe_keys({secret: 1}, r),
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


def _closed_session():
    from hadavin_sdk.guard.redactor import MaskSession

    s = MaskSession()
    s.close()
    return s


def test_keyboard_interrupt_propagates_without_the_text_in_its_frames(monkeypatch):
    secret = "dave.private@example.com"  # noqa: S105 - a fake address
    redact = _redact_mod()

    def interrupt(self, text):
        raise KeyboardInterrupt

    monkeypatch.setattr(redact._Redactor, "find", interrupt)
    r, s, _ = kit()
    with pytest.raises(KeyboardInterrupt) as info:
        r.mask(f"hello {secret}", s)
    for frame in _frames_of(info.value):
        if frame.f_code.co_filename.replace(chr(92), "/").endswith("guard/redactor.py"):
            assert secret not in repr(frame.f_locals), frame.f_code.co_name
    assert s.size == 0  # and the session is usable afterwards
    monkeypatch.undo()
    assert r.mask(f"hello {secret}", s) == "hello <EMAIL_1>"


def test_error_inside_a_callers_except_block_hides_the_callers_context():
    """Python sets __context__ on raise, so the caller's own exception is attached; it is hidden from tracebacks
    (__suppress_context__) and documented in the module docstring: call mask outside an except block."""
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    try:
        raise ValueError("the caller's own problem")
    except ValueError:
        with pytest.raises(RedactionError) as info:
            r.mask("x\x00", s)
    assert info.value.__suppress_context__ is True and info.value.__cause__ is None
    assert "the caller's own problem" not in "".join(
        traceback.format_exception(info.value, chain=False)
    )


def test_protocol_members_and_no_put_back():
    from hadavin_sdk.guard.redactor import REGEX_VERSION, Redactor, RegexRedactor

    r = RegexRedactor()
    assert isinstance(r, Redactor)
    assert (r.name, r.version) == ("regex", REGEX_VERSION) and len(r.fingerprint) == 64
    assert not hasattr(r, "put_back") and "put_back" not in vars(
        Redactor
    )  # F10: put-back arrives with ticket C1f
    assert {"name", "version", "fingerprint", "mask", "check", "find", "lint"} <= set(
        Redactor.__protocol_attrs__
    )
    assert r.find(f"mail bob@example.com and {IBAN}") == ["EMAIL", "IBAN"]
    assert r.find("nothing sensitive here") == []


def test_decode_input_strips_boms_in_linear_time():
    from hadavin_sdk.guard.redactor import decode_input

    t0 = time.perf_counter()
    assert decode_input(b"\xef\xbb\xbf" * 260_000) == ""
    assert decode_input((chr(0xFEFF) * 260_000) + "x") == "x"
    assert time.perf_counter() - t0 < 2.0


def test_deep_comb_of_nested_secrets_near_the_cap_stays_fast_and_masked():
    """Values that are prefixes of each other nest the sweep's finder deeper than its limit, which sends guard.redact to
    its split fallback. 320 nested keys must still be masked, checked and fast."""
    r, s, _ = kit()
    keys = ["sk-" + "a" * n for n in range(20, 340)]
    doc = "\n".join(f"line {i} {k}" for i, k in enumerate(keys))
    t0 = time.perf_counter()
    masked = r.mask(doc, s)
    masked2 = r.mask(
        "\n".join(reversed(doc.split("\n"))), s
    )  # second pass sweeps every known value through the finder
    elapsed = time.perf_counter() - t0
    assert "sk-" not in masked and "sk-" not in masked2
    r.check(masked, s)
    engine = s.cache["regex.engine"]
    assert len(engine._finders) > 1 or engine._slow  # the split / one-by-one fallback really ran
    assert elapsed < 30.0


# ------------------------------------------------------------------------------------------ wiring (batch 3)


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
            "max_work": 400,
            "max_session_values": 4,
            "max_walk_items": 11,
        }
    )
    assert "redactor" in named.explicit
    built = make("redactor", named.redactor)
    assert (
        built.name,
        built.max_doc_chars,
        built.max_token_chars,
        built.max_line_chars,
        built.max_work,
        built.max_session_values,
        built.max_walk_items,
    ) == ("regex", 50, 7, 9, 400, 4, 11)
    assert "redactor" in parse(redactor="regex").explicit
    with pytest.raises(ConfigError, match="unknown kind"):
        parse(redactor="other")
    for bad in (
        {"max_doc_chars": 0},
        {"max_doc_chars": 1_000_001},
        {"max_token_chars": 50_001},
        {"max_line_chars": 50_001},
        {"max_work": 2_000_000_001},
        {"max_session_values": 100_001},
        {"max_walk_items": 0},
        {"typo": 1},
    ):
        with pytest.raises(ConfigError):
            parse(redactor={"kind": "regex", **bad})
    with pytest.raises(ValidationError):
        type(default.redactor)(kind="other")


@pytest.mark.parametrize(
    "setting",
    [
        "max_doc_chars",
        "max_token_chars",
        "max_line_chars",
        "max_work",
        "max_session_values",
        "max_walk_items",
    ],
)
def test_config_hash_changes_with_non_default_redactor_settings(tmp_path, setting):
    base = registry_of(make_cfg(tmp_path / "a")).config_hash("test-agent")
    same = make_cfg(tmp_path / "b")
    set_backends(same, redactor={"kind": "regex"})  # named, but all defaults
    assert registry_of(same).config_hash("test-agent") == base
    other = make_cfg(tmp_path / "c")
    set_backends(
        other, redactor={"kind": "regex", setting: 2_000_000 if setting == "max_work" else 1000}
    )
    assert registry_of(other).config_hash("test-agent") != base


def test_config_hash_includes_the_fingerprint(tmp_path, monkeypatch):
    from hadavin_sdk.guard.redactor import RegexRedactor

    reg = registry_of(make_cfg(tmp_path))
    h1 = reg.config_hash("test-agent")
    monkeypatch.setattr(RegexRedactor, "fingerprint", "f" * 64)
    assert reg.config_hash("test-agent") != h1


def test_redact_source_change_without_a_version_bump_is_refused_at_start(monkeypatch):
    import inspect

    from hadavin_sdk.config import ConfigError
    from hadavin_sdk.guard import redactor as mod

    redact = _redact_mod()
    real = inspect.getsource
    monkeypatch.setattr(
        mod.inspect, "getsource", lambda m: real(m) + "\n# an edit" if m is redact else real(m)
    )
    with pytest.raises(ConfigError, match=r"guard/redact.py changed without a version bump"):
        mod.RegexRedactor()


def test_documented_misses_and_obligations_are_in_the_module_docstring():
    from hadavin_sdk.guard import redactor as mod

    doc = " ".join(mod.__doc__.split())
    for phrase in (
        "spaced or lower-case or hyphenated IBAN",
        "names in free prose",
        "bob@example.com_x",
        "soft-hyphen",
        "%2E",
        "&#64;",
        "base64",
        "full-width",
        "line-wrapped",
        "images and PDFs",
        "unsupported_input",
        "too_large",
        "split by the caller",
        "C1b obligations",
        "per run context, never shared",
        "test_two_threads_two_runs_no_crosstalk",
        "no NFKC",
        "close()",
        "Second kind",
        "service",
        "KERNEL-1",
        "call it outside such a block",
        "blocks every thread",
    ):
        assert phrase in doc, phrase
    assert (
        "other than ``%40``" in doc
    )  # %40 IS masked by the EMAIL pattern: the old docstring was wrong


# ------------------------------------------------------------------------------------------ trusted-text lint (batch 3)

PROSE2 = [
    "Dear Customer,",
    "Customer name: as printed on the invoice",
    "Never repeat the password: say you cannot share it.",
    "The user id: the numeric id of the account holder.",
    "Pay no more than up to 999999999999 units.",
    "Write the amount, the currency and the supplier name.",
    "Answer in the language of the customer. Use the marks like <EMAIL_1> exactly as given.",
    "See https://docs.example.com/guide and host api.corp.internal for the manual.",
    "Values above 2147483647 or 4294967295 do not fit; the epoch 1700000000 is a date.",
    "Ask the user for their phone number when it is missing.",
]
REAL2 = {
    "email": "Ask ops.lead@example.com about it.",
    "iban": f"Pay to {IBAN} only.",
    "apikey": f"Use the key {KEY} for the call.",
    "password value": "password: Zx9wq7Lm4pTv",
    "password letters only": "password: correcthorsebatterystaple",
    "card": "Card 4111 1111 1111 1111 is a test card.",
    "bsb": "Our bank BSB 062-000 is used.",
    "sort code": "sort code 12-34-56 at the bank",
    "address": "Ship to 12 Baker Street, London.",
    "phone": "Call +44 20 7946 0958 now.",
}


def prompt_path(root):
    return root / "prompts" / "test-agent.md"


@pytest.mark.parametrize("line", PROSE2)
def test_ordinary_prose_passes_the_lint(tmp_path, line):
    root = make_cfg(tmp_path)
    p = prompt_path(root)
    p.write_text(p.read_text(encoding="utf-8") + "\n" + line + "\n", encoding="utf-8")
    write_contract_with(root, description=line)  # create_draft_record is in scope
    registry_of(root)


@pytest.mark.parametrize(
    "number", [2147483647, 4294967295, 1700000000, 9007199254740991, 999999999999]
)
def test_ordinary_numbers_in_a_schema_pass_the_lint(tmp_path, number):
    root = make_cfg(tmp_path)
    write_contract_with(
        root,
        input_schema={
            "type": "object",
            "properties": {
                "n": {"type": "integer", "enum": [number]},
                "m": {"type": "string", "maxLength": number % 1000},
            },
        },
    )
    registry_of(root)


@pytest.mark.parametrize("name", sorted(REAL2))
def test_real_values_in_a_prompt_are_refused_with_file_and_line_but_not_the_text(tmp_path, name):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    p = prompt_path(root)
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text("\n".join([*lines, REAL2[name]]) + "\n", encoding="utf-8")
    with pytest.raises(ConfigError) as info:
        registry_of(root)
    msg = str(info.value)
    assert "test-agent" in msg and "prompts/test-agent.md" in msg
    assert f"line {len(lines) + 1}" in msg or "across lines" in msg
    for fragment in (
        "ops.lead",
        "example.com",
        IBAN,
        KEY,
        "Zx9wq7Lm4pTv",
        "4111",
        "correcthorse",
        "062-000",
        "12-34-56",
        "Baker",
        "7946",
    ):
        assert fragment not in msg


def test_contract_text_and_schema_with_pii_refused_and_the_message_hides_keys(tmp_path):
    from hadavin_sdk.config import ConfigError

    email = "erin@example.com"
    cases = (
        ("description", {"description": f"Pay to {IBAN} only."}),
        ("expected_outcome", {"expected_outcome": "a mail to dana@example.com exists"}),
        (
            "input_schema",
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"to": {"type": "string", "enum": [email]}},
                }
            },
        ),
        (
            "input_schema",
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"n": {"type": "integer", "enum": [4111111111111111]}},
                }
            },
        ),
        (
            "input_schema",
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"pattern": {"type": "string", "enum": [email]}},
                }
            },
        ),
        (
            "input_schema",
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"to": {"type": "string", "enum": [{"pattern": email}]}},
                }
            },
        ),
        (
            "input_schema",
            {"input_schema": {"type": "object", "properties": {email: {"type": "string"}}}},
        ),  # the KEY is the value
        (
            "input_schema",
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"d": {"type": "string", "enum": [{"pattern": email, "x": 1}]}},
                }
            },
        ),  # data, not a keyword
    )
    for where, extra in cases:
        root = make_cfg(tmp_path / f"{where}-{len(list(tmp_path.iterdir()))}")
        write_contract_with(root, **extra)
        with pytest.raises(ConfigError, match=f"action create_draft_record: {where}") as info:
            registry_of(root)
        msg = str(info.value)
        assert (
            "example.com" not in msg
            and "erin" not in msg
            and IBAN not in msg
            and "4111111111111111" not in msg
        )
    root = make_cfg(tmp_path / "keypath")
    write_contract_with(
        root, input_schema={"type": "object", "properties": {email: {"type": "string"}}}
    )
    with pytest.raises(ConfigError) as info:
        registry_of(root)
    assert "key#" in str(info.value) and "erin" not in str(info.value)


def test_context_gated_kinds_are_linted_on_the_joined_text_too(tmp_path):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    write_contract_with(
        root, description="Our bank sort code is", expected_outcome="12-34-56 on file"
    )
    with pytest.raises(ConfigError, match="all text joined") as info:
        registry_of(root)
    assert "12-34-56" not in str(info.value)


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


def test_every_agent_that_is_not_retired_is_linted_and_only_in_scope_contracts(tmp_path):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    write_contract_with(
        root, name="send_email", description="Mail dana@example.com"
    )  # not in test-agent scope
    agents = yaml.safe_load((root / "agents.yaml").read_text(encoding="utf-8"))
    assert "send_email" not in agents[0]["scope_allowed"], (
        "fixture changed: pick a contract outside the scope"
    )
    registry_of(root)  # a contract no agent can use is not read
    prompt_path(root).write_text("Mail dana@example.com\n", encoding="utf-8")
    for status, refused in (("live", True), ("draft", True), ("retired", False)):
        agents[0]["status"] = (
            status  # a draft agent's prompt goes through the gate (evals.py:48): it reaches a model
        )
        (root / "agents.yaml").write_text(yaml.safe_dump(agents), encoding="utf-8")
        if refused:
            with pytest.raises(ConfigError, match="agent test-agent: prompt"):
                registry_of(root)
        else:
            registry_of(root)


def test_prompt_file_changed_after_load_is_refused(tmp_path):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    reg = registry_of(root)
    clean = reg.prompt("test-agent")
    assert reg.prompt("test-agent") == clean
    prompt_path(root).write_text(clean + "\nAsk dana@example.com\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="changed since the registry was loaded"):
        reg.prompt("test-agent")


def test_bom_or_non_utf8_prompt_is_a_config_error(tmp_path):
    from hadavin_sdk.config import ConfigError

    for name, raw in (("bom", b"\xef\xbb\xbfYou help.\n"), ("latin1", b"You help. caf\xe9\n")):
        root = make_cfg(tmp_path / name)
        prompt_path(root).write_bytes(raw)
        with pytest.raises(ConfigError, match="prompts/test-agent.md") as info:
            registry_of(root)
        assert "UnicodeDecodeError" not in str(info.value)


def test_lint_kind_table():
    r = kit()[0]
    assert r.lint("a@example.com") == ["EMAIL"]
    assert r.lint("password: say") == [] and r.lint("password: Zx9wq7Lm4pTv") == ["SECRET"]
    assert r.lint("password: correcthorsebatterystaple") == ["SECRET"]
    assert (
        r.lint("host api.corp.internal ip 10.1.2.3 uuid 123e4567-e89b-12d3-a456-426614174000") == []
    )
    assert r.lint("Our bank BSB 062-000") == ["BANKCODE"] and r.lint("sort code 12-34-56") == [
        "BANKCODE"
    ]
    assert r.lint("Ship to 12 Baker Street") == ["ADDRESS"]
    assert r.lint("2147483647") == [] and r.lint("phone 2147483647") == ["PHONE"]
    assert r.lint("+44 20 7946 0958") == ["PHONE"]
    assert (
        r.lint("4111111111111111", numeric=True) == ["CREDITCARD"]
        and r.lint("2147483647", numeric=True) == []
    )
    assert code_of(r.lint, b"bytes") == "unsupported_input"
