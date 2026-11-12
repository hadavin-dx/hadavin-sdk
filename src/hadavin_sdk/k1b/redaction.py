"""Redaction before the model: every string of a case bundle is masked, then the case runs on the masked copy.

Uses the runtime's one choke point (``guard.runmap.redact_text``: NFKC, invisible characters, JSON escapes and the size
cap, then the studio redactor): ONE placeholder namespace per case, so a value
found in any alert field, log line, k8s record or runbook chunk is masked in all of them, and the model still
sees that two lines name the same host (``<HOST_1>`` stays ``<HOST_1>``). The placeholder map lives in this
call's memory only: it is never returned, written to the outputs, sent to the audit sink or logged. Only the
count of distinct values masked per class leaves this module, never a value.

Left unchanged on purpose, so citations and queries still resolve:
* evidence IDs (``logs/001.jsonl#2``) are built from file names and positions, not from content;
* file names; the values of ``service``, ``kind`` and ``fault_type`` are redacted like any other text (a plain word
  passes the redactor unchanged), so a secret planted there is masked;
* any string that is exactly a UTC timestamp (``parse_ts``); numbers, except under a credential key, where they are
  masked (a bool or None is always kept).

What this does NOT catch (``LIMITS``): the redactor is pattern-based. A name in free text ("Acme asked ..."), an
internal project name, a ticket number, a value in an unusual format, or a secret no pattern matches reaches the
model. Treat redaction as a strong first
filter, not as proof that no client data leaves.
"""

from __future__ import annotations

import base64
import binascii
import dataclasses
import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from typing import Any

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import (
    BARE_ENDINGS,
    COUNT_WORDS_BEFORE_TOKENS,
    GUARDED_ENDINGS,
    ORDINARY_WORDS,
    is_count_run,
    is_ordinary_pair,
)
from hadavin_sdk.k1b.bundle import Bundle, parse_ts

