"""G12 (escalation E18 item G7-F4): prose punctuation that a SECRET value takes in at its end.

The key=value value class keeps a comma that begins no `key=` pair and reads `.`, `)`, `!`, `?`, `:`, `]`, `}` as value characters
(`authorization:` reads `;` too), so `password=hunter22, hunter22` stored `hunter22,` and the every-copy sweep of that value left the
clear copy `hunter22` readable. `_place` registers the value without its trailing punctuation as an entry of its own (as a piece).
The E18 probe as written replaced the 6th character (`4`, not `x`) by U+FF58: its "plain copy" is another value (pinned below).
G12b (result review round 1): ONE rule strips both ends of a value (`_bare`: characters that are not letters or digits, markup tags, escaped
`\\n` `\\r` `\\t`), for the core `_place` registers and for the words `_decide` exempts, and the core is registered for a wrapper too.
G12c (result review round 2): the core is not registered for a REAL placeholder's text (`EMAIL_1`, a label of `_LABELS`) or the cut-off start of one
that `full` opened with `<`; `ADMIN_1`, `DB_PASS_2`, `API`, `HOST` are values and keep their core. The look-alike guard is "an escaped look-alike TOKEN
`‹KIND_n›` is in the value, or `_bare` cut a `‹` / `›` off it", not any `‹` (an interior `‹` of a password keeps its core). `_bare` also reads `%0A`,
`\\u000a`, `\\x0a`, `&quot;`, `&#10;`, `<br/>` as edges. A value gets no core when that would push the run's map past half of MAX_MAP_CHARS (G12d; a PRIVKEY doubled would pass it). NUMBERING: one secret can hold two placeholders (`<SECRET_1>` for `hunter22,` and `<SECRET_2>` for `hunter22`); both restore
to their own original, the link between the two is not kept. A value takes at most ONE extra entry (its core), besides the `_PIECE` entries it already had.
G12d (result review of G12c): the core is declined for a label-shaped value only when the text is a mapping key or the number is within the label's counter;
the look-alike brackets no longer drop a core (only a value of tokens, or the cut body of a real label); the 4,096-character rule is a budget rule (the core
is skipped when the run's map would pass half of MAX_MAP_CHARS); the sweep leaves an escaped look-alike of a placeholder the run could have issued alone.
Every assertion message starts with its id (`G12-n `): the mutants of tests/g12_mutants.py expect it."""

from __future__ import annotations

import importlib
import sys

import pytest

from hadavin_sdk.guard import runmap, textnorm

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

PW = "hunter22"  # made up; not secret-shaped (no upper case), so no `_PIECE` entry hides the gap


@pytest.mark.parametrize("mark", [",", ".", ")", "!", "?", ":", "]", "}", ",,", "...,", "),"])
def test_g12_a_trailing_mark_does_not_leave_the_clear_copy(mark):
    r = R.redact(f"password={PW}{mark} {PW}")
    assert PW not in r.text, f"G12-1 {r.text}"
    assert r.mapping == {"<SECRET_1>": PW + mark, "<SECRET_2>": PW}, f"G12-2 {r.mapping}"


def test_g12_the_authorization_value_drops_a_semicolon_too():
    v = "hunter22hunter"
    r = R.redact(f"authorization: {v}; {v}")
    assert r.text == "authorization: <SECRET_1> <SECRET_2>", f"G12-3 {r.text}"


def test_g12_the_copy_in_another_string_of_the_call_is_swept():
    out, mapping = R.redact_many([f"password={PW},", f"later: {PW} again"])
    assert out == ["password=<SECRET_1>", "later: <SECRET_2> again"], f"G12-4 {out}"
    assert mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-4 {mapping}"


