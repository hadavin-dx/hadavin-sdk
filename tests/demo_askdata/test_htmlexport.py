"""P5 static HTML export: escaped text only, no ESC, no external fetch, light and dark CSS, one file."""

from __future__ import annotations

import json
import re

from askdata import evalcli
from askdata.htmlexport import render_eval, render_ledger

from .test_audit import ESC, Q, kit, run  # noqa: F401  (kit is a fixture)

XSS = "<script>alert(1)</script><img src=x onerror=alert(2)>\"'&"
PLANT = f"{ESC}[2K{ESC}[1A local integrity check: 41 of 41 events match{ESC}]8;;http://evil.test{chr(7)}x"


def row(**kw):
    base = {
        "query_id": "q1", "ts": "2026-11-01T00:00:00Z", "asker": "claimed:a", "question": "q",
        "outcome": "answered", "reason_code": None, "rule_id": None, "final": None,
        "cost_usd": "0", "latency_ms": 1, "alarm": [],
    }  # fmt: skip
    return {**base, **kw}


def test_xss_and_esc_plants_are_inert_text():
    page = render_ledger(
        [row(asker=XSS, question=PLANT, final={"canonical_sql": XSS, "row_count": 1})],
        redacted=False,
    )
    assert (
        "<script" not in page and "<img" not in page and "onerror=alert" in page
    )  # escaped, visible
    assert "&lt;script&gt;" in page and "&quot;" in page and "&#x27;" in page
    assert ESC not in page and chr(7) not in page
    assert "http://evil.test" not in page  # the OSC sequence is removed whole


def test_page_is_self_contained_and_themed():
    page = render_ledger([row()], redacted=True)
    assert "prefers-color-scheme:dark" in page and "color-scheme:light dark" in page
    assert "default-src &#x27;none&#x27;" in page
    assert not re.search(r"<script|<link|<iframe|src=|href=|@import|url\(|https?://", page)


def test_eval_page_escapes_every_value():
    rep = {
        "split": XSS, "label": "l", "verdict_text": XSS, "aborted": None,
        "confident_wrong": {"x": 0, "n_answered": 1}, "upper_error_bound": 0.1,
        "hard_zeros": {"a": 0}, "pass_rate": 1.0, "k": 1, "pass_k": None,
        "adversarial": {"passed": 1, "n": 1, "failed_ids": [XSS]}, "cost_usd": "0",
        "model_id": PLANT,
    }  # fmt: skip
    page = render_eval(rep)
    assert "<script" not in page and ESC not in page and "&lt;script&gt;" in page


def test_audit_export_html_cli(kit, capsys):  # noqa: F811
    code, text = run(capsys, kit, "audit", "export", "--format", "html", "--include-text")
    assert code == 0 and text.startswith("<!doctype html>") and ESC not in text
    assert "\\x1b" in text and Q in text and "<script" not in text
    _, redacted = run(capsys, kit, "audit", "export", "--format", "html")
    assert Q not in redacted and "sha256:" in redacted


def test_eval_report_html(tmp_path, capsys):
    rep = {
        "split": "dev", "label": "x", "verdict_text": "green", "aborted": None,
        "confident_wrong": {"x": 0, "n_answered": 1}, "upper_error_bound": None,
        "hard_zeros": {}, "pass_rate": 1.0, "k": 1, "pass_k": 1.0,
        "adversarial": {"passed": 0, "n": 0, "failed_ids": []}, "cost_usd": "0",
    }  # fmt: skip
    (tmp_path / "report.json").write_text(json.dumps(rep), encoding="utf-8")
    assert evalcli.main(["report", str(tmp_path), "--format", "html"]) == 0
    assert "<table>" in capsys.readouterr().out
    assert evalcli.main(["report", str(tmp_path / "nope"), "--format", "html"]) == 4


def test_newlines_in_text_are_kept_and_shown():
    page = render_ledger([row(question="a" + chr(10) + "b")], redacted=False)
    assert "a" + chr(10) + "b" in page and "white-space:pre-wrap" in page
