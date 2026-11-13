"""Walk the channels an error keeps (`__cause__`, `__context__`), shared by the tests of the sign-in and of `migrate`
(r19 group 7: the helpers lived in `tests/test_sign_in_channels.py`)."""

from __future__ import annotations

import traceback


def everything_kept(err: BaseException) -> list[BaseException]:
    """`err` and every error reachable from it through `__cause__` and `__context__` (what a log handler could walk)."""
    seen: list[BaseException] = []
    todo = [err]
    while todo:
        e = todo.pop()
        if e is None or any(e is s for s in seen):
            continue
        seen.append(e)
        todo += [e.__cause__, e.__context__]
    return seen


def assert_no_channel(err: BaseException, *words: str) -> None:
    """The refusal holds no other error on any channel, and none of `words` is in anything it keeps or prints."""
    assert err.__cause__ is None, "the refusal keeps the error it was made from (`from <error>`)"
    assert err.__context__ is None, (
        "the refusal was raised inside an `except` block (`__context__` is set)"
    )
    assert err.__suppress_context__ is False, (
        "`from None` hides the error from the printed traceback only"
    )
    assert everything_kept(err) == [err]
    shown = "".join(traceback.format_exception(err)) + "".join(str(e) for e in everything_kept(err))
    for word in words:
        assert word not in shown, shown
