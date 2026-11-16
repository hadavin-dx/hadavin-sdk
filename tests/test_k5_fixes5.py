"""Review 5 of PR #42: scrubbing a short secret grows the text (6 characters become the 17-character marker), so a tool
result far below the redactor's cap used to pass it after the scrub and was refused (`InputTooLarge`). The scrub now
cuts such a text back to the cap, with the cut said, at each of the three places that replace text."""

from __future__ import annotations

import base64
from urllib.parse import quote

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod

CAP = defaults.MAX_REDACT_CHARS
SECRET = "Zx9Qw" + "+"  # a fake, built from parts; 6 characters is the shortest that is scrubbed
MAX_BYTES = 200_000
MARKER = "<SECRET_REDACTED>"


def _check(out: str) -> None:
    assert SECRET not in out
    assert MARKER in out
    assert len(out.encode()) <= MAX_BYTES + len(tools_mod.TRUNCATED.encode())


# Below the cap before the scrub, over it after: 15,421 x 6 = 92,526 characters, 15,421 x 17 = 262,157.
@pytest.mark.parametrize("copies", [15_420, 15_421, 20_000])
def test_a_short_secret_repeated_below_the_cap_is_scrubbed_not_refused(copies):
    assert len(SECRET * copies) < CAP
    _check(tools_mod.prepare_output(SECRET * copies, {}, MAX_BYTES, [SECRET]))


def test_spaced_copies_are_scrubbed_not_refused():
    _check(tools_mod.prepare_output((SECRET + " ") * 20_000, {}, MAX_BYTES, [SECRET]))


def test_a_derived_token_that_grows_when_replaced_is_scrubbed_not_refused():
    """A 12-character base64 token that decodes to text holding the secret also becomes the 17-character marker."""
    token = base64.b64encode((SECRET + "abc").encode()).decode()
    assert len(token) == 12
    raw = (token + " ") * 20_000  # 260,000 characters, 360,000 after the replacement
    assert len(raw) < CAP
    _check(tools_mod.prepare_output(raw, {}, MAX_BYTES, [SECRET]))


def test_a_percent_encoded_secret_that_grows_when_replaced_is_scrubbed_not_refused():
    """The secret hides behind an encoding layer: the decoded view is used and it grows when replaced."""
    hidden = "%5A" + quote(
        SECRET[1:], safe=""
    )  # "Z" percent-encoded, the rest quoted: 10 characters
    assert len(hidden) == 10
    raw = (hidden + " ") * 20_000  # 220,000 characters, 360,000 after the replacement
    assert len(raw) < CAP
    _check(tools_mod.prepare_output(raw, {}, MAX_BYTES, [SECRET]))


def test_the_cut_text_still_fits_the_cap_with_its_marker():
    out = tools_mod._fit("x" * (CAP + 5000))
    assert len(out) <= CAP
    assert out.endswith(tools_mod.TRUNCATED)
    assert tools_mod._fit("x" * CAP) == "x" * CAP