SCHEME = (
    "every text value and every key of the alert, metrics, logs, deploys, Kubernetes records and runbooks is "
    "masked with the studio redactor (pattern based; one placeholder per distinct value, per case) before the "
    "model or the injection screen sees it; file names, evidence IDs and timestamps are kept, and numbers are kept "
    "except under a credential key"
)
LIMITS = (
    "The redactor is pattern based. It does not catch names in free text, customer or project names, ticket "
    "numbers, values in unusual formats, or anything else no pattern matches.\n"
    "- A key that names a credential (for example `password` or `api_key`) and every entry of a Kubernetes Secret "
    "(a stored credential record) are masked under their own key. Three things are shown as written: a text that "
    "is exactly a UTC time, a true, false or null value, and a setting about a credential (below).\n"
    "- The same value is also masked where it is repeated elsewhere in the case only when all of this holds: it is "
    "a text of 4 to 255 characters directly under that key; it is made of printable ASCII characters and white "
    "space; it does not hold both kinds of quote mark; no part of it is something another pattern masks (an "
    "e-mail address, a host name, a key); and the copy is spelled the same way.\n"
    "- An entry of a Secret under a key that does not name a credential is masked elsewhere only when it also has "
    "at least 8 characters and is not all digits or one lower-case word (a value such as `orders` stays readable "
    "where it is repeated). At most 256 texts of one Secret, nested ones included, are treated this way.\n"
    "- Not masked where repeated: longer or shorter values, numbers, values nested deeper under a credential key, "
    "copies in another spelling (base64, capitals, wrapped over lines), and values with control or other special "
    "characters (a copy of such a value may be shown partly masked).\n"
    "- A setting about a credential (a key that ends in enabled, policy, count, expiry and the like) is shown only "
    "when its value is a yes or no word, a number or a time.\n"
    "- A record key with a word that ends in `pass`, `auth` or `session` (`newpass`, `postgresauth`) is masked unless that "
    "whole word is an ordinary English word from a short list (`bypass`, `compass`, `encompass`, `overpass`, `possession`, "
    "`obsession` and the like). An ordinary word with a second word of its own family is masked, written with `_`, `-` or "
    "nothing between: after `pass` words (`compass_key`, `compass_code`, `compass_value`, `compass_phrase`, `bypass_key`) "
    "and after `session` words (`possession_id`, `possession_key`, `possession_cookie`, `obsession_id`); `protection-bypass` "
    "is masked (a bypass secret). One table serves the key=value rule, the record walk and the flag rule. A bare `bypass`, "
    '`compass` or `possession` (and the other bare ordinary words of the list) is shown in every written form; a name made of an ordinary word and MORE characters (`compass_direction`, `compass2key`) is masked when its value is in quotes (`"compass_direction": "v"`, `compass2key="v"`), as before batch 11, and is shown as an unquoted `key=value` (`compass_direction=v`, `compass2key=v`) unless the name is one of the listed pairs (`compass_key=v` is masked); '
    "whether a bare `bypass` should be masked is the owner question `q-q8b-bare-bypass` (built: shown). `oauth`, `oauth_scopes` and `oauthProvider` are masked: `oauth` may hold a token. A harmless word that ends that way and is not on the list is hidden too, although it holds no "
    "credential. The record rule also masks some other keys that hold no credential "
    "(`session_duration`, `auth_method`, `pass_rate`, `tokenCount`, `tokenType`). A key written in capitals "
    "(`COOKIEJAR`, `COOKIESTORE`) is masked as a record key, as in a `key=value`; in lower case (`cookiejar`) it is shown on both sides.\n"
    '- A flag that names a credential (`--password`, `--newpass`, `--dbpass`, `--oauth`) takes the one word after a space as its value, on a card, in a tool result and in a log line: in `--newpass a b` the word `a` is masked and `b` is shown, because `b` may be a file name or another argument of the command (this second word is shown after every credential flag: a stated design choice). After the flags `--authorization` and `--bearer` the scheme word and the token after it are both masked (any scheme word, quoted or not; a Digest value to the next flag or the end of the line); in `Authorization: Token <t>` the scheme word stays readable and the token is masked. A second word after any other credential flag is shown (`--pass2 a b`: this holds for every flag named here); `authorization=a b` is a `key=value`, not a flag: its first word is masked and `b` is shown, not a flag rule. The flags `--cookie`, `--set-cookie` and `--session-cookie` take a value; `--no-cookies`, `--load-cookies`, `--save-cookies`, `--keep-session-cookies`, `--junk-session-cookies` and `--cookies` are not known to take a credential (switches or file names), so the word after them is shown. Written `--newpass=a b`, both words are masked. A flag with seven or more words joined by `-` or `_` in front of the credential word (`--a-b-c-d-e-f-g-password v`) keeps its value readable: the flag rule reads at most six words in front. In a `key=value` the key rule reads any run of digits after a key word (`pass` and 40 digits are masked) and then at most 20 more key characters, so a key word followed by digits and more than 20 other key characters (letters, `_`, `-`, `.`) keeps its value readable there. A header wrapped over lines: after `Basic`, `Token`, `ApiKey`, `Digest` or `Bearer` in an `Authorization` header (or a `Proxy-Authorization` one), or after a credential key (`X-Api-Key`, `token`, `secret`, `passwd`) with one of these scheme words, any line break and white space is a gap, as in a single line, and the next word of 8 or more characters (any letters, digits, `.`, `~`, `:`, `-`) is read as the token; a line that starts with a word of fewer than 8 characters is shown, and a line of prose that starts with a word of 8 or more characters is masked too (cost). A bare `Basic<LF>` uses only the base64 letters and 8 characters, a bare `Bearer` needs 12, and the other schemes have no rule without a header name in front of them (as on main). A header folded over several lines (each next line starts with a space or a tab, a line fold, RFC 9112 section 5.2) is masked to its last folded line for all five schemes, also when its first line has fewer than 8 characters (`Digest u="a",<LF> response="<hash>"`). A header named `Authorization` whose first word is any other scheme word (`NTLM`, `Negotiate`, `OAuth`, `Splunk`, `AWS4-HMAC-SHA256`, a name that starts with a capital letter and has hyphens or digits), or no scheme word, is masked to its last folded line too, with up to 8 more words on its first line; a fold may also start with a vertical tab, a form feed, a next-line, a line-separator or a paragraph-separator character. A lower-case word with a hyphen after `Authorization:` is read as the token, not as a scheme word. Three limits: a line that does not start with a space or a tab ends the header, so a continuation written with no indent is shown (it cannot be told from a new header line); the folded lines have no upper bound, so an unrelated indented block right after the header is masked (cost); and for `Basic`, `Token`, `ApiKey` and `Bearer` the token ends at white space on its line (a token has no space), so a second word on the same line is shown, as after a credential flag (a `Digest` value is masked to the end of its line). After `--authorization` and a scheme word a quoted text is read to 512 characters; a longer one is left to the other rules (a long text of ordinary words is shown).\n'
    "Masking is a first filter, not proof that no client data reached the model."
)
KINDS_NOTE = "Counts are distinct values masked per class (EMAIL, IPV4, ARN, ...), summed over the cases; no values."


