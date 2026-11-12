"""One base class for the models whose refusal must never carry the refused value (Q8a-1 batch 17 Issue 5, batch 18 Issue 2).

pydantic can put text of the refused input in six places of a `ValidationError`: the key `input`, the place line (`loc`: a
pasted unknown key, a mapping key), the context (`ctx`: the typed tag of a union, the exception a validator raised), the message
(`msg`: "Value error, <text of the exception>"), and, through those, `str`, `repr`, `errors()` and `json()`. The setting
`hide_input_in_errors` closes `input` in two of those channels and nothing else. This base class closes all of them at the one
place every refusal passes (`without_input`, called from `__init__`): it re-raises a rebuilt error, outside the `except` block, so
the first error is not kept as `__context__` either (it would still hold the value).

What the rebuilt error keeps, and why it is code and not input:
- `input`: always the fixed word `HIDDEN`.
- `loc`: a position (a number) is kept; a name is kept only when it is a field name, an alias, a tag or a class name written in
  code (collected from the annotations of the model, see `code_words`), or when `errors.shown_name` shows it (the id of a thing the
  loader loaded). The last place of an `extra_forbidden` problem is the pasted key itself and is always `UNKNOWN_KEY`. Any other
  name is `NOT_SHOWN`.
- `ctx`: a number or a flag is kept (a limit); the text of a key in `_CODE_CTX` is kept (written in code: `expected`, `pattern`,
  `discriminator`, `expected_tags`); the `error` of a `value_error` or `assertion_error` is kept only when it is a
  `ConfigValueError` (the marker for "Hadavin wrote this sentence"; its `__cause__` and `__context__` are cleared, so the
  exception it was raised from is not kept), else it is a fixed `ConfigValueError`; every other text
  (the typed tag of `union_tag_invalid`, the text a library puts in `error`, which may quote a character of the input) is `HIDDEN`.
- `msg`: pydantic builds it again from `type` and `ctx`, so it holds nothing that the rebuilt `ctx` does not.

Covered: `Model(...)` and a mapping given to `model_validate`, `model_validate_json`, `model_validate_strings` (pydantic-core calls
`__init__` of a model that defines one, `__pydantic_custom_init__`), and every other shape given to those three methods (a string, a
list, `None`, a number, bytes, JSON text, text that is not JSON): pydantic-core checks those itself and never calls `__init__`, so
the base defines the three class methods too and rebuilds the error there (`tests/test_q8a1_b19_fixes.py` pins both entries, for
every model of the package). A mapping passes both guards; a second pass over a rebuilt error changes nothing (tested). A mapping
whose key is not text (`{1: x}`, also given as the keyword `obj=`, also nested in a model field) is refused as a `ValidationError`
with a fixed sentence: Python cannot spread it into `__init__`.
One consequence, stated plainly: the options `strict=`, `context=` and `from_attributes=` are ignored for a mapping (the model's own
`model_config` still applies); `tests/test_q8a1_b19_fixes.py` fails when a call in `src/` or `demos/` gives one, and pins the
ignoring itself, so a pydantic change is noticed.
NOT covered: a `TypeAdapter(Model)` made by the caller, which calls the validator directly and does not pass through the model
class; `model_construct`, which validates nothing; a model nested inside a parent that is not a `HiddenInputModel`."""

from __future__ import annotations

import enum
import functools
import typing
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, ValidationError

from hadavin_sdk.errors import UNKNOWN_KEY, ConfigValueError, shown_name

HIDDEN = "<hidden>"
_REBUILT_MARK = (
    object()
)  # private to this module: input text cannot hold it, so it cannot forge the mark (batch 20, A2)
# Python's own refusal of a mapping with a key that is not text, raised when pydantic-core spreads the mapping into `__init__`
_KEYWORDS_REFUSAL = "keywords must be strings"
REFUSED = (
    "the value was refused"  # the fixed sentence of a refusal whose own text may quote the value
)
# the text of these ctx keys is written in code (a type name, a pattern, the allowed words), never taken from the input
_CODE_CTX = frozenset({"expected", "pattern", "discriminator", "expected_tags"})
_ERROR_KINDS = frozenset(
    {"value_error", "assertion_error"}
)  # their ctx `error` is an exception object


