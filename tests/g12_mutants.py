"""The mutants of ticket G12 (trailing prose punctuation of a SECRET value), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must hold
``expect`` (the ``G12-n `` start of the assertion message). Run from the repo root:

    python tests/g12_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g12_mutants.py G12-M3     # only mutants whose name contains the text

EQUIVALENT, not listed (G12d): at the END the entity `&#10;` and `<br/>` are also stripped by the pieces the other forms leave (`;` `>` `/` are not alphanumeric, then
`&#10` / `<br` are cut-short forms), so removing the whole forms changes nothing there; the same is NOT true of a tag the cut-short list does not name (`PW<em/>`: `<em` is
no cut-short form), so M36 tests the end with `<em/>`, and M29, M30 test the start. Also not listed: the `%` of `last in ";>%"` in `_bare_span` (no form ends in `%`; the
guard is about speed) and either half of the label-text rule alone (an entry of the map has its counter reached, so the mapping half only repeats what the counter says: dropping
the counter half leaves the mapping half, which decides the same on every run this redactor makes).
EQUIVALENT, not listed: dropping ``core != full and `` from the registration guard. When ``core == full``, ``full`` went into
``self.reverse`` earlier in ``_place`` and nothing in between removes it, so ``core not in self.reverse`` is already False.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
RD = "src/hadavin_sdk/guard/redact.py"
TEST = "tests/test_redact_g12_trailing_punct.py"
PIN = "tests/test_redact_g12_trailing_punct::"
C = "        if derived and label in SECRET_KINDS:\n            start, end = _bare_span(full)\n"
I = "        if core != full and len(core) >= 3 and core not in self.reverse:\n"
HEAD = "        elif not text[start].isalnum():\n"
TAIL = "        elif not last.isalnum():\n"
CLOSE = '        elif (last in ";>%" or last.isalnum()) and (\n            m := _EDGE_CLOSE.search(text, max(start, end - 64), end)\n        ) is not None:\n'
OPEN = "        if (m := _EDGE_OPEN.match(text, start, end)) is not None:\n"
EF = (
    r'''_EDGE_FORM = r"(?:</?[A-Za-z][A-Za-z0-9]{0,15} {0,3}/?>|\\[nrt]|%[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|\\x[0-9A-Fa-f]{2}|&(?:#[0-9]{1,7}|[A-Za-z]{2,10});)"'''
    + "\n"
)
CUTSHORT = (
    r'''    rf"(?:{_EDGE_FORM}|<(?:br|hr|b|i|p|a|li|tr|td|div|span)|&(?:#[0-9]{{1,7}}|quot|amp|lt|gt|nbsp|apos))\Z"'''
    + "\n"
)
J = '                self._journal.append(("map", f"<{label}_{self.counters[label]}>", core))\n'


def m(name, old, new, killer, expect):
    return Mutant(
        name,
        RD,
        old,
        new,
        expect,
        test_file=TEST,
        only_test=killer.split("[")[0],
        pinned=PIN + killer,
    )


WRAP = "test_g12_a_wrapper_at_either_end_does_not_leave_the_clear_copy"
MARK = "test_g12_a_trailing_mark_does_not_leave_the_clear_copy"
PH = "test_g12_a_core_that_is_a_placeholders_own_text_is_not_registered"
CAPS = "test_g12_an_all_caps_name_with_a_number_or_a_label_prefix_is_a_value_and_keeps_its_core"
LK = "test_g12_a_value_of_tokens_or_the_cut_body_of_a_real_label_gets_no_core"
E1 = "test_g12e_a_cut_off_opener_of_a_caps_word_or_leading_zeros_keep_the_core"
LB = "test_g12_a_lookalike_bracket_at_an_edge_or_inside_still_gets_a_core"
EDGE = "test_g12_an_escaped_or_encoded_edge_does_not_leave_the_clear_copy"
START = "test_g12_an_escaped_or_encoded_edge_at_the_start_does_not_leave_the_clear_copy"
M = [
    m("G12-M1 the core is never registered", I, "        if False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M2 only a comma is trailing", TAIL, "        elif last == \",\":\n", MARK + "[.]", "G12-1 "),
    m("G12-M3 a held core gets a second placeholder", I, "        if core != full and len(core) >= 3:\n", "test_g12_a_core_the_map_holds_gets_no_second_placeholder", "G12-9 "),
    m("G12-M4 the core is not journaled", J, "                pass\n", "test_g12_a_rolled_back_value_takes_its_core_with_it", "G12-10 "),
    m("G12-M5 the floor is 4", I, I.replace(">= 3", ">= 4"), "test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma", "G12-8 "),
    m("G12-M6 identifier kinds get a core", C, "        if derived:\n            start, end = _bare_span(full)\n", "test_g12_identifier_kinds_are_unchanged", "G12-11 "),
    m("G12-M7 a G9 union gets a core", C, C.replace("derived and ", ""), "test_g12_a_g9_union_registers_its_value_only_and_no_core", "G12-12 "),
    # G12b: the one edge rule (`_bare`), its halves, and the words the exemption shares it with
    m("G12-M8 the leading half is off", HEAD, "        elif False:\n", WRAP + "[9]", "G12-14 "),
    m("G12-M9 the trailing half is off", TAIL, "        elif False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M10 the trailing half is ASCII only", TAIL, "        elif last.isascii() and not last.isalnum():\n", WRAP + "[6]", "G12-14 "),
    m("G12-M11 the leading half is ASCII only", HEAD, "        elif text[start].isascii() and not text[start].isalnum():\n", WRAP + "[9]", "G12-14 "),
    m("G12-M12 a closing tag is kept", CLOSE, "        elif False:\n", WRAP + "[2]", "G12-14 "),
    m("G12-M13 an opening tag is kept", OPEN, "        if False:\n", WRAP + "[3]", "G12-14 "),
    m("G12-M14 an escaped newline is kept", EF, EF.replace(r"|\\[nrt]", ""), WRAP + "[10]", "G12-14 "),
    # G12c: the placeholder-like rule, the look-alike guard, the large value, the new edge forms
    m("G12-M26 a percent escape is kept", EF, EF.replace("|%[0-9A-Fa-f]{2}", ""), EDGE + "[%0A]", "G12-23 "),
    m("G12-M27 a JSON unicode escape is kept", EF, EF.replace(r"|\\u[0-9A-Fa-f]{4}", ""), EDGE + r"[\\u000a]", "G12-23 "),
    m("G12-M28 a hex escape is kept", EF, EF.replace(r"|\\x[0-9A-Fa-f]{2}", ""), EDGE + r"[\\x0a]", "G12-23 "),
    m("G12-M29 an entity is kept", EF, EF.replace("|&(?:#[0-9]{1,7}|[A-Za-z]{2,10});", ""), START + "[&#10;]", "G12-24 "),
    m("G12-M30 a self-closing tag is kept", EF, EF.replace(" {0,3}/?>", ">"), START + "[<br/>]", "G12-24 "),
    m("G12-M31 a cut-short tag is kept", CUTSHORT, CUTSHORT.replace("<(?:br|hr|b|i|p|a|li|tr|td|div|span)|", ""), EDGE + "[<br />]", "G12-23 "),
    m("G12-M32 a cut-short entity is kept", CUTSHORT, CUTSHORT.replace("|&(?:#[0-9]{{1,7}}|quot|amp|lt|gt|nbsp|apos)", ""), EDGE + "[&quot;]", "G12-23 "),
    m("G12-M15 a no-value core is registered", "    if core.lower() in _NOT_A_VALUE or ", "    if ", "test_g12_the_second_none_is_neither_masked_nor_swept", "G12-13 "),
    # G12c, G12d: the declined cores (`_core_is_declined`), the budget, the sweep's look-alikes, the close search
    m("G12-M18 a placeholder's own text is registered", "    if _LABEL_TEXT.fullmatch(core) is not None:\n", "    if False:\n", "test_g12_a_value_that_is_a_placeholders_text_keeps_the_real_placeholders_intact", "G12-20 "),
    m("G12-M19 a label-shaped value is never registered", "        and int(number) <= counters.get(label, 0)\n", "        and True\n", "test_g12_a_label_shaped_value_beyond_the_counter_keeps_its_core[password=SECRET_123, SECRET_123]", "G12-31 "),
    m("G12-M21 a `<` anywhere declines a cut-off start", '        and full[start - 1] == "<"\n', "", "test_g12_the_open_bracket_is_a_cut_off_form_only_right_before_the_core", "G12-34 "),
    m("G12-M22 a value of tokens gets a core", '    if core.lower() in _NOT_A_VALUE or not re.search(r"[^\\W_]", _ANY_TOKEN.sub("", full)):\n', "    if core.lower() in _NOT_A_VALUE:\n", "test_g12_a_value_of_tokens_alone_gets_no_core", "G12-35 "),
    m("G12-M23 the cut body of a real label gets a core", '    if "\\u2039" in full[:start] and _LABEL_PREFIX.fullmatch(core) is not None:\n', "    if False:\n", LK + "[\\u2039SECRET_x\\u203a]", "G12-22 "),
    m("G12-M33 any caps core behind a cut bracket is declined", "_LABEL_PREFIX.fullmatch(core) is not None:\n", 're.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Za-z0-9]*)?", core) is not None:\n', LB + "[password=\\u2039HUNTER2, HUNTER2-HUNTER2]", "G12-29 "),
    m("G12-M34 a cut bracket declines any core", '    if "\\u2039" in full[:start] and _LABEL_PREFIX.fullmatch(core) is not None:\n', '    if "\\u2039" in full[:start]:\n', LB + "[password=\\u2039HUNTER2, HUNTER2-HUNTER2]", "G12-29 "),
    m("G12-M35 a cut bracket before a token body is not declined", '    if full[start - 1 : start] == "\\u2039" and _TOKEN_BODY_START.match(core):\n', "    if False:\n", LK + "[\\u2039SECRET_1\\u203ahunter22]", "G12-22 "),
    m("G12-M37 a cut bracket at the end of a token is not declined", '    if full[end : end + 1] == "\\u203a" and _TOKEN_BODY_END.search(core):\n', "    if False:\n", LK + "[hunter22\\u2039SECRET_1\\u203a]", "G12-22 "),
    m("G12-M38 a stray bracket before a core declines it", '    if full[start - 1 : start] == "\\u2039" and _TOKEN_BODY_START.match(core):\n', '    if full[start - 1 : start] == "\\u2039":\n', "test_g12_one_stray_lookalike_bracket_keeps_the_core[\\u2039hunter22,]", "G12-28 "),
    m("G12-M24 any look-alike bracket declines the core", '    if core.lower() in _NOT_A_VALUE or not re.search(r"[^\\W_]", _ANY_TOKEN.sub("", full)):\n', '    if core.lower() in _NOT_A_VALUE or "\\u2039" in full or "\\u203a" in full:\n', "test_g12_an_interior_lookalike_bracket_keeps_the_core_of_the_value", "G12-21 "),
    m("G12-M25 a large core is never registered", "    return redactor._map_chars + len(core) > _CORE_BUDGET\n", "    return True\n", "test_g12_a_large_value_gets_a_core_unless_it_would_push_the_map_past_half_its_cap", "G12-26 "),
    m("G12-M39 a large core is always registered", "    return redactor._map_chars + len(core) > _CORE_BUDGET\n", "    return False\n", "test_g12_a_large_value_gets_a_core_unless_it_would_push_the_map_past_half_its_cap", "G12-26 "),
    m("G12-M40 the sweep does not skip look-alikes", '                if "\\u2039" in segment and "\\u2039" not in original and "\\u203a" not in original:\n', "                if False:\n", "test_g12_a_core_that_is_the_tail_of_a_real_label_never_corrupts_an_escaped_lookalike", "G12-30 "),
    m("G12-M41 the sweep skips the look-alike that is the value", "                and (inner != original or _issued(label, number, self.counters))\n", "                and True\n", "test_g12_a_lookalike_that_is_the_value_itself_is_swept", "G12-31 "),
    m("G12-M42 the close search is tried for every last character", '        elif (last in ";>%" or last.isalnum()) and (\n', "        elif True and (\n", "test_g12_a_run_of_non_edge_characters_does_not_search_for_a_close_form", "G12-33 "),
    m("G12-M36 a self-closing tag at the end is kept", EF, EF.replace(" {0,3}/?>", ">"), "test_g12_the_end_of_value_unlisted_tag_is_stripped_by_the_whole_form", "G12-32 "),
    m("G12-M16 the core is cut from the written value", C, C.replace("_bare_span(full)", "_bare_span(original)"), "test_g12_the_core_of_a_value_holding_a_placeholder_is_cut_from_the_resolved_value", "G12-16 "),
    m("G12-M17 the core is registered twice over", I, "        if core != full and len(core) >= 3 and core not in self.reverse:\n            self.reverse[core + ' '] = full\n            self.mapping['<SECRET_x>'] = full\n", "test_g12_a_value_takes_one_extra_entry_besides_its_own", "G12-15 "),
    # G12e: the label-built `_ANY_TOKEN`, the running map count, the canonical counter, the look-alikes without the original
    m("G12e-M43 a cut-off opener of any caps word declines the core", "{_LABEL_CUTS})(?=", "{_LABEL_CUTS}|[A-Z][A-Z0-9]*)(?=", E1 + "[password=<HUNTER2, HUNTER2-HUNTER2]", "G12e-1 "),
    m("G12e-M44 the escaped look-alike of any caps word declines the core", "\\u2039(?:{_LABEL_ALT})_[0-9]+\\u203a", "\\u2039[A-Z][A-Z0-9]*_[0-9]+\\u203a", E1 + "[password=\\u2039ADMIN_1\\u203a then ADMIN_1-ADMIN_1]", "G12e-1 "),
    m("G12e-M45 an opener needs no end or separator", "(?=[ \\t;,]|\\\\Z)", "", "test_g12e_the_any_token_alternatives_are_the_real_labels", "G12e-3 "),
    m("G12e-M46 a leading-zero number counts as issued", '        and f"{label}_{int(number)}" == f"{label}_{number}"\n', "", E1 + "[password=SECRET_001, SECRET_001-SECRET_001]", "G12e-1 "),
    m("G12e-M47 the running map count ignores a core", "            self._map_chars += len(core)\n", "            pass\n", "test_g12e_many_values_just_under_the_old_floor_cannot_double_the_map", "G12e-2 "),
    m("G12e-M48 a rollback keeps the count", '                self._map_chars -= len(self.mapping.pop(a, ""))\n', '                self.mapping.pop(a, "")\n', "test_g12e_the_running_map_count_follows_every_add_and_rollback", "G12e-5 "),
    m("G12e-M49 the budget is the 4,096 floor again", "    return redactor._map_chars + len(core) > _CORE_BUDGET\n", "    return len(core) >= 4096 and redactor._map_chars + len(core) > _CORE_BUDGET\n", "test_g12e_many_values_just_under_the_old_floor_cannot_double_the_map", "G12e-2 "),
    m("G12e-M50 every real look-alike is kept", "                original in inner\n                and label in self.counters\n", "                label in self.counters\n", "test_g12e_lookalikes_without_the_original_cost_one_replace_call", "G12e-4 "),
    m("G12e-M51 a real label beyond the counter is declined", "        and int(number) <= counters.get(label, 0)\n", "        and True\n", "test_g12e_a_real_label_beyond_the_counter_keeps_its_core[password=EMAIL_2024. EMAIL_2024]", "G12e-6 "),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    first_lines: dict[str, str] = {}
    res = run_mutants(
        ROOT,
        M,
        [TEST, "tests/__init__.py", "tests/conftest.py"],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
