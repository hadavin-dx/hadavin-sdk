"""The scrub settings (`tools.prepare_output`), in a module of their own: `tools.py` must not import `config.py`
(which pulls in the backends table and, through it, code a tool module may not reach: a repo test pins that)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from hadavin_sdk import defaults
from hadavin_sdk.hidden_input import HiddenInputModel


# `BaseModel` is named too so the linter knows the class is a pydantic model
class _Strict(HiddenInputModel, BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ScrubSettings(_Strict):
    """How a tool result is scrubbed of the secrets the tool was handed (`tools.prepare_output`). Defaults in
    `hadavin_sdk/defaults.py`. Ranges keep a typo from switching the scrub off or making it quadratic."""

    tail_window: int = Field(default=defaults.SCRUB_TAIL_WINDOW, ge=16, le=4096)
    min_redaction_window: int = Field(
        default=defaults.SCRUB_MIN_REDACTION_WINDOW, ge=1024, le=defaults.MAX_REDACT_CHARS
    )
    min_secret: int = Field(default=defaults.SCRUB_MIN_SECRET, ge=4, le=64)
    fragment_scan: int = Field(default=defaults.SCRUB_FRAGMENT_SCAN, ge=64, le=16384)
    fragment_min: int = Field(default=defaults.SCRUB_FRAGMENT_MIN, ge=1, le=8)
    partial_end: int = Field(default=defaults.SCRUB_PARTIAL_END, ge=10, le=64)