def _kind(placeholder: str) -> str:
    return placeholder.strip("<>").rsplit("_", 1)[0]


def _key(k: Any, f: Callable[[str], str]) -> Any:
    """Dict keys can hold data too ({"bob@example.com": ...}); plain schema words pass the redactor unchanged."""
    return f(k) if isinstance(k, str) and k not in SCHEMA_WORDS else k


# The record and alert field names the tools read; they are never data, so they are not run through the redactor.
SCHEMA_WORDS = frozenset(
    {
        "title",
        "summary",
        "severity",
        "service_label",
        "fired_by",
        "labels",
        "ts",
        "level",
        "message",
        "service",
        "version",
        "kind",
        "name",
        "as_of",
        "spec",
        "events",
        "reason",
        "query",
        "points",
        "value",
    }
)


MASKED = "<SECRET_REDACTED>"
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SPLIT = re.compile(r"[_.\-\s]+")
_TRAILING_DIGITS = re.compile(r"(?<=[a-z])[0-9]+$")
# The older rule was written with `re.IGNORECASE`, which also reads U+017F (long s) as `s` and U+0130 / U+0131 (dotted
# and dotless i) as `i`; NFKC maps the long s, these two are mapped here, so a key spelled with them is still a key.
_FOLD = str.maketrans({"\u0130": "i", "\u0131": "i", "\u017f": "s"})
CREDENTIAL_WORDS = frozenset(
    [
        "pass",
        "password",
        "passwords",
        "passwd",
        "pwd",
        "passphrase",
        "secret",
        "secrets",
        "token",
        "apikey",
        "apikeys",
        "authorization",
        "auth",
        "credential",
        "credentials",
        "bearer",
        "session",
        "sessionid",
        "jsessionid",
        "phpsessid",
        "sessid",
        "cookie",
        "cookies",
    ]
)
GLUED_ENDINGS = (
    "password", "passwd", "pwd", "secret", "token", "apikey", "secretkey", "accesskey",
    "privatekey", "sessid", "accountkey", "keydata", "certdata", "certificatedata",
    "credential", "credentials", "signingkey", "encryptionkey",
    "protectionbypass",
) + GUARDED_ENDINGS  # fmt: skip
# `pass`, `auth` and `session` end many credential keys written as one word (`newpass`, `dbpass`, `postgresauth`,
# `jenkinssession`), and a few ordinary English words (`bypass`, `compass`, `obsession`). `BARE_ENDINGS`,
# `ORDINARY_WORDS` and `COUNT_WORDS_BEFORE_TOKENS` are NOT defined in this file: they are imported from `guard/redact.py`,
# the one place the card rules read them too. `oauth` is no ordinary word: a record key `oauth` may hold a token,
# so it is masked, as the card rule masks `oauth=`. A list of the words allowed in front of `pass` fails open (an unlisted
# `newpass` stayed readable, round 4); a list of the ordinary words fails closed (a harmless value is hidden). So a word that
# ends with one of them is a credential unless the whole word is in `ORDINARY_WORDS`. After `_`, `-` or a capital letter they
# are words of their own (`CREDENTIAL_WORDS`). `cookie` and `cookies` are credential words (a header or record key named
# `Cookie`, `COOKIE` or `Set-Cookie` holds a session credential; the key is read case-folded).
# Measured on `tests/q8b_key_corpus.py` (made up by the builder, so the numbers hold for that corpus only).
# The words in front of `key` or `keys` that make a credential: `api_key`, `dbaccess_key` (the word BEFORE ends with one of
# them), and the exact pairs (word before, word) `client-key-data`, `connect.sid`.
KEY_QUALIFIERS = ("api", "private", "access", "secret", "signing", "encryption", "account")
WORD_PAIRS = frozenset(
    {
        ("key", "data"),
        ("cert", "data"),
        ("certificate", "data"),
        ("connect", "sid"),
        ("protection", "bypass"),
    }
)
COUNT_WORDS_AFTER_TOKENS = frozenset(
    [
        "used",
        "remaining",
        "left",
        "per",
        "limit",
        "limits",
        "budget",
        "count",
        "total",
        "usage",
        "consumed",
    ]
)
SETTING_WORDS = frozenset(
    [
        "enabled",
        "disabled",
        "required",
        "policy",
        "length",
        "count",
        "age",
        "days",
        "ttl",
        "expiry",
        "expires",
    ]
)
SETTING_VALUE = re.compile(r"(?i)true|false|yes|no|on|off|none|[0-9]{1,10}[smhdw]?")


