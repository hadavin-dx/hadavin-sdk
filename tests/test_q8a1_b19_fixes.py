"""Q8a-1 batch 19: tests of the fixes. Every value that must not be seen is built from parts (no secret-shaped literal)."""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path

import pytest
from pydantic import ValidationError

from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk.hidden_input import HIDDEN, HiddenInputModel, without_input
from tests.test_q8a1_b18_fixes import _every_model_class, _Probe

ROOT = Path(__file__).resolve().parent.parent


def _c19(tag: str) -> str:
    return "zq-b19-" + tag + "-" + "wm4"


def _all_text(exc: BaseException) -> str:
    """Every place the text of a refusal can sit: `str`, `repr`, `args`, `errors()` and `json()` in every form, the `ctx` error
    object of each problem and ITS `__cause__` / `__context__` chain, and the same for the chain of the error itself."""
    parts: list[str] = []
    seen: set[int] = set()
    todo: list[BaseException] = [exc]
    while todo:
        e = todo.pop()
        if id(e) in seen:
            continue
        seen.add(id(e))
        parts += [str(e), repr(e), repr(e.args)]
        if isinstance(e, ValidationError):
            rows = e.errors(include_input=True, include_url=True, include_context=True)
            parts += [
                repr(rows),
                e.json(include_input=True, include_context=True),
                e.json(),
                repr(e.errors()),
            ]
            for row in rows:
                inner = (row.get("ctx") or {}).get("error")
                if isinstance(inner, BaseException):
                    todo.append(inner)
        for nxt in (e.__cause__, e.__context__):
            if nxt is not None:
                todo.append(nxt)
    return "\n".join(parts)


# ---- Issue 1: every entry shape, every HiddenInputModel ----------------------------------------------------------------------
# Class: an input-bearing error built by a library on a path that does not pass the guard (CWE-209: error message with data of
# the request). pydantic-core calls `__init__` of a model with a custom `__init__` only for a mapping; a string, a list, `None`,
# a number, an object and the text of `model_validate_json` / `model_validate_strings` are checked by pydantic-core itself.
# Standard: pydantic docs, "Validators > Model validators": `model_validate*` is the entry that all shapes pass.


def _entry_shapes(c: str):
    """(label, how, argument): every shape a caller can hand to the three class methods."""
    return [
        ("str", "validate", c),
        ("list", "validate", [c]),
        ("list_of_list", "validate", [[c]]),
        ("none", "validate", None),
        ("int", "validate", 7),
        ("bytes", "validate", c.encode()),
        ("tuple", "validate", (c, c)),
        ("set", "validate", {c}),
        ("dict_key", "validate", {c: 1}),
        ("dict_value", "validate", {"x": c}),
        ("dict_nested", "validate", {"x": {c: {c: [c]}}}),
        ("dict_int_key", "validate", {1: c}),
        ("bad_json", "json", c),
        ("bad_json_open", "json", '{"a": "' + c),
        ("json_str", "json", json.dumps(c)),
        ("json_list", "json", json.dumps([c])),
        ("json_none", "json", "null"),
        ("json_int", "json", "7"),
        ("json_dict_key", "json", json.dumps({c: 1})),
        ("json_dict_value", "json", json.dumps({"x": c})),
        ("json_nested", "json", json.dumps({"x": {c: [c]}})),
        ("json_bytes", "json", c.encode()),
        ("strings_str", "strings", c),
        ("strings_list", "strings", [c]),
        ("strings_dict_key", "strings", {c: "1"}),
        ("strings_dict_value", "strings", {"x": c}),
        ("strings_none", "strings", None),
    ]


def _call(cls, how: str, arg):
    if how == "validate":
        return cls.model_validate(arg)
    if how == "json":
        return cls.model_validate_json(arg)
    return cls.model_validate_strings(arg)


def _refused(cls, how: str, arg) -> ValidationError | None:
    try:
        _call(cls, how, arg)
    except ValidationError as exc:
        return exc
    return None


