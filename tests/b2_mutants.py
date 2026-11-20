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

GATE = "src/hadavin_sdk/guard/model_gate.py"
RESERVE = "        return self._meter.reserve(*args, run_id=run_id)\n"
SETTLE = "            return self._meter.settle(reservation_id, actual_usd)\n"
FALLBACK = "                self.store.add_cost(run.run_id, cost_usd)\n"
KILL = '    "kill_switch": (S.STOPPED, "kill_switch"),\n'
ENDED_ON_ERROR = "                if run_meter.ended is not None:  # the settle at 0 failed: the run is already over\n"
ENDED_AFTER = "            if (\n                run_meter.ended is not None\n            ):  # the settle failed and the run could not go on (`_RunMeter`)\n"

M = [
    # F-install: the reserve now lives in the gate, reached through `_RunMeter.reserve`. Removed: the model is
    # called with no booking (and the settle has no id to settle)
    Mutant(
        "B2-1 gate reserve removed",
        LOOP,
        RESERVE,
        '        return "res-none"\n',
        "assert",
        test_file=T,
    ),
    # settle removed: the hold stays at the worst case, the day total is the worst case, not the cost
    Mutant(
        "B2-2 settle removed",
        LOOP,
        SETTLE,
        "            return 0\n",
        "assert",
        test_file=T,
    ),
    # settle on a provider error that was NOT marked refused before any response: lowers the hold to 0 although
    # the provider may have billed (the rule lives in the gate, rule (b))
    Mutant(
        "B2-3 settle on provider error",
        GATE,
        "            if refused_before_response(exc):  # rule (b): it cost nothing\n",
        "            if True:  # rule (b): it cost nothing\n",
        "assert",
        test_file=T,
    ),
    # the definite-refusal fallback removed: the run cost is never booked
    Mutant(
        "B2-4 settle fallback removed",
        LOOP,
        FALLBACK,
        "                pass\n",
        "assert",
        test_file=T,
    ),
    # the fallback also runs on an ambiguous failure: the run cost is double counted
    Mutant(
        "B2-5 fallback on ambiguous failure",
        LOOP,
        "        ambiguous = is_connectivity_error(exc)\n",
        "        ambiguous = False\n",
        "assert",
        test_file=T,
    ),
    # only ValueError / NotFound count as definite: a RuntimeError rollback loses the run cost
    Mutant(
        "B2-7 definite set too small",
        LOOP,
        "        ambiguous = is_connectivity_error(exc)\n",
        "        ambiguous = not isinstance(exc, (ValueError, NotFound))\n",
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
        '    "kill_switch": (S.NEEDS_PERSON, "kill_switch"),\n',
        "assert",
        test_file=T,
    ),
    # `_RunMeter` no longer applies the loop's rule for a failed settle (neither the direct run-cost booking nor
    # the end of the run)
    Mutant(
        "B2-9 _RunMeter fallback removed",
        LOOP,
        "            ended = self._rt._settle_failed(self._run, exc, actual_usd)\n",
        "            ended = None\n",
        "assert",
        test_file=T,
    ),
    # review M1: the ProviderError branch ignores the ended run: IllegalTransition escapes handle()
    Mutant(
        "B2-10 ended check removed on the provider error branch",
        LOOP,
        ENDED_ON_ERROR,
        "                if False:\n",
        "refused",  # the chained provider error leads the first E line; IllegalTransition follows
        allow_crash=True,
        crash_type="ProviderError",
        test_file=T,
    ),
    # the ended check after a reply removed: the run goes on after it was ended
    Mutant(
        "B2-11 ended check removed after the reply",
        LOOP,
        ENDED_AFTER,
        "            if False:\n",
        "IllegalTransition",
        allow_crash=True,
        crash_type="IllegalTransition",
        test_file=T,
    ),
    # review m2: a judge settle that ended the run is not noticed after the screen
    Mutant(
        "B2-12 ended check removed after the screen",
        LOOP,
        "        if meter.ended is not None:\n            raise _RunEnded(meter.ended)\n        return verdict\n",
        "        return verdict\n",
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
