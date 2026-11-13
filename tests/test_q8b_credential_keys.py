"""Q8b, incident cases: a value under a credential key (a key whose name says its value is a login secret) and every
entry of a Kubernetes Secret reach the model only as placeholders or as the fixed mask, never partly masked.

Made-up data only. The long key word and every value under it are built from parts (the repository's secret scan
refuses that word followed by a quoted text). Each assertion carries the message the mutant list quotes
(``tests/q8b_mutants.py``). The cases are named after the rows of the ticket's appendix.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import UTC, datetime

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
from hadavin_sdk.k1b import redaction as R
from hadavin_sdk.k1b.bundle import Bundle, load_bundle
from hadavin_sdk.k1b.redaction import redact_bundle
from hadavin_sdk.k1b.tools import Snapshot
from tests import k1b_support as K

PW_KEY = "pass" + "word"
P = "correct horse battery staple"
ONE = "hunter2" + "secretXYZ"
T = "tr0ub" + "4dor"
PLAIN = "qxzjkwvy1234"
LONG = " ".join(["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"] * 9)[:300]
V255 = ("ab cd " * 50)[:255]
V256 = ("ab cd " * 50)[:256]
ESC_VALUE = "hunter\x1b[0m2" + "secretXYZ"
BOTH_QUOTES = "pa55\"word 'tail' part"
DB_PW = "Zq7" + "xkW2vy9JtR4m"
ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")
BREAKS = re.compile(r"[\s;&,\"']+")
XFAIL = pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Q8d: sweep of registered secrets before the patterns",
)


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def shown(*records):
    """The records as `redact_bundle` shows them (two passes, one map), and the count of masked values per class."""
    bundle = Bundle(
        case_id="case-q8b",
        alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC),
        alert_time_text=K.ALERT_TIME,
        alert={},
        metrics=(),
        logs=(),
        deploys=tuple(records),
        k8s=(),
        runbooks=(),
        ids=frozenset(),
        manifest_sha256="0" * 64,
    )
    out, counts = redact_bundle(bundle)
    return list(out.deploys), counts


def shape_ok(value) -> bool:
    """Only placeholders, or the fixed mask; for a list or a dict: every item."""
    if isinstance(value, str):
        return value == R.MASKED or ONLY_PLACEHOLDERS.fullmatch(value) is not None
    if isinstance(value, list | tuple):
        return all(shape_ok(v) for v in value)
    if isinstance(value, dict):
        return all(shape_ok(v) for v in value.values())
    return False


def words_of(value) -> list[str]:
    """What must not be readable: every run of 4 or more characters between white space and break characters, of the
    value as written and of its base64-decoded text."""
    if isinstance(value, list | tuple):
        return [w for v in value for w in words_of(v)]
    if isinstance(value, dict):
        return [w for v in value.values() for w in words_of(v)]
    if not isinstance(value, str):
        return [str(value)]
    texts = [value]
    try:
        texts.append(base64.b64decode(value, validate=True).decode("utf-8"))
    except ValueError:
        pass
    # a value that is itself the text of a placeholder (`look-alike value`) cannot be told from its mask
    return [
        w
        for t in texts
        for w in BREAKS.split(t)
        if len(w) >= 4 and not runmap.PLACEHOLDER.fullmatch(w)
    ]


def tail(text):
    """A stand-in redactor that answers `<key>=<text>` for every `key=value` it is given."""
    return lambda s: s.partition("=")[0] + "=" + text if "=" in s else s


# ---- S: the acceptance rule of `_pair`, with a stand-in redactor ------------------------------------------------------


def test_s1_a_partly_masked_result_is_refused():
    got = R._pair(PW_KEY, PLAIN, tail("<SECRET_1> rest"))
    assert got == R.MASKED, f"a partly masked value was accepted: {got!r}"


def test_s2_text_after_the_placeholder_is_refused():
    got = R._pair(PW_KEY, PLAIN, tail("<SECRET_1>x"))
    assert got == R.MASKED, f"text after the placeholder was accepted: {got!r}"
    got = R._pair(PW_KEY, "qx zj", lambda s: 'secret="<SECRET_1>x"')
    assert got == R.MASKED, f"text after the placeholder was accepted (quoted): {got!r}"


def test_s3_a_result_without_its_key_is_refused():
    got = R._pair(PW_KEY, PLAIN, lambda s: "p<SECRET_1>ssword=<SECRET_1>")
    assert got == R.MASKED, f"a result without its key was accepted: {got!r}"
    # the whole `key=value` text answered as one placeholder: what is registered is not the value
    got = R._pair(PW_KEY, PLAIN, lambda s: "<SECRET_1>" if "=" in s else s)
    assert got == R.MASKED, f"a result without its key was accepted (one placeholder): {got!r}"


def test_s4_two_placeholders_are_accepted():
    got = R._pair(PW_KEY, PLAIN, tail("<SECRET_1><EMAIL_2>"))
    assert got == "<SECRET_1><EMAIL_2>", f"two placeholders were refused: {got!r}"


def test_s5_a_look_alike_placeholder_is_refused():
    got = R._pair(PW_KEY, PLAIN, tail("<secret_1>"))
    assert got == R.MASKED, f"a look-alike placeholder was accepted: {got!r}"


def test_s6_what_is_written_to_the_redactor():
    calls: list[str] = []

    def record(s: str) -> str:
        calls.append(s)
        return s

    R._pair(PW_KEY, "qx zj", record)
    assert calls == ['secret="qx zj"', "qx zj"], (
        f"a value that is not plain was written under its real key: {calls!r}"
    )
    calls.clear()
    R._pair(PW_KEY, "q" * 256, record)
    assert calls == ["q" * 256], (
        f"an over-long spelling was tried: {len(calls)} calls, {[c[:20] for c in calls]!r}"
    )


def test_s7_a_quoted_attempt_without_quotes_is_refused():
    got = R._pair(PW_KEY, "qx zj", lambda s: "secret=<SECRET_1>" if s.startswith("secret=") else s)
    assert got == R.MASKED, f"a quoted attempt without its quotes was accepted: {got!r}"


# ---- T1: the key rule -------------------------------------------------------------------------------------------------

CREDENTIAL_KEYS = [
    "PG" + PW_KEY.upper(),
    "pwd",
    "DB" + PW_KEY.capitalize(),
    "secretkey",
    "secrets",
    "root" + PW_KEY,
    "accessKey",
    "DB_" + PW_KEY.upper(),
    "authorization",
    "private_key",
    "privateKey",
    "bearer",
    "passphrase",
    PW_KEY + "_for_the_primary_database_replica",
    "api_tokens",
    "refresh_tokens",
    "tokens",
    "session",
    "JSESSIONID",
    "auth",
    "account_key",
    "client-key-data",
    "connect.sid",
    PW_KEY + "2",
    "token1",
    "OLDPWD",
    PW_KEY,
    "api_key",
    "api-key",
    "apikey",
    "clientSecret",
    "accessToken",
    "db" + PW_KEY.capitalize(),
    "credentials",
    "token",
    "pass",
    "SECRET_KEY_BASE",
    PW_KEY + "_hash",
    PW_KEY + "_used",
    "token_type",
    "client_secret_max",
    "API_KEY_TYPE",
    "token_policy",
    "sas_token",
]
SETTING_KEYS = [PW_KEY + "_policy_enabled", "token_expiry", "secret_count"]
OTHER_KEYS = [
    "author",
    "tokens_used",
    "max_tokens",
    "prompt_tokens",
    "total_tokens",
    "cache_key",
    "object_key",
    "key",
    "message",
    "compass",
    "bypass",
    "oauth",
    "authority",
]


def test_t1_the_key_rule():
    missed = [k for k in CREDENTIAL_KEYS + SETTING_KEYS if not R.sensitive(k)]
    assert not missed, f"the key rule changed: not a credential key any more: {missed}"
    wrong = [k for k in OTHER_KEYS if R.sensitive(k)]
    assert not wrong, f"the key rule changed: now a credential key: {wrong}"
    assert not R.sensitive(None) and not R.sensitive(7), (
        "the key rule changed: a key that is no text"
    )
    setting = [k for k in CREDENTIAL_KEYS + SETTING_KEYS + OTHER_KEYS if R._setting_key(k)]
    assert setting == ["token_policy", *SETTING_KEYS], (
        f"the key rule changed: setting keys: {setting}"
    )


def test_t1_every_key_the_older_rule_accepted_is_still_accepted():
    """The rule this ticket replaced, written out here, against the new one: every key of one or two words from the
    list below, with every separator (34,410 made-up keys, no random numbers)."""
    older = re.compile(
        r"(^|[_.\-\s])(pass(word|wd|phrase)?|secret|token|api[_-]?key|authorization|credentials?"
        r"|private[_-]?key|bearer)($|[_.\-\s])",
        re.IGNORECASE,
    )
    camel = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
    words = [
        "pass", PW_KEY, "passwd", "passphrase", "secret", "token", "api", "key", "apikey", "authorization",
        "credential", "credentials", "private", "bearer", "db", "client", "Access", "Token", "Secret", "Key", "x",
        "root", "enabled", "policy", "type", "id", "hash", "2", "base", "API", "Private", "used", "max", "min",
        "count", "expiry", "tokens",
    ]  # fmt: skip
    seps = ["_", ".", "-", " ", ""]
    keys = set(words) | {a + s + b for a in words for s in seps for b in words}
    keys |= {a + s for a in words for s in seps} | {s + a for a in words for s in seps}
    accepted = [k for k in sorted(keys) if older.search(camel.sub("_", k))]
    assert len(accepted) > 3000, len(accepted)
    refused = [k for k in accepted if not R.sensitive(k)]
    assert not refused, (
        f"the key rule changed: keys the older rule accepted are refused: {refused[:10]}"
    )


# ---- N1: masked under its own key -------------------------------------------------------------------------------------


def _under(key):
    return lambda rec: rec[key]


N1_ROWS = [
    ("M1 PG+key, multi-word", {"PG" + PW_KEY.upper(): P}, None),
    ("M1 env entry PG+key", {"name": "PG" + PW_KEY.upper(), "value": ONE}, "value"),
    ("M1 pwd", {"pwd": ONE}, None),
    ("M1 DB+key", {"DB" + PW_KEY.capitalize(): P}, None),
    ("M1 secretkey", {"secretkey": P}, None),
    ("M1 secrets", {"secrets": P}, None),
    ("M1 root+key", {"root" + PW_KEY: P}, None),
    ("M1 accessKey", {"accessKey": P}, None),
    ("M2 list in env entry", {"name": "DB_" + PW_KEY.upper(), "value": [P, 42]}, "value"),
    ("M2 Name/Value", {"Name": "DB_" + PW_KEY.upper(), "Value": P}, "Value"),
    ("M2 key/value", {"key": "api_key", "value": P}, "value"),
    ("B1r authorization", {"authorization": P}, None),
    ("B1r private_key", {"private_key": P}, None),
    ("B1r privateKey", {"privateKey": P}, None),
    ("B1r bearer", {"bearer": P}, None),
    ("B1r passphrase", {"passphrase": P}, None),
    ("B1r long-suffix key", {PW_KEY + "_for_the_primary_database_replica": P}, None),
    ("B1r long-suffix key, one word", {PW_KEY + "_for_the_primary_database_replica": ONE}, None),
    ("B1r 300-char multi-word", {PW_KEY: LONG}, None),
    ("255 chars", {PW_KEY: V255}, None),
    ("256 chars", {PW_KEY: V256}, None),
    ("M6 ESC inside value", {PW_KEY: ESC_VALUE}, None),
    ("F5 sweep", {PW_KEY: P}, None),
    ("F5 a b", {PW_KEY: "a b"}, None),
    ("F5 both quotes", {"db_" + PW_KEY: BOTH_QUOTES}, None),
    ("XF composite", {"token": "bob.smith@example.com Zx9 tail"}, None),
    ("1d near miss +00:00", {"token": "2026-11-11T10:00:00+00:00"}, None),
    ("B1 key_used one word", {PW_KEY + "_used": T}, None),
    ("B1 key_used multi-word", {PW_KEY + "_used": P}, None),
    ("B1 env API_KEY_TYPE", {"name": "API_KEY_TYPE", "value": T}, "value"),
    ("B1 client_secret_max", {"client_secret_max": T}, None),
    ("B1 gate refuses a word", {PW_KEY + "_policy_enabled": T}, None),
    ("B1 gate refuses a list", {PW_KEY + "_policy_enabled": ["on", T]}, None),
    ("B1 gate refuses 11 digits", {"token_expiry": "12345678901"}, None),
    ("M2 api_tokens list", {"api_tokens": [P]}, None),
    ("M2 refresh_tokens", {"refresh_tokens": P}, None),
    ("M2 tokens", {"tokens": P}, None),
    ("M2 session", {"session": P}, None),
    ("M2 JSESSIONID", {"JSESSIONID": ONE}, None),
    ("M2 auth", {"auth": P}, None),
    ("M2 account_key", {"account_key": P}, None),
    ("M2 client-key-data", {"client-key-data": P}, None),
    ("M2 connect.sid", {"connect.sid": ONE}, None),
    ("M2 key2", {PW_KEY + "2": P}, None),
    ("M2 token1", {"token1": P}, None),
    ("M2 OLDPWD", {"name": "OLDPWD", "value": "/srv/app"}, "value"),
    ("look-alike value", {PW_KEY: "<SECRET_1>"}, None),
    ("one letter", {PW_KEY: "a"}, None),
]
N1_SECRET_ROWS = [
    ("M3 Secret username", {"kind": "Secret", "stringData": {"username": "orders-svc"}}),
    ("M5 Secret DB_NAME b64", {"kind": "Secret", "data": {"DB_NAME": b64("orders")}}),
    ("F5b Secret cfg", {"kind": "Secret", "stringData": {"cfg": P}}),
    ("F5b Secret b64", {"kind": "Secret", "data": {"p": b64(P)}}),
    ("M1 Secret LOG_LEVEL", {"kind": "Secret", "data": {"LOG_LEVEL": b64("info")}}),
    ("M1 Secret credential key short", {"kind": "Secret", "stringData": {"db_" + PW_KEY: "abcd"}}),
    (
        "F5c Secret data under spec",
        {"kind": "Secret", "spec": {"data": {"DB_USER": b64("postgres")}}},
    ),
    ("F5c Secret stringData under spec", {"kind": "Secret", "spec": {"stringData": {"cfg": P}}}),
]


def _check_n1(label, original, got):
    assert shape_ok(got), f"part of the value is readable ({label}): shown as {got!r}"
    text = json.dumps(got)
    readable = [w for w in words_of(original) if w in text]
    assert not readable, f"part of the value is readable ({label}): {readable} in {got!r}"


@pytest.mark.parametrize(("label", "record", "at"), N1_ROWS, ids=[r[0] for r in N1_ROWS])
def test_n1_a_value_under_a_credential_key(label, record, at):
    key = at or next(iter(record))
    (out,), _ = shown(record)
    _check_n1(label, record[key], out[key])


@pytest.mark.parametrize(("label", "record"), N1_SECRET_ROWS, ids=[r[0] for r in N1_SECRET_ROWS])
def test_n1_an_entry_of_a_secret(label, record):
    def entries(rec):
        inner = rec.get("spec", rec)
        return inner.get("data") or inner.get("stringData")

    (out,), _ = shown(record)
    _check_n1(label, entries(record), entries(out))


def test_n1_a_secret_whose_data_is_not_a_map():
    """A malformed Secret (the ticket is silent; the option that masks more): nothing of it is shown or registered."""
    for content in (P, [P, 42], 12345678, [{"note": P}]):
        for record in (
            {"kind": "Secret", "data": content},
            {"kind": "Secret", "spec": {"stringData": content}},
        ):
            (out, second), counts = shown(record, {"message": f"saw {P}"})
            text = json.dumps(out)
            assert "horse" not in text and "12345678" not in text and "42" not in text, (
                f"part of the value is readable: a Secret whose data is not a map: {out!r}"
            )
            assert second == {"message": f"saw {P}"} and not counts, (second, counts)


def test_n1_a_number_in_a_named_entry():
    (out,), _ = shown({"name": "DB_" + PW_KEY.upper(), "value": 12345678})
    assert out["value"] == R.MASKED, (
        f"part of the value is readable: a number in a named entry: {out!r}"
    )
    (out,), _ = shown({"pin_token": 12345678})
    assert out["pin_token"] == R.MASKED, f"part of the value is readable: a number: {out!r}"


SETTING_ROWS = [
    {PW_KEY + "_used": T},
    {"name": "API_KEY_TYPE", "value": T},
    {"token_policy": {"default": T}},
    {"client_secret_max": T},
    {PW_KEY + "_policy_enabled": T},
    {"name": "TOKEN_TTL", "value": T},
    {"token_expiry": T + " 30d"},
    {"secret_count": "3 " + T},
]


def test_n1_a_value_under_a_setting_key_is_masked():
    """One test, not one per row: the mutant list pins it by its plain name."""
    for record in SETTING_ROWS:
        (out,), _ = shown(record)
        assert T not in json.dumps(out), f"a value under a setting key was shown: {out!r}"
        value = out["value"] if "value" in out else next(iter(out.values()))
        assert shape_ok(value), f"a value under a setting key was shown: {out!r}"


def test_n1_a_list_under_a_setting_key():
    (out,), _ = shown({PW_KEY + "_policy_enabled": ["on", T]})
    got = out[PW_KEY + "_policy_enabled"]
    assert shape_ok(got), f"a value under a setting key was shown: an item of a list: {got!r}"
    (out,), _ = shown({"token_policy": {"allowed": [T, {"note": T}]}})
    assert T not in json.dumps(out), f"a value under a setting key was shown: nested: {out!r}"


# ---- N2: masked where it is repeated ----------------------------------------------------------------------------------

N2_ROWS = [
    ("F5b repeat, pattern-free", {PW_KEY: P}, f"login with {P} failed; correct answer", ["horse", "battery", "staple"]),
    ("M3 Secret username + log", {"kind": "Secret", "stringData": {"username": "orders-svc"}},
     "user orders-svc NAME denied", ["orders-svc"]),
    ("M4 percent in value + copy", {PW_KEY: "ab%20cd9xtail"},
     "saw ab%20cd9xtail and ab cd9xtail", ["cd9xtail"]),
    ("M4 backslash-u in value + copy", {PW_KEY: "ab\\u0041cd9xtail"},
     "saw ab\\u0041cd9xtail and abAcd9xtail", ["cd9xtail"]),
    ("XF respelled, percent copy", {"kind": "Secret", "stringData": {"cfg": P}},
     "GET /login?p=correct%20horse%20battery%20staple", ["horse", "battery", "staple"]),
]  # fmt: skip


@pytest.mark.parametrize(("label", "record", "line", "words"), N2_ROWS, ids=[r[0] for r in N2_ROWS])
def test_n2_a_value_is_masked_where_repeated(label, record, line, words):
    (_, second), _ = shown(record, {"message": line})
    readable = [w for w in words if w in second["message"]]
    assert not readable, f"readable in the log line ({label}): {readable} in {second['message']!r}"


def test_n2_a_secret_entry_is_masked_where_repeated():
    (first, second), _ = shown(
        {"kind": "Secret", "stringData": {"cfg": P}}, {"message": f"login with {P} failed"}
    )
    readable = [w for w in ("horse", "battery", "staple") if w in second["message"]]
    assert not readable, f"readable in the log line: {readable} in {second['message']!r}"
    assert first["stringData"]["cfg"] in second["message"], (first, second)


def test_n2_decoded_copy_of_a_base64_entry():
    (first, second), _ = shown(
        {"kind": "Secret", "data": {"p": b64(P)}}, {"message": f"login with {P} failed"}
    )
    readable = [w for w in ("horse", "battery", "staple") if w in second["message"]]
    assert not readable, f"readable in the log line: {readable} in {second['message']!r}"
    under_key = first["data"]["p"]
    assert second["message"] == f"login with {under_key} failed", (
        f"readable in the log line: the placeholder under the key ({under_key}) is not the one in "
        f"{second['message']!r}"
    )


@pytest.mark.parametrize("value", ["line1 horse\nline2 staple", 'say "horse" twice'])
def test_n2_a_json_escaped_copy(value):
    copy = json.dumps({"stringData": {"cfg": value}})
    (_, second), _ = shown(
        {"kind": "Secret", "stringData": {"cfg": value}},
        {"annotations": {"last-applied-configuration": copy}},
    )
    text = json.dumps(second)
    assert "horse" not in text and "staple" not in text, f"readable in the log line: {text}"


def _fixture(tmp_path, shape="spec.data"):
    """The default made-up case plus one Secret record (the only shape a loaded case allows: `data` under `spec`)
    and a second log file whose lines use the Secret's words; the fourth line holds the made-up database secret."""
    parts = K.default_parts()
    data = {
        "LOG_LEVEL": b64("info"),
        "DEBUG": b64("true"),
        "ENV": b64("prod"),
        "PORT": b64("5432"),
        "DB_USER": b64("postgres"),
        "DB_NAME": b64("orders"),
        "DB_" + PW_KEY.upper(): b64(DB_PW),
    }
    spec = {"data": data} if shape == "spec.data" else {"kind": "Secret", "data": data}
    parts["k8s"]["002"] = {
        "kind": "Secret",
        "name": "orders-conn",
        "as_of": "2026-01-01T09:00:00Z",
        "spec": spec,
        "events": [],
    }
    ts = "2026-01-01T09:{:02d}:00Z"
    parts["logs"]["002"] = [
        {"ts": ts.format(20), "level": "info", "message": "information: retry in 5s", "service": "orders"},
        {"ts": ts.format(21), "level": "error",
         "message": "orders-api timeout on port 5432 as postgres in prod", "service": "orders"},
        {"ts": ts.format(22), "level": "info", "message": "debug=true orders_count=3 env prod", "service": "api"},
        {"ts": ts.format(23), "level": "error",
         "message": "login as postgres with " + DB_PW + " refused", "service": "db"},
        {"ts": ts.format(24), "level": "info", "message": "start", "service": "postgres"},
    ]  # fmt: skip
    raw = load_bundle(K.make_bundle(tmp_path, **{k: parts[k] for k in ("k8s", "logs")}))
    masked, _ = redact_bundle(raw)
    return raw, masked


