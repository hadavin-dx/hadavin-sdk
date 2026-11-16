#!/usr/bin/env python3
"""Hand-planted mutation runner (evidence only: it runs and records, it never judges beyond the exit code).
LINUX ONLY (it reads /proc and uses waitid to find and stop an orphaned test run); on another system it refuses
at the start, on every option, including --restore.

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
  * Every signal that can be sent and that ends a process by default is handled (all of signal.valid_signals() except
    SIGKILL, SIGSTOP, SIGCHLD, SIGCONT, SIGWINCH, SIGURG, SIGTSTP, SIGTTIN, SIGTTOU, SIGPIPE, SIGXFSZ; review r4 M1),
    in every window: planting, tests awaited, restore (T47). A real memory fault inside this very process (SIGSEGV
    raised by the CPU, not sent by kill) cannot be handled in Python: it acts like SIGKILL, the marker stays.
  * While a mutant is planted a signal unwinds the run only while the tests are awaited; a signal at any other
    moment is remembered and delivered after the restore, and only the first signal ever acts (review 4 M3).
    No remaining window is known, but none is proven absent: T20 is a probabilistic burst test, T21 proves
    only the handler logic (not the timing). The cleanup after a failure (stop the test group, read what it
    printed) is itself guarded: a failure to stop the group falls back to killing the leader (T29).
  * A handled signal restores the file, stops the test process group, removes the marker and exits with 128 + the
    signal number (SIGTERM 143, SIGINT 130, SIGHUP 129).
  * The pytest command carries `--rootdir=<root>` and `--confcutdir=<root>`; in addition a `setup.py`, `conftest.py`
    or `pyproject.toml` in any folder ABOVE --root is refused (review r4 M2).
  * After EACH mutant the scratch tree is compared with the git archive again (all files but `.venv` directly under
    the root and the cache folders) and the result is written into that mutant's raw file; a mutant whose tests
    changed the tree (wrote a conftest.py, an ini file, data) ends the loop with exit 4 before the next mutant
    runs (review r4 M3). Files declared with --extra may exist; their content is not compared.
  * Any regular file in the tree with more than one name is refused (not only the target). The file under test is
    opened one folder at a time with O_NOFOLLOW from its parent's descriptor (a folder swapped for a link after
    the checks is refused); its content is READ by path, and the restore is verified by hash after the write.
  * After the test leader ends, processes of its group that are still alive are stopped and recorded in the raw
    file. A control run (`--control`) keeps a control marker while its tests run; if run.py is killed with
    SIGKILL, `--restore` stops the orphaned control test group.
  * `--raw`, `--out-json` and every output file: no symbolic link, regular files only, checked before planting.
  * After the loop `raw/<prefix>-tree-diff.txt` records the differences between the scratch tree and
    a FRESH `git archive` extract (+ patches). Any difference other than the declared `--extra`
    files, or a marker left behind, gives exit code 4 (M-D).
  * Hard links (review r3 safety Major B): the file under test is written in place, so a scratch tree built
    with `cp -al` or `rsync --link-dest` would plant the mutant in the file it is linked to (maybe the real
    repository). A target or reference file with more than one name (st_nlink > 1), or the same inode as its
    reference, is REFUSED before anything is planted; `write_target` re-checks on the open file descriptor,
    before the file is truncated (this also covers `--restore`).
  * pytest takes its settings from the first ini file found going UP from the test paths. If the scratch root
    has none and a folder above it has one (e.g. `addopts` in /tmp/pytest.ini), the run is REFUSED (put the
    ini inside --root, i.e. into the git archive).
  * `--restore` also recovers a target that was deleted (re-created with O_EXCL and exactly the recorded mode, whatever
    the umask), needs no git repository unless --repo is given, and clears the marker without writing if the file
    already holds the original. The
    marker records the identity of the test process (start time and full argument list from /proc): an orphaned
    group is stopped only if that identity still matches (pid reuse), or, when its leader is already gone, if
    group members started after it and work inside --root (a path argument counts only as a whole path part). If
    SIGKILL hit between the start and the marker rewrite, or the marker lacks the identity, the first marker holds
    the expected full command: the group is found by that command, in root, started after the run; with no
    command recorded nothing is stopped.
  * SIGKILL and SIGSTOP cannot be caught: use `--restore`.
NOT A SANDBOX (read this): the tests run as this user with this user's full file rights. The tool checks the
scratch tree and the files it plants into; it cannot stop a test from writing elsewhere. Paths inside --root
are trusted as a whole: `.venv` (directly under the root) and the cache folders are NOT compared, so a mutant
planted into, or a test that changes, files in them is not detected; other test files in --root run too.
Exit codes: 0 all mutants ran and the tree is clean; 2 refused; 3 restore failed (marker and backup
kept); 4 tree not clean or marker left after the loop; 128+N interrupted by signal N.
Verdict per mutant from the pytest exit code: 0 SURVIVED, 1 KILLED, anything else ERROR.

Usage:
  run.py --root /tmp/c8/wC --sha b4cce5b --prefix C-01 --raw DIR --list mutants.json -- TESTS...
  run.py --root ... --sha ... --prefix C-01 --raw DIR --id m01 --file src/x.py --old "a" --new "b" -- TESTS...
mutants.json: [{"id": "m01", "file": "...", "old": "...", "new": "...", "desc": "..."}, ...]
`--control` runs the unmutated tree once first and records it as <prefix>-baseline.txt.
TESTS are pytest arguments (paths / -k ...). The command run is, with only the environment named above:
  <root>/.venv/bin/python -m pytest -q -p no:cacheprovider --rootdir=<root> --confcutdir=<root> --tb=line -rf TESTS
"""