def test_every_entry_shape_of_every_hidden_input_model_holds_no_refused_text():
    classes = [c for c in _every_model_class() if issubclass(c, HiddenInputModel)]
    assert len(classes) > 40, "the scan found too few model classes"
    refused = 0
    leaks: list[str] = []
    for cls in classes:
        c = _c19(cls.__name__)
        for label, how, arg in _entry_shapes(c):
            exc = _refused(cls, how, arg)
            if exc is None:
                continue
            refused += 1
            seen = _all_text(exc)
            if c in seen or c.upper() in seen or "input_value" in str(exc):
                leaks.append(f"{cls.__module__}.{cls.__name__} {how}:{label}")
            if exc.__cause__ is not None or exc.__context__ is not None:
                leaks.append(f"{cls.__name__} {how}:{label} keeps a cause or context")
    assert refused > 20 * len(classes), (
        f"the shapes were not refused ({refused}): the scan is empty"
    )
    assert leaks == [], (
        f"the refused text is in an error channel: {leaks[:12]} ({len(leaks)} in all)"
    )


@pytest.mark.parametrize(
    ("how", "method"),
    [
        pytest.param("validate", "model_validate", id="model_validate"),
        pytest.param("json", "model_validate_json", id="model_validate_json"),
        pytest.param("strings", "model_validate_strings", id="model_validate_strings"),
    ],
)
def test_each_class_method_hides_a_shape_that_does_not_reach_init(how, method):
    """One case per class method (so that one mutant per method has its own killer): a string and a text that is not JSON."""
    c = _c19("method-" + how)
    args = {
        "validate": [c, [c], None],
        "json": [c, '{"a": "' + c, json.dumps([c])],
        "strings": [c, [c]],
    }[how]
    for arg in args:
        exc = _refused(_Probe, how, arg)
        assert exc is not None, f"{method}: {arg!r} was not refused"
        assert c not in _all_text(exc), f"{method}: the refused text is still in the error"
        assert exc.__cause__ is None and exc.__context__ is None, (
            f"{method}: the first error is kept as cause or context"
        )


def test_a_refused_text_that_is_not_json_does_not_come_back_in_the_json_error():
    """The text pydantic-core puts in `ctx.error` of `json_invalid` is a library sentence about a position; it is hidden anyway."""
    c = _c19("badjson")
    exc = _refused(_Probe, "json", c)
    assert exc is not None
    kinds = {row["type"] for row in exc.errors()}
    assert kinds == {"json_invalid"}, kinds
    assert c not in _all_text(exc)
    ctx = exc.errors(include_context=True)[0]["ctx"]
    assert ctx["error"] == HIDDEN, f"the library text of a json error is kept: {ctx!r}"


def test_a_subclass_of_the_config_sentence_class_is_kept_as_that_class():
    """The loader tests for its own subclass of `ConfigValueError` (the stage rename sentence): clearing the chain keeps the class."""
    from pydantic import field_validator

    class _Named(ConfigValueError):
        pass

    class _Sub(HiddenInputModel):
        n: int = 0

        @field_validator("n", mode="before")
        @classmethod
        def _n(cls, v):
            raise _Named("n is renamed")

    for how, arg in (("validate", {"n": 1}), ("json", '{"n": 1}')):
        exc = _refused(_Sub, how, arg)
        assert exc is not None
        assert type(exc.errors(include_context=True)[0]["ctx"]["error"]) is _Named, (
            f"{how}: the class of the sentence is lost"
        )


def test_a_config_sentence_kept_in_the_context_has_no_cause_and_no_context_of_its_own():
    """A `ConfigValueError` raised `from` an error that quotes the value is kept by sentence only (the design residual of r19)."""
    from pydantic import field_validator

    c = _c19("chain")

    class _Chain(HiddenInputModel):
        n: int = 0

        @field_validator("n", mode="before")
        @classmethod
        def _n(cls, v):
            try:
                int(v)
            except ValueError as inner:
                raise ConfigValueError("n is not a whole number") from inner
            return v

    for how, arg in (("validate", {"n": c}), ("json", json.dumps({"n": c})), ("strings", {"n": c})):
        exc = _refused(_Chain, how, arg)
        assert exc is not None
        row = exc.errors(include_context=True)[0]
        inner = row["ctx"]["error"]
        assert isinstance(inner, ConfigValueError) and str(inner) == "n is not a whole number", row
        assert inner.__cause__ is None and inner.__context__ is None, (
            f"{how}: the kept sentence keeps its own chain"
        )
        assert c not in _all_text(exc), f"{how}: the text is in the chain of the kept sentence"


