#!/usr/bin/env python3
"""Hand-planted mutation runner (evidence only: it runs and records, it never judges beyond the exit code).

For ONE mutant (or a JSON list of them) in a SCRATCH copy of the code, never the real repo:
  1. read the target file, check `old` occurs exactly once, write the mutated text;
  2. run the test command with a clean environment (only PATH, HOME, PYTHONDONTWRITEBYTECODE and, if
     asked, PYTHONPATH), one process, NO -x (so every killing test is listed);
  3. restore the original bytes and byte-compare with the saved copy and with the git-archive
     reference; abort if they differ. The saved copy lives in a state folder OUTSIDE any repository
     (`$TMPDIR/hadavin-mutation-lane/`), not in the lane folder, and is deleted after each mutant;
  4. write raw/<prefix>-<id>.txt with: rc, exact command, base commit sha, root, file, old text, new
     text, restore check, pytest summary line, first failing test id, all failing test ids, and the
     full pytest output.
Safety (review 2 M2/M3, review 3 M-A..M-E and nits):
  * Before anything is planted the scratch tree is compared with a reference built from
    `git archive <sha>` (+ every `--patch FILE`, applied with `patch -p1`). Any difference (other
    than `--extra` files) means REFUSED: the tree may already hold a planted change. The original
    of each target file is taken from that reference, never from the file on disk.
  * Every mutant `file` (and every `--extra`) must be a relative path without `..`, no path
    component may be a symbolic link, and it must resolve inside the root (M-A). A symbolic link to
    a folder anywhere in the scratch tree is a difference from the reference and is refused (M-B).
  * `--root` is REFUSED if it is, contains, or lies inside the real repository (the one that holds
    this script, any `--real-repo`, and the one that holds `--repo`), if a `.git` entry exists in
    it or above it, or if git cannot tell. A failing `git rev-parse` is a refusal, never a pass (M-C).
  * A lock (flock) per root: a second run on the same root is refused while one is running; so is
    `--restore` while a run holds it.
  * A marker (with the process group of the test run) is written before each planting and removed
    after the restore. If a run is killed with SIGKILL the marker stays: the next run refuses and
    prints how to restore (`run.py --root R --restore`), which also stops the orphaned test group.
  * SIGTERM, SIGINT and SIGHUP restore the file, stop the test process group, remove the marker and
    exit with 128 + the signal number (143, 130, 129).
  * After the loop `raw/<prefix>-tree-diff.txt` records the differences between the scratch tree and
    a FRESH `git archive` extract (+ patches). Any difference other than the declared `--extra`
    files, or a marker left behind, gives exit code 4 (M-D).
Exit codes: 0 all mutants ran and the tree is clean; 2 refused; 3 restore failed (marker and backup
kept); 4 tree not clean or marker left after the loop; 128+N interrupted by signal N.
Verdict per mutant from the pytest exit code: 0 SURVIVED, 1 KILLED, anything else ERROR.

Usage:
  run.py --root /tmp/c8/wC --sha b4cce5b --prefix C-01 --raw DIR --list mutants.json -- TESTS...
  run.py --root ... --sha ... --prefix C-01 --raw DIR --id m01 --file src/x.py --old "a" --new "b" -- TESTS...
mutants.json: [{"id": "m01", "file": "...", "old": "...", "new": "...", "desc": "..."}, ...]
`--control` runs the unmutated tree once first and records it as <prefix>-baseline.txt.
TESTS are pytest arguments (paths / -k ...). The command run is, with only the environment named above:
  <root>/.venv/bin/python -m pytest -q -p no:cacheprovider --tb=line -rf TESTS
"""

import argparse
import fcntl
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

SKIP_DIRS = {".venv", "__pycache__", ".pytest_cache"}
STATE = pathlib.Path(tempfile.gettempdir()) / "hadavin-mutation-lane"  # outside every repository
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
SHA_RE = re.compile(r"[0-9a-fA-F]{4,64}")
HANDLED_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
EXIT_REFUSED, EXIT_RESTORE_FAILED, EXIT_TREE_NOT_CLEAN = 2, 3, 4


class Refused(Exception):
    pass


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _term(signum, frame):
    raise KeyboardInterrupt(signum)  # unwinds through the `finally` that restores the file


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise Refused(f"required program not found: {name}")
    return found