def _log_records(bundle):
    return [r for _, rows in bundle.logs for r in rows]


def test_n2_f5c_secret_data_under_spec(tmp_path):
    """Both shapes a loaded case can have: `spec: {data: ...}` and `spec: {kind: Secret, data: ...}`."""
    for shape in ("spec.data", "spec.manifest"):
        _, masked = _fixture(tmp_path / shape, shape)
        lines = [r["message"] for r in _log_records(masked)]
        assert not [x for x in lines if DB_PW in x], f"readable in the log line ({shape}): {lines}"
        secret = next(o for _, o in masked.k8s if o.get("kind") == "Secret")
        entries = secret["spec"]["data"]
        assert shape_ok(entries), (
            f"readable in the log line ({shape}): a Secret entry under spec is shown: {entries!r}"
        )
        under_key = entries["DB_" + PW_KEY.upper()]
        assert f"login as postgres with {under_key} refused" in lines, (under_key, lines)


# ---- N3: no fragment of a value is registered --------------------------------------------------------------------------


def test_n3_no_fragment_for_an_esc_value():
    (_, second), _ = shown({PW_KEY: ESC_VALUE}, {"message": "the hunter came"})
    assert second["message"] == "the hunter came", (
        f"a fragment was registered: {second['message']!r}"
    )