@functools.lru_cache(maxsize=256)
def code_words(model: type[BaseModel]) -> frozenset[str]:
    """The names written in code that the place line of an error of `model` may hold: the field names and aliases of the model
    and of every model reachable through its annotations, their class names (a smart union names the member), the text values of a
    `Literal` (a union tag) and of an `Enum`. Never a name taken from the input."""
    words: set[str] = set()
    done: set[type] = set()  # the models already walked: a model that holds itself ends here

    def walk(tp: Any) -> None:
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            if tp in done:
                return
            done.add(tp)
            words.add(tp.__name__)
            for name, field in tp.model_fields.items():
                words.add(name)
                for alias in (field.alias, field.validation_alias):
                    if isinstance(alias, str):
                        words.add(alias)
                walk(field.annotation)
        elif isinstance(tp, type) and issubclass(tp, enum.Enum):
            words.update(str(m.value) for m in tp if isinstance(m.value, str))
        elif typing.get_origin(tp) is typing.Literal:
            words.update(a for a in typing.get_args(tp) if isinstance(a, str))
        elif isinstance(tp, typing.TypeAliasType):  # `type Rows = list[Inner]`
            walk(tp.__value__)
        else:
            for arg in typing.get_args(tp):
                walk(arg)

    walk(model)
    return frozenset(words)


def _place(error: dict[str, Any], words: frozenset[str]) -> tuple[int | str, ...]:
    """The place line of one problem with every name that is not written in code replaced (see the module text)."""
    loc = error["loc"]
    out: list[int | str] = []
    for i, part in enumerate(loc):
        if isinstance(part, int):
            out.append(part)
        elif error["type"] == "extra_forbidden" and i == len(loc) - 1:
            out.append(UNKNOWN_KEY)
        elif type(part) is str and part in words:
            out.append(part)
        else:
            out.append(shown_name(part))  # NOT_SHOWN unless it is the id of a loaded thing
    return tuple(out)


def _without_chain(error: ConfigValueError) -> ConfigValueError:
    """The same sentence and class (a caller may test for a subclass) with no `__cause__`, no `__context__` and no `__traceback__`:
    the exception a validator raised `from` another one keeps that one, and the other may quote the value (batch 19, Issue 1);
    the traceback keeps the frames of the raise, and their local names hold the value (batch 20, A3)."""
    error.__cause__ = None
    error.__context__ = None
    # the frames of the raise hold the refused value in their local names (batch 20, A3)
    return error.with_traceback(None)


