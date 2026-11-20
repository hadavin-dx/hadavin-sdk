"""G7 fix round 1: the own-output rule (redact._mask) must not leave a secret in clear.

The rule leaves alone a value made only of escaped SECRET look-alikes (`‹SECRET_1›`, as `runmap.escape_placeholders`
writes them) and genuine `<SECRET_n>` tokens, and at most a cut-off SECRET opening at the end (E9(2): SECRET tokens only;
the older rule for a value of genuine placeholders of any kind is separate). It applies to the SECRET label only, accepts
only ASCII digits, and the whole value must match one anchored token shape: a secret wrapped in look-alike brackets, a
token of another kind (masked, and it makes one junk map entry), a mixed form, or a non-ASCII digit is masked as before G7. Every value here is made up and built from parts.
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


# --- E9(2): the exemption names the SECRET kind only ---------------------------------------------------------------


@pytest.mark.parametrize(
    "tail",
    ["<EMAIL_1", "<EMAIL_", "<EMA", "<I", "<IPV4_12", f"{L}IPV4_1{G}", f"{L}EMAIL_1{G}"],
)
def test_e9_a_cut_off_opening_or_lookalike_of_another_kind_is_masked(tail):
    """E9(2), changed shapes (fail before: `_OWN_OUTPUT` named every kind and left these unmasked; now masked whole)."""
    result = R.redact(f"password={tail}")
    assert result.text == "password=<SECRET_1>" and result.mapping == {"<SECRET_1>": tail}


def test_e9_a_secret_token_followed_by_a_cut_off_opening_of_another_kind_is_masked():
    value = f"{L}SECRET_1{G}<EMA"
    result = R.redact(f"password={value}")
    assert result.mapping == {"<SECRET_1>": value}


def test_e9_a_cut_off_opening_of_another_kind_alone_is_masked():
    """E9(2): `<EMA` is not the cut-off start of a SECRET token (fail before: any kind's opening was exempt). Killer of the cut-off-widening mutant."""
    result = R.redact("password=<EMA")
    assert result.text == "password=<SECRET_1>" and result.mapping == {"<SECRET_1>": "<EMA"}


def test_e9_a_lookalike_of_another_kind_alone_is_masked():
    """E9(2): `password=‹EMAIL_1›` is masked (fail before: exempt). Killer of the kind-widening mutant."""
    result = R.redact(f"password={L}EMAIL_1{G}")
    assert result.text == "password=<SECRET_1>" and result.mapping == {
        "<SECRET_1>": f"{L}EMAIL_1{G}"
    }


# --- E9(2) fix round: the tools error path with a token of ANOTHER kind after a key (accepted trade-off) -----------
#
# The first pass (`tools.error_reason`, a throwaway map) writes the tokens of every kind after a key (the EMAIL, IPV4, APIKEY,
# JWT, URLCRED, HIGHENTROPY and PHONE patterns run before the SECRET key=value pattern). The second pass (`prepare_output`,
# the run's map) escapes them, and the escaped spelling is a SECRET value that is masked: one junk map entry per distinct
# escaped token. Option (a) of the E9 review, core-c's default (security first: a real credential spelled like another
# kind's token must not stay in clear). Option (b), the lead's alternative, would exempt those escaped tokens on the tools
# path only (a flag from `neutralise_untrusted`); if the lead orders it, these tests change with it.

JWT = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ4eXoifQ" + "." + "c2ln" + "nYXR1cmVfeHl6AAAA"
APIKEY = "sk-" + "proj" + "-" + "Ab12Cd34Ef56Gh78Ij90" + "Kl12Mn34"


def _error_path(message: str):
    """The error text as the model sees it (first pass, then the run's pass), with the run map and its copy."""
    rmap = runmap.RunMap()
    reason = tools.error_reason(ValueError(message))
    out = tools.prepare_output(tools.ERROR_PREFIX + reason, rmap, 4096)
    return reason, out, rmap


_KIND_CASES = [
    ("jwt", f"call failed token={JWT} now", "token", "JWT_1"),
    ("apikey", f"call failed api_key={APIKEY} now", "api_key", "APIKEY_1"),
    ("email", "login failed password=a@b.co host", "password", "EMAIL_1"),
]


@pytest.mark.parametrize(
    ("name", "message", "key", "kind"), _KIND_CASES, ids=[c[0] for c in _KIND_CASES]
)
def test_e9_error_path_token_of_another_kind_after_a_key_makes_one_junk_entry(
    name, message, key, kind
):
    """Pins an ACCEPTED trade-off (option (a)); the lead's option (b) would exempt these escaped tokens instead.

    The first pass writes `key=<KIND_1>`; the second escapes it to `key=‹KIND_1›`, a SECRET value that is masked: ONE
    `<SECRET_n>` entry holding the escaped token. Not a leak (no real value is in the text or the map). The model loses the
    kind of the masked value; restore gives back nothing for a SECRET kind; a third pass makes no new entry.
    """
    reason, out, rmap = _error_path(message)
    assert f"{key}=<{kind}>" in reason
    assert out == "ERROR: ValueError: " + reason[len("ValueError: ") :].replace(
        f"<{kind}>", "<SECRET_1>"
    )
    assert dict(rmap) == {"<SECRET_1>": f"{L}{kind}{G}"}
    assert f"{key}=<SECRET_1>" in out
    assert JWT not in out and APIKEY not in out and "a@b.co" not in out
    # restore: a SECRET kind is never restored, the model-visible text stays as it is
    assert runmap.restore_text(out, dict(rmap)) == out
    # a third pass: the map does not grow; the text only gets its (now genuine-looking) token escaped, nothing masked again
    held = dict(rmap)
    third = tools.prepare_output(out, rmap, 4096)
    assert dict(rmap) == held
    assert third == out.replace("<SECRET_1>", f"{L}SECRET_1{G}")
    assert tools.prepare_output(third, rmap, 4096) == third and dict(rmap) == held


def test_e9_error_path_cut_off_opening_of_another_kind_makes_one_junk_entry():
    """Pins an ACCEPTED trade-off (option (a)); the lead's option (b) would exempt such a cut-off opening instead.

    The 160-character cut of `error_reason` lands inside `password=<EMAIL_1>`: the text ends `password=<EMA`. The second pass
    masks that value (a cut-off opening of another kind is not exempt): one junk entry `<SECRET_1>` = `<EMA`.
    """
    message = "ab " * 49 + "password=a@b.co tail"
    reason, out, rmap = _error_path(message)
    assert reason == "ValueError: " + "ab " * 49 + "password=<EMA"
    assert out == "ERROR: " + reason.replace("password=<EMA", "password=<SECRET_1>")
    assert dict(rmap) == {"<SECRET_1>": "<EMA"}
    held = dict(rmap)
    assert tools.prepare_output(out, rmap, 4096) == out.replace("<SECRET_1>", f"{L}SECRET_1{G}")
    assert dict(rmap) == held


def test_e9_a_junk_entry_in_the_run_map_keeps_later_genuine_placeholders_and_sweeps_a_stray_copy():
    """Pins the effect of the accepted junk entry (`<SECRET_1>` = `<EMA`) on a LATER text of the same run (review round 2, N4).

    A genuine `<EMAIL_1>` in a later text is not rewritten (a held-back edge value), a stray `<EMA` is swept into the entry's
    placeholder, and `redact_text` and `enforce_map` agree; neither adds an entry.
    """
    message = "ab " * 49 + "password=a@b.co tail"
    _reason, _out, rmap = _error_path(message)
    assert dict(rmap) == {"<SECRET_1>": "<EMA"}
    held = dict(rmap)
    for later, expected in (
        ("mail <EMAIL_1> here", "mail <EMAIL_1> here"),
        ("x<EMA<IPV4_1>", "x<SECRET_1><IPV4_1>"),
        ("plain <EMA end", "plain <SECRET_1> end"),
    ):
        assert runmap.redact_text(later, rmap) == expected
        assert runmap.enforce_map(later, rmap) == expected
        assert dict(rmap) == held
