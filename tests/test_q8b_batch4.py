"""Q8b batch 4 (round-4 review): the key list is a superset of the older rule's keys on every path, a key with a word in front
of `pass`, `auth` or `session` is masked in a record, a `;` inside an unquoted value, flag names read the one list, the
card's second view keeps every kind of secret, and the wording of the shipped text.

Made-up data only; every secret-looking value is built from parts.
"""

from __future__ import annotations

import ast
import importlib
import json
import pathlib
import string

from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from tests import q8b_older_rule as older
from tests.q8b_helpers import (
    P1,
    P2,
    P3,
    VALUE_STYLES,
    key_spellings,
    path_outputs,
    readable_pieces,
    second_key_lists,
    text_paths,
)
from tests.q8b_key_corpus import BENIGN, CREDENTIAL

redact = importlib.import_module("hadavin_sdk.guard.redact")
ROOT = pathlib.Path(__file__).resolve().parents[1]

# The keys of the round-4 findings (D1): masked by the older rule's bare `pass` and `session` prefixes, and the `_value` forms
# of the four bare words, which neither the older rule nor the first Q8b code masked on a card.
D1_KEYS = [
    "passcode",
    "passkey",
    "pass_code",
    "session_key",
    "sessionkey",
    "pass_value",
    "PASS_value",
    "Pass_value",
    "session_value",
    "SESSION_value",
    "Session_value",
    "auth_value",
    "AUTH_value",
    "Auth_value",
    "bearer_value",
    "BEARER_value",
    "Bearer_value",
    "key-data",
    "cert-data",
    "certificate-data",
    "client-key-data",
    "My-Key-Data",
    "session_cookie",
]
# D2: a credential written as one word with a word in front that no list could hold.
D2_KEYS = [
    "newpass",
    "oldpass",
    "confirmpass",
    "defaultpass",
    "postgresauth",
    "jenkinssession",
    "NewPass",
    "newAuth",
]
# Ordinary words the record rule must keep readable (they end in `pass`, `auth` or `session`).
ORDINARY = [
    "bypass",
    "compass",
    "encompass",
    "overpass",
    "underpass",
    "surpass",
    "trespass",
    "impass",
    "obsession",
    "possession",
    "supersession",
]
PATHS = ("card", "tool", "log", "walk")


# ---- D1: the older rule's keys and the new spellings, on every path and in every style -----------------------------------------


def test_j1_the_d1_keys_are_masked_in_every_style_on_every_path():
    left = []
    for key in D1_KEYS:
        for style in VALUE_STYLES:
            outputs = path_outputs(key, style)
            for path in PATHS:
                if readable_pieces(outputs[path]):
                    left.append(
                        f"{key} {style}/{path}: {readable_pieces(outputs[path])} in {outputs[path]!r}"
                    )
    assert not left, f"a value stayed readable: {left[:3]} ({len(left)} cases)"


def test_j1_every_credential_of_the_corpus_is_masked_in_every_style_on_every_path():
    left = []
    for key in CREDENTIAL:
        for style in VALUE_STYLES:
            outputs = path_outputs(key, style)
            left += [(key, style, p) for p in PATHS if readable_pieces(outputs[p])]
    assert not left, f"credential keys left a value readable: {left[:5]} ({len(left)} cases)"


class _Steps:
    """A fixed, repeatable series of choices (a linear congruential generator: no `random` module, the series never changes)."""

    def __init__(self, seed: int):
        self.state = seed

    def below(self, n: int) -> int:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) % 2**64
        return (self.state >> 33) % n

    def choice(self, items):
        return items[self.below(len(items))]


def _generated_keys(rng: _Steps, n: int) -> list[str]:
    words = [
        "pass", "password", "passwd", "pwd", "secret", "token", "api_key", "apikey", "credential", "session", "auth",
        "access_key", "account_key", "private_key", "client_secret", "sessionid", "key_data", "cert_data",
    ]  # fmt: skip
    fronts = ["", "db_", "x", "My-", "user", "app.", "zz_", "ORDERS_", "a" * 30]
    backs = [
        "",
        "_value",
        "_x",
        "id",
        "2",
        "_cookie",
        "key",
        "code",
        "_data",
        "word",
        "-name",
        ".v",
        "S",
        "_" + "b" * 19,
    ]
    return sorted(
        {rng.choice(fronts) + rng.choice(words) + rng.choice(backs) for _ in range(n)}
        | {w + b for w in words for b in backs}
    )