def test_n3_no_fragment_of_a_multi_word_value():
    (_, second), _ = shown({PW_KEY: P}, {"message": f"login with {P} failed; correct answer"})
    assert second["message"].endswith("failed; correct answer"), (
        f"a fragment was registered: {second['message']!r}"
    )


def test_n3_no_fragment_of_a_one_letter_value():
    (_, second), _ = shown({PW_KEY: "a"}, {"message": "a cat and a hat"})
    assert second["message"] == "a cat and a hat", (
        f"a fragment was registered: {second['message']!r}"
    )


# ---- X: not masked where repeated (limits; follow-up Q8d). Each: one assertion, strict xfail ---------------------------


def _second_message(record, line):
    (_, second), _ = shown(record, {"message": line})
    return second["message"]


@XFAIL
def test_x1_a_composite_value_is_masked_where_repeated():
    line = _second_message(
        {"token": "bob.smith@example.com Zx9 tail"},
        "login with bob.smith@example.com Zx9 tail failed",
    )
    assert "Zx9 tail" not in line


@XFAIL
def test_x2_a_value_over_255_characters_is_masked_where_repeated():
    assert "bravo" not in _second_message({PW_KEY: LONG}, "saw " + LONG)


@XFAIL
def test_x3_a_value_with_both_quote_marks_is_masked_where_repeated():
    assert "pa55" not in _second_message({PW_KEY: BOTH_QUOTES}, "saw " + BOTH_QUOTES)


