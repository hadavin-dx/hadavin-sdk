"""C18a batch 4: round-3 review findings (BL-core-c18a-013..026). Fake values only; non-ASCII built with chr()."""

from __future__ import annotations

import logging

import pytest

from hadavin_sdk.errors import ConfigError

EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"
KEY = "sk-" + "a" * 30
ESC = chr(0x1B)
ZW = chr(0x200B)
SHY = chr(0xAD)


def u(*cps: int) -> str:
    return "".join(map(chr, cps))


def sm(exc, limit=300):
    from hadavin_sdk.guard.safe_message import safe_message

    return safe_message(exc, limit)


# --- 1: invisible characters must not defeat the word boundary before a key --------------------------------


@pytest.mark.parametrize(
    "text",
    [
        ESC + "[1m" + KEY,
        "see" + ZW + KEY,
        "see" + SHY + KEY,
        "see" + u(0x2060) + KEY,
        "see" + chr(8) + KEY,
    ],
)
def test_key_after_an_invisible_or_escape_is_masked(text):
    out = sm(ConfigError(text))
    assert "sk-" not in out and "aaaa" not in out and "<APIKEY_1>" in out


def test_value_split_by_a_zero_width_character_inside_is_still_masked():
    out = sm(ConfigError("bo" + ZW + "b@example.com and sk-" + ZW + "a" * 30))
    assert "bob" not in out and "example" not in out and "aaaa" not in out


# --- 2: e-mail addresses in any script ---------------------------------------------------------------------

_ADDRESSES = {
    "latin_accent": "jos" + chr(0xE9) + "@example.com",
    "umlaut_domain": "m" + chr(0xFC) + "ller@firma.de",
    "cyrillic_local": u(0x438, 0x432, 0x430, 0x43D) + "@example.com",
    "cyrillic_o_a": "b" + chr(0x43E) + "b@ex" + chr(0x430) + "mple.com",
    "khmer_inherent_vowel": "bob" + chr(0x17B4) + "@example.com",
    "mongolian_fvs": "bob" + chr(0x180B) + "@example.com",
    "combining_acute": "bob" + chr(0x301) + "@example.com",
    "composed_a": "b" + chr(0xE1) + "b@example.com",
    "fullwidth": u(0xFF42, 0xFF4F, 0xFF42) + "@example.com",
    "unassigned": "bob" + chr(0x378) + "@example.com",
    "lone_surrogate": "bob" + chr(0xD800) + "@example.com",
}


@pytest.mark.parametrize("name", sorted(_ADDRESSES))
def test_address_in_any_script_is_masked(name):
    original = _ADDRESSES[name]
    out = sm(ConfigError("customer " + original + " called"))
    assert original not in out  # the ORIGINAL string is gone, not just a look-alike of it
    assert "example" not in out and "firma" not in out
    assert "<EMAIL_1>" in out


# --- 3: built-in exception text is withheld -------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        KeyError("Acme GmbH invoice 4711"),
        ValueError("could not convert string to float: 'Total EUR 1,234.00 Acme GmbH'"),
        UnicodeEncodeError("ascii", "Acme " + chr(0xE9), 5, 6, "ordinal not in range"),
        ImportError("No module named 'C:/Users/bob/secret'"),
        AssertionError({"name": "Acme GmbH"}),
        SyntaxError("invalid syntax near Acme"),
        RuntimeError("anything"),
    ],
)
def test_builtin_exception_text_is_withheld(exc):
    assert sm(exc) == type(exc).__name__


def test_hadavin_sdk_class_text_is_shown_masked_and_also_trust_is_explicit():
    from hadavin_sdk.guard.safe_message import safe_message

    assert sm(ConfigError("config says no")) == "ConfigError: config says no"
    vendor = type("VendorError", (Exception,), {"__module__": "vendor_x.errors"})(
        "seen by the caller"
    )
    assert safe_message(vendor) == "VendorError"
    assert safe_message(vendor, 300, frozenset({"vendor_x"})) == "VendorError: seen by the caller"


# --- 6: back off before a value that was cut in half ----------------------------------------------------------


