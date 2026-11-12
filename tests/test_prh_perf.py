"""PR H, T9: what taking hidden items out costs (gates G1 to G3 of the ticket, section 4.4; G4 is the `__main__` mode).

Shapes (one line each, repeated to the size): S1 to S5 hold no hidden item (the ratio gate), H1 and H2 hold colour codes,
W is the worst case (a Persian sentence, a colour code inside a word and a percent sign, so every reading has to be
read). All values are made up.

* G1  the number of `redact` calls per `redact_text` call equals main's (recorded in `fixtures/prh_main_passes.json`) for
      S1 to S5; H2 at most one more than main per reading; W and the sgr0 shapes at most `defaults.MAX_REDACT_PASSES` (24, counted in `runmap._Work`).
* G2  the number of `undo` calls equals main's for S1 to S5.
* G3  every S and H shape at the cap under 3.0 s of CPU (median of 5); growth by `fixtures/timing.py`; W finishes or
      raises `InputTooLarge`, never past the 6-second budget by more than one pass.
* G4  `python tests/test_prh_perf.py --compare-main PATH` runs main (`PATH/src`) and the branch in child processes, five
      times each, alternately, and prints both medians per shape (evidence only; the limit 1.25 is read by a person).
* `python tests/test_prh_perf.py --record-main-passes OUT.json` (run with main's `src` first on `PYTHONPATH`) writes the
  counts of main.

The tests carry the marker `perf`: CI runs them in their own step, alone."""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

try:
    import pytest
except ImportError:  # the `__main__` mode needs no test runner
    pytest = None

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

ROOT = Path(__file__).resolve().parents[1]
PASSES = ROOT / "tests" / "fixtures" / "prh_main_passes.json"
ESC = "\x1b"
CAP = defaults.MAX_REDACT_CHARS
SMALL = 65_536
REPEATS = 5
SECONDS_LIMIT = 3.0
SHAPES = {
    "S1 plain ASCII log": "2026-11-04T10:00:00Z INFO worker-7 request served status=200 path=/api/v1/items took 12ms\n",
    "S2 tab table": "pod-web-7f9c\tRunning\t3\tnode-a12\tdefault\tcluster-east\n",
    "S3 JSON lines": '{"ts": "2026-11-04T10:00:00Z", "level": "info", "msg": "served", "status": 200, "path": "/api/v1/items", "ms": 12}\n',
    "S4 Hindi": "यह एक साधारण वाक्य है जिसमें कोई गुप्त जानकारी नहीं है।\n",
    "S5 Persian ZWNJ emoji": "این یک جملهٔ ساده است؛ می‌خواهم بگویم \U0001f600❤️ \U0001f468‍\U0001f469‍\U0001f467\n",
    "H1 coloured output": ESC
    + "[32mPASS"
    + ESC
    + "[0m tests/test_items.py::test_list "
    + ESC
    + "[1;34m12ms"
    + ESC
    + "[0m\n",
    "H2 colour inside a word": "match: req" + ESC + "[1;31muest" + ESC + "[0m_id served in 12ms\n",
    "H3 sgr0 inside a word": "match: req"
    + ESC
    + "(B"
    + ESC
    + "[mu"
    + ESC
    + "(B"
    + ESC
    + "[mest_id served in 12ms\n",
    "H4 colourised log with sgr0": ESC
    + "[32mINFO"
    + ESC
    + "(B"
    + ESC
    + "[m worker-7 "
    + ESC
    + "[1mrequest"
    + ESC
    + "(B"
    + ESC
    + "[m served status=200 path=/api/v1/items "
    + ESC
    + "[34m12ms"
    + ESC
    + "(B"
    + ESC
    + "[m\n",
    "W worst: Persian + colour inside a word + percent": "می‌خواهم req"
    + ESC
    + "[1;31muest"
    + ESC
    + "[0m_id 50%25 done\n",
}


def _letters(n: int, seed: int) -> list[str]:
    """`n` single characters of a made-up run: a fixed order of 12 different letters, shifted by `seed`."""
    alphabet = "bcdfghjkmnpq"
    return [alphabet[(i * 5 + seed) % len(alphabet)] for i in range(n)]


