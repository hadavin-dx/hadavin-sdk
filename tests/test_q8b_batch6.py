"""Q8b batch 6 (round-6 review): a session cookie value keeps what follows a `&`, the card's flag names and the record walk
read ONE list of ordinary words and word endings, the wording of the shipped text, and no test writes a fixed `/tmp` path.

Made-up data only; every secret-looking value is built from parts. Each assertion carries the message the mutant list
quotes (``tests/q8b_mutants.py``).
"""

from __future__ import annotations

import ast
import importlib
import pathlib

from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.k1b import redaction as R
from tests import q8b_key_corpus as corpus
from tests import q8b_older_rule as older
from tests.q8b_helpers import P1, P2, P3, key_spellings, readable_pieces, text_paths

redact = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # the module (the package exports a function of that name)
ROOT = pathlib.Path(__file__).resolve().parents[1]
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

SESSION_COOKIE_KEYS = (
    "session_cookie",
    "session-cookie",
    "x_session_cookie",
    "Session_Cookie",
    "session_cookies",
    "X-Session-Cookie",
    "HTTP_SESSION_COOKIE",
    "sessioncookie",
)
# Characters the older cookie rule stopped at (`[`, `{`) or that need no care (a backslash), put inside the first piece.
INSIDE = ("", "[", "{", "\\")


# ---- F1: the part of a session cookie after a `&` ------------------------------------------------------------------------


def test_k1_a_session_cookie_value_keeps_the_part_after_an_ampersand_masked():
    """Round 6 (Blocker): the generic value stops at `&` (a query separator); the older cookie rule took `&` into the value."""
    left = []
    for key in SESSION_COOKIE_KEYS:
        for ch in INSIDE:
            for text in (
                f"x {key}={P1}{ch}&{P2} y",
                f"{key}={P1}{ch}&{P2}={P3}",
                f"{key}={P1}{ch}&{P2}",
                f"{key}={P1}&{P2}{ch}&{P3}",
            ):
                for path, out in text_paths(text).items():
                    if readable_pieces(out):
                        left.append((path, text, out))
    assert not left, f"the part after the ampersand is readable: {left[:3]} ({len(left)} cases)"


def test_k1_every_cookie_key_the_older_cookie_rule_masked_is_masked_with_an_ampersand_a_bracket_or_a_backslash():
    """Class check: every key that ends in a cookie word, with `&`, `[`, `{` and a backslash in its value (the older cookie rule masked
    the plain and backslash values whole and stopped at `[` and `{`: this one masks them whole)."""
    keys = [
        f"{front}{sep}{word}"
        for front in ("", "session", "auth", "set", "http", "x-auth", "my_session", "token", "user")
        for sep in ("", "_", "-")
        for word in ("cookie", "cookies", "Cookie", "COOKIE")
        if front or not sep
    ]
    left = []
    for key in keys:
        for ch in INSIDE:
            for text in (f"x {key}={P1}{ch}&{P2}={P3} y", f"{key}={P1}{ch}{P2}&{P3}"):
                older_parts = older.masked_parts(text)
                for path, out in text_paths(text).items():
                    for part in older_parts:
                        left += [(path, text, p) for p in readable_pieces(out, part)]
                    if older.COOKIE_ASSIGN.search(text) and (shown := readable_pieces(out)):
                        left.append((path, text, shown))
    assert not left, (
        f"the older cookie rule masks it and this one does not: {left[:3]} ({len(left)})"
    )


def test_k1_a_cookie_key_value_with_a_bracket_after_its_first_character_is_masked_whole():
    for key in ("Cookie", "cookie", "Set-Cookie", "HTTP_COOKIE"):
        out = clean(f"x {key}={P1}[{P2}{{{P3} y")
        assert not readable_pieces(out), f"a bracket ended the cookie value: {out!r}"


