"""Mutants of the live-path reserve/settle (builder B2). Each reverts ONE part of src/hadavin_sdk/runtime/agent_loop.py;
tests/test_live_path_reserve_settle.py must fail. Not collected by pytest.

    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/b2_mutants.py

(without a DSN only the memory-store cases run; the kills still hold). Ends with ``N of N good; problems: [...]``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
LOOP = "src/hadavin_sdk/runtime/agent_loop.py"
T = "tests/test_live_path_reserve_settle.py"

RESERVE = "                rid = self.limits.reserve(run.agent_id, worst, run_id=run.run_id)\n"
SETTLE = "            self.limits.settle_for(run.agent_id, rid, cost_usd)\n"
ERR = '                self._note(run, "llm", "chat", result="failed", error_code=code)\n'

FALLBACK = "                    self.store.add_cost(run.run_id, cost_usd)\n"
KILL = '                    return self._to(run, S.STOPPED, "kill_switch")\n'

M = [
    # reserve removed: the model is called with no booking (and the settle has no id to settle)
    Mutant(
        "B2-1 reserve removed",
        LOOP,
        RESERVE,
        '                rid = "res-none"\n',
        "assert",
        test_file=T,
    ),
    # settle removed: the hold stays at the worst case, the day total is the worst case, not the cost
    Mutant(
        "B2-2 settle removed",
        LOOP,
        SETTLE,
        "            pass\n",
        "assert",
        test_file=T,
    ),
    # settle on a provider error: lowers the hold to 0 although the provider may have billed
    Mutant(
        "B2-3 settle on provider error",
        LOOP,
        ERR,
        ERR + "                self._settle_model_call(run, rid, 0)\n",
        "quota",  # the first E line is the chained provider error; the assertion on spy.settles follows
        allow_crash=True,
        crash_type="ProviderExhausted",
        test_file=T,
    ),
    # the definite-refusal fallback removed: the run cost is never booked
    Mutant(
        "B2-4 settle fallback removed",
        LOOP,
        FALLBACK,
        "                    pass\n",
        "assert",
        test_file=T,
    ),
    # the fallback also runs on an ambiguous failure: the run cost is double counted
    Mutant(
        "B2-5 fallback on ambiguous failure",
        LOOP,
        "            ambiguous = is_connectivity_error(exc)\n",
        "            ambiguous = False\n",
        "assert",
        test_file=T,
    ),
    # only ValueError / NotFound count as definite: a RuntimeError rollback loses the run cost
    Mutant(
        "B2-7 definite set too small",
        LOOP,
        "            ambiguous = is_connectivity_error(exc)\n",
        "            ambiguous = not isinstance(exc, (ValueError, NotFound))\n",
        "assert",
        test_file=T,
    ),
    # the method raises when the run cannot be ended
    Mutant(
        "B2-8 settle helper raises",
        LOOP,
        "            return run\n\n    def _to(",
        "            raise\n\n    def _to(",
        "RuntimeError",
        allow_crash=True,
        crash_type="RuntimeError",
        test_file=T,
    ),
    # kill switch at reserve mapped to NEEDS_PERSON
    Mutant(
        "B2-6 kill switch at reserve not STOPPED",
        LOOP,
        KILL,
        '                    return self._to(run, S.NEEDS_PERSON, "kill_switch")\n',
        "assert",
        test_file=T,
    ),
]

if __name__ == "__main__":
    fl = {}
    res = run_mutants(ROOT, M, [T], extra_dirs=("tests", "tools"), timeout=300, first_lines=fl)
    bad = [n for n, _, _, g in res if not g]
    for n, v, tid, g in res:
        print(f"{'ok ' if g else 'BAD'} {v}  {n}  [{tid.split('::')[-1][:90]}]")
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