@pytest.mark.parametrize(
    "spelled",
    [
        PW[:2] + "ｎ" + PW[3:],  # full-width n
        PW[:6] + "２" + PW[7:],  # full-width 2
        PW[:2] + "ⓝ" + PW[3:],  # circled n
        PW[:2] + "\u200b" + PW[2:],  # zero-width space inside
        PW[:3] + "́" + PW[3:],  # combining acute
    ],
    ids=["fullwidth-letter", "fullwidth-digit", "circled", "zero-width", "combining"],
)
def test_g12_a_spelled_stored_original_sweeps_its_plain_copy(spelled):
    """The E18 shape built as intended: the stored value is a compatibility spelling of the clear copy."""
    text = f"password={spelled}, {PW}"
    assert PW not in R.redact(text).text, "G12-5 bare redact"
    m = runmap.RunMap()
    out = runmap.redact_text(text, m)
    assert PW not in textnorm.fold(out) and spelled not in out, f"G12-5 {out}"
    assert runmap.redact_text(out, m) == out, f"G12-6 {out}"


def test_g12_the_e18_probe_as_written_holds_a_different_value():
    value = "Zq9xW4mT7pLy"  # made up
    s6 = value[:5] + "ｘ" + value[6:]  # the 6th character is `4`: the fold is Zq9xWxmT7pLy
    assert textnorm.fold(s6) != value, "G12-7 the probe's fold"
    r = R.redact(f"password={s6}, {value}")
    # a value one character away is not a copy: unchanged by G12
    assert r.text == f"password=<SECRET_1> {value}", f"G12-7 {r.text}"


def test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma():
    control = R.redact("password=abc abc").text
    assert control == "password=<SECRET_1> <SECRET_1>", f"G12-8 control {control}"
    assert R.redact("password=abc, abc").text == "password=<SECRET_1> <SECRET_2>", "G12-8 abc"
    # under 3 characters: no core, as `_sweep` never sweeps such a value
    assert R.redact("password=ab, ab").mapping == {"<SECRET_1>": "ab,"}, "G12-8 ab"
    # 3 characters: standalone copies only, as for the control
    assert R.redact("password=abc, xabcx").text == "password=<SECRET_1> xabcx", "G12-8 glued"


def test_g12_a_core_the_map_holds_gets_no_second_placeholder():
    r = R.redact(f"password={PW} x\npassword={PW}, y")
    assert r.mapping == {"<SECRET_1>": PW, "<SECRET_2>": PW + ","}, f"G12-9 {r.mapping}"
    assert r.text == "password=<SECRET_1> x\npassword=<SECRET_2> y", f"G12-9 {r.text}"


def test_g12_a_rolled_back_value_takes_its_core_with_it():
    """A discarded in-place round (``_folded_line``) rolls back what it registered: the core goes with its value, so the number
    handed out again names one value only."""
    r = R._Redactor(None)
    counters = r._open_journal()
    r._place("SECRET", PW + ",", PW + ",")
    assert r.mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-10 {r.mapping}"
    r._rollback(counters)
    assert r.mapping == {} and r.reverse == {}, f"G12-10 {r.mapping} {r.reverse}"
    assert r._place("SECRET", "zz9other", "zz9other") == "<SECRET_1>", "G12-10 number"
    assert r.sweep(f"x {PW} y") == f"x {PW} y", "G12-10 a ghost entry sweeps the core"


def test_g12_identifier_kinds_are_unchanged():
    tenant = R.redact("user_id=acme01, then acme01").mapping
    assert tenant == {"<TENANT_1>": "acme01"}, f"G12-11 {tenant}"
    host = R.redact("host db01.corp.internal. next db01.corp.internal").mapping
    assert host == {"<HOSTNAME_1>": "db01.corp.internal"}, f"G12-11 {host}"
    # no identifier pattern takes trailing punctuation today; the rule is for the secret kinds only
    r = R._Redactor(None)
    r._place("TENANT", "acme01,", "acme01,")
    assert r.mapping == {"<TENANT_1>": "acme01,"}, f"G12-11 {r.mapping}"


def test_g12_a_g9_union_registers_its_value_only_and_no_core():
    """G9's unions (`derived=False`) register the value only: no written form, no pieces, and no G12 core."""
    r = R._Redactor(None)
    r._place("SECRET", PW + ",", PW + ",", derived=False)
    assert r.mapping == {"<SECRET_1>": PW + ","}, f"G12-12 {r.mapping}"


# --- G12b ---------------------------------------------------------------------------------------------------------------------

