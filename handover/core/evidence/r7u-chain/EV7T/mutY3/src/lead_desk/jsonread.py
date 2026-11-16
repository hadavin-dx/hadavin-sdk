"""The ONE place that parses JSON text that came from outside (a reply, a request body, a file, a stored row).

`json.loads` raises RecursionError (not ValueError) for text such as 30,000 opening brackets, so a caller that
catches only ValueError showed a Python error trace and, on a money path, left a reserved spend unsettled. Here the
RecursionError becomes `JsonTooDeep`, a ValueError: every caller already treats a ValueError as "this is not JSON" and
turns it into its own fixed one-line refusal. A repo test (tests/test_r7c_one_json_loader.py) fails when any other
file of the library, the scripts, the demos or the tools calls `json.loads` or `json.load` itself."""

from __future__ import annotations

import json
from typing import Any


class JsonTooDeep(ValueError):
    """The text nests so deeply that the JSON reader gave up. The text is fixed and never holds the input."""


def loads_bounded(raw: bytes | str, **kwargs: Any) -> Any:
    """`json.loads(raw, **kwargs)`; text nested too deeply raises JsonTooDeep (a ValueError), never RecursionError."""
    try:
        return json.loads(raw, **kwargs)  # the one call
    except RecursionError:
        raise JsonTooDeep("nested too deeply") from None
