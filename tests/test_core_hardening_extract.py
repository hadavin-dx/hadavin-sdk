"""G-01 / G-08: extract() leaks no document value into retry prompts, dead letters, logs or exceptions (R85), and
reads fenced or prose-wrapped JSON (R82)."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, field_validator

from hadavin_sdk.extract import Valid, extract
from hadavin_sdk.models import DeadLetter, Reply

# Built from parts so no secret-shaped literal sits in the repo.
CANARY = "canary-" + "key-" + "AKIA" + "ZZ9" + "QX"
CANARY_EMAIL = "jane." + "doe" + "@" + "example" + ".com"


class Inner(BaseModel):
    n: int


class Rec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    amount: Decimal
    tags: dict[str, int] = {}
    inner: Inner | None = None

    @field_validator("title")
    @classmethod
    def _no_secret(cls, v: str) -> str:
        if v.startswith("canary"):
            raise ValueError(f"title {v} looks like a secret")  # a validator that quotes the value
        return v


class Scripted:
    def __init__(self, texts: list[str]) -> None:
        self.texts, self.calls = list(texts), []

    def chat(self, messages: list[dict[str, Any]], **kw: Any) -> Reply:
        self.calls.append({"messages": messages, **kw})
        return Reply(text=self.texts.pop(0), model_id="m")


def _all(llm: Scripted) -> str:
    return json.dumps([c["messages"] for c in llm.calls], default=str)


@pytest.mark.parametrize(
    "bad",
    [
        {"title": CANARY, "amount": "1"},  # validator quotes the value
        {"title": "ok", "amount": CANARY_EMAIL},  # type error with input
        {"title": "ok", "amount": "1", "tags": {CANARY: "x"}},  # a dict key in the loc
        {"title": "ok", "amount": "1", "extra_" + CANARY: 1},  # extra key name in the loc
        {"title": "ok", "amount": "1", "inner": {"n": CANARY}},  # nested
    ],
)
def test_no_value_leaks(bad, caplog, capsys):
    llm = Scripted([json.dumps(bad), json.dumps(bad)])
    with caplog.at_level(logging.DEBUG):
        out = extract(llm, b"doc", Rec, run_id="r", route="x")
    assert isinstance(out, DeadLetter) and out.reason == "extract_invalid"
    seen = _all(llm) + json.dumps(out.errors) + caplog.text + capsys.readouterr().out
    assert CANARY not in seen and CANARY_EMAIL not in seen and "canary" not in seen.lower()
    assert len(llm.calls) == 2 and "Your previous reply was invalid" in _all(llm)
    assert out.errors  # the path and type survive


def test_error_names_field_path_and_type():
    llm = Scripted([json.dumps({"title": "t", "amount": "1", "inner": {"n": "x"}})] * 2)
    out = extract(llm, b"d", Rec, run_id="r", route="x")
    assert "inner.n: int_parsing" in out.errors[0]


def test_invalid_json_is_not_echoed():
    llm = Scripted(["not json " + CANARY, "still not " + CANARY])
    out = extract(llm, b"d", Rec, run_id="r", route="x")
    assert isinstance(out, DeadLetter)
    assert CANARY not in _all(llm) + json.dumps(out.errors)
    assert out.errors == ["JSONDecodeError: reply is not JSON"] * 2


def test_exception_text_has_no_value():
    llm = Scripted([json.dumps({"title": CANARY, "amount": "1"})] * 2)
    out = extract(llm, b"d", Rec, run_id="r", route="x")
    assert CANARY not in repr(out)


@pytest.mark.parametrize(
    "text",
    [
        '```json\n{"title": "t", "amount": "2"}\n```',
        'Here you go: {"title": "t", "amount": "2"} hope that helps',
        '{"title": "t", "amount": "2"}',
    ],
)
def test_fenced_and_prose_json_parse(text):
    out = extract(Scripted([text]), b"d", Rec, run_id="r", route="x")
    assert isinstance(out, Valid) and out.data.amount == 2


@pytest.mark.parametrize("text", ["[1, 2]", '"a string"', "null", "42", "", "```\n[]\n```"])
def test_non_object_is_a_validation_error_not_an_exception(text):
    out = extract(Scripted([text, text]), b"d", Rec, run_id="r", route="x")
    assert isinstance(out, DeadLetter) and len(out.errors) == 2


@pytest.mark.parametrize(
    "text",
    [
        '```json\n[{"title": "t", "amount": "2"}]\n```',  # an array: its items are not the answer
        '[{"title": "t", "amount": "2"}, {"title": "u", "amount": "3"}]',
        '{"wrapper": {"title": "t", "amount": "2"}',  # cut off: the nested object is a fragment
    ],
)
def test_json_in_text_rejects_objects_nested_in_arrays_or_cut_off_objects(text):
    from hadavin_sdk.llm.common import json_in_text

    assert json_in_text(text) is None


@pytest.mark.parametrize(
    "text",
    [
        'Sure, {"a": 1}',
        'Here is the JSON: {"a": 1} done',
        'x {not json} then {"a": 1}',
        '```json\n{"a": 1}\n```',
    ],
)
def test_json_in_text_still_reads_prose_wrapped_and_fenced_objects(text):
    from hadavin_sdk.llm.common import json_in_text

    assert json_in_text(text) == {"a": 1}


def test_a_default_that_looks_like_a_schema_does_not_break_extract():
    class WithDefault(BaseModel):
        title: str
        metadata: dict = {"properties": None}

    llm = type(
        "L", (), {"chat": lambda self, *a, **k: Reply(text='{"title": "t"}', model_id="m")}
    )()
    assert isinstance(extract(llm, b"doc", WithDefault, run_id="r", route="x"), Valid)