def _straddle(material: str, cut_in: int) -> str:
    """A long key (masked to a short mark) first, so the 2400-character cap lands `cut_in` characters into
    `material` while the displayed text is short enough to show it."""
    pad = 2400 - len(KEY) - 1 - cut_in
    text = KEY + "b" * pad + " " + material + " tail words"
    assert len(text) > 2400
    return text


def test_aadhaar_straddling_the_cap_is_not_half_shown():
    out = sm(ConfigError(_straddle("2345 6789 0123", len("2345 6789 "))))
    assert "2345" not in out and "6789" not in out and out.endswith("[truncated]")


def test_open_quote_after_a_shrinking_key_is_not_half_shown():
    material = 'password="correct horse battery staple"'
    out = sm(ConfigError(_straddle(material, len('password="correct horse batt'))))
    assert "correct" not in out and "horse" not in out and "<APIKEY_1>" in out


def test_open_quote_without_an_assignment_is_not_half_shown():
    material = 'the passphrase is "correct horse battery staple"'
    out = sm(ConfigError(_straddle(material, len('the passphrase is "correct horse batt'))))
    assert "correct" not in out and "horse" not in out and "<APIKEY_1>" in out


def test_extract_failure_for_any_other_value_error_is_the_class_name_only():
    from hadavin_sdk.extract import _failure

    assert _failure(ValueError("Acme GmbH owes 5 EUR")) == "ValueError"


def test_assignment_near_the_cap_is_not_half_shown():
    material = "password=correct horse battery staple"
    out = sm(ConfigError(_straddle(material, len("password=correct horse batt"))))
    assert "horse" not in out and "password=" not in out and "<APIKEY_1>" in out


def test_putty_key_lines_masked_before_newlines_are_squeezed():
    putty = chr(10).join(
        [
            "PuTTY-User-Key-File-3: ssh-ed25519",
            "Encryption: none",
            "Comment: k",
            "Public-Lines: 2",
            "AAAAC3NzaC1lZDI1NTE5AAAAIAbc",
            "Private-Lines: 1",
            "AAAAIQCsecretsecretsecret1234",
            "Private-MAC: abcdef0123",
        ]
    )
    out = sm(ConfigError("failed " + putty))
    assert "secretsecret" not in out and "<PRIVKEY_1>" in out


def test_fullwidth_key_prefix_is_folded_then_masked():
    out = sm(ConfigError("see " + u(0xFF53, 0xFF4B, 0xFF0D) + "a" * 30))
    assert "aaaa" not in out and "<APIKEY_1>" in out


def test_os_error_subclass_in_the_sdk_is_still_withheld():
    cls = type("SdkOs", (OSError,), {"__module__": "hadavin_sdk.x"})
    assert sm(cls("host db.internal")) == "SdkOs"


def test_safe_str_rejects_a_non_positive_limit_and_masks_plain_text():
    from hadavin_sdk.guard.safe_message import safe_str

    with pytest.raises(ValueError):
        safe_str("x", 0)
    assert safe_str("mail " + EMAIL) == "mail <EMAIL_1>"


def test_multi_line_secret_is_masked_before_newlines_are_squeezed():
    pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIabcdef\nghijkl\n-----END RSA PRIVATE KEY-----"
    out = sm(ConfigError("failed with " + pem))
    assert "MIIabcdef" not in out and "ghijkl" not in out and "<PRIVKEY_1>" in out
    assert "\n" not in out


# --- 7: never raises, sanitises the class name, keeps the marker ----------------------------------------------


def test_hostile_module_and_name_cannot_break_the_handler():
    class Meta(type):
        @property
        def __module__(cls):  # type: ignore[override]
            raise RuntimeError("boom")

    hostile = Meta("Hostile", (Exception,), {})
    assert sm(hostile("x")) == "Hostile"  # trust check failed -> withheld, nothing raised


def test_hostile_class_name_cannot_break_the_handler():
    from hadavin_sdk.guard.safe_message import with_class

    class Meta(type):
        @property
        def __name__(cls):  # type: ignore[override]
            raise RuntimeError("boom")

    hostile = Meta("X", (Exception,), {"__module__": "hadavin_sdk.x"})
    assert with_class(hostile("x"), "text") == "Exception: text"