import argparse
import configparser
import errno
import fcntl
import hashlib
import io
import json
import os
import pathlib
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib

# skipped in the tree comparison: `.venv` ONLY directly under the root (the scratch environment); the two
# cache folders at any depth. A `.venv` deeper in the tree is compared like any other folder.
SKIP_TOP = {".venv"}
SKIP_ANY = {"__pycache__", ".pytest_cache"}
# outside every repository, one folder per user (a shared temp folder must not be shared) (review 4 M4)
STATE = pathlib.Path(tempfile.gettempdir()) / f"hadavin-mutation-lane-{os.geteuid()}"
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
SHA_RE = re.compile(r"[0-9a-fA-F]{4,64}")
# Every signal that can be sent to a process, except the ones named here (review r4 M1). Not handled, with the reason:
# SIGKILL and SIGSTOP cannot be caught; SIGCHLD (a child changed state), SIGCONT, SIGWINCH and SIGURG are
# informational and do not end the process; SIGTSTP, SIGTTIN and SIGTTOU only stop it; SIGPIPE and SIGXFSZ are
# turned into ordinary errors by Python. All the rest (including SIGTRAP, SIGSYS, SIGSTKFLT, all real-time
# signals and SIGSEGV/SIGBUS/SIGFPE/SIGILL when another process sends them with kill()) end the process by
# default, so each one is caught: the file is restored first. A real memory fault inside this very process
# cannot be handled in Python (the faulting instruction would run again); that case is the SIGKILL case:
# the marker stays and `--restore` recovers.
_NOT_HANDLED = frozenset(
    getattr(signal, n)
    for n in (
        "SIGKILL",
        "SIGSTOP",
        "SIGCHLD",
        "SIGCONT",
        "SIGWINCH",
        "SIGURG",
        "SIGTSTP",
        "SIGTTIN",
        "SIGTTOU",
        "SIGPIPE",
        "SIGXFSZ",
    )
    if hasattr(signal, n)
)
HANDLED_SIGNALS = tuple(sorted(int(x) for x in signal.valid_signals() if x not in _NOT_HANDLED))
# `-p no:NAME` may only switch off one of these (review r3 safety Major A: `-p no:runner` runs NO test and every
# mutant would look like a survivor; `no:skipping`, `no:python`, `no:terminal`, `no:mark` change what is run or
# reported). A fixed set, exact names: every core plugin is refused by not being in it.
PLUGINS_OFF_ALLOWED = frozenset({"randomly", "xdist", "cov", "cacheprovider"})
# files from which pytest takes its settings (looked up going up from the test paths)
PYTEST_INI_NAMES = ("pytest.ini", ".pytest.ini", "pytest.toml", ".pytest.toml")
PYTEST_INI_SECTIONS = (("tox.ini", "pytest"), ("setup.cfg", "tool:pytest"))  # (file, section name)
# files that must not exist in any folder ABOVE --root (review r4 M2)
ABOVE_ROOT_FILES = ("setup.py", "conftest.py", "pyproject.toml")
# other places a run with another TMPDIR may have left a marker (built from parts, not typed as literals)
STATE_PARENTS = tuple(
    pathlib.Path(os.sep, *parts) for parts in (("tmp",), ("var", "tmp"), ("dev", "shm"))
)
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


def check_single_link(path: pathlib.Path, what: str) -> None:
    """A file with more than one name is refused: writing it in place changes every name (review r3 safety B)."""
    st = os.lstat(path)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise Refused(
            f"{what} {path} is not a regular file with exactly one name (links: {st.st_nlink}): "
            f"a hard-linked scratch tree would plant the mutant in the file it is linked to: refused"
        )


def _open_parent(
    root: pathlib.Path | None, path: pathlib.Path, create_dirs: bool
) -> tuple[int, str]:
    """Open the folder that holds `path` one component at a time with O_NOFOLLOW and dir_fd, starting at `root`
    (or, with no root, at the parent folder itself): a folder swapped for a symbolic link after the path checks
    is refused, never followed (review r4 nit 3). Returns (fd of the parent folder, last name)."""
    if root is None:
        base, parts = path.parent, []
    else:
        base = root
        try:
            parts = list(path.parent.relative_to(root).parts)
        except ValueError as e:
            raise Refused(f"{path} is not inside {root}: not written") from e
    dflags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            try:
                nxt = os.open(part, dflags, dir_fd=fd)
            except FileNotFoundError:
                if not create_dirs:
                    raise
                os.mkdir(part, 0o755, dir_fd=fd)
                nxt = os.open(part, dflags, dir_fd=fd)
            except OSError as e:
                if e.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise Refused(
                        f"{path}: the folder {part!r} is a symbolic link or not a folder: not written"
                    ) from e
                raise
            os.close(fd)
            fd = nxt
        return fd, path.name
    except BaseException:
        os.close(fd)
        raise


