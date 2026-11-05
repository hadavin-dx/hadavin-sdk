"""C18a: safe_message masks first, cuts second, shows text only for trusted exception classes. Fake values only."""

from __future__ import annotations

import datetime as dt
import logging

import pytest

EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"
ZW = "\u200b"  # zero-width space (format character, category Cf)
FULLWIDTH_BOB = "ｂｏｂ"


def _sm():
    from hadavin_sdk.guard.safe_message import (
        safe_message,
    )  # inside: each test fails on its own on base

    return safe_message


def _st():
    from hadavin_sdk.guard.safe_message import safe_text

    return safe_text


def _cls(name: str, module: str, base: type = Exception) -> type:
    return type(name, (base,), {"__module__": module})


def test_class_name_prefix_and_masked_text():
    out = _sm()(ValueError(f"bad {EMAIL} {IBAN}"))
    assert out.startswith("ValueError: ")
    assert "example.com" not in out and IBAN not in out and "<EMAIL_1>" in out


def test_redact_before_truncate():
    out = _sm()(ValueError("x" * 290 + " " + EMAIL), 300)
    assert "bob" not in out and "example.com" not in out and "bob@exa" not in out


def test_limit_applies_to_text():
    assert _sm()(ValueError("y" * 1000), 50) == "ValueError: " + "y" * 50


def test_newlines_stripped():
    assert _sm()(ValueError("a\nb\r\nc\td"), 300) == "ValueError: a b c d"


@pytest.mark.parametrize("limit", [0, -1])
def test_non_positive_limit_raises(limit):
    with pytest.raises(ValueError):
        _sm()(ValueError("x"), limit)


def test_empty_message_is_class_name_only():
    assert _sm()(ValueError()) == "ValueError"
    assert _sm()(ValueError("   \n ")) == "ValueError"


def test_broken_str_is_unavailable_not_raised():
    class Broken(Exception):
        def __str__(self) -> str:
            raise RuntimeError("no " + EMAIL)

    Broken.__module__ = "builtins"  # trusted on purpose: this isolates the str() guard
    assert _sm()(Broken()) == "Broken: (message unavailable)"


# --- which classes may show their text (allowlist: builtins + hadavin_sdk, whole MRO) ---------------------


@pytest.mark.parametrize(
    "exc",
    [
        ConnectionError("db.internal user=admin"),
        OSError("host x"),
        TimeoutError("h"),
        FileNotFoundError("/home/bob/secret.txt"),
    ],
)
def test_os_errors_withheld(exc):
    assert _sm()(exc) == type(exc).__name__


@pytest.mark.parametrize(
    "module",
    [
        "psycopg.errors",
        "psycopg2.errors",
        "psycopg_pool",
        "asyncpg.exceptions",
        "sqlite3",
        "sqlalchemy.exc",
        "urllib.error",
        "urllib3.exceptions",
        "http.client",
        "httpx",
        "requests.exceptions",
        "google.api_core.exceptions",
        "azure.core.exceptions",
        "anthropic",
        "openai",
        "pydantic_core",
        "botocore.exceptions",
        "boto3.exceptions",
        "aiohttp.client_exceptions",
        "socket",
        "ssl",
        "some_unknown_vendor.errors",
    ],
)
def test_any_non_trusted_module_withheld(module):
    exc = _cls("VendorError", module)(f"host=db.internal password=hunter2abc {EMAIL}")
    assert _sm()(exc) == "VendorError"


def test_user_subclass_of_driver_exception_withheld_by_mro():
    driver = _cls("DriverError", "psycopg.errors")
    mine = _cls("MyError", "my_app.errors", driver)  # user's own module, driver ancestor
    assert _sm()(mine("host=db.internal")) == "MyError"


def test_trusted_class_with_driver_ancestor_withheld_by_mro():
    """Even our own wrapper class is withheld if any ancestor is a driver class."""
    driver = _cls("DriverError", "psycopg.errors")
    ours = _cls("OurWrapper", "hadavin_sdk.store.x", driver)
    assert _sm()(ours("host=db.internal")) == "OurWrapper"


def test_user_subclass_of_builtin_in_own_module_withheld():
    assert _sm()(_cls("Mine", "my_app.errors", ValueError)("x")) == "Mine"


def test_builtin_value_error_and_sdk_module_shown():
    assert _sm()(ValueError("plain")) == "ValueError: plain"
    sdk = _cls("SdkError", "hadavin_sdk.errors")("config says no")
    assert _sm()(sdk) == "SdkError: config says no"


