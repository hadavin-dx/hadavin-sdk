#!/usr/bin/env python3
"""PEEL-run-id mutants (ticket handover/tickets/PEEL-run-id.md, mutation plan). NOT run through tools/mutation_runner.py: that runner
starts pytest with --noconftest, and these tests need tests/conftest.py (the cfg_dir fixture), so its own baseline fails
("the unmutated copy does not pass its tests"). This script does the same per-mutant temp copy with the real conftest.

Run from the root of the PR worktree (it needs tools/ and tests/test_peel_run_id.py):
    python peel_mutants.py [--only TEXT]
Exit 0 only if every mutant is good (KILLED by the pinned test for the stated reason).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))


AL = "src/hadavin_sdk/runtime/agent_loop.py"
MD = "src/hadavin_sdk/models.py"
T = "tests/test_peel_run_id.py"
RAISE = "DID NOT RAISE"
T4 = "test_t4_hostile_ids_are_refused_before_any_write"
T5 = "test_t5_accepts_exactly_the_pattern"


def m(name, file, old, new, test, expect, crash=False):
    return (name, file, old, new, test, expect, crash)


D2B = "test_d2b_direct_a_foreign_run_is_never_returned"
D2 = "test_d2_same_message_twice_returns_the_existing_run"
SAME = "            return self._same_message_run(run, exists)\n"
GUARD = "        if agent_id not in self.agents:\n            raise Unqualified(agent_id)\n        agent = self.registry.agents[agent_id]\n"
EXTRA = '        extra = {} if run_id is None else {"run_id": _checked_run_id(run_id)}\n'

MUTANTS = [
    m("PM-1 (MP1) given run_id ignored (fresh id)", AL, "            **extra,\n", "", "test_t1_given_id_is_the_run_id", "assert"),
    m("PM-2 on a matching existing run the loop runs again", AL, SAME, "            pass\n", D2, "IllegalTransition"),
    m("PM-3 foreign run returned although its agent differs", AL, "found.agent_id != asked.agent_id", "False", D2B + "[foreign-agent]", "StaleState"),
    m("PM-4 foreign run returned although its principal differs", AL, "found.principal_id != asked.principal_id", "False", D2B + "[foreign-principal]", "StaleState"),
    m("PM-5 foreign run returned although its trigger_ref differs", AL, "found.trigger_ref != asked.trigger_ref", "False", D2B + "[foreign-trigger-ref]", "StaleState"),
    m("PM-6 any existing run returned (no comparison result used)", AL, "            raise exists\n        return found", "            return found\n        return found", D2B + "[foreign-agent]", "StaleState"),
    m("PM-7 run id checked before the agent (order swapped)", AL, GUARD + EXTRA, EXTRA + GUARD, "test_t9_order_unqualified_first_then_invalid_run_id", "InvalidRunId"),
    m("PM-8 limits checked on the same-message path", AL, "        try:\n            found = self.store.get_run(asked.run_id)", "        self.limits.blocked(asked.agent_id)\n        try:\n            found = self.store.get_run(asked.run_id)", D2, "assert"),
    m("PM-9 a second received note on the same-message path", AL, "        return found\n\n    # --- the loop", "        self._note(found, 'run', 'received')\n        return found\n\n    # --- the loop", D2, "assert"),
    m("PM-10 vanished run raises NotFound, not StaleState", AL, "            raise exists from None", "            raise", "test_d2d_direct_the_existing_run_vanished_is_still_stale", "NotFound"),
    m("PM-11 returns the asked run, not the stored one", AL, "            raise exists\n        return found", "            raise exists\n        return asked", D2, "assert"),
    m("PM-12 validation placed after create_run", AL, EXTRA + "        run = Run(\n            agent_id=agent_id,\n            principal_id=principal_id,\n            trigger_kind=trigger_kind,\n            trigger_ref=trigger_ref,\n            **extra,\n        )\n        try:\n            self.store.create_run(run)\n", "        run = Run(\n            agent_id=agent_id,\n            principal_id=principal_id,\n            trigger_kind=trigger_kind,\n            trigger_ref=trigger_ref,\n            **({} if run_id is None else {'run_id': run_id}),\n        )\n        try:\n            self.store.create_run(run)\n            if run_id is not None:\n                _checked_run_id(run_id)\n", T4, "ValidationError"),
    m("PM-13 (old MP6) duplicate swallowed, fresh run returned", AL, "            return self._same_message_run(run, exists)\n", "            run = run.model_copy(update={'run_id': 'run-' + 'f' * 32})\n            self.store.create_run(run)\n            return run\n", D2, "assert"),
    m("MP2 validation removed", AL, "    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):", "    if False:", T5, RAISE),
    m("MP3 pattern length loosened", MD, "[0-9a-f]{32}", "[0-9a-f]{1,64}", T5, RAISE),
    m("MP4 fullmatch -> match", AL, "RUN_ID_PATTERN.fullmatch(run_id)", "RUN_ID_PATTERN.match(run_id)", T4, RAISE),
    m("MP5 upper-case hex allowed", MD, 'r"run-[0-9a-f]{32}"', 'r"run-[0-9a-fA-F]{32}"', T4, RAISE),
    m("MP7 non-string accepted", AL, "not isinstance(run_id, str) or ", "", T4, "TypeError", crash=True),
    m("MP9 keyword made positional", AL, "        *,\n        run_id: str | None = None,", "        run_id: str | None = None,", "test_t7_run_id_is_keyword_only_with_default_none", "assert"),
    m("MP10 default id shape changed", MD, 'return f"{prefix}-{uuid.uuid4().hex}"', 'return f"{prefix}-{uuid.uuid4().hex[:31]}"', "test_t3_without_run_id_ids_are_fresh_and_well_formed", "assert"),
]


def run_one(mut):
    name, file, old, new, test, expect, _crash = mut
    with tempfile.TemporaryDirectory(prefix="peel_mut_") as tmp:
        for d in ("src", "tests"):
            shutil.copytree(ROOT / d, Path(tmp) / d, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "pyproject.toml", tmp)
        f = Path(tmp) / file
        text = f.read_text(encoding="utf-8")
        if text.count(old) != 1:
            return name, "ERROR", f"old text found {text.count(old)} times", False
        if file.startswith("src/") and old == new:
            return name, "ERROR", "no change", False
        f.write_text(text.replace(old, new), encoding="utf-8")
        xml = Path(tmp) / "r.xml"
        env = {k: v for k, v in os.environ.items() if "DSN" not in k and "TOKEN" not in k}
        env["PYTHONPATH"] = str(Path(tmp) / "src")
        rc = subprocess.run(  # noqa: S603 - fixed argv, our own pytest
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}", f"{T}::{test}"],
            cwd=tmp, env=env, capture_output=True, text=True, timeout=300, check=False,
        ).returncode
        first = ""
        if xml.exists():
            for case in ET.parse(xml).getroot().iter("testcase"):  # noqa: S314 - our own pytest file
                for bad in list(case.iter("failure")) + list(case.iter("error")):
                    first = (bad.get("message") or "").splitlines()[0] if bad.get("message") else ""
                    first = first or (bad.text or "").strip().splitlines()[0]
        if rc == 0:
            return name, "SURVIVED", "", False
        if rc != 1:
            return name, "ERROR", f"pytest exit {rc}", False
        ok = expect in first
        return name, "KILLED" if ok else "WRONG_REASON", first[:160], ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    sel = [x for x in MUTANTS if a.only in x[0]]
    if not sel:
        return 2
    good = 0
    for mut in sel:
        name, verdict, line, ok = run_one(mut)
        good += ok
        print(f"{name} | {verdict} | {'GOOD' if ok else 'BAD'} | {line}", flush=True)
    print(f"{good}/{len(sel)} good")
    return 0 if good == len(sel) else 1


if __name__ == "__main__":
    raise SystemExit(main())
