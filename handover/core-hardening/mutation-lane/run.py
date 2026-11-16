#!/usr/bin/env python3
"""Hand-planted mutation runner (evidence only: it runs and records, it never judges beyond the exit code).

For ONE mutant (or a JSON list of them) in a SCRATCH copy of the code, never the real repo:
  1. read the target file, check `old` occurs exactly once, write the mutated text;
  2. run the test command with a clean environment (`env -i`), one process, NO -x (so every killing test is listed);
  3. restore the original bytes, and byte-compare with a saved copy (`diff`); abort if they differ;
  4. write raw/<prefix>-<id>.txt with: rc, exact command, base commit sha, root, file, old text, new text,
     restore check, pytest summary line, first failing test id, all failing test ids, and the full pytest output.
Verdict from the exit code: 0 SURVIVED, 1 KILLED, anything else ERROR (not counted as killed).

Usage:
  run.py --root /tmp/c8/wC --sha b4cce5b --prefix C-01 --raw DIR --list mutants.json -- TESTS...
  run.py --root ... --sha ... --prefix C-01 --raw DIR --id m01 --file src/x.py --old "a" --new "b" -- TESTS...
mutants.json: [{"id": "m01", "file": "...", "old": "...", "new": "...", "desc": "..."}, ...]
`--control` runs the unmutated tree once first and records it as <prefix>-baseline.txt.
TESTS are pytest arguments (paths / -k ...). The command run is:
  env -i PATH=.. HOME=.. PYTHONDONTWRITEBYTECODE=1 <root>/.venv/bin/python -m pytest -q -p no:cacheprovider --tb=line -rf TESTS
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys


def run_tests(root: pathlib.Path, tests: list[str]):
    # stale .pyc files could hide a planted change (same size, same second): never write or reuse them
    for d in root.rglob("__pycache__"):
        if ".venv" not in d.parts:
            shutil.rmtree(d, ignore_errors=True)
    cmd = [
        "env",
        "-i",
        f"PATH={os.environ['PATH']}",
        f"HOME={os.environ['HOME']}",
        "PYTHONDONTWRITEBYTECODE=1",
        str(root / ".venv/bin/python"),
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--tb=line",
        "-rf",
        *tests,
    ]
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=600)
        return cmd, r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return cmd, None, "TIMEOUT after 600 s"


def summary(out: str):
    lines = [x for x in out.splitlines() if x.strip()]
    last = lines[-1] if lines else ""
    failed = [x.split(" ", 1)[1].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    return last, failed


def one(a, tests, m, results):
    root = pathlib.Path(a.root)
    p = root / m["file"]
    orig = p.read_bytes()
    backup = pathlib.Path(a.raw).parent / ".restore-copy"
    backup.write_bytes(orig)
    n = orig.decode().count(m["old"])
    if n != 1:
        verdict, out, cmd, rc = f"COULD-NOT-PLANT (old text occurs {n} times)", "", [], None
        restore = "no change made"
    else:
        p.write_bytes(orig.decode().replace(m["old"], m["new"], 1).encode())
        try:
            cmd, rc, out = run_tests(root, tests)
        finally:
            p.write_bytes(orig)
        d = subprocess.run(["diff", str(backup), str(p)], capture_output=True, text=True)
        restore = f"diff <saved original> <file after restore>: rc={d.returncode} (0 = identical)"
        if d.returncode != 0:
            print("RESTORE FAILED", m["id"], file=sys.stderr)
            sys.exit(3)
        verdict = "TIMEOUT" if rc is None else "SURVIVED" if rc == 0 else "KILLED" if rc == 1 else f"ERROR rc={rc}"
    last, failed = summary(out)
    text = (
        f"MUTANT {a.prefix}-{m['id']}  VERDICT: {verdict}\n"
        f"description: {m.get('desc', '')}\n"
        f"base commit: {a.sha}   root: {a.root}   file: {m['file']}\n"
        f"command: {' '.join(cmd)}   (cwd={a.root})\n"
        f"rc: {rc}\n"
        f"restore check: {restore}\n"
        f"pytest summary line: {last}\n"
        f"first failing test: {failed[0] if failed else '-'}\n"
        f"all failing tests ({len(failed)}): {'; '.join(failed) if failed else '-'}\n"
        f"--- OLD TEXT (full) ---\n{m['old']}\n--- NEW TEXT (full) ---\n{m['new']}\n--- PYTEST OUTPUT (full) ---\n{out}\n"
    )
    (pathlib.Path(a.raw) / f"{a.prefix}-{m['id']}.txt").write_text(text)
    results.append(
        {"id": m["id"], "desc": m.get("desc", ""), "verdict": verdict, "rc": rc, "first": failed[0] if failed else "", "n_failed": len(failed), "summary": last}
    )
    print(m["id"], verdict, failed[0] if failed else "", flush=True)


def main():
    argv = sys.argv[1:]
    tests = argv[argv.index("--") + 1 :] if "--" in argv else []
    ap = argparse.ArgumentParser()
    for k in ("root", "sha", "prefix", "raw"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--list")
    ap.add_argument("--id")
    ap.add_argument("--file")
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--desc", default="")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--out-json")
    a = ap.parse_args(argv[: argv.index("--")] if "--" in argv else argv)
    pathlib.Path(a.raw).mkdir(parents=True, exist_ok=True)
    results = []
    if a.control:
        cmd, rc, out = run_tests(pathlib.Path(a.root), tests)
        last, _ = summary(out)
        (pathlib.Path(a.raw) / f"{a.prefix}-baseline.txt").write_text(
            f"UNMUTATED BASELINE\nbase commit: {a.sha} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nrc: {rc}\nsummary: {last}\n\n{out}"
        )
        print("baseline", rc, last)
    ms = json.load(open(a.list)) if a.list else [{"id": a.id, "file": a.file, "old": a.old, "new": a.new, "desc": a.desc}]
    for m in ms:
        one(a, tests, m, results)
    if a.out_json:
        json.dump(results, open(a.out_json, "w"), indent=1)


if __name__ == "__main__":
    main()