def test_real_sdk_config_error_shown_masked():
    from hadavin_sdk.errors import ConfigError

    assert _sm()(ConfigError(f"bad {EMAIL}")) == "ConfigError: bad <EMAIL_1>"


def test_non_string_module_is_withheld_not_a_crash():
    cls = type("Odd", (Exception,), {"__module__": None})
    assert _sm()(cls("secret")) == "Odd"
    cls2 = type("Odd2", (Exception,), {"__module__": 5})
    assert _sm()(cls2("secret")) == "Odd2"


# --- input hygiene, bounds, fail closed ------------------------------------------------------------------


def test_zero_width_char_cannot_hide_a_value():
    out = _sm()(ValueError(f"b{ZW}ob{ZW}@example.com"))
    assert "example.com" not in out and "bob" not in out
    assert ZW not in out


def test_fullwidth_email_is_folded_and_masked():
    out = _sm()(ValueError(f"{FULLWIDTH_BOB}@example.com"))
    assert "example" not in out and "ｂ" not in out and "<EMAIL_1>" in out


def test_input_is_capped_before_masking(monkeypatch):
    seen = []
    import hadavin_sdk.guard.safe_message as mod

    real = mod.redact
    monkeypatch.setattr(mod, "redact", lambda t: (seen.append(len(t)), real(t))[1])
    _sm()(ValueError("z" * 200_000), 300)
    assert seen and max(seen) <= 300 * 8


def test_200k_message_within_time_budget():
    import time

    t0 = time.perf_counter()
    out = _sm()(ValueError(("word " * 40_000) + EMAIL), 300)
    assert time.perf_counter() - t0 < 2.0
    assert len(out) <= len("ValueError: ") + 300


@pytest.mark.parametrize("fail", [ValueError("x"), RecursionError("deep"), MemoryError()])
def test_redact_failure_returns_unavailable(monkeypatch, fail):
    import hadavin_sdk.guard.safe_message as mod

    def broken(text):
        raise fail

    monkeypatch.setattr(mod, "redact", broken)
    assert _sm()(ValueError(f"has {EMAIL}")) == "ValueError: (message unavailable)"


def test_safe_text_has_no_class_prefix():
    assert _st()(ValueError("plain")) == "plain"
    assert _st()(_cls("V", "psycopg")("x")) == ""


# --- coverage limits inherited from the redactor (documented, strict xfail: expiry note below) -----------
# EXPIRY: when guard.redact learns a spaced IBAN, a name in prose or a lowercase-hex presigned signature, the
# matching test XPASSes, strict=True fails the run, and the test must be turned into a normal test (target:
# KERNEL-1 / the next redactor release; review again 2027-01-31).


@pytest.mark.xfail(strict=True, reason="redactor does not mask a spaced IBAN (expires 2027-01-31)")
def test_spaced_iban_masked():
    out = _sm()(ValueError("iban GB82 WEST 1234 5698 7654 32 end"))
    assert "GB82" not in out and "5698" not in out


@pytest.mark.xfail(
    strict=True, reason="redactor does not mask a name in prose (expires 2027-01-31)"
)
def test_name_in_prose_masked():
    assert "Robert" not in _sm()(ValueError("customer Robert Smith called"))


@pytest.mark.xfail(
    strict=True, reason="redactor does not mask lowercase-hex presigned signatures (2027-01-31)"
)
def test_presigned_url_signature_masked():
    sig = "ab12" * 16
    assert sig not in _sm()(ValueError(f"GET https://b.s3.example.com/k?X-Amz-Signature={sig}"))


# --- tick uses it ----------------------------------------------------------------------------------------


def test_tick_step_error_has_one_class_prefix_and_masked_text(caplog):
    """A failing tick step stores and logs the masked message once, with one class prefix, on one line."""
    from hadavin_sdk.runtime import tick

    class _Store:
        saved = None

        def get_tick_state(self, name):
            return None

        def save_tick_state(self, st):
            self.saved = st

    class _App:
        store = _Store()

    class _Ctx:
        now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        app = _App()

    def boom(ctx):
        raise RuntimeError(f"step died for {EMAIL}\nsecond line")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        tick._run_step(_Ctx, tick.TickStep("probe", 0, boom))
    err = _App.store.saved.last_error
    assert err.count("RuntimeError") == 1 and "example.com" not in err and "<EMAIL_1>" in err
    assert "\n" not in err
    line = next(ln for ln in caplog.text.splitlines() if "step=probe" in ln)
    assert "step=probe error_kind=RuntimeError message=step died for <EMAIL_1> second line" in line
    assert caplog.text.count("RuntimeError") == 1 and "example.com" not in caplog.text
