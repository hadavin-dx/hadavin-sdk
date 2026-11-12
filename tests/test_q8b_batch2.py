"""Q8b fix batch 2 (review round 2): the key-glue guard has no length bound, one key list, the card keeps its words, the
tail of a value with spaces is masked on every path, a link or a Bearer word cannot hide a credential key."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

from hadavin_sdk.approvals.cards import render_shadow
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.approvals.requests import summary
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from tests.q8b_helpers import key_spellings, shown_records, slack_notice
from tests.test_q8b_card_text import plan as _plan

redact = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # the module (the package also exports a function of that name)
PW = "pass" + "word"
WORDS = "correct horse battery staple"
V = "zq" + "hunter2" + "secretXYZ"  # made-up; built from parts


def _readable(out: str) -> list[str]:
    return [w for w in WORDS.split() if w in out]


def _all_keys() -> list[str]:
    return key_spellings()


# ---- Issue 1: the glue guard is not bounded by a length -----------------------------------------------------------------


def test_the_value_tail_rule_skips_exactly_the_secret_kinds():
    """The value rule leaves a value that is only placeholders of a secret kind alone (a second cleaning changes nothing).
    The kinds come from `SECRET_KINDS`, the one list: each of them is skipped, and a kind that is not a secret is not."""
    for kind in sorted(redact.SECRET_KINDS):
        text = f"{PW}=<{kind}_1> tail"
        assert redact.redact(text).text == text, f"a placeholder of kind {kind} was masked again"
    assert redact.redact(f"{PW}=<EMAIL_1> tail").text != f"{PW}=<EMAIL_1> tail"
    assert not hasattr(redact, "_MASKED_KINDS"), "a second hand copy of the secret kinds"


def test_a_key_glued_to_an_address_of_any_length_keeps_its_value_masked():
    bad = []
    for n in (1, 39, 40, 41, 42, 100, 255, 256, 300):
        for sep in ("=", ": ", '":"'):
            for domain in ("a" * n + ".com", "x." + "b" * n + ".com", "x." + "c" * n):
                text = f"bob@{domain}{PW}{sep}{V}"
                for out in (clean(text), runmap.redact_untrusted(text, runmap.RunMap())):
                    if "hunter2" in out or "secretXYZ" in out:
                        bad.append(out[-60:])
    assert not bad, f"a value glued to a key is readable: {len(bad)} cases, first {bad[:2]!r}"


def test_a_key_glued_to_a_long_identifier_keeps_its_value_masked():
    bad = [n for n in (0, 1, 40, 41, 42, 255, 1000) if "hunter2" in clean("a" * n + f"{PW}={V}")]
    assert not bad, f"a value behind a word of these lengths is readable: {bad}"


def test_a_key_glued_to_an_arn_at_every_distance_is_masked():
    bad = []
    for n in range(redact.KEY_PREFIX_MAX + 4):
        text = f"arn:aws:iam::123456789012:role/{'r' * n}{PW}={V}"
        if "hunter2" in clean(text):
            bad.append(n)
    assert not bad, f"a value glued to a credential key is readable at distances {bad}"


# ---- Issues 2, 4, 5: one key list, the card keeps its words, the tail is masked --------------------------------------------


def test_every_spelling_of_every_key_masks_a_value_with_spaces_on_every_path():
    bad = []
    for key in _all_keys():
        text = f"x {key}={WORDS}"
        walked = shown_records({"note": text})[0]["note"]
        for path, out in (("card", clean(text)), ("walk", walked), ("notice", slack_notice(text))):
            if _readable(out):
                bad.append((key, path))
    assert not bad, f"a word of the value is readable: {bad[:5]}"


def test_no_file_of_the_redaction_code_keeps_its_own_list_of_credential_keys():
    """A second key list is a collection literal (one entry per line or not) or a `a|b|c` string that names three or more
    credential words, anywhere in the package (an AST scan: not tied to two words on one line). Allowed, each for its reason:
    the one list, the words a tool prints after a key, the record walk's words and endings (compared with the one list by
    test_r7), and the HTTP header-name filter of the tool path (broader than the key list on purpose), and the start pieces of the key rules for the batch 12 prefilter (`KEY_GATE_WORDS`: not a key list, it only says where a rule is tried; a differential test and a start-word test pin it against the rules). Fails on the code before
    batch 3, where the quoted-value rules carried a third list. Scope: `src/` only (`tools/` and `demos/` are not scanned). The
    detection is `tests.q8b_helpers.second_key_lists`, the same function the self-test in test_q8b_batch4 runs on a sample."""
    import ast

    from tests.q8b_helpers import second_key_lists

    root = Path(__file__).resolve().parents[1] / "src/hadavin_sdk"
    allowed = {
        "KEY_ALTERNATIVES",
        "_NOT_A_VALUE",
        "CREDENTIAL_WORDS",
        "GLUED_ENDINGS",
        "_CREDENTIAL_HEADER",
        "KEY_GATE_WORDS",
    }
    bad = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for lineno, hits in second_key_lists(tree, allowed):
            bad.append(f"{path.relative_to(root.parent.parent)}:{lineno}: {hits}")
    assert not bad, f"a second list of credential keys: {bad}"


def test_a_card_keeps_flags_and_words_after_a_masked_value():
    out = clean(f"{PW}=correct horse battery staple user=bob")
    assert out == f"{PW}=<SECRET_1> user=bob", f"user=bob is not kept: {out!r}"
    assert (
        clean("run --password=x1y2z3w4 --force --target prod")
        == "run --password=<SECRET_1> --force --target prod"
    )
    assert (
        clean(f"{PW}=correct horse --force --target prod")
        == f"{PW}=<SECRET_1> --force --target prod"
    )


def plan(system, inputs, expected="service restarted"):
    p = _plan(system, inputs)
    return p.model_copy(update={"expected_outcome": expected})


def test_the_plan_line_survives_a_masked_value_at_the_end_of_the_text():
    text = summary(plan("crm", {}, "Expected: rotate token=abc12345 on the primary"), None)
    assert "abc12345" not in text and re.search(r" Plan [0-9a-f]{12}\.$", text), text
    assert text.startswith(
        "agent-ops asks to run restart_service v1 (reversible) on crm. Inputs: {}."
    ), text


def test_the_walk_masks_the_words_after_a_value_and_a_passphrase():
    for text in (
        f"{PW}={WORDS}",
        f"passphrase={WORDS}",
        f"my passphrase: {WORDS}",
        f"session={WORDS}",
    ):
        out = shown_records({"note": text})[0]["note"]
        assert not _readable(out), f"{text!r} -> {out!r}"
    out = shown_records({"note": f"{PW}={WORDS} --force --target prod"})[0]["note"]
    assert "--force --target prod" in out and not _readable(out), out


# ---- Issue 6: a link in front of a credential key -----------------------------------------------------------------------


LINKS = [
    "http://x.example/a",
    "https://x.example/a?b=c",
    "https://x.example",
    "www.x.example/p",
    "ftp://h.example/f",
]


def test_a_link_glued_to_a_credential_key_keeps_the_value_masked():
    bad = []
    for link in LINKS:
        for sep in (": ", "=", " = "):
            text = f"{link}{PW}{sep}{WORDS}"
            for path, out in (("card", clean(text)), ("notice", slack_notice(text))):
                if _readable(out):
                    bad.append(f"{path}: {out!r}")
    assert not bad, f"{len(bad)} cases leak, first {bad[:2]}"


def test_an_address_link_glued_to_a_credential_key_keeps_the_value_masked():
    out = clean(f"10.0.0.1/a{PW}: {WORDS}")
    assert not _readable(out), out
    assert out.startswith("[link removed]"), f"the link is not removed: {out!r}"


def test_a_link_alone_is_still_removed_whole():
    assert "path" not in clean("see http://x.example/path/with/more?q=1 now")


# ---- Issue 7: a credential key after a Bearer word ------------------------------------------------------------------------


FORMS = ["{k}={v}", "{k} = {v}", "{k}\t=\t{v}", "{k}: {v}", '"{k}":"{v}"', "{k}='{v}'", '{k}="{v}"']


def test_a_credential_key_after_a_bearer_word_is_masked_whole():
    bad = []
    for form in FORMS:
        _bearer_rows(form, bad)
    assert not bad, f"a value after Bearer is readable: {len(bad)} cases, first {bad[:3]}"


def _bearer_rows(form, bad):
    for key in (
        "password",
        "passphrase",
        "secret",
        "token",
        "api_key",
        "client_secret",
        "access_token",
        "session",
    ):
        tail = form.format(
            k=key, v=WORDS if "'" not in form and '"' not in form else "correct-horse-battery"
        )
        for text in (f"Bearer {tail}", f"Authorization: Bearer {tail}", f"authorization={tail}"):
            out = clean(text)
            if _readable(out) or "correct-horse" in out:
                bad.append((text, out))


def test_a_plain_bearer_token_is_masked_and_text_after_it_is_kept():
    out = clean("Authorization: Bearer abcdefghijklmnop1234 then more")
    assert "abcdefghijklmnop1234" not in out and out.endswith("then more"), out


# ---- Issue 10: the shadow card shows the label ---------------------------------------------------------------------------


def test_the_shadow_card_shows_the_target_label():
    from hadavin_sdk.models import GateDecision

    decision = GateDecision(run_id="r", plan_hash="h" * 64, outcome="needs_approval", rule_id="x")
    shown = render_shadow(
        plan("crm", {}), decision, [], target_labels={"crm": "Customer system"}
    ).text
    assert "on Customer system" in shown, f"the shadow card does not show the label: {shown!r}"
    assert "on crm" in render_shadow(plan("crm", {}), decision, []).text


# ---- the plain-value rule of the walk, called directly (the redactor masks such a value first on a card) ------------------


def test_a_value_with_a_control_character_is_never_written_unquoted():
    attempts = R._attempts("password", "hunter\x1b[0m2" + "secretXYZ", True)
    assert all(q for _, q in attempts), (
        f"a value with a control character was written unquoted: {attempts}"
    )


def test_a_flag_with_a_value_that_has_spaces_is_masked_whole():
    for text in (f"run --{PW}={WORDS}", f"run --token={WORDS} --force"):
        out = clean(text)
        assert not _readable(out), f"a word of a flag value is readable: {out!r}"
    assert clean(f"run --{PW}={WORDS} --force --target prod").endswith("--force --target prod")


# ---- Issue 3: the CHANGELOG entry that says it is the same text as LIMITS --------------------------------------------------


def test_the_changelog_entry_is_the_same_text_as_limits():
    changelog = (Path(__file__).resolve().parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
    start = changelog.index("- **Masked where repeated, with limits**")
    end = changelog.index("\n- **", start + 5)
    entry = changelog[start:end]
    body = [ln.strip().removeprefix("- ") for ln in entry.split("\n")[1:] if ln.strip()]
    body[-1] = body[-1].split(" (A sweep", 1)[0]  # the follow-up note is not part of LIMITS
    wanted = [ln.strip().removeprefix("- ") for ln in R.LIMITS.split("\n") if ln.strip()]
    assert body == wanted, f"the CHANGELOG entry differs from LIMITS: {set(body) ^ set(wanted)}"


def test_the_card_path_masks_glued_key_spellings_and_makes_no_new_fence():
    for key in ("dbpass", "mycredential", "usersession", "userauth", "dbaccess_key", "dbapi_key"):
        out = clean(f"{key}={WORDS}")
        assert not _readable(out), f"a glued spelling is readable on the card: {out!r}"
    for text in (f"{PW}={WORDS} ``` tail", f"x ``` {PW}: {WORDS}", "plain text"):
        assert clean(text).count("```") <= text.count("```"), (
            f"a new fence appeared: {clean(text)!r}"
        )