NOT_VALUES = [
    "none",
    "null",
    "true",
    "false",
    "set",
    "empty",
    "missing",
    "required",
    "invalid",
    "nil",
    "unset",
]


@pytest.mark.parametrize("word", NOT_VALUES)
@pytest.mark.parametrize("mark", ["!", "?", "}", ".", ",", "`", "**", "]"])
def test_g12_a_word_that_says_there_is_no_value_gets_no_core(word, mark):
    """M-1: `password=none!` is masked whole as before, but its core `none` is not registered: it swept every `none` of the text."""
    stored = f"{word}{mark}"
    r = R.redact(f"password={stored} {word} un{word}")
    assert word in r.text.split() and f"un{word}" in r.text, f"G12-13 {r.text}"
    assert set(r.mapping.values()) <= {stored}, f"G12-13 {r.mapping}"


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("password=password!", "password=<SECRET_1>"),
        (
            "password=password=",
            "<SECRET_1><SECRET_1>",
        ),  # the whole `password=` is the value (the k5 perf shape)
        ("password=none!", "password=<SECRET_1>"),
        ("password=true-", "password=<SECRET_1>"),
        ("password=null_", "password=<SECRET_1>"),
        ("password=*none*", "password=<SECRET_1>"),
    ],
)
def test_g12_what_the_exemption_never_took_is_still_masked_whole(text, masked):
    """The exemption keeps its old strip set: a value masked before G12b is masked now (no leak by widening)."""
    r = R.redact(text)
    assert r.text == masked, f"G12-13 {text} -> {r.text}"


def test_g12_what_the_exemption_took_it_still_takes():
    assert R.redact("password=(null),").text == "password=(null),", "G12-13 old exemption"


def test_g12_the_second_none_is_neither_masked_nor_swept():
    r = R.redact("password=none! none")
    assert r.text == "password=<SECRET_1> none" and r.mapping == {"<SECRET_1>": "none!"}, (
        f"G12-13 {r.text} {r.mapping}"
    )
    r = R.redact("password=*none*, none untrue")
    assert r.text == "password=<SECRET_1> none untrue", f"G12-13 {r.text}"
    # a value that is not one of those words keeps its core
    r = R.redact("password=none1! none1")
    assert r.text == "password=<SECRET_1> <SECRET_2>", f"G12-13 {r.text}"


