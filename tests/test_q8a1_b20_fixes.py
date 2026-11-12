"""Q8a-1 batch 20: tests of the fixes of round 20 (classes A, B, D). Every value that must not be seen is built from parts."""

from __future__ import annotations

import collections.abc
import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field, ValidationError, field_validator

from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk.hidden_input import HIDDEN, HiddenInputModel, is_rebuilt, without_input
from tests.test_q8a1_b19_fixes import _all_text, _refused

ROOT = Path(__file__).resolve().parent.parent


def _c20(tag: str) -> str:
    return "zq-b20-" + tag + "-" + "wm4"


class _Inner(HiddenInputModel):
    name: str = "x"


class _Outer(HiddenInputModel):
    inner: _Inner | None = None
    table: dict[str, _Inner] = Field(default_factory=dict)
    rows: list[_Inner] = Field(default_factory=list)


class _Boom(HiddenInputModel):
    n: int = 0

    @field_validator("n", mode="before")
    @classmethod
    def _n(cls, v):
        raise TypeError("a bug of the caller")


class _AMapping(collections.abc.Mapping):
    """A mapping that is not a `dict`."""

    def __init__(self, data):
        self._d = data

    def __getitem__(self, k):
        return self._d[k]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)


# ---- A1: a key that is not text, in every spelling, is a validation error with a fixed sentence ---------------------------------
# Class: a library `TypeError` ("keywords must be strings", raised by Python when pydantic-core spreads a mapping into `__init__`)
# escaping a guard that promises a `ValidationError`. Probe: `handover/evidence/Q8a-1/b20-builder/probe-a1.py` (the nested and
# keyword spellings raised a bare TypeError on a24d98ae; the top-level positional dict and a non-dict mapping did not).


def _assert_fixed_refusal(exc: ValidationError, c: str) -> None:
    assert c not in _all_text(exc), "the refused key is in the error"
    assert exc.__cause__ is None and exc.__context__ is None, (
        "the first error is kept as cause or context"
    )
    assert [r["type"] for r in exc.errors()] == ["value_error"], exc.errors()
    assert "a key of the mapping is not text" in str(
        exc.errors(include_context=True)[0]["ctx"]["error"]
    )


@pytest.mark.parametrize("method", ["model_validate", "model_validate_strings"])
def test_a_mapping_given_as_the_keyword_obj_with_a_key_that_is_not_text_is_a_validation_error(
    method,
):
    c = _c20("kw-" + method)
    for key in (1, b"k", (1, 2), None):
        with pytest.raises(ValidationError) as raised:
            getattr(_Outer, method)(obj={key: c})
        _assert_fixed_refusal(raised.value, c)


@pytest.mark.parametrize(
    "shape",
    [
        pytest.param(lambda c: {"inner": {1: c}}, id="field"),
        pytest.param(lambda c: {"table": {"k": {1: c}}}, id="dict_of_models"),
        pytest.param(lambda c: {"rows": [{1: c}]}, id="list_of_models"),
        pytest.param(lambda c: {"rows": [{"name": "x"}, {b"k": c}]}, id="second_of_list_bytes_key"),
    ],
)
@pytest.mark.parametrize("how", ["validate", "strings", "ctor"])
def test_a_non_text_key_nested_in_a_model_field_is_a_validation_error(shape, how):
    c = _c20("nested-" + how)
    data = shape(c)
    with pytest.raises(ValidationError) as raised:
        if how == "validate":
            _Outer.model_validate(data)
        elif how == "strings":
            _Outer.model_validate_strings(data)
        else:
            _Outer(**data)
    _assert_fixed_refusal(raised.value, c)


def test_a_type_error_of_the_caller_is_not_taken_for_a_refused_key():
    """Control of the catch: only Python's own sentence is rebuilt; another `TypeError` is a bug and stays one."""
    with pytest.raises(TypeError, match="a bug of the caller"):
        _Boom.model_validate({"n": 1})
    with pytest.raises(TypeError, match="a bug of the caller"):
        _Boom(n=1)
    with pytest.raises(TypeError, match="a bug of the caller"):
        _Boom.model_validate_strings({"n": "1"})


class _PlainInner(BaseModel):
    """A plain model with its own `__init__`: pydantic-core spreads a mapping into it, as into a `HiddenInputModel`."""

    def __init__(self, /, **data):
        super().__init__(**data)


class _PlainOuter(BaseModel):
    x: _PlainInner | None = None


