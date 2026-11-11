"""``validation_text`` (grammar V) and the validation facts of ``diagnose``."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
from pydantic_core import ValidationError, core_schema

from hadavin_sdk import defaults
from hadavin_sdk.codes import FACT_BOUNDS, VALIDATION_OTHER, VALIDATION_TYPES, FactKey, Where
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
    """The bound is computed from the closed list and the defaults, not typed in: at most ``DIAG_MAX_ERRORS`` closed names joined by
    ``"; "``, then ``"; +N more"`` with N at most the count bound. The 7-error input must match that shape exactly."""
    names = VALIDATION_TYPES | {VALIDATION_OTHER}
    longest = max(len(n) for n in names)
    n_max = defaults.DIAG_MAX_ERRORS
    hi = FACT_BOUNDS[FactKey.count][1]
    bound = n_max * longest + (n_max - 1) * len("; ") + len("; +") + len(str(hi)) + len(" more")
    out = validation_text(
        err("many", {"a": CAN, "b": CAN, "c": CAN, "d": CAN, "e": CAN, "f": CAN, "g": CAN})
    )
    alt = "|".join(sorted(map(re.escape, names)))
    assert re.fullmatch(rf"(?:{alt})(?:; (?:{alt})){{{n_max - 1}}}; \+2 more", out), out
    assert len(out) <= bound and grammar_ok(out, "V"), (len(out), bound)


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


def _fixture_config(tmp_path: Path) -> Path:
    """The fixture config folder copied under ``tmp_path`` (the same steps as ``tests.conftest.make_cfg``, which the mutation runner does not load)."""
    for name in ("config", "recorded", "inputs", "golden"):
        shutil.copytree(
            Path(__file__).parent / "fixtures" / name, tmp_path / name, dirs_exist_ok=True
        )
    root = tmp_path / "config"
    (root / "config.yaml").write_text(
        (root / "config.yaml").read_text(encoding="utf-8").replace("{port}", "0"), encoding="utf-8"
    )
    return root


def _config_problem(tmp_path: Path, **change: object) -> ValidationError:
    """The real ``Config`` model, built the way ``load_config`` builds it, with a stray key or a wrong value (ticket golden T6)."""
    from pydantic import ValidationError as PydanticError

    from hadavin_sdk.config import Config, _read_yaml, parse_backends

    root = _fixture_config(tmp_path)
    raw = _read_yaml(root / "config.yaml")
    for key in ("golden_dir", "inputs_dir"):
        raw[key] = root / raw[key]
    raw["backends"] = parse_backends(raw.get("backends"), root)
    try:
        Config(**{**raw, **change}, egress_hosts=frozenset(), root=root)
    except PydanticError as exc:
        return exc  # type: ignore[return-value]
    raise AssertionError("the real Config accepted the change")


T6_HEAD = r"pydantic_core\._pydantic_core\.ValidationError: diag_v=1 code=validation_failed step=config_load at=- fp=[0-9a-f]{8} "


def test_t6_a_stray_key_in_the_real_config_is_two_literal_outputs(tmp_path: Path) -> None:
    e = _config_problem(tmp_path, zzz_typo=1)
    out = render(diagnose(e, step=Where.config_load))
    assert re.fullmatch(T6_HEAD + r"type=extra_forbidden count=1", out), out
    assert validation_text(e) == "extra_forbidden"
    assert "zzz_typo" not in out and grammar_ok(out)


def test_t6_a_wrong_value_in_the_real_config_is_two_literal_outputs(tmp_path: Path) -> None:
    e = _config_problem(tmp_path, environment="nowhere")
    out = render(diagnose(e, step=Where.config_load))
    assert re.fullmatch(T6_HEAD + r"type=literal_error count=1", out), out
    assert validation_text(e) == "literal_error"
    assert "nowhere" not in out and grammar_ok(out)


def test_t6_through_the_loader_the_error_is_a_config_error_with_no_type_fact(
    tmp_path: Path,
) -> None:
    """``load_config`` wraps the pydantic error as ``ConfigError(str(exc))``: code ``config_invalid``, the own frame as locator, no type fact."""
    from hadavin_sdk import config as config_module
    from hadavin_sdk.config import load_config

    root = _fixture_config(tmp_path)
    (root / "config.yaml").write_text(
        (root / "config.yaml").read_text(encoding="utf-8") + "\nzzz_typo: 1\n", encoding="utf-8"
    )
    wrapped = "raise ConfigError(_validation_text(exc)) from exc"
    source = Path(config_module.__file__).read_text(encoding="utf-8").splitlines()
    line = 1 + next(i for i, text in enumerate(source) if text.strip() == wrapped)
    with pytest.raises(Exception) as info:
        load_config(root)
    out = render(diagnose(info.value, step=Where.config_load))
    assert re.fullmatch(
        rf"ConfigError: diag_v=1 code=config_invalid step=config_load at=config\.py:{line} fp=[0-9a-f]{{8}}",
        out,
    ), out
    assert "zzz_typo" not in out


def test_t6_five_thousand_links_of_a_cause_chain_read_zero_hostile_names() -> None:
    """The row that chains 5000 links: no link is asked for ``args``, ``__cause__``, ``__context__`` or ``__notes__`` (zero reads), and the
    only read of any counted name is the head's own ``__traceback__`` (the locator needs it): at most 1 read in all (the traceback is walked once per diagnosis), not one per link."""
    rows = [r for r in corpus.ROWS if r.spec.get("reads_zero")]
    assert [r.id for r in rows] == ["HC-size_time-05"]
    for r in rows:
        exc = corpus.build_exception(r.spec)
        assert corpus._Counting.reads == []
        render(diagnose(exc, step=Where.extract))
        reads = list(corpus._Counting.reads)
        assert {n for n in reads if n != "__traceback__"} == set(), reads[:5]
        assert len(reads) <= 1, f"{len(reads)} reads: the chain was walked"


