"""The ONE place that makes an error safe to hand on when a secret was in play (a password, a key, a token, the AUTH
blob of a mail login). A library error can repeat what was sent (a mailbox server may echo the LOGIN line, and imaplib
puts that line in the text of its error), and Python keeps the earlier error as `__cause__` or `__context__` and keeps
every frame of the call, with its local names (`password`, `token`, `key`), reachable from `__traceback__`.
`raise ... from None` only hides the earlier error from a printout; it is still there for a program that reads it.

`scrub_error(exc)` cuts every earlier error and clears the frames of the call. `secret_boundary` wraps a function that
touches a secret: any error leaves it scrubbed, and an error of a class that is not ours (we write the text of our own
classes, never a library's) is replaced by one fixed refusal made OUTSIDE the `except` block, so it has no context.
A repo test (tests/test_r7n_findings.py) is a tripwire: it fails for a function it can see that touches a secret and
uses neither. It reads names, so it can miss a new way of touching a secret; it is not a proof.

What `scrub_error` does NOT follow (none of these is used in this repository): the members of an `ExceptionGroup`
(`.exceptions`), the notes added with `add_note` (`__notes__`), and an error held inside a generator or coroutine
that has not finished. It cuts errors only through `__cause__` and `__context__`, and it never rewrites the text in an
error's `args`: a `KeyboardInterrupt` or `SystemExit` leaves scrubbed of its chain and frames but with its own `args`.

Passed on untouched by the fallback (still scrubbed of chain and frames): `BaseException` classes that are not
`Exception` (Ctrl-C, `SystemExit`) and `MemoryError`. `MemoryError` is what callers such as the mail send hand straight
back on purpose (tests/test_except_clause_hierarchy.py); turning it into a refusal hid that, and the machine is out of
memory whatever the label says."""

from __future__ import annotations

import functools
import traceback
from collections.abc import Callable
from typing import Any, TypeVar, cast

E = TypeVar("E", bound=BaseException)
F = TypeVar("F", bound=Callable[..., Any])
PACKAGE = __name__.split(".", maxsplit=1)[0]


def scrub_error(exc: E) -> E:
    """Drop the cause and the context of `exc` and of everything reachable from it, and clear the local names of every
    finished frame in their tracebacks. Returns `exc`."""
    seen: set[int] = set()
    todo: list[BaseException | None] = [exc]
    while todo:
        e = todo.pop()
        if e is None or id(e) in seen:
            continue
        seen.add(id(e))
        todo += [e.__cause__, e.__context__]
        e.__cause__ = None
        e.__context__ = None
        e.__suppress_context__ = True
        if e.__traceback__ is not None:
            traceback.clear_frames(e.__traceback__)  # a frame that still runs is left alone
    return exc


def _ours(e: BaseException) -> bool:
    return type(e).__module__.split(".", maxsplit=1)[0] == PACKAGE


def secret_boundary(fallback: type[Exception] | None = None, text: str = "") -> Callable[[F], F]:
    """Decorator for a function that touches a secret. Every error that leaves it is scrubbed. With `fallback`, an
    `Exception` of a class that is not from this package becomes `fallback(text)` (a fixed text, no earlier error); a
    `MemoryError` and anything that is not an `Exception` leave as they are (scrubbed)."""

    def wrap(fn: F) -> F:
        @functools.wraps(fn)
        def inner(*args: Any, **kwargs: Any) -> Any:
            failure: Exception | None = None
            try:
                return fn(*args, **kwargs)
            except BaseException as e:
                scrub_error(e)
                args, kwargs = (), {}  # this frame stays in the traceback: it must not keep the secret it was given
                if fallback is None or not isinstance(e, Exception) or isinstance(e, MemoryError) or _ours(e):
                    raise
                failure = fallback(text)
            raise failure from None  # outside the `except` block: nothing is chained to the fixed error

        return cast(F, inner)

    return wrap