def write_target(
    path: pathlib.Path,
    data: bytes,
    create: bool = False,
    mode: int = 0o644,
    root: pathlib.Path | None = None,
    on_open=None,
) -> None:
    """Write the file under test in place. No link is followed at any path part below `root` (each folder is
    opened with O_NOFOLLOW from its parent's descriptor), the open cannot block on a FIFO (O_NONBLOCK), and the
    checks are made on the OPEN file, before anything is truncated: it must be a regular file with exactly one
    name (a hard link would write through to another tree). `on_open` is called after those checks and just
    before the file is truncated: only from then on has the file been touched. `create=True` (restore only)
    re-creates a deleted file (and missing folders) with O_EXCL and sets exactly `mode` (umask does not apply)."""
    pfd, name = _open_parent(root, path, create)
    try:
        flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        created = False
        try:
            fd = os.open(name, flags, dir_fd=pfd)
        except FileNotFoundError:
            if not create:
                raise
            fd = os.open(name, flags | os.O_CREAT | os.O_EXCL, mode, dir_fd=pfd)
            created = True
        except OSError as e:
            if e.errno == errno.ENXIO:  # a FIFO with no reader
                raise Refused(f"{path} is not a regular file (a FIFO): not written") from e
            if e.errno == errno.ELOOP:
                raise Refused(f"{path} is a symbolic link: not written") from e
            raise
    finally:
        os.close(pfd)
    with os.fdopen(fd, "wb") as fh:
        st = os.fstat(fh.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise Refused(
                f"{path} is not a regular file with exactly one name (links: {st.st_nlink}): not written"
            )
        if created:
            os.fchmod(
                fh.fileno(), mode
            )  # the umask of the caller must not change the recorded mode
        if on_open is not None:
            on_open()
        fh.truncate(0)
        fh.write(data)


def read_regular(path: pathlib.Path) -> bytes:
    """Read a file without following a link at the last part and without blocking on a FIFO."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as e:
        raise Refused(f"{path} cannot be opened safely ({e.strerror}): refused") from e
    with os.fdopen(fd, "rb") as fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise Refused(f"{path} is not a regular file: refused")
        return fh.read()


def write_out(path: pathlib.Path, text: str) -> None:
    """Write an output file (raw file, baseline, tree diff, --out-json): never through a symbolic link, only to a
    regular file (review r4 nit 11)."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644)
    except OSError as e:
        raise Refused(f"output file {path} cannot be written safely ({e.strerror}): refused") from e
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise Refused(f"output file {path} is not a regular file: refused")
        fh.truncate(0)
        fh.write(text)


def check_out_path(path: pathlib.Path) -> None:
    """Before anything is planted: an output path must not be a symbolic link or a special file."""
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Refused(f"output path {path} is a symbolic link or not a regular file: refused")


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
                out[rel] = sha256(read_regular(p))
            else:
                out[rel] = f"special file, not read (mode {mode:o})"
    return out


def mount_points(text: str | None = None) -> list[pathlib.Path]:
    """Mount points from /proc/self/mountinfo (field 5; space, tab, newline and backslash are written as octal).
    `text` replaces the file (for tests)."""
    out = []
    if text is None:
        text = pathlib.Path("/proc/self/mountinfo").read_text(errors="replace")
    for line in text.splitlines():
        parts = line.split(" ")
        if len(parts) > 4:
            out.append(
                pathlib.Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), parts[4]))
            )
    return out


def refuse_mounts(root: pathlib.Path) -> None:
    """Nothing may be mounted INSIDE the scratch tree (a bind mount of another tree would show another tree's
    files under a name with one link; review r4 nit 4). The root itself may be a mount point; `.venv` directly
    under the root is skipped as everywhere else."""
    for mp in mount_points():
        if mp != root and mp.is_relative_to(root) and mp.relative_to(root).parts[0] not in SKIP_TOP:
            raise Refused(
                f"{mp.relative_to(root)} is a mount point inside --root {root}: it shows another tree's files "
                f"inside the scratch tree: refused"
            )


def refuse_hard_links(root: pathlib.Path) -> None:
    """Every regular file in the tree (not just the target) must have exactly one name: a tree built with
    `cp -al` or a bind mount of another tree shares files that a test or a mutant could change in place
    (review r4 nit 4). `.venv` directly under the root and the cache folders are skipped as everywhere else."""
    for dp, dns, fns in os.walk(root):
        top = pathlib.Path(dp) == root
        dns[:] = [d for d in dns if d not in SKIP_ANY and not (top and d in SKIP_TOP)]
        for f in fns:
            p = pathlib.Path(dp) / f
            st = os.lstat(p)
            if stat.S_ISREG(st.st_mode) and st.st_nlink != 1:
                raise Refused(
                    f"{p.relative_to(root)} is not a regular file with exactly one name (links: {st.st_nlink}): "
                    f"a hard-linked scratch tree shares files with another tree: refused"
                )


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


def refuse_real_repo(root: pathlib.Path, repo: str | None, extra_real: list[str]) -> None:
    """`repo` None (only for --restore with no --repo given): the repository of --repo is not looked up, so a
    restore needs no git repository; the other checks (this script's repository, --real-repo, a .git entry in or
    above the root, git's own answer for the root) still apply."""
    if not root.is_dir():
        raise Refused(f"--root {root} is not a folder")
    root = root.resolve()
    real = {*(pathlib.Path(x).resolve() for x in extra_real)}
    if repo is not None:
        real.add(repo_toplevel(repo))
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


def proc_stat(pid: int) -> dict | None:
    """From /proc/<pid>/stat: state, parent, process group, session, start time (clock ticks since boot).
    The name field may hold spaces and brackets, so the fields are counted from the LAST closing bracket."""
    try:
        data = pathlib.Path(f"/proc/{pid}/stat").read_text(errors="replace")
        rest = data[data.rindex(")") + 2 :].split()
        return {
            "state": rest[0],
            "ppid": int(rest[1]),
            "pgrp": int(rest[2]),
            "sid": int(rest[3]),
            "start": int(rest[19]),
        }
    except (OSError, ValueError, IndexError):
        return None


def proc_argv(pid: int) -> list[str] | None:
    try:
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return None
    return raw.decode(errors="replace").split("\0")[:-1] if raw else []


def proc_identity(pid: int) -> dict:
    """What identifies this very process later (a pid alone can be reused): start time and full argument list."""
    st, argv = proc_stat(pid), proc_argv(pid)
    return {} if st is None or not argv else {"start_ticks": st["start"], "argv": argv}


