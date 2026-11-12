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
  `ConfigValueError` (the marker for "Hadavin wrote this sentence"), else it is a fixed `ConfigValueError`; every other text
  (the typed tag of `union_tag_invalid`, the text a library puts in `error`, which may quote a character of the input) is `HIDDEN`.
- `msg`: pydantic builds it again from `type` and `ctx`, so it holds nothing that the rebuilt `ctx` does not.

Covered: `Model(...)`, and `model_validate`, `model_validate_json`, `model_validate_strings`, which pydantic routes through the
`__init__` of a model that defines one (`__pydantic_custom_init__`; a test pins this). One consequence, stated plainly: the options
`strict=`, `context=` and `from_attributes=` of those three methods are ignored on such a model (the model's own `model_config`
still applies); no call in `src/` or `demos/` relies on them (`tests/test_q8a1_b18_fixes.py` fails when one does).
NOT covered: a `TypeAdapter(Model)` made by the caller, which calls the validator directly and does not pass through the model
class; `model_construct`, which validates nothing."""

from __future__ import annotations

import enum
import functools
import typing
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from hadavin_sdk.errors import UNKNOWN_KEY, ConfigValueError, shown_name

HIDDEN = "<hidden>"
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


def _context(kind: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """`ctx` with every text that may hold input replaced (see the module text)."""
    out: dict[str, Any] = {}
    for key, value in ctx.items():
        if kind in _ERROR_KINDS and key == "error":
            out[key] = value if isinstance(value, ConfigValueError) else ConfigValueError(REFUSED)
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
    return ValidationError.from_exception_data(exc.title, lines, hide_input=True)


class HiddenInputModel(BaseModel):
    """A model whose `ValidationError` holds no text of the refused input in `str`, `repr`, `args`, `errors()` or `json()`."""

    model_config = ConfigDict(hide_input_in_errors=True)

    def __init__(self, /, **data: Any) -> None:
        hidden = None
        try:
            super().__init__(**data)
        except ValidationError as exc:
            hidden = without_input(exc, type(self))
        if hidden is not None:
            raise hidden  # outside the `except`, so the first error is not kept as `__context__`
