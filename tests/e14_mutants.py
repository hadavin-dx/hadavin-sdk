"""The mutants of ticket E14 (finder memory cap), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must hold
``expect`` (``E14-Tn `` the id of the assertion message and a space). Every ``old`` occurs exactly once in the ruff-formatted file.
Run from the repo root:

    python tests/e14_mutants.py          # all mutants; exit 1 if any is not good
    python tests/e14_mutants.py E14-4    # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
RD = "src/hadavin_sdk/guard/redact.py"
AL = "src/hadavin_sdk/runtime/agent_loop.py"
CF = "src/hadavin_sdk/config.py"
DF = "src/hadavin_sdk/defaults.py"
TEST = "tests/test_redact_finder_cap.py"
PIN = "tests/test_redact_finder_cap::"


def m(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


DOC_OLD = "            len(rmap) > self._evidence.max_map_entries  # too many distinct values to redact cheaply\n            or _map_chars(rmap) > self._evidence.max_map_chars\n"
DOC_NEW = "            len(rmap) > self._evidence.max_map_entries  # too many distinct values to redact cheaply\n"
TOOL_OLD = "                    or _map_chars(rmap) > self._evidence.max_map_chars  # tool result\n"
DOC_GE = (
    "or _map_chars(rmap) > self._evidence.max_map_chars\n",
    "or _map_chars(rmap) >= self._evidence.max_map_chars\n",
)
TOOL_GE = (
    "or _map_chars(rmap) > self._evidence.max_map_chars  # tool result\n",
    "or _map_chars(rmap) >= self._evidence.max_map_chars  # tool result\n",
)

M = [
    m("E14-1 the first trie has no limit", RD, "_trie(self._rules, limit=defaults.MAX_FINDER_CHARS)", "_trie(self._rules)", "test_t1_a_build_over_the_cap_is_refused", "E14-T1 "),
    m("E14-2 the cap refuses at equality", RD, "if held > limit:", "if held >= limit:", "test_t2_the_boundary_is_the_constant", "E14-T2 "),
    m("E14-3 characters counted, not nodes", RD, "held += _new_nodes(root, w)", "held += len(w)", "test_t3_nodes_not_characters", "E14-T3 "),
    m("E14-4 the document check reads entries only", AL, DOC_OLD, DOC_NEW, "test_t6_document_path_boundary", "E14-T6 "),
    m("E14-5 the tool check reads entries only", AL, TOOL_OLD, "", "test_t7_tool_path_boundary", "E14-T7 "),
    m("E14-6 the map is counted in entries", AL, "return sum(map(len, set(rmap.values())))", "return len(rmap)", "test_t6_document_path_boundary", "E14-T6 "),
    m("E14-7 the config has no upper bound", CF, "gt=0, le=defaults.MAX_FINDER_CHARS)", "gt=0)", "test_t8_config", "E14-T8 "),
    m("E14-9 the document check refuses at equality", AL, *DOC_GE, "test_t6_document_path_boundary", "E14-T6 "),
    m("E14-10 the tool check refuses at equality", AL, *TOOL_GE, "test_t7_tool_path_boundary", "E14-T7 "),
    m("E14-8 the defaults drift", DF, "MAX_MAP_CHARS = 2 * MAX_REDACT_CHARS", "MAX_MAP_CHARS = 4 * MAX_REDACT_CHARS", "test_t9_derivation_pin", "E14-T9 "),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    first_lines: dict[str, str] = {}

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
        [TEST, "tests/k5_support.py", "tests/__init__.py", "tests/conftest.py"],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