def group_members(pgid: int) -> list[int]:
    """Live processes of the process group (and session) `pgid`, zombies left out."""
    out = []
    for d in pathlib.Path("/proc").iterdir():
        if d.name.isdigit():
            st = proc_stat(int(d.name))
            if st and st["pgrp"] == pgid and st["sid"] == pgid and st["state"] != "Z":
                out.append(int(d.name))
    return out


def works_in(pid: int, root: pathlib.Path) -> bool:
    """The process runs inside root: its folder is root or under it, or an argument IS root or a path under it
    (exact path match on whole path parts: /x/wCD does not count as /x/wC; review r4 nit 7)."""
    try:
        if pathlib.Path(os.readlink(f"/proc/{pid}/cwd")).is_relative_to(root):
            return True
    except OSError:
        pass
    prefix = str(root) + os.sep
    return any(a == str(root) or a.startswith(prefix) for a in proc_argv(pid) or [])


def unreaped_child(pid: int) -> bool:
    """True while `pid` is our own child that nobody has waited for yet (running or zombie). Once it is reaped
    its number may be given to another process, and a signal to that group would hit a stranger (review r3)."""
    try:
        os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return False
    return True


def orphan_candidates(m: dict, root: pathlib.Path) -> list[int]:
    """Process groups that are provably this run's test group (a killed run may leave several things behind)."""
    pgid, rec_start, rec_argv = m.get("pgid"), m.get("start_ticks"), m.get("argv")
    if (
        isinstance(pgid, int)
        and pgid > 1
        and isinstance(rec_start, int)
        and isinstance(rec_argv, list)
    ):
        st = proc_stat(pgid)
        if (
            st and st["state"] != "Z"
        ):  # the leader still exists: must be exactly the process we started
            same = st["start"] == rec_start and proc_argv(pgid) == rec_argv
            return [pgid] if same and st["pgrp"] == pgid and st["sid"] == pgid else []
        # leader gone (pid not in use or a zombie): its group may live on while members exist. A pid cannot be
        # given to a new group while members live, so members are ours if they started after the leader
        # and work in root
        alive = [
            q
            for q in group_members(pgid)
            if (qs := proc_stat(q)) and qs["start"] >= rec_start and works_in(q, root)
        ]
        return [pgid] if alive else []
    # No group recorded (SIGKILL between the start and the marker rewrite), or a marker with a group but without
    # its identity (review r4 nit 7): find a session leader that runs exactly the command the first marker
    # names (full argument list when recorded, else its first words), in root, started after this run did.
    # Never a guess: without the command and the start time of the run nothing is stopped.
    head, full, run_start = m.get("cmd_head"), m.get("cmd_argv"), m.get("run_start_ticks")
    want = full if isinstance(full, list) else head
    if not isinstance(want, list) or not want or not isinstance(run_start, int):
        return []
    found = []
    for d in pathlib.Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        q = int(d.name)
        st = proc_stat(q)
        argv = proc_argv(q) or []
        if (
            st
            and st["state"] != "Z"
            and st["pgrp"] == q == st["sid"]
            and st["start"] >= run_start
            and (argv == want if isinstance(full, list) else argv[: len(want)] == want)
            and works_in(q, root)
        ):
            found.append(q)
    return found


def stop_orphan(m: dict, root: pathlib.Path) -> str:
    """After a SIGKILL of run.py the test group may still run: stop it, but only if it is ours (start time and
    full argument list recorded in the marker must match; review r3 minors). A failure to stop it is reported,
    never allowed to abort the restore of the file."""
    pgid = m.get("pgid")
    if not isinstance(pgid, int) and not m.get("cmd_head") and not m.get("cmd_argv"):
        return "no test group recorded"
    if isinstance(pgid, int) and pgid <= 1:
        return "no test group recorded"
    groups = orphan_candidates(m, root)
    if not groups:
        leader = proc_stat(pgid) if isinstance(pgid, int) else None
        if (
            isinstance(pgid, int)
            and (leader is None or leader["state"] == "Z")
            and not group_members(pgid)
        ):
            return "test group already gone"
        what = f"process {pgid}" if isinstance(pgid, int) else "no process"
        return f"{what} is not this run's pytest (or cannot be verified): left alone"
    notes = []
    for g in groups:
        try:
            stop_group(g)
        except OSError as e:
            notes.append(f"could NOT stop test group {g} ({e.strerror or e}): file restored anyway")
            continue
        for _ in range(50):
            if not group_members(g):
                break
            time.sleep(0.1)
        notes.append(f"stopped orphaned test group {g}")
    return "; ".join(notes)


def other_state_check(root: pathlib.Path, key: str) -> tuple[bool, str]:
    """No marker in our state folder. A run that used another TMPDIR keeps its marker THERE: look in the usual
    places. A marker found there whose backup differs from the file now on disk means the file is still
    planted: not ok (exit 3). A stale marker (file already equals the backup) is reported, exit 0.
    Anything that cannot be read safely fails closed (review r2 nit)."""
    here = STATE.parent.resolve()
    spots = {p.resolve() for p in STATE_PARENTS}
    spots |= {pathlib.Path(v).resolve() for v in map(os.environ.get, ("TMP", "TEMP")) if v}
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
            differs = read_regular(target) != saved
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


def control_marker_path(key: str) -> pathlib.Path:
    return STATE / f"{key}.control.json"


