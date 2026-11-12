"""PR H batch 10: the rows of the round-9 review (groups 1 to 6). Every credential-shaped value is built from parts; the only literal is
the allowed example key. Each test names the group it guards and, where one exists, the mutant (tests/prh_mutants.py) that reverts the
guard; the failing message of a killer names the planted fault. Cost tests count WORK (calls, characters read), never seconds."""

import importlib
import sys

import pytest

from hadavin_sdk import defaults, tools
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import (
    WITHHELD_NOTE,
    SpacedRunLimit,
    redact,
    redact_many,
    spaced_unknown,
)

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")

ESC = "\x1b"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
MARKER = tools.MARKER
WITHHELD = tools.MARKER + tools.TRUNCATED
BSL = chr(92)
CJK = "一二三四五六七八"  # eight different characters that no pattern reads, even as one long token


def spaced(value: str) -> str:
    return " ".join(value)


def on_the_run_path(text: str) -> str:
    return runmap.redact_untrusted(text, {})


def stands(out: str, value: str, size: int = 8) -> bool:
    return any(value[i : i + size] in out for i in range(len(value) - size + 1))


def _count_calls(fn):
    """Number of Python and C calls `fn()` makes (sys.setprofile): work, not seconds."""
    n = 0

    def prof(frame, event, arg):
        nonlocal n
        if event in ("call", "c_call"):
            n += 1

    sys.setprofile(prof)
    try:
        result = fn()
    finally:
        sys.setprofile(None)
    return n, result


# ---- group 1: the cost of the spaced-run code is bounded and counted ---------------------------------------------------------


def test_b10_g1_values_that_share_their_first_twelve_characters_cost_linear_work():
    """Group 1 (class: new work neither counted nor measured; mutants 133, 134). 1,000 known values share their first 12 characters
    and the text holds 4,000 copies of that prefix with a gap: the batch 9 index scanned the whole bucket for each hit (about 4
    million `startswith` calls). One pass of the automaton makes work in proportion to the text. The three values written with
    spaces are found."""
    prefix = "Zq4nWs8kLpv3"
    values = [prefix + f"{i:04d}" + "Xy" for i in range(1000)]
    index = redact_mod.spaced_index(values)
    copies = " ".join(prefix + "!" for _ in range(4000))
    wanted = [values[7], values[500], values[999]]
    text = copies + " " + " ".join(spaced(v) for v in wanted)
    compact_len = len(text.replace(" ", ""))
    calls, found = _count_calls(lambda: redact_mod.spaced_spans(text, (), index=index))
    assert calls < 12 * compact_len, (
        f"mutant 133: the index search made {calls} calls for a text of {compact_len} characters (a bucket scan per hit)"
    )
    assert sorted(v for _, _, v in found) == sorted(wanted), found


def test_b10_g1_the_automaton_finds_every_value_that_the_old_search_found():
    """Group 1 (mutants 133, 134, 135): a value that ends inside another value (a suffix) and values that overlap are all found; at each end the
    longest is returned (the shorter one lies inside it and `mask_spans` drops it). Seeded texts, compared by what the masking
    makes of them."""
    from hadavin_sdk.guard.redact import mask_spans
    from tests.seeded import rng

    def reference(text, values):
        pos = [i for i, c in enumerate(text) if c != " "]
        compact = "".join(text[i] for i in pos)
        found = []
        for v in values:
            j = compact.find(v)
            while j >= 0:
                a, b = pos[j], pos[j + len(v) - 1] + 1
                if b - a > len(v):
                    found.append((a, b, v))
                j = compact.find(v, j + 1)
        return found

    r = rng(1010)
    alphabet = "abAB-"
    for n in range(300):
        values = []
        for _ in range(r.randint(2, 6)):
            v = "".join(r.choice(alphabet) for _ in range(r.randint(12, 18)))
            values += [v, v[r.randint(1, 4) :]] if r.random() < 0.5 else [v]
        values = [v for v in values if len(v) >= defaults.SPACED_VALUE_MIN_CHARS]
        text = ""
        for _ in range(r.randint(1, 5)):
            v = r.choice(values)
            if (
                r.random() < 0.4
            ):  # the front of a value only: the walk ends inside a longer value while a shorter one ends here
                v = v[: len(v) - r.randint(1, 5)]
            text += (
                r.choice(["", " "])
                + (" ".join(v) if r.random() < 0.7 else v)
                + r.choice(["", " ", "x"])
            )
        ph = {v: f"<S_{i}>" for i, v in enumerate(values)}
        got = redact_mod.spaced_spans(text, values)
        want = reference(text, [v for v in values])
        mg = mask_spans(text, [(a, b, ph[v]) for a, b, v in got], {})
        mw = mask_spans(text, [(a, b, ph[v]) for a, b, v in want], {})
        assert mg == mw, (n, text, values, "mutants 133 to 135: the automaton lost a copy")