def run_cmd(argv: list[str], input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    """The one place that starts a helper program (git, patch): fixed argument list, no shell."""
    return subprocess.run(argv, input=input_bytes, capture_output=True, check=False)


def text_of(cp: subprocess.CompletedProcess) -> str:
    return (cp.stdout + cp.stderr).decode(errors="replace").strip()


def safe_rel(base: pathlib.Path, rel, what: str, must_exist: bool = True) -> pathlib.Path:
    """A relative path inside `base`: no absolute path, no `..`, no symbolic link on the way."""
    if not isinstance(rel, str) or not rel or "\0" in rel or "\\" in rel:
        raise Refused(f"{what}: not a usable relative path: {rel!r}")
    pp = pathlib.PurePosixPath(rel)
    if pp.is_absolute() or ".." in pp.parts:
        raise Refused(f"{what}: must be relative to the root and contain no '..': {rel!r}")
    real_base = base.resolve()
    cur = base
    for part in pp.parts:
        cur = cur / part
        if cur.is_symlink():
            raise Refused(f"{what}: {rel!r} passes through a symbolic link ({part}): refused")
    if not cur.resolve().is_relative_to(real_base):
        raise Refused(f"{what}: {rel!r} resolves outside {base}: refused")
    if must_exist and not cur.is_file():
        raise Refused(f"{what}: {rel!r} is not a regular file under {base}")
    return cur


def tree_files(root: pathlib.Path) -> dict[str, str]:
    out = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for d in dns:
            dpath = pathlib.Path(dp) / d
            if dpath.is_symlink():  # os.walk lists but never enters it: record it (M-B)
                out[str(dpath.relative_to(root)) + "/"] = "symlinked folder:" + os.readlink(dpath)
        for f in fns:
            p = pathlib.Path(dp) / f
            rel = str(p.relative_to(root))
            out[rel] = "symlink:" + os.readlink(p) if p.is_symlink() else sha256(p.read_bytes())
    return out


def diff_trees(ref: pathlib.Path, root: pathlib.Path, extra: set[str]) -> list[str]:
    a, b = tree_files(ref), tree_files(root)
    return [
        f
        for f in sorted(set(a) | set(b))
        if a.get(f) != b.get(f) and not (f in extra and f not in a)
    ]


def repo_toplevel(repo: str) -> pathlib.Path:
    cp = run_cmd([tool("git"), "-C", repo, "rev-parse", "--show-toplevel"])
    if cp.returncode != 0 or not cp.stdout.strip():
        raise Refused(
            f"git rev-parse failed for --repo {repo} (rc {cp.returncode}): {text_of(cp)[:200]}"
        )
    return pathlib.Path(cp.stdout.decode().strip()).resolve()


def build_reference(repo: str, sha: str, patches: list[str], dest: pathlib.Path) -> None:
    """Fresh `git archive <sha>` extract (+ patches) into dest: the one source of truth for original bytes."""
    if not SHA_RE.fullmatch(sha):
        raise Refused(f"--sha is not a commit id: {sha!r}")
    top = repo_toplevel(repo)  # archive from the top: a subfolder would archive only itself
    arc = run_cmd([tool("git"), "-C", str(top), "archive", sha])
    if arc.returncode != 0:
        raise Refused(f"git archive {sha} failed in {repo}: {text_of(arc)[:200]}")
    with tarfile.open(fileobj=io.BytesIO(arc.stdout), mode="r:") as tf:
        tf.extractall(dest, filter="data")
    for pf in patches:
        r = run_cmd(
            [tool("patch"), "-p1", "-s", "-d", str(dest), "-i", str(pathlib.Path(pf).resolve())]
        )
        if r.returncode != 0:
            raise Refused(f"patch {pf} does not apply to {sha}: {text_of(r)[:300]}")


def script_repo_root() -> pathlib.Path | None:
    """The repository that holds this script, found by walking up to a `.git` entry (no git call)."""
    here = pathlib.Path(__file__).resolve().parent
    return next((p for p in (here, *here.parents) if (p / ".git").exists()), None)


def refuse_real_repo(root: pathlib.Path, repo: str, extra_real: list[str]) -> None:
    if not root.is_dir():
        raise Refused(f"--root {root} is not a folder")
    root = root.resolve()
    real = {repo_toplevel(repo), *(pathlib.Path(x).resolve() for x in extra_real)}
    mine = script_repo_root()
    if mine is not None:
        real.add(mine)
    for top in sorted(real):
        if root == top or top in root.parents or root in top.parents:
            raise Refused(
                f"--root {root} is, contains or lies inside the real repository {top}: use a scratch copy"
            )
    for p in (root, *root.parents):
        if (p / ".git").exists():
            raise Refused(
                f"--root {root}: a .git entry exists in {p}: use a plain scratch copy (git archive + patch)"
            )
    inside = run_cmd([tool("git"), "-C", str(root), "rev-parse", "--is-inside-work-tree"])
    said = text_of(inside)
    if inside.returncode == 0 and said.endswith("true"):
        raise Refused(f"--root {root} is inside a git work tree: use a plain scratch copy")
    if inside.returncode != 0 and "not a git repository" not in said.lower():
        raise Refused(
            f"git cannot tell whether --root {root} is a work tree (rc {inside.returncode}): {said[:200]}"
        )


def key_for(root: pathlib.Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]


def stop_group(pgid: int) -> None:
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def stop_orphan(m: dict, root: pathlib.Path) -> str:
    """After a SIGKILL of run.py the test group may still run: stop it, but only if it is ours."""
    pgid = m.get("pgid")
    if not isinstance(pgid, int) or pgid <= 1:
        return "no test group recorded"
    try:
        cmdline = pathlib.Path(f"/proc/{pgid}/cmdline").read_bytes().decode(errors="replace")
    except OSError:
        return "test group already gone"
    if "pytest" not in cmdline or str(root) not in cmdline:
        return f"process {pgid} is not this run's pytest: left alone"
    stop_group(pgid)
    for _ in range(50):
        if not pathlib.Path(f"/proc/{pgid}").exists():
            break
        time.sleep(0.1)
    return f"stopped orphaned test group {pgid}"


def restore_from_marker(root: pathlib.Path) -> tuple[bool, str]:
    marker = STATE / f"{key_for(root)}.planted.json"
    if not marker.exists():
        return True, "no marker: nothing to restore"
    m = json.loads(marker.read_text())
    bk = pathlib.Path(m["backup"]).resolve()
    if bk.parent != STATE.resolve():
        raise Refused(f"marker names a backup outside the state folder: {bk}")
    target = safe_rel(root, m["file"], "marker file")
    orphan = stop_orphan(m, root)
    target.write_bytes(bk.read_bytes())
    ok = sha256(target.read_bytes()) == m["orig_sha256"]
    if ok:
        marker.unlink()
        bk.unlink(missing_ok=True)
    return ok, f"{orphan}; restored {m['file']} from {bk}; hash matches saved original: {ok}"


def run_tests(
    root: pathlib.Path,
    tests: list[str],
    pythonpath: str | None = None,
    timeout: int = 600,
    on_start=None,
):
    # stale .pyc files could hide a planted change (same size, same second): never write or reuse them
    for d in root.rglob("__pycache__"):
        if ".venv" not in d.parts:
            shutil.rmtree(d, ignore_errors=True)
    py = root / ".venv/bin/python"
    if not py.exists():
        raise Refused(f"{py} does not exist: the scratch root needs its own .venv")
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    cmd = [str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", "-rf", *tests]
    # one process group, so a timeout or a signal can stop all of it
    proc = subprocess.Popen(
        cmd,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    if on_start:
        on_start(proc.pid)
    try:
        out, _ = proc.communicate(timeout=timeout)
        return cmd, proc.returncode, out
    except subprocess.TimeoutExpired:
        stop_group(proc.pid)
        proc.communicate()
        return cmd, None, f"TIMEOUT after {timeout} s"
    except BaseException:  # SIGTERM / SIGINT while the tests run: stop the test process group, then let the caller restore
        stop_group(proc.pid)  # a group that is already gone must not hide the signal
        proc.communicate()
        raise


def summary(out: str):
    lines = [x for x in out.splitlines() if x.strip()]
    last = lines[-1] if lines else ""
    failed = [x.split(" ", 1)[1].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    return last, failed


def one(a, tests, m, results, ref):
    root = pathlib.Path(a.root)
    p = safe_rel(root, m["file"], f"mutant {m['id']} file")
    refp = safe_rel(ref, m["file"], f"mutant {m['id']} reference file")
    if os.path.samefile(p, refp):
        raise Refused(f"mutant {m['id']}: {m['file']} and its reference are the same file")
    orig = p.read_bytes()
    ref_bytes = refp.read_bytes()
    if orig != ref_bytes:  # hash baseline from git archive, not from the file on disk
        raise Refused(
            f"{m['file']} differs from the git archive reference (sha256 {sha256(orig)[:12]} vs {sha256(ref_bytes)[:12]}): refusing"
        )
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
        info = {
            "root": str(root),
            "file": m["file"],
            "backup": str(backup),
            "orig_sha256": sha256(orig),
            "mutant": f"{a.prefix}-{m['id']}",
        }
        marker.write_text(json.dumps(info))

        def note_group(pgid: int) -> None:
            marker.write_text(json.dumps({**info, "pgid": pgid}))

        try:
            p.write_bytes(orig.decode().replace(m["old"], m["new"], 1).encode())
            cmd, rc, out = run_tests(root, tests, a.pythonpath, a.timeout, note_group)
        finally:
            p.write_bytes(orig)
            back = p.read_bytes()
            same_hash = sha256(back) == sha256(ref_bytes) and back == backup.read_bytes()
            if not same_hash:
                print(
                    "RESTORE FAILED",
                    m["id"],
                    "(marker and backup kept; run --restore)",
                    file=sys.stderr,
                )
                sys.exit(EXIT_RESTORE_FAILED)
            marker.unlink(
                missing_ok=True
            )  # the file is verified identical: no marker may stay, even on an error
            backup.unlink(missing_ok=True)
        restore = f"saved original == file after restore (byte compare): True; sha256 equals git-archive reference: {same_hash}"
        verdict = (
            "TIMEOUT"
            if rc is None
            else "SURVIVED"
            if rc == 0
            else "KILLED"
            if rc == 1
            else f"ERROR rc={rc}"
        )
    last, failed = summary(out)
    text = (
        f"MUTANT {a.prefix}-{m['id']}  VERDICT: {verdict}\n"
        f"description: {m.get('desc', '')}\n"
        f"base commit: {a.sha}   root: {a.root}   file: {m['file']}\n"
        f"command: {' '.join(cmd)}   (cwd={a.root}; environment: PATH, HOME, PYTHONDONTWRITEBYTECODE only)\n"
        f"rc: {rc}\n"
        f"restore check: {restore}\n"
        f"pytest summary line: {last}\n"
        f"first failing test: {failed[0] if failed else '-'}\n"
        f"all failing tests ({len(failed)}): {'; '.join(failed) if failed else '-'}\n"
        f"--- OLD TEXT (full) ---\n{m['old']}\n--- NEW TEXT (full) ---\n{m['new']}\n--- PYTEST OUTPUT (full) ---\n{out}\n"
    )
    (pathlib.Path(a.raw) / f"{a.prefix}-{m['id']}.txt").write_text(text)
    results.append(
        {
            "id": m["id"],
            "desc": m.get("desc", ""),
            "verdict": verdict,
            "rc": rc,
            "first": failed[0] if failed else "",
            "n_failed": len(failed),
            "summary": last,
        }
    )
    print(m["id"], verdict, failed[0] if failed else "", flush=True)


def load_mutants(a) -> list[dict]:
    if a.list:
        ms = json.loads(pathlib.Path(a.list).read_text())
    else:
        ms = [{"id": a.id, "file": a.file, "old": a.old, "new": a.new, "desc": a.desc}]
    if not isinstance(ms, list) or not ms:
        raise Refused("the mutant list is empty or not a list")
    seen = set()
    for m in ms:
        if not isinstance(m, dict) or not all(
            isinstance(m.get(k), str) for k in ("id", "file", "old", "new")
        ):
            raise Refused(f"mutant needs string fields id, file, old, new: {str(m)[:120]}")
        if not NAME_RE.fullmatch(m["id"]) or m["id"] in seen:
            raise Refused(f"mutant id is not a plain unique name: {m['id']!r}")
        seen.add(m["id"])
    return ms


def tree_check(a, root, fresh, marker) -> list[str]:
    """Differences between the scratch tree and a fresh archive; written to raw/<prefix>-tree-diff.txt."""
    diffs = diff_trees(fresh, root, set(a.extra))
    leftover = marker.exists()
    (pathlib.Path(a.raw) / f"{a.prefix}-tree-diff.txt").write_text(
        f"TREE CHECK after the loop\ncompared: <fresh git archive {a.sha} + patches {a.patch}> against {a.root} "
        f"(skipping {sorted(SKIP_DIRS)}; symbolic links compared by target)\n"
        f"declared extra files (allowed as 'only in root'): {a.extra}\n"
        f"differing files ({len(diffs)}; 0 = clean): {diffs}\nmarker left behind: {leftover}\n"
    )
    return [*diffs, *(["<marker left behind>"] if leftover else [])]


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
    ap.add_argument("--timeout", type=int, default=600, help="seconds per test run")
    ap.add_argument(
        "--pythonpath", help="only for the proof copies, whose venv .pth points at another tree"
    )
    ap.add_argument(
        "--repo",
        default=str(pathlib.Path(__file__).resolve().parent),
        help="a folder inside the repository that holds --sha (default: this script's folder)",
    )
    ap.add_argument(
        "--real-repo",
        action="append",
        default=[],
        help="a folder that must never be used as --root or inside it; repeatable",
    )
    ap.add_argument(
        "--patch",
        action="append",
        default=[],
        help="patch applied (-p1) on top of the git archive to get the expected tree; repeatable",
    )
    ap.add_argument(
        "--extra",
        action="append",
        default=[],
        help="path (relative to root) of a file that may exist in root beyond the reference, e.g. proof tests; repeatable",
    )
    ap.add_argument(
        "--restore",
        action="store_true",
        help="restore a file left planted by a killed run, then exit",
    )
    a = ap.parse_args(argv[: argv.index("--")] if "--" in argv else argv)
    root = pathlib.Path(a.root)
    if not root.is_dir():
        print(f"REFUSED: --root {root} is not a folder", file=sys.stderr)
        sys.exit(EXIT_REFUSED)
    root = root.resolve()
    a.root = str(root)
    if not a.restore and not (a.prefix and a.raw and a.sha):
        ap.error("--sha, --prefix and --raw are required")
    for signum in HANDLED_SIGNALS:
        signal.signal(signum, _term)
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = STATE / f"{key_for(root)}.planted.json"
    tmpref = pathlib.Path(tempfile.mkdtemp(prefix="mutation-ref-"))
    try:
        with (STATE / f"{key_for(root)}.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                raise Refused(
                    f"another run holds the lock for {root}; two runs on one tree would plant over each other"
                ) from e
            if a.restore:
                ok, text = restore_from_marker(root)
                print(text)
                sys.exit(0 if ok else EXIT_RESTORE_FAILED)
            refuse_real_repo(root, a.repo, a.real_repo)
            if not NAME_RE.fullmatch(a.prefix):
                raise Refused(f"--prefix is not a plain name: {a.prefix!r}")
            for x in a.extra:
                safe_rel(root, x, "--extra", must_exist=False)
            if marker.exists():
                m = json.loads(marker.read_text())
                raise Refused(
                    f"a mutant ({m['mutant']}) is still planted in {m['file']} from an earlier run that was killed. "
                    f"Restore with: python3 {sys.argv[0]} --root {root} --restore   "
                    f"(stops a leftover test run, copies {m['backup']} back and checks the hash); then run again"
                )
            ref = tmpref / "ref"
            ref.mkdir()
            build_reference(a.repo, a.sha, a.patch, ref)
            diffs = diff_trees(ref, root, set(a.extra))
            if diffs:
                raise Refused(
                    f"scratch tree differs from git archive {a.sha} + patches in {len(diffs)} file(s), first: {diffs[:3]}: it may hold a planted change; rebuild it from the archive"
                )
            ms = load_mutants(a)
            for m in ms:  # every path is checked before anything is planted
                safe_rel(root, m["file"], f"mutant {m['id']} file")
                safe_rel(ref, m["file"], f"mutant {m['id']} reference file")
            pathlib.Path(a.raw).mkdir(parents=True, exist_ok=True)
            results = []
            if a.control:
                cmd, rc, out = run_tests(root, tests, a.pythonpath, a.timeout)
                last, _ = summary(out)
                (pathlib.Path(a.raw) / f"{a.prefix}-baseline.txt").write_text(
                    f"UNMUTATED BASELINE\nbase commit: {a.sha} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nrc: {rc}\nsummary: {last}\n\n{out}"
                )
                print("baseline", rc, last)
            for m in ms:
                one(a, tests, m, results, ref)
            if a.out_json:
                pathlib.Path(a.out_json).write_text(json.dumps(results, indent=1))
            # proof the scratch tree is unchanged: compare with a FRESH archive extract
            fresh = tmpref / "fresh"
            fresh.mkdir()
            build_reference(a.repo, a.sha, a.patch, fresh)
            bad = tree_check(a, root, fresh, marker)
            print("tree diff:", len(bad), "difference(s)")
            if bad:
                print("TREE NOT CLEAN after the loop:", bad[:5], file=sys.stderr)
                sys.exit(EXIT_TREE_NOT_CLEAN)
    except Refused as e:
        print("REFUSED:", e, file=sys.stderr)
        sys.exit(EXIT_REFUSED)
    except KeyboardInterrupt as e:
        signum = e.args[0] if e.args and isinstance(e.args[0], int) else int(signal.SIGINT)
        state = (
            restore_from_marker(root)[1]
            if marker.exists()
            else "planting step restored the file and removed the marker"
        )
        print(f"INTERRUPTED (signal {signum}): {state}", file=sys.stderr)
        sys.exit(128 + signum)
    finally:
        shutil.rmtree(tmpref, ignore_errors=True)


if __name__ == "__main__":
    main()
