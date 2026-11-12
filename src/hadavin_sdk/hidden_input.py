"""One base class for the models whose refusal must never carry the refused value (Q8a-1 batch 17, Issue 5).

pydantic puts the refused value in four places: the text of the error, `repr`, and, as the key `input`, in `errors()` and
`json()`. The setting `hide_input_in_errors` closes the first two and nothing else, so a caller that logs `exc.errors()` or
`exc.json()` still printed the value (a bad event id, a pasted key in a setting). This base class closes all four at the
one place every refusal passes: it re-raises the error with the value replaced by a fixed word (`<hidden>`), outside the `except`
block, so the first error is not kept as `__context__` either (it would still hold the value). The place line (`loc`), the kind of problem (`type`), the message
and the limits (`ctx`) are kept: they are written in code, not taken from the refused value.

Covered: `Model(...)`, `Model.model_validate(...)`, `model_validate_json(...)`, `model_validate_strings(...)`. NOT covered: a
`TypeAdapter(Model)` made by the caller, which calls the validator directly and does not pass through the model class."""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic_core import PydanticCustomError

HIDDEN = "<hidden>"


def without_input(exc: ValidationError) -> ValidationError:
    """The same problems as `exc` with every `input` replaced by `HIDDEN`; the title is kept."""
    lines: list[Any] = []
    for e in exc.errors(include_url=False, include_context=True, include_input=False):
        ctx = dict(e.get("ctx") or {})
        try:
            ValidationError.from_exception_data(
                exc.title, [{"type": e["type"], "loc": e["loc"], "input": HIDDEN, "ctx": ctx}]
            )
            kind: Any = e["type"]
        except (
            KeyError,
            ValueError,
            TypeError,
        ):  # a custom type that pydantic does not know by name
            kind = PydanticCustomError("hidden_input_refused", "the value was refused")
            ctx = {}
        lines.append({"type": kind, "loc": e["loc"], "input": HIDDEN, "ctx": ctx})
    return ValidationError.from_exception_data(exc.title, lines, hide_input=True)


class HiddenInputModel(BaseModel):
    """A model whose `ValidationError` holds no refused value in `str`, `repr`, `args`, `errors()` or `json()`."""

    model_config = ConfigDict(hide_input_in_errors=True)

    def __init__(self, /, **data: Any) -> None:
        hidden = None
        try:
            super().__init__(**data)
        except ValidationError as exc:
            hidden = without_input(exc)
        if hidden is not None:
            raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    @classmethod
    def model_validate(cls, *args: Any, **kwargs: Any) -> Self:
        try:
            return super().model_validate(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    @classmethod
    def model_validate_json(cls, *args: Any, **kwargs: Any) -> Self:
        try:
            return super().model_validate_json(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`

    @classmethod
    def model_validate_strings(cls, *args: Any, **kwargs: Any) -> Self:
        try:
            return super().model_validate_strings(*args, **kwargs)
        except ValidationError as exc:
            hidden = without_input(exc)
        raise hidden  # outside the `except`, so the first error is not kept as `__context__`