def _context(kind: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """`ctx` with every text that may hold input replaced (see the module text)."""
    out: dict[str, Any] = {}
    for key, value in ctx.items():
        if kind in _ERROR_KINDS and key == "error":
            out[key] = (
                _without_chain(value)
                if isinstance(value, ConfigValueError)
                else ConfigValueError(REFUSED)
            )
        elif (
            isinstance(value, bool | int | float)
            or value is None
            or key in _CODE_CTX
            and type(value) is str
        ):
            out[key] = value
        elif key in _CODE_CTX and isinstance(value, list | tuple):
            out[key] = [v if type(v) is str else HIDDEN for v in value]
        else:
            out[key] = HIDDEN
    return out


def without_input(exc: ValidationError, model: type[BaseModel] | None = None) -> ValidationError:
    """The same problems as `exc` with no text of the refused input (see the module text); the title is kept. `model` is the model
    that refused: its code words keep the field names in the place line (without it, no name is kept)."""
    words = code_words(model) if model is not None else frozenset()
    lines: list[Any] = []
    for e in exc.errors(include_url=False, include_context=True, include_input=False):
        kind: str = e["type"]
        ctx = _context(kind, dict(e.get("ctx") or {}))
        line: dict[str, Any] = {"type": kind, "loc": _place(e, words), "input": HIDDEN, "ctx": ctx}
        try:
            ValidationError.from_exception_data(exc.title, [line])
        except (
            KeyError,
            ValueError,
            TypeError,
        ):  # a type pydantic does not know by name, or a ctx it cannot use
            line = {
                "type": "value_error",
                "loc": line["loc"],
                "input": HIDDEN,
                "ctx": {"error": ConfigValueError(REFUSED)},
            }
        lines.append(line)
    return _marked(ValidationError.from_exception_data(exc.title, lines, hide_input=True))


def _marked(rebuilt: ValidationError) -> ValidationError:
    """`rebuilt` with the private mark that `is_rebuilt` looks for (batch 20, A2)."""
    vars(rebuilt)["_hadavin_rebuilt"] = _REBUILT_MARK
    return rebuilt


def is_rebuilt(exc: ValidationError) -> bool:
    """True only for an error that `without_input` made (it carries the private mark). An error whose inputs merely read as the
    fixed word is not one: the word can be pasted into a config value (batch 20, A2)."""
    return getattr(exc, "_hadavin_rebuilt", None) is _REBUILT_MARK


def _not_text(cls: type[BaseModel]) -> ValidationError:
    """The refusal of a mapping whose key is not text, as an ordinary validation problem with a fixed sentence (the key is never
    printed)."""
    return ValidationError.from_exception_data(
        cls.__name__,
        [
            {
                "type": "value_error",
                "loc": (),
                "input": HIDDEN,
                "ctx": {"error": ConfigValueError("a key of the mapping is not text")},
            }
        ],
        hide_input=True,
    )


def _first_argument(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """The object given to `model_validate` and `model_validate_strings`: positional, or the keyword `obj` (batch 20, A1)."""
    return args[0] if args else kwargs.get("obj")


def _text_keys_only(cls: type[BaseModel], obj: Any) -> ValidationError | None:
    """pydantic-core hands a mapping to `__init__(**mapping)`, and Python refuses a key that is not text with a `TypeError`
    ("keywords must be strings"): not a `ValidationError`, so a caller that catches `ValidationError` would not catch it. Refuse
    the top-level shape here (a `dict`: the probe in `handover/evidence/Q8a-1/b20-builder/` shows pydantic-core does not spread a
    mapping of another class, and accepts it); a key of a mapping nested in a model field is caught by `_keywords_refusal`."""
    if isinstance(obj, dict) and any(type(k) is not str for k in obj):
        return _not_text(cls)
    return None


def _keywords_refusal(exc: TypeError) -> bool:
    """True for the `TypeError` Python raises when a mapping with a key that is not text is spread into `__init__`, anywhere
    in the nesting. Any other `TypeError` is a bug of the caller and is not hidden."""
    return any(_KEYWORDS_REFUSAL in part for part in exc.args if isinstance(part, str))


class HiddenInputModel(BaseModel):
    """A model whose `ValidationError` holds no text of the refused input in `str`, `repr`, `args`, `errors()` or `json()`."""

    model_config = ConfigDict(hide_input_in_errors=True)

    def __init__(self, /, **data: Any) -> None:
        hidden = None
        try:
            super().__init__(**data)
        except ValidationError as exc:
            hidden = without_input(exc, type(self))
        except TypeError as exc:  # a nested mapping with a key that is not text
            if not _keywords_refusal(exc):
                raise
            hidden = _not_text(type(self))
        if hidden is not None:
            raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    # Only a dict reaches `__init__` (pydantic-core calls it for a mapping). A string, a list, `None`, a number, an object, and
    # the text of `model_validate_json` are checked by pydantic-core itself, so the three class methods are the second entry
    # (Q8a-1 batch 19 Issue 1: the lead probe showed the value in `errors()` and `json()` for those shapes).
    @classmethod
    def model_validate(cls, *args: Any, **kwargs: Any) -> Self:
        hidden = _text_keys_only(cls, _first_argument(args, kwargs))
        try:
            if hidden is None:
                return super().model_validate(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc, cls)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    @classmethod
    def model_validate_json(cls, *args: Any, **kwargs: Any) -> Self:
        hidden = None
        try:
            return super().model_validate_json(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc, cls)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    @classmethod
    def model_validate_strings(cls, *args: Any, **kwargs: Any) -> Self:
        hidden = _text_keys_only(cls, _first_argument(args, kwargs))
        try:
            if hidden is None:
                return super().model_validate_strings(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc, cls)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`
