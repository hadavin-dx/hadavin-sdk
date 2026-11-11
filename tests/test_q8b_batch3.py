"""Q8b batch 3 (round-3 review): tool phrases kept, one key list for every rule, the record-walk key rule measured on a key
corpus, the card text second view, a second pass that equals the first, and the stops of the unquoted value.

Made-up data only; every secret-looking value is built from parts.
"""

from __future__ import annotations

import importlib
import json
import pathlib
import re

import pytest
from tools.mutation_runner import run_mutants

from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from tests.q8b_helpers import key_spellings, slack_notice
from tests.q8b_key_corpus import (
    BENIGN,
    CARD_COST,
    CREDENTIAL,
    UNLISTED_PREFIX,
    WALK_COST,
)
from tests.test_q8b_card_text import first_pass_originals_readable

redact = importlib.import_module("hadavin_sdk.guard.redact")
ROOT = pathlib.Path(__file__).resolve().parents[1]
VALUE = "Zq7" + "mV4xk9"
PART_B = "Hh5" + "kQ8wLm2"
PART_C = "Tt3" + "pR6vNb1"


def walk(obj):
    mapping = runmap.RunMap()

    def mask(s):
        try:
            return runmap.redact_untrusted(s, mapping)
        except runmap.TooDeep:
            return R.MASKED

    return R._walk(obj, mask)


def log_text(text: str) -> str:
    return runmap.redact_untrusted(text, runmap.RunMap())


# ---- Issue 1: a tool's words after a credential key are not a value --------------------------------------------------------

TOOL_PHRASES = [
    "password: not set",
    "--token not set",
    "token: field required",
    "secret: has expired",
    "api_key: not provided",
    "password: is missing",
]


def test_i1_a_tool_phrase_after_a_key_is_kept_on_every_path():
    for text in TOOL_PHRASES:
        assert clean(text) == text, f"a tool phrase was masked on the card: {clean(text)!r}"
        assert log_text(text) == text, f"a tool phrase was masked in the log text: {text!r}"
        assert walk([{"message": text}]) == [{"message": text}], (
            f"a tool phrase was masked in a record: {text!r}"
        )
        assert text in slack_notice(text), f"a tool phrase was masked in a Slack notice: {text!r}"


def test_i1_an_unrelated_not_set_line_stays_readable():
    text = "password: not set\nthe region is not set\nuse the default region: not set"
    assert clean(text) == text, f"other 'not set' lines were swept: {clean(text)!r}"


UNKNOWN_WORD = [
    ("password=key lime pie", "lime"),
    ("password: no more secrets here", "secrets"),
    ("password=not set yet 7Kx9", "7Kx9"),
    ("token: field required " + VALUE, VALUE),
]


def test_i1_one_unknown_word_makes_the_phrase_a_value():
    for text, gone in UNKNOWN_WORD:
        assert gone not in clean(text), f"a passphrase word stayed readable: {clean(text)!r}"
        assert gone not in log_text(text), (
            f"a passphrase word stayed readable in the log text: {text!r}"
        )


# ---- Issue 2: one key list for every value rule ----------------------------------------------------------------------------


def test_i2_every_key_spelling_masks_a_quoted_value_with_a_separator():
    value = f"{VALUE};{PART_B} {PART_C}"
    for spelling in key_spellings():
        for quote in ('"', "'"):
            text = f"{spelling}={quote}{value}{quote}"
            for name, out in (("card", clean(text)), ("log", log_text(text))):
                assert PART_B not in out and PART_C not in out and VALUE not in out, (
                    f"a quoted value stayed readable on the {name} path for key {spelling!r}: {out!r}"
                )


def test_i2_the_named_keys_of_the_review_mask_the_part_after_a_separator():
    for spelling in [
        "access_key",
        "private_key",
        "account_key",
        "key_data",
        "connect.sid",
        "phpsessid",
        "sessid",
        "auth",
    ]:
        for value in (f"{VALUE};{PART_B} {PART_C}", f"{VALUE}&{PART_B}"):
            out = clean(f'{spelling}="{value}"')
            assert PART_B not in out and VALUE not in out, f"{spelling}: {out!r}"


def test_i2_there_is_one_key_list_and_every_rule_reads_it():
    src = pathlib.Path(redact.__file__).read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    assert code.count('"|".join(KEY_ALTERNATIVES)') == 1, (
        "KEY_WORDS must be the only place the list is joined"
    )
    assert code.count("signing[_") == 1, (
        "a second hand-kept key list holds a key spelling of the first"
    )
    assert code.count("KEY_WORDS") >= 6, "the key rules must read KEY_WORDS"


