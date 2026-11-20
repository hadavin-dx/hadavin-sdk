"""G7 follow-up (ORDER 012 item 2): untrusted redaction applied to its OWN output adds nothing.

The caller that does it, always: a failing tool. `tools.error_reason` redacts the exception message with a throwaway
map and the untrusted hook, then `tools.prepare_output` redacts the result again with the RUN map and the same hook.
The second pass must escape the first pass's placeholders (`<SECRET_1>` of the throwaway map is not the run map's
`<SECRET_1>`), so `password=<SECRET_1>` becomes `password=‹SECRET_1›`. Before this change the value pattern then took
that escaped token for a new secret: the run map gained `<SECRET_n>` = `‹SECRET_1›`, a junk entry of a secret kind
whose "value" was swept from every later text.

The rule now (`redact._decide`; E9(2): SECRET tokens only, any other kind is masked): a value that is nothing but escaped look-alikes (`‹SECRET_n›`, exactly what
`runmap.escape_placeholders` writes) and genuine placeholders, with nothing besides but spaces, `;` and `,`, is left
alone, as a value of genuine placeholders alone already was. A value that holds a look-alike AND anything a secret
can be made of is masked whole, as before. Nothing is added to a map for an escaped token, so it restores to nothing.

Every value here is made up and built from parts.
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
OTHER_PW = "other" + "pw" + "77"
IP = "10." + "1.2.3"
DOC_IP = "10." + "9.9.9"
L, G = "‹", "›"  # the escaped look-alike's brackets
ESC_SECRET = f"{L}SECRET_1{G}"
ESC_IP = f"{L}IPV4_1{G}"


def _run_map_after_a_document() -> runmap.RunMap:
    rmap = runmap.RunMap()
    doc = runmap.redact_untrusted(f"db at {DOC_IP} password={OTHER_PW}", rmap)
    assert doc == "db at <IPV4_1> password=<SECRET_1>"
    return rmap


# --- the measured shape, through the real functions --------------------------------------------------------------


def test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text():
    rmap = _run_map_after_a_document()
    held = dict(rmap)
    exc = ValueError(f"login failed password={PW} host {IP}")
    raw = tools.ERROR_PREFIX + tools.error_reason(exc)
    assert raw == "ERROR: ValueError: login failed password=<SECRET_1> host <IPV4_1>"
    out = tools.prepare_output(raw, rmap, 4096)
    # escaped (the throwaway map's numbers are not the run map's), and NOT masked again
    assert out == f"ERROR: ValueError: login failed password={ESC_SECRET} host {ESC_IP}"
    assert dict(rmap) == held
    assert PW not in out and IP not in out


def test_the_error_path_output_reads_as_masked_with_the_hook_it_was_redacted_with():
    rmap = _run_map_after_a_document()
    exc = ValueError(f"login failed password={PW} host {IP}")
    out = tools.prepare_output(tools.ERROR_PREFIX + tools.error_reason(exc), rmap, 4096)
    held = dict(rmap)
    assert runmap.redact_untrusted(out, rmap) == out and dict(rmap) == held


def test_a_tool_that_echoes_a_secret_placeholder_from_its_arguments():
    """`restore_value` leaves secret-kind placeholders in a tool's arguments; an echo brings them back in."""
    rmap = _run_map_after_a_document()
    held = dict(rmap)
    out = tools.prepare_output("ran: psql password=<SECRET_1> -h <IPV4_1>", rmap, 4096)
    assert out == f"ran: psql password={ESC_SECRET} -h {ESC_IP}"
    assert dict(rmap) == held


def test_redact_untrusted_twice_is_once():
    rmap = runmap.RunMap()
    once = runmap.redact_untrusted(f"token={PW} at {IP}", rmap)
    assert once == "token=<SECRET_1> at <IPV4_1>"
    held = dict(rmap)
    twice = runmap.redact_untrusted(once, rmap)
    assert twice == f"token={ESC_SECRET} at {ESC_IP}"
    assert dict(rmap) == held
    assert runmap.redact_untrusted(twice, rmap) == twice and dict(rmap) == held


# --- security: a real secret beside, glued to or mixed with a look-alike is still masked -------------------------

