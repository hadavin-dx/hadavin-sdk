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
    in every window of a normal run: planting, tests awaited, restore (T47), and the exit after exit code 3, 4 or 5
    (a signal there is remembered and cannot change the result). `--restore` itself: from the first write on (the marker
    is read, the file is written back, the state files are removed) a signal is remembered and the restore ends first;
    BEFORE that (state folder, lock, real-repository check, and the `git archive` of `--sha`) nothing has been written,
    so a signal ends it at once with 128+N and every state file untouched (r9 minor 1; T96). A real memory fault inside this very process (SIGSEGV,
    SIGBUS, SIGFPE, SIGILL raised by the CPU, not sent by kill) is NOT recovered by that handler: the handler returns
    to the faulting instruction, the process spins at full speed and keeps the lock and the planted file until it is
    killed by hand (it does NOT act like SIGKILL; measured, T64). Then: `kill -9` it and run `--restore`.
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
    the checks is refused). The restore COMPARES, WRITES and VERIFIES on that one open file (review r5 M3): a folder
    swapped for a decoy that holds the original bytes cannot make the restore report success.
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
  * FORGED STATE (r8 d): the marker and the backup live in a folder only this user may write (mode 700). Someone who can
    write there as this user can write a marker plus a swapped backup with a matching hash, and a plain `--restore` then
    puts the swapped text into the file. That CANNOT be closed by this tool alone: such a person can also edit run.py, the
    tests and the tree, and a signature would need a key this user cannot read (a root-owned secret or another account).
    What closes it for the operator: `--restore --sha COMMIT [--repo R] [--patch F]` takes the original from `git archive`
    of that commit (named on the command line, not read from the state folder) and refuses, exit 3, when the backup differs
    or when the mode recorded in the marker has other execute bits than the file in git (r9 minor 8).
  * A mutant file replaced by a symbolic link at --restore is never written through; the failure text says the exact two
    commands to run (remove the link, then --restore again).
  * Output that cannot be written (/dev/full, closed pipe) is dropped, never an exit 1 or 120; the raw files hold the result.
  * PROCESS GROUP ONLY (review r7 N5): what a test starts is stopped only while it stays in the test's process group. A
    background process that leaves it (`setsid`, `setpgid`, a double fork into a new session) is NOT found and NOT
    stopped, by the sweep after the leader ends or by `--restore`; it can keep writing into the tree later. The tree
    comparison after each mutant and after the loop may catch such a write (exit 4), but only if it lands before that
    comparison. Closing this needs a kernel boundary (a cgroup or a PID namespace) that a normal user cannot set up;
    run the tests in one if that matters (T89).
  * Two runs on one root with DIFFERENT TMPDIR do not share a lock folder: a normal run looks in the usual other places
    (/tmp, /var/tmp, /dev/shm, TMP, TEMP) at the start and refuses when another run holds its lock there or left a
    planted file (r7 N6); two runs started within the same instant, before either has taken its lock, can still race
    (the refusal is tested in T91; the race is not). A run whose TMPDIR is outside those places is NOT seen by another
    run or by `--restore`; what is still true: `--restore` without a marker exits 2 (not 0), `--restore --sha` compares
    the files with git, and a normal run compares the tree with the git archive before it plants (r9 M1).
  * A marker that can never be used (the root folder renamed and replaced, a damaged marker, a marker for another root)
    is removed with `--restore --sha COMMIT --discard-marker`, only after the tree under --root equals the git archive
    and no test group of the marker still runs (r9 minor 3; T96). r10 M1: the marker must also be readable and carry the device and
    inode of the folder now at --root; a marker of a renamed-away or replaced folder, or an unreadable one, gives exit 3 and is
    removed only with the extra flag `--accept-unchecked-folder`, whose text says what was NOT checked (T97). `--sha` is 4 to 64
    hex digits; an empty value (an unset shell variable) is refused with exit 2, as is an empty value of any option that
    names a path or a name (r10 M2). `--helper-timeout S` (default 300) stops a `git` or
    `patch` call that does not end and refuses (r9 minor 2).
  * Not a target: a file under `.venv` (directly under the root) or in a cache folder (`__pycache__`, `.pytest_cache`) is
    refused as the file under test, an `--extra` or a marker file, because the tree comparison skips those folders (r9).
  * State files are made durable: the state folder is synced after every write and removal (r9).