def test_b10_g1_one_very_long_spaced_run_is_withheld_by_the_work_budget():
    """Group 1 (mutant 136): a run of 60,000 single characters of 8 different ones would be read up to 4 times (240,000
    characters against a budget of `SPACED_READ_MAX_CHARS`); the budget is counted BEFORE each read and the text is withheld."""
    text = spaced(CJK * 7500)
    with pytest.raises(SpacedRunLimit):
        spaced_unknown(text)
    assert tools.prepare_output(text, {}, 4000, []) == WITHHELD, (
        "mutant 136: a run over the budget was read"
    )


def test_b10_g1_a_value_that_is_a_suffix_of_the_prefix_the_walk_ends_in_is_found():
    """Group 1 (mutants 133, 135): the walk ends inside the longer value `abcdefghijklmnop` while the shorter `bcdefghijklm` (a suffix of
    what was read) ends at the same place; the suffix link is what finds it."""
    short, long_ = "bcdefghijklm", "abcdefghijklmnop"
    text = "x " + " ".join("abcdefghijklm") + " y"
    got = redact_mod.spaced_spans(text, [long_, short])
    assert [v for _, _, v in got] == [short], (
        f"mutants 133 and 135: the value ending inside a longer one was not found: {got!r}"
    )


def test_b10_g1_a_run_under_the_budget_is_still_read():
    """Group 1 (mutant 158, the other side): the budget does not stop an ordinary spaced key or a run of 20,000 characters."""
    assert spaced_unknown(spaced(KEY))[0][2] == KEY
    assert spaced_unknown(spaced(CJK * 2500)) == []


