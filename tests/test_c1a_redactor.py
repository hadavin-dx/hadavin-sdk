"""C1a: the redactor kind (MaskSession, RedactionError, RegexRedactor) and its wiring (table, config, hash, lint).

Modules added by C1a are imported INSIDE each test, so on the base commit every test fails on its own (FAIL-BEFORE)
and not at collection. Fake secrets only: example.com, an IBAN from the public examples, keys built from parts.
"""

from __future__ import annotations

import copy
import pickle
import random
import time
from datetime import UTC, date, datetime

import pytest
import yaml

from tests.conftest import make_cfg, qualify

IBAN = "GB82WEST12345698765432"  # the public example IBAN
KEY = "sk-" + "a" * 30
# The hash `config_hash` gave the fixture agent on main 6608146, before C1a: a qualified.jsonl line made then.
OLD_FIXTURE_HASH = "3ac5b7c34e7a0d7750a75adcd4642364be70af601e8078ee6b46c0dfb0f1be9e"
# REGEX_VERSION -> (sha256 of PATTERNS, sha256 of the sweep rules). Bump the version, then add the new row.
PINNED = {
    "1": (
        "28781a00547858212f3d43c7a79ce8d4439b0c4d4a97a0ebe57678ab0cee933f",
        "04e447242b827967f8a02410fcfdfae134433ad701a7151d48119ea22d86c4cd",
    ),
}


def kit():
    from hadavin_sdk.guard.redactor import MaskSession, RedactionError, RegexRedactor

    return RegexRedactor(), MaskSession(), RedactionError


def code_of(fn, *args) -> str:
    from hadavin_sdk.guard.redactor import RedactionError

    with pytest.raises(RedactionError) as info:
        fn(*args)
    return info.value.code


# ------------------------------------------------------------------------------------------ input rules


@pytest.mark.parametrize(
    "raw",
    [
        b"hello\x00world",
        b"%PDF-1.7\n1 0 obj",
        b"\x89PNG\r\n\x1a\n....",
        b"\xff\xd8\xff\xe0\x00\x10JFIF",
        b"GIF89a\x01\x00",
        b"GIF87a\x01\x00",
        b"PK\x03\x04\x14\x00",
        b"caf\xe9 invoice",  # cp1252, not UTF-8
        b"\xff\xfe\xfa",
        "text with a lone surrogate \ud800",
        "%PDF-1.7 pasted as text",
        "NUL \x00 inside",
        b"\x80",
        12345,
        None,
    ],
    ids=lambda x: repr(x)[:24],
)
def test_unsupported_input(raw):
    r, s, _ = kit()
    assert code_of(r.mask, raw, s) == "unsupported_input"
    assert s.counts == {}  # nothing was learned from a refused input


def test_bom_is_stripped_and_utf8_accepted():
    r, s, _ = kit()
    assert r.mask("﻿hello café".encode(), s) == "hello café"


def test_oversize_refused():
    from hadavin_sdk.guard.redactor import MaskSession, RegexRedactor

    r, s = RegexRedactor(max_doc_chars=100), MaskSession()
    assert len(r.mask("a " * 50, s)) == 100  # exactly at the cap is accepted
    assert code_of(r.mask, "a " * 50 + "b", s) == "too_large"
    assert code_of(r.mask, b"a " * 50 + b"b", s) == "too_large"
    assert code_of(r.mask, b"x " * 1000, s) == "too_large"  # refused before decoding


def test_long_unbroken_run_refused_not_passed_on():
    from hadavin_sdk.guard.redactor import MAX_TOKEN_CHARS

    r, s, _ = kit()
    assert code_of(r.mask, "a" * (MAX_TOKEN_CHARS + 1), s) == "too_large"
    assert r.mask("a" * MAX_TOKEN_CHARS, s) == "a" * MAX_TOKEN_CHARS


BUDGET_S = 20.0  # stated budget for any one 190,000-character adversarial shape on a slow CI runner (laptop: 1-4 s)


