"""The mutants of ticket G12 (trailing prose punctuation of a SECRET value), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must hold
``expect`` (the ``G12-n `` start of the assertion message). Run from the repo root:

    python tests/g12_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g12_mutants.py G12-M3     # only mutants whose name contains the text

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
ESC = r'_EDGE_CLOSE = re.compile(r"(?:</[A-Za-z][A-Za-z0-9]{0,15}>|\\[nrt])\Z")' + "\n"
EXEMPT = "            _bare(original).lower() in _NOT_A_VALUE or"
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
M = [
    m("G12-M1 the core is never registered", I, "        if False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M2 only a comma is trailing", TAIL, "        elif text[end - 1] == \",\":\n", MARK + "[.]", "G12-1 "),
    m("G12-M3 a held core gets a second placeholder", I, "        if core != full and len(core) >= 3:\n", "test_g12_a_core_the_map_holds_gets_no_second_placeholder", "G12-9 "),
    m("G12-M4 the core is not journaled", J, "                pass\n", "test_g12_a_rolled_back_value_takes_its_core_with_it", "G12-10 "),
    m("G12-M5 the floor is 4", I, I.replace(">= 3", ">= 4"), "test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma", "G12-8 "),
    m("G12-M6 identifier kinds get a core", C, "        core = _bare(full) if derived else full\n", "test_g12_identifier_kinds_are_unchanged", "G12-11 "),
    m("G12-M7 a G9 union gets a core", C, C.replace("derived and ", ""), "test_g12_a_g9_union_registers_its_value_only_and_no_core", "G12-12 "),
    # G12b: the one edge rule (`_bare`), its halves, and the words the exemption shares it with
    m("G12-M8 the leading half is off", HEAD, "        elif False:\n", WRAP + "[11]", "G12-14 "),
    m("G12-M9 the trailing half is off", TAIL, "        elif False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M10 the trailing half is ASCII only", TAIL, "        elif text[end - 1].isascii() and not text[end - 1].isalnum():\n", WRAP + "[6]", "G12-14 "),
    m("G12-M11 the leading half is ASCII only", HEAD, "        elif text[start].isascii() and not text[start].isalnum():\n", WRAP + "[9]", "G12-14 "),
    m("G12-M12 a closing tag is kept", CLOSE, "        elif False:\n", WRAP + "[2]", "G12-14 "),
    m("G12-M13 an opening tag is kept", OPEN, "        if False:\n", WRAP + "[3]", "G12-14 "),
    m("G12-M14 an escaped newline is kept", ESC, ESC.replace("|\\\\[nrt]", ""), WRAP + "[10]", "G12-14 "),
    m("G12-M15 the exemption strips the old narrow set", EXEMPT, '            original.lower().strip(".,;:)(<>") in _NOT_A_VALUE or', "test_g12_a_word_that_says_there_is_no_value_is_exempt_with_its_punctuation_too[!-none]", "G12-13 "),
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
