"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` takes ONE snapshot of ``root/src`` (and the listed test files and fixtures) when it starts (an edit of ``root`` during the run never leaks into a later mutant) and copies it to a temp dir for EACH mutant; the pytest child sees only the environment variables in ``CHILD_ENV`` plus the names given in ``pass_env`` (no other DSN, token or secret of the caller), replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

This is a developer tool, not a runtime module: it lives in ``tools/`` (NOT in the wheel, not under ``src``). A repository that wants
it copies ``tools/__init__.py`` and ``tools/mutation_runner.py`` byte for byte (the files and their sha256 values are listed in
``tests/fixtures/mutation_manifest.json``); the tool imports only ``hadavin_sdk.testing.mutation``. It runs a subprocess on caller-chosen trees, so the mutant file is found by LISTING the
tree (``_locate``: the caller's string is compared with the listed names and never joined to a path), every other path is checked to
stay inside its tree (``_inside``: a ``..`` part or an absolute path is a ``ValueError``), a path that starts with ``-`` or ``@`` is refused
everywhere (``_plain_operand``: pytest would read it as an option or as an argument file, also after ``--``; ``./name`` is the way to write it),
a relative symlink of the snapshot that points outside the tree is refused (``_refuse_links_out``), a Windows junction (a folder link that ``shutil.copytree`` follows and copies as a real folder)
in ``src`` or in a fixture folder, or one of those folders itself or a part of its path, is refused before the copy (``_refuse_junctions``; ``os.path.isjunction``, Python 3.12 and later, where it is always False off Windows), and every pytest run has a timeout, and a timeout kills the whole process tree of the run.

The limit on names: a path may not contain ':' (a Windows drive or an NTFS stream name), so a file or folder whose name holds a colon cannot be named to this tool at all, on any system.

Limits, stated plainly. The tree kill reaches the processes that stay in the run's process group (POSIX) or the parent chain
(Windows ``taskkill /T``). A test or mutant that starts a process in a NEW session (``setsid``, ``start_new_session=True``) or, on
Windows, a process whose parent has already ended, escapes it. The mutant runner does not use a Windows Job Object (one would
reach those processes). After a normal exit the group is killed once more, so a leftover background process of a finished run
does not outlive it (POSIX only; on Windows nothing is killed after a normal exit: the parent is gone, ``taskkill /T`` cannot
find the children, and its pid may already belong to an unrelated process).

A SIGTERM or SIGHUP sent to the process that runs ``run_mutants`` (POSIX, main thread; a signal that was ignored on entry stays
ignored: SIGHUP under ``nohup``, or a SIGTERM that the parent set to ignore) is turned into ``SystemExit(128 + signal number)`` for
the length of the call, so the same cleanup as for Ctrl-C runs: the pytest tree is killed and the temp folders are removed. The old
handlers are restored afterwards. While the cleanup runs (the tree kill, the removal of the temp folders) and while the child is
being started, a termination signal is remembered and raised when that step is done, and once one signal has ended the run a further
one is remembered and dropped, so a second signal cannot cut the cleanup short. What stays open: a signal in the few bytecodes
between the handler and the cleanup's first line is held only by the "one signal already ended the run" rule, and SIGKILL cannot be
caught, and then the temp folders (``mutants_*`` and ``mutant_ini_*`` in the temp directory) stay.

On POSIX the run's process group is killed while its leader has ended but is NOT yet reaped (``os.waitid`` with ``WNOWAIT``), so the
group id cannot belong to an unrelated process by then. Where ``os.waitid`` does not exist (macOS) the leader is reaped by ``wait``
first and the group kill after a normal exit has the old, tiny pid-reuse risk.

Two more limits of the "reaped by someone else" case (SIGCHLD ignored, or a stray ``wait``). (a) Where ``os.waitid`` does not exist
(macOS) the run is waited for with ``proc.wait``, which cannot tell a reaped child from one that exited with status 0, so such a child
can still read as exit code 0 there: the ``REAPED_ELSEWHERE`` result exists on platforms with ``os.waitid`` only. (b) On the reaped-leader
path the group is NOT killed (its leader's pid may belong to another process by now), so descendants the child left behind are not killed.

pytest runs with ``--noconftest`` and with an empty ini file on purpose (a planted file in a parent folder is never read), so a
``pyproject.toml`` / ``pytest.ini`` is never read and, by default, no ``conftest.py`` is loaded. Three opt-in keywords of ``run_mutants``
(all off by default) cover tests that need more:

- ``conftest="tests/conftest.py"``: a file of the tree (copied like a test file) that every pytest run loads as a plugin (``-p``), named
  by a path of plain ASCII identifier parts that ends in ``.py`` and is either called ``conftest.py`` or lies in a folder called ``tests``
  (any other tree file, such as ``src/pk/core.py``, is refused). It replaces ``--noconftest`` for that one file only; no other conftest is read.
- ``pass_env=("HADAVIN_TEST_PG_DSN",)``: names of caller environment variables the pytest child also sees (baseline and mutants). Only
  names in ``PASS_ENV_ALLOWED`` are accepted (``ValueError`` for any other name, before anything runs): a token or any other secret of the
  caller still never reaches the child. A name that is not set in the caller is simply not passed. To allow one more name, add it to
  ``PASS_ENV_ALLOWED``, re-copy the file and update its pin (see the CHANGELOG); do that only for the ADDRESS of a throwaway test resource
  that a demo's tests need (a second database, for example), never for a token or a key.
  Masking: the value of a passed name (and the password inside it: the one of a URL, the one after ``password=``, ``passwd=`` or ``pwd=`` in a
  key=value text or a URL query, a quoted one included; each also percent-decoded, a backslash escape of libpq (``password='it\\'s'``, ``password=ab\\ cd``) read both ways, a URL password with an unencoded ``/``, ``?``, ``#`` or ``@`` read by trying every ``@`` as the end of the login, and each also as ``repr``, ``unicode_escape``, JSON (with and without ``\\u`` escapes) and the ``repr`` of its UTF-8 bytes print it, with each quote mark escaped or not (a ``repr`` of a larger text picks its quote from the whole text), so a backslash, a quote or a non-ASCII letter is covered) is replaced by ``[REDACTED]`` in ``first_lines``, in the failing test id of a row,
  in the ``COLLECTION ERROR``, ``FIXTURE ERROR`` and ``SKIPPED TESTS`` messages and in the baseline skip message. Checked with a real run: pytest
  shortens a long text in the first ``E`` line of a comparison to about its first 12 and last 13 characters around ``...``. Observed with
  pytest 9.2.0 (one 69-character value): the text is still shortened with ``-q``, with ``-q -vv`` and by default; it is printed in full only with
  ``-vv`` without ``-q`` and with ``-o verbosity_assertions=2``. The runner keeps ``-q`` and adds no such option, so the ``first_lines`` of every
  caller stay as they were,
  so every start of a secret that ends right before ``...`` and every end that starts right after ``...`` of ``FRAGMENT_MIN`` characters or more is masked too (all pieces are found in the original text and cut out at once; a text with more than ``MAX_FRAGMENT_HITS`` ``...`` or more than ``MAX_MATCHES`` matches of the secrets is replaced as a whole).
  What stays open, stated plainly: a test that prints a changed form of the value (only the host, only the user name, a re-encoded copy, a
  piece cut out of the middle, a fragment shorter than ``FRAGMENT_MIN`` characters, a head or tail piece that does not stand next to a plain-ASCII ``...`` (pprint line wrapping, a Unicode ellipsis), another encoding such as base64, hex or HTML escapes) is not masked; neither is a password that holds a quote, a ``;`` or an ``&`` and is written without quotes (only the part before that character is read as the password; the whole value is still masked; a quoted password with a backslash escape is read as libpq reads it, anything else odd is masked only inside the whole value) nor a password word glued to a letter or digit in front (``dbpassword=``); a password that has no ``password=`` word
  in front of it and is not the password of a URL is masked only as part of the whole value; and text of a failure that the runner never
  reads (the child's own console output is discarded) cannot leak through it.
  SAFETY: the address must point at a THROWAWAY database, and its login must be able to touch only that database (never a shared or
  production one): every mutant run executes the tests against it, and a mutant can make those tests write, drop or fill tables with
  anything. Two runs at once that share one database collide (the same tables and rows), so give each parallel run its own database.
  The runner checks one thing in code: after EVERY mutant run it runs the unmutated copy again on that same database (the canary run), and
  when that no longer passes it stops with ``RuntimeError`` naming the mutant, because what the mutant left behind would make the verdicts
  of the later mutants unreliable (a false kill). The cost is one extra pytest run (and one extra copy of the tree) per mutant while a ``pass_env`` name is set; the second copy is kept on purpose: the canary run leaves bytecode that could hide the next mutation. The canary proves only that the full unmutated tests still pass; it does not prove the database is clean, and under ``forbid_skips`` a canary run with a skipped test is refused too. A failed canary, a skipped one included, raises ``CanaryFailed`` (a ``RuntimeError``; its ``rows`` hold the rows judged so far); the message says "timed out" or "reaped" instead of an exit code when the run did. A second runner that uses the same temp folder (in practice the same machine and the same account, or the same ``TMPDIR``) with the same passed value is refused by an exclusive lock file there, named by the first 16 hex digits of a SHA-256 of the value (a hash is not the value, but the file name is readable by other users of that folder and a guessable value could be tested against it: use a database address with a random password); a runner with another temp folder or on another machine is not seen (give each run a database of its own). The lock file is opened without following a symbolic link (``O_NOFOLLOW`` where the system has it; a planted link is refused with a clear message), with mode 0600, and is never deleted: one empty file per distinct value stays in the temp folder (delete it by hand only when no run is going: a deleted file that a run still holds lets a second run lock a new file of the same name). A lock file that cannot be opened or locked for another reason (no permission, no lock space) is refused with its own message.
- ``forbid_skips=True``: a run in which any selected test is skipped (or an expected failure) proves nothing, so it is an ERROR row
  ``SKIPPED TESTS`` (never a kill), and an unmutated baseline with a skipped test raises ``RuntimeError``. This closes the false kill where
  a mutant "dies" because the tests could not run (for example no database was reachable). A mutant run with no JUnit file or an empty one
  is the ERROR row ``JUNIT MISSING`` under this keyword.

Always on (no keyword), two changes of result and one new label: (1) a run whose FIRST failing test case failed in a fixture, at setup or at teardown
(``testing.mutation.fixture_errors``), is the ERROR row ``FIXTURE ERROR`` and never a kill; before, such a run was a kill when the fixture
failed with an ``AssertionError`` and a crash otherwise. A test whose body failed and whose teardown failed afterwards is judged by the failure
(the test ran as written). (2) ``testing.mutation.judge`` returns ``ERROR`` when the run failed (exit 1) and no failing test id is known (an empty or
unreadable JUnit file), where it used to return ``CRASH`` or ``KILLED``; (3) a run whose FIRST failing case is a test file that could not be imported or collected (pytest word: ``collection failure``; an ``assert`` at import time included) is the ERROR row ``COLLECTION ERROR`` with pytest's message. This is only a new label: pytest exits 2 for it and the judge already returned ERROR for every exit code other than 1, so the old row was an ERROR row with the module name as its test id (observed: the unchanged runner of ``main``, commit 2a8c2aa, ``tools/mutation_runner.py`` sha256 489517fb224f0598e14244ded1b37fe2a68be69e2396e56e450be0d8b1c0a1a7, on a tree whose test file starts with ``assert go(True) is True, 'at import'``, gave ``('flip', ERROR, '::tests.test_core', False)`` with the first line ``E   AssertionError: at import`` and pytest exit codes 0 for the baseline and 2 for the mutant run), never a kill. A mutant counts as killed only when a test ran as written and failed: that part of the rule is not changed by item 3.

Result rows. A row is ``(name, verdict, test id, good)``. The test id column holds the failing test id, or one of these texts for an ERROR row
that has no verdict from the judge: ``SETUP FAILED: <error class>``, ``SNIPPET NOT FOUND``, ``TIMEOUT``, ``REAPED ELSEWHERE``, ``JUNIT REFUSED``,
``JUNIT MISSING`` (``forbid_skips``), ``COLLECTION ERROR``, ``FIXTURE ERROR``, ``SKIPPED TESTS`` (``forbid_skips``) and ``NO FAILING TEST NAMED`` (the run failed, the JUnit file names no failing test). ``first_lines`` holds the first ``E`` line (masked)
of the rows that have one, and for ``COLLECTION ERROR``, ``FIXTURE ERROR`` and ``SKIPPED TESTS`` the masked message that says why.

Dev-tool constants: ``MAX_JUNIT_CHARS`` (in ``testing.mutation``), ``PASS_ENV_ALLOWED``, ``MASK``, ``FRAGMENT_MIN``, ``MAX_FRAGMENT_HITS``, ``MAX_MATCHES``, ``NO_TEST_NAMED``, ``SETUP_TRIES``, ``SETUP_WAIT``, ``WAIT_POLL``, ``TREE_KILL_TIMEOUT``,
``TIMED_OUT``, ``REAPED_ELSEWHERE``, ``CHILD_ENV``, ``CHILD_FIXED_ENV``, ``JUNIT_REFUSED`` and the default run timeout (``DEFAULT_TIMEOUT``, 900.0 seconds) are module constants here and NOT in ``defaults.py``:
the no-hardcoding rule is about product behaviour (names, regions, prices, thresholds a deployment tunes), and this is a developer tool
that ships in no wheel, has no config surface and is copied byte for byte into demos. A caller changes the timeouts by argument.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import itertools
import json
import keyword
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import unquote, urlsplit

from hadavin_sdk.testing.mutation import (
    MAX_JUNIT_CHARS,
    JunitReport,
    Verdict,
    judge,
    read_junit,
    skipped_tests,
)


@dataclass(frozen=True)
class Mutant:
    name: str
    file: str  # relative to the copied root
    old: str
    new: str
    expect: str  # >= 4 characters: a distinctive fragment of the INTENDED failing assertion line (its message), never of the killer's name
    allow_crash: bool = (
        False  # the intended reaction is a crash (an exception other than an assertion)
    )
    crash_type: str = ""  # REQUIRED with allow_crash: the exception CLASS NAME that must LEAD the first ``E`` line (parsed, not a substring match), or the mutant is not good
    crash_markers: tuple[
        str, ...
    ] = ()  # passed to ``judge``: a first line holding one of these is a CRASH even if it is an assertion
    test_file: str = ""  # one of the `tests` files: run ONLY this file for the mutant (its killer is not in the first file)
    pinned: str = ""  # the test id (as ``first_failure_junit`` writes it, ``tests/test_x::test_y``) that must be the one failing; another failing test is OTHER_TEST
    only_test: str = ""  # a test function name: run ONLY that test (of the first test file, or of `test_file`), so the killer never depends on test order or a fuzz seed

    def __post_init__(self) -> None:
        _relative(self.file)
        if len(self.expect) < 4:
            raise ValueError("expect must be at least 4 characters")
        if self.allow_crash and not self.crash_type.isidentifier():
            raise ValueError(
                "allow_crash needs crash_type: the exception class name the kill must show"
            )
        if self.crash_type and not self.allow_crash:
            raise ValueError("crash_type without allow_crash")
        if self.only_test and not self.only_test.isidentifier():
            raise ValueError("only_test must be a test function name")
        if self.test_file:
            _relative(self.test_file)


def _plain_operand(arg: str) -> str:
    """``arg`` may reach the pytest command line as an operand: it must not start with ``-`` (pytest reads it as an option; the ``--``
    marker is not a safe fence, on some Python 3.12 builds argparse still takes the next word after it as an option) or with ``@``
    (pytest reads ``@name`` as a file of further arguments, also after ``--``). A caller who means such a file name writes ``./name``."""
    if arg.startswith(("-", "@")):
        raise ValueError(f"a path may not start with '-' or '@' (write ./name): {arg!r}")
    return arg


def _relative(rel: str) -> str:
    """``rel`` must be a relative path with no ``..`` part (checked as a POSIX and as a Windows path) and must not start with ``-`` or ``@``."""
    if not isinstance(rel, str) or not rel:
        raise ValueError("a path is a non-empty string")
    _plain_operand(rel)
    # a Windows drive, or an NTFS alternate data stream name (``file.py:stream``): neither is a plain relative path
    if ":" in rel:
        raise ValueError(f"a path may not contain ':': {rel!r}")
    for pure in (PurePosixPath(rel), PureWindowsPath(rel)):
        if pure.is_absolute() or pure.anchor or ".." in pure.parts:
            raise ValueError(f"path escapes its tree: {rel!r}")
    return rel


def _inside(base: Path, rel: str) -> Path:
    """``base / rel``, resolved, and proven to lie inside ``base`` (symlinks included)."""
    root = base.resolve()
    path = (root / _relative(rel)).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"path escapes its tree: {rel!r}")
    return path


_IS_WINDOWS = (
    os.name == "nt"
)  # one place to ask (tests set it to check the Windows branch of the tree kill on any system)
DEFAULT_TIMEOUT = 900.0  # seconds one pytest run may take (a 15-minute ceiling for the slowest killer); override by argument
REAPED_ELSEWHERE = -1001  # returned instead of an exit code when someone else reaped the child first (SIGCHLD ignored, a stray ``wait``): its exit status is lost and ``Popen`` would report 0, which the judge must never read as a pass or a fail
TIMED_OUT = -1000  # returned instead of an exit code when the run exceeded its timeout; no process exit status is this low (POSIX -9 is a SIGKILL, for example the OOM killer, and is judged as an error)
CHILD_ENV = (
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
    "LANG", "LC_ALL", "PYTHONHASHSEED", "PYTHONUTF8", "PYTHONIOENCODING",
)  # fmt: skip  # the only variables a mutant run inherits
# the ONLY names ``pass_env`` may add to the child's environment: the address of a throwaway test resource, never a token or a key.
# To widen it: add the name here, re-copy this file and update its pin (CHANGELOG list and tests/fixtures/mutation_manifest.json); the
# trigger is a demo's tests needing the address of another throwaway test resource, and each name gets the same review.
PASS_ENV_ALLOWED = ("HADAVIN_TEST_PG_DSN",)
MASK = "[REDACTED]"
NO_TEST_NAMED = "NO FAILING TEST NAMED"  # the id column of an ERROR row for a failed run whose JUnit file names no failing test
FRAGMENT_MIN = 6  # pytest shortens a long text in an assertion line to ``head...tail``: a head or tail fragment of a secret this long (or longer) next to ``...`` is masked
MAX_MATCHES = 100_000  # more matches of the secrets than this in one text is no honest line either: the whole text is replaced (a 1-character secret on a huge line stays fast)
MAX_FRAGMENT_HITS = 10_000  # more ``...`` than this in one text is no honest line: the whole text is replaced, and the scan stays short
CHILD_FIXED_ENV = {
    "PYTHONNOUSERSITE": "1"
}  # set, not inherited: the child never imports from the caller's user site-packages
SETUP_TRIES = 5  # attempts to clear and rebuild the temp copy (a Windows file lock may hold a file for a moment)
SETUP_WAIT = 0.5  # seconds between those attempts
# a refused JUnit file (DOCTYPE, ENTITY, too large) or a truncated one (ET.ParseError is a SyntaxError) is THIS mutant's ERROR, not the end of the run
JUNIT_REFUSED = (ValueError, SyntaxError)


def _taskkill() -> str:
    """taskkill.exe by its full path under %SystemRoot%\\System32, not by a PATH search (a planted taskkill in a work folder is not run)."""
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32" / "taskkill.exe")


WAIT_POLL = (
    0.05  # seconds between two looks at a running child (POSIX ``os.waitid`` has no timeout)
)
TREE_KILL_TIMEOUT = 60.0  # seconds ``taskkill`` may take before the child itself is killed anyway


def _leading_class(first: str) -> str:
    """The exception class name that starts a pytest ``E`` line (``E   demo.fakes.AuditWriteError: text`` gives ``AuditWriteError``;
    a name that only CONTAINS the declared one, or that appears later in the text, does not match it). The ``E`` marker is a letter
    followed by spaces: a class such as ``EOFError`` keeps its first letter, and a line with no marker (a message fallback) is read as is."""
    head = re.sub(r"^E\s+", "", first.strip()).split(":", 1)[0].strip()
    return head.rsplit(".", 1)[-1]


def _locate(base: Path, rel: str) -> Path:
    """The file ``rel`` names inside ``base``, found by listing the tree (``os.walk``; a match is accepted only if its real path stays inside the tree): the caller's string is only
    COMPARED as data with the listed relative names and is never joined to a path, so it cannot steer a read or a write out of the tree."""
    want = _relative(rel).replace("\\", "/")
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            full = os.path.join(dirpath, name)
            if os.path.relpath(full, base).replace(os.sep, "/") != want:
                continue
            real_base, real_full = os.path.realpath(base), os.path.realpath(full)
            # a link (or junction) out of the tree does not count
            if os.path.commonpath([real_base, real_full]) == real_base:
                return Path(full)
    raise ValueError(f"no such file inside the tree: {rel!r}")


class _ReapedElsewhere(Exception):
    """The child ended but another waiter reaped it, so its exit status is unknown (``Popen`` itself would call it 0)."""


def _plugin_module(conftest: str) -> str:
    """The module name pytest loads (``-p``) for the tree file ``conftest``: ``tests/conftest.py`` gives ``tests.conftest``. Every part must be a
    plain ASCII identifier that is not a Python keyword (``class.py`` and a non-ASCII look-alike are refused) and the file must end in ``.py``, so the name can carry no option, no ``no:`` prefix and no path trick."""
    _relative(conftest)
    parts = conftest.replace("\\", "/").split("/")
    names = (*parts[:-1], parts[-1][:-3])
    if not parts[-1].endswith(".py") or not all(
        p.isascii() and p.isidentifier() and not keyword.iskeyword(p) for p in names
    ):
        raise ValueError(
            f"conftest must be a .py file whose path parts are plain ASCII names that are not Python keywords: {conftest!r}"
        )
    if parts[-1] != "conftest.py" and "tests" not in parts[:-1]:
        raise ValueError(
            f"conftest must be called conftest.py or lie in a folder called tests: {conftest!r}"
        )
    return ".".join([*parts[:-1], parts[-1][:-3]])


def _checked_env_names(names: Iterable[str]) -> tuple[str, ...]:
    """``names`` if every one is in ``PASS_ENV_ALLOWED``, else ``ValueError`` (a bare string is a ``TypeError``, not read letter by letter)."""
    if isinstance(names, str):
        raise TypeError("pass_env is a sequence of names, not one string")
    chosen = tuple(names)
    for name in chosen:
        if name not in PASS_ENV_ALLOWED:
            raise ValueError(f"pass_env may name only {PASS_ENV_ALLOWED}: {name!r} is refused")
    return chosen


_PASSWORD_WORD = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:password|passwd|pwd)\s*=\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|((?:[^\s&;'\"\\]|\\.)+))"
)  # ``password=...`` of a key=value DSN or a URL query; a quoted value may hold spaces, and a backslash escapes the next character (libpq)
_BACKSLASH_ESCAPE = re.compile(r"\\(.)", re.DOTALL)


def _written_forms(text: str) -> set[str]:
    """``text`` and the ways a test or pytest may print it: as ``repr`` shows it inside quotes, as ``unicode_escape`` writes it, as JSON writes it
    (with and without ``\\u`` escapes for non-ASCII letters) and as the ``repr`` of its UTF-8 bytes (a backslash, a quote or a non-ASCII letter
    shows up escaped in an assertion line or a log line). Empty forms are dropped."""
    forms = {
        text,
        text.encode("unicode_escape").decode("ascii"),
        json.dumps(text)[1:-1],
        json.dumps(text, ensure_ascii=False)[1:-1],
        repr(text.encode("utf-8", "backslashreplace"))[2:-1],
    }
    # a Python ``repr`` of a LARGER text picks its quote from the whole text, so the quote marks of this value come out escaped or not
    # whatever it holds itself: every mix of the two (a quote mark written with a backslash, or as it is)
    plain = "".join(c if c in "'\"" else repr(c)[1:-1] for c in text)
    for single in (False, True):
        for double in (False, True):
            swap = {"'": "\\'" if single else "'", '"': '\\"' if double else '"'}
            forms.add("".join(swap.get(c, c) for c in plain))
    return {f for f in forms if f}


def _url_passwords(value: str) -> list[str]:
    """The password of a URL as ``urlsplit`` reads it, and every text between the first ``:`` after ``://`` and an ``@`` after it: a password that
    holds an unencoded ``/``, ``?``, ``#`` or ``@`` is not read right by ``urlsplit`` (it takes the first of them as the end of the address), so
    every ``@`` is tried as the end of the login (more than needed is masked, never less)."""
    found: list[str] = []
    with contextlib.suppress(ValueError):  # not URL-shaped: only the key=value scan applies
        found.append(urlsplit(value).password or "")
    if "://" in value:
        rest = value.split("://", 1)[1]
        colon = rest.find(":")
        at = rest.find("@", colon + 1) if colon != -1 else -1
        while at != -1:
            found.append(rest[colon + 1 : at])
            at = rest.find("@", at + 1)
    return found


def _secret_values(names: Iterable[str]) -> tuple[str, ...]:
    """The values of the passed environment variables, and the password inside them (the one of a URL, the one after ``password=`` in a
    key=value text or a URL query; each as written, percent-decoded, and as ``repr`` / ``unicode_escape`` print it), longest first: text that may show them is run through ``_masked``."""
    found: set[str] = set()
    for name in names:
        value = os.environ.get(name, "")
        if not value:
            continue
        found.update(_written_forms(value))
        passwords = [
            next(g for g in m.groups() if g is not None) for m in _PASSWORD_WORD.finditer(value)
        ]
        passwords += [
            _BACKSLASH_ESCAPE.sub(r"\1", word) for word in passwords
        ]  # libpq: a backslash escapes the next character
        passwords += _url_passwords(value)
        for password in passwords:
            if password:
                for form in (password, unquote(password)):
                    found.update(_written_forms(form))
    return tuple(sorted(found, key=len, reverse=True))


class _TooManyHits(Exception):
    """A line holds more ``...`` than ``MAX_FRAGMENT_HITS`` (or more matches of the secrets than ``MAX_MATCHES``): no honest line does, so
    ``_masked`` replaces the whole line. ``args`` is ``(limit, what was counted)``."""


def _fragment_spans(text: str, secret: str) -> list[tuple[int, int]]:
    """Spans of ``text`` that show a shortened ``secret``: pytest cuts a long text in an assertion line to ``head...tail`` (about 12 characters
    each side, checked with a real run), so the longest start of the secret that ends right before a ``...`` and the longest end of it that
    starts right after one are returned (each ``FRAGMENT_MIN`` characters or longer, and shorter than the secret). Each ``...`` costs at most a
    scan of ``len(secret)`` characters; more than ``MAX_FRAGMENT_HITS`` of them is ``_TooManyHits``."""
    spans: list[tuple[int, int]] = []
    top = len(secret) - 1
    head, tail = secret[:FRAGMENT_MIN], secret[-FRAGMENT_MIN:]
    hits = list(itertools.islice(re.finditer(r"\.\.\.", text), MAX_FRAGMENT_HITS + 1))
    if len(hits) > MAX_FRAGMENT_HITS:
        raise _TooManyHits(MAX_FRAGMENT_HITS, "'...'")
    for hit in hits:
        start, end = hit.start(), hit.end()
        i = text.find(head, max(0, start - top), start)  # the leftmost start gives the longest head
        while i != -1:
            if text[i:start] == secret[: start - i]:
                spans.append((i, start))
                break
            i = text.find(head, i + 1, start)
        stop = min(len(text), end + top)
        j = text.rfind(tail, end, stop)  # the rightmost end gives the longest tail
        while j != -1:
            k = j + FRAGMENT_MIN - end
            if text[end : j + FRAGMENT_MIN] == secret[-k:]:
                spans.append((end, end + k))
                break
            j = text.rfind(tail, end, j + FRAGMENT_MIN - 1)
    return spans


def _masked(text: str, secrets: Sequence[str]) -> str:
    """``text`` with every secret value replaced by a marker (pass_env values must never reach ``first_lines``, a result row or an error message).
    A secret that pytest shortened to ``head...tail`` is masked by its fragments too (see ``_fragment_spans``). Every span is found in the
    ORIGINAL text and then all are cut out at once, so a short secret that sits inside a longer one cannot break the match of the longer one.
    More than ``MAX_MATCHES`` matches (a 1-character secret on a huge line) or ``MAX_FRAGMENT_HITS`` ``...`` replace the whole text."""
    chosen = tuple(v for v in secrets if v)
    if not chosen:
        return text
    hit = bytearray(len(text))
    matches = 0
    try:
        for value in chosen:
            at = text.find(value)
            while at != -1:
                matches += 1
                if matches > MAX_MATCHES:
                    raise _TooManyHits(MAX_MATCHES, "matches of a secret")
                hit[at : at + len(value)] = b"\x01" * len(value)
                at = text.find(value, at + 1)
            if len(value) > FRAGMENT_MIN:
                for lo, hi in _fragment_spans(text, value):
                    hit[lo:hi] = b"\x01" * (hi - lo)
    except _TooManyHits as many:
        limit, what = many.args
        return f"{MASK} (line with more than {limit} {what} replaced: it cannot be checked for pieces of a value)"
    out: list[str] = []
    for ch, bad in zip(text, hit, strict=True):
        if not bad:
            out.append(ch)
        elif not out or out[-1] != MASK:
            out.append(MASK)
    return "".join(out)


class CanaryFailed(RuntimeError):
    """The unmutated copy no longer passes after a mutant run (shared database). ``rows`` holds the rows of the mutants judged so far."""

    rows: tuple[tuple[str, Verdict, str, bool], ...] = ()


_LOCK_HELD = (
    errno.EAGAIN,
    errno.EACCES,
    errno.EDEADLK,
)  # what a non-blocking lock reports when another holder has it (EWOULDBLOCK equals EAGAIN)


_RUN_END_IN_WORDS = {
    TIMED_OUT: "the run timed out",
    REAPED_ELSEWHERE: "the run was reaped by another waiter, its exit status is lost",
}


def _run_end(rc: int) -> str:
    """How a failed canary run ended, in words: the two internal codes (``TIMED_OUT``, ``REAPED_ELSEWHERE``) are not exit codes."""
    return _RUN_END_IN_WORDS.get(rc, f"exit code {rc}")


def _lock_dir() -> Path:
    return Path(tempfile.gettempdir())


def _check_lock_file(fd: int) -> None:
    """Refuse (``RuntimeError``) a lock file that is not a regular file of the current user with a mode no wider than 0600 (not on Windows, whose
    mode bits mean nothing): a file left by an older version or made by hand with wider rights could be written by another user of the temp folder."""
    if _IS_WINDOWS:
        return
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) & 0o177
    ):
        raise RuntimeError(
            "the lock file of this run is not a regular file of this user with mode 0600 or narrower (delete it by hand when no run is going), so the run cannot be proven alone on its database"
        )


@contextlib.contextmanager
def _one_run_per_database(values: Sequence[str]) -> Iterator[None]:
    """Hold an exclusive lock named by a hash of the passed values (never the values) in the temp folder for the whole run: a second runner that
    uses the same temp folder (same machine and account, or the same ``TMPDIR``) with the same passed value is refused (``RuntimeError``) instead
    of sharing the database and its tables. It does not see a runner with another temp folder or on another machine; that stays the caller's
    job (a database of its own per run). The file is opened without following a symbolic link and with mode 0600, and is never deleted (one empty file per value; it stays in the temp folder, and a left-behind file of another user, a wider mode or another kind than a regular file is refused with a clear message, to be deleted by hand when no run is going). The file name holds the first 16 hex digits of a SHA-256 of the values: not the values, but readable by
    other users of the temp folder. A lock file that cannot be opened (another user's file) or locked for a reason other than "held by another
    run" is a ``RuntimeError`` with its own message."""
    digest = hashlib.sha256("\0".join(sorted(values)).encode()).hexdigest()[:16]
    path = _lock_dir() / f"hadavin_mutation_{digest}.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            handle = os.fdopen(fd, "r+b")
        except OSError:
            os.close(fd)  # no file object took the descriptor over
            raise
    except OSError as exc:
        raise RuntimeError(
            f"the lock file of this run could not be opened ({type(exc).__name__}): {'it is a symbolic link' if exc.errno == errno.ELOOP else 'it may belong to another user of the temp folder'}, so the run cannot be proven alone on its database"
        ) from None
    with handle:
        _check_lock_file(handle.fileno())
        try:
            if _IS_WINDOWS:
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined,unused-ignore]
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in _LOCK_HELD:
                raise RuntimeError(
                    "another mutation run that uses the same temp folder has the same passed database address: give each run a database of its own"
                ) from None
            raise RuntimeError(
                f"the lock file of this run could not be locked ({type(exc).__name__}, errno {exc.errno}), so the run cannot be proven alone on its database"
            ) from None
        yield  # the lock goes with the closed file


def _pytest(
    cwd: Path,
    tests: Sequence[str],
    junit: Path,
    timeout: float,
    *,
    plugin: str = "",
    env_names: Sequence[str] = (),
) -> int:
    # an ALLOWLIST, not os.environ: a mutant run must not see a database DSN, a token or any other secret of the caller; PYTHONPATH also holds the tree root (tests may import tools.*)
    for operand in tests:  # the one place the caller's strings reach the argv: refuse here too, not only where the paths are first checked
        _plain_operand(operand)
    env = {k: os.environ[k] for k in CHILD_ENV if k in os.environ}
    env.update({k: os.environ[k] for k in _checked_env_names(env_names) if k in os.environ})
    env.update(CHILD_FIXED_ENV)
    load = ["-p", _plugin_module(plugin)] if plugin else []
    env["PYTHONPATH"] = os.pathsep.join([str(cwd / "src"), str(cwd)])
    # an EMPTY ini file inside the copy is the config file and the copy is the rootdir: a planted pytest.ini, tox.ini, setup.cfg or
    # pyproject.toml in a parent folder (the shared temp folder, for one) is never picked up
    # the ini file lives in a private temp folder of its own, never in the caller's working folder
    ini_dir: Path | None = None
    proc: subprocess.Popen[bytes] | None = None
    try:
        with _signals_held():
            ini_dir = Path(tempfile.mkdtemp(prefix="mutant_ini_"))
        ini = ini_dir / "mutant_run.ini"
        ini.write_text("", encoding="utf-8")
        cmd = [
            sys.executable,
            *("-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", *load),
            *("-x", "-c", str(ini), f"--rootdir={cwd}", f"--junitxml={junit}", *tests),
        ]
        # own process group (POSIX session / Windows group): on a timeout the whole tree dies, not only pytest (a test may have started psql or a server)
        own = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            if _IS_WINDOWS
            else {"start_new_session": True}
        )
        # a termination signal during the start is held until ``proc`` is known, then raised inside this ``try``: the child is killed
        with _signals_held():
            # S603 stays a listed exception: the argument list holds the caller's test paths and the junit path, so ruff cannot see it as a literal. Fixed argv (our own interpreter), no shell, caller strings only as pytest operands that ``_plain_operand`` has checked
            proc = subprocess.Popen(  # noqa: S603
                cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **own  # type: ignore[call-overload]
            )  # fmt: skip
        try:
            _wait_unreaped(proc, timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            # a mutant that loops forever is reported, never allowed to hang the run
            return TIMED_OUT
        except _ReapedElsewhere:
            return REAPED_ELSEWHERE  # ``proc`` knows it has ended (poll), so there is no group to signal and nothing to kill
        # a normal exit can leave a background process of the run behind: on POSIX it is killed too. Not on Windows: the parent is
        # gone, taskkill /T finds no children, and the pid may already belong to an unrelated process
        if not _IS_WINDOWS:
            _kill_tree(proc)
        return proc.wait()
    except BaseException:  # Ctrl-C (KeyboardInterrupt) or any other exit while waiting: never leave a spinning mutant behind
        if proc is not None and proc.returncode is None:
            _kill_tree(proc)
        raise
    finally:
        with _signals_held():
            if ini_dir is not None:
                shutil.rmtree(ini_dir, ignore_errors=True)


def _wait_unreaped(proc: subprocess.Popen[bytes], timeout: float) -> None:
    """Return when ``proc`` has ended; raise ``subprocess.TimeoutExpired`` after ``timeout`` seconds. On POSIX the ended leader is NOT
    reaped (``os.waitid`` with ``WNOWAIT``, polled), so the later group kill cannot hit a reused pid; ``_kill_tree`` reaps it. If someone
    else reaped it first (SIGCHLD ignored) its exit status is gone: ``proc`` is told it has ended, and ``_ReapedElsewhere`` is raised.
    Windows,
    and a POSIX without ``os.waitid`` (macOS): ``proc.wait``, which reaps. Tests patch this function to steer the wait."""
    if _IS_WINDOWS or not hasattr(os, "waitid"):
        proc.wait(timeout=timeout)
        return
    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                return
        except ChildProcessError:  # someone else reaped it already (SIGCHLD ignored): let ``proc`` learn it, or ``_kill_tree`` would signal a reaped group
            proc.poll()  # sets returncode (0, a guess) so ``_kill_tree`` will not signal a reaped group
            raise _ReapedElsewhere from None
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        time.sleep(min(WAIT_POLL, left))


def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill ``proc`` and everything it started (POSIX: its process group; Windows: ``taskkill /T``). A failing tree kill (no ``taskkill``
    on the PATH, its own timeout, ``PermissionError`` from ``killpg``) never skips the kill of the child itself. The group is not
    killed when the leader was already reaped (its pid may be someone else's by now), except where ``os.waitid`` is missing. A
    termination signal during the kill is held until it is done."""
    with _signals_held():
        try:
            if _IS_WINDOWS:
                # S603 stays a listed exception: the pid is our own child's, but the list is not a literal to ruff. Fixed argv, no shell
                subprocess.run(  # noqa: S603
                    [_taskkill(), "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=TREE_KILL_TIMEOUT,
                )  # fmt: skip
            elif proc.returncode is None or not hasattr(os, "waitid"):
                os.killpg(proc.pid, signal.SIGKILL)
        # ProcessLookupError and PermissionError are OSErrors
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            proc.kill()  # the child itself, always
            proc.wait()


# the signals that end a run like Ctrl-C does (POSIX; SIGHUP does not exist on Windows)
_TERMINATING = ("SIGTERM", "SIGHUP")
# State of the termination handling. Only the main thread changes it (the handlers run there, and ``_signals_held`` does nothing in
# another thread): ``depth`` counts the steps that must not be cut short, ``pending`` is the first signal that arrived during one,
# ``ended`` says that a signal has already ended the run (every later one is remembered and dropped: the cleanup is under way),
# ``active`` says that a ``run_mutants`` call of this thread is under way (one at a time: the counters are shared, see ``run_mutants``).
_SIGNALS = {"depth": 0, "pending": 0, "ended": 0, "active": 0}


def _signals_active() -> bool:
    return not _IS_WINDOWS and threading.current_thread() is threading.main_thread()


@contextlib.contextmanager
def _signals_held() -> Iterator[None]:
    """POSIX main thread: a termination signal that arrives inside the block does not raise there; the first one is raised as
    ``SystemExit`` when the outermost block ends (unless a signal has already ended the run). Used around the start of the child, the
    tree kill and the removal of temp folders. Elsewhere it changes nothing."""
    if not _signals_active():
        yield
        return
    _SIGNALS["depth"] += 1
    try:
        yield
    finally:
        _SIGNALS["depth"] -= 1
        if _SIGNALS["depth"] == 0 and _SIGNALS["pending"]:
            number, _SIGNALS["pending"] = _SIGNALS["pending"], 0
            if not _SIGNALS["ended"]:
                _SIGNALS["ended"] = 1
                raise SystemExit(128 + number)


@contextlib.contextmanager
def _terminations_raise() -> Iterator[None]:
    """POSIX main thread: SIGTERM and SIGHUP raise ``SystemExit(128 + signal number)`` inside the block, so the cleanup in ``finally`` and in
    ``_pytest`` runs (a stopped runner would otherwise leave the pytest tree and the temp folders behind). The old handlers are restored;
    a signal that was ignored on entry (``nohup``) stays ignored. Elsewhere (Windows, another thread) it changes nothing."""
    if not _signals_active():
        yield
        return
    # refused BEFORE anything is changed: the counters of the outer call stay as they are
    if _SIGNALS["active"]:
        raise RuntimeError(
            "run_mutants is not re-entrant: a second call inside a running one is refused"
        )

    def stop(signum: int, _frame: object) -> None:
        if _SIGNALS["depth"] or _SIGNALS["ended"]:
            _SIGNALS["pending"] = _SIGNALS["pending"] or signum
            return
        _SIGNALS["ended"] = 1
        raise SystemExit(128 + signum)

    previous: dict[int, object] = {}
    _SIGNALS.update(depth=0, pending=0, ended=0, active=1)
    try:
        for name in _TERMINATING:
            sig = getattr(signal, name, None)
            if sig is None or signal.getsignal(sig) is signal.SIG_IGN:
                continue
            previous[sig] = signal.signal(sig, stop)
        yield
    finally:
        for sig, old in previous.items():
            signal.signal(sig, old if old is not None else signal.SIG_DFL)  # type: ignore[arg-type]
        _SIGNALS.update(depth=0, pending=0, ended=0, active=0)


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    only: Sequence[str] = (),
    timeout: float = DEFAULT_TIMEOUT,
    baseline_timeout: float | None = None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None = None,
    first_lines: dict[str, str] | None = None,
    conftest: str = "",
    pass_env: Sequence[str] = (),
    forbid_skips: bool = False,
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` if the unmutated copy fails or times out; a mutant whose temp copy cannot be built (after ``SETUP_TRIES`` tries) is ``(name, Verdict.ERROR, "SETUP FAILED: <error class>", False)``; a mutant run that exceeds
    ``timeout`` seconds is ``(name, Verdict.ERROR, "TIMEOUT", False)``. The unmutated baseline run gets ``baseline_timeout`` (default: ``timeout``; 0 is a real, immediate timeout and not "unset"),
    so a test can use a short mutant timeout without failing a slow baseline. ``on_result`` is called with each result as soon as that mutant
    finishes (stream it and a timeout of the whole run still leaves a kill list). Every ``tests`` and ``extra_dirs`` entry and every mutant file
    must name a file inside its tree (``ValueError``). ``first_lines``, if given, is emptied at the start and then filled with the first ``E`` line
    of each judged kill (mutant name -> line; diagnostics, and what ``crash_type`` is checked against): it belongs to this call, so two
    runs in two threads never share it. ``conftest``, ``pass_env`` and ``forbid_skips`` are opt-in (see the module docstring; by default no plugin, no environment name and no skip check
    are added; the always-on changes in the module docstring still apply): a plugin file of the tree, allowlisted environment names for the child, and "a skipped test is an
    error, not a kill". A bad value, or a ``conftest`` that is not a file of the tree, is a ``ValueError`` before any temp folder exists. A SIGTERM or SIGHUP during the call ends it like Ctrl-C (see the module docstring).
    NOT re-entrant: the signal state is one module-level record, so on POSIX in the main thread a ``run_mutants`` call made while another is
    running in the same thread (from ``on_result``, say) raises ``RuntimeError`` and leaves the outer call untouched. Calls in other threads do not
    share that state, and each is handled by its own thread (the signal handling is then off, as the module docstring says)."""
    with _terminations_raise():
        return _run_mutants(
            root, mutants, tests, extra_dirs, only, timeout, baseline_timeout, on_result,
            {} if first_lines is None else first_lines, conftest, pass_env, forbid_skips,
        )  # fmt: skip


def _refuse_links_out(base: Path) -> None:
    """Refuse a RELATIVE symlink of the snapshot whose target lies outside ``base`` (``ValueError``). The snapshot and every copy of it sit
    side by side in the shared temp folder, so such a link (``../../x`` out of ``src``) would resolve to a neighbour in that folder, not to
    what it meant in the caller's tree. An absolute link keeps its meaning in a copy and stays a link (it is the caller's explicit choice)."""
    real_base = os.path.realpath(base)
    for dirpath, dirs, files in os.walk(base):  # os.walk does not enter a linked folder
        for name in (*dirs, *files):
            link = os.path.join(dirpath, name)
            if not os.path.islink(link):
                continue
            target = os.readlink(link)
            if os.path.isabs(target):
                continue
            hop = os.path.normpath(os.path.join(os.path.realpath(dirpath), target))
            if os.path.commonpath([real_base, hop]) != real_base:
                raise ValueError(
                    f"a relative link points outside the tree: {os.path.relpath(link, base)!r}"
                )


def _refuse_junctions(root: Path, rel: str) -> None:
    """Refuse a Windows junction at ``root / rel`` (``ValueError``): the folder itself, any part of the path ``rel`` (``tests`` in
    ``tests/fixtures``) and anything below it. ``shutil.copytree(symlinks=True)`` does not see a junction as a link (Python
    3.12 ``islink`` is False for it), follows it and copies the target as a real folder, so the snapshot would hold files from outside the
    tree. Looked at in the CALLER's tree before the copy: afterwards nothing tells the copy from a real folder. ``os.path.isjunction`` exists
    from Python 3.12 (always False off Windows); where it is missing there is nothing to ask."""
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is None:
        return
    here = root
    for part in re.split(r"[\\/]", rel):
        here = here / part
        if isjunction(here):
            raise ValueError(f"a junction is not followed: {rel!r} (at {part!r})")
    for dirpath, dirs, _files in os.walk(here):
        for name in dirs:
            if isjunction(os.path.join(dirpath, name)):
                raise ValueError(
                    f"a junction is not followed: {os.path.relpath(os.path.join(dirpath, name), root)!r}"
                )


def _refuse_skips_in_baseline(junit: Path, secrets: Sequence[str] = ()) -> None:
    """``RuntimeError`` when the passing unmutated run skipped a test, or left no readable JUnit file to prove it did not (``forbid_skips``)."""
    try:
        skipped = skipped_tests(junit.read_text(encoding="utf-8"))
    except (OSError, *JUNIT_REFUSED) as exc:
        raise RuntimeError(
            f"the unmutated copy left no usable JUnit file to check for skips: {type(exc).__name__}"
        ) from None
    if skipped:
        raise RuntimeError(
            _masked(
                f"the unmutated copy skipped {len(skipped)} selected test(s): {skipped[:3]}",
                secrets,
            )
        )


def _row(
    m: Mutant,
    rc: int,
    junit: Path,
    forbid_skips: bool,
    secrets: Sequence[str],
    first_lines: dict[str, str],
) -> tuple[str, Verdict, str, bool]:
    """The result row of one mutant run: its exit code ``rc`` and its JUnit file, judged once (one parse of the file)."""
    if rc == TIMED_OUT:
        return (m.name, Verdict.ERROR, "TIMEOUT", False)
    # the exit status is lost: an error row, never a pass or a kill
    if rc == REAPED_ELSEWHERE:
        return (m.name, Verdict.ERROR, "REAPED ELSEWHERE", False)
    try:
        too_big = (
            junit.exists() and junit.stat().st_size > MAX_JUNIT_CHARS
        )  # looked at BEFORE the file is read
        if too_big:
            raise ValueError("junit file over the ceiling")
        xml_text = junit.read_text(encoding="utf-8") if junit.exists() else ""
        report = read_junit(xml_text) if xml_text else JunitReport("", "", [], [], False, False)
    except JUNIT_REFUSED:
        return (m.name, Verdict.ERROR, "JUNIT REFUSED", False)
    if (
        forbid_skips and not xml_text
    ):  # no record of what ran cannot prove nothing was skipped: never judged
        return (m.name, Verdict.ERROR, "JUNIT MISSING", False)
    if report.collection_failed:  # a test file that could not be imported or collected: no test ran, an assert at import time is no kill
        first_lines[m.name] = _masked(report.first_line, secrets)
        return (m.name, Verdict.ERROR, "COLLECTION ERROR", False)
    if report.fixture_failed:  # a fixture that failed in setup or teardown means the test never ran as written: never a kill
        first_lines[m.name] = _masked(report.first_line, secrets)
        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)
    if (
        forbid_skips and report.skipped
    ):  # a skipped test proves nothing: never a kill, whatever else failed in the same run
        why = report.first_line or f"skipped: {', '.join(report.skipped[:3])}"
        first_lines[m.name] = _masked(why, secrets)
        return (m.name, Verdict.ERROR, "SKIPPED TESTS", False)
    v = judge(
        rc,
        report.test_id,
        report.first_line,
        expect=m.expect,
        pinned=m.pinned or None,
        crash_markers=m.crash_markers,
    )
    first_lines[m.name] = _masked(report.first_line, secrets)
    declared = _leading_class(report.first_line) == m.crash_type
    crash_ok = v is Verdict.CRASH and m.allow_crash and declared
    shown = report.test_id or (NO_TEST_NAMED if v is Verdict.ERROR else "")
    return (m.name, v, _masked(shown, secrets), v is Verdict.KILLED or crash_ok)


def _run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    extra_dirs: Sequence[str],
    only: Sequence[str],
    timeout: float,
    baseline_timeout: float | None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None,
    first_lines: dict[str, str],
    conftest: str = "",
    pass_env: Sequence[str] = (),
    forbid_skips: bool = False,
) -> list[tuple[str, Verdict, str, bool]]:
    first_lines.clear()  # the diagnostics of an earlier run must not answer for this one
    root = Path(root)
    mutants = list(mutants)
    for t in (*tests, *extra_dirs):
        _relative(t)
    env_names = _checked_env_names(
        pass_env
    )  # before anything runs: an unlisted name is refused, never passed
    if conftest:
        _plugin_module(conftest)
        if (
            not _inside(root, conftest).is_file()
        ):  # before any temp folder: a missing plugin file is a refusal, not a late copy error
            raise ValueError(f"conftest is not a file of the tree: {conftest!r}")
    secrets = _secret_values(env_names)
    canary = any(
        name in os.environ for name in env_names
    )  # a passed name that is set, even to an empty text, means a shared resource
    copied = (*tests, conftest) if conftest and conftest not in tests else tuple(tests)
    for m in mutants:  # before anything runs: a bad `test_file` must not surface after earlier mutants were already run
        if m.test_file and m.test_file not in tests:
            raise ValueError(
                f"mutant {m.name!r}: test_file {m.test_file!r} is not one of the copied tests"
            )
    # both folders are named from ONE mkdtemp, made inside the try below (held against a signal), so no signal can leave ``tmp`` alone behind
    made: list[Path] = []
    tmp: Path
    snap: Path

    def build() -> None:
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "tests").mkdir(parents=True)
        shutil.copytree(snap / "src", tmp / "src", symlinks=True)
        for t in copied:
            dst = _inside(tmp, t)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(_inside(snap, t), dst)
        for d in extra_dirs:
            if _inside(snap, d).exists():
                shutil.copytree(
                    _inside(snap, d), _inside(tmp, d), symlinks=True, dirs_exist_ok=True
                )

    def fresh() -> None:
        """Rebuild the temp copy: retried ``SETUP_TRIES`` times, then the last ``OSError`` is raised (never swallowed)."""
        for attempt in range(SETUP_TRIES):
            try:
                return build()
            except OSError:
                if attempt == SETUP_TRIES - 1:
                    raise
                time.sleep(SETUP_WAIT)

    out: list[tuple[str, Verdict, str, bool]] = []

    def emit(row: tuple[str, Verdict, str, bool]) -> None:
        out.append(row)
        if on_result is not None:
            on_result(row)

    held = contextlib.ExitStack()
    if canary:  # before any temp folder: a second runner on the same database is refused
        held.enter_context(
            _one_run_per_database([os.environ[n] for n in env_names if n in os.environ])
        )
    # the try starts right after the first temp folder exists: a refusal (a path through a link out of the tree, a missing ``src``)
    # or a signal at any later point leaves no temp folder behind
    try:
        with _signals_held():
            made.append(Path(tempfile.mkdtemp(prefix="mutants_")))
        tmp = made[0]
        snap = tmp.with_name(tmp.name + "_snap")
        snap.mkdir()
        # ONE snapshot of the tree at the start: every mutant copy is made from it, so an edit of ``root`` while the run is going (a
        # developer saving a file, a second tool) can never leak into a later mutant
        _refuse_junctions(root, "src")
        shutil.copytree(
            root / "src", snap / "src", symlinks=True, ignore=shutil.ignore_patterns("__pycache__")
        )  # links stay links (never followed out of the tree)
        for t in copied:
            dst = _inside(snap, t)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(_inside(root, t), dst)
        for d in extra_dirs:
            if _inside(root, d).exists():
                _refuse_junctions(root, d)
                shutil.copytree(
                    _inside(root, d), _inside(snap, d), symlinks=True, dirs_exist_ok=True
                )
        _refuse_links_out(snap)
        fresh()
        base_timeout = timeout if baseline_timeout is None else baseline_timeout
        base_rc = _pytest(
            tmp, tests, tmp / "base.xml", base_timeout, plugin=conftest, env_names=env_names
        )
        if base_rc == REAPED_ELSEWHERE:
            raise RuntimeError(
                "the baseline run was reaped by someone else: its exit status is unknown"
            )
        if base_rc != 0:
            raise RuntimeError("the unmutated copy does not pass its tests")
        if forbid_skips:
            _refuse_skips_in_baseline(tmp / "base.xml", secrets)
        for m in mutants:
            if only and not any(o in m.name for o in only):
                continue
            try:
                fresh()
            except OSError as exc:  # a setup failure is a RESULT ROW for this mutant, never a crash of the run and never silent
                emit((m.name, Verdict.ERROR, f"SETUP FAILED: {type(exc).__name__}", False))
                continue
            p = _locate(tmp, m.file)
            text = p.read_text(encoding="utf-8")
            if m.old not in text:
                emit((m.name, Verdict.ERROR, "SNIPPET NOT FOUND", False))
                continue
            p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\n")
            junit = tmp / "r.xml"
            if m.test_file:
                operands = [f"{m.test_file}::{m.only_test}" if m.only_test else m.test_file]
            else:
                operands = [f"{tests[0]}::{m.only_test}", *tests[1:]] if m.only_test else tests
            rc = _pytest(tmp, operands, junit, timeout, plugin=conftest, env_names=env_names)
            emit(_row(m, rc, junit, forbid_skips, secrets, first_lines))
            if canary:  # the passed database is shared by the baseline and every mutant run: prove the unmutated copy still passes on what this one left
                try:
                    fresh()
                except OSError as exc:
                    raise RuntimeError(
                        f"the unmutated copy could not be rebuilt for the canary run after mutant {m.name!r}: {type(exc).__name__}"
                    ) from None
                again = _pytest(
                    tmp,
                    tests,
                    tmp / "again.xml",
                    base_timeout,
                    plugin=conftest,
                    env_names=env_names,
                )
                reason = ""
                if again == 0 and forbid_skips:
                    try:
                        _refuse_skips_in_baseline(
                            tmp / "again.xml", secrets
                        )  # a database that is gone makes the tests skip, not fail
                    except RuntimeError as exc:
                        reason = f"after mutant {m.name!r}: {exc}"
                if again != 0:
                    reason = (
                        f"the unmutated copy no longer passes its tests after mutant {m.name!r} ({_run_end(again)}): the shared test database holds what the"
                        " mutant left behind, so the verdicts of the later mutants would not be reliable"
                    )
                if reason:
                    failure = CanaryFailed(reason)
                    failure.rows = tuple(out)
                    raise failure
    finally:
        held.close()
        with _signals_held():  # a signal is raised after the removal
            for folder in made:
                shutil.rmtree(folder, ignore_errors=True)
                shutil.rmtree(folder.with_name(folder.name + "_snap"), ignore_errors=True)
    return out
