"""G7 fix round 1: the own-output rule (redact._mask) must not leave a secret in clear.

The rule leaves alone a value made only of escaped look-alikes (`‹SECRET_1›`, as `runmap.escape_placeholders` writes
them), genuine placeholders, and at most a cut-off placeholder opening at the end. It applies to the SECRET label
only, accepts only a real label of this redactor (upper case, as the redactor issues them) and ASCII digits, and the
whole value must match one anchored token shape: a secret wrapped in look-alike brackets, an unknown kind, a mixed
form, or a non-ASCII digit is masked as before G7. Every value here is made up and built from parts.
"""

from __future__ import annotations

import importlib
import sys

import pytest

from hadavin_sdk import tools
from hadavin_sdk.guard import runmap

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

PW = "hun" + "ter" + "2" + "zz"
SID = "Zx9" + "Qm4" + "Lp2" + "Vt7"
L, G = "‹", "›"


def _masked(text: str, secret: str) -> None:
    result = R.redact(text)
    assert secret not in result.text, result.text
    assert secret in "".join(result.mapping.values())


# --- a secret wrapped in look-alike brackets is masked -----------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        f"password={L}{PW}_1{G}",
        f"token={L}{PW}_12{G}",
        f"Cookie: sid={L}{SID}_3{G}",
        f"password={L}{PW}_1{G} host {L}IPV4_1{G}",
    ],
)
def test_a_secret_wrapped_in_lookalike_brackets_is_masked(text):
    _masked(text, PW if PW in text else SID)


def test_the_real_runmap_path_masks_a_wrapped_secret():
    rmap: dict[str, str] = {}
    out = runmap.redact_text(f"password={L}{PW}_1{G}", rmap)
    assert PW not in out and PW in "".join(rmap.values())


@pytest.mark.parametrize(
    "token",
    [
        f"{L}{PW}_1{G}",  # unknown kind
        f"{L}SECRET_x{G}",  # real label, non-digit suffix
        f"{L}SECRET_1a{G}",
        f"{L}SECRET{G}",  # no number
        f"{L}secret_1{G}",  # not as the redactor issues it
        f"{L}SE<X_1>CRET_1{G}",  # mixed form (reviewer dz-7)
        f"{L}SECRET_١{G}",  # Arabic-indic digit one
        f"{L}SECRET_1{G}{PW}",
    ],
)
def test_a_malformed_lookalike_is_masked(token):
    result = R.redact(f"password={token}")
    assert result.mapping, result.text
    assert result.text != f"password={token}"


# --- the legitimate own-output shapes are left alone, with no map entry -------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        f"password={L}SECRET_1{G}",
        f"password={L}SECRET_1{G} host {L}IPV4_1{G}",
        f"password={L}SECRET_1{G}; {L}SECRET_22{G}, <SECRET_3>",
    ],
)
def test_legitimate_own_output_is_left_alone(text):
    result = R.redact(text)
    assert result.text == text and result.mapping == {}


def test_the_measured_tool_error_path_still_adds_nothing():
    rmap = runmap.RunMap()
    runmap.redact_untrusted(f"db password={PW}x", rmap)
    held = dict(rmap)
    raw = tools.ERROR_PREFIX + tools.error_reason(ValueError(f"login failed password={PW}"))
    out = tools.prepare_output(raw, rmap, 4096)
    assert out == f"ERROR: ValueError: login failed password={L}SECRET_1{G}"
    assert dict(rmap) == held


def test_redact_untrusted_twice_adds_nothing():
    first = runmap.redact_untrusted(f"password={PW} x", {})
    rmap: dict[str, str] = {}
    second = runmap.redact_untrusted(first, rmap)
    assert second == f"password={L}SECRET_1{G} x" and rmap == {}


# --- a placeholder cut by the 160-character cut -------------------------------------------------------------------


@pytest.mark.parametrize("tail", ["<SECRET_1", "<SECRET_", "<SECRET", "<SEC", "<S"])
def test_a_cut_off_placeholder_is_not_a_new_secret(tail):
    result = R.redact(f"password={tail}")
    assert result.text == f"password={tail}" and result.mapping == {}


def test_a_cut_off_placeholder_after_a_whole_one_is_left_alone():
    text = "password=<SECRET_1> <SECRET_2"
    result = R.redact(text)
    assert result.mapping == {}


@pytest.mark.parametrize("tail", [f"<{PW}", "<SECRET_1x", "<secret_1", "<SECRET_1>" + PW])
def test_a_partial_opening_with_anything_else_is_masked(tail):
    result = R.redact(f"password={tail}")
    assert result.mapping, result.text


def test_the_cut_at_160_in_error_reason_adds_no_entry():
    msg = "x" * 140 + f" password={PW}"
    raw = tools.ERROR_PREFIX + tools.error_reason(ValueError(msg))
    rmap: dict[str, str] = {}
    out = tools.prepare_output(raw, rmap, 4096)
    assert PW not in out
    assert not any(v.startswith("<") for v in rmap.values())