def _older_shapes(key: str) -> tuple[str, ...]:
    """Texts a key can be written in, with values that hold a space, a `;` and a `,` (the older rules read each differently)."""
    return (
        f'{key}="{P1};{P2} {P3}"',
        f"{key}='{P1};{P2}, {P3}'",
        f"{key}={P1}{P2}",
        f"{key}={P1};{P2}",
        f"{key}={P1},{P2}",
        f"{key}={P1}; csrf={P2}; user={P3}",
        f"{key}: {P1}{P2}",
        f"--{key} {P1}{P2}",
    )


def _older_rule_left_readable(keys: list[str]) -> list[tuple]:
    """Every (path, text, readable pieces, output) where a value the older rules capture is still readable: the whole
    captured part, or any one of its plain pieces (a quoted value masked only up to its first word leaves two pieces)."""
    left = []
    for key in keys:
        for text in _older_shapes(key):
            parts = [p for p in older.masked_parts(text) if not p.startswith("<")]
            if not parts:
                continue
            for path, out in text_paths(text).items():
                for part in parts:
                    pieces = readable_pieces(out, part)
                    if part in out or pieces:
                        left.append((path, text, pieces or [part], out))
    return left


def _record_keys_left_readable(keys: list[str]) -> list[tuple]:
    left = []
    for key in keys:
        if not older.record_key_masked(key):
            continue
        for style in VALUE_STYLES:
            out = path_outputs(key, style)["walk"]
            if readable_pieces(out):
                left.append(("walk", key, style, out))
    return left


def test_j1_every_key_the_older_rule_masked_is_still_masked():
    """The older rules (copied into `tests/q8b_older_rule.py`: the two quoted rules, the unquoted rule, the cookie rule, the
    flag rule and the `"auth"` JSON rule) are the ORACLE: on a generated set of keys of every form the older rule read (a
    word, a prefix, a suffix of up to 20 key characters) and values with a space, `;` and `,`, no part of any value they
    mask may be readable (the whole part, or any plain piece of it) on a card, in a tool result, in an untrusted text of a
    run or in a log line; and a key the older record rule masked is masked in a record. Fails when the key list is not a
    superset of the older one, and when a value is masked only in part."""
    keys = _generated_keys(_Steps(8841), 600)
    assert len(keys) > 300
    left = _older_rule_left_readable(keys) + _record_keys_left_readable(keys)
    assert not left, (
        f"the older rule masks it and this one does not: {left[:3]} ({len(left)} cases)"
    )


def test_j1_the_older_rule_check_fails_when_only_the_first_word_of_a_value_is_masked(monkeypatch):
    """The check above must see a half-masked value: with a card that masks only the first word of a quoted value (two
    pieces stay readable), it reports the key."""

    def first_piece_only(text: str) -> str:
        return text.replace(
            P1, "<SECRET_1>"
        )  # the first piece is masked, the others are written as they were

    real = text_paths
    monkeypatch.setitem(
        globals(),
        "text_paths",
        lambda t: {path: first_piece_only(t) for path in real(t)},
    )
    assert _older_rule_left_readable(["db_password"]), "a half-masked value was not reported"


def test_j1_a_session_cookie_keeps_its_whole_jar_masked():
    """Round 5 (Blocker): the cookie assignment rule took `;`-joined `name=value` pairs after `cookie=`; the generic key rule
    that now owns `session_cookie=` stopped at `; `, so `session_cookie=a; csrf=b; user=c` showed `csrf=b; user=c`."""
    for key in (
        "session_cookie",
        "session-cookie",
        "Session_Cookie",
        "sessioncookie",
        "session_cookies",
    ):
        for sep in ("; ", ";", ";\t"):
            text = f"x {key}={P1}{sep}csrf={P2}{sep}user={P3} y"
            for path, out in text_paths(text).items():
                assert not readable_pieces(out), (
                    f"{path}: a pair of the cookie jar is readable: {out!r}"
                )
    # a `,` does not join pairs (the older cookie rule stopped there too); the first value is masked
    out = clean(f"x session_cookie={P1},csrf={P2} y")
    assert P1 not in out, out
    out = clean(f"x session_cookie={P1}, csrf={P2} y")
    assert P1 not in out, out