def _key_words(key: str) -> list[str]:
    # camelCase is cut first, on the key as written (as the older rule did), then NFKC (full-width and compatibility
    # letters read as plain letters), the fold of the three letters above, and the case
    plain = unicodedata.normalize("NFKC", _CAMEL.sub("_", key)).translate(_FOLD).casefold()
    return [_TRAILING_DIGITS.sub("", w) for w in _SPLIT.split(plain) if w]


# A key written in capitals with `COOKIE` and more letters glued behind it (`COOKIEJAR`, `COOKIESTORE`): the card rule reads `cookie`
# followed by a capital letter as a cookie key (`_COOKIE_KEY` in `guard/redact.py`); the word cut below does not split capitals
# from capitals, so the record walk reads the one word `cookiejar` and left it readable (round 10, Issue 6: text and record drift).
# `cookiejar` in lower case stays readable on both sides (pinned).
_CAPITALS_COOKIE = re.compile(r"(?<![A-Za-z])COOKIES?[0-9]*+[A-Z]")


def _glued_ending(w: str) -> bool:
    """Does the word end with one of `GLUED_ENDINGS`? An ending that is a bare word and one more word (`passcode`, `sessionid`,
    `authvalue`) counts after an ordinary word too (`bypasscode`, `compasskey`, `possessionid` are credential
    names, round 10 Issue 6): only the bare ordinary word is no key. The card rules read the same list."""
    return w.endswith(GLUED_ENDINGS)


