"""Mutants of pull request H (hidden items taken out at the choke point). Not collected by pytest.

Each mutant reverts ONE guard in a temp copy of `src`; the test named in `killer` (a test function, run alone) must fail
with a failing first line that holds `expect` (a distinctive fragment of the row or the message, so a crash or another failure
does not count). A killer that is parametrised runs all its rows, and the first failing row is
accepted (no pin), unless `pinned` is the id of one row (44); a killer that is one test is pinned, so another test failing first is "OTHER_TEST", not good. Numbers 1 to
43 follow the ticket (section 5.2); 44 and later are added by the builder (the consuming reading). Mutant 11 differs from the
ticket: a lone ESC that is KEPT would make the reader loop for ever, so the mutant makes a lone ESC swallow the next character.
Mutants 18, 27, 29 and 40 are written as the nearest one-place revert of the guard. Run from the repo root:

    uv run python tests/prh_mutants.py            # all; exit 1 if any is not good
    uv run python tests/prh_mutants.py glue       # only names that hold the text

The last line is `N of N good; problems: [...]`. The check `test_every_prh_mutant_still_applies` in `tests/test_prh_regressions.py`
fails when a mutant's `old` text is no longer in its file exactly once, or its killer test no longer exists. Honest limit: `expect` is the word `AssertionError` (any assertion failure of the named test counts) only for the mutants of the
class tables whose killers compare whole sets (12 to 15, 19) and are pinned to one test; every other mutant holds a distinctive
fragment of its failing row or message, and the kill is judged by the named test failing by an assertion, not by a crash (a crash counts only
where `crash` is given).
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
        pinned=pinned
        if isinstance(pinned, str)
        else (f"{test_file[:-3]}::{killer}" if pinned else ""),
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
        expect="csi final 0x7E",
    ),
    mutant(
        "2 C1 CSI opener not recognised",
        H,
        "if c == _C1_CSI:\n        return _csi_end(text, i + 1)",
        "if c == _C1_CSI:\n        return i + 1",
        UNIT,
        "test_grammar_row",
        expect="csi c1",
    ),
    mutant(
        "3 C0 inside a CSI aborts instead of being dropped",
        H,
        "if c in _CSI_DROP:",
        "if False:",
        UNIT,
        "test_grammar_row",
        expect="csi c0 inside dropped",
    ),
    mutant(
        "4 DEL inside a CSI not dropped",
        H,
        "(0x19, 0x19), (0x1C, 0x1F), (0x7F, 0x7F)",
        "(0x19, 0x19), (0x1C, 0x1F)",
        UNIT,
        "test_grammar_row",
        expect="csi del inside dropped",
    ),
    mutant(
        "5 OSC does not end at BEL",
        H,
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\x9c\n\r]")',
        r'_STRING_END_OSC = re.compile(r"[\x18\x1a\x1b\x9c\n\r]")',
        UNIT,
        "test_grammar_row",
        expect="osc BEL",
    ),
    mutant(
        "6 ST as U+009C not recognised in an OSC",
        H,
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\x9c\n\r]")',
        r'_STRING_END_OSC = re.compile(r"[\x07\x18\x1a\x1b\n\r]")',
        UNIT,
        "test_grammar_row",
        expect="osc C1 ST",
    ),
    mutant(
        "7 a string never ended runs past the line end",
        H,
        '    if c in "\\n\\r":\n        return m.start()',
        "    if False:\n        return m.start()",
        UNIT,
        "test_grammar_row",
        expect="osc never ended, line end kept",
    ),
    mutant(
        "8 DCS payload kept",
        H,
        '"P": False, "X"',
        '"X"',
        UNIT,
        "test_grammar_row",
        expect="dcs BEL is body",
    ),
    mutant(
        "9 nF final byte not consumed",
        H,
        "            return k + 1\n        return i + 1  # no final byte",
        "            return k\n        return i + 1  # no final byte",
        UNIT,
        "test_grammar_row",
        expect="nF symbol final goes",
    ),
    mutant(
        "10 Fp range missing",
        H,
        'if "\\x30" <= d <= "\\x7e":  # Fp, Fe, Fs',
        'if "\\x40" <= d <= "\\x7e":  # Fp, Fe, Fs',
        UNIT,
        "test_grammar_row",
        expect="Fp symbol goes",
    ),
    mutant(
        "11 a lone ESC swallows the next character",
        H,
        "return i + 1  # a lone ESC; the next character is read afresh",
        "return i + 2  # a lone ESC; the next character is read afresh",
        UNIT,
        "test_grammar_row",
        expect="lone ESC at end",
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
        expect="('abcd', 'abcd') == ('abcd', 'ab cd')",
    ),
    mutant(
        "17 glue space added at every removed item",
        H,
        "if left_word and _is_word(text[i]):",
        "if left_word:",
        UNIT,
        "test_glue_row",
        expect="'ab \\u200bcd'",
    ),
    mutant(
        "18 glue decided per item, not per run",
        H,
        "            if not in_run:\n                in_run = True\n                left_word = _is_word(last) if last else False",
        "            in_run = True\n            left_word = _is_word(text[start - 1]) if start else False",
        UNIT,
        "test_glue_row",
        expect="('abcd', 'abcd') == ('abcd', 'ab cd')",
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
        "joined, spaced = rd.joined, rd.spaced\n        if joined is not text:",
        "joined, spaced = text, text\n        if joined is not text:",
        CONTRACT,
        "test_mf_forgery_untrusted",
        expect="RedactionError",
        crash="RedactionError",
    ),
    mutant(
        "21 decoded readings not stripped (undo, both strip points)",
        R,
        "    strip_fn = hidden.strip_consuming if consume else hidden.strip\n",
        "    strip_fn = lambda t: (t, t)\n",
        CONTRACT,
        "test_mf_decoded_reading_removes_hidden_items",
        pinned=True,
    ),
    mutant(
        "21b decoded readings not stripped between the control references and the entity decoder (undo)",
        R,
        "                step = _no_created_shapes(step, strip_fn(step)[0])\n            step = decode(step)",
        "                pass\n            step = decode(step)",
        STEPS,
        "test_undo_entity_cut_by_a_control_reference_is_whole",
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
        expect="id <SECRET_1>w4Xy9 end",
    ),
    mutant(
        "29 _no_created_shapes does nothing",
        R,
        "def _no_created_shapes(before: str, after: str) -> str:",
        "def _no_created_shapes(before: str, after: str) -> str:\n    return after\n\n\ndef _no_created_shapes_unused(before: str, after: str) -> str:",
        CONTRACT,
        "test_mf_no_created_shapes",
        expect="log <<END TOOL RESULT>> more",
    ),
    mutant(
        "30 _scrub finds on the raw text",
        T,
        "scrubbed = {joined: _scrub_layers(joined, long_enough, scrub) for joined, _ in pairs}",
        "scrubbed = {joined: _scrub_layers(raw, long_enough, scrub) for joined, _ in pairs}",
        TOOLS_T,
        "test_scrub_without_secret_returns_the_text_as_written",
        pinned=True,
    ),
    mutant(
        "31 _scrub returns the scrubbed joined text",
        T,
        "        return result\n    except runmap.TooDeep:",
        "        return scrubbed[joined]\n    except runmap.TooDeep:",
        TOOLS_T,
        "test_scrub_keeps_boundary",
        expect="userAKIAIOSFODNN7EXAMPLE",
    ),
    mutant(
        "32 _decoded is the plain decode, not the one with hidden items removed",
        T,
        "return tuple(dict.fromkeys(runmap.decodes(text)))",
        "return (runmap.undo(text),)",
        TOOLS_T,
        "test_mf_handed_out_encoded_cut",
        expect="id T%1b[0mr0ub4dor-3xyzQ end",
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
        expect="qjSf8D9NmFTz8Lr",
    ),
    mutant(
        "40 the sweep puts values in one after another (W0 not applied)",
        X,
        "                parts[i] = mask_spans(segment, spans, self.mapping, _redactor=self)",
        "                out_seg = segment\n                for original, placeholder, rule in todo:\n                    out_seg = out_seg.replace(original, placeholder)\n                parts[i] = out_seg",
        SPANS,
        "test_mf_sweep_partial_overlap",
        expect="id Qz7k<SECRET_2> end",
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
        "if any(_has_form(left, f) or any(_has_form(d, f) for d in decoded) for f in forms):",
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
        "if r.consuming_joined is r.joined and r.consuming_spaced is r.spaced:\n                return  # no sequence",
        "if True:\n                return  # no sequence",
        REG,
        "test_regression_row",
        expect="t_L9 [untrusted]",
        pinned="tests/test_prh_regressions::test_regression_row[mf_t_L9]",
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
    mutant(
        "47 the consuming reading not computed (hidden.readings)",
        H,
        "cj, cs = strip_consuming(text) if _ESC in text else (joined, spaced)",
        "cj, cs = (joined, spaced)",
        UNIT,
        "test_readings_are_the_same_set_everywhere",
        expect="AKIAIOSFODNN7EXAMPLE",
        pinned=True,
    ),
    mutant(
        "48 a lost letter in the consuming reading not refused",
        R,
        'if any(v[i : i + _PIECE] in shown for v in values for i in range(len(v) - _PIECE + 1)):\n        raise InputTooLarge("InputTooLarge")',
        'if False:\n        raise InputTooLarge("InputTooLarge")',
        STEPS,
        "test_consuming_wins_needs_a_novel_value_and_refuses_a_lost_letter",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "49 the consuming reading wins without a novel value",
        R,
        "    if not novel:\n        return False",
        "    if False:\n        return False",
        STEPS,
        "test_consuming_wins_needs_a_novel_value_and_refuses_a_lost_letter",
        expect="is False",
        pinned=True,
    ),
    mutant(
        "50 the pass counter never refuses",
        R,
        "if self.passes > defaults.MAX_REDACT_PASSES:",
        "if False:",
        STEPS,
        "test_pass_counter_refuses_past_the_bound",
        expect="DID NOT RAISE",
        pinned=True,
    ),
    mutant(
        "51 a control reference is not kept (control_refs)",
        R,
        'return _CONTROL_REF.sub(_control_ref, text) if "&#" in text else text',
        "return text",
        STEPS,
        "test_control_refs_keeps_a_terminated_control_reference",
        expect="a&#27;b",
        pinned=True,
    ),
    mutant(
        "52 decodes has no consuming reading",
        R,
        "    consuming = undo(text, strip_hidden=True, consume=True)\n    return (plain,) if consuming == plain else (plain, consuming)",
        "    return (plain,)",
        STEPS,
        "test_decodes_holds_the_consuming_reading",
        expect="(BIOSFODNN7EXAMPLE',)",
    ),
    mutant(
        "53 the scrub shows the first reading with a find when no reading holds every secret found",
        T,
        "if chosen is None:\n            return MARKER + TRUNCATED",
        "if chosen is None:\n            chosen = next((j, sp) for j, sp, _ in triples if held[j])",
        TOOLS_T,
        "test_scrub_lost_letter_withholds_the_result",
        expect="Tr0ub4dor(B-3xyzQ",
        pinned=True,
    ),
    mutant(
        "54 the scrub does not search the consuming reading",
        T,
        "                    (rd.consuming_joined, rd.consuming_spaced, False),\n",
        "",
        TOOLS_T,
        "test_mf_scrub_consuming_cut",
        expect="Tr0ub4dor(B-3xyzQ",
    ),
    mutant(
        "55 a terminated control reference deleted by the entity decoder",
        R,
        "return html.unescape(control_refs(text))",
        "return html.unescape(text)",
        STEPS,
        "test_undo_keeps_a_control_reference_as_the_character",
        expect="a(Bb",
        pinned=True,
    ),
    mutant(
        "56 the pass bound set to 1",
        "src/hadavin_sdk/defaults.py",
        "MAX_REDACT_PASSES = 24",
        "MAX_REDACT_PASSES = 1",
        STEPS,
        "test_pass_bound_is_above_the_measured_worst_case",
        expect="17 <",
        pinned=True,
    ),
    # ---- added by batch b5 (the scrub never hands on a joined reading; the pass bound; the unterminated ESC reference)
    mutant(
        "57 the scrub returns the chosen reading with no gap (a joined reading handed on)",
        T,
        "        joined, spaced = chosen\n",
        "        joined, spaced = chosen[0], chosen[0]\n",
        TOOLS_T,
        "test_scrub_result_is_the_spaced_copy_of_the_reading_that_holds_the_secret",
        expect="result with no gap before the key",
        pinned=True,
    ),
    mutant(
        "58 the scrub takes the secrets of the first reading with a find only (union over all readings dropped)",
        T,
        "union = {\n            x: max(h.get(x, 0) for h in held.values())\n            for x in {x for h in held.values() for x in h}\n        }\n",
        "union = next((h for h in held.values() if h), {})\n",
        TOOLS_T,
        "test_b6_the_union_is_the_most_any_reading_holds_without_the_piece_check",
        expect="AssertionError",
        pinned=True,
    ),
    mutant(
        "59 the character reading is a result although the text holds a control sequence",
        T,
        "if faithful or not chars]",
        "if True or not chars]",
        TOOLS_T,
        "test_scrub_character_reading_with_a_sequence_is_withheld",
        expect="a character reading with a sequence body was shown",
        pinned=True,
    ),
    mutant(
        "60 leaves_text finds no body",
        H,
        "if body and not (len(body) == 1 and body.isalnum()):",
        "if False:",
        TOOLS_T,
        "test_leaves_text",
        pinned=True,
    ),
    mutant(
        "61 the spaced character reading is the joined one (hidden.readings)",
        H,
        "return Readings(joined, spaced, chars, chars_spaced, cj, cs)",
        "return Readings(joined, spaced, chars, chars, cj, cs)",
        TOOLS_T,
        "test_scrub_result_is_the_spaced_copy_of_the_reading_that_holds_the_secret",
        expect="result with no gap before the key",
        pinned=True,
    ),
    mutant(
        "62 no glue space in the spaced character reading",
        H,
        'return " " if a and b < len(s) and _is_word(s[a - 1]) and _is_word(s[b]) else ""',
        'return ""',
        UNIT,
        "test_characters_readings_examples",
        pinned=True,
    ),
    mutant(
        "63 redact() returns the joined text when more values need pairing than the limit",
        X,
        "        if len(needed) > MAX_DECODED_MASKS:\n            return WITHHELD_NOTE",
        "        if len(needed) > MAX_DECODED_MASKS:\n            return found",
        STEPS,
        "test_redact_fails_closed_when_more_than_the_limit_of_values_need_pairing",
        expect="<APIKEY_1>",
        pinned=True,
    ),
    mutant(
        "64 redact() returns the joined text when a found value is not located in the spaced reading",
        X,
        "                if not matches:\n                    return WITHHELD_NOTE",
        "                if not matches:\n                    return found",
        STEPS,
        "test_redact_fails_closed_when_a_found_value_cannot_be_located_in_the_spaced_reading",
        expect="<APIKEY_1>",
        pinned=True,
    ),
    mutant(
        "65 an unterminated reference to ESC is left to the entity decoder",
        R,
        "(;|(?=[\\[(\\]]))",
        "(;)",
        STEPS,
        "test_control_refs_reads_an_unterminated_esc_before_a_sequence_start",
        pinned=True,
    ),
    mutant(
        "66 an unterminated reference to any control character is read",
        R,
        'if m.group(3) != ";" and n != 0x1B:',
        "if False:",
        STEPS,
        "test_control_refs_reads_an_unterminated_esc_before_a_sequence_start",
        pinned=True,
    ),
    mutant(
        "67 the pass bound set to 8 (below the worst of the seeded search)",
        "src/hadavin_sdk/defaults.py",
        "MAX_REDACT_PASSES = 24",
        "MAX_REDACT_PASSES = 8",
        STEPS,
        "test_pass_bound_holds_for_a_seeded_search",
        expect="texts reached the pass bound",
        pinned=True,
    ),
    mutant(
        "68 the pass bound set to 6 (below what a regression row needs)",
        "src/hadavin_sdk/defaults.py",
        "MAX_REDACT_PASSES = 24",
        "MAX_REDACT_PASSES = 6",
        STEPS,
        "test_every_regression_row_needs_at_most_seven_passes",
        expect="AssertionError: 6",
        pinned=True,
    ),
    mutant(
        "44b the consuming reading removed, a row with a tail",
        R,
        "if r.consuming_joined is r.joined and r.consuming_spaced is r.spaced:\n                return  # no sequence",
        "if True:\n                return  # no sequence",
        REG,
        "test_tail_row_trail_is_masked",
        expect="b4_1_trail [untrusted]",
        pinned=True,
    ),
    mutant(
        "44c the consuming reading removed, a row with a tail on the next line",
        R,
        "if r.consuming_joined is r.joined and r.consuming_spaced is r.spaced:\n                return  # no sequence",
        "if True:\n                return  # no sequence",
        REG,
        "test_tail_row_on_the_next_line_is_masked",
        expect="b4_1_nextline [untrusted]",
        pinned=True,
    ),
    mutant(
        "44d the consuming reading removed, a row with a long tail",
        R,
        "if r.consuming_joined is r.joined and r.consuming_spaced is r.spaced:\n                return  # no sequence",
        "if True:\n                return  # no sequence",
        REG,
        "test_tail_row_long_tail_is_masked",
        expect="b4_1_longtail [untrusted]",
        pinned=True,
    ),
    # ---- batch 6: the readings are compared per copy (round 5: H1, H2, H3, d3, d11, and the tests that passed on old code) ----
    mutant(
        "72 the readings compared as sets again: the per-copy count dropped (a reading that holds ONE copy of a secret found twice elsewhere is the result)",
        T,
        "if all(held[j].get(x, 0) >= n for x, n in union.items())\n                    and held[j].keys() == union.keys()\n",
        "if held[j].keys() == union.keys()\n",
        TOOLS_T,
        "test_b6_the_readings_are_compared_per_copy_without_the_piece_check",
        expect="AssertionError",
        pinned=True,
    ),
    mutant(
        "73 the text as written is returned when only another reading changed (a cut fragment stays)",
        T,
        "                chosen = next(((j, sp) for j, sp in usable if scrubbed[j] != j), None)",
        "                return raw",
        TOOLS_T,
        "test_b6_h2_a_cut_fragment_after_an_esc_is_never_returned_as_written",
        expect="log ",
    ),
    mutant(
        "74 the piece check removed (a copy a reading could not read whole stays when counts agree)",
        T,
        "        if any(_has_piece(t, forms, scrub.piece_min) for t in (left, *decoded)):",
        "        if False:",
        TOOLS_T,
        "test_b6_h1_equal_counts_that_are_different_copies_show_nothing",
        expect="AssertionError",
        pinned=True,
    ),
    mutant(
        "75 the character reading's output is the joined reading again (no glue space)",
        R,
        "            elif view in char_pairs:\n                vj, vs = char_pairs[view]\n",
        "            elif False:\n                vj, vs = char_pairs[view]\n",
        TOOLS_T,
        "test_b6_h3_a_value_glued_by_a_bell_stays_a_word_of_its_own_in_the_character_reading",
        expect="AssertionError",
        pinned=True,
    ),
    mutant(
        "76 redact() reads only the grammar's reading (a key cut by ESC ( B ESC [ m stays readable)",
        X,
        "            if len(_PLACEHOLDER.findall(alt)) > len(_PLACEHOLDER.findall(out)):",
        "            if False:",
        TOOLS_T,
        "test_b6_d3_a_key_cut_by_sgr0_is_masked_in_a_direct_redact_call",
        expect="IOSFODNN",
        pinned=True,
    ),
    mutant(
        "77 redact() does not withhold a known value an ESC cut in one copy",
        X,
        "        if any(r.count(v) > joined.count(v) for v in known for r in others):",
        "        if False:",
        TOOLS_T,
        "test_b6_d11_a_known_value_after_an_esc_is_withheld_in_a_direct_redact_call",
        expect="AssertionError",
        pinned=True,
    ),
    mutant(
        "79 the fragment an ESC took the first letter of is not cut at the end of the result",
        T,
        "        result = _strip_fragment(result, sorted({f[1:] for f in forms if len(f) > 1}), scrub)\n",
        "",
        TOOLS_T,
        "test_b6_seeded_mixes_of_copies_never_leave_a_piece_of_the_secret",
        expect="texts left a piece",
        pinned=True,
    ),
    mutant(
        "80 every pass counted twice (the code makes more passes than the recorded rows need)",
        R,
        "        self.passes += 1\n        if self.passes > defaults.MAX_REDACT_PASSES:",
        "        self.passes += 2\n        if self.passes > defaults.MAX_REDACT_PASSES:",
        STEPS,
        "test_every_regression_row_needs_at_most_seven_passes",
        expect="AssertionError",
    ),
    mutant(
        "81 every pass counted twice (the seeded search reaches the bound)",
        R,
        "        self.passes += 1\n        if self.passes > defaults.MAX_REDACT_PASSES:",
        "        self.passes += 2\n        if self.passes > defaults.MAX_REDACT_PASSES:",
        STEPS,
        "test_pass_bound_holds_for_a_seeded_search",
        expect="texts reached the pass bound",
        pinned=True,
    ),
    mutant(
        "78 a refusal reads as masked again (the verdict of a path that returned nothing)",
        REG,
        'return "refused"',
        'return "masked"',
        REG,
        "test_a_refusal_is_not_masked_unless_the_row_says_so",
        expect="AssertionError",
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
