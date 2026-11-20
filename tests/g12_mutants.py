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
C = "        core = full.rstrip(_TRAIL) if derived and label in SECRET_KINDS else full\n"
I = "        if core != full and len(core) >= 3 and core not in self.reverse:\n"
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


MARK = "test_g12_a_trailing_mark_does_not_leave_the_clear_copy"
M = [
    m("G12-M1 the core is never registered", I, "        if False:\n", MARK + "[,]", "G12-1 "),
    m("G12-M2 only a comma is trailing", '_TRAIL = ".,;:!?)]}"', '_TRAIL = ","', MARK + "[.]", "G12-1 "),
    m("G12-M3 a held core gets a second placeholder", I, "        if core != full and len(core) >= 3:\n", "test_g12_a_core_the_map_holds_gets_no_second_placeholder", "G12-9 "),
    m("G12-M4 the core is not journaled", J, "                pass\n", "test_g12_a_rolled_back_value_takes_its_core_with_it", "G12-10 "),
    m("G12-M5 the floor is 4", I, I.replace(">= 3", ">= 4"), "test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma", "G12-8 "),
    m("G12-M6 identifier kinds get a core", C, "        core = full.rstrip(_TRAIL) if derived else full\n", "test_g12_identifier_kinds_are_unchanged", "G12-11 "),
    m("G12-M7 a G9 union gets a core", C, C.replace("derived and ", ""), "test_g12_a_g9_union_registers_its_value_only_and_no_core", "G12-12 "),
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