def test_error_count_is_called_only_in_the_one_helper_and_no_input_is_read_by_name() -> None:
    """BN-4: ``error_count()`` is called in ``_error_types`` and nowhere else, and nothing in the module reads an ``"input"``,
    ``"msg"``, ``"ctx"`` or ``"loc"`` entry of an error (by ``.get(...)`` or by subscript)."""
    import ast

    src = Path(__file__).resolve().parents[1] / "src/hadavin_sdk/guard/diagnostic.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    banned = {"input", "msg", "ctx", "loc", "url"}
    helper = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_error_types"
    )
    inside = {id(n) for n in ast.walk(helper)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "error_count":
                assert id(node) in inside, f"line {node.lineno}: error_count() outside _error_types"
            if node.func.attr in ("get", "pop", "setdefault") and node.args:
                first = node.args[0]
                assert not (isinstance(first, ast.Constant) and first.value in banned), node.lineno
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in banned, (
                f"line {node.lineno}: reads a {node.slice.value!r} entry"
            )


def test_a_custom_error_with_free_text_never_reaches_the_text() -> None:
    """BN-23: a ``PydanticCustomError`` carries a free message and a context; neither appears in the closed text or the line."""
    from pydantic_core import PydanticCustomError

    secret = "free-" + "text-quentin-abernathy"  # made up

    def check(value: str) -> str:
        raise PydanticCustomError("my_own_type", "bad {thing}: " + secret, {"thing": secret})

    schema = core_schema.no_info_after_validator_function(check, core_schema.str_schema())
    from pydantic_core import SchemaValidator

    try:
        SchemaValidator(schema).validate_python("x")
    except ValidationError as exc:
        out = render(diagnose(exc, step=Where.config_load))
        assert (
            validation_text(exc) == "other"
        )  # a type that is not in the closed list is printed as "other"
        assert secret not in out and "my_own_type" not in out and grammar_ok(out, "A"), out
    else:
        raise AssertionError("the validator did not fail")