def _plain(exc: ValidationError) -> list[dict]:
    """`errors()` with each exception object of a context replaced by its class name and sentence (two objects never compare equal)."""
    rows = exc.errors(include_context=True, include_url=False)
    for row in rows:
        ctx = row.get("ctx") or {}
        for k, v in ctx.items():
            if isinstance(v, BaseException):
                ctx[k] = (type(v).__name__, str(v))
    return rows


def test_a_second_pass_over_a_rebuilt_error_changes_nothing():
    """`model_validate` of a dict goes through `__init__` and then through the class method: the second pass must keep what the
    first pass kept (the field name, the two fixed words of the place line, the sentence of the package)."""
    c = _c19("twice")
    for data in ({c: 1}, {"table": {c: {"n": "x"}}}, {"number": c}, {"backend": {"kind": c}}):
        first = _refused(_Probe, "validate", data)
        assert first is not None
        again = without_input(first, _Probe)
        assert _plain(again) == _plain(first), (
            f"a second pass changed the rebuilt error of {min(data)[:6]}"
        )


def test_the_place_line_of_a_dict_through_the_class_method_still_names_the_field():
    """Control against a double pass that blanks every name: the field names survive and the pasted keys do not."""
    exc = _refused(_Probe, "validate", {"table": {"k": {"n": "x"}}, _c19("loc"): 1})
    assert exc is not None
    places = sorted(row["loc"] for row in exc.errors())
    assert places == [("<unknown key>",), ("table", "<not shown>", "n")], places


def _random_value(rng: random.Random, c: str, depth: int = 0):
    kind = rng.randrange(9 if depth < 3 else 5)
    if kind == 0:
        return c
    if kind == 1:
        return rng.choice([None, True, 0, 7, -3, 2**70, 1.5, float("nan")])
    if kind == 2:
        return c[: rng.randrange(1, len(c))]
    if kind == 3:
        return rng.choice(["", " ", "{", "[", "null", "1"])
    if kind == 4:
        return c.encode()
    if kind == 5:
        return [_random_value(rng, c, depth + 1) for _ in range(rng.randrange(3))]
    if kind == 6:
        return {
            rng.choice([c, "n", "name", "table", "kind", 1]): _random_value(rng, c, depth + 1)
            for _ in range(rng.randrange(3))
        }
    if kind == 7:
        return {c: _random_value(rng, c, depth + 1)}
    return {"x": {c: _random_value(rng, c, depth + 1)}}


def test_fuzz_a_random_shape_never_puts_the_refused_text_in_the_error():
    """Seeded fuzz over every model class and the three entries (the same seed every run, so a failure can be repeated)."""
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
    classes = [c for c in _every_model_class() if issubclass(c, HiddenInputModel)]
    c = _c19("fuzz")
    refused = 0
    bad: list[str] = []
    for cls in classes:
        for _ in range(12):
            value = _random_value(rng, c)
            for how, arg in (
                ("validate", value),
                ("strings", value),
                (
                    "json",
                    json.dumps(value, default=lambda o: c)
                    if not isinstance(value, bytes)
                    else value,
                ),
            ):
                try:
                    exc = _refused(cls, how, arg)
                except (
                    TypeError,
                    ValueError,
                ):  # not text for the JSON entry: the library's own refusal, not a validation
                    continue
                if exc is None:
                    continue
                refused += 1
                if c in _all_text(exc) or exc.__cause__ is not None or exc.__context__ is not None:
                    bad.append(f"{cls.__name__} {how} {type(value).__name__}")
    assert refused > 200, f"the fuzz refused too little ({refused}): the scan is empty"
    assert bad == [], f"a random shape put the text in the error: {bad[:10]} ({len(bad)} in all)"


