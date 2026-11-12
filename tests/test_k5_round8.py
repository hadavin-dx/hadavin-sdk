"""Round 8 (security path): ONE choke point for every producer, and no raw text cut before pattern redaction.

M-1: the layered decode (percent, entity, backslash escapes, NFKC, to a fixed point) lives in `guard/runmap.py` and every
producer reaches it. M-2: a token longer than the cut window (a 900-character JWT, a PEM block) is redacted whole
before any cut, whatever the prefix in front of it."""

from __future__ import annotations

import base64

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.judge import JudgeDetector
from hadavin_sdk.runtime import tick as tick_mod

AWS = "AKIA" + "IOSFODNN7EXAMPLE"  # the one literal AWS allows, built from parts
SPELLINGS = {
    "percent": "%41KIA" + "IOSFODNN7EXAMPLE",
    "entity": "&#65;KIA" + "IOSFODNN7EXAMPLE",
    "percent-assignment": "password%3Dhunter2",
}
NEEDLES = ("IOSFODNN7EXAMPLE", "hunter2")


def _clean(out: str) -> bool:
    return not any(n in out for n in NEEDLES)


def _judge(text: str) -> str:
    seen = {}

    class LLM:
        def chat(self, messages, **kw):
            seen["doc"] = kw["documents"][0].decode()
            raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        JudgeDetector(LLM(), "r", 0.5).check(text, "t")
    return seen["doc"]


def _bundle_text(text: str) -> str:
    from hadavin_sdk.k1b.redaction import redact_bundle
    from tests.test_k1b_redaction_layers import _bundle, _log

    return repr(redact_bundle(_bundle(**_log(f"x {text} y")))[0].logs)


# every row of guard/producers.py, by the function the producer calls (the registry test asserts the rows)
PRODUCER_CALLS = {
    "redact_text": lambda t, c: runmap.redact_text(f"a {t} b", {}),
    "redact_untrusted": lambda t, c: runmap.redact_untrusted(f"a {t} b", {}),
    "redact_value": lambda t, c: repr(runmap.redact_value({"k": f"a {t} b"}, {})),
    "safe_head": lambda t, c: runmap.safe_head(f"a {t} b", 300),
    "prepare_output": lambda t, c: tools_mod.prepare_output(f"a {t} b", {}, 16384, []),
    "error_reason": lambda t, c: tools_mod.error_reason(ValueError(f"a {t} b"), []),
    "tick": lambda t, c: tick_mod._message(tick_mod.ConfigError(f"a {t} b")),
    "card": lambda t, c: channel_mod.clean(f"a {t} b"),
    "judge": lambda t, c: _judge(f"a {t} b"),
    "bundle": lambda t, c: _bundle_text(t),
}


@pytest.mark.parametrize("producer", sorted(PRODUCER_CALLS))
@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_every_producer_undoes_the_layers_before_it_redacts(producer, spelling, caplog):
    out = PRODUCER_CALLS[producer](SPELLINGS[spelling], caplog)
    assert _clean(out), (producer, spelling, out[:120])


def test_the_layered_decode_lives_in_runmap_and_tools_does_not_own_a_copy():
    assert callable(runmap.undo) and issubclass(runmap.TooDeep, runmap.RedactionError)
    assert tools_mod.TooDeep is runmap.TooDeep


