"""`tools.error_reason`: an exception message is sanitised before any encode (a lone surrogate in it must not raise
inside the error handler, which would kill the tool turn), and a handed-out secret never survives in the reason."""

from __future__ import annotations

from hadavin_sdk import tools as tools_mod

KEY = "sk-live-9f8e7d6c5b4a39281706f5e4d3c2b1a0"  # at or above the default min_secret


def test_lone_surrogate_message_with_a_handed_out_secret_does_not_raise():
    reason = tools_mod.error_reason(RuntimeError("bad \ud800 input " + KEY), [KEY])
    assert reason.startswith("RuntimeError: ")
    assert KEY not in reason
    reason.encode("utf-8")  # the reason itself is encodable


def test_lone_surrogate_in_a_refused_message_does_not_raise():
    reason = tools_mod.error_reason(tools_mod.ToolRefused("no \udfff " + KEY), [KEY])
    assert KEY not in reason
    reason.encode("utf-8")


def test_no_secret_fragment_survives_next_to_a_surrogate():
    reason = tools_mod.error_reason(ValueError("\ud800" + KEY + "\ud800"), [KEY])
    assert KEY not in reason and KEY[:16] not in reason and KEY[-16:] not in reason


def test_a_secret_cut_by_the_bound_leaves_no_front_in_the_reason():
    from hadavin_sdk import defaults

    msg = "a" * (defaults.MAX_REDACT_CHARS - 10) + KEY
    reason = tools_mod.error_reason(RuntimeError(msg), [KEY])
    assert KEY[:8] not in reason