GLUED = [
    ("after", f"password={ESC_SECRET}{PW}", f"{ESC_SECRET}{PW}"),
    ("before", f"password={PW}{ESC_SECRET}", f"{PW}{ESC_SECRET}"),
    ("between", f"password={ESC_SECRET}{PW}{ESC_IP}", f"{ESC_SECRET}{PW}{ESC_IP}"),
    ("dot-joined", f"password={ESC_SECRET}.{PW}", f"{ESC_SECRET}.{PW}"),
    ("one-letter", f"password={ESC_SECRET}k", f"{ESC_SECRET}k"),
    ("one-digit", f"password={ESC_SECRET}7", f"{ESC_SECRET}7"),
    (
        "non-ascii-letters",
        f"password={ESC_SECRET}" + "пар" + "оль",
        f"{ESC_SECRET}" + "пар" + "оль",
    ),
    ("punctuation-only", f"password={ESC_SECRET}!!??", f"{ESC_SECRET}!!??"),
    ("dot-joined-lookalikes", f"password={ESC_SECRET}.{ESC_IP}", f"{ESC_SECRET}.{ESC_IP}"),
    ("genuine-and-secret", f"password=<UUID_9>.{PW}", f"<UUID_9>.{PW}"),
]


@pytest.mark.parametrize(("name", "text", "value"), GLUED, ids=[g[0] for g in GLUED])
def test_a_value_with_a_lookalike_and_more_is_masked_whole(name, text, value):
    result = R.redact(text)
    assert result.text == "password=<SECRET_1>"
    assert result.mapping["<SECRET_1>"] == value
    assert PW not in result.text and "!!??" not in result.text


def test_a_real_secret_next_to_a_lookalike_is_masked():
    """Separate values on one line: the look-alike is left, the secret beside it is masked like any other."""
    result = R.redact(f"password={ESC_SECRET} token={PW} host {ESC_IP} peer {IP}")
    assert result.text == f"password={ESC_SECRET} token=<SECRET_1> host {ESC_IP} peer <IPV4_1>"
    assert result.mapping == {"<SECRET_1>": PW, "<IPV4_1>": IP}


def test_the_same_through_untrusted_redaction_with_a_typed_lookalike():
    """An attacker types the escaped spelling next to a real credential: the credential is masked."""
    rmap = runmap.RunMap()
    out = runmap.redact_untrusted(f"password={ESC_SECRET}{PW}\nkey={ESC_SECRET} token={PW}", rmap)
    assert PW not in out
    assert out == f"password=<SECRET_1>\nkey={ESC_SECRET} token=<SECRET_2>"
    assert rmap["<SECRET_1>"] == f"{ESC_SECRET}{PW}" and rmap["<SECRET_2>"] == PW


def test_a_cookie_of_lookalikes_with_a_real_session_id_is_masked_whole():
    sid = "Zx9" + "Qm4" + "Lp2" + "Vt7"
    result = R.redact(f"Cookie: a={ESC_SECRET}; sid={sid}")
    assert sid not in result.text
    assert sid in "".join(result.mapping.values())


# --- security: a forged look-alike is not restorable --------------------------------------------------------------


def test_a_lookalike_gets_no_map_entry_so_restore_gives_nothing_back():
    rmap = _run_map_after_a_document()
    held = dict(rmap)
    text = f"password={ESC_SECRET} host {ESC_IP}"
    out = runmap.redact_untrusted(text, rmap)
    assert out == text and dict(rmap) == held
    # the run map's genuine <SECRET_1> / <IPV4_1> are other values: the escaped spelling restores to itself
    assert runmap.restore_text(out, rmap) == text
    assert R.RedactionResult(out, dict(rmap)).restore(out) == text
    assert OTHER_PW not in runmap.restore_text(out, rmap)
    assert not runmap.has_placeholder(out)


def test_a_typed_genuine_placeholder_in_untrusted_text_is_still_escaped_never_kept():
    """The escape itself is untouched: untrusted `<SECRET_1>` never survives as the run map's placeholder."""
    rmap = _run_map_after_a_document()
    out = runmap.redact_untrusted("password=<SECRET_1> host <IPV4_1> and <ipv4_1>", rmap)
    assert "<SECRET_1>" not in out and "<IPV4_1>" not in out
    assert out == f"password={ESC_SECRET} host {ESC_IP} and {L}ipv4_1{G}"


# --- the rule's edges ---------------------------------------------------------------------------------------------