@XFAIL
def test_x4_a_value_nested_under_a_credential_key_is_masked_where_repeated():
    assert "horse" not in _second_message({"credentials": {"note": P}}, f"saw {P}")


@pytest.mark.parametrize(
    "record",
    [
        pytest.param({"pin_token": 12345678}, marks=XFAIL, id="under a credential key"),
        pytest.param(
            {"name": "DB_" + PW_KEY.upper(), "value": 12345678}, marks=XFAIL, id="env entry value"
        ),
    ],
)
def test_x5_a_number_is_masked_where_repeated(record):
    assert "12345678" not in _second_message(record, "pin 12345678 used")


X6_COPIES = {
    "base64": b64(P),
    "capitals": P.upper(),
    "wrapped over two lines": "correct horse\nbattery staple",
    "double space": "correct  horse battery staple",
    "hex": P.encode().hex(),
}


@pytest.mark.parametrize(
    "copy", [pytest.param(c, marks=XFAIL, id=name) for name, c in X6_COPIES.items()]
)
def test_x6_a_respelled_copy_is_masked(copy):
    (_, second), _ = shown(
        {"kind": "Secret", "stringData": {"cfg": P}},
        {"annotations": {"last-applied-configuration": copy}},
    )
    assert second["annotations"]["last-applied-configuration"] != copy