def test_j1_every_cookie_key_the_older_cookie_rule_masked_is_still_masked_with_its_jar():
    """Class check: every key that ends in a cookie word, written as the older cookie rule read it."""
    keys = [
        f"{front}{sep}{word}"
        for front in ("", "session", "auth", "set", "http", "x-auth", "my_session", "token", "user")
        for sep in ("", "_", "-")
        for word in ("cookie", "cookies")
        if front or not sep
    ]
    left = []
    for key in keys:
        for sep in ("; ", ";"):
            text = f"x {key}={P1}{sep}csrf={P2}{sep}user={P3} y"
            parts = older.masked_parts(text)
            for path, out in text_paths(text).items():
                for part in parts:
                    left += [(path, text, p) for p in readable_pieces(out, part)]
    assert not left, (
        f"the older cookie rule masks it and this one does not: {left[:3]} ({len(left)})"
    )


def test_j1_a_key_the_older_rule_masked_only_by_a_bare_prefix_is_still_masked():
    for key in ("session_data", "sessionToken2", "pass_phrase2", "passthru", "session_expires_at"):
        for q in ('"', "'"):
            out = clean(f"{key}={q}{P1} {P2}{q}")
            assert P1 not in out and P2 not in out, (
                f"a bare prefix key stayed readable: {key}: {out!r}"
            )


def test_j1_a_cookie_key_with_a_session_word_in_front_masks_a_value_with_spaces():
    """Bug class: an earlier, narrower rule (the cookie assignment) takes `cookie=` and leaves a placeholder, so the generic
    rule never saw the rest of the value (`session_cookie=correct horse battery staple`)."""
    for key in ("session_cookie", "session-cookie", "Session_Cookie"):
        out = clean(f"x {key}={P1} {P2} {P3} y")
        assert not readable_pieces(out), f"a word of the cookie value is readable: {out!r}"


def test_j1_the_quoted_rules_read_one_shared_name():
    """The quoted-value rules read `QUOTED_KEY_WORDS`, which starts with the one key list (behaviour: M54, M55, M67)."""
    assert redact.QUOTED_KEY_WORDS.startswith(redact.KEY_WORDS)


def test_j1_a_quoted_value_after_authorization_is_masked_whole():
    """`authorization` is a bare prefix of the quoted rules (not in main's quoted rules): a quoted value with spaces after it was
    half readable. Also the over-masking named in the CHANGELOG: `authorization_endpoint` with a quoted value."""
    for key in ("authorization", "Authorization", "authorization_endpoint"):
        for q in ('"', "'"):
            out = clean(f"x {key}={q}{P1} {P2} {P3}{q} y")
            assert not readable_pieces(out), (
                f"{key}: a word of the quoted value is readable: {out!r}"
            )


def test_j1_a_credential_key_ending_in_a_link_scheme_word_keeps_its_value_masked_after_a_colon():
    """Bug class: a link remover that reads a scheme word in the middle of a key (`key-data:` is not `data:`)."""
    for key in ("key-data", "cert-data", "certificate-data", "client-key-data", "my-key-data"):
        out = clean(f"x {key}: {P1}{P2}")
        assert P1 not in out and P2 not in out, (
            f"a key ending in a link scheme word: {key}: {out!r}"
        )
    assert clean("see data:text/html,hello now") == "see [link removed] now"
    assert clean("see mailto:a@b.co now") == "see [link removed] now"
    # a scheme word inside a word is no link: only the start of a word counts (`-https:` and `.mailto:` stay as written)
    assert clean("x .mailto:a@b.co y") == "x .mailto:<EMAIL_1> y"


# ---- D2: a key with a word in front of pass, auth or session, in a record ------------------------------------------------------


