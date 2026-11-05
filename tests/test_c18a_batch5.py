"""C18a batch 5: round-4 findings (BL-core-c18a-027..042). Fake values only; control and non-ASCII characters
are built with chr()."""

from __future__ import annotations

import logging

import pytest

from hadavin_sdk.errors import ConfigError

EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"
KEY = "sk-" + "a" * 30
AKIA = "AKIAIOSFODNN7EXAMPLE"
ESC, ZW, BEL = chr(0x1B), chr(0x200B), chr(7)
C1_CSI, C1_OSC, C1_DCS = chr(0x9B), chr(0x9D), chr(0x90)
BACKSLASH = chr(92)


def sm(exc, limit=300):
    from hadavin_sdk.guard.safe_message import safe_message

    return safe_message(exc, limit)


def shown(text: str, limit: int = 300) -> str:
    return sm(ConfigError(text), limit)


# --- 1: complete escape sequences (7-bit and 8-bit) are removed before any pattern runs ------------------------

_ESCAPED = {
    "c1_csi_akia": (C1_CSI + "31m" + AKIA, [AKIA, "KIAIOSF"]),
    "c1_osc_ant_key": (C1_OSC + "0;title" + BEL + "sk-ant-api03-" + "a" * 40, ["aaaa", "sk-ant"]),
    "c1_csi_ghp": (C1_CSI + "1;31m" + "ghp_" + "a" * 36, ["ghp_", "aaaa"]),
    "c1_dcs_akia": (C1_DCS + "data" + chr(0x9C) + AKIA, [AKIA, "KIAIOSF"]),
    "esc_akia": (ESC + AKIA, [AKIA, "KIAIOSF"]),
    "esc_asia": (ESC + "ASIA" + "IOSFODNN7EXAMPLE", ["ASIAIOSF", "SIAIOSF"]),
    "esc_aiza": (ESC + "AIza" + "a" * 35, ["aaaa", "Izaaa"]),
    "esc_sendgrid": (ESC + "SG." + "a" * 22 + "." + "b" * 43, ["aaaa", "bbbb"]),
    "esc_iban": (ESC + IBAN, [IBAN, "82WEST"]),
    "osc_st_akia": (ESC + "]0;title" + ESC + BACKSLASH + AKIA, [AKIA]),
    "csi_final_is_the_key_letter": (ESC + "[31" + AKIA, [AKIA]),
    "email_split_by_esc": ("bob@exa" + ESC + "mple.com", ["bob", "example"]),
    "key_split_by_esc": ("sk-aaaaa" + ESC + "a" * 30, ["aaaa"]),
    "esc_before_at": ("bob" + ESC + "@example.com", ["bob", "example"]),
    "line_separator_inside_key": ("sk-aaaaa" + chr(0x2028) + "a" * 30, ["aaaa"]),
    "paragraph_separator_inside_key": ("sk-aaaaa" + chr(0x2029) + "a" * 30, ["aaaa"]),
    "ogham_space_inside_key": ("sk-aaaaa" + chr(0x1680) + "a" * 30, ["aaaa"]),
}


@pytest.mark.parametrize("name", sorted(_ESCAPED))
def test_escape_sequences_never_hide_or_eat_part_of_a_secret(name):
    text, forbidden = _ESCAPED[name]
    out = shown("see " + text)
    for bit in forbidden:
        assert bit not in out, (bit, out)


def test_a_lone_escape_character_is_not_left_in_the_output():
    assert ESC not in shown("a" + ESC + "b") and C1_CSI not in shown("a" + C1_CSI + "b")


# --- 2: no vote between forms -------------------------------------------------------------------------------


def test_key_split_at_one_place_and_preceded_by_a_word_is_masked():
    out = shown(
        "see" + ZW + "sk-" + "a" * 5 + ZW + "a" * 30
    )  # neither all-removed nor all-spaced masks it
    assert "aaaa" not in out


def test_two_keys_one_split_one_clean_are_both_masked():
    out = shown("x" + ZW + "sk-aaaaa" + ZW + "a" * 30 + " and sk-" + "b" * 30)
    assert "aaaa" not in out and "bbbb" not in out


def test_decoys_cannot_steer_which_form_wins():
    out = shown(("a" + ZW + "@b.com ") * 5 + KEY)
    assert "aaaa" not in out


def test_literal_marks_in_the_text_cannot_steer_anything():
    out = shown("see" + ZW + KEY + " <APIKEY_1> <EMAIL_1> <PHONE_1>" * 20)
    assert "aaaa" not in out


# --- 3: extract reports where and what kind, never a value, a key or an extra field name ---------------------