def restore_control(root: pathlib.Path, key: str) -> str:
    """A control run (nothing planted) that was killed with SIGKILL leaves its test group running: the control
    marker names it. Stop it only if it is provably ours (same checks as for a planted run), then remove the
    marker (review r4 nit 5)."""
    path = control_marker_path(key)
    m = json.loads(read_state(path)) if os.path.lexists(path) else None
    if not isinstance(m, dict) or m.get("root") != str(root):
        raise Refused(f"control marker {path} is not for this root: refused")
    note = stop_orphan(m, root)
    path.unlink()
    return f"control run: {note}"


def restore_from_marker(root: pathlib.Path) -> tuple[bool, str]:
    ensure_state()
    key = key_for(root)
    marker = STATE / f"{key}.planted.json"
    control = restore_control(root, key) if os.path.lexists(control_marker_path(key)) else None
    if not os.path.lexists(marker):
        ok, text = other_state_check(root, key)
        return ok, f"{control}; {text}" if control else text
    m = load_marker(marker)
    if m.get("root") != str(root):
        raise Refused(f"marker is for another root ({m.get('root')!r}): refused")
    bk = STATE / f"{key}.backup"
    if m.get("backup") != str(bk):
        raise Refused(f"marker names a backup other than {bk}: refused")
    saved = read_state(bk)
    if sha256(saved) != m["orig_sha256"]:
        raise Refused("the saved backup does not match the hash recorded in the marker: refused")
    # must_exist=False: a deleted target is re-created (review r3 minor); checked again right before the write
    target = safe_rel(root, m["file"], "marker file", must_exist=False)
    orphan = stop_orphan(m, root)
    mode = m.get("mode") if isinstance(m.get("mode"), int) and 0 <= m["mode"] <= 0o777 else 0o644
    try:
        try:
            already = (
                read_regular(target) == saved
            )  # the file already holds the original: nothing to write
        except (Refused, FileNotFoundError):
            already = False
        if not already:
            write_target(target, saved, create=True, mode=mode, root=root)
        ok = sha256(read_regular(target)) == m["orig_sha256"]
    except OSError as e:
        raise Refused(f"cannot write {m['file']} back: {e.strerror or e}: refused") from e
    if ok:
        marker.unlink()
        bk.unlink(missing_ok=True)
    note = " (it already held the original)" if already else ""
    text = f"{orphan}; restored {m['file']} from {bk}{note}; hash matches saved original: {ok}"
    return ok, f"{control}; {text}" if control else text


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
    """ALLOWLIST of what may follow `--` (review r2 safety M1): -k EXPR, -m EXPR, -q, -x, -p no:NAME (NAME from
    the fixed set PLUGINS_OFF_ALLOWED, review r3 Major A) and paths
    (with an optional ::node) that resolve inside root. Anything else is refused, in particular every argument
    starting with `@` (pytest reads options from that file), clustered short flags and every long option."""
    allowed = f"allowed: -k EXPR, -m EXPR, -q, -x, -p no:NAME with NAME one of {sorted(PLUGINS_OFF_ALLOWED)}, and paths inside --root"
    off_why = f"may only switch off one of the plugins {sorted(PLUGINS_OFF_ALLOWED)} (no:NAME)"

    def plugin_off_ok(v: str) -> bool:
        return v.startswith("no:") and v[3:] in PLUGINS_OFF_ALLOWED

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
            if nxt is None or not plugin_off_ok(nxt):
                raise no(f"-p {nxt or ''}".strip(), off_why)
            i += 1
        elif t.startswith("-p") and not t.startswith("--"):
            if not plugin_off_ok(t[2:]):
                raise no(t, off_why)
        elif t.startswith("-"):
            raise no(t, "is not an allowed option")
        else:
            path = t.split("::", 1)[0]
            if not path or not (real_root / path).resolve().is_relative_to(real_root):
                raise no(t, "is not a path inside --root")
        i += 1


def pytest_config_in(d: pathlib.Path) -> list[str]:
    """Names of the files in folder `d` from which pytest would take settings. Files are parsed, not searched for
    a text, so dotted keys (`tool.pytest.ini_options.x = ...`) and inline tables count too; a file that cannot be
    read or parsed counts as holding settings (fail closed)."""
    found = [n for n in PYTEST_INI_NAMES if (d / n).is_file()]
    f = d / "pyproject.toml"
    if f.is_file():
        try:
            tool = tomllib.loads(f.read_text(encoding="utf-8")).get("tool")
            if isinstance(tool, dict) and "pytest" in tool:
                found.append("pyproject.toml")
        except (OSError, ValueError):  # unreadable, not UTF-8, not valid TOML
            found.append("pyproject.toml (unreadable)")
    for name, section in PYTEST_INI_SECTIONS:
        f = d / name
        if f.is_file():
            try:
                cp = configparser.ConfigParser(interpolation=None, strict=False)
                cp.read_string(f.read_text(encoding="utf-8"))
                if cp.has_section(section):
                    found.append(name)
            except (OSError, ValueError, configparser.Error):
                found.append(f"{name} (unreadable)")
    return found