@pytest.mark.parametrize(
    ("value", "line", "readable"),
    [
        pytest.param("q", "q alone", "q alone", marks=XFAIL, id="1 character"),
        pytest.param("a1", "a1 alone", "a1 alone", marks=XFAIL, id="2 characters"),
        pytest.param("ab1", "xab1y there", "ab1", marks=XFAIL, id="3 characters glued to a letter"),
    ],
)
def test_x7_a_very_short_value_is_masked_where_repeated(value, line, readable):
    assert readable not in _second_message({"pin_token": value}, line)


@XFAIL
def test_x8_the_copy_without_the_escape_sequence_is_masked():
    assert "hunter" not in _second_message({PW_KEY: ESC_VALUE}, "saw hunter2" + "secretXYZ")


# ---- guards -------------------------------------------------------------------------------------------------------------


def test_g1_a_one_word_value_is_one_placeholder():
    (out,), _ = shown({PW_KEY: ONE})
    assert runmap.PLACEHOLDER.fullmatch(out[PW_KEY]), out


def test_g2_a_message_is_not_a_credential():
    (out,), _ = shown({"message": P})
    assert out == {"message": P}


def test_g3_a_timestamp_stays_and_near_misses_are_masked():
    (out,), _ = shown({"token": "2026-11-11T10:00:00Z"})
    assert out == {"token": "2026-11-11T10:00:00Z"}
    for near in (
        "2026-11-11T10:00:00+00:00",
        "2026-11-11 10:00:00Z",
        "2026-11-11T10:00:00Zx",
        "2026-13-11T10:00:00Z",
    ):
        (out,), _ = shown({"token": near})
        assert shape_ok(out["token"]), (
            f"part of the value is readable: near miss {near!r} shown as {out!r}"
        )
        assert "10:00:00" not in out["token"], f"part of the value is readable: {out!r}"