def sensitive(key: object) -> bool:
    """Does a key (or the name of a named entry) say its value is a credential?

    The key is cut into words (at camelCase, `_`, `.`, `-` and white space; lower case; digits at the end of a word
    dropped). It is a credential key when a word is in `CREDENTIAL_WORDS`, ends with one of `GLUED_ENDINGS`, ends with
    `pass`, `auth` or `session` unless the whole word is in `ORDINARY_WORDS` (`newpass`, `dbpass`, `userauth` are keys;
    `bypass` and `compass` are not), is `key` or `keys` after a word that ends with one of `KEY_QUALIFIERS` (`dbaccess_key`),
    forms a pair of `WORD_PAIRS` with the word before it, or is `tokens` (unless it is a count: `max_tokens`, `reasoning_tokens`,
    `tokens_used`, `tokens_per_second`; the words are `COUNT_WORDS_BEFORE_TOKENS` and `COUNT_WORDS_AFTER_TOKENS`) or a word that ends
    in `tokens` (`apitokens`) unless the letters in front are count words alone (`maxtokens`, `is_count_run`).
    There is no exception by the last word: a key the older rule accepted is still accepted. Cost, accepted on purpose,
    so a key that holds no login secret is masked: `auth_method`, `session_duration`, `sessionAffinity` (the word
    `session` or `auth` alone), env entries named `PWD`, `OLDPWD` or ending in `pwd`, and any `tokens` key whose other
    words are not a count word listed above. A key is read after NFKC and with the long s and the dotted and dotless
    i written as plain letters, as the older `re.IGNORECASE` rule read it."""
    if not isinstance(key, str):
        return False
    # on the key as the older rule read it: NFKC and the fold of the long s and the dotted and dotless i (`COOKIEſTORE`, full-width capitals)
    if _CAPITALS_COOKIE.search(unicodedata.normalize("NFKC", key).translate(_FOLD)):
        return True
    words = _key_words(key)
    for i, w in enumerate(words):
        before = words[i - 1] if i else ""
        after = words[i + 1] if i + 1 < len(words) else ""
        if (
            w in CREDENTIAL_WORDS
            or _glued_ending(w)
            or (w.endswith(BARE_ENDINGS) and w not in ORDINARY_WORDS)
            or (w in ("key", "keys") and before.endswith(KEY_QUALIFIERS))
            or (before, w) in WORD_PAIRS
            or is_ordinary_pair(before, w)
        ):
            return True
        if (
            w == "tokens"
            and before not in COUNT_WORDS_BEFORE_TOKENS
            and after not in COUNT_WORDS_AFTER_TOKENS
        ):
            return True
        # A plural `tokens` glued to the word in front (`apitokens`, `accessTokens` is cut at the capital and read above):
        # a credential unless what stands in front of it is made of count words alone (`maxtokens`, `cachedinputtokens`).
        if (
            w.endswith("tokens")
            and w != "tokens"
            and not is_count_run(w[: -len("tokens")])
            and after not in COUNT_WORDS_AFTER_TOKENS
        ):
            return True
    return False


def _setting_key(key: object) -> bool:
    """A credential key whose last word says the entry is a setting ABOUT a credential (`..._policy_enabled`)."""
    return sensitive(key) and _key_words(str(key))[-1] in SETTING_WORDS


def _setting_value(obj: Any) -> bool:
    """The only values shown under a setting key: a bool, None, a number, a short on/off word or count. (A text that
    is exactly a UTC time is shown under any key; `_walk` checks that first, so it is not repeated here.)"""
    if obj is None or isinstance(obj, bool | int | float):
        return True
    return isinstance(obj, str) and SETTING_VALUE.fullmatch(obj) is not None


FALLBACK_KEY = "secret"
MAX_SPELLING_CHARS = 255
MIN_REGISTER_CHARS = 8
MAX_REGISTERED_ENTRIES = (
    256  # per `data` / `stringData` of one Secret; later entries get the fixed mask
)
_PLAIN_CHARS = frozenset(chr(c) for c in range(0x21, 0x7F)) - frozenset(";&,\"'")
_SAFE_KEY = re.compile(r"[A-Za-z0-9_.\-]{1,60}")
_ONE_LOWER_WORD = re.compile(r"[a-z]+")
_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")


def _attempts(key: str, text: str, credential: bool) -> list[tuple[str, str]]:
    """(key to write, quote) for one spelling of a value, in the order tried."""
    if not text or len(text) > MAX_SPELLING_CHARS:
        return []
    if not credential and (
        len(text) < MIN_REGISTER_CHARS or text.isdigit() or _ONE_LOWER_WORD.fullmatch(text)
    ):
        return []
    if all(c in _PLAIN_CHARS for c in text):
        own = [(key, "")] if credential and _SAFE_KEY.fullmatch(key) else []
        return [*own, (FALLBACK_KEY, "")]
    quote = next((q for q in ('"', "'") if q not in text), None)
    return [(FALLBACK_KEY, quote)] if quote else []