def test_k1_the_session_cookie_rule_costs_what_the_changelog_says():
    """D6-2: plain words after a session cookie on the same line are masked with it (the older rule kept them)."""
    out = clean(f"session_cookie={P1}; csrf={P2}; user={P3} then prose")
    assert out == "session_cookie=<SECRET_1>", f"the trailing prose pin changed: {out!r}"
    out = clean(f"session_cookie={P1}&{P2}={P3} then prose")
    assert out == "session_cookie=<SECRET_1>", f"the trailing prose pin changed: {out!r}"
    for fragment in (
        "session_cookie=a; csrf=b; user=c then prose",
        "session_cookie=a&b=c",
        "`Cookie=a[b&c{d`",
        "the older rule kept ` then prose`",
    ):
        assert fragment in CHANGELOG, f"the CHANGELOG lacks {fragment!r}"
    assert "`session_cookie=` keeps its whole value masked" not in CHANGELOG


def test_k1_a_placeholder_followed_by_a_comma_or_a_semicolon_is_masked_whole():
    """F3: `password=<SECRET_1>, retry later` is masked whole (a new over-masking, written in the CHANGELOG)."""
    for tail in (", retry later", ",retry later", ";retry later"):
        out = clean(f"password=<SECRET_1>{tail}")
        assert "retry" not in out and "later" not in out, (
            f"a word after a placeholder is readable: {out!r}"
        )
    assert "`password=<SECRET_1>, retry later`" in CHANGELOG, (
        "the CHANGELOG lacks the placeholder example"
    )


def test_k1_the_comment_on_the_value_character_says_what_the_comma_does():
    """F2: the comment read `,` and `;` as one rule; the code ends a value at a `,` only in front of a new key."""
    text = (ROOT / "src/hadavin_sdk/guard/redact.py").read_text(encoding="utf-8")
    assert "a `,` only in front of a new `key=` or `key:`" in text
    assert "a `,` or `;` that is followed by a space" not in text


# ---- D6-1: one list of ordinary words and word endings for the record walk and the card's flags ----------------------------


def test_d6_the_record_walk_reads_the_one_list_of_ordinary_words_and_endings():
    assert R.ORDINARY_WORDS is redact.ORDINARY_WORDS, (
        "the record walk keeps its own list of ordinary words"
    )
    assert R.BARE_ENDINGS is redact.BARE_ENDINGS, "the record walk keeps its own list of endings"
    tree = ast.parse((ROOT / "src/hadavin_sdk/k1b/redaction.py").read_text(encoding="utf-8"))
    own = [
        n.targets[0].id
        for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id in ("ORDINARY_WORDS", "BARE_ENDINGS")
    ]
    assert not own, f"the record walk assigns its own {own}"


def test_d6_a_flag_with_a_word_glued_in_front_masks_its_value_like_the_record_key():
    for key in (
        "dbpass",
        "confirmpass",
        "rootauth",
        "oauth",
        "dbpassword",
        "mytoken",
        "x-dbpass",
        "db_rootauth",
        "xbypass",
        "DBPASS",
        "defaultpass",
        "jenkinssession",
        "session",
        "auth",
        "bearer",
        "credentials",
    ):
        out = clean(f"run --{key} {P1}{P2} now")
        assert out == f"run --{key} <SECRET_1> now", f"a glued flag value is readable: {out!r}"
        assert R.sensitive(key), f"the record walk does not mask {key}: the test list is wrong"


def test_d6_a_flag_with_an_ordinary_word_stays_readable():
    for key in (
        "bypass",
        "compass",
        "obsession",
        "author",
        "encompass",
        "x-bypass",
        "new_bypass",
        "supersession",
        "authority",
    ):
        text = f"run --{key} {P1}{P2} now"
        assert clean(text) == text, f"an ordinary word was masked as a flag: {clean(text)!r}"