def check_pytest_config(root: pathlib.Path, tests: list[str]) -> None:
    """Two checks. (1) Above --root there must be no `setup.py`, `conftest.py` or `pyproject.toml` at all: pytest
    takes its root folder from a setup.py or a pyproject.toml without a pytest section, and loads a conftest.py
    from every folder up to its root (review r4 M2). The pytest command also carries --rootdir and --confcutdir
    set to --root, so those files could not act even if present; they are refused as well (second lock).
    (2) pytest looks for its ini file going UP from the common folder of the test paths. If the first one found
    lies above --root (e.g. `addopts` in /tmp/pytest.ini) the settings would come from outside the scratch
    tree and could change what runs: refused (review r3 minor). An ini inside --root is part of the archive."""
    root = root.resolve()
    for d in root.parents:
        for name in ABOVE_ROOT_FILES:
            if (d / name).exists() or (d / name).is_symlink():
                raise Refused(
                    f"{d / name} lies outside --root {root} and above it: pytest could take its root folder, "
                    f"settings or a conftest from it and change what runs; move the scratch tree "
                    f"or remove the file: refused"
                )
    dirs = []
    for t in tests:
        if not t.startswith("-"):
            q = (root / t.split("::", 1)[0]).resolve()
            dirs.append(q if q.is_dir() else q.parent)
    start = pathlib.Path(os.path.commonpath([str(d) for d in dirs])) if dirs else root
    if not start.is_relative_to(root):
        start = root
    for d in (start, *start.parents):
        found = pytest_config_in(d)
        if found:
            if d == root or d.is_relative_to(root):
                return
            raise Refused(
                f"pytest would take its settings from {d / found[0]}, outside --root {root}: "
                f"the run could be changed from outside the scratch tree; put the ini file into the "
                f"scratch tree (it must be part of the git archive) or remove it: refused"
            )


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


def reap(proc: subprocess.Popen, wait: int = 30) -> str:
    """Collect what the test run printed. If it does not end in `wait` seconds the leader is killed AND waited
    for (no zombie, and its number is not left to be reused while we still hold the handle)."""
    try:
        return proc.communicate(timeout=wait)[0] or ""
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            return proc.communicate(timeout=10)[0] or ""
        except subprocess.TimeoutExpired:
            return ""


def stop_or_kill(proc: subprocess.Popen) -> None:
    """Stop the whole test group; if that is not allowed, at least the leader. Never raises OSError."""
    try:
        stop_group(proc.pid)
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def sweep_group(pgid: int) -> str:
    """After the leader has ended: stop what is still alive in its process group (a test may have started a
    background process). While any member lives the number cannot be given to another group, so the members are
    this run's own (review r4 nit 5). Returns a line for the raw file."""
    left = group_members(pgid)
    if not left:
        return "no process of the test group left after the leader ended"
    stop_group(pgid)
    for _ in range(50):
        if not group_members(pgid):
            break
        time.sleep(0.1)
    return f"STOPPED {len(left)} process(es) of the test group that outlived the leader: {left}"


def pytest_cmd(root: pathlib.Path, tests: list[str]) -> list[str]:
    """The one pytest command line. --rootdir and --confcutdir pin pytest's root folder and the highest folder
    from which a conftest.py is loaded to --root, so nothing above the scratch tree can change what runs."""
    return [
        str(root / ".venv/bin/python"),
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        f"--rootdir={root}",
        f"--confcutdir={root}",
        "--tb=line",
        "-rf",
        *tests,
    ]


def run_tests(
    root: pathlib.Path,
    tests: list[str],
    pythonpath: str | None = None,
    timeout: int = 600,
    on_start=None,
):
    """Returns (command, exit code or None on timeout, output, sweep note)."""
    # stale .pyc files could hide a planted change (same size, same second): never write or reuse them
    for d in root.rglob("__pycache__"):
        if d.relative_to(root).parts[0] != ".venv":
            shutil.rmtree(d, ignore_errors=True)
    py = root / ".venv/bin/python"
    if not py.exists():
        raise Refused(f"{py} does not exist: the scratch root needs its own .venv")
    env = test_env(pythonpath)
    cmd = pytest_cmd(root, tests)
    # From the start of the child to the first statement of the `try` below a signal is only REMEMBERED (critical),
    # never raised: a raise between the fork and `proc = ...` would leave the new group running with nobody to
    # stop it (review r3 minor, control run). It is delivered inside the `try`, where the group is stopped.
    was_critical = SIG.critical
    SIG.critical = True
    try:
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
    except BaseException:
        SIG.critical = was_critical
        raise
    try:
        SIG.critical = was_critical
        deliver_pending()  # a signal remembered during the start (control run: nothing is planted)
        if on_start:  # inside the try: a failure here must still stop the group (review 4 M2)
            on_start(proc.pid)
        SIG.allow = True  # only now may a signal unwind us while a mutant is planted
        deliver_pending()  # a signal that came earlier (during the planting) is delivered here
        try:
            out, _ = proc.communicate(timeout=timeout)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            SIG.allow = False  # first: nothing in the cleanup below may be cut short by a signal
            stop_or_kill(
                proc
            )  # a failure to stop the group is no reason to lose the result (review r4 T46)
            rest = reap(proc)  # a second communicate() returns everything printed so far
            out = f"TIMEOUT after {timeout} s\n--- output printed before the timeout ---\n{rest}"
            rc = None
        SIG.allow = False
        try:
            note = sweep_group(proc.pid)
        except OSError as e:
            note = f"could NOT sweep the test group ({e.strerror or e})"
        return (cmd, rc, out, note)
    except (
        BaseException
    ):  # a signal while the tests run, or a failure: stop the group, let the caller restore
        SIG.allow = False  # first statement: nothing below can raise a second time
        # Once the leader has been waited for (communicate returned just before the signal) its number may belong
        # to a stranger: then nothing is signalled (review r3 minor, pid reuse after reap).
        try:
            if proc.returncode is None and unreaped_child(proc.pid):
                stop_group(proc.pid)  # a group that is already gone must not hide the signal
            elif proc.returncode is not None:
                sweep_group(proc.pid)  # leader ended already: stop members that outlived it
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
            except (OSError, ValueError):
                pass
        raise