WRAPPED = [
    ("`password=hunter22` hunter22", "`password=<SECRET_1> <SECRET_2>"),
    ("**password=hunter22** hunter22", "**password=<SECRET_1> <SECRET_2>"),
    ("<b>password=hunter22</b> hunter22", "<b>password=<SECRET_1> <SECRET_2>"),
    ("password=<b>hunter22</b> hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("~password=hunter22~ hunter22", "~password=<SECRET_1> <SECRET_2>"),
    ("|password=hunter22| hunter22", "|password=<SECRET_1> <SECRET_2>"),
    ("password=hunter22… hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=hunter22。 hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=hunter22） hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=「hunter22」 hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=hunter22\\n hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=\\thunter22 hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=(hunter22), hunter22", "password=<SECRET_1> <SECRET_2>"),  # L-G12a, closed
    ("password=[hunter22]. hunter22", "password=<SECRET_1> <SECRET_2>"),
    ("password=--hunter22-- hunter22", "password=<SECRET_1> <SECRET_2>"),
]


@pytest.mark.parametrize(("text", "masked"), WRAPPED, ids=[str(i) for i in range(len(WRAPPED))])
def test_g12_a_wrapper_at_either_end_does_not_leave_the_clear_copy(text, masked):
    r = R.redact(text)
    assert PW not in r.text, f"G12-14 {r.text}"
    assert r.text == masked, f"G12-14 {r.text}"
    assert PW in r.mapping.values() and len(r.mapping) == 2, f"G12-14 {r.mapping}"


def test_g12_a_wrapper_around_a_three_character_core_is_swept_standalone_only():
    r = R.redact("password=*abc*, xabcx abc")
    assert r.text == "password=<SECRET_1> xabcx <SECRET_2>", f"G12-14 {r.text}"


def test_g12_a_value_takes_one_extra_entry_besides_its_own():
    """N-1: the core is one extra entry per value; the budget (E14, MAX_MAP_ENTRIES) sees at most one more entry per value."""
    values = [f"zq{n:04d}x" for n in range(40)]
    text = "\n".join(f"password={v}, x" for v in values)
    assert len(R.redact(text).mapping) == 2 * len(values), "G12-15 trailing"
    wrapped = "\n".join(f"password=(`{v}`), x" for v in values)
    assert len(R.redact(wrapped).mapping) == 2 * len(values), "G12-15 wrapped"
    plain = "\n".join(f"password={v}" for v in values)
    assert len(R.redact(plain).mapping) == len(values), "G12-15 control"
    for text in (f"password={PW},, {PW}", f"password=({PW}), {PW}", f"password=<b>{PW}</b> {PW}"):
        assert len(R.redact(text).mapping) <= 2, f"G12-15 {text}"


def test_g12_the_core_of_a_value_holding_a_placeholder_is_cut_from_the_resolved_value():
    """The stored value is the resolved one (`full`), so is its core: a placeholder is never inside a registered value."""
    text = "password=zq9xk\npassword=<SECRET_1>-hunter22, zq9xk-hunter22"
    r = R.redact(text)
    assert r.mapping == {
        "<SECRET_1>": "zq9xk",
        "<SECRET_2>": "zq9xk-hunter22,",
        "<SECRET_3>": "zq9xk-hunter22",
    }, f"G12-16 {r.mapping}"
    assert r.text == "password=<SECRET_1>\npassword=<SECRET_2> <SECRET_3>", f"G12-16 {r.text}"


@pytest.mark.parametrize("value", ["....", "a.", "!!", "...,", "ab.", "..a.."])
def test_g12_an_all_punctuation_or_short_value_gets_no_core(value):
    r = R.redact(f"password={value} {value}")
    assert set(r.mapping.values()) <= {value}, (
        f"G12-17 {r.mapping}"
    )  # the value itself, never a core


def test_g12_a_core_of_exactly_three_characters_is_swept_standalone_only():
    for wrap in ("{0},", "({0})", "*{0}*", "{0}..."):
        stored = wrap.format("abc")
        r = R.redact(f"password={stored} xabcx abc")
        assert r.text == "password=<SECRET_1> xabcx <SECRET_2>", f"G12-17 {stored} {r.text}"
    # two characters: no core
    assert R.redact("password=(ab), ab").text == "password=<SECRET_1> ab", "G12-17 ab"


def test_g12_the_edge_rule_is_linear_on_a_long_run_of_tags():
    big = "<a>" * 60_000 + "x" + "</b>" * 60_000
    assert R._bare(big) == "x"
    assert R._bare("<b>" * 50_000) == ""


@pytest.mark.parametrize("value", ["\u2039EMAIL_1\u203a", "<EMA", "<EMAIL_", "<IPV4_12>", "(<EMA)"])
def test_g12_a_core_that_is_a_placeholders_own_text_is_not_registered(value):
    """A value spelled like a placeholder: its core (`EMAIL_1`, `EMA`) swept from every copy would eat the real placeholders."""
    r = R.redact(f"password={value} host")
    assert set(r.mapping.values()) <= {value}, f"G12-18 {r.mapping}"


# --- G12c ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "core"),
    [
        ("password=ADMIN_1, ADMIN_1", "ADMIN_1"),
        ("password=DB_PASS_2! x DB_PASS_2", "DB_PASS_2"),
        ("password=HOST, HOST", "HOST"),
        ("password=SEC, SEC", "SEC"),
        ("password=JWT, JWT", "JWT"),
    ],
)
def test_g12_an_all_caps_name_with_a_number_or_a_label_prefix_is_a_value_and_keeps_its_core(
    text, core
):
    """M2: only a real placeholder's text is declined; `ADMIN_1`, `DB_PASS_2`, `SEC`, `JWT`, `HOST` are values: the plain copy is swept."""
    r = R.redact(text)
    assert core in r.mapping.values(), f"G12-19 {r.mapping}"
    assert core not in R._PLACEHOLDER.sub("", r.text), f"G12-19 {r.text}"