def test_the_base_defines_the_three_class_methods_itself():
    """The routing pin of the r19 Issue 1/2: the guard for a non-dict entry is these three methods; deleting one reopens it."""
    own = HiddenInputModel.__dict__
    for name in ("model_validate", "model_validate_json", "model_validate_strings"):
        assert name in own, (
            f"HiddenInputModel does not define {name}: a non-dict entry bypasses the guard"
        )
    assert "__init__" in own
    # the control: the entry the guard must cover is really not routed through `__init__` by pydantic-core
    calls: list[int] = []

    class _Seen(HiddenInputModel):
        n: int = 0

        def __init__(self, /, **data):
            calls.append(1)
            super().__init__(**data)

    _Seen.model_validate({"n": 1})
    assert len(calls) == 1, (
        "a dict is not routed through the custom __init__ any more (pydantic changed)"
    )
    assert _refused(_Seen, "validate", "text") is not None
    assert len(calls) == 1, (
        "a string reached __init__: the class methods are no longer the only guard for it"
    )


# ---- sibling check: every class method of the base is covered for a class made in a test ---------------------------------------


def test_a_subclass_made_in_a_test_with_its_own_validator_is_covered_too():
    from pydantic import field_validator

    c = _c19("subclass")

    class _Mine(HiddenInputModel):
        text: str = ""

        @field_validator("text", mode="before")
        @classmethod
        def _t(cls, v):
            if v == "boom":
                raise ValueError(c)
            return v

    for how, arg in (
        ("validate", {"text": "boom"}),
        ("json", json.dumps({"text": "boom"})),
        ("validate", c),
    ):
        exc = _refused(_Mine, how, arg)
        assert exc is not None
        assert c not in _all_text(exc), f"{how}: a plain ValueError text is in the error"
    assert ast  # the module is used by the later tests of this file


def test_a_mapping_with_a_key_that_is_not_text_is_a_validation_error_not_a_type_error():
    """Found while probing Issue 1: `model_validate({1: x})` died with `TypeError: keywords must be strings` (pydantic-core calls
    `__init__(**mapping)`), which a caller that catches `ValidationError` does not catch."""
    c = _c19("intkey")
    for how, arg in (
        ("validate", {1: c}),
        ("validate", {(c,): c}),
        ("strings", {b"k": c}),
        ("validate", {c: 1, 2: 3}),
    ):
        exc = _refused(_Probe, how, arg)
        assert exc is not None, f"{how}: {arg!r} was not refused as a validation error"
        assert c not in _all_text(exc), f"{how}: the key is printed"
        assert exc.errors(include_context=True)[0]["ctx"]["error"].args == (
            "a key of the mapping is not text",
        ), f"{how}: the sentence of a key that is not text changed"


# ---- Issue 2: the options that a dict entry ignores are not used anywhere --------------------------------------------------
# Class: a documented guard with no test (the docstring of `hidden_input.py` said a test fails when a call uses `strict=`,
# `context=` or `from_attributes=`; none existed, and `diagnosis.py` used `strict=`). pydantic-core calls the custom `__init__`
# for a mapping, and `__init__` takes no options, so for a dict these three options are ignored (the model config applies).

VALIDATE_OPTIONS = frozenset({"strict", "context", "from_attributes"})
VALIDATE_METHODS = frozenset({"model_validate", "model_validate_json", "model_validate_strings"})
# call sites allowed by file and line text, each with a written reason (the base's own forwarding only)
ALLOWED_VALIDATE_OPTIONS: dict[tuple[str, str], str] = {
    (
        "src/hadavin_sdk/hidden_input.py",
        "**",
    ): "the three class methods of the base forward the caller's own arguments unchanged",
}