# ---- Issue 3: the record-walk key rule, measured --------------------------------------------------------------------------


def test_i3_corpus_is_not_empty_and_disjoint():
    assert len(BENIGN) >= 100 and len(CREDENTIAL) >= 100
    assert not set(BENIGN) & set(CREDENTIAL)


def test_i3_every_credential_key_is_masked_on_the_walk_card_and_log_paths():
    missed_walk = [k for k in CREDENTIAL if not R.sensitive(k)]
    missed_card = [k for k in CREDENTIAL if VALUE in clean(f"{k}={VALUE}")]
    missed_log = [k for k in CREDENTIAL if VALUE in log_text(f"{k}={VALUE}")]
    assert not missed_walk, f"credential keys left readable in a record: {missed_walk}"
    assert not missed_card, f"credential keys left readable on a card: {missed_card}"
    assert not missed_log, f"credential keys left readable in a log text: {missed_log}"


def test_i3_the_walk_masks_exactly_the_named_cost_among_benign_keys():
    masked = sorted(k for k in BENIGN if R.sensitive(k))
    assert masked == sorted(WALK_COST), f"the benign false-mask set changed: {masked}"


def test_i3_every_key_the_card_masks_as_text_is_masked_on_the_walk_too():
    differ = [k for k in CREDENTIAL if (VALUE not in clean(f"{k}={VALUE}")) and not R.sensitive(k)]
    assert not differ, f"the two paths disagree: {differ}"


def test_i3_the_card_masks_exactly_the_named_cost_among_benign_keys():
    masked = sorted(k for k in BENIGN if VALUE not in clean(f"{k}={VALUE}"))
    assert masked == sorted(CARD_COST), f"the benign over-mask set of the card changed: {masked}"


def test_i3_a_pass_auth_or_session_key_with_an_unlisted_word_in_front_is_the_named_limit():
    on_walk = [k for k in UNLISTED_PREFIX if R.sensitive(k)]
    on_card = [k for k in UNLISTED_PREFIX if VALUE not in clean(f"{k}={VALUE}")]
    assert on_walk == [], f"the limit shrank: update LIMITS and D-032: {on_walk}"
    assert on_card == UNLISTED_PREFIX, "the card path must still mask these as text"
    assert "unlisted" in R.LIMITS.lower(), (
        "LIMITS must name the unlisted word in front of a glued key"
    )


def test_i3_the_six_keys_of_the_review_are_masked_in_a_record():
    for key in ["dbpass", "mycredential", "usersession", "userauth", "dbaccess_key", "dbapi_key"]:
        out = json.dumps(walk({key: VALUE}))
        assert VALUE not in out, f"{key}: {out}"


# ---- Issue 4: the card text second view keeps what the first view masked -----------------------------------------------------

M22_TEXTS = [
    'token: password%<br/> secret="notepassword%' + "Zx9" + "tailpart77",
    VALUE + '"' + PART_B + '\nsecret="10.20.30.40' + VALUE + "<br/> " + VALUE,
]


def test_i4_the_tag_stripped_view_starts_from_the_first_views_masks():
    for text in M22_TEXTS:
        left = first_pass_originals_readable(text)
        assert not left, f"readable in the returned text: {left} in {clean(text)!r}"


def test_i4_a_decoded_value_that_holds_a_shown_placeholder_is_one_masked_value():
    for text in (";;token: ab%26<IPV4_1>", "password=ab<IPV4_1>%26"):
        for out in (clean(text), log_text(text)):
            assert "&" not in out and "%26" not in out, (
                f"a decoded character stayed readable: {out!r}"
            )
            assert len(re.findall(r"<SECRET_\d+>", out)) == 1, (
                f"the value was split in two: {out!r}"
            )


# ---- Issue 6: a second pass over an output equals the first -----------------------------------------------------------------


def _same_after_normal(a: str, b: str) -> bool:
    return a == b.replace("\\u2039", "<").replace("\\u203a", ">")


SECOND_PASS_TEXTS = [
    "Authorization: Bearer bob.smith@example.com tail",
    "Authorization: Bearer " + VALUE,
    "Authorization: Bearer " + VALUE + " " + PART_B,
    "password=" + VALUE + " and Bearer 10.20.30.40",
]


def test_i6_a_second_pass_changes_nothing_but_the_escape_of_shown_placeholders():
    for text in SECOND_PASS_TEXTS:
        first = walk([{"message": text}])
        second = walk(first)
        a, b = json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        assert _same_after_normal(a, b), f"the second pass changed the output: {a!r} then {b!r}"