def test_g12_a_core_in_the_common_words_is_registered_but_swept_as_its_control_is():
    """`api` is in `_COMMON`: a 3-character standalone copy is never swept (the same for `password=API API`): the core is registered all the same."""
    assert "API" in R.redact("password=API! API").mapping.values(), "G12-19 API"
    assert R.redact("password=API API").text == "password=<SECRET_1> API", "G12-19 control"


def test_g12_a_value_that_is_a_placeholders_text_keeps_the_real_placeholders_intact():
    """`password=EMAIL_1,` has no core (a real label); the real `<EMAIL_1>` is untouched and no junk placeholder is made. STATED LIMIT: its plain
    copy `EMAIL_1` stays as typed (a registered core would be swept out of an escaped look-alike, E9)."""
    r = R.redact("password=EMAIL_1, EMAIL_1 and a@example.com")
    assert r.mapping.get("<SECRET_1>") == "EMAIL_1,", f"G12-20 {r.mapping}"
    assert "EMAIL_1" not in r.mapping.values(), f"G12-20 {r.mapping}"
    assert "<EMAIL_1>" in r.text and r.text.startswith("password=<SECRET_1> "), f"G12-20 {r.text}"
    assert R.redact(r.text).text == r.text, "G12-20 not idempotent"


def test_g12_an_interior_lookalike_bracket_keeps_the_core_of_the_value():
    """M3: `hun‹ter22,` is a real password with a `‹` inside: its core is registered and the clear copy is swept."""
    v = "hun\u2039ter22"
    r = R.redact(f"password={v}, {v}")
    assert r.mapping == {"<SECRET_1>": v + ",", "<SECRET_2>": v}, f"G12-21 {r.mapping}"
    assert r.text == "password=<SECRET_1> <SECRET_2>", f"G12-21 {r.text}"


@pytest.mark.parametrize(
    "value",
    [
        "\u2039SECRET_1\u203a<UUID_3>\u2039IPV4_1\u203a",  # the E9 own-output shape
        "\u2039SECRET_x\u203a",  # not a token, but `_bare` cut the brackets off the body of a real label
        "\u2039SECRET_x",  # a cut-off look-alike body
        "\u2039SECRET_1\u203ahunter22",  # a token, then a secret: `_bare` cut the `‹` off a token body
        "hunter22\u2039SECRET_1\u203a",  # the same at the end
    ],
)
def test_g12_a_value_of_tokens_or_the_cut_body_of_a_real_label_gets_no_core(value):
    r = R.redact(f"password={value}")
    assert set(r.mapping.values()) == {value}, f"G12-22 {r.mapping}"


@pytest.mark.parametrize(
    ("text", "core"),
    [
        ("password=\u2039HUNTER2, HUNTER2", "HUNTER2"),  # one leading bracket, an all-caps core
        ("password=\u2039hunter2zz\u203a hunter2zz", "hunter2zz"),  # both brackets cut
        ("password=12\u2039EMAIL_1\u203a34, 12\u2039EMAIL_1\u203a34", "12\u2039EMAIL_1\u203a34"),
        ("password=hunter2\u2039X_1\u203a, hunter2\u2039X_1\u203a", "hunter2\u2039X_1\u203a"),
    ],
)
def test_g12_a_lookalike_bracket_at_an_edge_or_inside_still_gets_a_core(text, core):
    """G12d: the look-alike brackets are no reason to leave the plain copy readable (a core is declined only for a real label's token)."""
    r = R.redact(text)
    assert core in r.mapping.values(), f"G12-29 {r.mapping}"
    assert core not in R._PLACEHOLDER.sub("", r.text), f"G12-29 {r.text}"


def test_g12_a_core_that_is_the_tail_of_a_real_label_never_corrupts_an_escaped_lookalike():
    """`MAIL_1` is a value here; the sweep leaves `\u2039EMAIL_1\u203a` alone (no `\u2039E<SECRET_3>\u203a`)."""
    r = R.redact("password=MAIL_1, MAIL_1 and \u2039EMAIL_1\u203a and \u2039AIL_1\u203a")
    assert r.text.count("\u2039EMAIL_1\u203a") == 1, f"G12-30 {r.text}"
    assert "MAIL_1" not in R._PLACEHOLDER.sub("", r.text.replace("\u2039EMAIL_1\u203a", "")), (
        f"G12-30 {r.text}"
    )


