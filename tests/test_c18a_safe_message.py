"""C18a: safe_message masks first, cuts second, withholds driver errors. Fake values only."""

from __future__ import annotations

import pytest

EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"


def _sm():
    from hadavin_sdk.guard.safe_message import (
        safe_message,
    )  # inside: each test fails on its own on base

    return safe_message


def test_class_name_prefix_and_masked_text():
    out = _sm()(ValueError(f"bad {EMAIL} {IBAN}"))
    assert out.startswith("ValueError: ")
    assert "example.com" not in out and IBAN not in out and "<EMAIL_1>" in out


def test_redact_before_truncate():
    out = _sm()(ValueError("x" * 290 + " " + EMAIL), 300)
    assert "bob" not in out and "example.com" not in out and "bob@exa" not in out


def test_limit_applies_to_text():
    out = _sm()(ValueError("y" * 1000), 50)
    assert out == "ValueError: " + "y" * 50


def test_newlines_stripped():
    out = _sm()(ValueError("a\nb\r\nc\td"), 300)
    assert out == "ValueError: a b c d"


@pytest.mark.parametrize(
    "exc", [ConnectionError("db.internal user=admin"), OSError("host x"), TimeoutError("h")]
)
def test_os_errors_withheld(exc):
    out = _sm()(exc)
    assert out == f"{type(exc).__name__}: (driver error; details withheld)"


def test_driver_module_withheld():
    cls = type("Oops", (Exception,), {"__module__": "psycopg.errors"})
    assert "withheld" in _sm()(cls("host=db.internal password=hunter2abc"))


def test_broken_str_does_not_raise():
    class Broken(Exception):
        def __str__(self) -> str:
            raise RuntimeError("no")

    assert _sm()(Broken()) == "Broken: (message unavailable)"


def test_tick_step_error_has_one_class_prefix_and_masked_text(tmp_path, caplog):
    """A failing tick step stores and logs the masked message once, with one class prefix."""
    import logging

    from hadavin_sdk.runtime import tick

    class _Store:
        saved = None

        def get_tick_state(self, name):
            return None

        def save_tick_state(self, st):
            self.saved = st

    class _Ctx:
        now = __import__("datetime").datetime(
            2026, 1, 1, tzinfo=__import__("datetime").timezone.utc
        )

        class app:
            store = _Store()

    def boom(ctx):
        raise RuntimeError(f"step died for {EMAIL}")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        tick._run_step(_Ctx, tick.TickStep("probe", 0, boom))
    err = _Ctx.app.store.saved.last_error
    assert err.count("RuntimeError") == 1 and "example.com" not in err and "<EMAIL_1>" in err
    assert "example.com" not in caplog.text and "RuntimeError" in caplog.text