# Keys the record walk masks and the card does NOT as a FLAG or as `key=value`, each for a stated reason (the reverse drift
# test below reads them). They are skipped by the LAST WORD of the key only, never one by one:
#   - `SETTING_WORDS` (`enabled`, `policy`, `count`, `ttl`, `days`, ...): the key names a setting ABOUT a credential
#     (`password_policy_enabled`, `secrets_count`, `passkeyCount`);
#   - `PROPERTY_LAST_WORDS`: the key names a property OF a credential, not its value (`auth_method`, `authMode`,
#     `oauthProvider`, `oauth_scopes`, `pass_rate`, `pass_fail`, `session_affinity`, `session_duration`, `tokenBucket`,
#     `token_type`, `tokenUsage`). The record rule masks them (a named cost in `LIMITS`). The FLAG rule needs the credential
#     word at the END of the name (`--token-type` stays readable). The card `key=value` rule does not need that: it accepts up
#     to 20 key characters after the credential word, so `token_type=x` is masked there; only the keys whose credential word
#     is a bare word (`auth_method=`, `pass_rate=`, `session_duration=`) stay readable in that form.
# `--tokens` (flag only) is a count (`--tokens 4096`). Round 7: `auth0` and `oauth2` are NOT exceptions any more: a digit
# glued to a credential word is masked on every path, as the record walk masks it.
PROPERTY_LAST_WORDS = frozenset(
    [
        "method",
        "mode",
        "provider",
        "scopes",
        "rate",
        "fail",
        "affinity",
        "duration",
        "bucket",
        "type",
        "usage",
    ]
)
# Round 8 Issue 2: `--cookies` is no credential flag (the plural of a switch family: `--no-cookies`, `--load-cookies`); the cookie
# flag is the exact name (`--cookie`, `--set-cookie`, `--session_cookie`). The record key `cookies` stays masked.
FLAG_ONLY_EXCEPTIONS = {"tokens", "cookies"}
KEY_EQ_EXCEPTIONS: set[str] = set()
# The least number of keys the drift test must COMPARE (after the skip above): 215 measured at batch 7 (236 walked, 21 skipped).
COMPARED_KEYS_FLOOR = 210


def _skipped_by_last_word(key: str) -> bool:
    """The key is a setting or a property of a credential: its LAST word (digits dropped) is in one of the two short lists."""
    return R._key_words(key)[-1] in (R.SETTING_WORDS | PROPERTY_LAST_WORDS)


def test_d6_every_key_the_record_walk_masks_is_masked_as_a_flag_and_as_key_value_on_the_card():
    keys = (
        set(corpus.CREDENTIAL)
        | set(corpus.BENIGN)
        | set(corpus.UNLISTED_PREFIX)
        | set(key_spellings())
        | {"newpass", "oldpass", "dbpass", "confirmpass", "rootauth", "oauth", "bypass", "author"}
    )
    walked = sorted(k for k in keys if R.sensitive(k))
    assert len(walked) > 150, f"the key sample shrank: {len(walked)}"
    compared = [k for k in walked if not _skipped_by_last_word(k)]
    assert len(compared) >= COMPARED_KEYS_FLOOR, (
        f"the drift test compares {len(compared)} keys, fewer than the floor {COMPARED_KEYS_FLOOR}: the filter skips too much"
    )
    flag_left, eq_left = [], []
    for key in compared:
        if key not in FLAG_ONLY_EXCEPTIONS and readable_pieces(clean(f"run --{key} {P1}{P2} now")):
            flag_left.append(key)
        if key not in KEY_EQ_EXCEPTIONS and readable_pieces(clean(f"run {key}={P1}{P2} now")):
            eq_left.append(key)
    assert not flag_left, (
        f"the record walk masks these keys and the card does not, as flags: {flag_left}"
    )
    assert not eq_left, (
        f"the record walk masks these keys and the card does not, as key=value: {eq_left}"
    )