def test_class_name_is_sanitised():
    evil = type(
        "Evil\nerror_kind=Fake" + ESC + "[31m", (Exception,), {"__module__": "hadavin_sdk.x"}
    )
    out = sm(evil("hi"))
    assert "\n" not in out and ESC not in out and " " not in out.split(":")[0]


def test_truncation_marker_survives_a_long_masked_text():
    out = sm(ConfigError("word " * 3000))
    assert len(out) <= len("ConfigError: ") + 300 and out.endswith("[truncated]")


# --- 8: cli ------------------------------------------------------------------------------------------------


def test_interactive_refused_is_masked(monkeypatch, capsys):
    from hadavin_sdk import cli

    err = ConfigError(f"backends.llm: bad value {KEY} for {EMAIL}")
    monkeypatch.setattr(cli, "_main", lambda argv=None: (_ for _ in ()).throw(err))
    assert cli.main(["gate", "x"]) == 2
    out = capsys.readouterr().err
    assert out.startswith("refused: ConfigError: ") and KEY not in out and "example.com" not in out


def test_debug_detail_is_for_a_terminal_and_never_for_tick(monkeypatch):
    import io

    from hadavin_sdk import cli

    class Tty(io.StringIO):
        def isatty(self):
            return True

    real_main = cli._main
    monkeypatch.setenv("HADAVIN_DEBUG", "1")
    monkeypatch.setattr(
        cli, "_main", lambda argv=None: (_ for _ in ()).throw(RuntimeError("secret " + KEY))
    )
    monkeypatch.setattr(cli, "_CMD", None)
    pipe = io.StringIO()
    monkeypatch.setattr(cli.sys, "stderr", pipe)
    assert cli.main(["gate", "x"]) == 3
    assert "debug:" not in pipe.getvalue() and KEY not in pipe.getvalue()  # a pipe or a log file
    tty = Tty()
    monkeypatch.setattr(cli.sys, "stderr", tty)
    assert cli.main(["gate", "x"]) == 3
    assert "debug: RuntimeError at " in tty.getvalue() and "Traceback" not in tty.getvalue()
    assert KEY not in tty.getvalue()
    # `tick` keeps quiet even on a terminal. The command is the PARSED sub-command, not the word in argv:
    # `--config tick limits stop` is a `limits` run and does get the detail.
    monkeypatch.setattr(cli, "_main", real_main)
    monkeypatch.setattr(cli, "_CMD", None)
    monkeypatch.setattr(
        "hadavin_sdk.runtime.tick.run_tick", lambda app: (_ for _ in ()).throw(RuntimeError("x"))
    )
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: object())
    monkeypatch.setattr(cli, "load_registry", lambda cfg: type("R", (), {"agents": {}})())
    monkeypatch.setattr("hadavin_sdk.app.build", lambda *a, **k: object())
    tty2 = Tty()
    monkeypatch.setattr(cli.sys, "stderr", tty2)
    assert cli.main(["tick"]) == 3
    assert "debug:" not in tty2.getvalue() and cli._CMD == "tick"
    monkeypatch.setattr(
        cli, "load_config", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
    )
    tty3 = Tty()
    monkeypatch.setattr(cli.sys, "stderr", tty3)
    assert cli.main(["--config", "tick", "limits", "stop", "--by", "me"]) == 3
    assert "debug:" in tty3.getvalue() and cli._CMD == "limits"


def _tick_logging_state():
    ours, root = logging.getLogger("hadavin_sdk"), logging.getLogger()
    return (
        list(ours.handlers),
        ours.level,
        ours.propagate,
        list(root.handlers),
        root.level,
        logging.lastResort,
    )


def _restore_tick_logging(state):
    from hadavin_sdk import cli

    ours, root = logging.getLogger("hadavin_sdk"), logging.getLogger()
    ours.handlers[:], ours.level, ours.propagate = state[0], state[1], state[2]
    root.handlers[:], root.level, logging.lastResort = state[3], state[4], state[5]
    cli._TICK_LOGGING_READY = False