Output files (review r6 nit 4): `--raw` and `--out-json` may not lie inside --root (they would dirty the tree), an
output file that already exists must be a regular file with one name, and the folder of `--out-json` must exist: all
checked before anything is planted. The folder --root is identified by device and inode when the run starts and
recorded in the marker: a folder that has been renamed away and replaced by another one with the same name is refused
(plant and restore, exit 3), so a decoy cannot receive a restore. When the file under test holds changed text and a test made it read-only (444), the owner's own
write permission is given back on the open file, the same inode is opened for writing, the original text and mode are
written back (r7 N7; as root a mode bit never blocks a write, so this path is only proven as a normal user, T88). A read-only
file that ALREADY holds the original text is left as it is, mode included (nothing is written, T88d); if it cannot be opened for
writing the added owner permission is taken away again (r10 m6). The recorded mode is restored exactly: mode 0 stays 0, and the mode is CHECKED after the write (r11). A plain `--restore` never
writes a setuid, setgid or sticky bit: a marker mode with such a bit is cut to its lowest 9 bits and the text says so (r11 MAJ-1;
a forged marker cannot make a setuid file); with --sha a marker mode with such a bit, or with a write bit for the group or for others,
is refused (r10 m2, r11 m6).
`--out-json` may not be run.py itself, the `--list` file, a `--patch` file or the same path as a raw file (r7 N4), may not lie in any
state folder that is searched (ours, /tmp, /var/tmp, /dev/shm, TMP, TEMP), and an existing file is overwritten only when it is a
result file of this tool (a JSON list of objects with id and verdict; r10 m3). Helper programs (git, patch, the import probe) run
in their own process group and the whole group is killed on a timeout (r10 m8); text taken from a state file is quoted and control
characters are shown as \\xNN (r10 m9).
Limit (d), exact: a plain `--restore` (no --sha) believes the marker and the backup in the state folder; a person or program
that can write that folder AS THIS USER can write a forged marker plus a backup whose hash matches, and plain --restore would write that
text into the file (a mode with a setuid, setgid or sticky bit is cut to its lowest 9 bits, never more: r11 MAJ-1, T99b). Only `--restore --sha
COMMIT` closes it: the original then comes from git, a forged marker is refused or ignored, never trusted (T98d, T98e). Use --sha
whenever the state folder may not be trusted. A path of 4096 bytes or more (the kernel counts the closing NUL: 4095 is the longest), the root plus a relative path together, or a name over 255
bytes, is refused with exit 2; the length limits apply to path-shaped arguments only (a long -k expression is fine, T98a, T99c). The
signal handlers are installed right after the imports; a signal before that (Python's own start-up, about 20 to 50 ms) ends the
process by that signal at a time when nothing has been written (T98b).
NOT A SANDBOX (read this): the tests run as this user with this user's full file rights. The tool checks the
scratch tree and the files it plants into; it cannot stop a test from writing elsewhere. The modes (chmod) of the
other files in the tree are not compared; the tree is compared by content. Paths inside --root
are trusted as a whole: `.venv` (directly under the root) and the cache folders are NOT compared, so a mutant
planted into, or a test that changes, files in them is not detected; other test files in --root run too.
Exit codes (round 8, reviews r6 M1/M2 and r7 M1):
  0    EVERY mutant ran and got a clean verdict (KILLED or SURVIVED, no flag), a baseline of the unmutated tree
       ran and passed, and the tree is clean. With --restore: the file is KNOWN to hold the original (a marker was found
       and its file written back or already original, and every test group settled), or `--restore --sha` found the
       whole tree equal to the git archive; also `--discard-marker` after that same comparison, when the marker is readable and
       belongs to the folder now at --root (or --accept-unchecked-folder says the other folder does not matter)
  2    refused: this run wrote nothing and planted nothing. 2 NEVER says "nothing is planted": the planted-ness of an
       earlier run is either shown by its marker (then 3, or 0 after a good restore) or it is unknown. 2 is the answer to a
       refusal when NO planted or control marker for this root exists (a bad argument or an empty value such as `--sha ""`,
       an argparse error, a refused real-repository check, a state folder that is not mode 700, a lock held by a live run, a
       --sha that names no commit, a git or patch call that did not finish (--helper-timeout), a temporary folder that
       cannot be found) and, with a marker, only when the marker names another root or another backup path (it is not this
       run's marker; nothing is written). In a normal run also: the baseline of the unmutated tree is not usable, or the
       marker of an EARLIER killed run (this run planted nothing). With --restore: NO marker for this root exists anywhere
       searched and no --sha was given to check the files (the files are unknown). With --restore --sha and no marker: the
       files are compared with git, equal is 0, different is 3; a marker for another root with --sha: the files are compared
       with git too, equal stays 2, different is 3
  3    restore failed (marker and backup kept; run --restore): the class is "an exit code that says nothing is planted
       while the mutant is planted", fixed in ONE place (may_be_planted in main): with --restore, EVERY failure once a
       planted or control marker for this root exists exits 3: invalid or damaged marker, missing, linked, FIFO or
       damaged backup (hash differs: nothing is written), unusable state folder, refused real-repository check, a lock
       held by a live run, an unwritable file, a link or swapped folder on the way, two names, a root folder that is no
       longer the one the mutant was planted in, an internal bug; in a normal run, any exit while this run's own marker
       still exists. Also: --restore could not settle a control run, a control marker that cannot be read, or an
       orphaned test group that could not be stopped (the file is still written back; marker and backup are kept); `--restore --sha` with no marker
       when the tree differs from git; `--discard-marker` when the tree differs, a test group still runs, or the marker does not
       prove it belongs to the folder now at --root or cannot be read (unless --accept-unchecked-folder is given; r10 M1)
  4    tree not clean (before the first mutant, after a mutant, or after the loop) or marker left behind
  5    INCOMPLETE: at least one mutant has no clean verdict (COULD-NOT-PLANT, TIMEOUT, ERROR, NO-TEST-PASSED,
       or a KILLED whose failing tests equal the baseline's), or the loop ended before every mutant ran, or
       `--no-control` was given (no baseline ran, so no result can be called complete)
  128+N interrupted by signal N
A line `SUMMARY: ...` (also in raw/<prefix>-summary.txt) counts every verdict; exit 0 means that line shows no
COULD-NOT-PLANT, TIMEOUT, ERROR, NO-TEST-PASSED, flagged or not-run mutant and says COMPLETE. Exit 4 wins over exit 5.
An unexpected failure inside this tool (a bug, not a planned refusal) prints INTERNAL ERROR with the traceback and
exits 2 when nothing is planted (a planted mutant is always restored first, exit 3 if that fails); it never ends with
Python's own exit 1.
Verdict per mutant from the pytest exit code: 0 SURVIVED (NO-TEST-PASSED when no test passed: all skipped), 1 KILLED,
None TIMEOUT, anything else ERROR. The mutant ids `baseline`, `tree-diff` and `summary` are reserved (they name
other raw files).
Baseline (review r5 M1, r6 M2): the unmutated tree is run first (`--control` is the DEFAULT); the mutants are REFUSED
(exit 2) unless that run exits 0 and at least one test passed. A KILLED mutant whose failing tests equal the baseline's
failing tests is flagged (exit 5). `--no-control` skips the baseline (the last of --control and --no-control wins):
an already failing tree would then make every mutant KILLED, so every raw file says `baseline: NOT RUN`, the SUMMARY
line says `NO BASELINE ... INCOMPLETE` (never COMPLETE) and the exit code is 5 even when every verdict is clean.

Usage:
  run.py --root /tmp/c8/wC --sha b4cce5b --prefix C-01 --raw DIR --list mutants.json -- TESTS...
  run.py --root ... --sha ... --prefix C-01 --raw DIR --id m01 --file src/x.py --old "a" --new "b" -- TESTS...
  run.py --root R --restore [--sha COMMIT [--repo R] [--patch F] [--extra F]] [--discard-marker [--accept-unchecked-folder]]
mutants.json: [{"id": "m01", "file": "...", "old": "...", "new": "...", "desc": "..."}, ...]
The unmutated tree is run once first (default; `--no-control` turns it off) and recorded as <prefix>-baseline.txt.
TESTS are pytest arguments (paths / -k ...). The command run is, with only the environment named above:
  <root>/.venv/bin/python -m pytest -q -p no:cacheprovider --rootdir=<root> --confcutdir=<root> --tb=line -rfp TESTS
"""

from __future__ import annotations

import os
import signal
import sys

if __name__ == "__main__":
    # r11 (independent r10 run: signals 0 to 0.2 s after the start ended 15 of 30 runs by the default action or by a
    # KeyboardInterrupt traceback): the handlers are installed BEFORE the other standard modules are loaded (those took 20 to
    # 50 ms under load). Until main() installs the real handlers nothing has been written, no marker exists and no file is
    # planted, so a signal simply ends the run with 128+N. What stays: Python's own start-up (before the first line of this
    # file, about 10 to 20 ms) cannot be handled in Python (impossible-now); nothing exists then that could be left behind.
    for _sn in signal.valid_signals():
        if _sn in (
            signal.SIGKILL,
            signal.SIGSTOP,
            signal.SIGCHLD,
            signal.SIGCONT,
            signal.SIGWINCH,
            signal.SIGURG,
            signal.SIGTSTP,
            signal.SIGTTIN,
            signal.SIGTTOU,
            signal.SIGPIPE,
            signal.SIGXFSZ,
        ):
            continue
        try:
            signal.signal(_sn, lambda signum, frame: os._exit(128 + signum))
        except (OSError, ValueError):
            pass

import argparse
import configparser
import errno
import fcntl
import hashlib
import io
import json
import pathlib
import re
import shlex
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import traceback

# skipped in the tree comparison: `.venv` ONLY directly under the root (the scratch environment); the two
# cache folders at any depth. A `.venv` deeper in the tree is compared like any other folder.
SKIP_TOP = {".venv"}
SKIP_ANY = {"__pycache__", ".pytest_cache"}
# outside every repository, one folder per user (a shared temp folder must not be shared) (review 4 M4)
# r10 m10: a failure while the module is loaded (no usable temporary folder, no sysconf) must end as a refusal (exit 2) in
# main(), never as Python's own exit 1 with a traceback before main() runs
_INIT_ERRORS: list[str] = []
try:
    STATE = pathlib.Path(tempfile.gettempdir()) / f"hadavin-mutation-lane-{os.geteuid()}"
except (
    OSError,
    RuntimeError,
    ValueError,
) as _e:  # any failure of tempfile or os here is the same class
    STATE = pathlib.Path(os.sep, "nonexistent", f"hadavin-mutation-lane-{os.geteuid()}")
    _INIT_ERRORS.append(f"no usable temporary folder ({type(_e).__name__}: {_e})")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
SHA_RE = re.compile(r"[0-9a-fA-F]{4,64}")
# Every signal that can be sent to a process, except the ones named here (review r4 M1). Not handled, with the reason:
# SIGKILL and SIGSTOP cannot be caught; SIGCHLD (a child changed state), SIGCONT, SIGWINCH and SIGURG are
# informational and do not end the process; SIGTSTP, SIGTTIN and SIGTTOU only stop it; SIGPIPE and SIGXFSZ are
# turned into ordinary errors by Python. All the rest (including SIGTRAP, SIGSYS, SIGSTKFLT, all real-time
# signals and SIGSEGV/SIGBUS/SIGFPE/SIGILL when another process sends them with kill()) end the process by
# default, so each one is caught: the file is restored first. A real memory fault inside this very process
# cannot be handled in Python (the faulting instruction would run again and again): the process then spins and
# keeps the lock and the planted file until it is killed by hand with `kill -9`; only after that does
# `--restore` work (the lock is free, the marker stays).
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
EXIT_REFUSED, EXIT_RESTORE_FAILED, EXIT_TREE_NOT_CLEAN, EXIT_INCOMPLETE = 2, 3, 4, 5
MIN_PYTHON = (3, 11, 4)  # tomllib (3.11) and tarfile's `filter="data"` (3.11.4)
# raw files named after a fixed word: a mutant may not take one of these as its id (review r5 nit 7)
RESERVED_IDS = frozenset({"baseline", "tree-diff", "summary"})
FULL_SHA_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# (path, device, inode) of --root as found when the run started; None in unit tests that call the writers directly.
# Every open of the root folder checks it (review r6 nit 8: a root renamed away and replaced by a decoy folder).
ROOT_IDENT: tuple[str, int, int] | None = None
try:
    CLK_TCK = os.sysconf("SC_CLK_TCK")
except (ValueError, OSError) as _e:
    CLK_TCK = 100
    _INIT_ERRORS.append(f"the clock tick rate cannot be read ({type(_e).__name__}: {_e})")


class Refused(Exception):
    pass


# what a restore may fail with: a refusal, the operating system, or a bug of these kinds; anything else still ends in main(),
# which maps it to exit 3 while this run's own marker exists
RESTORE_ERRORS = (
    Refused,
    OSError,
    RuntimeError,
    ValueError,
    TypeError,
    LookupError,
    AttributeError,
    AssertionError,
)


def shown(x, limit: int = 200) -> str:
    """r10 m9: text that came from a state file (marker fields, link targets) is quoted and escaped before it is printed: a
    newline, a carriage return or a terminal escape inside a marker can neither add a fake line nor overwrite a real one."""
    return json.dumps(str(x)[:limit] + ("..." if len(str(x)) > limit else ""), ensure_ascii=True)


_CTRL = re.compile("[\x00-\x08\x0b-\x1f\x7f]")


CHILD_ENV_ALLOWED = frozenset({"PATH", "HOME", "LC_ALL", "PYTHONDONTWRITEBYTECODE", "PYTHONPATH"})


def check_child_call(args, kwargs: dict) -> None:
    """r11 (review r10 S603): the checks every program start must pass, in ONE place (a test calls this directly and through
    Child). Raises Refused. The argument list is a list of str (never one shell string), the program is an absolute path, no
    text holds a NUL, no shell, no `executable=` or `preexec_fn=` override, and an environment holds only names from
    CHILD_ENV_ALLOWED (no LD_PRELOAD, no BASH_ENV, no GIT_* ...)."""
    if type(args) is not list or not args or not all(type(a) is str for a in args):
        raise Refused(
            "program start refused: the arguments must be a non-empty list of text (never one shell string)"
        )
    if not os.path.isabs(args[0]):
        raise Refused(
            f"program start refused: the program must be an absolute path, got {shown(args[0])}"
        )
    if any("\0" in a for a in args):
        raise Refused("program start refused: an argument holds a NUL character")
    if kwargs.get("shell"):
        raise Refused("program start refused: a shell is never used")
    for bad in ("executable", "preexec_fn", "pass_fds", "creationflags"):
        if kwargs.get(bad):
            raise Refused(f"program start refused: {bad}= is not allowed")
    env = kwargs.get("env")
    if env is not None:
        if not isinstance(env, dict) or not all(
            type(k) is str and type(v) is str for k, v in env.items()
        ):
            raise Refused("program start refused: the environment must be a dict of text")
        extra = sorted(set(env) - CHILD_ENV_ALLOWED)
        if extra or any("\0" in v for v in env.values()):
            raise Refused(f"program start refused: environment variable(s) not allowed: {extra}")


class Child(subprocess.Popen):
    """The ONE way this tool starts another program (r11: a real guard, not only a name). Every start runs
    `check_child_call` first: a list of text, an absolute program path, no NUL, no shell, an environment from the fixed
    allowed names. The arguments are built by this tool (run_cmd and run_tests), never taken as one string from the caller;
    the check is there so that a later change cannot weaken that without a test failing (T99a)."""

    def __init__(self, args, *a, **kw):
        check_child_call(args, kw)
        super().__init__(args, *a, **kw)


class SafeOut:
    """r8: standard output and error that never fail. A closed pipe, /dev/full or a full disk made print() raise (and the
    flush at exit made Python exit with 1 or 120, which are no exit codes of this tool; found by the independent r7 run).
    Text that cannot be written is dropped (`lost` is set); the result is always in the raw files and the exit code."""

    encoding = "utf-8"

    def __init__(self, fd: int):
        self.fd, self.lost = fd, False

    def write(self, text: str) -> int:
        # r10 m9: every control character except newline and tab is shown as \xNN (a terminal escape cannot act)
        text = _CTRL.sub(lambda m: f"\\x{ord(m.group()):02x}", text)
        data = text.encode("utf-8", "replace")
        try:
            while data:
                data = data[os.write(self.fd, data) :]
        except OSError:
            self.lost = True
        return len(text)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        return self.fd


class NoMarker(Refused):
    """--restore found no marker anywhere and no --sha was given: the planted-ness of the files is unknown (exit 2)."""


class Forged(Refused):
    """A marker that names another root or another backup path: it does not belong to this run, so nothing is written
    and `--restore` exits 2. Every OTHER refusal after a marker for this root exists is a failed restore (exit 3)."""


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
    exiting = False  # the result is decided and the process is leaving: a signal can no longer change it (r6 nit 2)
    own_marker = False  # this run wrote its planted marker and has not yet verified the restore (r7 review M1)


SIG = SigState()


def _term(signum, frame):
    if SIG.first is None:
        SIG.first = signum
    if not SIG.exiting and not SIG.fired and (SIG.allow or not SIG.critical):
        SIG.fired = True
        SIG.allow = False
        raise KeyboardInterrupt(SIG.first)  # unwinds through the `finally` that restores the file


def leave(code: int) -> None:
    """Leave with `code`; from here a signal is only remembered, so it cannot turn exit 3, 4 or 5 into a signal exit
    while the `finally` blocks run (review r6 nit 2). Class: a late signal changing an already decided result."""
    SIG.exiting = True
    sys.exit(code)


def deliver_pending() -> None:
    """Raise the remembered first signal, once, at a point where nothing is planted or the tests are awaited."""
    if SIG.first is not None and not SIG.fired and not SIG.exiting:
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


def fsync_state_dir() -> None:
    """r9 minor 5: a rename or an unlink in the state folder is only durable after the FOLDER is synced. Without it a power
    loss could bring back a removed marker (a stale marker) or lose a new one (a planted file with no marker)."""
    dfd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def unlink_state(path: pathlib.Path) -> None:
    """The one way a state file (marker, backup, control marker) is removed: unlink, then sync the folder."""
    path.unlink(missing_ok=True)
    try:
        fsync_state_dir()
    except OSError as e:
        # r10 m11: the file IS gone; only the proof that the removal survives a power loss failed. That must not turn a finished
        # restore into an error (and strand the backup): a marker that came back later is stale and `--restore` settles it.
        print(
            f"WARNING: the state folder could not be synced after removing {path.name} ({e.strerror}): the removal is not "
            f"proven durable; after a power loss a stale marker may return (harmless: --restore settles it)",
            file=sys.stderr,
        )


def write_state(path: pathlib.Path, data: bytes) -> None:
    """Atomic: a new private file (O_EXCL, mode 600) in the state folder, then rename over the target, then the folder is synced."""
    fd, tmp = tempfile.mkstemp(dir=STATE, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # replaces a link itself, never follows it
        fsync_state_dir()
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


def loads_json(data: bytes | str):
    """json.loads where every way to say "this is not usable JSON" is one error type (r8: a text nested 200000 deep raised
    RecursionError, which is no ValueError, and ended as an INTERNAL ERROR with a traceback)."""
    try:
        return json.loads(data)
    except RecursionError as e:
        raise ValueError("nested too deeply") from e


def load_marker(path: pathlib.Path) -> dict:
    try:
        m = loads_json(read_state(path))
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
        if root is not None and ROOT_IDENT is not None and str(root) == ROOT_IDENT[0]:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) != ROOT_IDENT[1:]:
                raise Refused(
                    f"the folder now at {root} is not the folder this run started in (it was renamed or replaced): "
                    f"nothing is written there"
                )
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
            fd = os.open(name, flags | os.O_CREAT | os.O_EXCL, mode & 0o777, dir_fd=pfd)
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
        if (
            created and mode & 0o7000
        ):  # a write by a user without CAP_FSETID clears setuid/setgid: set the recorded bits again
            fh.flush()
            os.fchmod(fh.fileno(), mode)


def _make_writable(fd: int, name: str, pfd: int, base: int, saved: bytes) -> tuple[int, bool]:
    """r7 review N7: a test of the mutant may have run chmod on the file under test (mode 444, or 000); then the planted
    text could never be written back. The owner may always change the mode of an own file: on the OPEN file (a regular
    file, our own, exactly one name) give the owner read and write permission, then open the SAME inode for writing from
    the same folder descriptor. The recorded mode is set back by the caller. Anything else stays as it is (compared only)."""
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid() or st.st_nlink != 1:
        return fd, False
    try:
        with os.fdopen(os.dup(fd), "rb") as probe:
            same = probe.read() == saved  # the duplicate shares the file offset: rewind below
        os.lseek(fd, 0, os.SEEK_SET)
        if same:  # nothing to write: a read-only file that holds the original is left alone
            return fd, False
    except OSError:  # an O_PATH descriptor (mode 000) cannot be read: assume it differs
        pass
    os.chmod(
        f"/proc/self/fd/{fd}", stat.S_IMODE(st.st_mode) | 0o600
    )  # works on O_PATH descriptors, follows the inode

    def put_back() -> (
        None
    ):  # r10 m6: the owner permission we added is taken away again when the file is not written
        try:
            os.chmod(f"/proc/self/fd/{fd}", stat.S_IMODE(st.st_mode))
        except OSError:
            pass

    try:
        fd2 = os.open(name, base | os.O_RDWR, dir_fd=pfd)
    except OSError:
        put_back()
        return fd, False
    st2 = os.fstat(fd2)
    if (st2.st_dev, st2.st_ino) != (
        st.st_dev,
        st.st_ino,
    ):  # swapped meanwhile: not the file we changed
        os.close(fd2)
        put_back()
        return fd, False
    os.close(fd)
    return fd2, True


def restore_target(
    path: pathlib.Path,
    saved: bytes,
    root: pathlib.Path,
    create: bool = False,
    mode: int | None = None,
) -> tuple[bool, bytes]:
    """Put `saved` into the file under test: COMPARE, WRITE and VERIFY on ONE open file (review r5 M3). The folders are
    opened one at a time with O_NOFOLLOW from `root` (as in write_target), the file is opened ONCE from its parent's
    descriptor, and everything below is done through that descriptor: a folder swapped for a decoy after the path checks
    can neither make a decoy that holds the original bytes look like the restored file (r5: compared by path, then
    skipped the write and cleared the marker) nor receive the write. Returns (already_original, bytes read back from
    the same open file). The write is skipped when the open file already holds `saved` (a read-only file that was never
    changed is not an error); a file with more than one name, or that is not a regular file, is never written.
    `create=True` (restore only) re-creates a deleted file and missing folders with O_EXCL and exactly `mode`. With a
    `mode` given, the mode of the open file is set back to it when a test changed it (review r6 nit 8)."""
    pfd, name = _open_parent(root, path, create)
    try:
        base = os.O_NOFOLLOW | os.O_NONBLOCK  # NONBLOCK: a FIFO must not hang the open
        created = writable = False
        try:
            fd = os.open(name, base | os.O_RDWR, dir_fd=pfd)
            writable = True
        except FileNotFoundError:
            if not create:
                raise
            fd = os.open(
                name,
                base | os.O_RDWR | os.O_CREAT | os.O_EXCL,
                (0o644 if mode is None else mode) & 0o777,
                dir_fd=pfd,
            )
            created = writable = True
        except (
            PermissionError
        ):  # a read-only file: it can still be compared (mode 000: not even that, O_PATH only)
            try:
                fd = os.open(name, base | os.O_RDONLY, dir_fd=pfd)
            except PermissionError:
                fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=pfd)
            if mode is not None:
                fd, writable = _make_writable(fd, name, pfd, base, saved)
        except OSError as e:
            if e.errno == errno.ELOOP:
                raise Refused(f"{path} is a symbolic link: not written") from e
            raise
    finally:
        os.close(pfd)
    st = os.fstat(fd)
    # checked BEFORE a buffered file object is built (a FIFO is not seekable)
    if not stat.S_ISREG(st.st_mode):
        os.close(fd)
        raise Refused(f"{path} is not a regular file: not written")
    with os.fdopen(fd, "r+b" if writable else "rb") as fh:
        already = fh.read() == saved
        need_mode = (
            not created
            and mode is not None
            and writable
            and st.st_nlink == 1
            and stat.S_IMODE(st.st_mode) != mode
        )
        if writable and not created and st.st_nlink != 1 and not already:
            # r9 minor 6: checked BEFORE anything is written. The mode of a file with two names is NEVER changed (the other
            # name may be a file outside the scratch tree: r8 changed its mode); a two-name file that already holds the
            # original text is left as it is (content is what is verified), with its mode as the tests left it.
            raise Refused(
                f"{path} is not a regular file with exactly one name (links: {st.st_nlink}): not written, mode not changed"
            )
        if created:
            os.fchmod(
                fh.fileno(), 0o644 if mode is None else mode
            )  # the umask of the caller must not change the recorded mode (r10 m2: a recorded mode 0 stays 0)
        elif need_mode:
            os.fchmod(fh.fileno(), mode)  # a test changed the mode of the file under test
        if not already:
            if not writable:
                raise PermissionError(
                    errno.EACCES, "the file is read-only and differs from the original"
                )
            if st.st_nlink != 1:
                raise Refused(
                    f"{path} is not a regular file with exactly one name (links: {st.st_nlink}): not written"
                )
            fh.seek(0)
            fh.truncate(0)
            fh.write(saved)
            fh.flush()
            os.fsync(fh.fileno())
            want = 0o644 if mode is None else mode
            if (created or need_mode) and want & 0o7000:
                # r10: a write by a user without CAP_FSETID (not root) clears the setuid and setgid bits, so the recorded
                # mode is set once more AFTER the write (T97e as user nobody: 4755 came back as 755)
                os.fchmod(fh.fileno(), want)
        if writable and (created or need_mode):
            # r11 MAJ-1: the mode is CHECKED after the write, never assumed (a bit the kernel dropped is a failure, not a pass)
            got = stat.S_IMODE(os.fstat(fh.fileno()).st_mode)
            want_mode = 0o644 if mode is None else mode
            if got != want_mode:
                raise Refused(
                    f"{path}: the mode after the write is {oct(got)}, not the recorded {oct(want_mode)} "
                    f"(the system did not keep it): marker and backup kept"
                )
        fh.seek(0)
        return already, fh.read()


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
        st = os.fstat(fh.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise Refused(
                f"output file {path} is not a regular file with exactly one name (links: {st.st_nlink}): refused"
            )
        fh.truncate(0)
        fh.write(text)


def check_out_path(path: pathlib.Path, root: pathlib.Path | None = None) -> None:
    """Before anything is planted (review r4 nit 11, r6 nit 4): an output path must not be a symbolic link or a special
    file, must have an existing folder, must not have two names (writing it would change the other name too) and, with
    `root`, must not lie inside the scratch tree (it would be overwritten by or dirty the tree)."""
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Refused(f"output path {path} is a symbolic link or not a regular file: refused")
    if not path.parent.is_dir():
        raise Refused(
            f"the folder of output path {path} does not exist: refused (nothing is created for you)"
        )
    if path.exists() and os.lstat(path).st_nlink != 1:
        raise Refused(f"output path {path} has more than one name (hard link): refused")
    if root is not None and (path.parent.resolve() / path.name).is_relative_to(root.resolve()):
        raise Refused(
            f"output path {path} lies inside --root {root}: refused (it would change the scratch tree)"
        )


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


def helper_env() -> dict:
    """The environment of git and patch: only PATH, HOME (for the user's own git settings) and LC_ALL=C. Nothing else of
    the caller's environment (GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_CONFIG_*, PATCH settings ...) reaches them, so a
    variable in the caller's shell cannot point `git archive` or `git rev-parse` at another repository (review r5)."""
    return {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "LC_ALL": "C"}


HELPER_TIMEOUT = (
    300  # seconds for one git or patch call (r9 minor 2); `--helper-timeout` changes it
)


def run_cmd(
    argv: list[str],
    input_bytes: bytes | None = None,
    cwd: pathlib.Path | None = None,
    env: dict | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    """The one place that starts a helper program (git, patch, the import probe): fixed argument list, no shell.
    With no `env` the helper environment above is used (never the caller's whole environment). A call with no `timeout`
    gets HELPER_TIMEOUT (r9: a stalled `git archive` used to hang the run and the `--restore --sha`); the child is killed
    and the call is a refusal. A caller that passes its own `timeout` handles `TimeoutExpired` itself."""
    limit = HELPER_TIMEOUT if timeout is None else timeout
    # r10 m8: the helper gets its OWN process group; on a timeout (or a signal that unwinds the run) the WHOLE group is killed,
    # not only the leader (a wrapper script's children and the import probe's children used to stay alive)
    proc = Child(
        argv,
        stdin=subprocess.PIPE
        if input_bytes is not None
        else subprocess.DEVNULL,  # no helper may read the caller's input
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=helper_env() if env is None else env,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(input_bytes, timeout=limit)
    except BaseException as e:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        proc.kill()
        try:
            proc.communicate(timeout=5)
        except (
            subprocess.TimeoutExpired,
            OSError,
            ValueError,
        ):  # a process that left the group may still hold the pipes: give up on them
            for fh in (proc.stdout, proc.stderr, proc.stdin):
                try:
                    fh and fh.close()
                except OSError:
                    pass
            proc.wait()
        if isinstance(e, subprocess.TimeoutExpired) and timeout is None:
            raise Refused(
                f"{pathlib.Path(argv[0]).name} did not finish within {HELPER_TIMEOUT} s and was stopped (--helper-timeout)"
            ) from e
        raise
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def text_of(cp: subprocess.CompletedProcess) -> str:
    return (cp.stdout + cp.stderr).decode(errors="replace").strip()


def safe_rel(base: pathlib.Path, rel, what: str, must_exist: bool = True) -> pathlib.Path:
    """A relative path inside `base`: no absolute path, no `..`, no symbolic link on the way."""
    if not isinstance(rel, str) or not rel or "\0" in rel or "\\" in rel:
        raise Refused(f"{what}: not a usable relative path: {rel!r}"[:300])
    if too_long(rel):
        raise Refused(f"{what}: not a usable relative path: {too_long(rel)}")
    if too_long(
        os.fspath(base) + "/" + rel
    ):  # r11 m2: the whole path (root + relative part) is what the kernel sees
        raise Refused(
            f"{what}: root plus relative path is too long: {too_long(os.fspath(base) + '/' + rel)}"
        )
    pp = pathlib.PurePosixPath(rel)
    if pp.is_absolute() or ".." in pp.parts:
        raise Refused(f"{what}: must be relative to the root and contain no '..': {rel!r}")
    # r9 minor 7: the tree comparison skips `.venv` directly under the root and the cache folders at any depth, so a file
    # there would be planted, changed or restored without any later check seeing it: never a target
    if pp.parts and (pp.parts[0] in SKIP_TOP or SKIP_ANY & set(pp.parts)):
        raise Refused(
            f"{what}: {rel!r} lies in a folder the tree comparison does not look at ({', '.join(sorted(SKIP_TOP | SKIP_ANY))}): refused"
        )
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


def resolve_commit(repo: str, sha: str) -> str:
    """The full id of the COMMIT `sha` names (review r5 nit 9): a short id can become ambiguous later and an id of a tree
    or a file is no commit. `git rev-parse --verify <sha>^{commit}`; anything else is refused. The full id is what the
    raw files record."""
    if not SHA_RE.fullmatch(sha):
        raise Refused(f"--sha is not a commit id: {sha!r}")
    top = repo_toplevel(repo)
    cp = run_cmd(
        [tool("git"), "-C", str(top), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"]
    )
    full = cp.stdout.decode(errors="replace").strip()
    # review r6 nit 7: a short hex that is also the name of a branch or tag resolves to the REF; the id must start with
    # exactly the hex that was typed, or the commit is not the one the user named
    if cp.returncode != 0 or not FULL_SHA_RE.fullmatch(full) or not full.startswith(sha.lower()):
        raise Refused(
            f"--sha {sha!r} does not name exactly one commit in {top} (unknown, ambiguous, not a commit, or the name of a branch or tag): "
            f"{text_of(cp)[:200]}"
        )
    return full


def build_reference(repo: str, sha: str, patches: list[str], dest: pathlib.Path) -> None:
    """Fresh `git archive <sha>` extract (+ patches) into dest: the one source of truth for original bytes."""
    if not SHA_RE.fullmatch(sha):
        raise Refused(f"--sha is not a commit id: {sha!r}")
    top = repo_toplevel(repo)  # archive from the top: a subfolder would archive only itself
    arc = run_cmd([tool("git"), "-C", str(top), "archive", sha])
    if arc.returncode != 0:
        raise Refused(f"git archive {sha} failed in {repo}: {text_of(arc)[:200]}")
    try:
        with tarfile.open(fileobj=io.BytesIO(arc.stdout), mode="r:") as tf:
            tf.extractall(dest, filter="data")
    except (
        tarfile.TarError,
        OSError,
    ) as e:  # FilterError is a TarError: a member the data filter refuses
        raise Refused(
            f"the archive of {sha} cannot be extracted safely ({type(e).__name__}: {e}): refused"
        ) from e
    for pf in patches:
        # --batch: never ask a question (stdin is /dev/null as well); --forward: a patch that looks reversed or already
        # applied is skipped and fails, never applied reversed; --no-backup-if-mismatch: no `.orig` file in the reference
        r = run_cmd(
            [
                tool("patch"),
                "-p1",
                "-s",
                "--batch",
                "--forward",
                "--no-backup-if-mismatch",
                "-d",
                str(dest),
                "-i",
                str(pathlib.Path(pf).resolve()),
            ]
        )
        if r.returncode != 0:
            raise Refused(f"patch {pf} does not apply to {sha}: {text_of(r)[:300]}")


def script_repo_root() -> pathlib.Path | None:
    """The repository that holds this script, found by walking up to a `.git` entry (no git call)."""
    here = pathlib.Path(__file__).resolve().parent
    return next((p for p in (here, *here.parents) if os.path.lexists(p / ".git")), None)


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
        if os.path.lexists(p / ".git"):
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


def stop_orphan(m: dict, root: pathlib.Path) -> tuple[str, bool]:
    """After a SIGKILL of run.py the test group may still run: stop it, but only if it is ours (start time and
    full argument list recorded in the marker must match; review r3 minors). A failure to stop it is reported,
    never allowed to abort the restore of the file. Returns (what was done, settled): `settled` is True only when
    nothing of this run's test group is left (stopped, already gone, or its number now belongs to another process
    while the group has no member), False when it may still run (cannot be verified, not provably ours, could not
    be stopped); a control marker is removed only when settled (review r5 nit 4)."""
    pgid = m.get("pgid")
    if not isinstance(pgid, int) and not m.get("cmd_head") and not m.get("cmd_argv"):
        return "no test group recorded", False
    if isinstance(pgid, int) and pgid <= 1:
        return "no test group recorded", False
    groups = orphan_candidates(m, root)
    if not groups:
        has_identity = (
            isinstance(pgid, int)
            and isinstance(m.get("start_ticks"), int)
            and isinstance(m.get("argv"), list)
        )
        want = m.get("cmd_argv") if isinstance(m.get("cmd_argv"), list) else m.get("cmd_head")
        has_command = (
            isinstance(want, list) and bool(want) and isinstance(m.get("run_start_ticks"), int)
        )
        leader = proc_stat(pgid) if isinstance(pgid, int) else None
        gone = leader is None or leader["state"] == "Z"
        if isinstance(pgid, int) and gone and not group_members(pgid):
            return "test group already gone", True
        what = f"process {pgid}" if isinstance(pgid, int) else "no process"
        text = f"{what} is not this run's pytest (or cannot be verified): left alone"
        if (
            has_identity and not gone
        ):  # another process now has that number: a group number is never reused while it has members
            return text, True
        if (
            not isinstance(pgid, int) and has_command
        ):  # searched by the recorded command: nothing matches
            return text, True
        return text, False
    notes = []
    settled = True
    for g in groups:
        try:
            stop_group(g)
        except OSError as e:
            notes.append(f"could NOT stop test group {g} ({e.strerror or e}): file restored anyway")
            settled = False
            continue
        for _ in range(50):
            if not group_members(g):
                break
            time.sleep(0.1)
        notes.append(f"stopped orphaned test group {g}")
        settled = settled and not group_members(g)
    return "; ".join(notes), settled


def other_state_check(root: pathlib.Path, key: str) -> tuple[bool, str, bool]:
    """No marker in our state folder. A run that used another TMPDIR keeps its marker THERE: look in the usual
    places. A marker found there whose backup differs from the file now on disk means the file is still
    planted: not ok (exit 3). A stale marker (file already equals the backup) is reported (ok).
    Anything that cannot be read safely fails closed (review r2 nit).
    Returns (ok, text, found). `found` is False when NO marker was seen anywhere: planted-ness is then UNKNOWN (r8 M1:
    a run with a TMPDIR outside the places searched keeps its marker where nobody looks), and the caller must not turn
    that into "nothing is planted"."""
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
                True,
            )
        if differs:
            return (
                False,
                (
                    f"STILL PLANTED: {shown(m['file'])} differs from the backup kept by a run that used another TMPDIR; "
                    f"restore with: TMPDIR={shlex.quote(str(parent))} python3 {shlex.quote(sys.argv[0])} --root {shlex.quote(str(root))} --restore"
                ),
                True,
            )
        notes.append(
            f"stale marker in {folder}: {shown(m['file'])} already equals its backup (remove it by hand)"
        )
    if notes:
        return True, "; ".join(notes), True
    return (
        True,
        (
            f"no marker in {STATE} or in {sorted(map(str, spots - {here}))}: nothing is recorded as planted, but WITHOUT a "
            f"marker this CANNOT TELL whether a file is still planted (a lost marker, or a run that used another state "
            f"folder, for example another TMPDIR)"
        ),
        False,
    )


def control_marker_path(key: str) -> pathlib.Path:
    return STATE / f"{key}.control.json"


def restore_control(root: pathlib.Path, key: str) -> tuple[bool, str]:
    """A control run (nothing planted) that was killed with SIGKILL leaves its test group running: the control
    marker names it. Stop it only if it is provably ours (same checks as for a planted run). The marker is removed
    only when nothing of the group is left; otherwise it is KEPT and the answer is not ok (review r4 nit 5, r5 nit 4).
    A control marker that is not valid JSON is a refusal, not a traceback."""
    path = control_marker_path(key)
    try:
        m = loads_json(read_state(path))
    except ValueError as e:
        raise Refused(
            f"control marker {path} is not valid JSON: refused (remove it by hand)"
        ) from e
    if not isinstance(m, dict) or m.get("root") != str(root):
        raise Refused(f"control marker {path} is not for this root: refused")
    note, settled = stop_orphan(m, root)
    if settled:
        unlink_state(path)
        return True, f"control run: {note}"
    return False, (
        f"control run: {note}; the control marker {path} is KEPT because its test group may still run: "
        f"stop it by hand, then remove the marker"
    )


def settle_control(root: pathlib.Path, key: str) -> tuple[bool, str | None]:
    """r7 review N1: a control marker that cannot be read, is not valid JSON or does not belong to this root must not
    block the restore of a PLANTED file: the problem is recorded and makes the final answer exit 3, nothing more."""
    if not os.path.lexists(control_marker_path(key)):
        return True, None
    try:
        return restore_control(root, key)
    except (Refused, OSError) as e:
        why = e.strerror or e if isinstance(e, OSError) else e
        return False, (
            f"control run: RESTORE FAILED: {why}; its test group may still run; the control marker "
            f"{control_marker_path(key)} is KEPT (check it by hand)"
        )


def link_hint(root: pathlib.Path, rel) -> str:
    """r8 (independent r7 run, T-ln): when the restore failed because the file under test, or a folder on the way, is now a
    symbolic link, say exactly what to do. Nothing is ever written through a link."""
    if not isinstance(rel, str):
        return ""
    cur = root
    parts = pathlib.PurePosixPath(rel).parts
    for i, part in enumerate(parts):
        cur = cur / part
        if cur.is_symlink():
            try:
                where = os.readlink(cur)
            except OSError:
                where = "?"
            q, script = shlex.quote(str(cur)), shlex.quote(sys.argv[0])
            again = f"python3 {script} --root {shlex.quote(str(root))} --restore"
            if i == len(parts) - 1:
                return (
                    f"; the file under test is now a symbolic link ({cur} -> {shown(where)}) and nothing was written through it. "
                    f"Do this: 1) rm -- {q}   2) {again}   (the original is created again from the backup)"
                )
            return (
                f"; a folder on the way is a symbolic link ({cur} -> {shown(where)}) and the planted file may be behind it. "
                f"Do this: 1) mv -- {q} {q}.link   2) put the real folder back under the name {part!r}   3) {again}"
            )
    return ""


def verify_against_git(
    root: pathlib.Path, expected_ref: pathlib.Path, extra: set[str]
) -> tuple[bool, str]:
    """r9 (r8 M1): with `--restore --sha` and no marker to go by, the files themselves decide: the tree under --root is
    compared with the git archive named on the command line (same comparison as a normal run: `.venv` and the cache
    folders are skipped, --extra files may exist). Equal: nothing is planted (exit 0). Different: a mutant may be planted
    (exit 3) and the first differing files are named."""
    diffs = diff_trees(expected_ref, root, extra)
    if not diffs:
        return (
            True,
            "the tree equals the git archive given with --sha: no file is planted or changed",
        )
    return False, (
        f"the tree differs from the git archive given with --sha in {len(diffs)} file(s), first: {diffs[:5]}: a mutant may "
        f"still be planted (no marker was found to restore it from). By hand: git show <sha>:<file> > <file> for each"
    )


def restore_from_marker(
    root: pathlib.Path,
    expected_ref: pathlib.Path | None = None,
    extra: set[str] | frozenset[str] = frozenset(),
) -> tuple[bool, str]:
    """Returns (ok, text); ok means the file is KNOWN to hold the original. No marker found anywhere and no --sha to check
    the files with: planted-ness is UNKNOWN, which is a refusal (Refused, exit 2), never ok (r8 M1)."""
    ensure_state()
    key = key_for(root)
    marker = STATE / f"{key}.planted.json"
    control_ok, control = settle_control(root, key)
    if not os.path.lexists(marker):
        ok, text, found = other_state_check(root, key)
        if expected_ref is not None and ok:  # git decides, whatever the state folders say
            vok, vtext = verify_against_git(root, expected_ref, set(extra))
            ok, text = vok, f"{text}; {vtext}" if found else vtext
        elif not found and control_ok and control is None:
            # a settled CONTROL marker is knowledge: a control run plants nothing, so its group is stopped and nothing is open
            raise NoMarker(
                f"{text}. Nothing was written. Do ONE of: run --restore again with the TMPDIR of the killed run (TMPDIR=<its "
                f"folder>), or add --sha COMMIT [--repo R] [--patch F] [--extra F] so the files are compared with git"
            )
        return ok and control_ok, f"{control}; {text}" if control else text
    m = load_marker(marker)
    # Class (r6 M1, r7 M1): an exit code that says "nothing planted" while the mutant is planted. Only a marker that names
    # another root or another backup path is a refusal (Forged, exit 2, nothing written). Everything else that goes wrong
    # once a marker for this root exists (unreadable or damaged marker, missing, linked or damaged backup, state folder,
    # real-repository check, lock) is raised as Refused or fails otherwise and main() maps it to exit 3.
    bk = STATE / f"{key}.backup"
    if m.get("root") != str(root) or m.get("backup") != str(bk):
        why = (
            f"marker is for another root ({shown(m.get('root'))}): refused"
            if m.get("root") != str(root)
            else f"marker names a backup other than {bk}: refused"
        )
        if expected_ref is not None:
            # r10 m5: the marker is not this run's, but the files themselves can still be compared with the git archive
            vok, vtext = verify_against_git(root, expected_ref, set(extra))
            if not vok:
                raise Refused(
                    f"{why}; {vtext}"
                )  # a marker exists for this key: exit 3, a mutant may be planted
            why = f"{why}; {vtext} (the marker was left alone; to remove it use --discard-marker)"
        raise Forged(why)
    saved = read_state(bk)
    if sha256(saved) != m["orig_sha256"]:
        raise Refused(
            "the saved backup does not match the hash recorded in the marker: nothing written"
        )
    if (
        expected_ref is not None
    ):  # --sha given on the restore command line: git, not the state folder, is the authority (r8 d)
        try:
            want = read_regular(safe_rel(expected_ref, m["file"], "marker file"))
        except (Refused, OSError, TypeError) as e:
            raise Refused(
                f"the git archive given with --sha has no usable {m['file']!r} ({e}): nothing written"
            ) from e
        if want != saved:
            raise Refused(
                f"the saved backup differs from {shown(m['file'])} in the git archive given with --sha: the state folder may be "
                f"forged or --sha is the wrong commit; nothing written. By hand: git show <sha>:{shown(m['file'])} > the file"
            )
        ref_mode = stat.S_IMODE(os.stat(safe_rel(expected_ref, m["file"], "marker file")).st_mode)
        mm = m.get("mode") if isinstance(m.get("mode"), int) else None
        special = (
            f"the mode in the marker ({oct(mm)}) has a special bit (setuid, setgid, sticky) or is writable by "
            f"group or others: git has neither, so the marker may be forged; nothing written (r10 m2)"
            if mm is not None
            else ""
        )
        if mm is not None and mm & 0o7000:  # a setuid, setgid or sticky bit is named as such first
            raise Refused(special)
        if mm is not None and (mm & 0o111) != (ref_mode & 0o111):
            raise Refused(
                f"the mode in the marker ({oct(mm)}) has other execute bits than {shown(m['file'])} in the git archive given "
                f"with --sha ({oct(ref_mode)}): the marker may be forged; nothing written"
            )
        if mm is not None and mm & 0o022:  # r11 m6: any group or other write bit, not only "other"
            raise Refused(special)
    try:
        # must_exist=False: a deleted target is re-created (review r3 minor); checked again right before the write
        target = safe_rel(root, m["file"], "marker file", must_exist=False)
        orphan, settled = stop_orphan(
            m, root
        )  # r7 review N2: an orphan that could not be stopped is reported, not hidden
        mode = (
            m["mode"]
            if isinstance(m.get("mode"), int)
            and not isinstance(m["mode"], bool)
            and 0 <= m["mode"] <= 0o7777
            else 0o644
        )
        mode_note = ""
        if mode & 0o7000:
            # r11 MAJ-1: a plain --restore believes the marker, and a forged marker must never make a setuid, setgid or sticky
            # file: the bits are cut off (never written); the content is still restored; the text says so
            mode_note = (
                f"; NOTE the marker mode {oct(mode)} had a setuid, setgid or sticky bit: --restore never writes those, the "
                f"file got {oct(mode & 0o777)} (set the special bit by hand if it was really there)"
            )
            mode &= 0o777
        if isinstance(m.get("root_dev"), int) and isinstance(m.get("root_ino"), int):
            now = os.stat(root)
            if (now.st_dev, now.st_ino) != (m["root_dev"], m["root_ino"]):
                raise Refused(
                    f"the folder now at {root} is not the folder the mutant was planted in (it was renamed or "
                    f"replaced): look for the renamed folder and restore it by hand from {bk}"
                )
        # compare, write and verify on ONE open file (review r5 M3); nothing is compared by path
        already, back = restore_target(target, saved, root, create=True, mode=mode)
        ok = sha256(back) == m["orig_sha256"]
    except (Refused, OSError) as e:
        why = e.strerror or e if isinstance(e, OSError) else e
        text = (
            f"RESTORE FAILED: cannot write {shown(m['file'])} back: {why}; the mutant may still be planted; marker and backup kept"
            + link_hint(root, m["file"])
        )
        return False, f"{control}; {text}" if control else text
    note = " (it already held the original)" if already else ""
    text = f"{orphan}; restored {shown(m['file'])} from {bk}{note}; hash matches saved original: {ok}{mode_note}"
    if ok and not settled:
        text += (
            "; the test group may STILL RUN (it could not be stopped or verified): marker and backup KEPT, stop it by "
            "hand, then run --restore again"
        )
    elif ok:
        unlink_state(marker)
        unlink_state(bk)
    return ok and settled and control_ok, f"{control}; {text}" if control else text


def discard_marker(
    root: pathlib.Path,
    expected_ref: pathlib.Path,
    extra: set[str],
    unchecked_folder: bool = False,
) -> tuple[bool, str]:
    """r9 minor 3: a marker that `--restore` can never use (the root folder was renamed and replaced, the marker names
    another root or backup, it is damaged) used to strand the operator: exit 3 or 2 on every try and no command to remove it.
    Deleting a marker is safe only when the files themselves are known to be original: the tree under --root must equal the
    git archive named by --sha, and no orphaned test group of that marker may still run.
    r11 m7: the CONTROL marker (a killed baseline run) has no folder identity to check; it is removed after the same git comparison and
    after its test group is stopped, so the identity check applies to the mutant marker only.
    r10 M1 (class: an exit code 0 that says "nothing is planted" while the place the mutant was planted is not looked at): the
    tree under --root says nothing about a folder that was renamed away, and a marker that cannot be read says nothing about
    its test group. So the marker must PROVE it belongs to the folder now at --root (its recorded device and inode equal this
    folder's) and must be readable; otherwise the answer is exit 3, nothing removed, unless the operator adds
    `--accept-unchecked-folder` (a statement that they looked at, or do not need, the folder that was renamed away)."""
    ensure_state()
    key = key_for(root)
    vok, vtext = verify_against_git(root, expected_ref, extra)
    if not vok:
        return False, f"marker NOT discarded: {vtext}"
    notes = [vtext]
    unchecked: list[str] = []
    todo: list[pathlib.Path] = []
    now = os.stat(root)
    for path in (STATE / f"{key}.planted.json", control_marker_path(key)):
        if not os.path.lexists(path):
            continue
        planted = path.name.endswith(".planted.json")
        try:
            m = loads_json(read_state(path))
        except (Refused, ValueError, OSError):
            m = None
        if not isinstance(m, dict):
            unchecked.append(
                f"{path.name} cannot be read as a marker: its test group, if any, was not looked for"
                + (" and the folder it was planted in is unknown" if planted else "")
            )
            note, settled = "the marker could not be read", True
        else:
            if planted and (
                m.get("root") != str(root)
                or not isinstance(m.get("root_dev"), int)
                or not isinstance(m.get("root_ino"), int)
                or (now.st_dev, now.st_ino) != (m["root_dev"], m["root_ino"])
            ):
                unchecked.append(
                    f"{path.name} was written for another folder than the one now at {root} (renamed away, replaced, or no "
                    f"folder identity recorded): the folder the mutant was planted in was NOT compared with git"
                )
            note, settled = stop_orphan(m, root)
        if not settled:
            return False, f"marker NOT discarded: {note}; stop that test group by hand first"
        notes.append(f"{path.name}: {note}")
        todo.append(path)
    if unchecked and not unchecked_folder:
        return False, (
            f"marker NOT discarded (exit 3): {'; '.join(unchecked)}. The tree at {root} equals git, but that says nothing about "
            f"the other folder. Look at it by hand; if it does not matter, repeat the command with --accept-unchecked-folder"
        )
    for path in todo:
        unlink_state(path)
    unlink_state(STATE / f"{key}.backup")
    tail = (
        f" ACCEPTED BY YOU (--accept-unchecked-folder), not checked: {'; '.join(unchecked)}"
        if unchecked
        else ""
    )
    return True, "marker and backup discarded (" + "; ".join(notes) + ")." + tail


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
            if not path or too_long(str(real_root) + "/" + path):  # r11 m2: root plus path together
                raise no(t, "is empty or too long together with --root")
            if not (real_root / path).resolve().is_relative_to(real_root):
                raise no(t, "is not a path inside --root")
        i += 1


def pytest_config_in(d: pathlib.Path) -> list[str]:
    """Names of the files in folder `d` from which pytest would take settings. Files are parsed, not searched for
    a text, so dotted keys (`tool.pytest.ini_options.x = ...`) and inline tables count too; a file that cannot be
    read or parsed counts as holding settings (fail closed)."""
    found = [n for n in PYTEST_INI_NAMES if (d / n).is_file()]
    f = d / "pyproject.toml"
    if f.is_file():
        import tomllib  # here, not at the top: a Python without it must still reach the version refusal in main()

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
    for t in path_args(tests):
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
        except OSError as e:  # the interpreter cannot be started, the folder is gone ...
            raise Refused(f"import check of {mod} cannot start: {e.strerror or e}") from e
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


def boot_ticks() -> int:
    """Now, in the unit of the start times in /proc/<pid>/stat (clock ticks since boot)."""
    return int(time.clock_gettime(time.CLOCK_BOOTTIME) * CLK_TCK)


def sweep_group(pgid: int, started_ticks: int | None = None, ended_ticks: int | None = None) -> str:
    """After the leader has ended: stop what is still alive in its process group (a test may have started a
    background process). While any member lives the number cannot be given to another group, so the members are
    this run's own (review r4 nit 5); but once the leader has been waited for and the group was empty, a stranger may
    have been given the number (review r6 nit 3): when the start time of the leader and the time it ended are known,
    only members that started in between are ours. Returns a line for the raw file."""
    left = group_members(pgid)
    if started_ticks is not None and ended_ticks is not None:
        ours = [
            q for q in left if (qs := proc_stat(q)) and started_ticks <= qs["start"] <= ended_ticks
        ]
        if left and not ours:
            return f"process(es) {left} now hold the number of the test group but started outside this run: left alone"
        left = ours
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
        "-rfp",
        *(
            t for t in tests if t != "-q"
        ),  # the command already says -q: a second -q drops pytest's summary line
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
        proc = Child(
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
    leader_start = (proc_stat(proc.pid) or {}).get(
        "start"
    )  # for the pid-reuse check in sweep_group
    try:
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
                SIG.allow = (
                    False  # first: nothing in the cleanup below may be cut short by a signal
                )
                stop_or_kill(
                    proc
                )  # a failure to stop the group is no reason to lose the result (review r4 T46)
                rest = reap(proc)  # a second communicate() returns everything printed so far
                out = (
                    f"TIMEOUT after {timeout} s\n--- output printed before the timeout ---\n{rest}"
                )
                rc = None
            ended = boot_ticks()  # as early as possible after the leader was waited for
            SIG.allow = False
            try:
                note = sweep_group(proc.pid, leader_start, ended)
            except OSError as e:
                note = f"could NOT sweep the test group ({e.strerror or e})"
            result = (cmd, rc, out, note)
        finally:
            # review r5 nit 2: on EVERY way out of the body (also a failure that is no signal) `allow` is off and later
            # signals are only remembered, so none can raise again before the group is stopped below; a signal
            # arriving inside this `finally` still lands in the outer `except`, which stops the group
            SIG.allow = False
            SIG.critical = True
        SIG.critical = was_critical
        if (
            not was_critical
        ):  # a control run: nothing is planted, so a remembered signal is delivered now
            deliver_pending()
        return result
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
                # leader ended already: stop members that outlived it (only those that started before now)
                sweep_group(proc.pid, leader_start, boot_ticks())
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
        SIG.critical = was_critical  # the group is stopped: the caller's state again
        raise


def summary(out: str):
    lines = [x for x in out.splitlines() if x.strip()]
    last = lines[-1] if lines else ""
    failed = [x.split(" ", 1)[1].split(" - ")[0] for x in lines if x.startswith("FAILED ")]
    return last, failed


def passed_count(last: str) -> int:
    """Number of passed tests in pytest's last line (`2 passed, 1 skipped in 0.1s`); 0 when the word is not there."""
    mt = re.search(r"\b(\d+) passed\b", last)
    return int(mt.group(1)) if mt else 0


def passed_total(out: str) -> int:
    """Passed tests in the whole pytest output: the larger of the count in the last line and the number of
    `PASSED ...` lines (`-rp`). A doubled `-q` (one from an ini file's addopts) drops the last line's count, so
    the `PASSED` lines are the second witness."""
    n_lines = sum(1 for x in out.splitlines() if x.startswith("PASSED "))
    return max(passed_count(summary(out)[0]), n_lines)


VERDICT_KINDS = ("KILLED", "SURVIVED", "TIMEOUT", "COULD-NOT-PLANT", "NO-TEST-PASSED", "ERROR")


def kind_of(verdict: str) -> str:
    return next((k for k in VERDICT_KINDS if verdict.startswith(k)), "ERROR")


def file_diffs(ref_files: dict[str, str], now: dict[str, str], extra: set[str]) -> list[str]:
    """Files whose hash differs between the reference and the tree now; declared --extra files may exist beyond it."""
    return [
        f
        for f in sorted(set(ref_files) | set(now))
        if ref_files.get(f) != now.get(f) and not (f in extra and f not in ref_files)
    ]


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
    # review r5 nit 5: the import check is made again before EACH mutant (a test of an earlier mutant could have changed
    # `.venv` or a .pth file, which are not compared); a failure gives COULD-NOT-PLANT, nothing is planted
    imp_line = a.imports.get(m["file"], "not run")
    recheck_error = None
    if n == 1 and not a.skip_import_check:
        try:
            imp_line = (
                import_check(root, a.pythonpath, [m["file"]])[m["file"]]
                + " (checked again before this mutant)"
            )
        except Refused as e:
            recheck_error = str(e)
    if n != 1:
        verdict, out, cmd, rc = f"COULD-NOT-PLANT (old text occurs {n} times)", "", [], None
        restore = "no change made"
    elif recheck_error is not None:
        verdict, out, cmd, rc = (
            f"COULD-NOT-PLANT (import check failed just before this mutant: {recheck_error[:300]})",
            "",
            [],
            None,
        )
        restore = "no change made"
        imp_line = recheck_error[:300]
    else:
        info = {
            "root": str(root),
            "file": m["file"],
            "backup": str(backup),
            "orig_sha256": sha256(orig),
            "mutant": f"{a.prefix}-{m['id']}",
            "mode": stat.S_IMODE(sp.st_mode),
            "root_dev": ROOT_IDENT[1] if ROOT_IDENT else None,
            "root_ino": ROOT_IDENT[2] if ROOT_IDENT else None,
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
                SIG.own_marker = True  # from here this run owns a marker: any exit while it exists is exit 3 (r7 review M1)
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
                    # compare, write (only if the bytes differ: review r4 nit 1, a file that was never touched is not
                    # written again) and verify on ONE open file (review r5 M3), never by path
                    _, back = restore_target(p2, orig, root, mode=stat.S_IMODE(sp.st_mode))
                    same_hash = back == orig and back == ref_bytes
                except (
                    RESTORE_ERRORS
                ) as e:  # any failure (also a bug) to write the original back is a failed restore
                    print("RESTORE ERROR:", e, file=sys.stderr)
                    same_hash = False
                if not same_hash:
                    print(
                        "RESTORE FAILED",
                        m["id"],
                        "(marker and backup kept; run --restore)",
                        file=sys.stderr,
                    )
                    leave(EXIT_RESTORE_FAILED)
                # verified identical: no marker may stay, even on an error
                unlink_state(marker)
                unlink_state(backup)
                SIG.own_marker = False
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
        if verdict == "SURVIVED" and passed_total(out) == 0:
            # exit 0 without one passed test (all skipped, nothing selected): nothing was checked (review r5 M1)
            verdict = "NO-TEST-PASSED"
    # integrity of the whole scratch tree after this mutant (review r4 M3): every file but .venv and the caches
    # against the fresh git archive; a test that wrote a conftest.py, an ini file or data would contaminate the
    # next mutant. Files declared with --extra are allowed to exist (their content is not compared).
    now = tree_files(root)
    diffs = file_diffs(a.ref_files, now, set(a.extra))
    integrity = (
        f"{len(now)} files compared with the git archive (all but .venv directly under the root and the cache "
        f"folders), digest {tree_digest(now)}; differing files ({len(diffs)}; 0 = clean): {diffs}"
    )
    last, failed = summary(out)
    flags = []
    if (
        verdict == "KILLED"
        and a.baseline_failed is not None
        and set(failed) == set(a.baseline_failed)
    ):
        flags.append(
            "the failing tests are the same as the baseline's (here: none named): the failure may not come from the mutant"
        )
    text = (
        f"MUTANT {a.prefix}-{m['id']}  VERDICT: {verdict}\n"
        f"description: {m.get('desc', '')}\n"
        f"base commit: {a.sha_full}{' (given as ' + a.sha + ')' if a.sha != a.sha_full else ''}   root: {a.root}   file: {m['file']}\n"
        f"command: {' '.join(cmd)}   (cwd={a.root}; environment: {', '.join(sorted(test_env(a.pythonpath)))} only)\n"
        f"baseline: {a.baseline_note}\n"
        f"flags: {'; '.join(flags) if flags else 'none'}\n"
        f"import check: {imp_line}\n"
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
            "kind": kind_of(verdict),
            "flags": flags,
            "rc": rc,
            "first": failed[0] if failed else "",
            "n_failed": len(failed),
            "summary": last,
            "tree_differences": diffs,
        }
    )
    print(
        m["id"],
        verdict,
        failed[0] if failed else "",
        *(["FLAGGED:"] + flags if flags else []),
        flush=True,
    )
    return diffs


def load_mutants(a) -> list[dict]:
    if a.list:
        try:
            ms = loads_json(pathlib.Path(a.list).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:  # missing, unreadable, not UTF-8, not JSON
            raise Refused(
                f"--list {a.list} cannot be read as a JSON list ({type(e).__name__}: {e}): refused"
            ) from e
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
        if not NAME_RE.fullmatch(m["id"]) or m["id"] in seen or m["id"] in RESERVED_IDS:
            raise Refused(
                f"mutant id is not a plain unique name (and not one of {sorted(RESERVED_IDS)}, which name other raw files): "
                f"{m['id']!r}"
            )
        seen.add(m["id"])
        for k in (
            "id",
            "file",
            "old",
            "new",
            "desc",
        ):  # review r6 nit 5: a lone surrogate cannot be written as UTF-8
            v = m.get(k, "")
            if not isinstance(v, str):
                raise Refused(f"mutant {m['id']}: {k} is not a string: refused")
            try:
                v.encode("utf-8")
            except UnicodeEncodeError as e:
                raise Refused(
                    f"mutant {m['id']}: {k} holds a character that is not valid text (a lone surrogate): refused"
                ) from e
        if m["old"] == m["new"] or not m["old"]:
            raise Refused(f"mutant {m['id']}: old text is empty or equal to new text (a no-op)")
    return ms


def tree_check(a, root, fresh, marker) -> list[str]:
    """Differences between the scratch tree and a fresh archive; written to raw/<prefix>-tree-diff.txt."""
    diffs = diff_trees(fresh, root, set(a.extra))
    leftover = os.path.lexists(marker)  # r10 m7: a dangling link in the marker's place counts too
    write_out(
        pathlib.Path(a.raw) / f"{a.prefix}-tree-diff.txt",
        f"TREE CHECK after the loop\ncompared: <fresh git archive {a.sha_full} + patches {a.patch}> against {a.root} "
        f"(skipping {sorted(SKIP_TOP)} directly under the root only and {sorted(SKIP_ANY)} anywhere; symbolic links compared by target; special files recorded, never read)\n"
        f"declared extra files (allowed as 'only in root'): {a.extra}\n"
        f"differing files ({len(diffs)}; 0 = clean): {diffs}\nmarker left behind: {leftover}\n",
    )
    return [*diffs, *(["<marker left behind>"] if leftover else [])]


def stop_if_dirty(a, root: pathlib.Path, after: str) -> None:
    """The tree must equal the git archive before the first mutant is planted; if running the import check or the control
    tests changed it, stop with exit 4 (review r5 nit 6). Files declared with --extra may exist."""
    diffs = file_diffs(a.ref_files, tree_files(root), set(a.extra))
    if diffs:
        print(
            f"STOPPED before the first mutant: {after} changed the scratch tree: {diffs[:5]}",
            file=sys.stderr,
        )
        leave(EXIT_TREE_NOT_CLEAN)


def summarize(results: list[dict], planned: int, baseline_ran: bool = True) -> tuple[str, bool]:
    """The SUMMARY line (review r5 M2, r6 M2): one count per verdict kind, flagged and not run. `complete` is True only
    when a baseline ran and every planned mutant ran and has a clean KILLED or SURVIVED verdict without a flag."""
    count = {k: sum(1 for r in results if r["kind"] == k) for k in VERDICT_KINDS}
    flagged = sum(1 for r in results if r["flags"])
    not_run = planned - len(results)
    complete = (
        baseline_ran
        and not_run == 0
        and flagged == 0
        and all(r["kind"] in ("KILLED", "SURVIVED") for r in results)
    )
    parts = ", ".join(f"{count[k]} {k}" for k in VERDICT_KINDS)
    line = (
        f"SUMMARY: {planned} mutant(s) planned, {len(results)} ran: {parts}; {flagged} flagged; {not_run} not run; "
        + (
            "COMPLETE (a baseline ran and every mutant has a clean KILLED or SURVIVED verdict)"
            if complete
            else f"NO BASELINE (--no-control): INCOMPLETE (exit {EXIT_INCOMPLETE}) whatever the verdicts are"
            if not baseline_ran
            else f"INCOMPLETE (exit {EXIT_INCOMPLETE} unless the tree is not clean: then exit {EXIT_TREE_NOT_CLEAN})"
        )
    )
    return line, complete


def may_be_planted(
    restore: bool, root: pathlib.Path, marker: pathlib.Path, e: BaseException
) -> bool:
    """The ONE choke point for the exit code (r7 review M1; class: an exit code that says "nothing planted" while the mutant
    is planted). True when a mutant, or a test group of a control run, may still be in place: with `--restore` whenever a
    planted or control marker for this root exists (unless the marker is Forged: it names another root or backup, nothing is
    written, exit 2); in a normal run when THIS run wrote its marker and has not verified the restore. Then the exit code is
    3 (restore failed, marker and backup kept), never 2 and never Python's own 1."""
    if isinstance(e, Forged):
        return False
    if os.path.lexists(marker) and (restore or SIG.own_marker):
        return True
    return restore and os.path.lexists(control_marker_path(key_for(root)))


def state_folders() -> list[pathlib.Path]:
    """Every folder a run of this tool may keep markers in: ours and the other usual places (the same list `--restore` and
    the other-run check search)."""
    spots = {p.resolve() for p in STATE_PARENTS} | {STATE.parent.resolve()}
    spots |= {pathlib.Path(v).resolve() for v in map(os.environ.get, ("TMP", "TEMP")) if v}
    return sorted(parent / STATE.name for parent in spots)


def check_out_json_target(path: pathlib.Path) -> None:
    """r10 m3: --out-json overwrites its target, so an EXISTING file is accepted only when it is the tool's own earlier
    result (a JSON list of objects that each have `id` and `verdict`); any other file is refused, nothing is overwritten.
    A path that does not exist yet is fine."""
    if not os.path.lexists(path):
        return
    try:
        old = loads_json(read_regular(path))
    except (Refused, ValueError, OSError):
        old = None
    ok = (
        isinstance(old, list)
        and old
        and all(isinstance(x, dict) and "id" in x and "verdict" in x for x in old)
    )
    if not ok:
        raise Refused(
            f"--out-json {path} already exists and is not a result file of this tool (a JSON list of objects with id and "
            f"verdict): refused, it would be overwritten. Use a new file name"
        )


def reject_output_inputs(paths: list[pathlib.Path], inputs: list[pathlib.Path]) -> None:
    """r7 review N4: an output file (--out-json, raw files) must not be one of the files this run reads: run.py itself,
    --list, --patch. Compared by device and inode, so a different spelling or a hard link is caught too."""
    states = [f.resolve() for f in state_folders()]
    for o in paths:
        here = pathlib.Path(os.path.abspath(o)).resolve()
        for state in states:  # r10 m3: every folder a marker may live in, not only the current one
            if here.is_relative_to(state):
                raise Refused(
                    f"output path {o} lies in the state folder {state}: refused (a file written there could pose as a marker)"
                )
        if not os.path.lexists(o):
            continue
        for i in inputs:
            try:
                if os.path.samefile(o, i):
                    raise Refused(
                        f"output path {o} is the same file as the input {i}: refused (it would be overwritten)"
                    )
            except OSError:
                continue


def other_run_check(root: pathlib.Path, key: str) -> None:
    """r7 review N6: state and lock live in a folder named after TMPDIR. A run with ANOTHER TMPDIR on the same root holds
    its lock and keeps its marker THERE: before this run starts, look in the usual places (the same list as `--restore`):
    a still planted file or a lock that is held now refuses this run. (A run that has not yet taken its lock cannot be
    seen: two runs started in the same instant with different TMPDIR remain a race, named in the docstring.)"""
    ok, text, _found = other_state_check(root, key)
    if not ok:
        raise Refused(text)
    here = STATE.parent.resolve()
    spots = {p.resolve() for p in STATE_PARENTS}
    spots |= {pathlib.Path(v).resolve() for v in map(os.environ.get, ("TMP", "TEMP")) if v}
    for parent in sorted(spots - {here}):
        folder = parent / STATE.name
        lock = folder / f"{key}.lock"
        try:
            fst = os.lstat(folder)
            if not stat.S_ISDIR(fst.st_mode) or fst.st_uid != os.geteuid() or fst.st_mode & 0o077:
                continue
            fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except OSError:
            continue
        with os.fdopen(fd, "r") as fh:
            lst = os.fstat(fh.fileno())
            if not stat.S_ISREG(lst.st_mode) or lst.st_uid != os.geteuid():
                continue
            try:
                fcntl.flock(fh, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except OSError as e:
                raise Refused(
                    f"another run holds the lock for {root} in {folder} (it uses another TMPDIR): two runs on one "
                    f"tree would plant over each other"
                ) from e


PATH_MAX_BYTES, NAME_MAX_BYTES = (
    4096,
    255,
)  # Linux limits: a longer path or name can never be opened


def too_long(v: str) -> str | None:
    """r10 (independent r9 run: a root over 4096 bytes ended in Python's own exit 1): the reason a path text can never be
    used, or None. Checked where a value enters (argparse, safe_rel, the test paths) so no later call can raise ENAMETOOLONG."""
    try:
        raw = os.fsencode(v)
    except UnicodeEncodeError:
        return "it is not valid text for a file name"
    if (
        len(raw) >= PATH_MAX_BYTES
    ):  # r11 m2: the 4096 of the kernel counts the closing NUL, so 4095 bytes is the longest path
        return f"it is {len(raw)} bytes long (the limit is {PATH_MAX_BYTES - 1})"
    if any(len(part) > NAME_MAX_BYTES for part in raw.split(b"/")):
        return f"one name in it is longer than {NAME_MAX_BYTES} bytes"
    return None


ARG_MAX_BYTES = 100_000  # one program argument: Linux allows 131072 bytes (MAX_ARG_STRLEN); r11 m1


def path_indexes(tests: list[str]) -> list[int]:
    """r11 m1 (class: a word that is not a path treated as one): the arguments after `--` that are PATHS (with an optional ::node).
    Not paths: an option (starts with "-"), the expression after -k or -m, the plugin name after -p. ONE parser, used by the
    length check, by `check_pytest_config` (r10 crashed there with a traceback on a long -k expression) and by `check_test_args`."""
    out, skip = [], False
    for i, w in enumerate(tests):
        if skip:
            skip = False
        elif w in ("-k", "-m", "-p"):
            skip = True
        elif not w.startswith("-"):
            out.append(i)
    return out


def path_args(tests: list[str]) -> list[str]:
    return [tests[i] for i in path_indexes(tests)]


def refuse_in_state_folders(path: pathlib.Path, what: str) -> None:
    """r11 m3 (class: a folder created before every refusal that could stop it): no output path, and no folder to be created for
    one, may lie in a folder a marker may live in (ours and the other usual places). Works on a path that does not exist yet."""
    here = pathlib.Path(os.path.abspath(path)).resolve()
    for state in (f.resolve() for f in state_folders()):
        if here.is_relative_to(state):
            raise Refused(
                f"{what} {path} lies in the state folder {state}: refused (a file written there could pose as a marker)"
            )


def nonempty(v: str) -> str:
    """argparse type: an empty value is an error, never "not given" (r10 M2), and so is a text no path can be (too long)."""
    if v == "":
        raise argparse.ArgumentTypeError(
            "an empty value is not allowed (is a shell variable unset?)"
        )
    bad = too_long(v)
    if bad:
        raise argparse.ArgumentTypeError(f"not usable as a path or name: {bad}")
    return v


def sha_arg(v: str) -> str:
    """argparse type for --sha: 4 to 64 hex digits; an empty or malformed value is refused with exit 2 (r10 M2)."""
    if not SHA_RE.fullmatch(v):
        raise argparse.ArgumentTypeError(
            f"{v!r} is not a commit id (4 to 64 hexadecimal digits; an empty value is refused: is a shell variable unset?)"
        )
    return v


def restore_args(a, repo_given: bool) -> str:
    """The extra words of the restore command that make it equal to this run's own checks (--repo and
    --real-repo are what refuse a root inside the real repository), review r4 nit 10."""
    words = (["--repo", a.repo] if repo_given else []) + [
        w for x in a.real_repo for w in ("--real-repo", x)
    ]
    return "".join(f" {shlex.quote(w)}" for w in words)


def main():
    global HELPER_TIMEOUT
    sys.stdout, sys.stderr = (
        SafeOut(1),
        SafeOut(2),
    )  # first: even the first refusal text must not be able to fail
    if (
        tuple(sys.version_info[:3]) < MIN_PYTHON
    ):  # before anything else, on every option including --restore (review r5 nit 8)
        print(
            f"REFUSED: this tool needs Python {'.'.join(map(str, MIN_PYTHON))} or newer (tomllib, tarfile filters); "
            f"this is {'.'.join(map(str, tuple(sys.version_info[:3])))}",
            file=sys.stderr,
        )
        sys.exit(EXIT_REFUSED)
    if _INIT_ERRORS:  # r10 m10
        print(f"REFUSED: this tool cannot start here: {'; '.join(_INIT_ERRORS)}", file=sys.stderr)
        sys.exit(EXIT_REFUSED)
    argv = sys.argv[1:]
    tests = argv[argv.index("--") + 1 :] if "--" in argv else []
    ap = argparse.ArgumentParser()
    for k in ("root", "prefix", "raw"):
        ap.add_argument("--" + k, required=(k == "root"), type=nonempty)
    # r10 M2 (class: an empty value read as "option not given"): `--sha ""` (an unset shell variable) used to drop the git
    # authority of --restore; an empty value is now a refusal (exit 2) for every option that names a path, a commit or a name
    ap.add_argument("--sha", type=sha_arg)
    ap.add_argument("--list", type=nonempty)
    ap.add_argument("--id", type=nonempty)
    ap.add_argument("--file", type=nonempty)
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--desc", default="")
    ap.add_argument(
        "--control",
        dest="control",
        action="store_true",
        default=True,
        help="run the unmutated tree first and refuse the mutants unless it passes (the default)",
    )
    ap.add_argument(
        "--no-control",
        dest="control",
        action="store_false",
        help="skip the baseline: the run can never be COMPLETE and exits 5 (the last of --control/--no-control wins)",
    )
    ap.add_argument("--out-json", type=nonempty)
    ap.add_argument("--timeout", type=int, default=600, help="seconds per test run")
    ap.add_argument(
        "--pythonpath",
        type=nonempty,
        help="only for the proof copies, whose venv .pth points at another tree",
    )
    ap.add_argument(
        "--repo",
        default=None,
        type=nonempty,
        help="a folder inside the repository that holds --sha (default: this script's folder; "
        "--restore needs no repository unless --repo is given)",
    )
    ap.add_argument(
        "--real-repo",
        action="append",
        default=[],
        type=nonempty,
        help="a folder that must never be used as --root or inside it; repeatable",
    )
    ap.add_argument(
        "--patch",
        action="append",
        default=[],
        type=nonempty,
        help="patch applied (-p1) on top of the git archive to get the expected tree; repeatable",
    )
    ap.add_argument(
        "--extra",
        action="append",
        default=[],
        type=nonempty,
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
    ap.add_argument(
        "--discard-marker",
        action="store_true",
        help="with --restore --sha: delete a marker and backup that cannot be used (the folder was renamed, the marker is "
        "damaged or names another root) AFTER the tree under --root was compared with git and found equal",
    )
    ap.add_argument(
        "--accept-unchecked-folder",
        action="store_true",
        help="with --discard-marker: also discard a marker that does not prove it belongs to the folder now at --root "
        "(that folder was renamed away or replaced, or the marker cannot be read). You state that you looked at the other folder "
        "or do not need it; the text says what was not checked",
    )
    ap.add_argument(
        "--helper-timeout",
        type=int,
        default=HELPER_TIMEOUT,
        help="seconds one git or patch call may take before it is stopped and refused (default %(default)s)",
    )
    a = ap.parse_args(argv[: argv.index("--")] if "--" in argv else argv)
    if not sys.platform.startswith("linux") or not pathlib.Path("/proc/self/stat").is_file():
        print(
            "REFUSED: this tool works on Linux only (it reads /proc to identify and stop an orphaned test run "
            "and uses waitid); on this system a --restore could not stop a leftover test run: refused",
            file=sys.stderr,
        )
        sys.exit(EXIT_REFUSED)
    if a.helper_timeout < 1:
        ap.error("--helper-timeout must be at least 1")
    HELPER_TIMEOUT = a.helper_timeout
    if a.accept_unchecked_folder and not a.discard_marker:
        ap.error("--accept-unchecked-folder only goes with --discard-marker")
    if a.discard_marker and not (a.restore and a.sha is not None):
        ap.error(
            "--discard-marker needs --restore and --sha (git must confirm the files are original)"
        )
    repo_given = a.repo is not None
    default_repo = str(pathlib.Path(__file__).resolve().parent)
    if not a.restore or repo_given or a.sha is not None:
        a.repo = a.repo or default_repo
    paths_among = set(path_indexes(tests))
    for ix, t in enumerate(tests):  # the test paths and words after `--`
        # r11 m1: the path-length limits are for PATH-shaped arguments only; the text after -k or -m is an expression (and
        # the name after -p a plugin name), never a path, so a long expression is not refused for its length. One limit
        # stays for every word: what one program argument can hold (128 KiB on Linux, E2BIG when more).
        size = len(os.fsencode(t))
        if "\0" in t:
            why = "it holds a NUL"
        elif ix in paths_among:
            why = too_long(t)
        elif size > ARG_MAX_BYTES:
            why = f"it is {size} bytes long (the limit for one argument is {ARG_MAX_BYTES})"
        else:
            why = None
        if why:
            ap.error(f"a test argument is not usable as a path or word: {why}")
    root = pathlib.Path(a.root)
    try:
        is_folder = root.is_dir()
        root = root.resolve() if is_folder else root
    except (OSError, RuntimeError, ValueError):
        is_folder = False
    if not is_folder:
        print(f"REFUSED: --root {shown(a.root)} is not a folder", file=sys.stderr)
        sys.exit(EXIT_REFUSED)
    if too_long(
        str(root) + "/x"
    ):  # r11 m2: after resolve() the path can be longer than the text given
        print(
            f"REFUSED: --root {shown(a.root)}: the resolved folder path {too_long(str(root) + '/x')}",
            file=sys.stderr,
        )
        sys.exit(EXIT_REFUSED)
    a.root = str(root)
    global ROOT_IDENT
    rst = os.stat(root)
    ROOT_IDENT = (
        str(root),
        rst.st_dev,
        rst.st_ino,
    )  # every later open of the root must find this very folder
    if not a.restore and not (a.prefix and a.raw and a.sha):
        ap.error("--sha, --prefix and --raw are required")
    # r10 m4 (class: a window between installing the handlers and the `try` that maps a signal to an exit code): the handled
    # signals are BLOCKED while the handlers are installed and the temporary folder is made, and unblocked inside the `try`,
    # so a signal there is held and then handled like any other (128+N, folder removed), never an uncaught KeyboardInterrupt
    try:
        signal.pthread_sigmask(signal.SIG_BLOCK, HANDLED_SIGNALS)
    except (OSError, ValueError):
        pass
    for signum in HANDLED_SIGNALS:
        try:
            signal.signal(signum, _term)
        except (OSError, ValueError):  # a signal the C library keeps for itself (32, 33 on Linux)
            pass
    marker = STATE / f"{key_for(root)}.planted.json"
    tmpref = None
    try:
        tmpref = pathlib.Path(tempfile.mkdtemp(prefix="mutation-ref-"))
        try:
            signal.pthread_sigmask(signal.SIG_UNBLOCK, HANDLED_SIGNALS)
        except (OSError, ValueError):
            pass
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
                expected_ref = None
                if (
                    a.sha is not None
                ):  # r8 (d): the commit named on the command line decides what the original is
                    # r9 minor 1: nothing is written yet, so a signal here ends the run (128+N) with every state file untouched
                    expected_ref = tmpref / "ref"
                    expected_ref.mkdir()
                    build_reference(a.repo, resolve_commit(a.repo, a.sha), a.patch, expected_ref)
                # review r6 nit 2: from the first write on, a signal during the restore is remembered, never raised
                SIG.critical = True
                if a.discard_marker:
                    ok, text = discard_marker(
                        root, expected_ref, set(a.extra), a.accept_unchecked_folder
                    )
                    print(text)
                    leave(0 if ok else EXIT_RESTORE_FAILED)
                ok, text = restore_from_marker(root, expected_ref, set(a.extra))
                print(text)
                if SIG.first is not None:
                    print(
                        f"signal {SIG.first} arrived during the restore: the restore was finished first",
                        file=sys.stderr,
                    )
                leave(0 if ok else EXIT_RESTORE_FAILED)
            other_run_check(root, key_for(root))
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
                    f"python3 {shlex.quote(sys.argv[0])} --root {shlex.quote(str(root))} --restore{restore_args(a, repo_given)}"
                )
            if os.path.lexists(marker):
                m = load_marker(marker)
                raise Refused(
                    f"a mutant ({shown(m['mutant'])}) is still planted in {shown(m['file'])} from an earlier run that was killed. "
                    f"Restore with: python3 {shlex.quote(sys.argv[0])} --root {shlex.quote(str(root))} --restore{restore_args(a, repo_given)}   "
                    f"(stops a leftover test run, copies {shown(m['backup'])} back and checks the hash); then run again"
                )
            a.sha_full = resolve_commit(a.repo, a.sha)  # the full id of a COMMIT (review r5 nit 9)
            a.baseline_failed = None
            a.baseline_note = "NOT RUN (--no-control): a tree that already fails would make every mutant look KILLED"
            ref = tmpref / "ref"
            ref.mkdir()
            build_reference(a.repo, a.sha_full, a.patch, ref)
            diffs = diff_trees(ref, root, set(a.extra))
            if diffs:
                raise Refused(
                    f"scratch tree differs from git archive {a.sha_full} + patches in {len(diffs)} file(s), first: {diffs[:3]}: it may hold a planted change; rebuild it from the archive"
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
            if rawdir.resolve().is_relative_to(root):
                raise Refused(
                    f"--raw {rawdir} lies inside --root {root}: refused (it would change the scratch tree)"
                )
            if rawdir.resolve().is_relative_to(
                STATE.resolve()
            ):  # before anything is created there (r9 N4 gap)
                raise Refused(
                    f"--raw {rawdir} lies in the state folder {STATE}: refused (a file written there could pose as a marker)"
                )
            refuse_in_state_folders(rawdir, "--raw")  # r11 m3: BEFORE the folder is created
            if too_long(os.path.abspath(rawdir) + "/" + a.prefix + "-" + "x" * 60 + ".txt"):
                raise Refused(
                    f"--raw {shown(a.raw)}: the folder plus a raw file name would be too long a path"
                )
            rawdir.mkdir(parents=True, exist_ok=True)
            outs = [rawdir / f"{a.prefix}-{n}.txt" for n in sorted(RESERVED_IDS)]
            outs += [rawdir / f"{a.prefix}-{m['id']}.txt" for m in ms]
            outs += [pathlib.Path(a.out_json)] if a.out_json else []
            for o in outs:  # before anything is planted (review r4 nit 11, r6 nit 4)
                check_out_path(o, root)
            if a.out_json:
                check_out_json_target(pathlib.Path(a.out_json))
            if len({os.path.abspath(o) for o in outs}) != len(outs):
                raise Refused(
                    "two output files have the same path (--out-json is also a raw file): refused"
                )
            reject_output_inputs(
                outs,
                [
                    pathlib.Path(__file__),
                    *([pathlib.Path(a.list)] if a.list else []),
                    *map(pathlib.Path, a.patch),
                ],
            )
            results = []
            a.ref_files = tree_files(ref)
            # review r5 nit 6: the tree must still equal the archive after the import check (it runs the target module)
            # and after the control run, BEFORE the first mutant is planted
            stop_if_dirty(a, root, "the import check")
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
                    unlink_state(control)
                last, bfailed = summary(out)
                bad_reason = (
                    "it timed out"
                    if rc is None
                    else f"it exited with {rc}, not 0"
                    if rc != 0
                    else f"no test passed (summary line: {last!r}): everything was skipped or nothing was selected"
                    if passed_total(out) == 0
                    else None
                )
                write_out(
                    rawdir / f"{a.prefix}-baseline.txt",
                    f"UNMUTATED BASELINE\nbase commit: {a.sha_full}{' (given as ' + a.sha + ')' if a.sha != a.sha_full else ''} (+ the patch under test)   root: {a.root}\ncommand: {' '.join(cmd)}\nenvironment: {', '.join(sorted(test_env(a.pythonpath)))} only\nimport check: {a.imports}\nrc: {rc}\ntest group after the leader ended: {sweep}\nsummary: {last}\nbaseline usable: {'NO: ' + bad_reason if bad_reason else 'yes (exit 0, at least one test passed)'}\n\n{out}",
                )
                print("baseline", rc, last)
                if (
                    bad_reason
                ):  # review r5 M1: a failing baseline would make every mutant look KILLED
                    raise Refused(
                        f"the baseline (unmutated tree, --control) is not usable: {bad_reason}; no mutant was planted; "
                        f"see {a.prefix}-baseline.txt"
                    )
                a.baseline_failed = bfailed
                a.baseline_note = f"rc 0, {passed_total(out)} passed (see {a.prefix}-baseline.txt)"
                stop_if_dirty(a, root, "the control run")
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
            line, complete = summarize(results, len(ms), a.control)
            print(line, flush=True)
            write_out(rawdir / f"{a.prefix}-summary.txt", line + "\n")
            # proof the scratch tree is unchanged: compare with a FRESH archive extract
            fresh = tmpref / "fresh"
            fresh.mkdir()
            build_reference(a.repo, a.sha_full, a.patch, fresh)
            bad = tree_check(a, root, fresh, marker) or dirty
            print("tree diff:", len(bad), "difference(s)")
            if bad:
                print("TREE NOT CLEAN after the loop:", bad[:5], file=sys.stderr)
                leave(EXIT_TREE_NOT_CLEAN)
            if not complete:
                print(
                    f"INCOMPLETE: not every mutant has a clean KILLED or SURVIVED verdict (exit {EXIT_INCOMPLETE}); "
                    f"see the SUMMARY line and the raw files",
                    file=sys.stderr,
                )
                leave(EXIT_INCOMPLETE)
            SIG.exiting = True  # exit 0 is decided: a late signal (while the folders are removed) cannot change it (r7 N3)
    except Refused as e:
        SIG.exiting = True
        if may_be_planted(a.restore, root, marker, e):
            print(
                f"RESTORE FAILED: {e}; the mutant may still be planted; marker and backup kept "
                f"(run --restore again when the cause is fixed)",
                file=sys.stderr,
            )
            sys.exit(EXIT_RESTORE_FAILED)
        print("REFUSED:", e, file=sys.stderr)
        if a.restore and not isinstance(e, NoMarker):
            if a.sha is None:
                print(
                    "exit 2 does NOT mean nothing is planted: nothing was written and the file under test was not checked; "
                    "`--restore --sha COMMIT [--repo R]` compares the files with git",
                    file=sys.stderr,
                )
            else:
                print(
                    "exit 2 does NOT mean nothing is planted anywhere: nothing was written; the files under --root were "
                    "compared with the git archive of --sha (see above); a folder the marker may name is not looked at",
                    file=sys.stderr,
                )
        sys.exit(EXIT_REFUSED)
    except KeyboardInterrupt as e:
        SIG.exiting = True
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
    except (
        Exception
    ) as e:  # review r6 nit 5: a bug here must not end in Python's own exit 1 with a bare traceback
        SIG.exiting = True
        traceback.print_exc(limit=-6)  # the last frames only: a recursion error has thousands
        state = (
            f"a marker exists ({marker}): a mutant may be planted, run --restore"
            if os.path.lexists(marker)
            else "no marker: nothing is planted by this run"
        )
        print(f"INTERNAL ERROR ({type(e).__name__}: {str(e)[:300]}); {state}", file=sys.stderr)
        raise SystemExit(
            EXIT_RESTORE_FAILED if may_be_planted(a.restore, root, marker, e) else EXIT_REFUSED
        ) from e
    finally:
        if tmpref is not None:
            shutil.rmtree(tmpref, ignore_errors=True)


if __name__ == "__main__":
    main()