@pytest.mark.parametrize(
    "text", ["password=TOKEN_2024. TOKEN_2024", "password=SECRET_123, SECRET_123"]
)
def test_g12_a_label_shaped_value_beyond_the_counter_keeps_its_core(text):
    """M1: `TOKEN_2024` is no placeholder this run issued (the counter is far below 2024): a value, its bare copy is swept."""
    r = R.redact(text)
    assert text.split()[1].rstrip(".,") not in R._PLACEHOLDER.sub("", r.text), f"G12-31 {r.text}"
    assert R.redact(r.text).text == r.text, "G12-31 not idempotent"


def test_g12_a_value_of_tokens_alone_gets_no_core():
    from types import SimpleNamespace

    run = SimpleNamespace(mapping={}, counters={})
    assert R._core_is_declined("UUID_3> <IPV4_1", "<UUID_3> <IPV4_1>", 1, 16, run), "G12-35 tokens"
    assert not R._core_is_declined("hunter22", "<UUID_3> hunter22,", 9, 17, run), "G12-35 control"


def test_g12_a_lookalike_that_is_the_value_itself_is_swept():
    """`\u2039TOKEN_2024\u203a` is the escaped spelling of a typed `<TOKEN_2024>`: no placeholder of this run, and the value inside it is swept."""
    r = R.redact("password=SECRET_123. and \u2039SECRET_123\u203a")
    assert "SECRET_123" not in R._PLACEHOLDER.sub("", r.text), f"G12-31 {r.text}"


@pytest.mark.parametrize(
    "edge",
    [
        "<br/>",
        "<br />",
        "<a/>",
        "%0A",
        "%22",
        "\\u000a",
        "\\u0022",
        "\\x0a",
        "&quot;",
        "&nbsp;",
        "&#10;",
    ],
)
def test_g12_an_escaped_or_encoded_edge_does_not_leave_the_clear_copy(edge):
    """M4: a line end or a quote in transit at the end of the value."""
    r = R.redact(f"password={PW}{edge} {PW}")
    assert PW in r.mapping.values(), f"G12-23 {r.mapping}"
    assert r.text.endswith("<SECRET_2>") and PW not in r.text, f"G12-23 {r.text}"


@pytest.mark.parametrize("edge", ["%0A", "\\u000a", "\\x0a", "<br/>", "&#10;"])
def test_g12_an_escaped_or_encoded_edge_at_the_start_does_not_leave_the_clear_copy(edge):
    r = R.redact(f"password={edge}{PW} {PW}")
    assert PW in r.mapping.values() and PW not in r.text, f"G12-24 {r.text} {r.mapping}"


def test_g12_the_edge_rule_is_linear_on_every_new_form():
    for unit in ("%0A", "\\u000a", "&amp;", "<br/>"):
        big = unit * 80_000 + "x" + unit * 80_000
        assert R._bare(big) == "x", f"G12-25 {unit}"
    for unit in ("<br", "&quot"):  # cut-short forms count at the end only
        assert R._bare("x" + unit * 80_000) == "x", f"G12-25 {unit}"


