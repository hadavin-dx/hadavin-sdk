"""``validation_text`` (grammar V) and the validation facts of ``diagnose``."""

from __future__ import annotations

import json
import re

import pytest
from pydantic_core import core_schema

from hadavin_sdk.codes import VALIDATION_OTHER, VALIDATION_TYPES, Where
from hadavin_sdk.guard.diagnostic import diagnose, render, validation_text
from tests.data import c18a_hostile_corpus as corpus
from tests.data.c18a_oracle import grammar_ok

CAN = "Quentin Abernathy"


def err(model: str, doc: dict[str, object] | str) -> BaseException:
    return corpus.build_validation_error(
        {"model": model, "document": doc if isinstance(doc, str) else json.dumps(doc)}
    )


def test_closed_type_list_is_pydantic_error_types() -> None:
    known = set(core_schema.ErrorType.__args__)  # type: ignore[attr-defined]
    assert VALIDATION_TYPES <= known, sorted(VALIDATION_TYPES - known)
    assert len(VALIDATION_TYPES) == 26


def test_grammar_v_and_plain_cases() -> None:
    assert validation_text(err("invoice", {"total": 1})) == "missing"
    assert validation_text(err("invoice", {"total": 1, "vendor": "x", CAN: 1})) == "extra_forbidden"
    assert validation_text(err("lit", {"pick": "z"})) == "literal_error"
    assert validation_text(err("invoice", "{not json")) == "json_invalid"


def test_validation_text_length_bound() -> None:
    out = validation_text(
        err("many", {"a": CAN, "b": CAN, "c": CAN, "d": CAN, "e": CAN, "f": CAN, "g": CAN})
    )
    assert len(out) <= 108 and grammar_ok(out, "V")
    assert re.fullmatch(r"[a-z_; ]+", out.replace("+", "").replace("more", "")) or "more" in out


def test_uuid_parsing_char_is_never_printed() -> None:
    out = validation_text(err("uuid", {"ident": "Q"}))
    assert out in VALIDATION_TYPES | {VALIDATION_OTHER} and "Q" not in out.replace("uuid", "")


def test_value_error_and_assertion_error_text_never_printed() -> None:
    for model in ("custom", "asserting"):
        out = validation_text(err(model, {"name": CAN}))
        assert "Quentin" not in out and "bad value" not in out and grammar_ok(out, "V")


def test_extra_forbidden_key_never_shown() -> None:
    out = validation_text(err("invoice", {"total": 1, "vendor": "x", CAN: 1}))
    assert out == "extra_forbidden" and CAN not in out


def test_union_tag_and_rootmodel_dict_key_never_shown() -> None:
    assert CAN not in validation_text(err("pet", {"pet": {"kind": CAN}}))
    assert CAN not in validation_text(err("dict", {CAN: "x"}))


def test_more_than_5_errors_gives_plus_n_more() -> None:
    out = validation_text(err("many", {"a": CAN}))  # seven fields, all failing
    assert out.count(";") == 5, f"types printed: {out}"
    assert out.endswith("; +2 more"), f"tail: {out}"


def test_non_validation_error_gives_other() -> None:
    assert validation_text(ValueError(CAN)) == VALIDATION_OTHER
    assert validation_text(object()) == VALIDATION_OTHER  # type: ignore[arg-type]


def test_a_type_outside_the_closed_list_prints_other() -> None:
    from typing import Annotated

    from pydantic import Field, TypeAdapter

    with pytest.raises(Exception) as info:
        TypeAdapter(Annotated[int, Field(ge=5)]).validate_python(1)
    assert validation_text(info.value) == "other", (
        f"outside the closed list: {validation_text(info.value)}"
    )


def test_json_decode_error_prints_code_and_position_only() -> None:
    e = corpus._f_json(CAN, CAN, 4)
    out = render(diagnose(e, step=Where.extract))
    assert CAN not in out and out.endswith(" position=4") and "code=validation_failed" in out


def test_diagnose_reads_type_and_count() -> None:
    out = render(diagnose(err("many", {"a": CAN}), step=Where.config_load))
    assert re.fullmatch(
        r"pydantic_core\._pydantic_core\.ValidationError: diag_v=1 code=validation_failed step=config_load at=- fp=[0-9a-f]{8} "
        r"type=[a-z_]+ count=7",
        out,
    ), out


def test_pydantic_error_reads_are_closed_ast() -> None:
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src/hadavin_sdk/guard/diagnostic.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "errors"
    ]
    assert len(calls) == 1
    kws = {k.arg: ast.literal_eval(k.value) for k in calls[0].keywords}
    assert kws == {"include_url": False, "include_context": False, "include_input": False}
    fn = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_error_types"
    )
    assert calls[0] in list(ast.walk(fn))
    subs = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
    ]
    assert {s.slice.value for s in subs} == {"type"}


@pytest.mark.parametrize("n", range(3))
def test_t6_real_config_typo(n: int) -> None:
    from hadavin_sdk.config import Config

    try:
        Config.model_validate({"zzz_typo": n})
    except Exception as e:  # noqa: BLE001
        out = render(diagnose(e, step=Where.config_load))
        assert "code=validation_failed step=config_load" in out and "zzz_typo" not in out
        assert grammar_ok(validation_text(e), "V")
    else:
        raise AssertionError("validated")