def test_tick_logging_is_traceback_free_visible_and_installed_once(monkeypatch):
    import io

    from hadavin_sdk import cli

    state = _tick_logging_state()
    buf = io.StringIO()
    monkeypatch.setattr(cli.sys, "stderr", buf)
    try:
        cli._TICK_LOGGING_READY = False
        cli._tick_logging()
        n_ours, n_root = (
            len(logging.getLogger("hadavin_sdk").handlers),
            len(logging.getLogger().handlers),
        )
        cli._tick_logging()
        cli._tick_logging()
        assert (
            len(logging.getLogger("hadavin_sdk").handlers),
            len(logging.getLogger().handlers),
        ) == (
            n_ours,
            n_root,
        )  # no duplication across calls
        assert logging.getLogger("hadavin_sdk").propagate is False
        try:
            raise ConfigError("inner " + KEY)
        except ConfigError:
            logging.getLogger("hadavin_sdk.x").exception("ours failed")
            logging.getLogger("thirdparty").exception("theirs failed")
            logging.getLogger("thirdparty").info("theirs info")
        logging.getLogger("other").warning("plain warning")
        err = buf.getvalue()
        assert (
            "ours failed" in err and "theirs failed" in err and "plain warning" in err
        )  # all visible
        assert "theirs info" not in err  # root stays at WARNING
        assert "Traceback" not in err and "inner" not in err  # no exc_info of anybody
        assert logging.lastResort is not None and isinstance(
            logging.lastResort.formatter, cli._NoTraceback
        )
    finally:
        _restore_tick_logging(state)


def test_tick_logging_handler_follows_the_current_stderr(monkeypatch):
    import io

    from hadavin_sdk import cli

    state = _tick_logging_state()
    try:
        cli._TICK_LOGGING_READY = False
        cli._tick_logging()
        first, second = io.StringIO(), io.StringIO()
        monkeypatch.setattr(cli.sys, "stderr", first)
        logging.getLogger("hadavin_sdk").error("one")
        monkeypatch.setattr(cli.sys, "stderr", second)
        logging.getLogger("hadavin_sdk").error("two")
        assert (
            "one" in first.getvalue()
            and "two" in second.getvalue()
            and "two" not in first.getvalue()
        )
    finally:
        _restore_tick_logging(state)


def test_tick_logging_with_caplog_style_root_handlers_still_prints_ours(monkeypatch, caplog):
    import io

    from hadavin_sdk import cli

    state = _tick_logging_state()
    buf = io.StringIO()
    monkeypatch.setattr(cli.sys, "stderr", buf)
    try:
        cli._TICK_LOGGING_READY = False
        cli._tick_logging()
        logging.getLogger("hadavin_sdk.tick").error("step=probe boom")
        assert "step=probe boom" in buf.getvalue()
    finally:
        _restore_tick_logging(state)


# --- 4/9: exact exit code ----------------------------------------------------------------------------------


def test_tick_store_unavailable_exact_exit_code_and_masked(monkeypatch, capsys):
    from hadavin_sdk import cli
    from hadavin_sdk.store.protocol import StoreUnavailable

    monkeypatch.setattr(
        cli, "load_config", lambda *a, **k: (_ for _ in ()).throw(StoreUnavailable(f"x {EMAIL}"))
    )
    assert cli.main(["tick"]) == 4
    err = capsys.readouterr().err
    assert "example.com" not in err and err.startswith("tick: StoreUnavailable: ")


# --- 9: tests that map behaviour --------------------------------------------------------------------------


def test_invisible_characters_before_a_value_are_gone_and_the_value_masked():
    out = sm(ConfigError((ZW * 5000) + "ok " + (ZW * 5000) + EMAIL))
    assert "bob" not in out and "example.com" not in out and ZW not in out and "<EMAIL_1>" in out


def test_truncated_text_ends_with_the_marker_and_no_half_value():
    out = sm(ConfigError(("word " * 700) + "bob@exa"))
    assert out.endswith("[truncated]") and "bob" not in out


def test_cyrillic_lookalike_email_original_string_absent():
    original = "b" + chr(0x43E) + "b@ex" + chr(0x430) + "mple.com"
    out = sm(ConfigError("x " + original))
    assert original not in out and "<EMAIL_1>" in out