def test_j2_a_key_with_any_word_in_front_is_masked_in_a_record_and_as_text():
    shown = [k for k in D2_KEYS if not R.sensitive(k)]
    assert not shown, f"{shown} is shown as written in a record"
    for key in D2_KEYS:
        for style in VALUE_STYLES:
            outputs = path_outputs(key, style)
            for path in PATHS:
                assert not readable_pieces(outputs[path]), (
                    f"{key} {style}/{path}: {outputs[path]!r}"
                )


def test_j2_oauth_is_a_credential_key_in_a_record_as_it_is_in_text():
    """Round 5: `oauth` may hold a token. The card masks `oauth=` as text; the record walk now masks the key too (it was on the
    ordinary-word list, so the two paths disagreed). Its cost is named in LIMITS (`oauth_scopes`, `oauthProvider` are masked)."""
    assert "oauth" not in R.ORDINARY_WORDS, "oauth is on the ordinary-word list"
    assert R.sensitive("oauth") and R.sensitive("oauth_scopes") and R.sensitive("oauthProvider")
    for key in ("oauth", "OAuth", "oauth_token_url"):
        for style in VALUE_STYLES:
            outputs = path_outputs(key, style)
            for path in PATHS:
                assert not readable_pieces(outputs[path]), (
                    f"{key} {style}/{path}: {outputs[path]!r}"
                )
    assert "`oauth`, `oauth_scopes` and `oauthProvider` are masked" in R.LIMITS


def test_j2_ordinary_words_stay_readable_in_a_record():
    shown = [k for k in ORDINARY if R.sensitive(k)]
    assert not shown, f"an ordinary word is taken for a credential key: {shown}"
    for k in ORDINARY:
        for style in ("dq", "plain"):
            raw = VALUE_STYLES[style][1]
            out = json.dumps(path_outputs(k, style)["walk"])
            assert raw.split(";")[0] in out or P1 in out, f"{k}: the value was hidden: {out}"


def test_j2_property_a_word_ending_in_pass_auth_or_session_is_a_credential_unless_ordinary():
    rng = _Steps(4417)
    letters = string.ascii_lowercase
    for _ in range(400):
        front = "".join(rng.choice(letters) for _ in range(1 + rng.below(12)))
        for ending in R.BARE_ENDINGS:
            word = front + ending
            assert R.sensitive(word) == (word not in R.ORDINARY_WORDS), word
            assert R.sensitive(word.upper()) == (word not in R.ORDINARY_WORDS), word.upper()


def test_j2_the_ordinary_words_are_a_closed_list_with_an_over_mask_cost_named_in_limits():
    assert set(ORDINARY) <= R.ORDINARY_WORDS
    assert all(w.endswith(R.BARE_ENDINGS) for w in R.ORDINARY_WORDS), "a word that needs no entry"
    assert "ordinary" in R.LIMITS and "not on the list" in R.LIMITS
    assert not hasattr(R, "GLUED_PREFIXES") and not hasattr(R, "PREFIXED_ENDINGS"), (
        "the allow-list is back"
    )


def test_j2_the_corpus_benign_keys_the_walk_masks_are_exactly_the_named_cost():
    from tests.q8b_key_corpus import WALK_COST

    assert sorted(k for k in BENIGN if R.sensitive(k)) == sorted(WALK_COST)


# ---- the `;` inside an unquoted value ---------------------------------------------------------------------------------------

SEMI_MASKED = [
    f"password={P1};{P2}",
    f"token={P1};{P2}{P3}",
    f"secret={P1};{P2};{P3}",
    f"api_key={P1};{P2} {P3}",
    f"x passcode={P1};{P2} y=1",
    f"password={P1};12:30{P2}",
    f"password={P1},12:30{P2}",
    f"password={P1};{P2},12:30{P3}",
]
SEMI_STOPS = [
    ("Password=" + P1 + ";Server=db1", "Password=<SECRET_1>;Server=db1"),
    ("token=" + P1 + "; path=/", "token=<SECRET_1>; path=/"),
    ("token=" + P1 + ";", "token=<SECRET_1>;"),
    ("token=" + P1 + ";;x", "token=<SECRET_1>;;x"),
    ("Password=" + P1 + ";Encrypt=true;Timeout=30", "Password=<SECRET_1>;Encrypt=true;Timeout=30"),
]