def test_python_still_words_the_refusal_of_a_non_text_key_as_the_catch_expects():
    """Pins the sentence the catch looks for: if Python or pydantic-core changes it, this fails by name."""
    with pytest.raises(TypeError, match="keywords must be strings"):
        _PlainOuter.model_validate({"x": {1: 2}})


def test_a_mapping_that_is_not_a_dict_is_not_a_bare_type_error():
    """Control (passes on the old head too): pydantic-core does not spread a mapping of another class, so there is no
    `TypeError` to catch; it is accepted or refused as a validation problem, never a bare error."""
    c = _c20("map")
    for method in ("model_validate", "model_validate_strings"):
        try:
            getattr(_Outer, method)(_AMapping({1: c}))
        except ValidationError as exc:
            assert c not in _all_text(exc)


def test_a_dict_with_a_key_that_is_not_text_still_says_the_fixed_sentence_positionally():
    """Control (passes on the old head): the positional spelling that batch 19 fixed."""
    c = _c20("pos")
    with pytest.raises(ValidationError) as raised:
        _Outer.model_validate({1: c})
    _assert_fixed_refusal(raised.value, c)


# ---- A2: the "already rebuilt" mark cannot be pasted ------------------------------------------------------------------------------


def test_an_error_whose_inputs_read_hidden_is_rebuilt_before_the_place_line_is_shown():
    from hadavin_sdk.config import config_error_text

    class _Plain(BaseModel):
        table: dict[str, int] = {}

    c = _c20("forged")
    with pytest.raises(ValidationError) as raised:
        _Plain.model_validate({"table": {c: HIDDEN}})
    assert all(e["input"] == HIDDEN for e in raised.value.errors()), (
        "the control: every input reads the fixed word"
    )
    text = config_error_text(raised.value)
    assert c not in text, (
        f"a word-like key of an error that only reads like a rebuilt one is shown: {text}"
    )


def test_only_an_error_made_by_without_input_carries_the_mark():
    class _Plain(BaseModel):
        n: int = 0

    with pytest.raises(ValidationError) as plain:
        _Plain.model_validate({"n": HIDDEN})
    assert not is_rebuilt(plain.value), "a plain error is marked as rebuilt"
    made = without_input(plain.value)
    assert is_rebuilt(made), "an error made by without_input is not marked"
    refused = _refused(_Inner, "validate", {"name": 1})
    assert refused is not None and is_rebuilt(refused), (
        "the error of a HiddenInputModel is not marked"
    )
    assert is_rebuilt(without_input(made)), "a second pass loses the mark"


# ---- A3: a kept sentence has no traceback ---------------------------------------------------------------------------------------


def test_a_config_sentence_kept_in_the_context_has_no_traceback():
    """The frames of the raise hold the refused value in their local names; the kept error must not carry them."""
    c = _c20("tb")

    class _Tb(HiddenInputModel):
        n: int = 0

        @field_validator("n", mode="before")
        @classmethod
        def _n(cls, v):
            refused_value = v  # noqa: F841 - a local name that a traceback would show
            raise ConfigValueError("n is not valid")

    for how, arg in (("validate", {"n": c}), ("json", json.dumps({"n": c})), ("strings", {"n": c})):
        exc = _refused(_Tb, how, arg)
        assert exc is not None
        inner = exc.errors(include_context=True)[0]["ctx"]["error"]
        assert isinstance(inner, ConfigValueError)
        assert inner.__traceback__ is None, (
            f"{how}: the kept sentence keeps the frames of its raise"
        )


# ---- B3 (Z-ids): the place line keeps the field names in each of the three entries -------------------------------------------------


@pytest.mark.parametrize(
    ("how", "arg"),
    [
        pytest.param("validate", {"table": {"k": {"n": "x"}}, "pasted": 1}, id="model_validate"),
        pytest.param(
            "json", json.dumps({"table": {"k": {"n": "x"}}, "pasted": 1}), id="model_validate_json"
        ),
        pytest.param(
            "strings", {"table": {"k": {"n": "x"}}, "pasted": "1"}, id="model_validate_strings"
        ),
    ],
)
def test_each_entry_keeps_the_field_names_in_the_place_line(how, arg):
    from tests.test_q8a1_b18_fixes import _Probe

    exc = _refused(_Probe, how, arg)
    assert exc is not None
    places = sorted(row["loc"] for row in exc.errors())
    assert ("<unknown key>",) in places and any(p[:1] == ("table",) for p in places), (
        f"{how}: the place line lost the field name: {places}"
    )