def _validate_calls_with_options(source: str) -> list[tuple[int, str]]:
    """[(line, option)] for every `<x>.model_validate*(...)` call that gives `strict=`, `context=`, `from_attributes=` or a
    `**mapping` (which may hold them). Found with `ast`: a call through another name (`validate = Model.model_validate`) is not seen."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in VALIDATE_METHODS
        ):
            for kw in node.keywords:
                if kw.arg is None:
                    out.append((node.lineno, "**"))
                elif kw.arg in VALIDATE_OPTIONS:
                    out.append((node.lineno, kw.arg))
    return out


def test_the_scan_for_validate_options_finds_each_option_in_a_planted_source():
    planted = (
        "M.model_validate(x, strict=True)\n"
        "M.model_validate_json(x, context={})\n"
        "M.model_validate_strings(x, from_attributes=True)\n"
        "M.model_validate(x, **opts)\n"
        "M.model_validate(x)\n"
        "other.call(x, strict=True)\n"
    )
    assert _validate_calls_with_options(planted) == [
        (1, "strict"),
        (2, "context"),
        (3, "from_attributes"),
        (4, "**"),
    ]
    assert (
        _validate_calls_with_options(
            "M.model_validate(x)\nM.model_validate_json(x, by_alias=True)\n"
        )
        == []
    )


def test_no_call_in_src_or_demos_gives_an_option_that_a_dict_entry_ignores():
    found: list[str] = []
    scanned = 0
    for folder in ("src", "demos"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            scanned += 1
            rel = path.relative_to(ROOT).as_posix()
            for line, option in _validate_calls_with_options(path.read_text(encoding="utf-8")):
                if (rel, option) not in ALLOWED_VALIDATE_OPTIONS:
                    found.append(f"{rel}:{line} {option}")
    assert scanned > 100, f"the scan saw too few files ({scanned})"
    assert found == [], (
        f"a model_validate* call gives an option that a mapping entry ignores: {found}"
    )
    assert all(reason.strip() for reason in ALLOWED_VALIDATE_OPTIONS.values())


def test_a_dict_entry_ignores_strict_so_the_model_config_is_what_applies():
    """Pins the consequence the module text states: if pydantic starts to honour the option for a mapping, this fails and the
    module text and the scan above are reviewed."""
    assert _Probe.model_validate({"number": 5}, strict=True).number == 5
    assert _Probe.model_validate({"number": "5"}, strict=True).number == 5, (
        "strict= is honoured for a mapping now"
    )


# ---- Issue 5: every method of the store protocol is a read or a write by exact name ---------------------------------------------


def test_every_method_of_the_store_protocol_is_in_the_read_list_or_the_write_list():
    from tests._text_guard import (
        STORE_READS,
        STORE_WRITES,
        store_protocol_methods,
        unclassified_store_methods,
    )

    names = store_protocol_methods()
    assert len(names) > 25, "the scan found too few store methods"
    assert unclassified_store_methods(names) == [], (
        "a store method is in neither list (or a row is stale)"
    )
    assert not STORE_READS & STORE_WRITES, "a method is both a read and a write"
    writeish = (
        "create_",
        "save_",
        "add_",
        "set_",
        "put_",
        "purge_",
        "update_",
        "record_",
        "transition",
        "touch",
    )
    assert [n for n in STORE_READS if n.startswith(writeish)] == [], (
        "a read that is named like a write"
    )


def test_a_new_store_write_named_like_a_read_is_not_taken_for_a_read():
    from tests._text_guard import store_protocol_methods, unclassified_store_methods

    planted = (
        "class Store(Protocol):\n"
        "    def get_run(self, run_id): ...\n"
        "    def get_or_create_run(self, run_id): ...\n"
        "    def list_and_claim(self): ...\n"
        "    def __enter__(self): ...\n"
    )
    names = store_protocol_methods(planted)
    assert names == ("get_run", "get_or_create_run", "list_and_claim"), names
    said = unclassified_store_methods(names)
    assert "get_or_create_run" in said and "list_and_claim" in said and "get_run" not in said, (
        f"a new write named like a read is not reported as unclassified: {said}"
    )
    assert any(row.startswith("stale:") for row in said), (
        "a listed method that the planted protocol lacks is not reported stale"
    )


def test_the_write_methods_the_guard_scans_are_the_listed_writes():
    from tests._text_guard import STORE_WRITES, store_write_methods

    assert set(store_write_methods()) == set(STORE_WRITES) and len(store_write_methods()) == len(
        STORE_WRITES
    ), "the write methods the guard scans are not the listed writes"


# ---- Issue 6: what the text guard sees and does not see of a name that reaches a stored record ----------------------------------
# The guard follows TEXT OF AN ERROR (or text made on the spot) into a stored record. It has no source for "a configured name":
# a parameter that holds an agent id is exactly what a record is meant to store, so the scan cannot tell a configured name from a
# legitimate field. The shapes below are pinned both ways: the error-derived form is found, the name-derived form is not seen,
# and the CHANGELOG lists the unseen forms. If the guard learns one, the second table fails and the CHANGELOG list is updated.


def _found(code: str) -> int:
    from tests.test_stage_names import _guard_violations

    return len(_guard_violations({"m.py": code}, allowed={}, exempt={})[0])


_STORED_FROM_AN_ERROR = {
    "a record class given the text of an error by keyword": "def f(g):\n    try:\n        g()\n    except OSError as exc:\n        return AuditEvent(operation=str(exc))",
    "an item of a record set to the text of an error": "def f(g, rec):\n    try:\n        g()\n    except OSError as exc:\n        rec['agent'] = str(exc)",
    "a store method given the text of an error by keyword": "def f(g, store):\n    try:\n        g()\n    except OSError as exc:\n        store.insert_event(detail=str(exc))",
}


@pytest.mark.parametrize("shape", sorted(_STORED_FROM_AN_ERROR))
def test_an_error_text_that_reaches_a_stored_record_is_found(shape):
    assert _found(_STORED_FROM_AN_ERROR[shape]) >= 1, shape


_STORED_FROM_A_NAME = {
    "a record class given a configured name by keyword": "def f(name):\n    return AuditEvent(operation=name)",
    "an item of a record set to a configured name": "def f(rec, agent_cfg_name):\n    rec['agent'] = agent_cfg_name",
    "a store method given a configured name by keyword": "def f(store, agent_cfg_name):\n    store.insert_event(detail=agent_cfg_name)",
}


@pytest.mark.parametrize("shape", sorted(_STORED_FROM_A_NAME))
def test_a_configured_name_that_reaches_a_stored_record_is_not_seen_and_the_changelog_says_so(
    shape,
):
    """The documented blind spot (see the section comment): pinned so that it can only change together with the CHANGELOG."""
    assert _found(_STORED_FROM_A_NAME[shape]) == 0, (
        f"{shape}: the guard sees it now: update the CHANGELOG list and this table"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "a configured name that is stored" in changelog, (
        "the CHANGELOG does not name the stored-name blind spot"
    )


# ---- Issue 7: `error_where(cleaned=True)` is reached only with a rebuilt error; a bundle folder is shown when it is listed --------


def test_a_plain_pydantic_error_is_rebuilt_before_the_place_line_shows_a_word_like_name():
    """`error_where(cleaned=True)` shows any word-like name; that is safe only for an error `without_input` made. A plain model's
    error that reaches `config_error_text` is rebuilt first (the mapping key below is word-like and was printed before)."""
    from pydantic import BaseModel

    from hadavin_sdk.config import config_error_text

    class _Plain(BaseModel):
        table: dict[str, int] = {}

    c = _c19("plain")
    with pytest.raises(ValidationError) as raised:
        _Plain.model_validate({"table": {c: "not a number"}})
    assert c in str(raised.value.errors()), "the control: the plain error does hold the key"
    text = config_error_text(raised.value)
    assert c not in text, f"a word-like key of a plain model is printed: {text}"
    assert "<not shown>" in text and "table" not in text.split("\n")[1], text


def test_a_rebuilt_error_is_not_rebuilt_a_second_time_by_the_config_text():
    """The control of the test above: an error of a `HiddenInputModel` keeps its field names in the config text."""
    from hadavin_sdk.config import config_error_text

    exc = _refused(_Probe, "validate", {"table": {"k": {"n": "x"}}})
    assert exc is not None
    assert config_error_text(exc).split("\n")[1].startswith("table."), config_error_text(exc)


def test_a_bundle_folder_that_is_not_listed_is_not_shown_and_a_missing_parent_is_a_refusal(
    tmp_path,
):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle

    with pytest.raises(
        BundleError, match="bundle <not shown>: folder name must look like case-001"
    ):
        load_bundle(tmp_path / "no-such-parent" / "case-001")
    (tmp_path / "case-012").mkdir()
    with pytest.raises(BundleError) as listed:
        load_bundle(tmp_path / "case-012")
    assert "bundle case-012: manifest.json is missing" in str(listed.value), (
        f"a listed folder name was not shown: {listed.value}"
    )
    (tmp_path / ("case-" + "7" * 25)).mkdir()
    with pytest.raises(BundleError, match="bundle <not shown>: "):
        load_bundle(tmp_path / ("case-" + "7" * 25))