def _extract(model, reply_text):
    from hadavin_sdk.extract import extract
    from hadavin_sdk.models import Reply

    prompts = []

    class Llm:
        def chat(self, messages, **kw):
            prompts.append(messages)
            return Reply(text=reply_text, model_id="m")

    res = extract(Llm(), b"doc", model, run_id="r", route="r")
    retry = " ".join(
        m["content"]
        for call in prompts[1:]
        for m in call
        if m["role"] == "user" and "failed" in m["content"]
    )
    return res, retry


def test_extract_dict_keys_and_extra_field_names_are_not_echoed():
    from decimal import Decimal

    from pydantic import BaseModel, ConfigDict

    class Out(BaseModel):
        model_config = ConfigDict(extra="forbid")
        items: dict[str, Decimal]

    key = "Acme Textiles Pvt Ltd inv 4417"
    res, retry = _extract(Out, f'{{"items": {{"{key}": "not-a-number"}}, "Jane Doe": 1}}')
    joined = " ".join(res.errors) + retry
    assert "Acme" not in joined and "Jane" not in joined and "4417" not in joined
    assert "items.[key]" in joined and "[key]: Extra inputs are not permitted" in joined


def test_extract_custom_validator_message_is_not_echoed():
    from pydantic import BaseModel, field_validator

    class Out(BaseModel):
        payee: str

        @field_validator("payee")
        @classmethod
        def known(cls, v):
            raise ValueError(f"unknown payee {v}")

    res, retry = _extract(Out, '{"payee": "Jane Doe of 12 High Street"}')
    joined = " ".join(res.errors) + retry
    assert "Jane" not in joined and "High Street" not in joined and "unknown payee" not in joined
    assert "payee: value_error" in joined


def test_extract_union_tag_and_uuid_values_are_not_echoed():
    import uuid
    from typing import Annotated, Literal

    from pydantic import BaseModel, Field

    class Cat(BaseModel):
        kind: Literal["cat"]

    class Dog(BaseModel):
        kind: Literal["dog"]

    class Out(BaseModel):
        pet: Annotated[Cat | Dog, Field(discriminator="kind")]
        ident: uuid.UUID

    res, retry = _extract(Out, '{"pet": {"kind": "Acme secret"}, "ident": "Jane Doe"}')
    joined = " ".join(res.errors) + retry
    assert "Acme" not in joined and "Jane" not in joined and "secret" not in joined
    assert "union_tag_invalid" in joined and "uuid_parsing" in joined


def test_extract_declared_nested_names_are_kept_and_unknown_ones_hidden():
    from pydantic import BaseModel

    class Line(BaseModel):
        amount: int

    class Out(BaseModel):
        lines: list[Line]

    res, _retry = _extract(Out, '{"lines": [{"amount": "x"}, {"nope": 1}]}')
    joined = " ".join(res.errors)
    assert "lines.0.amount" in joined and "lines.1.amount: Field required" in joined


def test_extract_deeply_nested_json_becomes_a_dead_letter_not_a_crash():
    from pydantic import BaseModel

    from hadavin_sdk.models import DeadLetter

    class Out(BaseModel):
        total: int

    res, _ = _extract(Out, "[" * 100000)
    assert (
        isinstance(res, DeadLetter)
        and res.errors
        and all("RecursionError" in e for e in res.errors)
    )


# --- 6: locator, class_name, registry hides input, config wrappers --------------------------------------------


def test_tick_last_error_has_a_locator_without_any_document_text():
    from hadavin_sdk.runtime import tick

    class Store:
        saved = None

        def get_tick_state(self, name):
            return None

        def save_tick_state(self, st):
            self.saved = st

    import datetime as dt

    class App:
        store = Store()

    class Ctx:
        now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        app = App()

    def boom(c):
        raise KeyError("Acme GmbH invoice 4711")  # a built-in: its text is withheld

    tick._run_step(Ctx, tick.TickStep("probe", 0, boom))
    err = Ctx.app.store.saved.last_error
    assert err.startswith("KeyError [test_c18a_batch5.py:") and "Acme" not in err


def test_dynamic_class_name_cannot_forge_a_tick_field(caplog):
    from hadavin_sdk.runtime import tick

    evil = type("Evil step=x" + chr(10) + "at=y", (ConfigError,), {"__module__": "hadavin_sdk.x"})

    class Store:
        def get_tick_state(self, name):
            return None

        def save_tick_state(self, st):
            pass

    import datetime as dt

    class App:
        store = Store()

    class Ctx:
        now = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        app = App()

    def boom(c):
        raise evil("x")

    with caplog.at_level(logging.ERROR, logger="hadavin_sdk.tick"):
        tick._run_step(Ctx, tick.TickStep("probe", 0, boom))
    line = next(ln for ln in caplog.text.splitlines() if "step=probe" in ln)
    assert (
        "error_kind=Evilstep=xat=y at=" in line and line.count("step=") == 2
    )  # 'step=probe' and the name text


