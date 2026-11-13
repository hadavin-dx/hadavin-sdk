"""One helper for tests that expect an input to be refused: when nothing is raised the failure line names the input
(`<what> was not refused`), so a mutation that lets one input through is told apart from a mutation that lets another
through. pytest's own `DID NOT RAISE <class ...>` line names no input and is not used for the mutant table. The failure is
an AssertionError (not `pytest.fail`), because the mutation judge counts only an AssertionError first line as a kill."""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def refused(exc: type[BaseException], what: str, *, match: str | None = None) -> Iterator[None]:
    """Expect `exc` (and, with `match`, that text in its message) from the block; fail naming `what` otherwise."""
    try:
        yield
    except exc as error:
        if match is not None and not re.search(match, str(error)):
            raise AssertionError(f"{what}: refused, but with another text: {error}") from None
        return
    raise AssertionError(f"{what} was not refused")
