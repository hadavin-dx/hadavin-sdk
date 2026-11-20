"""E19 N3: a combining mark inside a result marker must not defeat the marker look-alike escape (model-visible spoof only).
Written by core-a as strict expected failures against the base; G13 (`_INVISIBLE_OR_MARK` in `escape_markers`) fixes it, so
core-c turned them into normal tests (core-a's branch wip/core-a-for-c-e19 documented the old limit)."""

import pytest

from hadavin_sdk.guard import runmap

CASES = ["<≮TOOL RESULT", "<<T̸OOL RESULT", "≮<TOOL RESULT", "<<TOOL̸ RESULT"]


def test_plain_marker_is_neutralised():
    assert runmap.escape_markers("<<TOOL RESULT call_id=1>>").startswith("[[")


@pytest.mark.parametrize("spoof", CASES)
@pytest.mark.parametrize("fn", [runmap.escape_markers, runmap.neutralise_untrusted])
def test_combining_mark_marker_is_neutralised_like_the_plain_one(spoof, fn):
    assert "[[" in fn(spoof)