def test_b10_g1_the_budget_counts_the_context_read_too():
    """Group 1 (mutant 137): with 64 characters of context before the run a read scans the context twice and the token once more, so
    the cost of a run with context is above the cost of the same run without it. The text below stays within the budget without
    context and goes over it with context."""
    n = (
        defaults.SPACED_READ_MAX_CHARS // defaults.SPACED_DROP_MAX
    ) - 100  # tokens: 4 reads of n characters fit, barely
    body = spaced(CJK * (n // 8))
    assert spaced_unknown(body) == []
    with pytest.raises(SpacedRunLimit):
        spaced_unknown("x" * 70 + " = " + body)


# ---- group 4: the final guard runs against what the sweep leaves ----------------------------------------------------------------
PW = "pass" + "word="
VAL = "hun" + "ter2" + "Qx9"


def test_b10_g4_a_second_bare_copy_of_a_masked_secret_does_not_withhold_the_text():
    """Group 4 (mutant 138): colour code, `password=` + value, and the same value standing bare in prose. The sweep masks the bare
    copy; the batch 9 guard looked at the text before the sweep and withheld it (main masked both)."""
    text = ESC + "[0m " + PW + VAL + " ok login " + VAL + " failed"
    for out in (redact(text).text, redact_many([text])[0][0]):
        assert out != WITHHELD_NOTE, "mutant 138: ordinary coloured text was withheld by the guard"
        assert VAL not in out and out.count("<SECRET_1>") == 2, out


def test_b10_g4_a_copy_the_sweep_cannot_mask_still_withholds():
    """Group 4 (mutant 139, the other side): `ESC ( B` + `1.2.3.4` next to `1.2` + `ESC .` + `3.4`: the sweep does not mask the copy the
    reading could not see, so the guard still withholds (the batch 9 rule, unchanged)."""
    a, b = "10.20", "30.40"
    text = ESC + "(B" + a + "." + b + " and " + a + ESC + "." + b
    out = redact(text).text
    assert a + "." + b not in out, f"mutant 139: a copy of an address stood readable: {out!r}"


# ---- group 5: a wrapper next to the first or last character, and a front with more than one copy -------------------------------
WRAPPERS = [
    ("`", "`"),
    ("*", "*"),
    ("**", "**"),
    ("_", "_"),
    ("~~", "~~"),
    ("<", ">"),
    ("{", "}"),
    ("|", "|"),
    ("`", ""),
    ("", "}"),
    ("", ">"),
    ("", "*"),
]


@pytest.mark.parametrize(
    ("front", "back"), WRAPPERS, ids=[f"{a}{b}" or "none" for a, b in WRAPPERS]
)
def test_b10_g5_a_wrapper_glued_to_a_spaced_key_is_not_part_of_the_value(front, back):
    """Group 5 (mutant 140; class: a spaced secret slips past a rule because of a character next to it). A model quotes a key in a code
    span, bold, italic, strike, angle brackets, braces or pipes; the wrapper makes the first or last token two characters long, so the
    key lost its first or last letter. Exact output on the run path; no 8-stretch on the tool path."""
    text = "key: " + front + spaced(KEY) + back + " end"
    # an underscore is a word character: the view that reads the value has a space next to it, and the output keeps that space
    pad = " " if front.startswith("_") or back.startswith("_") else ""
    want = "key: " + front + pad + "<APIKEY_1>" + pad + back + " end"
    assert on_the_run_path(text) == want, (
        f"mutant 140: a spaced key wrapped in {front!r} {back!r} was not masked whole"
    )
    assert not stands(tools.prepare_output(text, {}, 4000, []), KEY, 6)


def test_b10_g5_the_wrapper_list_is_the_one_in_the_code():
    """Group 5: the allowlist of wrapper characters is one constant, used by both ends of the run rule."""
    assert set(redact_mod._WRAPPERS) == set("`*_~<>{}|")


@pytest.mark.parametrize("opener", ["\x90", "\x9d", ESC + "]0;"], ids=["dcs", "osc_c1", "osc_esc"])
def test_b10_g5_a_front_before_the_opener_withholds_when_the_value_is_masked_in_another_copy(
    opener,
):
    """Group 5 (mutant 141): a plain copy of a key, then a copy cut by a string opener (`AKIAIO` + opener + the rest). The first copy made
    the difference of the two readings empty, so the front standing before the opener was kept, one copy or two."""
    text = "k: " + KEY + " then " + KEY[:6] + opener + KEY[6:] + " tail"
    out = redact(text).text
    assert out == WITHHELD_NOTE, f"mutant 141: the front of a key stood before the opener: {out!r}"


def test_b10_g5_a_pattern_shaped_value_with_an_encoded_gap_is_masked():
    """Group 5 (mutant 147; class: a gap spelled another way). `A%20K%20I%20A...` and `A&#32;K&#32;...`: the decoded view holds a run of
    single characters; the reader of unknown spaced values ran on the text as written only, so the key stood readable in every
    letter."""
    for gap in ("%20", "&#32;", "%09"):
        out = on_the_run_path("key: " + gap.join(KEY))
        assert out == "key: <APIKEY_1>", (
            f"mutant 147: a key with the gap {gap!r} was not masked: {out!r}"
        )


def test_b10_g5_an_unknown_value_of_no_pattern_shape_with_an_encoded_gap_is_not_read_and_the_statement_is_pinned():
    """Group 5: like the plain-space case (`test_prh_b9`, the no-pattern-shape pin), a value that no pattern reads is not masked
    when its gap is encoded either (owner question `q-prh-spaced-secrets` covers both)."""
    unknown = "Qx7mLp9vRtzKw2Ab"
    text = "note: " + "%20".join(unknown)
    assert on_the_run_path(text) == text


# ---- group 6: smaller items --------------------------------------------------------------------------------------------------


def test_b10_g6_backslash_e_is_read_only_before_a_bracket_or_a_parenthesis():
    """Group 6 (mutants 129, 142, 148): a Windows path such as `C:\\env` and prose keep their `\\e` and do not take the heavier scrub
    path; `\\e[0m` and `\\e(B` are still read as ESC."""
    path = "C:" + BSL + "env" + BSL + "etc"
    assert runmap.hex_unescape(path) == path, "mutant 142: a Windows path was read as an ESC"
    assert runmap.hex_unescape(BSL + "e[0m") == ESC + "[0m", (
        "mutant 129: backslash-e before a bracket was not read"
    )
    assert runmap.hex_unescape(BSL + "e(B") == ESC + "(B", (
        "mutant 129: backslash-e before a parenthesis was not read"
    )
    assert tools._HIDDENISH.search("C:" + BSL + "env") is None, (
        "mutant 148: C:\\env takes the heavier scrub path"
    )
    assert tools._HIDDENISH.search("x" + BSL + "e[0m") is not None, (
        "mutant 148b: backslash-e before a bracket is not hidden-ish"
    )


@pytest.mark.parametrize("exc", [runmap.RedactionError("x"), runmap.InputTooLarge("InputTooLarge")])
def test_b10_g6_any_refusal_of_the_redactor_gives_the_withheld_text_on_the_tool_path(
    exc, monkeypatch
):
    """Group 6 (mutant 143): a plain `RedactionError` or `InputTooLarge` from `redact_untrusted` was not caught by `redact_layered`
    (only `TooDeep` and `RedactionLimit` were) and raised out of `prepare_output`."""

    def boom(raw, mapping):
        raise exc

    monkeypatch.setattr(runmap, "redact_untrusted", boom)
    assert tools.redact_layered("anything", {}) == WITHHELD, (
        "mutant 143: a refusal escaped as an error"
    )


def test_b10_g6_a_run_that_both_spellings_match_counts_once():
    """Group 6 (mutant 144): `a - b - c ...` is matched by the plain spelling and the visible-separator spelling; with 20 such runs the
    batch 9 count was 40 against a cap of 32 and the text was withheld. Counted once: 20 runs are read and the text is shown."""
    run = " - ".join("abcdefghijk")
    text = " ok ".join(run for _ in range(20))
    assert tools.prepare_output(text, {}, 40000, []) == text


def test_b10_g6_a_key_word_before_a_spaced_run_is_read_with_the_run():
    """Group 6 (mutant 145): the context width is `defaults.SPACED_CONTEXT_CHARS`; a context of 0 loses `password=` + a spaced value."""
    secret = "hunter2" + "xyzabc"
    out = on_the_run_path(PW + " " + spaced(secret))
    assert out.startswith(PW + " <SECRET_") and "u n t e r" not in out, (
        f"mutant 145: the key word before the run was not read with it, the value stands in part: {out!r}"
    )
    assert defaults.SPACED_CONTEXT_CHARS == 64


def test_b10_g6_a_run_with_a_one_letter_word_in_front_is_read():
    """Group 6 (mutant 146): the number of reads of a run is `defaults.SPACED_DROP_MAX`; one read loses `a A K I A ...`."""
    out = on_the_run_path("a " + spaced(KEY))
    assert out == "a <APIKEY_1>", (
        f"mutant 146: a run with a one-letter word in front was not read: {out!r}"
    )
    assert defaults.SPACED_DROP_MAX == 4


def test_b10_g6_a_refusal_keeps_its_own_message_on_the_run_path():
    """Group 6 (mutant 151; the 2 redaction errors of the fuzz, rand/465 and rand/607): `held value lost` (a value a reading found is
    gone from the stripped view: fail closed) was wrapped again by the catch-all as a plain `RedactionError("RedactionError")`, so
    the reason was lost. It keeps its message; on the tool path the text is withheld."""
    for text in (
        "x pas" + ESC + ESC + "(Bsword=hu" + "\x90" + "nter2secretXYZ y",
        "x p" + "\x9c" + "assword=" + "\x9d" + "0;t" + "\x07" + "hunte" + "\x07" + "r2secretXYZ y",
    ):
        with pytest.raises(runmap.RedactionError) as why:
            runmap.redact_untrusted(text, {})
        assert str(why.value) == "held value lost", (
            f"mutant 151: the reason was lost: {why.value!r}"
        )
        assert tools.prepare_output(text, {}, 4000, []) == WITHHELD


# ---- group 3 (rows of the run rule that had no mutant) ----------------------------------------------------------------------------


def test_b10_g3_the_run_rule_reads_any_separator_not_only_one_space():
    """Group 3 (mutant 153): two spaces between the characters of a key."""
    out = on_the_run_path("key: " + "  ".join(KEY) + " end")
    assert out == "key: <APIKEY_1> end", (
        f"mutant 153: a key with two spaces between its characters was not masked: {out!r}"
    )


def test_b10_g3_a_value_glued_to_its_key_name_starts_the_run():
    """Group 3 (mutant 154): `key=A K I A ...`: the character before the first token is `=`."""
    out = on_the_run_path("key=" + spaced(KEY))
    assert out == "key=<APIKEY_1>", (
        f"mutant 154: the value glued to its key name lost its first letter: {out!r}"
    )


def test_b10_g3_a_full_stop_standing_alone_after_the_run_is_not_part_of_the_value():
    """Group 3 (mutants 155, 157): `A K I A ... E .` (a space, then the full stop as its own token)."""
    out = on_the_run_path("see " + spaced(KEY) + " .")
    assert out == "see <APIKEY_1> .", (
        f"mutant 155: the sentence full stop became part of the value: {out!r}"
    )


def test_b10_g3_a_key_with_dashes_between_its_characters_is_masked():
    """Group 3 (mutant 156): `A-K-I-A-...` with the visible separator."""
    out = on_the_run_path("key: " + "-".join(KEY) + " end")
    assert out == "key: <APIKEY_1> end", (
        f"mutant 156: a key with dashes between its characters was not masked: {out!r}"
    )


def test_b10_g3_a_known_value_with_a_visible_dash_is_not_read_and_the_statement_is_pinned():
    """Group 2 (F1, pinned half 1): a KNOWN value of 12 or more characters written with a visible separator is not found by the gap
    pattern of a known value (`_GAP`: white space and invisible characters only); an UNKNOWN pattern-shaped value is (half 2, above)."""
    value = "Tr0ub4dor" + "-3xyzQabc"
    text = "n: " + "-".join(value) + " e"
    assert redact_mod.spaced_spans(text, [value]) == []
    plain = (
        "Tr0ub4dor" + "3xyzQabc"
    )  # a value with no hyphen of its own, written with a hyphen between its characters
    assert redact_mod.spaced_spans("n: " + "-".join(plain) + " e", [plain]) == [], (
        "mutant 157: a known value with a hyphen between its characters was read"
    )
