"""Mutants of pull request H (hidden items taken out at the choke point). Not collected by pytest.

Each mutant reverts ONE guard in a temp copy of `src`; the test named in `killer` (a test function, run alone) must fail,
with a failing line that holds `expect`. A killer that is parametrised runs all its rows, and the first failing row is
accepted (no pin); a killer that is one test is pinned, so another test failing first is "OTHER_TEST", not good. Numbers 1 to
43 follow the ticket (section 5.2); 44 and later are added by the builder (the consuming reading). Mutant 11 differs from the
ticket: a lone ESC that is KEPT would make the reader loop for ever, so the mutant makes a lone ESC swallow the next character.
Mutants 18, 27, 29 and 40 are written as the nearest one-place revert of the guard. Run from the repo root:

    uv run python tests/prh_mutants.py            # all; exit 1 if any is not good
    uv run python tests/prh_mutants.py glue       # only names that hold the text

The last line is `N of N good; problems: [...]`. The check `test_every_prh_mutant_still_applies` in `tests/test_prh_regressions.py`
fails when a mutant's `old` text is no longer in its file exactly once, or its killer test no longer exists. Honest limit: `expect` is the
word `assert` for most mutants (any assertion failure of the named test counts), because the killers are table tests whose failing
line holds the row data; the kill is judged by the named test failing by an assertion, not by a crash.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
UNIT = "tests/test_prh_hidden_unit.py"
CONTRACT = "tests/test_prh_contract.py"
REG = "tests/test_prh_regressions.py"
SPANS = "tests/test_prh_spans.py"
TOOLS_T = "tests/test_prh_tools.py"
STEPS = "tests/test_prh_steps.py"
H = "src/hadavin_sdk/guard/hidden.py"
R = "src/hadavin_sdk/guard/runmap.py"
X = "src/hadavin_sdk/guard/redact.py"
T = "src/hadavin_sdk/tools.py"
TEST_FILES = [UNIT, CONTRACT, REG, SPANS, TOOLS_T, STEPS]


def mutant(name, src, old, new, test_file, killer, expect="AssertionError", pinned=False, crash=""):
    return Mutant(
        name,
        src,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=f"{test_file[:-3]}::{killer}" if pinned else "",
        allow_crash=bool(crash),
        crash_type=crash,
    )


M = [
    # ---- the reader (hidden.py)
    mutant(
        "1 CSI final range ends at 0x7D",
        H,
        'if "@" <= c <= "~" or c == _CAN',
        'if "@" <= c <= "}" or c == _CAN',
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "2 C1 CSI opener not recognised",
        H,
        "if c == _C1_CSI:\n        return _csi_end(text, i + 1)",
        "if c == _C1_CSI:\n        return i + 1",
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "3 C0 inside a CSI aborts instead of being dropped",
        H,
        "if c in _CSI_DROP:",
        "if False:",
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "4 DEL inside a CSI not dropped",
        H,
        "(0x19, 0x19), (0x1C, 0x1F), (0x7F, 0x7F)",
        "(0x19, 0x19), (0x1C, 0x1F)",
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "5 OSC does not end at BEL",
        H,
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\x9c\n\r]")',
        r'_STRING_END_OSC = re.compile(r"[\x18\x1a\x1b\x9c\n\r]")',
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "6 ST as U+009C not recognised in an OSC",
        H,
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\x9c\n\r]")',
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\n\r]")',
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "7 a string never ended runs past the line end",
        H,
        '    if c in "\\n\\r":\n        return m.start()',
        "    if False:\n        return m.start()",
        UNIT,
        "test_grammar_row",
    ),
    mutant("8 DCS payload kept", H, '"P": False, "X"', '"X"', UNIT, "test_grammar_row"),
    mutant(
        "9 nF final byte not consumed",
        H,
        "            return k + 1\n        return i + 1  # no final byte",
        "            return k\n        return i + 1  # no final byte",
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "10 Fp range missing",
        H,
        'if "\\x30" <= d <= "\\x7e":  # Fp, Fe, Fs',
        'if "\\x40" <= d <= "\\x7e":  # Fp, Fe, Fs',
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "11 a lone ESC swallows the next character",
        H,
        "return i + 1  # a lone ESC; the next character is read afresh",
        "return i + 2  # a lone ESC; the next character is read afresh",
        UNIT,
        "test_grammar_row",
    ),
    mutant(
        "12 U+0000 not in removed",
        H,
        "(0x00, 0x08), (0x0E, 0x1B)",
        "(0x01, 0x08), (0x0E, 0x1B)",
        UNIT,
        "test_classes_exact",
        pinned=True,
    ),
    mutant(
        "13 U+0085 treated as removed, not space-like",
        H,
        "(0x80, 0x84), (0x86, 0x9F)",
        "(0x80, 0x9F)",
        UNIT,
        "test_classes_exact",
        pinned=True,
    ),
    mutant(
        "14 U+2028 left untouched",
        H,
        "(0x85, 0x85), (0x2028, 0x2029))",
        "(0x85, 0x85), (0x2029, 0x2029))",
        UNIT,
        "test_classes_exact",
        pinned=True,
    ),
    mutant(
        "15 tab moved into space-like",
        H,
        "SPACE_LIKE: frozenset[str] = _chars((0x0B, 0x0C)",
        "SPACE_LIKE: frozenset[str] = _chars((0x09, 0x09), (0x0B, 0x0C)",
        UNIT,
        "test_classes_exact",
        pinned=True,
    ),
    mutant(
        "16 glue space dropped",
        H,
        "if left_word and _is_word(text[i]):",
        "if False:",
        UNIT,
        "test_glue_row",
    ),
    mutant(
        "17 glue space added at every removed item",
        H,
        "if left_word and _is_word(text[i]):",
        "if left_word:",
        UNIT,
        "test_glue_row",
    ),
    mutant(
        "18 glue decided per item, not per run",
        H,
        "            if not in_run:\n                in_run = True\n                left_word = _is_word(last) if last else False",
        "            in_run = True\n            left_word = _is_word(text[start - 1]) if start else False",
        UNIT,
        "test_glue_row",
    ),
    mutant(
        "19 ignorable ranges emptied (Cf only)",
        H,
        "points = {c for lo, hi in IGNORABLE_RANGES for c in range(lo, hi + 1)}",
        "points = set()",
        UNIT,
        "test_ignorable_equals_file_and_rule",
        pinned=True,
    ),
    # ---- the choke point (runmap.py, redact.py)
    mutant(
        "20 hidden items not taken out first in redact_text",
        R,
        "joined, spaced = hidden.strip(text)\n        if joined is not text:",
        "joined, spaced = text, text\n        if joined is not text:",
        CONTRACT,
        "test_mf_forgery_untrusted",
        expect="RedactionError",
        crash="RedactionError",
    ),
    mutant(
        "21 decoded readings not stripped (undo)",
        R,
        "            step = _no_created_shapes(step, hidden.strip(step)[0])",
        "            pass",
        CONTRACT,
        "test_mf_decoded_reading_removes_hidden_items",
        pinned=True,
    ),
    mutant(
        "22 the gap pattern without the space alternative",
        X,
        'parts.append(" ?")',
        "pass",
        CONTRACT,
        "test_mf_gap_value_cut_is_masked",
        expect="RedactionError",
        crash="RedactionError",
        pinned=True,
    ),
    mutant(
        "23 step 6 returns the find result instead of refusing",
        R,
        'raise RedactionError("held value lost")',
        "return found.text, found.mapping",
        CONTRACT,
        "test_mf_step6_refuses",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "24 step 3 counts every held value, not only the needed ones",
        R,
        "and found.mapping[ph] not in spaced",
        "and True",
        CONTRACT,
        "test_mf_needed_count_only",
        expect="InputTooLarge",
        crash="InputTooLarge",
        pinned=True,
    ),
    mutant(
        "25 more than 256 needed values not refused",
        R,
        'if len(needed) > MAX_DECODED_MASKS:\n        raise InputTooLarge("InputTooLarge")',
        'if False:\n        raise InputTooLarge("InputTooLarge")',
        CONTRACT,
        "test_mf_over_256_needed_refuses",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "26 values under 4 characters replaced anywhere",
        X,
        'return re.compile(body if len(value) >= 4 else r"(?<!\\w)" + body + r"(?!\\w)")',
        "return re.compile(body)",
        CONTRACT,
        "test_short_value_whole_word_only",
        pinned=True,
    ),
    mutant(
        "27 earlier masks put in one value after another (W0 not applied)",
        R,
        "    return mask_spans(view, spans, mapping) if spans else view",
        "    out = view\n    for ph, decoded in pairs:\n        if decoded:\n            out = out.replace(decoded, ph)\n    return out",
        SPANS,
        "test_mf_keep_earlier_masks_partial_overlap",
    ),
    mutant(
        "28 the stripped decoded reading removed from _views",
        R,
        "        views.append(fits_after_nfkc(undo(text, strip_hidden=True)))",
        "        pass",
        REG,
        "test_regression_row",
    ),
    mutant(
        "29 _no_created_shapes does nothing",
        R,
        "def _no_created_shapes(before: str, after: str) -> str:",
        "def _no_created_shapes(before: str, after: str) -> str:\n    return after\n\n\ndef _no_created_shapes_unused(before: str, after: str) -> str:",
        CONTRACT,
        "test_mf_no_created_shapes",
    ),
    mutant(
        "30 _scrub finds on the raw text",
        T,
        "found = _scrub_layers(joined, long_enough, scrub)",
        "found = _scrub_layers(raw, long_enough, scrub)",
        TOOLS_T,
        "test_scrub_without_secret_returns_the_text_as_written",
        pinned=True,
    ),
    mutant(
        "31 _scrub returns the scrubbed joined text",
        T,
        "        return result\n    except runmap.TooDeep:",
        "        return found\n    except runmap.TooDeep:",
        TOOLS_T,
        "test_scrub_keeps_boundary",
    ),
    mutant(
        "32 _decoded not stripped",
        T,
        "return hidden.strip(undo(text, strip_hidden=True))[0]",
        "return undo(text)",
        TOOLS_T,
        "test_mf_handed_out_encoded_cut",
    ),
    mutant(
        "33 _first_decoded calls the stripped _decoded",
        T,
        "return runmap.undo(char)[",
        "return _decoded(char)[",
        TOOLS_T,
        "test_first_decoded_plain",
        pinned=True,
    ),
    mutant(
        "34 _sanitise turns NUL into U+FFFD again",
        T,
        'return text.encode("utf-8", "replace").decode("utf-8")',
        'return text.replace("\\0", "\\ufffd").encode("utf-8", "replace").decode("utf-8")',
        TOOLS_T,
        "test_mf_digest_keeps_nul",
        pinned=True,
    ),
    mutant(
        "35 _refuse_forgery reads only the as-written form",
        R,
        "for t in (out,) if out.isascii() else (out, canonical(out)):",
        "for t in (out,):",
        STEPS,
        "test_refuse_forgery_reads_canonical",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "36 _refuse_forgery not called",
        R,
        "            _refuse_forgery(out, current)",
        "            pass",
        STEPS,
        "test_refuse_forgery_called",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "37 the joined spelling of earlier masks removed",
        R,
        "if (sj := hidden.strip(d)[0]) != d and len(sj) >= 4 and (ph, sj) not in made",
        "if False and (sj := hidden.strip(d)[0])",
        SPANS,
        "test_case_790_regression",
        pinned=True,
    ),
    mutant(
        "38 a span inside another kept (both placeholders emitted)",
        X,
        "        if groups and start < reach:\n            if end > reach:",
        "        if groups and start < reach and end > reach:\n            if end > reach:",
        SPANS,
        "test_nested_restore_exact",
        pinned=True,
    ),
    mutant(
        "39 a merged span emits only its first member's placeholder",
        X,
        "held = redactor._place(label, merged, merged)",
        "held = members[0][2]",
        SPANS,
        "test_mf_span_rule_generator",
    ),
    mutant(
        "40 the sweep puts values in one after another (W0 not applied)",
        X,
        "                parts[i] = mask_spans(segment, spans, self.mapping, _redactor=self)",
        "                out_seg = segment\n                for original, placeholder, rule in todo:\n                    out_seg = out_seg.replace(original, placeholder)\n                parts[i] = out_seg",
        SPANS,
        "test_mf_sweep_partial_overlap",
    ),
    mutant(
        "41 a merged placeholder is issued anew",
        X,
        "held = redactor.reverse.get(merged)",
        "held = None",
        UNIT,
        "test_merged_placeholder_is_reused_by_mask_spans",
        pinned=True,
    ),
    mutant(
        "42 the _scrub backstop removed",
        T,
        "if any(_has_form(left, f) or _has_form(decoded, f) for f in forms):",
        "if False:",
        TOOLS_T,
        "test_scrub_backstop_withholds",
        pinned=True,
    ),
    mutant(
        "43 a space allowed between every pair of characters",
        X,
        "if i and hidden.is_word(value[i - 1]) and hidden.is_word(c):",
        "if i:",
        CONTRACT,
        "test_gap_only_between_word_chars",
        pinned=True,
    ),
    # ---- added by the builder
    mutant(
        "44 the consuming reading removed (tput sgr0 inside a key)",
        R,
        "for r in hidden.strip_consuming(text):",
        "for r in ():",
        REG,
        "test_regression_row",
    ),
    mutant(
        "45 the consuming reading keeps the final letter of an nF sequence",
        H,
        "(consume or not text[k].isalnum())",
        "(not text[k].isalnum())",
        UNIT,
        "test_strip_consuming",
        pinned=True,
    ),
    mutant(
        "46 the consuming reading keeps the letter after ESC",
        H,
        "and not d.isupper() and not consume",
        "and not d.isupper()",
        UNIT,
        "test_strip_consuming",
        pinned=True,
    ),
]


def check_applies() -> list[str]:
    """Problems found without running pytest: an `old` text that is not in its file exactly once; a killer that is not a test."""
    problems = []
    for m in M:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        if text.count(m.old) != 1:
            problems.append(f"{m.name}: old text occurs {text.count(m.old)} times in {m.file}")
        killer = (ROOT / m.test_file).read_text(encoding="utf-8")
        if f"def {m.only_test}(" not in killer:
            problems.append(f"{m.name}: no test {m.only_test} in {m.test_file}")
    return problems


if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    if (found := check_applies()) and not only:
        print("\n".join(found))
        print(f"0 of {len(M)} good; problems: {found}")
        sys.exit(1)
    first_lines = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    res = run_mutants(
        ROOT,
        M,
        TEST_FILES,
        extra_dirs=("tests", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
        timeout=300,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