# ---- B2: the mutant-list check can fail ---------------------------------------------------------------------------------------------


def test_the_mutant_check_fails_on_an_expected_text_that_is_in_no_file_and_on_a_pinned_id_that_is_not_a_test_id():
    from tools.mutation_runner import Mutant

    from tests._mutant_check import mutant_problems

    absent = "zq" + "-b20-" + "absent-" + "text"
    killer = "test_the_mutant_check_fails_on_an_expected_text_that_is_in_no_file_and_on_a_pinned_id_that_is_not_a_test_id"
    this = "tests/test_q8a1_b20_fixes.py"
    base = {"test_file": this, "only_test": killer}
    mutants = [
        Mutant("absent", "tools/mutation_runner.py", "import os", "import os2", absent, **base),
        Mutant(
            "pinned-absent",
            "tools/mutation_runner.py",
            "import os",
            "import os2",
            "mutant_problems",
            pinned=this[:-3] + "::" + killer + "[no-such-id]",
            **base,
        ),
        Mutant(
            "fine",
            "tools/mutation_runner.py",
            "import os",
            "import os2",
            "mutant_problems",
            pinned=this[:-3] + "::" + killer,
            **base,
        ),
    ]
    said = mutant_problems(ROOT, mutants)
    names = [s.split(":")[0] for s in said]
    assert names == ["absent", "pinned-absent"], said


def test_a_text_that_only_a_mutant_list_holds_is_not_found():
    """The search leaves the mutant lists out: the `expect` of a mutant is a literal of its own list, so counting it proves nothing."""
    from tests._mutant_check import _in_tree

    only_in_the_list = (
        "the taint of a dict " + "ignores its keys and values"
    )  # built from parts: this file must not hold it; a mutant name: a literal of stage_mutants.py only
    assert only_in_the_list in (ROOT / "tests/stage_mutants.py").read_text(encoding="utf-8")
    assert not _in_tree(ROOT, only_in_the_list), "a text that only a mutant list holds is found"
    assert _in_tree(ROOT, "mutant_problems"), "the control: a text of a test file is found"


def test_the_frozen_list_of_run_time_texts_holds_no_text_that_is_a_literal_now():
    """The frozen baseline must not hide a literal: a row whose text a search finds is stale and is removed."""
    from tests._dynamic_expects_baseline import DYNAMIC_EXPECTS
    from tests._mutant_check import _in_tree

    stale = sorted(n for n, e in DYNAMIC_EXPECTS if _in_tree(ROOT, e))
    assert stale == [], f"rows of the frozen list whose text is a literal now: {stale[:5]}"


# ---- D1: the parent folder of the bundles is listed once ---------------------------------------------------------------------------


def _make_cases(root: Path, n: int):
    from tests.k1b_support import make_bundle

    for i in range(1, n + 1):
        make_bundle(root, f"case-{i:03d}")


def test_load_bundles_lists_the_folder_once(tmp_path, monkeypatch):
    from hadavin_sdk.k1b.bundle import load_bundles

    _make_cases(tmp_path, 3)
    calls: list[Path] = []
    real = Path.iterdir

    def counting(self):
        if self == tmp_path:
            calls.append(self)
        return real(self)

    monkeypatch.setattr(Path, "iterdir", counting)
    assert len(load_bundles(tmp_path)) == 3
    assert len(calls) == 1, f"the bundles folder was listed {len(calls)} times, not once"


def test_a_sibling_folder_that_is_not_a_case_is_not_shown(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle

    (tmp_path / "notes").mkdir()
    (tmp_path / "case-012").mkdir()
    with pytest.raises(BundleError) as listed:
        load_bundle(tmp_path / "case-012")
    assert "bundle case-012: manifest.json is missing" in str(listed.value), listed.value
    with pytest.raises(BundleError) as sibling:
        load_bundle(tmp_path / "notes")
    assert "bundle <not shown>" in str(sibling.value) and "bundle notes" not in str(
        sibling.value
    ), f"a sibling folder that is not a case was shown: {sibling.value}"


def test_load_bundles_does_not_show_a_sibling_folder_that_is_not_a_case(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundles

    _make_cases(tmp_path, 1)
    (tmp_path / "notes").mkdir()
    with pytest.raises(BundleError) as sibling:
        load_bundles(tmp_path)
    assert "bundle <not shown>" in str(sibling.value) and "bundle notes" not in str(
        sibling.value
    ), f"load_bundles showed a sibling folder that is not a case: {sibling.value}"