def summary(out: str):
    lines = [x for x in out.splitlines() if x.strip()]
    last = lines[-1] if lines else ""
    failed = [x.split(" ", 1)[1].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    return last, failed


def tree_digest(files: dict[str, str]) -> str:
    return sha256(json.dumps(sorted(files.items())).encode())[:16]


def one(a, tests, m, results, ref) -> list[str]:
    """Runs one mutant. Returns the files that differ from the reference after the restore (must be empty)."""
    root = pathlib.Path(a.root)
    p = safe_rel(root, m["file"], f"mutant {m['id']} file")
    refp = safe_rel(ref, m["file"], f"mutant {m['id']} reference file")
    check_single_link(p, f"mutant {m['id']} target")
    check_single_link(refp, f"mutant {m['id']} reference")
    sp, sr = os.lstat(p), os.lstat(refp)
    if (sp.st_dev, sp.st_ino) == (sr.st_dev, sr.st_ino):
        raise Refused(f"mutant {m['id']}: {m['file']} and its reference are the same file")
    orig = read_regular(p)
    ref_bytes = read_regular(refp)
    if orig != ref_bytes:  # hash baseline from git archive, not from the file on disk
        raise Refused(
            f"{m['file']} differs from the git archive reference (sha256 {sha256(orig)[:12]} vs {sha256(ref_bytes)[:12]}): refusing"
        )
    ensure_state()
    key = key_for(root)
    backup = STATE / f"{key}.backup"
    marker = STATE / f"{key}.planted.json"
    n = decode_text(orig, m["file"]).count(m["old"])
    sweep = "not run"
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
            "mode": stat.S_IMODE(sp.st_mode),
            # first marker (before the tests start): what to look for if SIGKILL comes before the second one
            "cmd_head": [str(root / ".venv/bin/python"), "-m", "pytest"],
            "cmd_argv": pytest_cmd(root, tests),
            "run_start_ticks": (proc_stat(os.getpid()) or {}).get("start"),
        }

        def note_group(pgid: int) -> None:
            # second marker: the group and its identity (start time, full argument list), see stop_orphan
            write_state(marker, json.dumps({**info, "pgid": pgid, **proc_identity(pgid)}).encode())

        # From here to the end of the restore a signal never unwinds the run except while the tests are
        # awaited (see SigState): a second signal cannot cut the restore short.
        SIG.critical = True
        try:
            try:
                write_state(backup, orig)
                write_state(marker, json.dumps(info).encode())
                planted = decode_text(orig, m["file"]).replace(m["old"], m["new"], 1).encode()
                try:
                    write_target(p, planted, root=root)
                except (
                    OSError
                ) as e:  # e.g. a read-only file: a refusal, the restore below checks the bytes
                    raise Refused(f"cannot plant into {m['file']}: {e.strerror or e}") from e
                cmd, rc, out, sweep = run_tests(root, tests, a.pythonpath, a.timeout, note_group)
            finally:
                try:
                    p2 = safe_rel(root, m["file"], f"mutant {m['id']} file (before restore)")
                    # write only if the bytes differ (review r4 nit 1): a file that was never touched (refused
                    # open, read-only) is not written again, so a refusal is not reported as a failed restore
                    if read_regular(p2) != orig:
                        write_target(p2, orig, root=root)
                    back = read_regular(p2)
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
    # integrity of the whole scratch tree after this mutant (review r4 M3): every file but .venv and the caches
    # against the fresh git archive; a test that wrote a conftest.py, an ini file or data would contaminate the
    # next mutant. Files declared with --extra are allowed to exist (their content is not compared).
    now, extra = tree_files(root), set(a.extra)
    diffs = [
        f
        for f in sorted(set(a.ref_files) | set(now))
        if a.ref_files.get(f) != now.get(f) and not (f in extra and f not in a.ref_files)
    ]
    integrity = (
        f"{len(now)} files compared with the git archive (all but .venv directly under the root and the cache "
        f"folders), digest {tree_digest(now)}; differing files ({len(diffs)}; 0 = clean): {diffs}"
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
        f"tree integrity after this mutant: {integrity}\n"
        f"test group after the leader ended: {sweep}\n"
        f"pytest summary line: {last}\n"
        f"first failing test: {failed[0] if failed else '-'}\n"
        f"all failing tests ({len(failed)}): {'; '.join(failed) if failed else '-'}\n"
        f"--- OLD TEXT (full) ---\n{m['old']}\n--- NEW TEXT (full) ---\n{m['new']}\n--- PYTEST OUTPUT (full) ---\n{out}\n"
    )
    write_out(pathlib.Path(a.raw) / f"{a.prefix}-{m['id']}.txt", text)
    results.append(
        {
            "id": m["id"],
            "desc": m.get("desc", ""),
            "verdict": verdict,
            "rc": rc,
            "first": failed[0] if failed else "",
            "n_failed": len(failed),
            "summary": last,
            "tree_differences": diffs,
        }
    )
    print(m["id"], verdict, failed[0] if failed else "", flush=True)
    return diffs


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
    write_out(
        pathlib.Path(a.raw) / f"{a.prefix}-tree-diff.txt",
        f"TREE CHECK after the loop\ncompared: <fresh git archive {a.sha} + patches {a.patch}> against {a.root} "
        f"(skipping {sorted(SKIP_TOP)} directly under the root only and {sorted(SKIP_ANY)} anywhere; symbolic links compared by target; special files recorded, never read)\n"
        f"declared extra files (allowed as 'only in root'): {a.extra}\n"
        f"differing files ({len(diffs)}; 0 = clean): {diffs}\nmarker left behind: {leftover}\n",
    )
    return [*diffs, *(["<marker left behind>"] if leftover else [])]