def test_g4_a_value_nested_under_a_credential_key_registers_nothing():
    (first, second), counts = shown({"credentials": {"user": "svc"}}, {"message": "svc restarted"})
    assert first == {"credentials": {"user": R.MASKED}}
    assert not counts, counts
    assert second == {"message": "svc restarted"}


GATE_ROWS = [
    {PW_KEY + "_policy_enabled": "true"},
    {PW_KEY + "_policy_enabled": True},
    {"token_expiry": 3600},
    {"token_expiry": "30d"},
    {"secret_count": 3},
    {"token_expires": "2026-11-25T00:00:00Z"},
    {"name": "TOKEN_TTL", "value": "15m"},
]


@pytest.mark.parametrize("record", GATE_ROWS, ids=[json.dumps(r) for r in GATE_ROWS])
def test_g6_a_setting_about_a_credential_is_shown(record):
    (out,), _ = shown(record)
    assert out == record


def test_g6_no_setting_is_shown_under_a_credential_parent_or_in_a_secret():
    (out,), _ = shown({"credentials": {PW_KEY + "_policy_enabled": "true"}})
    assert out == {"credentials": {PW_KEY + "_policy_enabled": R.MASKED}}
    (out,), _ = shown({"kind": "Secret", "stringData": {"token_expiry": "30d"}})
    assert shape_ok(out["stringData"]["token_expiry"]), out
    (out,), _ = shown({"name": PW_KEY + "_policy_enabled", "value": {"mode": T}})
    assert T not in json.dumps(out), out