def _jwt(n: int) -> str:
    head = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    body = base64.urlsafe_b64encode(("x" * 520).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(bytes(range(256)) * 2).decode().rstrip("=")
    tok = f"{head}.{body}.{sig}"
    return (tok + tok)[:n] if len(tok) < n else tok[:n]


def _pem() -> str:
    body = "\n".join(
        base64.b64encode(bytes((i * 7 + j) % 256 for j in range(48))).decode() for i in range(28)
    )
    return "-----BEGIN " + "PRIVATE KEY-----\n" + body + "\n-----END " + "PRIVATE KEY-----"


def _frag_free(out: str, secret: str) -> bool:
    """No 24-character window of the secret survives in the output."""
    flat = secret.replace("\n", "")
    return not any(flat[i : i + 24] in out.replace("\n", "") for i in range(0, len(flat) - 24, 8))


@pytest.mark.parametrize("pre", range(3300, 4300, 100))
@pytest.mark.parametrize("kind", ["jwt", "pem"])
def test_a_long_token_straddling_the_old_cut_point_leaves_no_fragment(pre, kind):
    """The old pre-cut fell at max(2 x max_bytes, 4096) = 4096 raw characters for max_bytes 2048. A prefix of long
    e-mail addresses shrinks about four-fold when redacted, so what the cut left of the token landed INSIDE the final
    window (max_bytes). The token must be redacted whole before any cut."""
    secret = _jwt(900) if kind == "jwt" else _pem()
    prefix = ("bob.smith@verylongexamplehost.example.com " * (pre // 42 + 1))[:pre]
    raw = prefix + "\n" + secret + "\n" + "tail words " * 200
    out = tools_mod.prepare_output(raw, {}, 2048, [])
    assert _frag_free(out, secret), (kind, pre)


@pytest.mark.parametrize("kind", ["jwt", "pem"])
def test_the_same_for_a_large_result_cut_at_the_cap(kind):
    secret = _jwt(900) if kind == "jwt" else _pem()
    cap = defaults.MAX_REDACT_CHARS
    for back in (50, 300, 900, 1500):  # the token starts this far before the cap
        raw = "word " * ((cap - back) // 5) + secret + "tail " * 400
        out = tools_mod.prepare_output(raw, {}, cap, [])
        assert _frag_free(out, secret), (kind, back)


def test_error_reason_and_safe_head_keep_no_fragment_of_a_long_token():
    secret = _jwt(900)
    msg = "failed with " * 12 + secret
    assert _frag_free(tools_mod.error_reason(ValueError(msg), []), secret)
    assert _frag_free(runmap.safe_head(msg, 500), secret)
    big = "word " * (defaults.MAX_REDACT_CHARS // 5 - 100) + secret
    assert _frag_free(runmap.safe_head(big, defaults.MAX_REDACT_CHARS), secret)


# ---- minors: camelCase credential keys, scalars, nested values; the approval paths --------------------------------------------------------


def _bundle_k8s(record):
    from hadavin_sdk.k1b.redaction import redact_bundle
    from tests.test_k1b_redaction_layers import _bundle, _shown

    return _shown(redact_bundle(_bundle(k8s=(("k8s/x.json", record),)))[0])


@pytest.mark.parametrize(
    "key", ["clientSecret", "accessToken", "dbPassword", "apiKey", "privateKey", "authToken"]
)
def test_camel_case_credential_keys_are_masked_with_their_value(key):
    shown = _bundle_k8s({"kind": "Pod", "labels": {key: "zeta-nine"}})
    assert "zeta-nine" not in shown


def test_a_number_a_list_and_a_nested_object_under_a_credential_key_are_masked():
    shown = _bundle_k8s(
        {
            "kind": "Pod",
            "labels": {
                "pin_token": 424242,
                "passwords": "x",
                "secret": {"a": "eta-seven", "n": 515151},
            },
        }
    )
    assert "424242" not in shown and "eta-seven" not in shown and "515151" not in shown


def test_words_that_only_contain_a_credential_word_are_not_masked():
    shown = _bundle_k8s({"kind": "Pod", "labels": {"author": "ann", "tokens_used": 7}})
    assert "'ann'" in shown and "7" in shown


def _plan(inputs):
    from hadavin_sdk.models import Plan, Target

    return Plan(
        run_id="run-1",
        agent_id="test-agent",
        action_id="create_draft_record",
        action_version=1,
        risk_class="reversible",
        inputs=inputs,
        target=Target(system="fixture-records", ref=None),
        idempotency_key="run-1:create_draft_record",
        expected_outcome="x",
    )


def test_a_summary_with_inputs_too_large_to_redact_is_a_fixed_text_not_an_exception():
    from hadavin_sdk.approvals.requests import summary

    text = summary(_plan({"blob": "ﷺ" * 87000}))
    assert "too large to show" in text and "ﷺ" not in text


def test_the_slack_card_never_cuts_a_summary_silently():
    from types import SimpleNamespace

    from hadavin_sdk.approvals.slack_channel import SlackChannel

    ch = SlackChannel.__new__(SlackChannel)
    ch.max_card_chars = 100
    req = SimpleNamespace(
        summary="word " * 200, current_step=0, steps=[1], approval_id="a1", status="PENDING"
    )
    blocks = ch._blocks(req, None)
    shown = blocks[0]["text"]["text"]
    assert "too long to show" in shown and "word word" not in shown


def test_the_k1b_masking_module_does_not_import_the_tools_module():
    """The choke point lives in guard/runmap.py; a case-bundle module has no business loading the tool runtime."""
    import ast
    import pathlib

    src = pathlib.Path(hadavin_sdk_file()).parent / "k1b" / "redaction.py"
    names = [
        n.module if isinstance(n, ast.ImportFrom) else a.name
        for n in ast.walk(ast.parse(src.read_text(encoding="utf-8")))
        if isinstance(n, ast.ImportFrom | ast.Import)
        for a in (n.names if isinstance(n, ast.Import) else [n])
    ]
    assert "hadavin_sdk.tools" not in [x for x in names if x]


def hadavin_sdk_file() -> str:
    import hadavin_sdk

    return hadavin_sdk.__file__


def test_the_vendor_guardrail_receives_redacted_text_even_when_the_caller_did_not():
    from hadavin_sdk.guard.bedrock_guardrail import GuardrailDetector

    seen = {}

    class Client:
        def apply_guardrail(self, **kw):
            seen["text"] = kw["content"][0]["text"]["text"]
            return {"action": "NONE", "assessments": []}

    GuardrailDetector(Client(), "g", "1", 0.5).check(
        "mail " + SPELLINGS["percent"] + " and bob.smith@example.com", "t"
    )
    assert _clean(seen["text"]) and "bob.smith" not in seen["text"]