def test_g12_a_large_value_gets_a_core_unless_it_would_push_the_map_past_half_its_cap():
    """A PRIVKEY (the dashes are the whole difference) near the cap gets no core: a copy would double its characters in the map; the run is not refused."""
    key = "-----BEGIN PRIVATE KEY-----\n" + "Qw9z" * 65_520 + "\n-----END PRIVATE KEY-----"
    assert len(key) == 262_138 + 6 or abs(len(key) - 262_144) < 16
    r = R.redact(key)
    assert not any(len(key) - 16 < len(v) < len(key) for v in r.mapping.values()), (
        f"G12-26 {[len(v) for v in r.mapping.values()]}"
    )
    key2 = "-----BEGIN PRIVATE KEY-----\n" + "Qw9z" * 1500 + "\n-----END PRIVATE KEY-----"
    assert any(len(key2) - 16 < len(v) < len(key2) for v in R.redact(key2).mapping.values()), (
        "G12-26 a small key keeps its core"
    )
    big = "qwxz" * 2000  # no digit: no `_PIECE` entry of its own
    assert set(R.redact(f"password={big},").mapping.values()) == {big + ",", big}, (
        "G12-26 big value core registered"
    )
    assert big not in R.redact(f"password={big}, {big}").text, "G12-26 the bare copy is swept"
    five = "kq" * 2500
    assert R.redact(f"password={five}, {five}").text == "password=<SECRET_1> <SECRET_2>", (
        "G12-26 5000"
    )
    small = "qwxz" * 20
    assert small in R.redact(f"password={small},").mapping.values(), (
        "G12-26 small value keeps its core"
    )


def test_g12_the_end_of_value_unlisted_tag_is_stripped_by_the_whole_form():
    """`PW<em/>` at the END: `<em` is no cut-short form, so only the whole-form branch strips it (G12d)."""
    r = R.redact(f"password={PW}<em/> {PW}")
    assert PW in r.mapping.values() and PW not in r.text, f"G12-32 {r.text} {r.mapping}"
    assert R._bare(f"{PW}<em/>") == PW, "G12-32"


def test_g12_a_run_of_non_edge_characters_does_not_search_for_a_close_form():
    """Timing-insensitive: the close search is not tried for a last character that cannot end a form (`!`, `-`)."""

    class Counting:
        calls = 0

        def search(self, *a):
            Counting.calls += 1
            return R._EDGE_CLOSE_REAL.search(*a)

    R._EDGE_CLOSE_REAL = R._EDGE_CLOSE
    try:
        R._EDGE_CLOSE = Counting()
        for ch in "!-":
            Counting.calls = 0
            assert R._bare(ch * 500_000) == "", f"G12-33 {ch}"
            assert Counting.calls == 0, f"G12-33 {ch} {Counting.calls}"
        assert R._bare("a" + "!" * 5000 + "b") == "a" + "!" * 5000 + "b"
    finally:
        R._EDGE_CLOSE = R._EDGE_CLOSE_REAL
        del R._EDGE_CLOSE_REAL
    r = R.redact("password=" + "!" * 500_000)
    assert "!!!!" not in r.text, "G12-33"


def test_g12_the_open_bracket_is_a_cut_off_form_only_right_before_the_core():
    """`<EMA` as the core of a value that holds `<` elsewhere is a value: only a `<` directly before the core declines it."""
    from types import SimpleNamespace

    run = SimpleNamespace(mapping={}, counters={})
    assert R._core_is_declined("EMA", "<EMA!", 1, 4, run), "G12-34 right before"
    assert not R._core_is_declined("EMA", "<x EMA!<", 3, 6, run), "G12-34 a `<` elsewhere"
    assert R.redact("password=<EMA, EMA").text == "password=<SECRET_1> EMA", "G12-34 whole"


def test_g12_a_value_that_merely_holds_a_tag_like_word_keeps_it():
    """The cut-short forms (`<br`, `&quot`) are a closed list: `<bx` or `&qux` at the end are part of the value."""
    assert R._bare("abc<bx") == "abc<bx" and R._bare("abc&qux") == "abc&qux", "G12-27"
    assert R._bare("hunter22<br") == "hunter22" and R._bare("hunter22&quot") == "hunter22", "G12-27"


@pytest.mark.parametrize(
    "value",
    ["hunter22!\u203a", "\u2039hunter22,", "hunter22,\u203a", "\u203ahunter22,", "hunter22\u2039,"],
)
def test_g12_one_stray_lookalike_bracket_keeps_the_core(value):
    """A single `‹` or `›` is not an escaped look-alike: the core is registered and the plain copy is swept (E9 review round 3)."""
    r = R.redact(f"password={value} hunter22")
    assert "hunter22" in r.mapping.values(), f"G12-28 {r.mapping}"
    assert "hunter22" not in R._PLACEHOLDER.sub("", r.text), f"G12-28 {r.text}"