def test_g7_common_words_of_a_secret_stay_readable(tmp_path):
    raw, masked = _fixture(tmp_path)
    lines = " | ".join(r["message"] for r in _log_records(masked))
    gone = [w for w in ("orders", "info", "true", "5432", "prod", "postgres") if w not in lines]
    assert not gone, f"a common word was replaced: {gone} in {lines!r}"
    pairs = zip(_log_records(raw), _log_records(masked), strict=True)
    changed = [m["message"] for r, m in pairs if r != m and DB_PW not in r["message"]]
    assert not changed, (
        f"a common word was replaced: a log line without the secret changed: {changed}"
    )
    (_, second), _ = shown(
        {"kind": "Secret", "stringData": {"ENV": "Prod-1"}}, {"message": "deploy to Prod-1 done"}
    )
    assert second["message"] == "deploy to Prod-1 done", (
        f"a common word was replaced: a value under 8 characters: {second['message']!r}"
    )
    (_, second), _ = shown(
        {"kind": "Secret", "stringData": {"username": "orders-svc"}},
        {"message": "user orders-svc NAME denied"},
    )
    assert "orders-svc" not in second["message"], second
    assert re.search(r"user <SECRET_[0-9]+> NAME denied", second["message"]), second


def _calls(bundle):
    """The 24 tool calls of the fixture, built from what this bundle shows, in a fixed order."""
    services = list(dict.fromkeys(r["service"] for r in _log_records(bundle)))
    words = ("orders", "postgres", "prod", "5432", "info", "true", "retry")
    return (
        [("list_data", {})]
        + [("query_metrics", {"query": o["query"]}) for _, o in bundle.metrics]
        + [("query_logs", {"service": s}) for s in services]
        + [("query_logs", {"contains": w}) for w in words]
        + [("query_logs", {}), ("get_deploys", {})]
        + [("get_deploys", {"service": s}) for s in services]
        + [("get_k8s", {})]
        + [("get_k8s", {"kind": o["kind"], "name": o["name"]}) for _, o in bundle.k8s]
        + [("get_runbook", {"name": f}) for f, _ in bundle.runbooks]
        + [("get_runbook", {})]
    )