def test_d6_the_skip_by_last_word_holds_back_no_credential_key_that_the_card_leaves_readable_without_a_reason():
    """Without the skip, the keys left readable on the card are exactly the settings and properties of a credential (the
    two short lists), plus the count `--tokens`: nothing else is hidden from the drift test by the filter."""
    walked = sorted(
        k
        for k in (
            set(corpus.CREDENTIAL)
            | set(corpus.BENIGN)
            | set(corpus.UNLISTED_PREFIX)
            | set(key_spellings())
        )
        if R.sensitive(k)
    )
    for key in walked:
        for text in (f"run --{key} {P1}{P2} now", f"run {key}={P1}{P2} now"):
            if readable_pieces(clean(text)) and not (
                key in FLAG_ONLY_EXCEPTIONS and text.startswith("run --")
            ):
                assert _skipped_by_last_word(key), f"left readable, and no listed reason: {text!r}"


def test_d6_the_documented_exceptions_are_real_and_stay_readable_where_pinned():
    for key in ("--token-type", "--auth-method", "--pass-rate", "--session-duration"):
        text = f"run {key} {P1}{P2} now"
        assert clean(text) == text, (
            f"a property of a credential was masked as a flag: {clean(text)!r}"
        )
    assert clean(f"run --tokens {P1}{P2} now") == f"run --tokens {P1}{P2} now"
    for fragment in (
        "`--token-type`",
        "`--auth-method`",
        "`--tokens` is a count",
    ):
        assert fragment in CHANGELOG, f"the CHANGELOG lacks {fragment!r}"


def test_d6_a_flag_takes_the_one_word_after_a_space_and_the_whole_value_after_an_equals_sign():
    """The second word of a two-word value after a space is shown for EVERY credential flag, `--password` too (the older code
    read it the same way: it may be a file name or another argument). Closing it would hide the command's own arguments."""
    for flag in (
        "newpass",
        "oldpass",
        "postgresauth",
        "authorization",
        "password",
        "dbpass",
        "oauth",
    ):
        out = clean(f"run --{flag} {P1} {P2} now")
        assert out == f"run --{flag} <SECRET_1> {P2} now", (
            f"the one-word flag value changed: {out!r}"
        )
        out = clean(f"run --{flag}={P1} {P2} now")
        assert not readable_pieces(out), f"a word of an `=` flag value is readable: {out!r}"
    assert "`--newpass a b` the word `a` is masked and `b` is shown" in R.LIMITS
    assert "`--newpass a b` the word `a` is masked and `b` is shown" in CHANGELOG


# ---- item 4: no test writes a fixed path in the shared temporary folder ----------------------------------------------------

SHARED_TMP = "/" + "tmp/"  # built from parts: the scan must not trip over its own constant
# A text that is only the ARGUMENT of a tool under test and is never opened, written or created by any test.
FIXED_TMP_ALLOWED = {("tests/test_k5_round11.py", "%72m -rf /tmp/x")}


def test_no_test_names_a_fixed_path_in_the_shared_temporary_folder():
    """Bug class: a fixed `/tmp/...` path collides between concurrent runs (a file left by another run, owned by another user:
    "Permission denied", Q8b round 6). Every string constant of every test file and demo is scanned (an AST scan)."""
    bad = []
    for base in ("tests", "demos", "tools"):
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel == "tests/test_q8b_batch6.py":
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and SHARED_TMP in node.value
                    and (rel, node.value) not in FIXED_TMP_ALLOWED
                ):
                    bad.append(f"{rel}:{node.lineno}: {node.value[:60]!r}")
    assert not bad, f"a fixed shared-temporary path: {bad}"


def test_the_copy_attack_of_the_askdata_corpus_writes_a_per_run_file():
    from tests.demo_askdata import corpus as askdata

    attack = next(a for a in askdata.ATTACKS if a.name == "copy-to-file")
    assert str(askdata.COPY_TARGET) in attack.sql
    assert askdata.COPY_TARGET.name != "askdata_p2_copy.csv", (
        "the copy target has the fixed name again"
    )
    assert len(askdata.COPY_TARGET.stem) > len("askdata_p2_copy_") + 16, (
        "the copy target has no per-run part"
    )
