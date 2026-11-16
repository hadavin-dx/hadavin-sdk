#!/usr/bin/env python3
"""Hand-planted mutation runner (evidence only: it runs and records, it never judges beyond the exit code).

For ONE mutant (or a JSON list of them) in a SCRATCH copy of the code, never the real repo:
  1. read the target file, check `old` occurs exactly once, write the mutated text;
  2. run the test command with a clean environment (only PATH, HOME, PYTHONDONTWRITEBYTECODE and, if
     `--pythonpath` is given, PYTHONPATH; the raw files list the names actually used), one process, NO -x (so every killing test is listed);
  3. restore the original bytes and byte-compare with the saved copy and with the git-archive
     reference; abort if they differ. The saved copy lives in a state folder OUTSIDE any repository
     (`$TMPDIR/hadavin-mutation-lane-<uid>/`: one folder per user, refused unless it is a real folder
     owned by the user with mode 700; files in it are written atomically, read without following links), not in the lane folder, and is deleted after each mutant;
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
  * Before the loop, for every target file the module is imported in the same environment and folder the
    tests use, and the imported file must be the one under `--root` (review 4 M5); `--skip-import-check`
    turns this off and says so in every raw file. A target that is not a plain .py module path cannot be
    checked and is REFUSED too (fail closed) unless --skip-import-check is given (review r2 nit).
  * TESTS are an ALLOWLIST (review r2 safety M1): `-k EXPR`, `-m EXPR`, `-q`, `-x`, `-p no:NAME` and paths
    (optionally `::node`) that resolve inside --root. Everything else is refused: any `@file` argument,
    clustered short flags (-qc ...), --collect-only/--co/--setup-plan/--setup-only/--help/--version,
    --noconftest, --ignore, -p with anything but `no:`, -c, -o, --rootdir, --basetemp, ...
  * While a mutant is planted a signal unwinds the run only while the tests are awaited; a signal at any other
    moment is remembered and delivered after the restore, and only the first signal ever acts (review 4 M3).
    No remaining window is known, but none is proven absent: T20 is a probabilistic burst test, T21 proves
    only the handler logic (not the timing). The cleanup after a failure (stop the test group, read what it
    printed) is itself guarded: a failure to stop the group falls back to killing the leader (T29).
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
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

# skipped in the tree comparison: `.venv` ONLY directly under the root (the scratch environment); the two
# cache folders at any depth. A `.venv` deeper in the tree is compared like any other folder.
SKIP_TOP = {".venv"}
SKIP_ANY = {"__pycache__", ".pytest_cache"}
# outside every repository, one folder per user (a shared temp folder must not be shared) (review 4 M4)
STATE = pathlib.Path(tempfile.gettempdir()) / f"hadavin-mutation-lane-{os.geteuid()}"
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
SHA_RE = re.compile(r"[0-9a-fA-F]{4,64}")
HANDLED_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
# the only options a TESTS list may use (everything else is refused, see check_test_args)
PLUGIN_OFF_RE = re.compile(r"no:[A-Za-z0-9_.-]+")
STATE_PARENTS = (
    "/tmp",
    "/var/tmp",
    "/dev/shm",
)  # other places a run with another TMPDIR may have left a marker
EXIT_REFUSED, EXIT_RESTORE_FAILED, EXIT_TREE_NOT_CLEAN = 2, 3, 4


class Refused(Exception):
    pass


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class SigState:
    """Signal bookkeeping. While a mutant is planted (`critical`) a signal may unwind the run only while
    the tests are awaited (`allow`); anywhere else it is only remembered and delivered after the restore.
    Only the FIRST signal ever raises (`fired`); later ones are remembered and ignored (review 4 M3)."""

    critical = False
    allow = False
    fired = False
    first: int | None = None


SIG = SigState()


def _term(signum, frame):
    if SIG.first is None:
        SIG.first = signum
    if not SIG.fired and (SIG.allow or not SIG.critical):
        SIG.fired = True
        SIG.allow = False
        raise KeyboardInterrupt(SIG.first)  # unwinds through the `finally` that restores the file


def deliver_pending() -> None:
    """Raise the remembered first signal, once, at a point where nothing is planted or the tests are awaited."""
    if SIG.first is not None and not SIG.fired:
        SIG.fired = True
        SIG.allow = False
        raise KeyboardInterrupt(SIG.first)


def ensure_state() -> None:
    """The state folder: ours, a real folder (not a link), owner-only. Anything else is refused (review 4 M4)."""
    try:
        os.mkdir(STATE, 0o700)
    except FileExistsError:
        pass
    st = os.lstat(STATE)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid() or st.st_mode & 0o077:
        raise Refused(
            f"state folder {STATE} is not a plain folder owned by this user with mode 700: refused (remove it or fix it)"
        )


def write_state(path: pathlib.Path, data: bytes) -> None:
    """Atomic: a new private file (O_EXCL, mode 600) in the state folder, then rename over the target."""
    fd, tmp = tempfile.mkstemp(dir=STATE, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # replaces a link itself, never follows it
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise


def read_state(path: pathlib.Path) -> bytes:
    """Read a state file: no symbolic link, a regular file, owned by this user."""
    try:
        fd = os.open(
            path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        )  # a FIFO must not block the open
    except OSError as e:  # a link (ELOOP), missing, no permission: a refusal, not a traceback
        raise Refused(f"state file {path} cannot be opened safely ({e.strerror}): refused") from e
    with os.fdopen(fd, "rb") as fh:
        st = os.fstat(fh.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid():
            raise Refused(f"state file {path} is not a regular file owned by this user: refused")
        return fh.read()


def load_marker(path: pathlib.Path) -> dict:
    try:
        m = json.loads(read_state(path))
    except ValueError as e:
        raise Refused(f"marker {path} is not valid JSON: refused") from e
    if not isinstance(m, dict) or not all(
        k in m for k in ("root", "file", "backup", "orig_sha256", "mutant")
    ):
        raise Refused(f"marker {path} lacks required fields: refused")
    return m


def write_target(path: pathlib.Path, data: bytes) -> None:
    """Write the file under test without following a link at the last path part."""
    fd = os.open(path, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def decode_text(b: bytes, rel: str) -> str:
    try:
        return b.decode()
    except UnicodeDecodeError as e:
        raise Refused(f"{rel} is not UTF-8 text: cannot plant a text mutant in it") from e


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise Refused(f"required program not found: {name}")
    return found


def run_cmd(
    argv: list[str],
    input_bytes: bytes | None = None,
    cwd: pathlib.Path | None = None,
    env: dict | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    """The one place that starts a helper program (git, patch, the import probe): fixed argument list, no shell."""
    return subprocess.run(
        argv, input=input_bytes, capture_output=True, check=False, cwd=cwd, env=env, timeout=timeout
    )


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
    """Hash of every regular file; links by target; any other kind of file (FIFO, socket, device) is
    recorded by its mode and NEVER opened (opening a FIFO would block forever)."""
    out = {}
    for dp, dns, fns in os.walk(root):
        top = pathlib.Path(dp) == root
        dns[:] = [d for d in dns if d not in SKIP_ANY and not (top and d in SKIP_TOP)]
        for d in dns:
            dpath = pathlib.Path(dp) / d
            if dpath.is_symlink():  # os.walk lists but never enters it: record it (M-B)
                out[str(dpath.relative_to(root)) + "/"] = "symlinked folder:" + os.readlink(dpath)
        for f in fns:
            p = pathlib.Path(dp) / f
            rel = str(p.relative_to(root))
            mode = os.lstat(p).st_mode
            if stat.S_ISLNK(mode):
                out[rel] = "symlink:" + os.readlink(p)
            elif stat.S_ISREG(mode):
                out[rel] = sha256(p.read_bytes())
            else:
                out[rel] = f"special file, not read (mode {mode:o})"
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
    return pathlib.Path(cp.stdout.decode(errors="replace").strip()).resolve()


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


def other_state_check(root: pathlib.Path, key: str) -> tuple[bool, str]:
    """No marker in our state folder. A run that used another TMPDIR keeps its marker THERE: look in the usual
    places. A marker found there whose backup differs from the file now on disk means the file is still
    planted: not ok (exit 3). A stale marker (file already equals the backup) is reported, exit 0.
    Anything that cannot be read safely fails closed (review r2 nit)."""
    here = STATE.parent.resolve()
    spots = {
        pathlib.Path(x).resolve()
        for x in (*STATE_PARENTS, *(os.environ.get(v) or "/tmp" for v in ("TMP", "TEMP")))
    }
    notes = []
    for parent in sorted(spots - {here}):
        folder = parent / STATE.name
        if not os.path.lexists(folder / f"{key}.planted.json"):
            continue
        try:
            st = os.lstat(folder)
            if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid() or st.st_mode & 0o077:
                raise Refused(
                    f"state folder {folder} is not a plain folder owned by this user with mode 700"
                )
            m = load_marker(folder / f"{key}.planted.json")
            if m.get("root") != str(root) or m.get("backup") != str(folder / f"{key}.backup"):
                raise Refused("its marker does not belong to this root")
            saved = read_state(folder / f"{key}.backup")
            target = safe_rel(root, m["file"], "marker file")
            differs = target.read_bytes() != saved
        except (Refused, OSError) as e:
            return (
                False,
                f"a marker exists in {folder} but cannot be read safely ({e}): not touched; check by hand",
            )
        if differs:
            return False, (
                f"STILL PLANTED: {m['file']} differs from the backup kept by a run that used another TMPDIR; "
                f"restore with: TMPDIR={parent} python3 {sys.argv[0]} --root {root} --restore"
            )
        notes.append(
            f"stale marker in {folder}: {m['file']} already equals its backup (remove it by hand)"
        )
    return True, "; ".join(
        notes
    ) or f"no marker in {STATE} or in {sorted(map(str, spots - {here}))}: nothing to restore"


def restore_from_marker(root: pathlib.Path) -> tuple[bool, str]:
    ensure_state()
    key = key_for(root)
    marker = STATE / f"{key}.planted.json"
    if not os.path.lexists(marker):
        return other_state_check(root, key)
    m = load_marker(marker)
    if m.get("root") != str(root):
        raise Refused(f"marker is for another root ({m.get('root')!r}): refused")
    bk = STATE / f"{key}.backup"
    if m.get("backup") != str(bk):
        raise Refused(f"marker names a backup other than {bk}: refused")
    saved = read_state(bk)
    if sha256(saved) != m["orig_sha256"]:
        raise Refused("the saved backup does not match the hash recorded in the marker: refused")
    target = safe_rel(root, m["file"], "marker file")  # checked again right before the write
    orphan = stop_orphan(m, root)
    write_target(target, saved)
    ok = sha256(target.read_bytes()) == m["orig_sha256"]
    if ok:
        marker.unlink()
        bk.unlink(missing_ok=True)
    return ok, f"{orphan}; restored {m['file']} from {bk}; hash matches saved original: {ok}"


def test_env(pythonpath: str | None) -> dict:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    return env


def check_test_args(tests: list[str], root: pathlib.Path) -> None:
    """ALLOWLIST of what may follow `--` (review r2 safety M1): -k EXPR, -m EXPR, -q, -x, -p no:NAME and paths
    (with an optional ::node) that resolve inside root. Anything else is refused, in particular every argument
    starting with `@` (pytest reads options from that file), clustered short flags and every long option."""
    allowed = "allowed: -k EXPR, -m EXPR, -q, -x, -p no:NAME, and paths inside --root"

    def no(t: str, why: str) -> Refused:
        return Refused(f"TESTS argument {t!r} {why}: refused ({allowed})")

    def expr(flag: str, v: str | None) -> None:
        if not v or v.startswith(("@", "-")) or "\0" in v:
            raise no(f"{flag} {v or ''}".strip(), "needs a plain expression")

    real_root = root.resolve()
    i = 0
    while i < len(tests):
        t = tests[i]
        nxt = tests[i + 1] if i + 1 < len(tests) else None
        if not t or "\0" in t or t.startswith("@"):
            raise no(t, "is empty or reads arguments from a file")
        if t in ("-q", "-x"):
            pass
        elif t in ("-k", "-m"):
            expr(t, nxt)
            i += 1
        elif t[:2] in ("-k", "-m") and not t.startswith("--"):  # attached form: -kEXPR
            expr(t[:2], t[2:])
        elif t == "-p":
            if nxt is None or not PLUGIN_OFF_RE.fullmatch(nxt):
                raise no(f"-p {nxt or ''}".strip(), "may only switch a plugin off (no:NAME)")
            i += 1
        elif t.startswith("-p") and not t.startswith("--"):
            if not PLUGIN_OFF_RE.fullmatch(t[2:]):
                raise no(t, "may only switch a plugin off (no:NAME)")
        elif t.startswith("-"):
            raise no(t, "is not an allowed option")
        else:
            path = t.split("::", 1)[0]
            if not path or not (real_root / path).resolve().is_relative_to(real_root):
                raise no(t, "is not a path inside --root")
        i += 1


def module_of(rel: str) -> str | None:
    """`src/pkg/mod.py` -> `pkg.mod`; `pkg/__init__.py` -> `pkg`; None if not a plain python module path."""
    pp = pathlib.PurePosixPath(rel)
    if pp.suffix != ".py":
        return None
    parts = list(pp.parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if not parts:
        return None
    parts[-1] = pp.stem
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or not all(x.isidentifier() for x in parts):
        return None
    return ".".join(parts)


def import_check(root: pathlib.Path, pythonpath: str | None, files: list[str]) -> dict[str, str]:
    """For each target file: import its module in the SAME environment and folder the tests use and
    require that the imported file is the one under root (an editable install, a .pth file or an
    absolute path could point at another tree and make every mutant look like a survivor) (review 4 M5)."""
    py = root / ".venv/bin/python"
    if not py.exists():
        raise Refused(f"{py} does not exist: the scratch root needs its own .venv")
    out = {}
    for rel in dict.fromkeys(files):
        mod = module_of(rel)
        if (
            mod is None
        ):  # fail closed: an unchecked target could hide that the tests run another file
            raise Refused(
                f"import check: {rel!r} is not a plain .py module path, so the check cannot tell which file the "
                f"tests import; pass --skip-import-check if that is intended (it is recorded in the raw file)"
            )
        code = "import importlib,sys; m = importlib.import_module(sys.argv[1]); print(getattr(m, '__file__', '') or '')"
        try:
            cp = run_cmd(
                [str(py), "-c", code, mod], cwd=root, env=test_env(pythonpath), timeout=300
            )
        except subprocess.TimeoutExpired as e:
            raise Refused(f"import check of {mod} timed out after 300 s") from e
        if cp.returncode != 0:
            raise Refused(
                f"import check: `import {mod}` failed (rc {cp.returncode}): {text_of(cp)[-300:]}"
            )
        got = (
            cp.stdout.decode(errors="replace").strip().splitlines()[-1] if cp.stdout.strip() else ""
        )
        want = (root / rel).resolve()
        if not got or pathlib.Path(got).resolve() != want:
            raise Refused(
                f"import check: `import {mod}` loads {got!r}, not {want}: the tests would not run the mutated file; "
                f"fix the scratch environment (editable install, .pth file) or pass --pythonpath"
            )
        out[rel] = f"import {mod} -> {got} (== root/{rel}: True)"
    return out


def reap(proc: subprocess.Popen) -> str:
    try:
        return proc.communicate(timeout=30)[0] or ""
    except subprocess.TimeoutExpired:
        proc.kill()
        return ""


def run_tests(
    root: pathlib.Path,
    tests: list[str],
    pythonpath: str | None = None,
    timeout: int = 600,
    on_start=None,
):
    # stale .pyc files could hide a planted change (same size, same second): never write or reuse them
    for d in root.rglob("__pycache__"):
        if d.relative_to(root).parts[0] != ".venv":
            shutil.rmtree(d, ignore_errors=True)
    py = root / ".venv/bin/python"
    if not py.exists():
        raise Refused(f"{py} does not exist: the scratch root needs its own .venv")
    env = test_env(pythonpath)
    cmd = [str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=line", "-rf", *tests]
    # one process group, so a timeout or a signal can stop all of it
    proc = subprocess.Popen(
        cmd,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",  # bytes that are not UTF-8 must never turn a test run into an error
        start_new_session=True,
    )
    try:
        if on_start:  # inside the try: a failure here must still stop the group (review 4 M2)
            on_start(proc.pid)
        SIG.allow = True  # only now may a signal unwind us while a mutant is planted
        deliver_pending()  # a signal that came earlier (during the planting) is delivered here
        try:
            out, _ = proc.communicate(timeout=timeout)
            result = (cmd, proc.returncode, out)
        except subprocess.TimeoutExpired:
            SIG.allow = False  # first: nothing in the cleanup below may be cut short by a signal
            stop_group(proc.pid)
            rest = reap(proc)  # a second communicate() returns everything printed so far
            result = (
                cmd,
                None,
                f"TIMEOUT after {timeout} s\n--- output printed before the timeout ---\n{rest}",
            )
        SIG.allow = False
        return result
    except (
        BaseException
    ):  # a signal while the tests run, or a failure: stop the group, let the caller restore
        SIG.allow = False  # first statement: nothing below can raise a second time
        try:
            stop_group(proc.pid)  # a group that is already gone must not hide the signal
        except (
            OSError
        ):  # the group could not be stopped (e.g. no permission): at least stop the leader
            try:
                proc.kill()
            except OSError:
                pass
        finally:
            try:
                reap(proc)
            except OSError:
                pass
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
    ensure_state()
    key = key_for(root)
    backup = STATE / f"{key}.backup"
    marker = STATE / f"{key}.planted.json"
    n = decode_text(orig, m["file"]).count(m["old"])
    if n != 1:
        verdict, out, cmd, rc = f"COULD-NOT-PLANT (old text occurs {n} times)", "", [], None
        restore = "no change made"
    else:
        info = {
            "root": str(root),
            "file": m["file"],
            "backup": str(backup),
            "orig_sha256": sha256(orig),
            "mutant": f"{a.prefix}-{m['id']}",
        }

        def note_group(pgid: int) -> None:
            write_state(marker, json.dumps({**info, "pgid": pgid}).encode())

        # From here to the end of the restore a signal never unwinds the run except while the tests are
        # awaited (see SigState): a second signal cannot cut the restore short.
        SIG.critical = True
        try:
            try:
                write_state(backup, orig)
                write_state(marker, json.dumps(info).encode())
                planted = decode_text(orig, m["file"]).replace(m["old"], m["new"], 1).encode()
                write_target(p, planted)
                cmd, rc, out = run_tests(root, tests, a.pythonpath, a.timeout, note_group)
            finally:
                try:
                    p2 = safe_rel(root, m["file"], f"mutant {m['id']} file (before restore)")
                    write_target(p2, orig)
                    back = p2.read_bytes()
                    same_hash = back == orig and back == ref_bytes
                except (Refused, OSError) as e:
                    print("RESTORE ERROR:", e, file=sys.stderr)
                    same_hash = False
                if not same_hash:
                    print(
                        "RESTORE FAILED",
                        m["id"],
                        "(marker and backup kept; run --restore)",
                        file=sys.stderr,
                    )
                    sys.exit(EXIT_RESTORE_FAILED)
                # verified identical: no marker may stay, even on an error
                marker.unlink(missing_ok=True)
                backup.unlink(missing_ok=True)
        finally:
            SIG.critical = False
        deliver_pending()  # a signal that arrived during the plant is delivered now, after the restore
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
        f"command: {' '.join(cmd)}   (cwd={a.root}; environment: {', '.join(sorted(test_env(a.pythonpath)))} only)\n"
        f"import check: {a.imports.get(m['file'], 'not run')}\n"
        f"rc: {rc}\n"
        f"restore check: {restore}\n"
        f"pytest summary line: {last}\n"
        f"first failing test: {failed[0] if failed else '-'}\n"
        f"all failing tests ({len(failed)}): {'; '.join(failed) if failed else '-'}\n"
        f"--- OLD TEXT (full) ---\n{m['old']}\n--- NEW TEXT (full) ---\n{m['new']}\n--- PYTEST OUTPUT (full) ---\n{out}\n"
    )
    (pathlib.Path(a.raw) / f"{a.prefix}-{m['id']}.txt").write_text(text, encoding="utf-8")
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
        ms = json.loads(pathlib.Path(a.list).read_text(encoding="utf-8"))
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
        if m["old"] == m["new"] or not m["old"]:
            raise Refused(f"mutant {m['id']}: old text is empty or equal to new text (a no-op)")
    return ms


def tree_check(a, root, fresh, marker) -> list[str]:
    """Differences between the scratch tree and a fresh archive; written to raw/<prefix>-tree-diff.txt."""
    diffs = diff_trees(fresh, root, set(a.extra))
    leftover = marker.exists()
    (pathlib.Path(a.raw) / f"{a.prefix}-tree-diff.txt").write_text(
        f"TREE CHECK after the loop\ncompared: <fresh git archive {a.sha} + patches {a.patch}> against {a.root} "
        f"(skipping {sorted(SKIP_TOP)} directly under the root only and {sorted(SKIP_ANY)} anywhere; symbolic links compared by target; special files recorded, never read)\n"
        f"declared extra files (allowed as 'only in root'): {a.extra}\n"
        f"differing files ({len(diffs)}; 0 = clean): {diffs}\nmarker left behind: {leftover}\n",
        encoding="utf-8",
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
        "--skip-import-check",
        action="store_true",
        help="do NOT check that the tests import the target files from --root (recorded in every raw file)",
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
    marker = STATE / f"{key_for(root)}.planted.json"
    tmpref = pathlib.Path(tempfile.mkdtemp(prefix="mutation-ref-"))
    try:
        ensure_state()
        lock_fd = os.open(
            STATE / f"{key_for(root)}.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(lock_fd, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                raise Refused(
                    f"another run holds the lock for {root}; two runs on one tree would plant over each other"
                ) from e
            refuse_real_repo(
                root, a.repo, a.real_repo
            )  # --restore too: it writes into --root (review 4 M4)
            if a.restore:
                ok, text = restore_from_marker(root)
                print(text)
                sys.exit(0 if ok else EXIT_RESTORE_FAILED)
            check_test_args(tests, root)
            if not NAME_RE.fullmatch(a.prefix):
                raise Refused(f"--prefix is not a plain name: {a.prefix!r}")
            for x in a.extra:
                safe_rel(root, x, "--extra", must_exist=False)
            if os.path.lexists(marker):
                m = load_marker(marker)
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
            a.imports = (
                {m["file"]: "SKIPPED by --skip-import-check" for m in ms}
                if a.skip_import_check
                else import_check(root, a.pythonpath, [m["file"] for m in ms])
            )
            pathlib.Path(a.raw).mkdir(parents=True, exist_ok=True)
            results = []
            if a.control:
                cmd, rc, out = run_tests(root, tests, a.pythonpath, a.timeout)
                last, _ = summary(out)
                (pathlib.Path(a.raw) / f"{a.prefix}-baseline.txt").write_text(
                    f"UNMUTATED BASELINE\nbase commit: {a.sha} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nenvironment: {', '.join(sorted(test_env(a.pythonpath)))} only\nimport check: {a.imports}\nrc: {rc}\nsummary: {last}\n\n{out}",
                    encoding="utf-8",
                )
                print("baseline", rc, last)
            for m in ms:
                one(a, tests, m, results, ref)
            if a.out_json:
                pathlib.Path(a.out_json).write_text(json.dumps(results, indent=1), encoding="utf-8")
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
        # a run restores and removes its own marker before the signal leaves one(); a marker found here
        # is from another run: never touch it from a signal handler (review 4 nit)
        state = (
            f"a marker exists ({marker}); not touched here, use --restore"
            if os.path.lexists(marker)
            else "no mutant planted, no marker"
        )
        print(f"INTERRUPTED (signal {signum}): {state}", file=sys.stderr)
        sys.exit(128 + signum)
    finally:
        shutil.rmtree(tmpref, ignore_errors=True)


if __name__ == "__main__":
    main()