def _ids(result):
    if isinstance(result, list):
        return sorted(r["id"] for r in result if isinstance(r, dict) and "id" in r)
    return json.dumps(result, sort_keys=True)


def _strings_outside_the_secret(bundle):
    out: list[str] = []

    def walk(o):
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(k)
                walk(v)
        elif isinstance(o, list | tuple):
            for v in o:
                walk(v)

    for part in (bundle.alert, bundle.metrics, bundle.logs, bundle.deploys, bundle.runbooks):
        walk(part)
    walk(tuple(x for x in bundle.k8s if x[1].get("kind") != "Secret"))
    return out


@pytest.mark.parametrize("shape", ["spec.data", "spec.manifest"])
def test_g9_the_fixture_answers_the_same_tool_calls(tmp_path, shape):
    raw, masked = _fixture(tmp_path, shape)
    raw_calls, masked_calls = _calls(raw), _calls(masked)
    assert len(raw_calls) == len(masked_calls) == 24
    for (name, raw_in), (_, masked_in) in zip(raw_calls, masked_calls, strict=True):
        want = _ids(Snapshot(raw).call(name, raw_in))
        got = _ids(Snapshot(masked).call(name, masked_in))
        assert got == want, f"evidence IDs differ for {name} {masked_in}: {got} against {want}"
    for field in ("level", "service"):
        assert [r[field] for r in _log_records(masked)] == [r[field] for r in _log_records(raw)]
    before, after = _strings_outside_the_secret(raw), _strings_outside_the_secret(masked)
    changed = [(a, b) for a, b in zip(before, after, strict=True) if a != b]
    assert len(changed) == 1, f"strings outside the Secret that changed: {changed}"
    was, now = changed[0]
    assert was == "login as postgres with " + DB_PW + " refused", changed
    assert re.fullmatch(r"login as postgres with <SECRET_[0-9]+> refused", now), changed


def test_g10_a_large_secret_is_bounded(monkeypatch):
    entries = {f"k{i}": ("qx zj " * 34)[:200] + str(i) for i in range(2000)}
    seen = 0
    real = runmap.redact_untrusted

    def counting(text, mapping, *args, **kwargs):
        nonlocal seen
        seen += len(text)
        return real(text, mapping, *args, **kwargs)

    monkeypatch.setattr(runmap, "redact_untrusted", counting)
    (out,), _ = shown({"kind": "Secret", "stringData": entries})
    per_pass = seen / 2
    assert per_pass <= 2 * defaults.MAX_BUNDLE_CHARS, per_pass
    assert per_pass <= 2.2 * sum(len(v) for v in entries.values()), per_pass
    values = list(out["stringData"].values())
    assert all(shape_ok(v) for v in values)
    assert R.MAX_REGISTERED_ENTRIES == 256
    assert all(v != R.MASKED for v in values[:256]), "an entry below the cap got the fixed mask"
    assert all(v == R.MASKED for v in values[256:]), "an entry over the cap was registered"
