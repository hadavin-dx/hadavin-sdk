"""The mutants of ticket G12 (trailing prose punctuation of a SECRET value), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must hold
``expect`` (the ``G12-n `` start of the assertion message). Run from the repo root:

    python tests/g12_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g12_mutants.py G12-M3     # only mutants whose name contains the text

EQUIVALENT, not listed (G12c): at the END the entity `&#10;`, the self-closing `/>` and `<br/>` are also stripped by the pieces the other forms leave (`;` `>` `/` are not
alphanumeric, then `&#10` / `<br` are cut-short forms); only at the START do the whole forms matter (M29, M30 use the start test).
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
C = "        core = _bare(full) if derived and label in SECRET_KINDS else full\n"
I = "        if core != full and len(core) >= 3 and core not in self.reverse:\n"
HEAD = "        elif not text[start].isalnum():\n"
TAIL = "        elif not text[end - 1].isalnum():\n"
CLOSE = "        elif (m := _EDGE_CLOSE.search(text, max(start, end - 64), end)) is not None:\n"
OPEN = "        if (m := _EDGE_OPEN.match(text, start, end)) is not None:\n"
NOVAL = "            core.lower() in _NOT_A_VALUE\n"
PHLIKE = "            or _placeholder_like(core, full)\n"
LOOK = "            or _LOOKALIKE.search(full) is not None\n"
CUT = "            or _cut_a_lookalike_bracket(full, core)\n"
BOTH = "    if opened and closed:\n"
OPENED = "    return opened and _CAPS_BODY.fullmatch(core) is not None\n"
BIG = "            or (len(full) > _CORE_BIG and len(full) - len(core) <= _CORE_DELTA)\n"
FULLM = "    return _LABEL_TEXT.fullmatch(core) is not None or (\n"
PREFIX = '        f"<{core}" in full and any(f"{label}_".startswith(core) for label in _LABELS)\n'
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
LK = "test_g12_a_value_with_a_lookalike_token_or_its_cut_brackets_gets_no_core"
EDGE = "test_g12_an_escaped_or_encoded_edge_does_not_leave_the_clear_copy"
START = "test_g12_an_escaped_or_encoded_edge_at_the_start_does_not_leave_the_clear_copy"
M = [
    m("G12-M1 the core is never registered", I, "        if False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M2 only a comma is trailing", TAIL, "        elif text[end - 1] == \",\":\n", MARK + "[.]", "G12-1 "),
    m("G12-M3 a held core gets a second placeholder", I, "        if core != full and len(core) >= 3:\n", "test_g12_a_core_the_map_holds_gets_no_second_placeholder", "G12-9 "),
    m("G12-M4 the core is not journaled", J, "                pass\n", "test_g12_a_rolled_back_value_takes_its_core_with_it", "G12-10 "),
    m("G12-M5 the floor is 4", I, I.replace(">= 3", ">= 4"), "test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma", "G12-8 "),
    m("G12-M6 identifier kinds get a core", C, "        core = _bare(full) if derived else full\n", "test_g12_identifier_kinds_are_unchanged", "G12-11 "),
    m("G12-M7 a G9 union gets a core", C, C.replace("derived and ", ""), "test_g12_a_g9_union_registers_its_value_only_and_no_core", "G12-12 "),
    # G12b: the one edge rule (`_bare`), its halves, and the words the exemption shares it with
    m("G12-M8 the leading half is off", HEAD, "        elif False:\n", WRAP + "[9]", "G12-14 "),
    m("G12-M9 the trailing half is off", TAIL, "        elif False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M10 the trailing half is ASCII only", TAIL, "        elif text[end - 1].isascii() and not text[end - 1].isalnum():\n", WRAP + "[6]", "G12-14 "),
    m("G12-M11 the leading half is ASCII only", HEAD, "        elif text[start].isascii() and not text[start].isalnum():\n", WRAP + "[9]", "G12-14 "),
    m("G12-M12 a closing tag is kept", CLOSE, "        elif False:\n", WRAP + "[2]", "G12-14 "),
    m("G12-M13 an opening tag is kept", OPEN, "        if False:\n", WRAP + "[3]", "G12-14 "),
    m("G12-M14 an escaped newline is kept", EF, EF.replace(r"|\\[nrt]", ""), WRAP + "[10]", "G12-14 "),
    m("G12-M15 a no-value core is registered", NOVAL, "            False\n", "test_g12_the_second_none_is_neither_masked_nor_swept", "G12-13 "),
    m("G12-M18 a placeholder-like core is registered", PHLIKE, "", PH + "[<EMA]", "G12-18 "),
    # G12c: the placeholder-like rule, the look-alike guard, the large value, the new edge forms
    m("G12-M19 only the label-prefix rule declines", FULLM, "    return (\n", "test_g12_a_value_that_is_a_placeholders_text_keeps_the_real_placeholders_intact", "G12-20 "),
    m("G12-M20 any all-caps NAME_n is a placeholder", FULLM, '    return re.fullmatch(r"[A-Z][A-Z0-9]*_[0-9]+", core) is not None or (\n', CAPS + "[password=ADMIN_1, ADMIN_1-ADMIN_1]", "G12-19 "),
    m("G12-M21 any label prefix declines the core", PREFIX, '        any(f"{label}_".startswith(core) for label in _LABELS)\n', CAPS + "[password=HOST, HOST-HOST]", "G12-19 "),
    m("G12-M22 the look-alike token guard is gone", LOOK, "", "test_g12_a_value_with_a_lookalike_token_or_its_cut_brackets_gets_no_core[12\\u2039EMAIL_1\\u203a34,]", "G12-22 "),
    m("G12-M23 the cut-bracket guard is gone", CUT, "", LK + "[\\u2039SECRET_x\\u203a]", "G12-22 "),
    m("G12-M33 a value wrapped in look-alike brackets gets a core", BOTH, "    if False:\n", LK + "[\\u2039hunter2zz\\u203a]", "G12-22 "),
    m("G12-M34 a cut-off look-alike body gets a core", OPENED, "    return False\n", LK + "[\\u2039SECRET_x]", "G12-22 "),
    m("G12-M35 one stray bracket drops the core", CUT, "            or _cut_a_lookalike_bracket(full, core)\n            or \"\u2039\" in full\n            or \"\u203a\" in full\n", "test_g12_one_stray_lookalike_bracket_keeps_the_core[hunter22!\\u203a]", "G12-28 "),
    m("G12-M24 any look-alike bracket declines the core", LOOK, '            or "\\u2039" in full\n            or "\\u203a" in full\n', "test_g12_an_interior_lookalike_bracket_keeps_the_core_of_the_value", "G12-21 "),
    m("G12-M25 a large value gets a core", BIG, "", "test_g12_a_large_value_whose_core_differs_by_a_few_characters_gets_no_core", "G12-26 "),
    m("G12-M26 a percent escape is kept", EF, EF.replace("|%[0-9A-Fa-f]{2}", ""), EDGE + "[%0A]", "G12-23 "),
    m("G12-M27 a JSON unicode escape is kept", EF, EF.replace(r"|\\u[0-9A-Fa-f]{4}", ""), EDGE + r"[\\u000a]", "G12-23 "),
    m("G12-M28 a hex escape is kept", EF, EF.replace(r"|\\x[0-9A-Fa-f]{2}", ""), EDGE + r"[\\x0a]", "G12-23 "),
    m("G12-M29 an entity is kept", EF, EF.replace("|&(?:#[0-9]{1,7}|[A-Za-z]{2,10});", ""), START + "[&#10;]", "G12-24 "),
    m("G12-M30 a self-closing tag is kept", EF, EF.replace(" {0,3}/?>", ">"), START + "[<br/>]", "G12-24 "),
    m("G12-M31 a cut-short tag is kept", CUTSHORT, CUTSHORT.replace("<(?:br|hr|b|i|p|a|li|tr|td|div|span)|", ""), EDGE + "[<br />]", "G12-23 "),
    m("G12-M32 a cut-short entity is kept", CUTSHORT, CUTSHORT.replace("|&(?:#[0-9]{{1,7}}|quot|amp|lt|gt|nbsp|apos)", ""), EDGE + "[&quot;]", "G12-23 "),
    m("G12-M16 the core is cut from the written value", C, C.replace("_bare(full)", "_bare(original)"), "test_g12_the_core_of_a_value_holding_a_placeholder_is_cut_from_the_resolved_value", "G12-16 "),
    m("G12-M17 the core is registered twice over", I, "        if core != full and len(core) >= 3 and core not in self.reverse:\n            self.reverse[core + ' '] = full\n            self.mapping['<SECRET_x>'] = full\n", "test_g12_a_value_takes_at_most_two_entries", "G12-15 "),
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
