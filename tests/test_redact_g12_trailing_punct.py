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
`\\u000a`, `\\x0a`, `&quot;`, `&#10;`, `<br/>` as edges. A value over 4,096 characters whose core differs by 16 or fewer gets no core (a PRIVKEY doubled
would pass MAX_MAP_CHARS). NUMBERING: one secret can hold two placeholders (`<SECRET_1>` for `hunter22,` and `<SECRET_2>` for `hunter22`); both restore
to their own original, the link between the two is not kept. A value takes at most ONE extra entry (its core), besides the `_PIECE` entries it already had.
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


def test_g12_a_value_takes_at_most_two_entries():
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
        "12\u2039EMAIL_1\u203a34,",  # a look-alike token inside, one edge cut (no secret-shaped piece)
        "\u2039SECRET_x\u203a",  # not a token, but `_bare` cut the brackets
        "\u2039hunter2zz\u203a",  # wrapped in the brackets: both cut
        "\u2039SECRET_x",  # a cut-off look-alike body
    ],
)
def test_g12_a_value_with_a_lookalike_token_or_its_cut_brackets_gets_no_core(value):
    r = R.redact(f"password={value}")
    assert set(r.mapping.values()) == {value}, f"G12-22 {r.mapping}"


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


def test_g12_a_large_value_whose_core_differs_by_a_few_characters_gets_no_core():
    """A PRIVKEY (the dashes are the whole difference) or any value over 4,096 characters: a copy would double its characters in the map."""
    key = "-----BEGIN PRIVATE KEY-----\n" + "Qw9z" * 1500 + "\n-----END PRIVATE KEY-----"
    r = R.redact(key)
    assert not any(len(key) - 16 < len(v) < len(key) for v in r.mapping.values()), (
        f"G12-26 {[len(v) for v in r.mapping.values()]}"
    )
    big = "qwxz" * 2000  # no digit: no `_PIECE` entry of its own
    assert set(R.redact(f"password={big},").mapping.values()) == {big + ","}, (
        "G12-26 big value core registered"
    )
    assert set(R.redact(f"password=<b>{big}</b>").mapping.values()) == {f"<b>{big}</b>"}, (
        "G12-26 big wrapped"
    )
    small = "qwxz" * 20
    assert small in R.redact(f"password={small},").mapping.values(), (
        "G12-26 small value keeps its core"
    )


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