def test_j3_a_semicolon_in_front_of_a_word_belongs_to_an_unquoted_value():
    for text in SEMI_MASKED:
        for out in (clean(text), runmap.redact_untrusted(text, runmap.RunMap())):
            assert P2 not in out and P1 not in out, f"the part after the `;` is readable: {out!r}"


def test_j3_a_semicolon_in_front_of_a_key_a_space_or_the_end_stops_the_value():
    for text, kept in SEMI_STOPS:
        assert clean(text) == kept, f"expected {kept!r}, got {clean(text)!r}"


def test_j3_the_stop_is_the_same_on_every_path():
    for text, kept in SEMI_STOPS:
        assert runmap.redact_untrusted(text, runmap.RunMap()) == kept


# ---- command-line flags read the one list ---------------------------------------------------------------------------------


def test_j4_a_flag_with_an_underscore_or_a_hyphen_masks_its_value():
    for flag in (
        "--client_secret",
        "--api_key",
        "--api-key",
        "--db_password",
        "--x-api-key",
        "--client-secret",
    ):
        for form in (f"{flag} {P1}{P2}", f"{flag}={P1}{P2}", f'{flag} "{P1} {P2}"'):
            out = clean(f"run {form} now")
            assert P1 not in out and P2 not in out, f"a flag value is readable: {form}: {out!r}"
    out = clean(f'["--api_key","{P1}{P2}"]')
    assert P1 not in out, out


def test_j4_a_flag_with_a_word_glued_in_front_of_pass_or_auth_masks_its_value():
    """Round 5 (Issue 10): `--newpass v`, `--oldpass v`, `--postgresauth v` and `--authorization v` were readable on main and on
    the head of round 5 (the `=` form of the first three was masked by the generic key rule only). Ordinary words that end
    in `pass` or `auth` stay readable as flags, as on main: a flag `--bypass` is no credential."""
    for flag in ("--newpass", "--oldpass", "--postgresauth", "--authorization", "--NewPass"):
        for form in (f"{flag} {P1}{P2}", f"{flag}={P1}{P2}", f'{flag} "{P1} {P2}"'):
            out = clean(f"run {form} now")
            assert P1 not in out and P2 not in out, f"a flag value is readable: {form}: {out!r}"
        out = clean(f'["{flag}","{P1}{P2}"]')
        assert P1 not in out, out
    for flag in ("--bypass", "--compass", "--obsession", "--author"):
        assert f"{flag} {P1}{P2}" in clean(f"run {flag} {P1}{P2} now"), flag


def test_j4_every_spelling_of_the_key_list_is_a_flag():
    for key in key_spellings():
        if key in (
            "pass",
            "auth",
            "session",
            "bearer",
        ):  # only before `=` or `:` in text; not a flag name
            continue
        for form in (f"--{key} {P1}{P2}", f"--{key}={P1}{P2}"):
            out = clean(f"run {form} now")
            assert P1 not in out and P2 not in out, (
                f"a flag of the key list is not masked: {form}: {out!r}"
            )


def test_j4_names_that_are_no_credential_stay_readable():
    for flag, value in (("--secret-name", "prod"), ("--token-file", "keys"), ("--token-ttl", "30")):
        out = clean(f"run {flag} {value}")
        assert flag in out and value in out, f"a name that is no credential was masked: {out!r}"


def test_j4_the_scan_finds_every_shape_of_a_second_list():
    """The scan itself must work (a scan that finds nothing proves nothing). It is the function the real scan of `src/` runs
    (`tests.q8b_helpers.second_key_lists`), on a sample of each shape: a tuple one entry per line, a regex string, spellings
    with non-letters (`api_key`, `pass_word`), a `.split()`, a `+` chain, a set; a list of two words and a named list are not found."""
    sample = (
        'A = (\n    "password",\n    "token",\n    "secret",\n)\n'
        'B = "(?:password|token|secret)"\n'
        'C = ["api_key", "pass_word", "Secret", "x"]\n'
        'D = "password passwd pwd secret".split()\n'
        'E = "password|" + "token|" + "secret"\n'
        'F = {"password", "pwd", "credential"}\n'
        'G = ("password", "token")\n'
        'KEYS = ("password", "token", "secret")\n'
    )
    found = second_key_lists(ast.parse(sample), {"KEYS"})
    assert sorted(lineno for lineno, _ in found) == [1, 6, 7, 8, 9, 10], found
    # one line each: the tuple (1), the regex (6), the spellings (7), the split (8), the `+` chain (9), the set (10); the
    # two-word list (11) and the named list (12) are not reported


