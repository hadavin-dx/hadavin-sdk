#!/usr/bin/env python3
"""Portable mutant runner for the real-run v6 chain (HANDOVER-ONLY; made-up data; no network).

usage: python3 mut_portable.py <repo_root> <muts.json> <test paths...>

<muts.json> is a list of [name, file, old_text, new_text]. For each entry the first occurrence of old_text in
<repo_root>/file is replaced by new_text, the given tests are run with `pytest -x -q`, then the file is restored.
Result per mutant: `killed` (tests failed), `SURVIVED` (tests passed) or `NOT-APPLIED` (old_text missing).

Environment:
  MUT_WRAP   command prefix (shell words) put in front of the pytest command, e.g.
             "unshare -n python3 /path/to/lo_up-q4g.py"   (network namespace, loopback up; NEVER run the tests that answer `y` outside one)
  MUT_PY     python to run pytest with (default: this python)
Safety: never answer y/yes or type a destination host; tests that ask a question run only inside the namespace.
The original v6 builder used a private mut.py (scratchpad) that was overwritten; mut-b12.py is the same interface from an earlier harness
(it needs its own run.sh wrapper, not shipped); this file is a clean re-write of the same behaviour and was NOT used to produce the shipped evidence.
"""
import json, os, shlex, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1]); muts = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")); tests = sys.argv[3:]
py = os.environ.get("MUT_PY", sys.executable)
wrap = shlex.split(os.environ.get("MUT_WRAP", ""))
for name, f, old, new in muts:
    p = root / f
    orig = p.read_text(encoding="utf-8")
    if old not in orig:
        print(f"{name}\tNOT-APPLIED (pattern missing)", flush=True)
        continue
    p.write_text(orig.replace(old, new, 1), encoding="utf-8")
    try:
        r = subprocess.run([*wrap, py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *tests],
                           cwd=root, capture_output=True, text=True, timeout=1800)
        out = (r.stdout or r.stderr).strip().splitlines()
        print(f"{name}\t{'SURVIVED' if r.returncode == 0 else 'killed'}\t{out[-1] if out else ''}", flush=True)
    finally:
        p.write_text(orig, encoding="utf-8")
