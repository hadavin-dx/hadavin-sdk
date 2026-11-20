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


def test_a_secret_cut_by_the_bound_leaves_no_front_in_the_reason(monkeypatch):
    """The secret straddles the first bound (MAX_REDACT_CHARS, shrunk so the cut lands inside it) and the fragment
    before the cut would lie inside the final 160 characters: only `_strip_fragment` removes it."""
    from hadavin_sdk import defaults
    from hadavin_sdk.scrub_settings import ScrubSettings

    key = "q9f8e7d6c5b4a39281706f5e4d3c2b1a0Zx"  # no pattern-recognisable prefix: the scrub alone must catch it
    scrub = ScrubSettings(
        tail_window=16
    )  # no whitespace in the last 16 bytes: the cut lands inside the secret
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", 40 + len(tools_mod.TRUNCATED))
    reason = tools_mod.error_reason(RuntimeError("ab ab ab " + key + " tail" * 50), [key], scrub)
    assert key[:8] not in reason
    assert reason.endswith(tools_mod.TRUNCATED)  # the bound did cut


def test_the_bound_test_fails_without_strip_fragment(monkeypatch):
    """Red proof: with `_strip_fragment` a no-op the fragment survives, so the test above is not vacuous."""
    from hadavin_sdk import defaults
    from hadavin_sdk.scrub_settings import ScrubSettings

    key = "q9f8e7d6c5b4a39281706f5e4d3c2b1a0Zx"
    monkeypatch.setattr(defaults, "MAX_REDACT_CHARS", 40 + len(tools_mod.TRUNCATED))
    monkeypatch.setattr(tools_mod, "_strip_fragment", lambda text, forms, scrub=None: text)
    reason = tools_mod.error_reason(
        RuntimeError("ab ab ab " + key + " tail" * 50), [key], ScrubSettings(tail_window=16)
    )
    assert key[:8] in reason


def test_lone_surrogate_without_handed_out_secrets_does_not_raise():
    """The agent loop calls `error_reason(exc)` with `secrets=None`: `_sanitise` runs before that branch."""
    for secrets in (None, []):
        reason = tools_mod.error_reason(RuntimeError("bad \ud800 input"), secrets)
        assert reason.startswith("RuntimeError: ")
        reason.encode("utf-8")