# ---- C1: the card's second view keeps every kind of secret ----------------------------------------------------------------

IBAN = "GB82" + "WEST" + "1234" + "5698" + "7654" + "32"
JWT = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ4eXoifQ" + "." + "Zm9vYmFyYmF6cXV4MTIz"
LONG = "Qx7" + "Lm2Vp9Zt4Rk8Ns1Yd6Hb3Wc5Jf0Ga7Eu2Xo9Ti4Pq"
CARD = "4539" + "1488" + "0343" + "6467"


def test_j5_a_secret_split_by_a_tag_is_masked_on_a_card():
    """Only the tag-stripped second view finds these (the first view reads the tag inside the secret): it is used when it
    found a secret of ANY kind of `SECRET_KINDS`, not only an assignment. A card number is split at a group boundary."""
    bad = []
    for secret in (IBAN, JWT, LONG, CARD):
        # The tag takes the spaces after it with it, so a tag followed by a space is what only the second view reads whole.
        # A card number is written with its own spaces, so it is split without one.
        seps = ("<i></i>", "<b></b>") if secret == CARD else ("<i></i> ", "<b></b>\t")
        for sep in seps:
            for i in (4, 8, 12) if secret == CARD else (4, 7, len(secret) // 2):
                out = clean(f"x {secret[:i]}{sep}{secret[i:]} y")
                flat = "".join(out.split())
                if secret[i:] in flat or secret[:i] in flat:
                    bad.append(out)
    assert not bad, f"a secret split by a tag is readable: {bad[:2]}"


def test_j5_the_card_test_reads_the_one_list_of_secret_kinds():
    assert runmap.SECRET_KINDS == redact.SECRET_KINDS
    assert {"IBAN", "JWT", "HIGHENTROPY", "CREDITCARD", "PRIVKEY"} <= runmap.SECRET_KINDS
    m = runmap.RunMap({"<IBAN_1>": IBAN, "<JWT_1>": JWT})
    assert channel_mod._secret_originals(m) == {IBAN, JWT}


# ---- the wording of the shipped text --------------------------------------------------------------------------------------


def test_j6_no_shipped_text_names_an_internal_decision_number():
    for name in ("CHANGELOG.md",):
        assert "D-03" not in (ROOT / name).read_text(encoding="utf-8"), name
    assert "D-03" not in R.LIMITS and "decision D" not in R.LIMITS
    for path in (ROOT / "src/hadavin_sdk").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "D-032" not in text, f"{path.name} names an internal decision number"


def test_j6_the_changelog_says_what_the_code_does_with_a_semicolon_and_a_comma():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for fragment in (
        "password=ab;cd",
        "Password=ab;Server=x",
        "password=ab,cd ef",
        "a value in angle brackets",
        "signing_key",
        "Bearer: John Smith paid",
        "password=ab;12:30x",
        "password=ab;http://x",
        "session_cookie=a; csrf=b; user=c",
        "`--newpass`",
        "authorization_endpoint",
        "`-https:`",
        "`newpass_enabled`",
        "`oauth` is not on the list",
    ):
        assert fragment in text, f"the CHANGELOG lacks {fragment!r}"
    assert "placeholder (`token=<A>" not in text


def test_j6_the_comma_pin_matches_the_code():
    out = clean(f"password={P1},{P2} {P3}")
    assert out == "password=<SECRET_1>", f"a comma ended the value: {out!r}"
    out = clean(f"a=1,password={P1},user=bob")
    assert out == "a=1,password=<SECRET_1>,user=bob", (
        f"a comma that starts a key was taken: {out!r}"
    )


def test_j6_the_whole_line_after_a_bearer_key_is_masked():
    out = clean("Bearer: John Smith paid")
    assert "Smith" not in out, f"a word after a bearer key is readable: {out!r}"