def _accepted(key: str, text: str, credential: bool, f: Callable[[str], str]) -> str | None:
    for k, quote in _attempts(key, text, credential):
        masked = f(f"{k}={quote}{text}{quote}")
        if not masked.startswith(k + "="):
            continue
        part = masked[len(k) + 1 :]
        if quote:
            if len(part) < 2 or part[0] != quote or part[-1] != quote:
                continue
            part = part[1:-1]
        if _ONLY_PLACEHOLDERS.fullmatch(part):
            return part
    return None


class _Budget:
    """The texts of ONE Kubernetes Secret that may be registered (`MAX_REGISTERED_ENTRIES`, counted over the whole
    `data` / `stringData`, nested lists and maps included); later texts get the fixed mask under their key only."""

    def __init__(self) -> None:
        self.left = MAX_REGISTERED_ENTRIES

    def take(self) -> bool:
        if self.left <= 0:
            return False
        self.left -= 1
        return True


def _pair(key: str, value: str, f: Callable[[str], str], budget: _Budget | None = None) -> str:
    """A value whose key names a credential, or a text inside a Kubernetes Secret (`budget` is that Secret's).

    The value is written to the redactor behind a key word (its own key when both are plain, else the word `secret`
    and a quote mark), so the redactor's key=value rules see it; the decoded text of a base64 value is tried too. The
    result is taken ONLY when it is that key, `=` and nothing but placeholders; a result that merely changed is not
    taken. Otherwise the whole value becomes `MASKED`. So a value under a credential key reaches the model only as
    placeholders or as the fixed mask, never partly masked.

    Masked where it is repeated elsewhere in the case only within the limits of `LIMITS`: a text of 4 to 255
    characters directly under the key, printable ASCII and white space, not both kinds of quote mark, no part that
    another pattern masks, and a copy spelled the same way. Two exceptions to the masking are made before this function
    is called (`_walk`): a text that is exactly a UTC timestamp, and a value under a setting key that is a yes or no
    word, a number or a time. A text of a Secret past the budget (and a credential value of such a text) is masked
    under its key only."""
    credential = sensitive(key)
    in_secret = budget is not None
    if (not credential and not in_secret) or (in_secret and not budget.take()):
        f(value)
        return MASKED
    spellings = [value]
    try:
        spellings.append(base64.b64decode(value, validate=True).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError):
        pass
    result = None
    for text in spellings:
        got = _accepted(key, text, credential, f)
        if got is None:
            continue
        result = got
        if not in_secret:
            return result
    if result is not None:
        return result
    f(value)
    return MASKED


def _named(obj: dict) -> tuple[Any, list[Any]]:
    """(the sensitive name, the keys that hold the value) of an entry shaped {name|key: ..., value: ...}, in any letter
    case. EVERY name-like key is looked at (`{"name": "db", "key": "password", "value": ...}` is named by `key`), and
    every spelling of `value` holds the value."""
    names = [obj[k] for k in obj if isinstance(k, str) and k.lower() in ("name", "key")]
    value_keys = [k for k in obj if isinstance(k, str) and k.lower() == "value"]
    name = next((n for n in names if sensitive(n)), None)
    if name is None or not value_keys:
        return None, []
    return name, value_keys


def _is_secret(obj: dict) -> bool:
    """A record of kind Secret, in any letter case (`kind: secret`)."""
    kind = obj.get("kind")
    return isinstance(kind, str) and kind.casefold() == "secret"