def test_locator_is_empty_without_a_traceback_and_never_raises():
    from hadavin_sdk.guard.safe_message import locator

    assert locator(ValueError("x")) == ""

    class Hostile(Exception):
        @property
        def __traceback__(self):  # type: ignore[override]
            raise RuntimeError("boom")

    assert locator(Hostile()) == ""


def test_registry_models_hide_the_input_in_errors():
    from pydantic import ValidationError

    from hadavin_sdk.registry import AgentRecord

    with pytest.raises(ValidationError) as ei:
        AgentRecord(bogus_field=KEY)
    assert KEY not in str(ei.value)


def test_config_wrapper_masks_pydantic_text(tmp_path):
    from hadavin_sdk import config

    path = tmp_path / "c.yaml"
    path.write_text("environment: dev\nbogus: " + KEY + "\n", encoding="utf-8")
    with pytest.raises(ConfigError) as ei:
        config.load_config(path)
    assert KEY not in str(ei.value)


# --- 7: e-mail pattern ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["numpy@1.26.4", "react@18.2.0 and numpy@1.26.4", "pkg@2"])
def test_versions_are_not_mailboxes(text):
    assert shown(text) == "ConfigError: " + text


@pytest.mark.parametrize(
    ("text", "gone"),
    [
        ("bob@example" + chr(0x3002) + "com", "bob"),
        ("bob@example" + chr(0xFF61) + "com", "bob"),
        ("bob&#64;example.com", "bob"),
        ("bob&#x40;example.com", "bob"),
        ("bob&commat;example.com", "bob"),
        ("bob%40example.com", "bob"),
        ("bob%2540example.com", "bob"),
        ("bob" + BACKSLASH + "u0040example.com", "bob"),
        ("o'brien@example.com", "brien"),
        ("a&b@example.com", "a&b"),
        ('"bob smith"@example.com', "smith"),
        ("bob@localhost", "bob"),
        ("bob@corp", "bob"),
        ("bob@[10.0.0.1]", "10.0.0.1"),
    ],
)
def test_more_address_shapes_are_masked(text, gone):
    out = shown("mail " + text + " end")
    assert gone not in out and "<EMAIL_1>" in out


# Coverage the redactor does not have (dated strict xfails; the README coverage limits list them too).
# EXPIRY: review again 2027-01-31 or when guard.redact changes; nothing enforces the date.


@pytest.mark.xfail(
    strict=True, reason="redactor does not mask a lowercase IBAN (expires 2027-01-31)"
)
def test_lowercase_iban_masked():
    assert "82west" not in shown("iban " + IBAN.lower())


def test_dotted_card_number_is_masked_today():
    assert "4111.1111" not in shown("card 4111.1111.1111.1111")


def test_dotted_aadhaar_is_masked_today():
    assert "2345.6789" not in shown("id 2345.6789.0123")


@pytest.mark.xfail(
    strict=True, reason="redactor does not mask a bracketed US phone (expires 2027-01-31)"
)
def test_us_phone_with_brackets_masked():
    assert "555-0132" not in shown("call (415) 555-0132")


@pytest.mark.xfail(
    strict=True, reason="redactor does not mask a dotted US phone (expires 2027-01-31)"
)
def test_us_phone_with_dots_masked():
    assert "555.0132" not in shown("call 415.555.0132")


# --- 8: NFKC input is capped BEFORE it runs; bounded by a work counter, not a clock ------------------------


def test_nfkc_never_sees_more_than_the_cap(monkeypatch):
    import hadavin_sdk.guard.safe_message as mod

    seen = []
    real = mod.unicodedata.normalize
    monkeypatch.setattr(
        mod.unicodedata, "normalize", lambda form, s: (seen.append(len(s)), real(form, s))[1]
    )
    shown(chr(0xFDFA) * 19200)  # one character folds to 18; 19200 of them would be 345,600
    assert seen and max(seen) <= 300 * 8


def test_redact_work_is_bounded_for_the_adversarial_43k_input(monkeypatch):
    import hadavin_sdk.guard.safe_message as mod

    total = []
    real = mod.redact
    monkeypatch.setattr(mod, "redact", lambda t, **kw: (total.append(len(t)), real(t, **kw))[1])
    for text in ["=" * 43000, " =" * 21500, EMAIL * 4000, chr(0xFDFA) * 2400 + EMAIL]:
        total.clear()
        shown(text)
        assert sum(total) <= 4 * 300 * 8  # a few forms at most, each capped