def restore_args(a, repo_given: bool) -> str:
    """The extra words of the restore command that make it equal to this run's own checks (--repo and
    --real-repo are what refuse a root inside the real repository), review r4 nit 10."""
    words = (["--repo", a.repo] if repo_given else []) + [
        w for x in a.real_repo for w in ("--real-repo", x)
    ]
    return "".join(f" {shlex.quote(w)}" for w in words)


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
        default=None,
        help="a folder inside the repository that holds --sha (default: this script's folder; "
        "--restore needs no repository unless --repo is given)",
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
    if not sys.platform.startswith("linux") or not pathlib.Path("/proc/self/stat").is_file():
        print(
            "REFUSED: this tool works on Linux only (it reads /proc to identify and stop an orphaned test run "
            "and uses waitid); on this system a --restore could not stop a leftover test run: refused",
            file=sys.stderr,
        )
        sys.exit(EXIT_REFUSED)
    repo_given = a.repo is not None
    default_repo = str(pathlib.Path(__file__).resolve().parent)
    if not a.restore or repo_given:
        a.repo = a.repo or default_repo
    root = pathlib.Path(a.root)
    if not root.is_dir():
        print(f"REFUSED: --root {root} is not a folder", file=sys.stderr)
        sys.exit(EXIT_REFUSED)
    root = root.resolve()
    a.root = str(root)
    if not a.restore and not (a.prefix and a.raw and a.sha):
        ap.error("--sha, --prefix and --raw are required")
    for signum in HANDLED_SIGNALS:
        try:
            signal.signal(signum, _term)
        except (OSError, ValueError):  # a signal the C library keeps for itself (32, 33 on Linux)
            pass
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
            check_pytest_config(root, tests)
            refuse_hard_links(root)
            refuse_mounts(root)
            if not NAME_RE.fullmatch(a.prefix):
                raise Refused(f"--prefix is not a plain name: {a.prefix!r}")
            for x in a.extra:
                safe_rel(root, x, "--extra", must_exist=False)
            if os.path.lexists(control_marker_path(key_for(root))):
                raise Refused(
                    f"a control run on {root} was killed and its test group may still run. Restore with: "
                    f"python3 {sys.argv[0]} --root {root} --restore{restore_args(a, repo_given)}"
                )
            if os.path.lexists(marker):
                m = load_marker(marker)
                raise Refused(
                    f"a mutant ({m['mutant']}) is still planted in {m['file']} from an earlier run that was killed. "
                    f"Restore with: python3 {sys.argv[0]} --root {root} --restore{restore_args(a, repo_given)}   "
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
                check_single_link(
                    safe_rel(root, m["file"], f"mutant {m['id']} file"), f"mutant {m['id']} target"
                )
                check_single_link(
                    safe_rel(ref, m["file"], f"mutant {m['id']} reference file"),
                    f"mutant {m['id']} reference",
                )
            a.imports = (
                {m["file"]: "SKIPPED by --skip-import-check" for m in ms}
                if a.skip_import_check
                else import_check(root, a.pythonpath, [m["file"] for m in ms])
            )
            rawdir = pathlib.Path(a.raw)
            if rawdir.is_symlink():
                raise Refused(f"--raw {rawdir} is a symbolic link: refused")
            rawdir.mkdir(parents=True, exist_ok=True)
            outs = [rawdir / f"{a.prefix}-{n}.txt" for n in ("baseline", "tree-diff")]
            outs += [rawdir / f"{a.prefix}-{m['id']}.txt" for m in ms]
            outs += [pathlib.Path(a.out_json)] if a.out_json else []
            for o in outs:  # before anything is planted (review r4 nit 11)
                check_out_path(o)
            results = []
            a.ref_files = tree_files(ref)
            if a.control:
                control = control_marker_path(key_for(root))
                cinfo = {
                    "root": str(root),
                    "cmd_head": [str(root / ".venv/bin/python"), "-m", "pytest"],
                    "cmd_argv": pytest_cmd(root, tests),
                    "run_start_ticks": (proc_stat(os.getpid()) or {}).get("start"),
                }

                def note_control(pgid: int) -> None:
                    write_state(
                        control, json.dumps({**cinfo, "pgid": pgid, **proc_identity(pgid)}).encode()
                    )

                try:
                    write_state(control, json.dumps(cinfo).encode())
                    cmd, rc, out, sweep = run_tests(
                        root, tests, a.pythonpath, a.timeout, note_control
                    )
                finally:
                    # reached only after the group was stopped or ended (a SIGKILL skips it: the marker stays)
                    control.unlink(missing_ok=True)
                last, _ = summary(out)
                write_out(
                    rawdir / f"{a.prefix}-baseline.txt",
                    f"UNMUTATED BASELINE\nbase commit: {a.sha} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nenvironment: {', '.join(sorted(test_env(a.pythonpath)))} only\nimport check: {a.imports}\nrc: {rc}\ntest group after the leader ended: {sweep}\nsummary: {last}\n\n{out}",
                )
                print("baseline", rc, last)
            dirty: list[str] = []
            for m in ms:
                dirty = one(a, tests, m, results, ref)
                if dirty:  # this mutant's tests changed the tree: the next mutant would run on a changed tree
                    print(
                        f"STOPPED after mutant {m['id']}: its test run changed the scratch tree: {dirty[:5]}",
                        file=sys.stderr,
                    )
                    break
            if a.out_json:
                write_out(pathlib.Path(a.out_json), json.dumps(results, indent=1))
            # proof the scratch tree is unchanged: compare with a FRESH archive extract
            fresh = tmpref / "fresh"
            fresh.mkdir()
            build_reference(a.repo, a.sha, a.patch, fresh)
            bad = tree_check(a, root, fresh, marker) or dirty
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