def test_only_the_exact_escaped_shape_is_left_alone():
    for value in (
        f"{L}SECRET{G}",  # no number
        f"{L}SECRET_x{G}",  # not a number
        f"{L}_1{G}",  # no kind
        f"{L}SECRET_1",  # not closed
        f"{L}{PW}{G}",  # a secret in the brackets
        f"{L}SECRET_1{G}{L}{PW}_1x{G}",
    ):
        result = R.redact(f"password={value}")
        assert result.text == "password=<SECRET_1>", value
        assert result.mapping == {"<SECRET_1>": value}


def test_secret_lookalikes_and_genuine_placeholders_together_are_left_alone():
    """E9(2): a run of escaped `‹SECRET_n›` and genuine SECRET placeholders is left alone, as before."""
    text = f"password={ESC_SECRET}<SECRET_3>{ESC_SECRET}"
    result = R.redact(text)
    assert result.text == text and result.mapping == {}


def test_a_genuine_placeholder_of_another_kind_beside_a_lookalike_is_masked_whole():
    """E9(2), changed shape (before: `password=‹SECRET_1›<UUID_3>‹SECRET_1›` was left unmasked as one own-output run; now masked whole): the
    older placeholders-only rule does not cover it (an escaped token is not a placeholder) and `<UUID_3>` is not a SECRET token."""
    value = f"{ESC_SECRET}<UUID_3>{ESC_SECRET}"
    result = R.redact(f"password={value}")
    assert result.text == "password=<SECRET_1>" and result.mapping == {"<SECRET_1>": value}


def test_a_lookalike_of_another_kind_in_a_secret_value_is_masked_whole():
    """E9(2), changed shape (before: left unmasked, a stated limit; now: masked): `password=‹SECRET_1›<UUID_3>‹IPV4_1›` held an escaped
    token of a kind that is not SECRET, so it is a real value spelled like a token and is masked whole."""
    value = f"{ESC_SECRET}<UUID_3>{ESC_IP}"
    result = R.redact(f"password={value}")
    assert result.text == "password=<SECRET_1>"
    assert result.mapping == {"<SECRET_1>": value}


def test_secret_lookalikes_separated_by_spaces_semicolons_or_commas_are_left_alone():
    text = f"Cookie: {ESC_SECRET}; {L}SECRET_2{G}, {ESC_SECRET}"
    result = R.redact(text)
    assert result.text == text and result.mapping == {}


def test_a_cookie_run_with_a_lookalike_of_another_kind_is_masked_whole():
    """E9(2), changed shape (before: left unmasked; now: masked): the escaped `‹IPV4_1›` in a SECRET run is not exempt."""
    value = f"{ESC_SECRET}; {ESC_IP}, {ESC_SECRET}"
    result = R.redact(f"Cookie: {value}")
    assert result.text == "Cookie: <SECRET_1>"
    assert result.mapping == {"<SECRET_1>": value}


def test_a_value_of_genuine_placeholders_alone_is_left_alone_as_before():
    result = R.redact("password=<SECRET_4>")
    assert result.text == "password=<SECRET_4>" and result.mapping == {}


def test_e9_redact_untrusted_twice_with_an_address_value_makes_one_junk_entry():
    """Pins an ACCEPTED trade-off (option (a)); the lead's option (b) would exempt the escaped token of another kind.

    A key followed by an address: the first pass writes `password=<EMAIL_1>` (EMAIL runs before the SECRET key=value pattern),
    the second pass escapes it to `‹EMAIL_1›`, a SECRET value that is masked: one entry `<SECRET_1>` = `‹EMAIL_1›`.
    """
    first_map: dict[str, str] = {}
    once = runmap.redact_untrusted("login failed password=a@b.co host", first_map)
    assert once == "login failed password=<EMAIL_1> host"
    assert first_map == {"<EMAIL_1>": "a@b.co"}
    rmap = runmap.RunMap()
    twice = runmap.redact_untrusted(once, rmap)
    assert twice == "login failed password=<SECRET_1> host"
    assert dict(rmap) == {"<SECRET_1>": f"{L}EMAIL_1{G}"}
    held = dict(rmap)
    third = runmap.redact_untrusted(twice, rmap)
    assert third == f"login failed password={ESC_SECRET} host" and dict(rmap) == held
