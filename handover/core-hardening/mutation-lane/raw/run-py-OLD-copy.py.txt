#!/usr/bin/env python3
"""Hand-planted mutation runner (evidence only: it runs and records, it never judges beyond the exit code).

For ONE mutant (or a JSON list of them) in a SCRATCH copy of the code, never the real repo:
  1. read the target file, check `old` occurs exactly once, write the mutated text;
  2. run the test command with a clean environment (`env -i`), one process, NO -x (so every killing test is listed);
  3. restore the original bytes, and byte-compare with a saved copy (`diff`); abort if they differ. The saved copy lives in
     a state folder OUTSIDE any repository (`$TMPDIR/hadavin-mutation-lane/`), not in the lane folder, and is deleted
     after each mutant;
  4. write raw/<prefix>-<id>.txt with: rc, exact command, base commit sha, root, file, old text, new text,
     restore check, pytest summary line, first failing test id, all failing test ids, and the full pytest output.
Safety (added after review 2, M2 + M3):
  * Before anything is planted the scratch tree is compared with a reference built from `git archive <sha>` (+ every
    `--patch FILE`, applied with `patch -p1`). Any difference (other than `--extra` files) means REFUSED: the tree may
    already hold a planted change from an earlier killed run. The original of each target file is taken from that
    reference, never from the file on disk (no circular check).
  * `--root` is REFUSED if it is, or lies inside, the repository work tree (the real repo), or is any git work tree.
  * A lock (flock) per root: a second run on the same root is refused while one is running.
  * A marker file is written before each planting and removed after the restore. If a run is killed with SIGKILL the
    marker stays: the next run refuses and prints how to restore (`run.py --root R --restore`).
  * SIGTERM and SIGINT restore the file, stop the test process group, remove the marker and exit (143 / 130).
  * After the loop `raw/<prefix>-tree-diff.txt` records `diff -rq` of the scratch tree against a FRESH `git archive`
    extract (+ patches); expected: no difference lines apart from the declared `--extra` files.
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
import fcntl
import hashlib
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile

SKIP_DIRS = {".venv", "__pycache__", ".pytest_cache"}
STATE = pathlib.Path(tempfile.gettempdir()) / "hadavin-mutation-lane"  # outside every repository


class Refused(Exception):
    pass


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _term(signum, frame):
    raise KeyboardInterrupt(signum)  # unwinds through the `finally` that restores the file


def tree_files(root: pathlib.Path) -> dict[str, str]:
    out = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for f in fns:
            p = pathlib.Path(dp) / f
            out[str(p.relative_to(root))] = sha256(p.read_bytes()) if not p.is_symlink() else "symlink:" + os.readlink(p)
    return out


def build_reference(repo: str, sha: str, patches: list[str], dest: pathlib.Path) -> None:
    """Fresh `git archive <sha>` extract (+ patches) into dest: the one source of truth for original bytes."""
    top = subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or repo
    arc = subprocess.run(["git", "-C", top, "archive", sha], capture_output=True)  # from the top: a subfolder would archive only itself
    if arc.returncode != 0:
        raise Refused(f"git archive {sha} failed in {repo}: {arc.stderr.decode(errors='replace')[:200]}")
    subprocess.run(["tar", "-x", "-C", str(dest)], input=arc.stdout, check=True)
    for pf in patches:
        r = subprocess.run(["patch", "-p1", "-s", "-d", str(dest), "-i", str(pathlib.Path(pf).resolve())], capture_output=True, text=True)
        if r.returncode != 0:
            raise Refused(f"patch {pf} does not apply to {sha}: {r.stdout[:200]}{r.stderr[:200]}")


def refuse_real_repo(root: pathlib.Path, repo: str) -> None:
    top = pathlib.Path(subprocess.run(["git", "-C", repo, "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or repo).resolve()
    root = root.resolve()
    if root == top or top in root.parents or root in top.parents:
        raise Refused(f"--root {root} is, contains or lies inside the real repository {top}: use a scratch copy")
    inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        raise Refused(f"--root {root} is inside a git work tree: use a plain scratch copy (git archive + patch)")


def key_for(root: pathlib.Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]


def restore_from_marker(root: pathlib.Path) -> str:
    marker = STATE / f"{key_for(root)}.planted.json"
    if not marker.exists():
        return "no marker: nothing to restore"
    m = json.loads(marker.read_text())
    bk = pathlib.Path(m["backup"])
    target = root / m["file"]
    target.write_bytes(bk.read_bytes())
    ok = sha256(target.read_bytes()) == m["orig_sha256"]
    if ok:
        marker.unlink()
        bk.unlink(missing_ok=True)
    return f"restored {m['file']} from {bk}; hash matches saved original: {ok}"


def run_tests(root: pathlib.Path, tests: list[str], pythonpath: str | None = None):
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
        *([f"PYTHONPATH={pythonpath}"] if pythonpath else []),
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
    proc = subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=600)
        return cmd, proc.returncode, out
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        return cmd, None, "TIMEOUT after 600 s"
    except BaseException:  # SIGTERM / SIGINT while the tests run: stop the test process group, then let the caller restore
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise


def summary(out: str):
    lines = [x for x in out.splitlines() if x.strip()]
    last = lines[-1] if lines else ""
    failed = [x.split(" ", 1)[1].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    return last, failed


def one(a, tests, m, results, ref):
    root = pathlib.Path(a.root)
    p = root / m["file"]
    orig = p.read_bytes()
    ref_bytes = (ref / m["file"]).read_bytes()
    if orig != ref_bytes:  # hash baseline from git archive, not from the file on disk
        raise Refused(f"{m['file']} differs from the git archive reference (sha256 {sha256(orig)[:12]} vs {sha256(ref_bytes)[:12]}): refusing")
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = key_for(root)
    backup = STATE / f"{key}.backup"
    marker = STATE / f"{key}.planted.json"
    n = orig.decode().count(m["old"])
    if n != 1:
        verdict, out, cmd, rc = f"COULD-NOT-PLANT (old text occurs {n} times)", "", [], None
        restore = "no change made"
    else:
        backup.write_bytes(orig)
        marker.write_text(json.dumps({"root": str(root), "file": m["file"], "backup": str(backup), "orig_sha256": sha256(orig), "mutant": f"{a.prefix}-{m['id']}"}))
        try:
            p.write_bytes(orig.decode().replace(m["old"], m["new"], 1).encode())
            cmd, rc, out = run_tests(root, tests, a.pythonpath)
        finally:
            p.write_bytes(orig)
        d = subprocess.run(["diff", str(backup), str(p)], capture_output=True, text=True)
        same_hash = sha256(p.read_bytes()) == sha256(ref_bytes)
        restore = f"diff <saved original> <file after restore>: rc={d.returncode} (0 = identical); sha256 equals git-archive reference: {same_hash}"
        if d.returncode != 0 or not same_hash:
            print("RESTORE FAILED", m["id"], "(marker and backup kept; run --restore)", file=sys.stderr)
            sys.exit(3)
        marker.unlink()
        backup.unlink()
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
        ap.add_argument("--" + k, required=(k == "root"))
    ap.add_argument("--list")
    ap.add_argument("--id")
    ap.add_argument("--file")
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--desc", default="")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--out-json")
    ap.add_argument("--pythonpath", help="only for the proof copies, whose venv .pth points at another tree")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent), help="a folder inside the repository that holds --sha (default: this script's folder)")
    ap.add_argument("--patch", action="append", default=[], help="patch applied (-p1) on top of the git archive to get the expected tree; repeatable")
    ap.add_argument("--extra", action="append", default=[], help="path (relative to root) of a file that may exist in root beyond the reference, e.g. proof tests; repeatable")
    ap.add_argument("--restore", action="store_true", help="restore a file left planted by a killed run, then exit")
    a = ap.parse_args(argv[: argv.index("--")] if "--" in argv else argv)
    root = pathlib.Path(a.root)
    if a.restore:
        print(restore_from_marker(root))
        return
    if not (a.prefix and a.raw and a.sha):
        ap.error("--sha, --prefix and --raw are required")
    signal.signal(signal.SIGTERM, _term)
    signal.signal(signal.SIGINT, _term)
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = open(STATE / f"{key_for(root)}.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(f"REFUSED: another run holds the lock for {root}; two runs on one tree would plant over each other")
    marker = STATE / f"{key_for(root)}.planted.json"
    tmpref = pathlib.Path(tempfile.mkdtemp(prefix="mutation-ref-"))
    try:
        refuse_real_repo(root, a.repo)
        if marker.exists():
            m = json.loads(marker.read_text())
            raise Refused(
                f"a mutant ({m['mutant']}) is still planted in {m['file']} from an earlier run that was killed. "
                f"Restore with: python3 {sys.argv[0]} --root {root} --restore   "
                f"(copies {m['backup']} back and checks the hash); then run again"
            )
        ref = tmpref / "ref"
        ref.mkdir()
        build_reference(a.repo, a.sha, a.patch, ref)
        diffs = diff_trees(ref, root, set(a.extra))
        if diffs:
            raise Refused(f"scratch tree differs from git archive {a.sha} + patches in {len(diffs)} file(s), first: {diffs[:3]}: it may hold a planted change; rebuild it from the archive")
        pathlib.Path(a.raw).mkdir(parents=True, exist_ok=True)
        results = []
        if a.control:
            cmd, rc, out = run_tests(root, tests, a.pythonpath)
            last, _ = summary(out)
            (pathlib.Path(a.raw) / f"{a.prefix}-baseline.txt").write_text(
                f"UNMUTATED BASELINE\nbase commit: {a.sha} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nrc: {rc}\nsummary: {last}\n\n{out}"
            )
            print("baseline", rc, last)
        ms = json.load(open(a.list)) if a.list else [{"id": a.id, "file": a.file, "old": a.old, "new": a.new, "desc": a.desc}]
        for m in ms:
            one(a, tests, m, results, ref)
        if a.out_json:
            json.dump(results, open(a.out_json, "w"), indent=1)
        # proof the scratch tree is unchanged: diff -rq against a FRESH archive extract
        fresh = tmpref / "fresh"
        fresh.mkdir()
        build_reference(a.repo, a.sha, a.patch, fresh)
        excl = [x for d in sorted(SKIP_DIRS) for x in ("-x", d)]
        r = subprocess.run(["diff", "-rq", *excl, str(fresh), str(root)], capture_output=True, text=True)
        (pathlib.Path(a.raw) / f"{a.prefix}-tree-diff.txt").write_text(
            f"TREE CHECK after the loop\ncommand: diff -rq {' '.join(excl)} <fresh git archive {a.sha} + patches {a.patch}> {a.root}\n"
            f"declared extra files (expected as 'Only in'): {a.extra}\nrc: {r.returncode} (0 = identical; 1 = differences listed)\n--- output ---\n{r.stdout}{r.stderr}"
        )
        print("tree diff rc", r.returncode)
    except Refused as e:
        print("REFUSED:", e, file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt as e:
        signum = e.args[0] if e.args and isinstance(e.args[0], int) else signal.SIGINT
        print(f"INTERRUPTED (signal {signum}): file restored, marker removed", file=sys.stderr)
        if marker.exists():
            print("restore from marker:", restore_from_marker(root), file=sys.stderr)
        sys.exit(128 + int(signum))
    finally:
        shutil.rmtree(tmpref, ignore_errors=True)


def diff_trees(ref: pathlib.Path, root: pathlib.Path, extra: set[str]) -> list[str]:
    a, b = tree_files(ref), tree_files(root)
    out = [f for f in sorted(set(a) | set(b)) if a.get(f) != b.get(f) and not (f in extra and f not in a)]
    return out


if __name__ == "__main__":
    main()
