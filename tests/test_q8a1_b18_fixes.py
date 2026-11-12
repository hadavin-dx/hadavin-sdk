"""Q8a-1 batch 18: tests of the fixes. Every value that must not be seen is built from parts (no secret-shaped literal)."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ---- Issue 1: the mutation runner's copy holds every repo-root file a test reads ------------------------------------------


RUNNERS = ("stage_mutants.py", "migration_numbers_mutants.py", "mutation_runner_mutants.py")


def _test_files_the_runners_run() -> set[str]:
    """Every `tests/test_*.py` text named by a mutation runner script (a mutant names its killer file, and `run_mutants` refuses a
    killer that is not in its copied list, so this is the list of copied test files or a superset of it)."""
    out: set[str] = set()
    for script in RUNNERS:
        for node in ast.walk(ast.parse((ROOT / "tests" / script).read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and re.fullmatch(r"tests/test_\w+\.py", node.value)
            ):
                out.add(node.value)
    return out


def _root_files_named_by_tests() -> dict[str, list[str]]:
    """{repo-root file name: test files (run by a mutation runner) that write `<something> / "<name>"`} found with `ast` (a path
    built another way, such as `Path("CHANGELOG.md")` or a string join, is NOT seen by this scan)."""
    names = {p.name for p in ROOT.iterdir() if p.is_file()}
    found: dict[str, list[str]] = {}
    run = _test_files_the_runners_run()
    assert run, "no runner names a test file: the scan is empty"
    for path in sorted((ROOT / "tests").rglob("*.py")):
        if path.name == Path(__file__).name or f"tests/{path.name}" not in run:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Div)
                and isinstance(node.right, ast.Constant)
                and node.right.value in names
            ):
                found.setdefault(node.right.value, []).append(path.name)
    return found


def test_the_runner_copies_every_repo_root_file_a_test_reads():
    from tools.mutation_runner import ROOT_FILES

    named = _root_files_named_by_tests()
    assert named, "no test names a repo-root file: the scan is empty"
    missing = sorted(n for n in named if n not in ROOT_FILES)
    assert missing == [], (
        f"a test reads a repo-root file that is not in ROOT_FILES, so a mutation copy cannot hold it: {missing}"
    )


def test_every_root_file_the_runner_copies_exists_and_is_a_plain_name():
    from tools.mutation_runner import ROOT_FILES

    assert ROOT_FILES, "ROOT_FILES is empty"
    for name in ROOT_FILES:
        assert "/" not in name and (ROOT / name).is_file(), (
            f"ROOT_FILES names {name!r}: not a file at the repository root"
        )


def _tree_with_a_changelog_reader(tmp_path):
    root = tmp_path / "repo"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests").mkdir()
    (root / "tests" / "test_core.py").write_text(
        "from pathlib import Path\n"
        "TEXT = (Path(__file__).resolve().parent.parent / 'CHANGELOG.md').read_text(encoding='utf-8')\n"
        "def test_a():\n    assert TEXT.startswith('top')\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text("top of the changelog\n", encoding="utf-8")
    return root


def test_a_test_that_reads_a_repo_root_file_passes_in_the_mutation_copy(tmp_path):
    from tools.mutation_runner import Mutant, run_mutants

    root = _tree_with_a_changelog_reader(tmp_path)
    mut = Mutant("m", "CHANGELOG.md", "top", "bottom", "assert")
    out = run_mutants(root, [mut], ["tests/test_core.py"], extra_dirs=())
    assert [(n, g) for n, _, _, g in out] == [("m", True)], (
        f"the copy did not hold CHANGELOG.md, or did not mutate it: {out}"
    )


def test_a_repo_root_file_that_is_not_listed_is_not_in_the_copy(tmp_path):
    """The control of the test above: with an empty list the same tree cannot start (so the test above proves the copy, not the tree)."""
    from tools.mutation_runner import run_mutants

    root = _tree_with_a_changelog_reader(tmp_path)
    with pytest.raises(RuntimeError, match="does not pass"):
        run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), extra_files=())


def test_the_baseline_leaves_out_a_timing_test_and_still_fails_on_a_plain_failure(tmp_path):
    from tools.mutation_runner import run_mutants

    root = tmp_path / "repo"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "tests").mkdir()
    timing = (
        "import pytest\n@pytest.mark.perf\ndef test_timing():\n    assert False\n"
        "def test_plain():\n    assert True\n"
    )
    (root / "tests" / "test_t.py").write_text(timing, encoding="utf-8")
    try:
        ran = run_mutants(root, [], ["tests/test_t.py"], extra_dirs=(), extra_files=())
    except RuntimeError:
        raise AssertionError("the baseline ran a perf test") from None
    assert ran == []
    (root / "tests" / "test_t.py").write_text(
        timing + "def test_broken():\n    assert False\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="does not pass"):
        run_mutants(root, [], ["tests/test_t.py"], extra_dirs=(), extra_files=())


# ---- Issue 2: a refused value is in no channel of the error: place line, context, message, siblings ---------------------------
# Class: a rebuilt error that keeps a part of the input (the CWE-209 shape: an error message that carries data of the request).
# Standard: pydantic documents `loc`, `ctx` and `msg` as built from the input and the validators' exceptions.

import json
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk.hidden_input import HIDDEN, HiddenInputModel, code_words, without_input


def _canary(tag: str) -> str:
    return "zq-b18-" + tag + "-" + "wm4"


def _everything(exc: BaseException) -> str:
    """`str`, `repr`, `args`, `errors()` in every form, `json()`, and the same for the whole chain (`__cause__`, `__context__`)."""
    parts, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        parts += [str(exc), repr(exc), repr(exc.args)]
        if isinstance(exc, ValidationError):
            parts += [
                repr(exc.errors()),
                exc.json(),
                repr(exc.errors(include_input=True, include_url=True, include_context=True)),
                json.dumps(exc.errors(include_context=False, include_input=False), default=str),
            ]
        exc = exc.__cause__ or exc.__context__
    return "\n".join(parts)


class _Row(HiddenInputModel):
    model_config = ConfigDict(extra="forbid")
    n: int


class _Fix(HiddenInputModel):
    kind: Literal["fix"]
    dsn: str


class _Other(HiddenInputModel):
    kind: Literal["other"]


class _Probe(HiddenInputModel):
    model_config = ConfigDict(extra="forbid")
    name: str = "x"
    table: dict[str, _Row] = Field(default_factory=dict)
    backend: Annotated[_Fix | _Other, Field(discriminator="kind")] | None = None
    ident: uuid.UUID | None = None
    number: int | None = None
    money: str | None = None
    raw: str | None = None

    @field_validator("number", mode="before")
    @classmethod
    def _number(cls, v):
        return int(v) if isinstance(v, str) else v

    @field_validator("money", mode="before")
    @classmethod
    def _money(cls, v):
        return str(float(v)) if isinstance(v, str) else v

    @field_validator("raw", mode="before")
    @classmethod
    def _raw(cls, v):
        if isinstance(v, str):
            bytes.fromhex(v)
        return v


def _refusals(data: dict):
    """The four ways a model is built from outside, each yielding the error it raises."""
    for how in ("init", "validate", "validate_json", "validate_strings"):
        with pytest.raises(ValidationError) as raised:
            if how == "init":
                _Probe(**data)
            elif how == "validate":
                _Probe.model_validate(data)
            elif how == "validate_json":
                _Probe.model_validate_json(json.dumps(data))
            else:
                _Probe.model_validate_strings(data)
        yield how, raised.value


_SHAPES = {
    "extra_forbidden": lambda c: {c: 1},
    "mapping_key": lambda c: {"table": {c: {"n": "not a number"}}},
    "mapping_key_extra": lambda c: {"table": {c: {"n": 1, c + "x": 2}}},
    "union_tag": lambda c: {"backend": {"kind": c}},
    "plain_value_error_int": lambda c: {"number": c},
    "plain_value_error_float": lambda c: {"money": c},
    "plain_value_error_hex": lambda c: {"raw": c},
    "library_error_text": lambda c: {"ident": c},
}


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_a_refused_value_is_in_no_channel_of_the_error_for_each_shape(shape):
    c = _canary(shape)
    data = _SHAPES[shape](c)
    for how, err in _refusals(data):
        seen = _everything(err)
        assert c not in seen and c.upper() not in seen, (
            f"{shape} via {how}: the refused text is still in str, repr, args, errors(), json() or the chain"
        )
        assert err.__cause__ is None and err.__context__ is None, (
            f"{shape} via {how}: the first error is kept as the cause or context"
        )


def test_the_place_line_keeps_a_field_name_and_hides_a_pasted_key():
    with pytest.raises(ValidationError) as raised:
        _Probe(**{_canary("k"): 1, "number": "x"})
    locs = sorted(map(tuple, (e["loc"] for e in raised.value.errors())))
    assert ("number",) in locs, "a field name written in code was hidden from the place line"
    assert ("<unknown key>",) in locs, "a pasted key is not the fixed word in the place line"


def test_the_place_line_of_a_mapping_key_is_not_shown_unless_it_is_a_loaded_id():
    from hadavin_sdk.errors import loaded_ids

    key = "agent-" + "one"
    with pytest.raises(ValidationError) as raised:
        _Probe(table={key: {"n": "x"}})
    assert raised.value.errors()[0]["loc"][:2] == ("table", "<not shown>"), (
        "a mapping key that no loader loaded is shown in the place line"
    )
    with loaded_ids([key]), pytest.raises(ValidationError) as raised:
        _Probe(table={key: {"n": "x"}})
    assert raised.value.errors()[0]["loc"][:2] == ("table", key), (
        "the id of a loaded thing is hidden: an operator cannot tell which entry is wrong"
    )


def test_a_fixed_sentence_of_the_package_is_kept_and_any_other_exception_text_is_not():
    class Own(HiddenInputModel):
        v: int | None = None

        @field_validator("v", mode="before")
        @classmethod
        def _check(cls, v):
            raise ConfigValueError("v must be a plain number")

    class Foreign(HiddenInputModel):
        v: int | None = None

        @field_validator("v", mode="before")
        @classmethod
        def _check(cls, v):
            raise ValueError("choked on " + str(v))

    with pytest.raises(ValidationError) as own:
        Own(v=1)
    assert "v must be a plain number" in str(own.value), (
        "the fixed sentence of the package was lost"
    )
    c = _canary("foreign")
    with pytest.raises(ValidationError) as foreign:
        Foreign(v=c)
    assert c not in _everything(foreign.value) and "the value was refused" in str(foreign.value), (
        "a foreign exception text is shown, or the refusal lost its fixed sentence"
    )


def test_a_ctx_text_of_a_library_is_the_fixed_word_and_a_limit_is_kept():
    class Limited(HiddenInputModel):
        ident: uuid.UUID | None = None
        short: Annotated[str, Field(max_length=3)] | None = None

    with pytest.raises(ValidationError) as raised:
        Limited(ident=_canary("u"), short="abcdef")
    by_type = {e["type"]: e for e in raised.value.errors()}
    assert by_type["uuid_parsing"]["ctx"]["error"] == HIDDEN, (
        "the library's text of a UUID error is shown"
    )
    assert by_type["string_too_long"]["ctx"]["max_length"] == 3, "a limit of a rule was dropped"


def test_a_problem_with_a_bad_context_becomes_one_fixed_refusal():
    c = _canary("x")
    raw = ValidationError.from_exception_data(
        "T", [{"type": "value_error", "loc": ("a",), "input": c, "ctx": {"error": ValueError(c)}}]
    )
    rebuilt = without_input(raw, None)
    assert c not in _everything(rebuilt), "the exception of a value_error was kept"
    assert rebuilt.errors()[0]["loc"] == ("<not shown>",), "without a model no name is kept"


def test_code_words_lists_fields_aliases_tags_enums_and_class_names_and_nothing_from_input():
    import enum

    class Color(enum.Enum):
        RED = "red"

    class Inner(HiddenInputModel):
        shade: Color = Color.RED
        outer_name: str = Field(default="", alias="outerAlias")

    class Holder(HiddenInputModel):
        items: list[Inner] = Field(default_factory=list)
        mode: Literal["fast", "slow"] = "fast"
        mapping: dict[str, Inner] = Field(default_factory=dict)

    words = code_words(Holder)
    assert {
        "items",
        "mode",
        "mapping",
        "shade",
        "outer_name",
        "outerAlias",
        "Inner",
        "Holder",
        "red",
        "fast",
        "slow",
    } <= words, f"a word written in code is missing: {sorted(words)}"
    assert code_words(Holder) is code_words(Holder), "the words are not cached"


def _every_model_class():
    import importlib
    import pkgutil

    import hadavin_sdk

    for m in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
        importlib.import_module(m.name)
    seen: set = set()

    def walk(c):
        for s in c.__subclasses__():
            if s not in seen:
                seen.add(s)
                yield s
                yield from walk(s)

    # the classes of the package's own files: another test builds a throw-away module `hadavin_sdk._round7_probe` in memory
    return [
        c
        for c in walk(BaseModel)
        if c.__module__.startswith("hadavin_sdk")
        and importlib.util.find_spec(c.__module__) is not None
        and importlib.util.find_spec(c.__module__).origin is not None
    ]


def test_every_model_class_of_the_package_refuses_without_the_refused_text():
    classes = _every_model_class()
    assert len(classes) > 40, "the scan found too few model classes"
    not_hidden = sorted(
        f"{c.__module__}.{c.__name__}" for c in classes if not issubclass(c, HiddenInputModel)
    )
    assert not_hidden == [], (
        f"a model class refuses with the pydantic text (the value shows): {not_hidden}"
    )
    for c in classes:
        if c is HiddenInputModel:  # the base itself allows extra keys: it is not built by anyone
            continue
        key = _canary("sibling")
        with pytest.raises(ValidationError) as raised:
            c(**{key: key})
        seen = _everything(raised.value)
        assert key not in seen, f"{c.__name__}: the key typed by a caller is in an error channel"


# ---- Issue 7: a str subclass never names an audit file; the words of a name are shown only for a loaded id ----------------------
# Class: a value whose type is checked with `isinstance` and then printed by a method the subclass can replace (CWE-704 type
# confusion; the object checked is not the object used). `shown_id` already used `type(x) is str`.


class _Sneaky(str):
    """A str whose text passes the check and whose `__str__` and `__format__` say something else."""

    def __str__(self) -> str:
        return "../zq-b18-escape"

    def __format__(self, spec: str) -> str:
        return "../zq-b18-escape"


def test_a_str_subclass_is_not_a_plain_event_name():
    from hadavin_sdk.models import plain_event_name

    assert plain_event_name("evt-" + "a" * 8) is True, "a plain id was refused"
    assert plain_event_name(_Sneaky("evt-aaaaaaaa")) is False, (
        "a str subclass was accepted as an event id"
    )


def test_the_local_audit_folder_never_names_a_file_from_a_str_subclass_id(tmp_path):
    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.audit.protocol import AuditUnavailable
    from hadavin_sdk.models import AuditEvent

    event = AuditEvent.model_construct(
        event_id=_Sneaky("evt-aaaaaaaa"),
        run_id="r",
        domain="d",
        operation="o",
        principal="p",
        source="s",
    )
    audit = LocalDirSink(tmp_path / "audit")
    with pytest.raises(AuditUnavailable):
        audit.write_intent(event)
    names = [p.name for p in (tmp_path).rglob("*")]
    assert not any("escape" in n for n in names), f"a file was named by the subclass text: {names}"


def test_write_intent_says_a_plain_name_problem_only_for_a_name_and_the_class_for_a_failed_write(
    tmp_path, monkeypatch
):
    """Issue 8: `write_intent` tests the name before its `try`; a failure of `_write` that is not the name (a serialisation
    error, whose library text may quote a value) is said by its class only, not as a name problem."""
    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.audit.protocol import AuditUnavailable
    from hadavin_sdk.models import AuditEvent

    audit = LocalDirSink(tmp_path / "audit")
    unplain = AuditEvent.model_construct(
        event_id="Evt-UPPER", run_id="r", domain="d", operation="o", principal="p", source="s"
    )
    with pytest.raises(AuditUnavailable, match="not a plain file name"):
        audit.write_intent(unplain)

    canary = _canary("serial")
    good = AuditEvent.model_construct(
        event_id="evt-" + "a" * 32, run_id="r", domain="d", operation="o", principal="p", source="s"
    )

    def broken(self, event):
        raise ValueError(canary)

    monkeypatch.setattr(LocalDirSink, "_write", broken)
    with pytest.raises(AuditUnavailable) as raised:
        audit.write_intent(good)
    assert "not a plain file name" not in str(raised.value)
    assert "ValueError" in str(raised.value)
    assert canary not in _everything(raised.value)


def test_every_purge_method_of_the_store_is_declared_to_give_a_number():
    """Issue 5 (Z65) and Issue 6: the rows of `runtime/tick.py` that add up what `purge_*` returns rest on the declaration of
    the store contract; the scan does not follow the type of a receiver, so this test reads the declaration itself."""
    tree = ast.parse((ROOT / "src/hadavin_sdk/store/protocol.py").read_text(encoding="utf-8"))
    store = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Store")
    purges = [
        n for n in store.body if isinstance(n, ast.FunctionDef) and n.name.startswith("purge_")
    ]
    assert len(purges) >= 2, "the store contract has too few purge methods: the scan is empty"
    for fn in purges:
        assert fn.returns is not None and ast.unparse(fn.returns) == "int", fn.name


def test_the_httpcode_check_accepts_only_the_library_class_with_its_import():
    """Issue 9: the HTTPCODE reason was accepted for any handler type that ends in `HTTPError`; it must be the class of
    `urllib.error`, with the import in the module."""
    from tests.test_guard_reasons import library_http_handler

    imported = ast.parse("import urllib.error\n")
    from_imported = ast.parse("from urllib import error\n")
    none = ast.parse("import json\n")
    assert library_http_handler("urllib.error.HTTPError", imported)
    assert library_http_handler("urllib.error.HTTPError", from_imported)
    assert not library_http_handler("urllib.error.HTTPError", none), "no import"
    assert not library_http_handler("my.module.HTTPError", imported), (
        "another class that ends in HTTPError"
    )
    assert not library_http_handler("HTTPError", imported)


def test_a_word_like_name_is_not_shown_when_no_loaded_set_was_given():
    from hadavin_sdk.errors import NOT_SHOWN, loaded_ids, shown_name

    word = "zq-b18-word"
    assert shown_name(word) == NOT_SHOWN, "a word-like name with no loaded set was shown"
    assert shown_name(word, loaded=[word]) == word, "a loaded name was hidden"
    with loaded_ids([word]):
        assert shown_name(word) == word, "a name of the active loaded set was hidden"
        assert shown_name("zq-b18-other") == NOT_SHOWN, (
            "a name outside the active loaded set was shown"
        )


# ---- Issue 4: a mutant whose text is no longer in its file is found by a quick test, not by the slow run ------------------------


def _load_mutant_list(script: str):

    spec = importlib.util.spec_from_file_location("_b18_" + script[:-3], ROOT / "tests" / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.M


@pytest.mark.parametrize("script", ["stage_mutants.py"])
def test_every_mutant_of_the_list_still_applies_to_its_file(script):
    from tests._mutant_check import mutant_problems

    mutants = _load_mutant_list(script)
    assert len(mutants) > 100, "the list holds too few mutants: the scan is empty"
    assert mutant_problems(ROOT, mutants) == [], "a mutant cannot apply (see the names)"


def test_the_mutant_check_names_each_kind_of_mutant_that_cannot_apply():
    from tools.mutation_runner import Mutant

    from tests._mutant_check import mutant_problems

    mk = lambda name, file, old, new, **kw: Mutant(name, file, old, new, "expect", **kw)
    mutants = [
        mk("gone", "tools/mutation_runner.py", "no such text zq-b18", "x"),
        mk("nofile", "tools/zq_b18_missing.py", "a", "b"),
        mk("same", "tools/mutation_runner.py", "import os", "import os"),
        mk(
            "nokiller",
            "tools/mutation_runner.py",
            "import os",
            "import os2",
            test_file="tests/test_q8a1_b18_fixes.py",
            only_test="test_zq_b18_missing",
        ),
        mk(
            "fine",
            "tools/mutation_runner.py",
            "import os",
            "import os2",
            test_file="tests/test_q8a1_b18_fixes.py",
            only_test="test_the_mutant_check_names_each_kind_of_mutant_that_cannot_apply",
        ),
        mk("fine", "tools/mutation_runner.py", "import os", "import os3"),
    ]
    said = mutant_problems(ROOT, mutants)
    kinds = [s.split(":")[0] for s in said]
    assert "nokiller" in kinds, f"the check missed a mutant whose killer does not exist: {said}"
    assert "fine" in kinds and "used twice" in said[-1], f"the check missed a repeated name: {said}"
    assert kinds == ["gone", "nofile", "same", "nokiller", "fine"], said
