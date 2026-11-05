"""C18a: safe_message masks first, cuts second, shows text only for trusted exception classes. Fake values only."""

from __future__ import annotations

import datetime as dt
import logging

import pytest

EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"
ZW = "\u200b"  # zero-width space (format character, category Cf)
FULLWIDTH_BOB = "\uff42\uff4f\uff42"


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
    out = _sm()(ValueError("y " * 500), 50)
    assert out.startswith("ValueError: y y y") and len(out) == len("ValueError: ") + 50


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
    assert "example" not in out and "\uff42" not in out and "<EMAIL_1>" in out


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
    assert _st()(_cls("V", "psycopg")("x")) == "(withheld)"


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
    assert (
        "step=probe error_kind=RuntimeError message='step died for <EMAIL_1> second line'" in line
    )
    assert caplog.text.count("RuntimeError") == 1 and "example.com" not in caplog.text


# --- batch 3: padding, invisibles, truncation, tick path, extract -------------------------------------------

KEY = "sk-" + "a" * 30


def test_whitespace_padding_cannot_push_a_value_into_a_cut():
    out = _sm()(ValueError(" " * 2395 + EMAIL), 300)
    assert "bob" not in out and "example.com" not in out


def test_many_invisible_characters_before_a_value():
    out = _sm()(ValueError((ZW * 5000) + "ok " + (ZW * 5000) + EMAIL), 300)
    assert "bob" not in out and "example.com" not in out and "ZW" not in out


def test_padding_longer_than_the_raw_read_drops_the_partial_word():
    # raw read is limit*64 = 19200 characters: the value starts inside it and is cut in half by it
    out = _sm()(ValueError(" " * 19190 + EMAIL), 300)
    assert "bob" not in out and out.endswith("[truncated]")


def test_long_key_shrinking_then_half_email_at_the_cap_edge():
    # the long key is masked to a short mark, so the final cut would fall AFTER the pre-cap point
    text = KEY + "b" * 2300 + " " + "x" * 60 + " " + EMAIL  # the cap (2400) lands inside the email
    assert len(text) > 300 * 8
    out = _sm()(ValueError(text), 300)
    assert "bob" not in out and "example" not in out and "<APIKEY_1>" in out


def test_huge_message_read_is_bounded():
    import time

    t0 = time.perf_counter()
    _sm()(ValueError("a " * 3_000_000), 300)  # 6 million characters
    assert time.perf_counter() - t0 < 1.0  # only 64*limit characters are ever read and cleaned


def test_truncated_text_ends_with_marker_and_no_half_value():
    out = _sm()(ValueError(("word " * 700) + "bob@exa"), 300)
    assert "bob" not in out


def test_nfkc_expansion_is_capped_again(monkeypatch):
    import hadavin_sdk.guard.safe_message as mod

    seen = []
    real = mod.redact
    monkeypatch.setattr(mod, "redact", lambda t: (seen.append(len(t)), real(t))[1])
    _sm()(ValueError("\ufdfa" * 2400), 300)  # each folds to 18 characters
    assert seen and max(seen) <= 300 * 8


def test_43k_adversarial_input_is_time_bounded():
    import time

    nasty = ["=" * 43_000, "-" * 43_000, " =" * 21_000, ("\ufdfa" * 2400) + EMAIL, EMAIL * 4000]
    t0 = time.perf_counter()
    for text in nasty:
        _sm()(ValueError(text), 300)
    assert time.perf_counter() - t0 < 4.0  # five inputs; the caps make it milliseconds


def test_combining_grapheme_joiner_cannot_split_an_email():
    out = _sm()(ValueError("bob@exa\u034fmple.com"))
    assert "example" not in out and "bob" not in out


@pytest.mark.parametrize("ch", ["\u3164", "\u2800", "\x00", "\x08", "\ue000", "\ufe0f"])
def test_other_invisibles_removed(ch):
    out = _sm()(ValueError(f"bo{ch}b@example.com"))
    assert "example" not in out and "bob" not in out
    assert ch not in _sm()(ValueError(f"a{ch}b"))


def test_cyrillic_lookalike_in_email_masked():
    assert "example" not in _sm()(ValueError("b\u043eb@ex\u0430mple.com"))


def test_withheld_text_is_marked_in_safe_text_and_empty_means_empty():
    assert _st()(OSError("x")) == "(withheld)"
    assert _st()(ValueError()) == ""


def _step_ctx():
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

    return _Ctx


