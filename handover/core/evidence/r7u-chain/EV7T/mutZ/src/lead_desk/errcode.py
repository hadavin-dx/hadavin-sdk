"""The short code that is STORED for an unexpected error and later shown to a person (the follow-up list, the review
page). It is never the class name of a library or of Python itself: that name tells a person nothing and, for a library,
can name the product or the place behind a call. The code is the class name only for a class defined in this package
(CrmTimeout, ModelAnswerLost ...: each is written for the person who reads it); the three Python classes that the
follow-up ranking treats as "bad input before the CRM was asked" (KeyError, ValueError, LookupError, exactly these
three) become `data`; everything else becomes `error`. The operator log keeps its own class names (log lines are for
the operator, never for the person, and never carry the text of the error)."""

from __future__ import annotations

PACKAGE = __name__.split(".", maxsplit=1)[0]
BAD_INPUT_CLASSES: tuple[type[BaseException], ...] = (KeyError, ValueError, LookupError)
CODE_BAD_INPUT = "data"
CODE_OTHER = "error"


def error_code(exc: BaseException) -> str:
    """The code to store for `exc` (see the module text); never raises."""
    cls = type(exc)
    if cls.__module__.split(".", maxsplit=1)[0] == PACKAGE:
        return cls.__name__
    return CODE_BAD_INPUT if cls in BAD_INPUT_CLASSES else CODE_OTHER