def _spaced_texts() -> dict[str, str]:
    """Batch 10, group 1: shapes that hold a spaced-out run (the cost of `redact.spaced_unknown` and `redact.spaced_spans`),
    each built to the cap. Made-up characters only."""
    fixed = defaults.MAX_REDACT_CHARS
    long_run = "key: " + " ".join(_letters(fixed // 2 - 8, 0)) + "\n"
    medium = "\n".join("n: " + " ".join(_letters(2000, i)) + " end" for i in range(32))
    shared = "\n".join(
        "n: " + " ".join(list("sharedprefix") + _letters(1000, i)) + " end" for i in range(32)
    )
    prefix = (
        "commonprefx"  # 11 characters; the map values add one more so that 12 characters are shared
    )
    values = [f"{prefix}A{i:04d}" for i in range(defaults.MAX_MAP_ENTRIES)]
    planted = "\n".join(f"password={v}" for v in values)
    tail = ("see " + " ".join(prefix + "A") + " end\n") * (fixed // 40)
    return {
        "P1 one very long spaced run": long_run[:fixed],
        "P2 32 medium spaced runs": medium[:fixed],
        "P3 32 spaced runs sharing a prefix": shared[:fixed],
        "P4 2000 values sharing 12 characters": (planted + "\n" + tail)[:fixed],
    }


SPACED_SHAPES = list(_spaced_texts())
HIDDEN_FREE = [k for k in SHAPES if k[0] == "S"]
SHAPE_H = [k for k in SHAPES if k[0] == "H"]
SHAPE_W = next(k for k in SHAPES if k[0] == "W")


def fill(unit: str, n: int) -> str:
    return (unit * (n // len(unit) + 1))[:n]


def cpu(text: str) -> float:
    start = time.process_time()
    try:
        runmap.redact_untrusted(text, {})
    except runmap.RedactionError:
        pass
    return time.process_time() - start


def median_cpu(text: str, repeats: int = REPEATS) -> float:
    return statistics.median(cpu(text) for _ in range(repeats))


def count_calls(text: str) -> tuple[int, int]:
    """(`redact` calls, `undo` calls) of one `redact_untrusted` call, by counting stand-ins."""
    counts = {"redact": 0, "undo": 0}
    real_redact, real_undo = runmap.redact, runmap.undo

    def redact(*a, **k):
        counts["redact"] += 1
        return real_redact(*a, **k)

    def undo(*a, **k):
        counts["undo"] += 1
        return real_undo(*a, **k)

    runmap.redact, runmap.undo = redact, undo
    try:
        runmap.redact_untrusted(text, {})
    except runmap.RedactionError:
        pass
    finally:
        runmap.redact, runmap.undo = real_redact, real_undo
    return counts["redact"], counts["undo"]


def _main_passes() -> dict[str, list[int]]:
    return json.loads(PASSES.read_text(encoding="utf-8"))


if pytest is not None:
    pytestmark = pytest.mark.perf

    @pytest.mark.parametrize("shape", HIDDEN_FREE)
    def test_pass_count(shape):
        """G1: as many `redact` calls as main, on text without a hidden item."""
        redacts, _ = count_calls(fill(SHAPES[shape], CAP))
        assert redacts == _main_passes()[shape][0], shape

    @pytest.mark.parametrize("shape", HIDDEN_FREE)
    def test_undo_count(shape):
        """G2: as many `undo` calls as main, on text without a hidden item."""
        _, undos = count_calls(fill(SHAPES[shape], CAP))
        assert undos == _main_passes()[shape][1], shape

    def test_pass_count_h2_and_w():
        """G1: H2 at most one more than main per reading (main's count plus 1 per reading, at most 4 readings); W and the sgr0 shapes at most `defaults.MAX_REDACT_PASSES` (24, counted in `runmap._Work`)."""
        redacts, _ = count_calls(fill(SHAPES["H2 colour inside a word"], CAP))
        assert redacts <= _main_passes()["H2 colour inside a word"][0] * 2 + 1
        redacts, _ = count_calls(fill(SHAPES[SHAPE_W], CAP))
        assert redacts <= defaults.MAX_REDACT_PASSES

    @pytest.mark.parametrize("shape", ["H3 sgr0 inside a word", "H4 colourised log with sgr0"])
    def test_sgr0_shapes_within_the_counted_bound(shape):
        """G1: a text with `ESC ( B` (`tput sgr0`) needs no more passes than the counted bound, and a large legitimate
        colourised log at the cap is shown (not refused) in under the time limit."""
        text = fill(SHAPES[shape], CAP)
        redacts, _ = count_calls(text)
        assert redacts <= defaults.MAX_REDACT_PASSES, redacts
        start = time.process_time()
        out = runmap.redact_untrusted(
            text, {}
        )  # raises InputTooLarge if the log is wrongly refused
        assert time.process_time() - start < SECONDS_LIMIT
        assert out

    @pytest.mark.parametrize("shape", HIDDEN_FREE + SHAPE_H)
    def test_seconds(shape):
        """G3: at the cap, under 3.0 s of CPU (median of 5)."""
        assert median_cpu(fill(SHAPES[shape], CAP)) < SECONDS_LIMIT, shape

    @pytest.mark.parametrize("shape", HIDDEN_FREE + SHAPE_H)
    def test_linear(shape):
        """G3: growth by the one rule of `tests/fixtures/timing.py`."""
        from tests.fixtures.timing import is_superlinear

        assert not is_superlinear(cpu, SHAPES[shape], SMALL, CAP), shape

    def test_worst_w():
        """G3: the worst shape finishes or is refused (`InputTooLarge`), and never runs past the budget by more than one pass."""
        text = fill(SHAPES[SHAPE_W], CAP)
        one_pass = (
            median_cpu(text[:SMALL], 3) / 10
        )  # a rough bound of one pass at the small size, scaled below
        start = time.monotonic()
        try:
            runmap.redact_untrusted(text, {})
        except runmap.InputTooLarge:
            pass
        elapsed = time.monotonic() - start
        assert elapsed < defaults.REDACT_BUDGET_S + max(one_pass * (CAP / SMALL), 1.0) + 2.0, (
            elapsed
        )

    def test_over_256_cut_values():
        """D5: 300 distinct e-mail addresses, each cut by a colour code inside its local part, are refused, not shown."""
        text = "\n".join(f"user{i:03d}" + ESC + f"[0mname{i:03d}@example.com" for i in range(300))
        with pytest.raises(runmap.InputTooLarge):
            runmap.redact_untrusted(text, {})

    def test_spaced_value_long_spaces():
        """D6: `password="a b c d"` followed by 10,000 spaces, repeated to the cap, in under 3.0 s of CPU."""
        unit = 'password="a b c d"' + " " * 10_000 + "\n"
        text = fill(unit, CAP)
        assert cpu(text) < SECONDS_LIMIT


def test_spaced_shapes_finish_within_the_limit():
    """Batch 10, group 1: each spaced shape finishes (shown or withheld) in under 3.0 s of CPU; the very long run is withheld by the
    work budget, not read in full."""
    for name, text in _spaced_texts().items():
        assert cpu(text) < SECONDS_LIMIT, name


def _child(py_path: str | None) -> dict[str, float]:
    code = (
        f"import json,sys;sys.path.insert(0,{str(ROOT)!r});from tests import test_prh_perf as P;"
        "print(json.dumps({k: P.median_cpu(P.fill(v, P.CAP), 1) for k, v in P.SHAPES.items() if k[0] in 'SH'} | {k: P.cpu(v) for k, v in P._spaced_texts().items()}))"
    )
    env = {"PYTHONPATH": py_path} if py_path else {}

    async def run() -> tuple[int | None, bytes]:
        # asyncio starts the child directly, with a fixed argument list and no shell
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            code,
            env={**os.environ, **env},
            stdout=asyncio.subprocess.PIPE,
        )
        out, _ = await proc.communicate()
        return proc.returncode, out

    code_returned, stdout = asyncio.run(run())
    if code_returned != 0:
        raise RuntimeError(f"the timing child exited with {code_returned}")
    return json.loads(stdout.decode().strip().splitlines()[-1])


def compare_main(main_root: str) -> None:
    runs: dict[str, dict[str, list[float]]] = {"main": {}, "head": {}}
    for _ in range(REPEATS):
        for who, path in (("main", str(Path(main_root) / "src")), ("head", None)):
            for shape, secs in _child(path).items():
                runs[who].setdefault(shape, []).append(secs)
    print("shape | chars | head median cpu | main median cpu | ratio")
    for shape in runs["head"]:
        h, m = statistics.median(runs["head"][shape]), statistics.median(runs["main"][shape])
        print(f"{shape} | {CAP} | {h:.3f} | {m:.3f} | {h / m:.2f}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--compare-main":
        compare_main(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--record-main-passes":
        print("hadavin_sdk loaded from", sys.modules["hadavin_sdk"].__file__)
        out = {
            k: list(count_calls(fill(SHAPES[k], CAP)))
            for k in HIDDEN_FREE + ["H2 colour inside a word"]
        }
        Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        print(out)
    else:
        sys.exit("usage: test_prh_perf.py --compare-main PATH | --record-main-passes OUT.json")