def test_tick_log_withheld_says_withheld_and_last_error_has_no_suffix(caplog):
    from hadavin_sdk.runtime import tick

    ctx = _step_ctx()

    def boom(c):
        raise ConnectionError("db.internal user=admin")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        tick._run_step(ctx, tick.TickStep("probe", 0, boom))
    assert ctx.app.store.saved.last_error == "ConnectionError"
    assert "message='(withheld)'" in caplog.text and "db.internal" not in caplog.text


def test_tick_log_message_cannot_forge_fields(caplog):
    from hadavin_sdk.runtime import tick

    ctx = _step_ctx()

    def boom(c):
        raise RuntimeError("x step=evil error_kind=Fake ok=true")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        tick._run_step(ctx, tick.TickStep("probe", 0, boom))
    line = next(ln for ln in caplog.text.splitlines() if "step=probe" in ln)
    assert "message='x step=evil" in line  # the whole value sits inside one quoted field
    assert line.count("message=") == 1


def test_tick_masks_once(monkeypatch):
    import hadavin_sdk.guard.safe_message as mod
    from hadavin_sdk.runtime import tick

    calls = []
    real = mod.redact
    monkeypatch.setattr(mod, "redact", lambda t: (calls.append(1), real(t))[1])
    ctx = _step_ctx()
    tick._run_step(
        ctx, tick.TickStep("probe", 0, lambda c: (_ for _ in ()).throw(RuntimeError("a")))
    )
    assert len(calls) == 1


def _config_error_with_secret():
    from pydantic import BaseModel, Field, ValidationError

    from hadavin_sdk.errors import ConfigError

    class Cfg(BaseModel):
        api_key: str = Field(max_length=5)

    try:
        Cfg(api_key=KEY)
    except ValidationError as exc:
        return ConfigError(f"backends.llm (anthropic): {exc}")
    raise AssertionError("expected a validation error")


@pytest.mark.parametrize("raiser", ["load_config", "build"])
def test_tick_config_error_secret_masked(monkeypatch, capsys, raiser):
    from hadavin_sdk import cli

    err = _config_error_with_secret()
    assert KEY in str(err)  # the raw error really carries the secret-shaped value
    if raiser == "load_config":
        monkeypatch.setattr(cli, "load_config", lambda *a, **k: (_ for _ in ()).throw(err))
    else:
        monkeypatch.setattr(cli, "load_config", lambda *a, **k: object())
        monkeypatch.setattr(cli, "load_registry", lambda cfg: type("R", (), {"agents": {}})())
        monkeypatch.setattr("hadavin_sdk.app.build", lambda *a, **k: (_ for _ in ()).throw(err))
    assert cli.main(["tick"]) == 2
    out = capsys.readouterr().err
    assert KEY not in out and "ConfigError" in out


def test_tick_store_unavailable_masked(monkeypatch, capsys):
    from hadavin_sdk import cli
    from hadavin_sdk.store.protocol import StoreUnavailable

    monkeypatch.setattr(
        cli, "load_config", lambda *a, **k: (_ for _ in ()).throw(StoreUnavailable(f"x {EMAIL}"))
    )
    assert cli.main(["tick"]) in (2, 4)
    assert "example.com" not in capsys.readouterr().err


def test_extract_dead_letter_masks_validation_error_input():
    """BL-005: a pydantic ValidationError echoes input_value; DeadLetter.errors must be masked."""
    from pydantic import BaseModel

    from hadavin_sdk.extract import extract
    from hadavin_sdk.models import DeadLetter, Reply

    class Out(BaseModel):
        total: int

    class Llm:
        def chat(self, messages, **kw):
            return Reply(text=f'{{"total": "contact {EMAIL} iban {IBAN}"}}', model_id="m")

    res = extract(Llm(), b"doc", Out, run_id="r1", route="r")
    assert isinstance(res, DeadLetter)
    joined = " ".join(res.errors)
    assert "ValidationError" in joined  # still useful for the retry prompt
    assert "example.com" not in joined and IBAN not in joined and "<EMAIL_1>" in joined


def test_with_retry_error_text_never_has_sdk_message():
    """Pins the waiver for llm/retry.py: ProviderError text is class + status, never the SDK message."""
    from hadavin_sdk.llm.retry import ProviderError, with_retry

    def call():
        raise ValueError(f"request body had {EMAIL}")

    with pytest.raises(ProviderError) as ei:
        with_retry(call, label="llm", max_attempts=2, sleep=lambda s: None)
    assert "example.com" not in str(ei.value)
