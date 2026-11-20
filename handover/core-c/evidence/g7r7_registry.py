"""G7 fix round 7: the memory of the spelled-form registry (scratch script kept as evidence; every credential is made up and built from parts).

Run from anywhere: uv run --all-extras --group test python handover/core-c/evidence/g7r7_registry.py
 1. the registry characters (`_Redactor._spelled_chars`: trie nodes held) of the corpus of tests/test_redact_idempotent_property.py (every input through
    `runmap.redact_text`, which makes several redactors: the largest count of any of them is reported) and of the honest jars of g7r6_units.py;
 2. the hostile case of the design review: `password=hunter22`, then 8 strings of `password=<SECRET_1>` + 260,000 secret-class characters each
    through `redact_many`, and one such string through `redact`: seconds of thread CPU and the tracemalloc peak, refused or not.
"""

from __future__ import annotations

import importlib
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(Path(__file__).resolve().parent)]
defaults = importlib.import_module("hadavin_sdk.defaults")
runmap = importlib.import_module("hadavin_sdk.guard.runmap")
importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]
units = importlib.import_module("g7r6_units")

PEAK = {"max": 0, "at": ""}


def watch(label: str) -> None:
    real = R._Redactor._spell

    def spell(self, *args, **kwargs):
        real(self, *args, **kwargs)
        if self._spelled_chars > PEAK["max"]:
            PEAK["max"], PEAK["at"] = self._spelled_chars, label

    R._Redactor._spell = spell


def corpus() -> None:
    prop = importlib.import_module("tests.test_redact_idempotent_property")
    biggest = 0
    forms = 0
    for name, text in prop.CORPUS:
        PEAK["max"] = 0
        try:
            runmap.redact_text(text, runmap.RunMap())
        except runmap.RedactionError:
            pass
        biggest = max(biggest, PEAK["max"])
        forms += PEAK["max"] > 0
    print(
        f"corpus: {len(prop.CORPUS)} inputs, {forms} register a spelled form, the largest registry holds {biggest} characters"
    )


def jars() -> None:
    for lines, sig in ((330, 64), (275, 128)):
        text, _ = units.jar_log(lines, sig)
        r = R._Redactor(None)
        r.find(text)
        r.sweep("")
        print(
            f"jar lines={lines} suffix={sig}: forms={len(r._spelled_at)} registry_chars={r._spelled_chars}"
        )


def hostile() -> None:
    fake = "hun" + "ter" + "22"
    tail = ("Ab3x" * 65000)[:260_000]
    items = ["password=" + fake] + [f"password=<SECRET_1>Zq{i}" + tail for i in range(8)]
    for label, call in (
        ("redact_many, 1 + 8 strings of 260,000 characters", lambda: R.redact_many(items)),
        (
            "redact, 1 string of 260,000 characters",
            lambda: R.redact(items[1], mapping={"<SECRET_1>": fake}),
        ),
    ):
        tracemalloc.start()
        t0 = time.thread_time()
        try:
            call()
            outcome = "not refused"
        except runmap.InputTooLarge as e:
            outcome = f"REFUSED ({e})"
        took = time.thread_time() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        print(
            f"hostile {label}: {outcome}; {took:.1f} s thread CPU under tracemalloc; peak {peak / 1e6:.0f} MB"
        )


if __name__ == "__main__":
    print(f"SPELLED_MAX_CHARS = {getattr(defaults, 'SPELLED_MAX_CHARS', None)}")
    watch("corpus")
    corpus()
    jars()
    hostile()