def _walk_dict(
    obj: dict, f: Callable[[str], str], sens: bool, budget: _Budget | None, secret: bool
) -> dict[Any, Any]:
    """One dict. `secret`: this dict is a Kubernetes Secret, or the `spec` of a record whose kind is Secret (a bundle's
    k8s record has exactly the keys kind, name, as_of, spec, events, so the Secret's `data` sits under `spec`)."""
    name, value_keys = _named(obj)
    out: dict[Any, Any] = {}
    for k, v in obj.items():
        if k in value_keys:
            out[_key(k, f)] = _walk(v, f, str(name), sens, budget)
        elif secret and k in ("data", "stringData"):
            # the content of a Secret whatever its shape (a map, a list, a text, a number): every text in it is
            # registered up to ONE budget, so a text copied into a log is masked there too
            out[_key(k, f)] = _walk(v, f, str(k), True, _Budget(), True)
        elif secret and k == "spec" and isinstance(v, dict):
            out[_key(k, f)] = _walk_dict(v, f, sens, budget, True)
        else:
            out[_key(k, f)] = _walk(v, f, k, sens, budget)
    return out


def _walk(
    obj: Any,
    f: Callable[[str], str],
    key: str | None = None,
    secret_data: bool = False,
    budget: _Budget | None = None,
    secret_content: bool = False,
) -> Any:
    """Every string is redacted, at any depth: no key exempts a value. `key` is the parent key (or the name of a named
    entry), `secret_data` says the value sits under a credential key or in a Secret, `budget` that it is inside the
    `data` / `stringData` of a Secret (only those and values directly under a credential key are registered).
    `secret_content` is true for the `data` / `stringData` value itself: a map there gives each entry its own key."""
    own = sensitive(key)
    sens = secret_data or own
    if own and not secret_data and _setting_key(key) and _setting_value(obj):
        return obj
    if isinstance(obj, str):
        if parse_ts(obj) is not None:
            return obj
        if key is not None and sens:
            return _pair(key, obj, f, budget)
        return f(obj)
    if isinstance(obj, int | float) and not isinstance(obj, bool) and sens:
        return MASKED
    if isinstance(obj, dict):
        if secret_content:
            return {_key(kx, f): _walk(vx, f, str(kx), True, budget) for kx, vx in obj.items()}
        return _walk_dict(obj, f, sens, budget, _is_secret(obj))
    if isinstance(obj, list):
        return [_walk(v, f, key, sens, budget) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, f, key, sens, budget) for v in obj)
    return obj


def _pairs(items: tuple[tuple[str, Any], ...], f: Callable[[str], str]) -> tuple[Any, ...]:
    """(file, content) pairs: the file name stays, the content is walked."""
    return tuple((rel, _walk(content, f)) for rel, content in items)


def _apply(b: Bundle, f: Callable[[str], str]) -> Bundle:
    return dataclasses.replace(
        b,
        alert=_walk(b.alert, f),
        metrics=_pairs(b.metrics, f),
        logs=_pairs(b.logs, f),
        deploys=_walk(b.deploys, f),
        k8s=_pairs(b.k8s, f),
        runbooks=_pairs(b.runbooks, f),
    )


def redact_bundle(b: Bundle) -> tuple[Bundle, Counter[str]]:
    """The masked copy of one bundle and the distinct values masked per class. EVERY string goes through
    `tools.redact_layered` (the runtime's choke point for tool results: NFKC, invisible characters, JSON escapes, the
    size cap, percent, entity and base64-free layers to a fixed point, marker neutralising) with ONE
    map: pass 1 builds the map over the whole bundle, pass 2 masks with the complete map (a value found in a later
    record is masked in the earlier ones). The map is dropped here; a string over the cap raises `InputTooLarge`."""
    mapping = runmap.RunMap()

    total = 0

    def mask(s: str) -> str:
        nonlocal total
        total += len(s)
        if total > 2 * defaults.MAX_BUNDLE_CHARS:  # pass 1 and pass 2 both count
            raise runmap.InputTooLarge("InputTooLarge")
        try:
            return runmap.redact_untrusted(s, mapping)
        except runmap.TooDeep:  # nested deeper than the cap: not shown
            return MASKED

    _apply(b, mask)  # pass 1: find every value
    total = 0
    out = _apply(b, mask)  # pass 2: mask with the whole map
    return out, Counter(_kind(p) for p in mapping)