def _shapes(n: int = 190_000) -> dict[str, str]:
    emails = " ".join(f"u{i}@example.com" for i in range(5000))
    ibans = " ".join(f"GB82WEST1234569876{i:04d}" for i in range(5000))
    comb = " ".join("a" * i + "Z" for i in range(1, 600))
    return {
        "equals": "=" * n,
        "dashes": "-" * n,
        "spaces": " " * n,
        "equals_spaced": "= " * (n // 2),
        "equals_word": ("=" * 2000 + " ") * (n // 2001),
        "dash_digits": ("1-" * 1000 + " ") * (n // 2001),
        "password_equals": ("password" + "=" * 2000 + " ") * (n // 2009),
        "emails": emails,
        "ibans": ibans,
        "comb": comb[:n],
    }


@pytest.mark.parametrize("shape", sorted(_shapes()))
def test_redos_bounded_time(shape):
    r, s, RedactionError = kit()
    text = _shapes()[shape]
    assert len(text) <= 190_000
    t0 = time.perf_counter()
    try:
        out = r.mask(text, s)
        r.check(out, s)
    except RedactionError:
        pass  # a refusal is bounded too
    assert time.perf_counter() - t0 < BUDGET_S


def test_many_distinct_values_in_a_full_document_bounded():
    r, s, _ = kit()
    text = " ".join(f"u{i}@example.com GB82WEST1234569876{i:04d}" for i in range(4000))[:200_000]
    t0 = time.perf_counter()
    out = r.mask(text, s)
    r.check(out, s)
    assert time.perf_counter() - t0 < BUDGET_S
    assert sum(s.counts.values()) >= 4000


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


def test_mark_in_dict_key_refused():
    from hadavin_sdk.guard.redactor import RedactionError, refuse_mark_keys

    refuse_mark_keys({"fine": {"also": [1, {"ok": "<EMAIL_1> as a VALUE is not a key"}]}})
    for bad in ({"<EMAIL_1>": 1}, {"a": {"b": [{"<IBAN_3>": 2}]}}, [{"x": 1}, {"<PHONE_1>": 0}]):
        with pytest.raises(RedactionError) as info:
            refuse_mark_keys(bad)
        assert info.value.code == "forged_mark"


def test_mark_next_to_raw_value_still_masked():
    r, s, _ = kit()
    first = r.mask("dave@example.com", s)
    assert first == "<EMAIL_1>"
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


# ------------------------------------------------------------------------------------------ session


def test_session_is_private_and_cannot_be_copied():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    assert "bob" not in repr(s) and "example" not in repr(s)
    assert not hasattr(s, "mapping") and not hasattr(s, "__dict__")
    for fn in (pickle.dumps, copy.copy, copy.deepcopy):
        with pytest.raises(TypeError):
            fn(s)
    assert s.issued("<EMAIL_1>") and not s.issued("<EMAIL_2>")


def test_session_refuses_to_renumber_or_reassign():
    from hadavin_sdk.guard.redactor import RedactionError

    r, s, _ = kit()
    r.mask("bob@example.com", s)
    with pytest.raises(RedactionError) as info:
        s._absorb({"<EMAIL_1>": "someone-else@example.com"})
    assert info.value.code == "internal"
    with pytest.raises(RedactionError):
        s._absorb({})  # dropping a mark is a change too


def test_redaction_error_carries_only_its_code():
    from hadavin_sdk.guard.redactor import CODES, RedactionError

    r, s, _ = kit()
    secret = "carol@example.com"  # noqa: S105 - a fake address, not a password
    with pytest.raises(RedactionError) as info:
        r.mask(f"{secret} <EMAIL_7>", s)
    e = info.value
    assert (str(e), e.code, e.args) == ("forged_mark", "forged_mark", ("forged_mark",))
    assert e.__cause__ is None and e.__suppress_context__ is True
    assert secret not in repr(e) and secret not in str(e.args)
    assert set(CODES) == {
        "unsupported_input",
        "too_large",
        "forged_mark",
        "self_check_failed",
        "internal",
    }


def test_unexpected_failure_becomes_internal_without_the_cause(monkeypatch):
    from hadavin_sdk.guard import redactor as mod

    def boom(*a, **k):
        raise ValueError("carol@example.com leaked in an exception")

    monkeypatch.setattr(mod._redact, "redact_many", boom)
    r, s, _ = kit()
    with pytest.raises(mod.RedactionError) as info:
        r.mask("hello", s)
    assert info.value.code == "internal"
    assert info.value.__cause__ is None and info.value.__suppress_context__ is True
    assert "carol" not in repr(info.value)


def test_protocol_has_no_put_back():
    from hadavin_sdk.guard.redactor import Redactor, RegexRedactor

    r = RegexRedactor()
    assert isinstance(r, Redactor)
    assert (r.name, r.version) == ("regex", "1")
    assert not hasattr(r, "put_back") and "put_back" not in vars(Redactor)
    assert r.find(f"mail bob@example.com and {IBAN}") == ["EMAIL", "IBAN"]
    assert r.find("nothing sensitive here") == []


# ------------------------------------------------------------------------------------------ check


def test_check_finds_a_leftover_original():
    r, s, RedactionError = kit()
    masked = r.mask(f"bob@example.com {KEY} {IBAN}", s)
    r.check(masked, s)  # clean
    for leak in ("bob@example.com", KEY, IBAN, f"x {KEY}y"):
        with pytest.raises(RedactionError) as info:
            r.check(f"fine <EMAIL_1> {leak}", s)
        assert info.value.code == "self_check_failed"


def test_check_is_case_sensitive_whole_token_and_four_plus_chars():
    r, s, _ = kit()
    r.mask("bob@example.com", s)
    r.check("BOB@EXAMPLE.COM", s)  # case-sensitive, like _sweep
    r.check("xbob@example.comy", s)  # an identifier must stand alone to count
    s._absorb({**s._snapshot(), "<TENANT_1>": "abc"})  # 3 characters: never required to be absent
    r.check("abc", s)
    s._absorb({**s._snapshot(), "<TENANT_2>": "abcd"})
    with pytest.raises(Exception) as info:
        r.check("see abcd here", s)
    assert str(info.value) == "self_check_failed"


def test_original_equal_to_mark_text_no_selfcheck_failure():
    # TENANT value "EMAIL_1" is the text inside the mark <EMAIL_1>; check must split on marks like _sweep does.
    r, s, _ = kit()
    masked = r.mask("tenant_id=EMAIL_1 and bob@example.com", s)
    assert masked == "tenant_id=<TENANT_1> and <EMAIL_1>"
    r.check(masked, s)
    assert r.mask(masked, s) == masked
    with pytest.raises(Exception) as info:
        r.check("tenant is EMAIL_1 here", s)  # the bare original IS a leak
    assert str(info.value) == "self_check_failed"


def test_check_failure_message_has_no_value():
    r, s, RedactionError = kit()
    r.mask("bob@example.com", s)
    with pytest.raises(RedactionError) as info:
        r.check("bob@example.com", s)
    assert "bob" not in repr(info.value) and "bob" not in str(info.value)


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
    the text is untouched (restoring the marks gives the source back); check passes; masking twice is a no-op."""
    t0 = time.perf_counter()
    r = kit()[0]
    for text, values in fuzz_corpus():
        s = kit()[1]
        masked = r.mask(text, s)
        for v in values:
            assert v not in masked, (text, v)
        assert _restore(masked, s) == text
        r.check(masked, s)
        assert r.mask(masked, s) == masked  # idempotent on this corpus
    assert time.perf_counter() - t0 < 20


def test_fuzz_corpus_is_not_trivial():
    cases = fuzz_corpus()
    assert sum(len(v) for _, v in cases) > 1500
    assert len({t for t, _ in cases}) > 900


@pytest.mark.xfail(
    strict=True,
    reason="spaced IBAN is not masked by the regex kind (README lists it as NOT masked). "
    "Expires 2027-02-01: by then the kind masks it or this xfail is replaced by a README-backed decision.",
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


def test_pattern_and_sweep_change_forces_a_version_bump():
    from hadavin_sdk.guard.redactor import REGEX_VERSION, regex_fingerprint

    assert REGEX_VERSION in PINNED, "new REGEX_VERSION: add its fingerprint row to PINNED"
    assert regex_fingerprint() == PINNED[REGEX_VERSION], (
        "guard/redact.py PATTERNS or _sweep changed: bump REGEX_VERSION, then pin the new fingerprint"
    )


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
    named = parse(redactor={"kind": "regex", "max_doc_chars": 50})
    assert "redactor" in named.explicit
    built = make("redactor", named.redactor)
    assert (built.name, built.max_doc_chars) == ("regex", 50)
    assert "redactor" in parse(redactor="regex").explicit
    with pytest.raises(ConfigError, match="unknown kind"):
        parse(redactor="other")
    with pytest.raises(ConfigError):
        parse(redactor={"kind": "regex", "max_doc_chars": 0})
    with pytest.raises(ConfigError):
        parse(redactor={"kind": "regex", "typo": 1})
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
    monkeypatch.setattr(RegexRedactor, "version", "2")
    assert reg.config_hash("test-agent") != h1
    monkeypatch.setattr(RegexRedactor, "version", "1")
    assert reg.config_hash("test-agent") == h1


def test_config_hash_changes_with_non_default_redactor_settings(tmp_path):
    base = registry_of(make_cfg(tmp_path / "a")).config_hash("test-agent")
    same = make_cfg(tmp_path / "b")
    set_backends(same, redactor={"kind": "regex"})  # named, but all defaults
    assert registry_of(same).config_hash("test-agent") == base
    other = make_cfg(tmp_path / "c")
    set_backends(other, redactor={"kind": "regex", "max_doc_chars": 1000})
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


def pilot_config(tmp_path, **backends):
    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(tmp_path)
    if backends:
        set_backends(root, **backends)
    return root


def test_pilot_config_without_redactor_refused(tmp_path):
    from hadavin_sdk.config import ConfigError, load_config

    with pytest.raises(ConfigError, match="redactor"):
        load_config(pilot_config(tmp_path))


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_live_config_with_named_redactor_loads(tmp_path, env):
    from hadavin_sdk.config import ConfigError, load_config
    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(tmp_path, env=env)
    set_backends(root, redactor={"kind": "regex"})
    try:
        cfg = load_config(root)
    except (
        ConfigError
    ) as exc:  # prod has its own refusals (anchor, signer); the redactor must not be one
        assert "redactor" not in str(exc)
    else:
        assert cfg.backends.explicit >= {"redactor"}


def test_dev_config_without_redactor_still_loads(tmp_path):
    from hadavin_sdk.config import load_config

    assert load_config(make_cfg(tmp_path)).backends.redactor.kind == "regex"


def write_contract_with(root, **extra):
    path = root / "actions" / "send_email.yaml"
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


def test_clean_fixture_config_passes_the_lint(tmp_path):
    registry_of(make_cfg(tmp_path))


def test_prompt_with_pii_refused_without_the_value(tmp_path):
    from hadavin_sdk.config import ConfigError

    root = make_cfg(tmp_path)
    prompt = root / "prompts" / "test-agent.md"
    prompt.write_text(
        prompt.read_text(encoding="utf-8") + "\nAsk bobby@example.com about it.\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError) as info:
        registry_of(root)
    msg = str(info.value)
    assert "test-agent" in msg and "prompt" in msg and "EMAIL" in msg
    assert "bobby" not in msg and "example.com" not in msg


def test_contract_text_and_schema_with_pii_refused(tmp_path):
    from hadavin_sdk.config import ConfigError

    for extra, where in (
        ({"description": f"Pay to {IBAN} only."}, "description"),
        ({"expected_outcome": "a mail to dana@example.com exists"}, "expected_outcome"),
        (
            {
                "input_schema": {
                    "type": "object",
                    "properties": {"to": {"type": "string", "enum": ["erin@example.com"]}},
                }
            },
            "input_schema",
        ),
    ):
        root = make_cfg(tmp_path / where)
        write_contract_with(root, **extra)
        with pytest.raises(ConfigError, match=where) as info:
            registry_of(root)
        assert "example.com" not in str(info.value) and IBAN not in str(info.value)


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
