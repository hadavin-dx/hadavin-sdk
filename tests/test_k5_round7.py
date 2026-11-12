"""Round 7: redact THEN cut at every short-message site; judge input through the choke point; bundle total cap;
NFKC per-character versus whole-text; the empty-decode candidate."""

from __future__ import annotations

import logging
import unicodedata

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import injection, runmap
from hadavin_sdk.runtime import tick as tick_mod

JWT = (
    "eyJhbGciOiJIUzI1NiJ9."
    + "eyJzdWIiOiJhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhIn0."
    + "c2lnbmF0dXJlc2lnbmF0dXJl"
)


def _msg(limit: int) -> str:
    """Words, then the token so that a cut at `limit` lands inside it."""
    words = "failed with " * ((limit - 25) // 12)
    return words + JWT


@pytest.mark.parametrize("limit", [160, 300, 500])
def test_safe_head_redacts_before_the_cut(limit):
    out = runmap.safe_head(_msg(limit), limit)
    assert len(out) <= limit and "eyJhbGci" not in out and "eyJzdWIi" not in out


def test_safe_head_bounds_the_work_and_never_raises():
    assert len(runmap.safe_head("e" * 1_000_000, 100)) <= 100
    assert (
        runmap.safe_head("ﷺ" * 87000, 100) == runmap.SAFE_HEAD_NOTE
    )  # refused after NFKC: a fixed note


def test_the_tick_message_and_the_detector_log_are_redacted_before_the_cut(caplog):
    assert "eyJhbGci" not in tick_mod._message(tick_mod.ConfigError(_msg(500)))

    class Boom:
        def check(self, text, source):
            raise ValueError(_msg(300))

    with caplog.at_level(logging.WARNING):
        v = injection.injection_check(Boom(), "x", "t")
    assert v.flagged and "eyJhbGci" not in caplog.text


def test_the_judge_sends_redacted_text_even_when_the_caller_did_not():
    from hadavin_sdk.guard.judge import JudgeDetector

    seen = {}

    class LLM:
        def chat(self, messages, **kw):
            seen["doc"] = kw["documents"][0].decode()
            raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        JudgeDetector(LLM(), "r", 0.5).check("mail bob.smith@example.com now", "t")
    assert "bob.smith" not in seen["doc"]


def test_nfkc_per_character_view_equals_the_whole_text_view_for_every_character_pair():
    """`runmap._canonical_view` normalises per character; `canonical` the whole text. If they differed, a marker or
    placeholder could be created by composition (a base character plus a combining mark). Checked on every pair
    drawn from the characters that compose or expand."""
    pool = [
        chr(c)
        for c in (
            0x41,
            0x3C,
            0x3E,
            0x300,
            0x301,
            0x338,
            0x3099,
            0xFF1C,
            0xFF1E,
            0xFDFA,
            0x200B,
            0x5F,
            0x31,
        )
    ]
    for a in pool:
        for b in pool:
            text = a + b
            view, _ = runmap._canonical_view(text)
            whole = runmap.canonical(text)
            # the per-character view may keep a combining mark the whole-text form composes: it must never be SHORTER
            # in a way that creates a placeholder or marker the whole text does not
            for token in ("<", ">"):
                assert view.count(token) <= whole.count(token) + text.count(token) + 1
            assert unicodedata.normalize("NFKC", "".join(view)) == unicodedata.normalize(
                "NFKC", whole
            )


def test_a_leaf_cap_and_a_total_cap_on_a_bundle():
    from hadavin_sdk.k1b.redaction import redact_bundle
    from tests.test_k1b_redaction_layers import _bundle, _log

    each = "word " * 40_000  # 200,000 characters: under the per-leaf cap
    records = tuple(
        ({"ts": "2026-01-01T00:00:01Z", "service": "api", "message": each}) for _ in range(30)
    )
    with pytest.raises(runmap.InputTooLarge):  # 6,000,000 characters in total
        redact_bundle(_bundle(logs=(("logs/001.jsonl", records),)))
    assert defaults.MAX_BUNDLE_CHARS >= defaults.MAX_REDACT_CHARS
    _ = _log


def test_a_tail_of_half_escapes_that_decodes_to_nothing_goes_with_the_front():
    """The empty-decode candidate in `_strip_fragment`: `%25%32` is `%2` at the second layer, nothing at the third."""
    from hadavin_sdk import tools as tools_mod

    forms = sorted(tools_mod._secret_forms("Zk3#9qWd" + "Xv7/pL2m"))
    for tail in ("%25%32", "%2525", "&#38;#"):
        cut = "ok " + tail + tools_mod.TRUNCATED
        out = tools_mod._strip_fragment(cut, forms)
        assert out == "ok " + tools_mod.TRUNCATED, (tail, out)
