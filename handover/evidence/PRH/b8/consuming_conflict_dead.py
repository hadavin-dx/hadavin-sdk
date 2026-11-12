"""PR H batch 8, Issue 2: can the call `compare_readings(set(values), {new_map values})` in `runmap._consuming_wins` ever
answer "conflict" or "first"? This script puts a recording wrapper around `_consuming_wins` that computes the answer of that
call exactly as the code at 5f9df48e computed it, over the builder's 3000-text fuzz (`fuzz_classify.texts`), the runner's
3096 texts (`own_fuzz.cases`) and the 600 seeded texts of `tests/test_prh_steps.py`, on the untrusted and the tool path, and
counts the answers. Run from the repository root:
    PYTHONPATH=src:. python handover/evidence/PRH/b8/consuming_conflict_dead.py
"""

import collections
import importlib.util
import sys
from pathlib import Path

import hadavin_sdk.guard  # noqa: F401
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap

R = sys.modules["hadavin_sdk.guard.redact"]
HERE = Path(__file__).resolve().parent
EVID = HERE.parent
sys.path.insert(0, str(HERE.parents[3]))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(mod)
    return mod


answers = collections.Counter()
calls = [0]
orig = runmap._consuming_wins


def wrapper(shown, new_map, known, *a, **k):
    values = [v for v in known.values() if not v.startswith("\0seed")]
    calls[0] += 1
    answers[
        R.compare_readings(set(values), {v for v in new_map.values() if not v.startswith("\0seed")})
    ] += 1
    return orig(shown, new_map, known, *a, **k)


runmap._consuming_wins = wrapper
fz = load(EVID / "b7" / "fuzz_classify.py", "fz")
for t in fz.texts(3000):
    try:
        tools.prepare_output(t, {}, 4000, [fz.HAND])
    except runmap.RedactionError:
        pass
src = (HERE / "runner_own_fuzz.py").read_text().replace("\nmain()", "\n")
ns: dict = {}
exec(compile(src, "own_fuzz", "exec"), ns)  # noqa: S102 - the evidence runner's own script, read as text
for _name, _s, t in ns["cases"]():
    try:
        tools.prepare_output(t, {}, 4000, [ns["HAND"]])
    except runmap.RedactionError:
        pass
from tests import test_prh_steps as steps  # noqa: E402
from tests.test_prh_spans import Gen  # noqa: E402

for seed in range(steps.SEARCH_TEXTS):
    try:
        runmap.redact_untrusted(steps._seeded_text(Gen(seed)), {})
    except runmap.RedactionError:
        pass
print(f"_consuming_wins calls that reached the compare: {calls[0]}; answers of compare_readings: {dict(answers)}")
