"""The case bundle goes through the runtime's one redaction choke point (`guard.runmap.redact_text`), not a plain
regex pass: a secret behind NFKC, a zero-width space, a JSON escape or a percent layer is masked; a value under a
credential key is masked with its key; no key exempts a value at any depth. A class test lists every module that
calls the bare pattern redactor, so a new model-bound path cannot skip the choke point unnoticed."""

from __future__ import annotations

import ast
import dataclasses
import pathlib
import re
from datetime import UTC, datetime

import pytest

from hadavin_sdk.guard.runmap import InputTooLarge
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle

AWS = "AKIA" + "IOSFODNN7EXAMPLE"  # the one literal AWS allows, built from parts
EMAIL = "bob.smith@example.com"
PW = "hunter2"


def _bundle(**kw) -> Bundle:
    base = Bundle(
        case_id="c1",
        alert_time=datetime(2026, 1, 1, tzinfo=UTC),
        alert_time_text="2026-01-01T00:00:00Z",
        alert={"title": "t", "summary": "s", "severity": "page"},
        metrics=(),
        logs=(),
        deploys=(),
        k8s=(),
        runbooks=(),
        ids=frozenset(),
        manifest_sha256="0" * 64,
    )
    return dataclasses.replace(base, **kw)


def _log(msg: str) -> dict:
    return {
        "logs": (
            ("logs/001.jsonl", ({"ts": "2026-01-01T00:00:01Z", "service": "api", "message": msg},)),
        )
    }


def _shown(b: Bundle) -> str:
    return repr((b.alert, b.metrics, b.logs, b.deploys, b.k8s, b.runbooks))


SPELLINGS = {
    "fullwidth": "ＡＫＩＡ" + "IOSFODNN7EXAMPLE",
    "zero-width": "AK\u200bIA" + "IOSFODNN7EXAMPLE",
    "json-escape": r"\u0041KIA" + "IOSFODNN7EXAMPLE",
    "plain": AWS,
}


@pytest.mark.parametrize("name", sorted(SPELLINGS))
def test_a_secret_in_any_spelling_in_a_log_line_runbook_or_alert_is_masked(name):
    s = SPELLINGS[name]
    for b in (
        _bundle(**_log(f"key {s} end")),
        _bundle(runbooks=(("rb/a.md", (f"use {s} here",)),)),
        _bundle(alert={"title": "t", "summary": f"leaked {s}", "severity": "page"}),
    ):
        out, counts = redact_bundle(b)
        assert AWS not in _shown(out) and "IOSFODNN7EXAMPLE" not in _shown(out), name
        assert sum(counts.values()) >= 1


def test_a_percent_or_fullwidth_email_and_password_assignment_are_masked():
    b = _bundle(**_log("mail bob%2Esmith@example.com and ｐａｓｓｗｏｒｄ=" + PW))
    shown = _shown(redact_bundle(b)[0])
    assert "smith" not in shown and PW not in shown


def test_env_name_value_pairs_labels_and_secret_data_are_masked_with_their_key():
    """One bundle per shape and a DIFFERENT value each: a shared value would be masked by one shape's hit in all."""
    shapes = {
        "env entry": (
            {"kind": "Pod", "spec": {"env": [{"name": "DB_PASSWORD", "value": "alpha-one"}]}},
            "alpha-one",
        ),
        "label": ({"kind": "Pod", "labels": {"password": "beta-two"}}, "beta-two"),
        "secret data": ({"kind": "Secret", "data": {"db": "Z2FtbWEtdGhyZWU="}}, "Z2FtbWEtdGhyZWU"),
        "short value": ({"kind": "Pod", "labels": {"token": "ab"}}, "'ab'"),
    }
    for name, (record, needle) in shapes.items():
        out, _ = redact_bundle(_bundle(k8s=(("k8s/x.json", record),)))
        assert needle not in _shown(out), name


def test_no_key_exempts_a_value_at_any_depth():
    b = _bundle(
        k8s=(
            (
                "k8s/x.json",
                {"spec": {"data": {"service": "postgres://admin:" + PW + "@db/x"}}, "kind": EMAIL},
            ),
        )
    )
    shown = _shown(redact_bundle(b)[0])
    assert PW not in shown and EMAIL not in shown


def test_plain_vocabulary_survives():
    b = _bundle(**_log("ok"))
    out, _ = redact_bundle(b)
    assert (
        out.logs[0][1][0]["service"] == "api" and out.logs[0][1][0]["ts"] == "2026-01-01T00:00:01Z"
    )
    assert out.alert["title"] == "t" and out.alert["severity"] == "page"


def test_a_leaf_over_the_cap_is_refused_not_passed_through():
    with pytest.raises(InputTooLarge):
        redact_bundle(_bundle(**_log("x" * 300_000)))


def test_the_same_value_gets_one_placeholder_across_records():
    b = _bundle(**_log("from " + EMAIL), runbooks=(("rb/a.md", ("mail " + EMAIL,)),))
    out, counts = redact_bundle(b)
    assert counts["EMAIL"] == 1
    assert (
        re.search(r"<EMAIL_1>", out.runbooks[0][1][0])
        and "<EMAIL_1>" in out.logs[0][1][0]["message"]
    )


def test_only_known_modules_call_the_bare_pattern_redactor():
    """Class test: a model-bound text that skips `redact_text` (layers, NFKC, caps) is the bug class of the bundle
    path. Every module that calls the bare `redact(...)`/`redact_many(...)` is listed; adding one needs a review."""
    import hadavin_sdk

    root = pathlib.Path(hadavin_sdk.__file__).resolve().parent
    callers = set()
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
                if name in {"redact", "redact_many"}:
                    callers.add(path.relative_to(root).as_posix())
    assert (
        callers
        == {
            "guard/runmap.py",  # the choke point
            "approvals/channel.py",  # the second pass of `clean`, in the namespace the choke point started (a card line)
        }
    ), sorted(callers)


def test_percent_and_entity_layers_are_undone_for_pattern_secrets_in_a_bundle():
    for s in ("%41KIA" + "IOSFODNN7EXAMPLE", "&#65;KIA" + "IOSFODNN7EXAMPLE", "password%3D" + PW):
        shown = _shown(redact_bundle(_bundle(**_log(f"x {s} y")))[0])
        assert "IOSFODNN7EXAMPLE" not in shown and PW not in shown, s


def test_a_base64_token_wrapping_a_quoted_or_hex_spelling_of_a_secret_is_replaced_whole():
    """Direct on the function (the redactor's own high-entropy pattern would hide a gap through a whole-prompt check)."""
    from hadavin_sdk import tools as tools_mod

    secret = "Zk3#9qWd" + "Xv7/pL2m"
    import base64
    import urllib.parse as up

    for spelling in (
        up.quote(secret, safe=""),
        secret.encode().hex(),
        secret.encode().hex().upper(),
    ):
        tok = base64.b64encode(("x=" + spelling).encode()).decode()
        assert tools_mod._derived(f"a {tok} b", [secret]) == "a <SECRET_REDACTED> b", spelling


def test_a_mime_wrapped_token_is_one_token():
    from hadavin_sdk import tools as tools_mod

    tok = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo" * 3
    wrapped = "\n".join(tok[i : i + 76] for i in range(0, len(tok), 76))
    assert len(tools_mod._B64_TOKEN.findall("x\n" + wrapped + "\ny")) == 1