def test_i6_an_escaped_placeholder_is_not_read_as_a_token():
    out = log_text("Authorization: Bearer bob.smith@example.com tail")
    again = log_text(out)
    assert again.replace("‹", "<").replace("›", ">") == out.replace("‹", "<").replace("›", ">")
    assert re.search(r"<SECRET_\d+>", again) is None or "EMAIL" not in out


# ---- Issue 7: where an unquoted value ends --------------------------------------------------------------------------------

TAIL_TABLE = [
    ("password=correct 12:30 horse", ("12:30", "horse")),
    ("password=correct -horse battery staple", ("horse", "battery", "staple")),
    ("password=correct horse battery staple", ("horse", "battery", "staple")),
]
STOPS = [
    ("--force --target prod", "--force --target prod"),
    ("password=" + VALUE + " -f", "<SECRET_1> -f"),
    ("password=" + VALUE + " --force now", "<SECRET_1> --force now"),
    ("password=" + VALUE + " next=/admin", "<SECRET_1> next=/admin"),
    ("--password " + VALUE + " word", "--password <SECRET_1> word"),
]


def test_i7_later_words_of_a_value_are_masked_with_it():
    for text, gone in TAIL_TABLE:
        out = clean(text)
        for word in gone:
            assert word not in out, f"{word!r} stayed readable: {out!r}"


def test_i7_a_flag_or_a_key_ends_the_value():
    for text, kept in STOPS:
        out = clean(text)
        assert kept in out, f"expected {kept!r} in {out!r}"
        assert VALUE not in out


def test_i7_a_shown_placeholder_value_followed_by_prose_is_one_placeholder():
    assert log_text("token=<A> on the primary") == "token=<SECRET_1>"


def test_i7_the_changelog_names_the_stops_and_both_examples():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for fragment in (
        "password=correct -horse battery staple",
        "password=correct 12:30 horse",
        "-uroot",
    ):
        assert fragment in text, f"the CHANGELOG lacks {fragment!r}"


# ---- Issue 8: pins -----------------------------------------------------------------------------------------------------------


def test_i8_a_link_label_before_a_key_keeps_the_next_parameter():
    out = clean("[link removed]token=" + VALUE + "&next=/admin/x")
    assert out == "[link removed]token=<SECRET_1>&next=/admin/x", out


def test_i8_the_secret_kinds_are_one_name_for_the_card_and_the_tail_rule():
    assert not hasattr(channel_mod, "_ASSIGNMENT_KINDS")
    assert not hasattr(redact, "_MASKED_KINDS")
    assert runmap.SECRET_KINDS == redact.SECRET_KINDS


# ---- Issue 5: the mutation copy holds every root file the Q8b tests open ---------------------------------------------------


def test_i5_the_mutation_copy_list_covers_every_root_file_the_q8b_tests_open():
    mut = importlib.import_module("tests.q8b_mutants")
    opened = set()
    for path in (ROOT / "tests").glob("test_q8b_*.py"):
        for m in re.finditer(
            r"(?:ROOT|parents\[1\])\s*/\s*\"([A-Za-z0-9_.\-]+\.[a-z]+)\"",
            path.read_text(encoding="utf-8"),
        ):
            opened.add(m.group(1))
    assert opened, "no root file found: the scan is broken"
    assert opened <= set(mut.EXTRA_FILES), (
        f"the mutation copy lacks: {sorted(opened - set(mut.EXTRA_FILES))}"
    )


def test_i5_the_runner_copies_an_extra_root_file_and_refuses_one_that_leaves_the_tree(tmp_path):
    """The unmutated copy must find CHANGELOG.md; a name that leaves the tree is refused."""
    root = tmp_path / "pkg"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    (root / "tests" / "test_a.py").write_text(
        "from pathlib import Path\n\n\ndef test_a():\n"
        "    assert (Path(__file__).resolve().parents[1] / 'CHANGELOG.md').read_text() == '# Changelog\\n'\n",
        encoding="utf-8",
    )
    with pytest.raises(
        RuntimeError, match="does not pass"
    ):  # not copied unless named: the case this test is about
        run_mutants(root, [], ["tests/test_a.py"], extra_dirs=(), timeout=120)
    assert (
        run_mutants(
            root, [], ["tests/test_a.py"], extra_dirs=(), extra_files=("CHANGELOG.md",), timeout=120
        )
        == []
    )
    for bad in ("../x.md", "/abs/x.md", "-x"):
        with pytest.raises(ValueError):
            run_mutants(
                root, [], ["tests/test_a.py"], extra_dirs=(), extra_files=(bad,), timeout=120
            )
