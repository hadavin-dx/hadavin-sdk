"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` takes ONE snapshot of ``root/src`` (and the listed test files and fixtures) when it starts (an edit of ``root`` during the run never leaks into a later mutant) and copies it to a temp dir for EACH mutant; the pytest child sees only the environment variables in ``CHILD_ENV`` plus the names given in ``pass_env`` (no other DSN, token or secret of the caller), replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

Ladder (CODE-LAST rung table): rung 1, a free library or standard tool: ``pytest`` itself runs the tests and ``mutmut``-style tools mutate whole files without a
judged reason, so they cannot say WHY a mutant died (rejected: no reason check, no pinned killer); rung 3, a no-code tool: none fits a developer check; so thin
code that wraps ``pytest`` and the judge. Reuse of ``guard.runmap.redact_text`` for the hiding was read and rejected: it is pattern-based (it finds secret-shaped
text, not a given value), raises ``RedactionError`` with a six-second time budget, and would couple a stdlib-only tool that demos copy byte for byte to the
product module; the hiding here is a projection plus a known-value masker.

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
  by a path of plain ASCII identifier parts (no part a Python keyword, so ``class/conftest.py`` is refused) that ends in ``.py`` and is either called ``conftest.py`` or lies in a folder called ``tests``
  (any other tree file, such as ``src/pk/core.py``, is refused). It replaces ``--noconftest`` for that one file only; no other conftest is read.
- ``pass_env=("HADAVIN_TEST_PG_DSN",)``: names of caller environment variables the pytest child also sees (baseline, mutants and canary runs). Only
  names in ``PASS_ENV_ALLOWED`` are accepted (``ValueError`` for any other name, before anything runs); a name that is not set is simply not passed. To
  allow one more name, add it to ``PASS_ENV_ALLOWED``, re-copy the file and update its pin (see the CHANGELOG); do that only for the ADDRESS of a throwaway
  test resource, never for a token or a key. Setting a passed name also switches on ``forbid_skips`` (pass ``forbid_skips=False`` to turn it off).

  What a passed value is held to, in order (each step is a ``ValueError`` or ``RuntimeError`` BEFORE any test runs, except step 5):

  1. Plain characters only: no quote mark, backslash, control character or non-ASCII character anywhere in the value, and at most ``MAX_VALUE_CHARS`` (2,000)
     characters (also after percent-decoding a password). The message names the variable and the kind of character, never the value.
  2. The address is read by one strict grammar (``_address_fields``, the same one that names the lock) and must be in it, or the run is refused
     (fail closed): a ``postgresql://`` URL with an optional login, a host, a port and ONE database name and nothing after it, or key=value words from
     ``ADDRESS_KEYS_ALLOWED`` with no repeated key and no password word. A ``service`` file, ``options``, a ``?host=`` query or a second host is outside it.
  3. ``host`` AND ``hostaddr``, when written, must each be an exact member of ``throwaway_hosts`` (default ``THROWAWAY_HOSTS``: ``localhost``, ``127.0.0.1``,
     ``::1``) or a unix socket folder (key=value form only); no host at all is the local socket. There is no pattern and no override keyword. A caller
     whose database sits behind another name (a container service name, say) lists that exact name. NOT PROVEN by this check: a loopback name does not make
     a database a throwaway one (a tunnel or a proxy can point it at a shared one), and the check cannot see the rights of the login. The CALLER owns the claim
     that the database is throwaway and that its login can touch only that database. The address CI uses, ``postgresql://postgres@localhost:5432/postgres``, passes.
  4. At most ``MAX_SECRETS`` (300) texts to hide.
  5. One runner per address: the lock below.

  What is hidden. The child's text is not shown at all while a passed value is set, because a list of the forms of a secret (a slice, a base64 or hex
  copy, another encoding) can never be complete. Where child text would become output, only a projection is shown (``_shown_line``, ``_shown_id``):

  =========================================  ========================================================================================================
  hidden (never shown)                       the line of the failure, its message, the ``[...]`` part of a test id, anything else the child printed
  shown, fixed or from the caller            the leading exception class name when it is a plain identifier that shares no piece of ``PROJECTION_MIN`` (4)
                                             characters with a secret (else ``CLASS_HIDDEN``); the words ``[expect found]`` or ``[expect not found]``; the
                                             caller's own ``expect`` text; the file path and function name of a test id (else ``ID_HIDDEN``), with the
                                             parameters replaced by ``PARAMETERS_HIDDEN``; the run end (exit code, timed out, reaped); mutant names
  refused (before any run)                   an odd character, a value over the length bound, an address outside the grammar, a host not on the allowlist
  not covered                                the caller's own ``expect`` text and mutant names are shown as given; a test that itself writes the value to a
                                             file or the network is out of reach of this tool; the child's own console output is discarded and never read
  =========================================  ========================================================================================================

  The raw line stays inside the runner: ``judge`` and the ``crash_type`` check read it. The projection is then passed through ``_masked`` (the older masker,
  now a second layer: the whole value, its URL password and the forms of that password, and the head and tail beside ``...``; its bounds are
  ``EDGE_MIN``, ``PASSWORD_PIECE_MIN``, ``MAX_FRAGMENT_HITS``, ``MAX_FRAGMENT_WORK``). Where: ``first_lines``, the failing test id of a row, the
  ``COLLECTION ERROR``, ``FIXTURE ERROR`` and ``SKIPPED TESTS`` messages, the baseline skip message, the canary message and the baseline failure message
  (the run end and the class name only). With no passed value set nothing is projected and the text is shown as it is.

  The environment is read ONCE. At the start of the call the runner takes a snapshot of the variables the child gets (``CHILD_ENV`` and the names in
  ``pass_env``); the secrets, the canary decision, the lock name and the environment of EVERY child run come from it, never again from ``os.environ``.
  SAFETY: the address must point at a THROWAWAY database whose login can touch only that database (never a shared or production one): every mutant run
  writes to it, and a mutant can make those tests drop or fill tables with anything. Two runs at once on one database collide, so give each run its own.
  The runner checks in code: after EVERY mutant run it runs the unmutated copy again on that same database (the canary run) and, when that no longer passes,
  stops with ``RuntimeError`` naming the mutant (what the mutant left behind would make later verdicts false kills). A failed canary, a skipped one
  included (under ``forbid_skips``), is ``CanaryFailed`` (a ``RuntimeError``; its ``rows`` hold the rows so far; the message says "timed out" or "reaped"
  instead of an exit code when the run did). Cost: one extra pytest run and one extra copy of the tree per mutant. The canary proves only that the full
  unmutated tests pass, not that the database is clean.

  The lock. A second runner with the same address (the same spelling of host, host address, port and database name; the rest of the value does not matter)
  is refused by an exclusive lock file named by the first 16 hex digits of a SHA-256 of those four parts (``_address_parts``; a password is never read or
  hashed). It lives in a folder of the user (POSIX: ``hadavin_mutation_locks_<uid>`` inside the temp folder, made with mode 0700 and refused unless it is a
  real folder of this user with no access for group or others, so another user of a shared ``/tmp`` can neither read the names nor plant a file to stop a run;
  Windows: the temp folder, which is private to the account). So two DIFFERENT users on one machine are not seen by each other's locks (the canary run still
  catches a collision afterwards). The match is on SPELLING: one database written two ways (``localhost`` and ``127.0.0.1``, a port written or left out,
  ``host=`` and ``hostaddr=``) gets two names and is NOT refused; values outside the grammar share the name ``unparsed``. The file is opened without following a
  symbolic link, without blocking, mode 0600, checked (regular file, this user, one name, mode 0600 or narrower) and never deleted (one empty file per
  distinct name; delete by hand only as its owner and when no run is going). A lock that cannot be opened or locked for another reason is a ``RuntimeError``
  with its own message. A runner with another temp folder or on another machine is not seen.
- ``forbid_skips=True``: a run in which any selected test is skipped (or an expected failure) proves nothing, so it is an ERROR row
  ``SKIPPED TESTS`` (never a kill), and an unmutated baseline with a skipped test raises ``RuntimeError``. This closes the false kill where
  a mutant "dies" because the tests could not run (for example no database was reachable). A mutant run with no JUnit file or an empty one
  is the ERROR row ``JUNIT MISSING`` under this keyword.

Always on (no keyword), two changes of result and one new label: (1) a run whose FIRST failing test case failed in a fixture, at setup or at teardown
(``read_junit(...).fixture_failed`` in ``testing.mutation``), is the ERROR row ``FIXTURE ERROR`` and never a kill; before, such a run was a kill when the fixture
failed with an ``AssertionError`` and a crash otherwise. A test whose body failed and whose teardown failed afterwards is judged by the failure
(the test ran as written). (2) ``testing.mutation.judge`` returns ``ERROR`` when the run failed (exit 1) and no failing test id is known (an empty or
unreadable JUnit file), where it used to return ``CRASH`` or ``KILLED``; (3) a run whose FIRST failing case is a test file that could not be imported or collected (pytest word: ``collection failure``; an ``assert`` at import time included) is the ERROR row ``COLLECTION ERROR`` with pytest's message. This is only a new label: pytest exits 2 for it and the judge already returned ERROR for every exit code other than 1, so the old row was an ERROR row with the module name as its test id (the CHANGELOG has the run that shows it), never a kill. A mutant counts as killed only when a test ran as written and failed: that part of the rule is not changed by item 3.

Result rows. A row is ``(name, verdict, test id, good)``. The test id column holds the failing test id, or one of these texts for an ERROR row
that has no verdict from the judge: ``SETUP FAILED: <error class>``, ``SNIPPET NOT FOUND``, ``TIMEOUT``, ``REAPED ELSEWHERE``, ``JUNIT REFUSED`` (refused or unreadable),
``JUNIT MISSING`` (``forbid_skips``), ``COLLECTION ERROR``, ``FIXTURE ERROR``, ``SKIPPED TESTS`` (``forbid_skips``), ``NO FAILING TEST NAMED`` (exit code 1, the JUnit file names no failing test) and ``EXIT CODE <n>`` (any other exit code with no failing test named: a usage error, an internal error, a kill by the system). ``first_lines`` holds, for every judged row that has a first ``E`` line (a kill or not), that line (a projection while a passed value is set), and for ``COLLECTION ERROR``, ``FIXTURE ERROR`` and ``SKIPPED TESTS`` the message that says why (a projection while a passed value is set).

Dev-tool constants: ``MAX_JUNIT_CHARS`` (in ``testing.mutation``), ``PASS_ENV_ALLOWED``, ``MASK``, ``EDGE_MIN``, ``PASSWORD_PIECE_MIN``, ``MAX_FRAGMENT_HITS``, ``MAX_SECRETS``, ``MAX_FRAGMENT_WORK``, ``MAX_VALUE_CHARS``, ``PROJECTION_MIN``, ``THROWAWAY_HOSTS``, ``ADDRESS_KEYS_ALLOWED``, ``NO_TEST_NAMED``, ``SETUP_TRIES``, ``SETUP_WAIT``, ``WAIT_POLL``, ``TREE_KILL_TIMEOUT``,
``TIMED_OUT``, ``REAPED_ELSEWHERE``, ``CHILD_ENV``, ``CHILD_FIXED_ENV``, ``JUNIT_REFUSED`` and the default run timeout (``DEFAULT_TIMEOUT``, 900.0 seconds) are module constants here and NOT in ``defaults.py``:
the no-hardcoding rule is about product behaviour (names, regions, prices, thresholds a deployment tunes), and this is a developer tool
that ships in no wheel, has no config surface and is copied byte for byte into demos. A caller changes the timeouts by argument.
"""

from __future__ import annotations

import contextlib
import errno
import functools
import hashlib
import importlib
import itertools
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
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote, quote_plus, unquote, unquote_plus, urlsplit

from hadavin_sdk.testing.mutation import (
    MAX_JUNIT_CHARS,
    JunitReport,
    Verdict,
    judge_report,
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
EDGE_MIN = 2  # a head or tail piece of a secret next to ``...`` is masked from this many characters on (one character cannot be told from ordinary text)
PASSWORD_PIECE_MIN = 3  # a piece of an unquoted password that holds a quote mark, ``;`` or ``&`` is a secret of its own from this many characters on
MAX_FRAGMENT_HITS = 1_000  # more ``...`` than this in one text is no honest line (pytest writes a few): the whole text is replaced, never scanned (see ``_masked``)
MAX_SECRETS = 300  # more secret texts than this (a value, its password and their decoded and encoded forms) are refused: no honest address has that many
MAX_FRAGMENT_WORK = 50_000  # (``...`` in a line) x (secrets): more than this replaces the whole line, so one line costs a bounded number of scans
MAX_VALUE_CHARS = 2_000  # a passed value longer than this is refused: no address is that long, and the scan and the memory of the secrets grow with its length
CHILD_FIXED_ENV = {
    "PYTHONNOUSERSITE": "1"
}  # set, not inherited: the child never imports from the caller's user site-packages
SETUP_TRIES = 5  # attempts to clear and rebuild the temp copy (a Windows file lock may hold a file for a moment)
SETUP_WAIT = 0.5  # seconds between those attempts
# a refused JUnit file (DOCTYPE, ENTITY, too large) or a truncated one (ET.ParseError is a SyntaxError) is THIS mutant's ERROR, not the end of the run
JUNIT_REFUSED = (ValueError, SyntaxError)
_UNUSABLE_JUNIT = (
    OSError,
    *JUNIT_REFUSED,
)  # a JUnit file that is refused, truncated or cannot be read: that mutant's ERROR row


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
    r"(?is)(?:password|passwd|pwd) *=( *)([^\s&;]+)"
)  # ``password=...`` of a key=value DSN or a URL query, up to the next white space, ``&`` or ``;`` (no quote mark, backslash or control character such as a tab can be in the value: see ``_refuse_odd``, which runs first, so only the space is spelled out). No lookbehind: ``sslpassword=`` and ``PGPASSWORD=`` are read too
_NOT_WHITE = re.compile(r"\S*")  # the rest of a word, up to the next white space
# every ``...`` (or the one character U+2026 that a newer pytest could print), also those that share a dot (a secret may end in a dot): one match at the start of each
_DOTS = re.compile(r"(?=\.\.\.|\u2026)")


def _odd_character(text: str) -> str | None:
    """The kind of the first character of ``text`` that a print of the text could change, or ``None``: a quote mark or a backslash (a print adds
    them), a control character or a non-ASCII character (a print writes them as an escape such as ``\\xe9``). Space and the other printable ASCII
    characters are printed as they are."""
    for char in text:
        if char in "'\"":
            return "a quote mark"
        if char == "\\":
            return "a backslash"
        if ord(char) < 32 or ord(char) == 127:
            return "a control character"
        if ord(char) > 127:
            return "a non-ASCII character"
    return None


def _refuse_odd(name: str, what: str, text: str) -> None:
    """``ValueError`` when ``text`` (``what`` of the variable ``name``) holds a character ``_odd_character`` names. The message names the variable and
    the kind of character, never the text."""
    kind = _odd_character(text)
    if kind is not None:
        raise ValueError(
            f"{name} is refused: {what} holds {kind}. The runner hides a secret by looking for its plain text, and a print of a text with such a"
            " character no longer shows the plain text, so it could not be hidden. The rule covers the whole address, also its host, database"
            " name and options. Use a throwaway database whose address and password hold only plain printable ASCII letters, digits and"
            " punctuation without quote marks and backslashes (a percent-encoded password is read decoded)."
        )


def _url_passwords(value: str) -> tuple[list[str], list[str]]:
    """The password of a URL as ``urlsplit`` reads it, and every text between the first ``:`` after ``://`` and an ``@`` after it: a password that
    holds an unencoded ``/``, ``?``, ``#`` or ``@`` is not read right by ``urlsplit`` (it takes the first of them as the end of the address), so
    every ``@`` is tried as the end of the login (more than needed is masked, never less). With no ``@`` after the first colon (``host:5432/db``) there is
    no password and no candidate; with one, everything between them is a candidate, also ``12/45`` in ``svc:12/45@h/db``."""
    found: list[str] = []  # every text between the first colon and an @
    proper = ""
    with contextlib.suppress(ValueError):  # not URL-shaped: only the key=value scan applies
        proper = urlsplit(value).password or ""
    if "://" in value:
        rest = value.split("://", 1)[1]
        colon = rest.find(":")
        at = rest.find("@", colon + 1) if colon != -1 else -1
        while at != -1:
            found.append(rest[colon + 1 : at])
            at = rest.find("@", at + 1)
    # a candidate with ``?`` or ``#`` in it may reach into the options after the address: hidden as written only; the others are read as passwords
    return [proper, *(c for c in found if not re.search(r"[?#]", c))], [
        c for c in found if re.search(r"[?#]", c)
    ]


def _password_texts(value: str) -> tuple[list[str], list[str]]:
    """``(decoded, plain)``: the texts of ``value`` that are, or may be, a password. ``decoded`` are those that are read as a password and so also
    checked and percent-decoded: the one right after ``password=`` (up to the next ``&``, ``;`` or white space) and the passwords of a URL.
    ``plain`` are those that are only hidden as written: the rest of the word after a password word (up to the next white space), its pieces split
    at ``;`` and ``&`` of ``PASSWORD_PIECE_MIN`` characters or more (an unquoted password may hold them), and the text after ``password=`` and a
    space (it may be the next option, not a password). Other options in the same value are not decoded, so a non-ASCII option does not refuse a run."""
    matches = list(_PASSWORD_WORD.finditer(value))
    decoded = [m.group(2) for m in matches if not m.group(1)]
    plain = [m.group(2) for m in matches if m.group(1)]
    words: list[str] = []
    reached = 0  # a password word inside the word of an earlier one adds nothing: its text is a piece of that word and of its pieces
    for m in matches:
        if m.start(2) >= reached:
            word = _NOT_WHITE.match(
                value, m.start(2)
            )  # ``\S*`` always matches; the fallback only keeps the type honest
            reached = word.end() if word else m.end(2)
            words.append(value[m.start(2) : reached])
    plain += words
    plain += [
        piece
        for word in words
        for piece in re.split(r"[;&]", word)
        if len(piece) >= PASSWORD_PIECE_MIN
    ]  # the pieces of an unquoted password that holds ``;`` or ``&``: each may stand alone in a message
    url_decoded, url_plain = _url_passwords(value)
    decoded += url_decoded
    plain += url_plain
    return [p for p in dict.fromkeys(decoded) if p], [p for p in dict.fromkeys(plain) if p]


def _decoded_forms(name: str, password: str) -> set[str]:
    """``password`` as written, percent-decoded once with and without ``+`` read as a space, and decoded again until nothing changes (a password that
    was encoded twice, ``a%2540b``, shows as ``a@b`` after two decodes). Every step is checked by ``_refuse_odd``."""
    forms = {password}
    for what, decode in (
        ("the password in it, percent-decoded", unquote),
        ("the password in it, percent-decoded with + read as a space", unquote_plus),
    ):
        text = password
        for _ in range(
            len(password) + 1
        ):  # each change makes the text shorter or swaps ``+`` for a space, so this ends
            decoded = decode(text)
            _refuse_odd(name, what, decoded)
            # this chain ends when a step changes nothing; the other chain starts again from the password (``a%2Bb`` is ``a+b`` after ``unquote`` and ``a b`` after ``unquote_plus``)
            if decoded == text:
                break
            forms.add(decoded)
            text = decoded
    return forms


def _encoded_forms(text: str) -> set[str]:
    """``text`` as a URL or a form writes it: every character but letters, digits and ``_.-~`` as a percent code (``quote(safe="")``), the same with
    ``/`` kept (``quote``), and with a space as ``+`` (``quote_plus``); each in upper and in lower case hex."""
    forms = set()
    for form in (quote(text, safe=""), quote(text), quote_plus(text)):
        forms.add(form)
        forms.add(re.sub(r"%[0-9A-F]{2}", lambda m: m.group().lower(), form))
    return forms


_HOST = r"(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:.]+\])"
_URL_ADDRESS = re.compile(
    rf"(?i:postgres(?:ql)?)://(?:[^@/?#\s]*@)?({_HOST})(?::([0-9]+))?/([A-Za-z0-9_.-]+)"
)  # the WHOLE value: a scheme, a login with no ``@``, ``/``, ``?`` or ``#`` in it, a host, a port, ONE database name, nothing after
_PAIR = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)=([A-Za-z0-9_.:/@+%,~-]+)"
)  # one ``key=token`` of a key=value address
_ADDRESS_VALUE = {
    "host": re.compile(_HOST),
    "hostaddr": re.compile(r"[A-Za-z0-9.:-]+"),
    "port": re.compile(r"[0-9]+"),
    "dbname": re.compile(r"[A-Za-z0-9_.-]+"),
}
_PASSWORD_KEY = re.compile(r"(?i)password|passwd|pwd")


def _address_parts(value: str) -> str:
    """The name of the database in ``value`` as the lock hashes it, or ``"unparsed"``. A STRICT ALLOWLIST: text is taken from ``value`` only when the
    WHOLE value is (a) a URL ``postgres://`` or ``postgresql://`` with an optional login, a host (letters, digits, ``.``, ``-`` or a bracketed
    IPv6), an optional ``:digits`` port and exactly one ``/name`` of letters, digits, ``_``, ``.``, ``-``, with nothing after it (no query, no
    fragment, no second ``/``), or (b) space-separated ``key=token`` pairs, none with a password word in its key, where ``host``, ``hostaddr``, ``port``
    and ``dbname`` (if present) match their own grammar. Only the host (in lower case), host address, port and database name are then used; the login
    and every other pair are never read. Everything else gives ``"unparsed"``, so a value that holds a password where this reading could be fooled
    shares one name with all such values (so whether a value is read can depend on the password's shape: a password with ``@``, ``/``, ``?``, ``#`` or
    a space in a URL gives ``"unparsed"``, a plain one gives the address; the hashed text itself never holds a password text). THIS IS A MATCH ON SPELLING, NOT ON THE DATABASE: ``localhost`` and ``127.0.0.1``, a port written or left
    out, and ``host=`` and ``hostaddr=`` give different names for one database, and two runners on those are NOT
    refused. A URL with a query (``?host=`` included) is ``"unparsed"``, and so is a value with a password word in a key=value address (a password with a space could pose as an option)."""
    fields = _address_fields(value)
    if fields is None:
        return "unparsed"
    return "\n".join(fields.get(key, "") for key in _ADDRESS_VALUE)


_SOCKET_DIR = re.compile(r"/[A-Za-z0-9_./-]*")
# the keys of a key=value address that the address check reads (everything else, ``service`` and ``options`` included, may change where the
# connection goes, so an address that holds one is refused when a name is passed)
ADDRESS_KEYS_ALLOWED = (
    "host", "hostaddr", "port", "dbname", "user", "sslmode", "connect_timeout", "application_name", "sslrootcert",
)  # fmt: skip
THROWAWAY_HOSTS = (
    "localhost",
    "127.0.0.1",
    "::1",
)  # the default of ``throwaway_hosts``: this machine, spelled out


def _address_fields(
    value: str, *, sockets: bool = False, keys: Sequence[str] | None = None
) -> dict[str, str] | None:
    """The parts (``host``, ``hostaddr``, ``port``, ``dbname``, as found) that the strict grammar of ``_address_parts`` reads from ``value``, or ``None``
    when the value is outside it. ``sockets=True``: a ``host`` in key=value form may be a unix socket folder (a path of plain characters with no ``..``
    part). ``keys``: every key of a key=value address must be in it and no key may repeat (the address check's stricter reading)."""
    found: dict[str, str] = {}
    url = _URL_ADDRESS.fullmatch(value)
    if url:
        found = {"host": url.group(1).lower(), "port": url.group(2) or "", "dbname": url.group(3)}
    else:
        for word in value.split(" "):
            pair = _PAIR.fullmatch(word)
            if not pair or _PASSWORD_KEY.search(pair.group(1)):
                return None
            key, token = pair.group(1).lower(), pair.group(2)
            if keys is not None and (key not in keys or key in found):
                return None
            if key in _ADDRESS_VALUE:
                socket = (
                    sockets
                    and key == "host"
                    and _SOCKET_DIR.fullmatch(token)
                    and ".." not in token.split("/")
                )
                if not (_ADDRESS_VALUE[key].fullmatch(token) or socket):
                    return None
                found[key] = token.lower() if key == "host" else token
    return found or None


def _checked_throwaway_hosts(hosts: Iterable[str]) -> tuple[str, ...]:
    """``hosts`` as a tuple of exact lower-case host names (no pattern: ``*``, ``/`` and white space are refused), else ``ValueError``."""
    if isinstance(hosts, str):
        raise TypeError("throwaway_hosts is a sequence of host names, not one string")
    chosen = tuple(h.lower().strip("[]") if isinstance(h, str) else h for h in hosts)
    for host in chosen:
        if not isinstance(host, str) or not re.fullmatch(r"[a-z0-9.:-]+", host):
            raise ValueError(
                "throwaway_hosts holds exact host names or addresses only (letters, digits, '.', ':', '-'): no pattern, no path"
            )
    return chosen


def _refuse_unsafe_address(env_name: str, value: str, throwaway_hosts: Sequence[str]) -> None:
    """``ValueError`` (before anything runs; the message names the variable and the reason, never the value) unless the address of a passed variable is read
    by the strict grammar (``_address_fields``; fail closed: an address it cannot read is refused) and BOTH its ``host`` and its ``hostaddr``, when written,
    are exact members of ``throwaway_hosts`` (or a unix socket folder; no host at all is the local socket). Least privilege: every mutant's tests write to
    this database. STATED PLAINLY: a loopback name does not prove the database is a throwaway one (a tunnel or a proxy can make it a shared one) and the check
    cannot see the login's rights; it only stops the plain mistakes (a remote host, a ``service`` file, a ``?host=`` override, a second host). The
    caller still owns the claim that the database is throwaway and that its login can touch only that database."""
    fields = _address_fields(value, sockets=True, keys=ADDRESS_KEYS_ALLOWED)
    if fields is None:
        raise ValueError(
            f"{env_name} is refused: its address is not in a shape the runner can check (a postgresql:// URL with an optional login, a host, a port and ONE"
            " database name and nothing after it, or key=value words from host, hostaddr, port, dbname, user, sslmode, connect_timeout,"
            " application_name, sslrootcert; no password word, no repeated key, no service file, no ?host= option)"
        )
    allowed = _checked_throwaway_hosts(throwaway_hosts)
    for part in ("host", "hostaddr"):
        host = fields.get(part, "").strip("[]").lower()
        if host and not host.startswith("/") and host not in allowed:
            raise ValueError(
                f"{env_name} is refused: its {part} is not one of throwaway_hosts {allowed}. Tests of every mutant write to that database; name"
                " the host on purpose with throwaway_hosts=(...) only when it is a throwaway database"
            )


def _env_snapshot(names: Iterable[str]) -> dict[str, str]:
    """ONE read of the caller's environment for a whole call: the variables a child gets (``CHILD_ENV``) and the passed ``names`` that are set (a
    name set to an empty text is kept). The secrets to hide, the canary test, the lock name and every child's environment come from this dict and
    never again from ``os.environ``, so a variable the caller changes while the run is going changes nothing."""
    return {k: os.environ[k] for k in (*CHILD_ENV, *names) if k in os.environ}


def _secret_values(
    names: Iterable[str], environ: Mapping[str, str] | None = None
) -> tuple[str, ...]:
    """The values of the passed environment variables (read from ``environ``, the snapshot of the call; ``os.environ`` when none is given), and the password inside them (see ``_password_texts``; each as written, percent-decoded
    until nothing changes, with ``+`` read as a space, and percent-encoded again as ``_encoded_forms`` writes it), longest first. Text that may show
    them is run through ``_masked``. ``ValueError`` (before anything runs) when a value is longer than ``MAX_VALUE_CHARS``, or when any of these
    texts but the encoded ones holds a quote mark, a backslash, a control character or a non-ASCII character (``_refuse_odd``): every text left is
    plain printable ASCII, so a print of it at any depth still holds it as written."""
    bases: set[str] = set()
    for name in names:
        value = (os.environ if environ is None else environ).get(name, "")
        if not value:
            continue
        if len(value) > MAX_VALUE_CHARS:
            raise ValueError(
                f"{name} is refused: its value is longer than {MAX_VALUE_CHARS} characters (no address is, and the runner would scan every secret"
                " in it against every line). Use a shorter address."
            )
        _refuse_odd(name, "its value", value)
        bases.add(value)
        decoded, plain = _password_texts(value)
        bases.update(plain)
        for password in decoded:
            for form in _decoded_forms(name, password):
                bases.add(form)
                bases |= _encoded_forms(form)
        if len(bases) > MAX_SECRETS:
            raise ValueError(
                f"{name} is refused: it gives more than {MAX_SECRETS} texts to hide (a password written in many encoded layers). Use a plainer address."
            )
    return tuple(sorted(bases, key=len, reverse=True))


def _prefix_table(pattern: str) -> list[int]:
    """The KMP failure table of ``pattern`` (entry ``i``: the length of the longest proper prefix of ``pattern[:i + 1]`` that is also its suffix)."""
    table = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k and pattern[i] != pattern[k]:
            k = table[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        table[i] = k
    return table


def _longest_overlap(pattern: str, table: Sequence[int], window: str) -> int:
    """The length of the longest prefix of ``pattern`` that is a suffix of ``window`` (``table`` is ``_prefix_table(pattern)``). One pass over ``window``
    (the cost is linear in ``len(window)``; the table work is amortised), no slice and no repeated compare. ``window`` must be shorter than ``pattern``."""
    k = 0
    for ch in window:
        while k and ch != pattern[k]:
            k = table[k - 1]
        if ch == pattern[k]:
            k += 1
    return k


def _fragment_spans(text: str, secret: str, hits: list[re.Match[str]]) -> list[tuple[int, int]]:
    """Spans of ``text`` that show a shortened ``secret``: pytest cuts a long text in an assertion line to ``head...tail`` (about 12 characters
    at the start and 13 at the end, checked with a real run), so the longest start of the secret that ends right before a ``...`` and the longest end of it that
    starts right after one are returned (each ``EDGE_MIN`` characters or longer, and shorter than the secret). ``hits`` are the ``...`` of the line,
    found once by ``_masked`` (not more than ``MAX_FRAGMENT_HITS``). Cost: the prefix tables of the secret and of its reverse are built once, O(len(secret)); each ``...`` then costs one pass
    over at most ``len(secret) - 1`` characters before it and one over as many after it (``_longest_overlap``), O(len(secret)) per ``...``, never a compare per candidate start."""
    spans: list[tuple[int, int]] = []
    top = len(secret) - 1
    if top < EDGE_MIN:  # a piece must be shorter than the secret and EDGE_MIN long
        return spans
    backwards = secret[::-1]
    head_table, tail_table = _prefix_table(secret), _prefix_table(backwards)
    for hit in hits:
        start = hit.start()
        end = start + (
            1 if text[start] == "\u2026" else 3
        )  # the width of the ellipsis that this hit is
        # the longest start of the secret that ends right before the ellipsis: the longest prefix of the secret that is a suffix of the text before it
        size = _longest_overlap(secret, head_table, text[max(0, start - top) : start])
        if size >= EDGE_MIN:
            spans.append((start - size, start))
        # the longest end of the secret that starts right after it: the same on the reversed secret and the reversed text after it
        size = _longest_overlap(backwards, tail_table, text[end : end + top][::-1])
        if size >= EDGE_MIN:
            spans.append((end, end + size))
    return spans


def _masked(text: str, secrets: Sequence[str]) -> str:
    """``text`` with every secret value replaced by a marker (pass_env values must never reach ``first_lines``, a result row or an error message).
    ``secrets`` are plain printable ASCII (``_secret_values`` refuses anything else), so each is found as it stands. A secret that pytest shortened
    to ``head...tail`` is masked by its pieces beside ``...`` too (see ``_fragment_spans``). Every span is found in the ORIGINAL text and then
    all are cut out at once, so a short secret that sits inside a longer one cannot break the match of the longer one. More than
    ``MAX_FRAGMENT_HITS`` ``...`` replace the whole text (no honest line has that many; hiding only the first ``MAX_FRAGMENT_HITS`` would leave a
    piece beside a later ``...`` readable). Cost: a line is scanned for each secret once, and each ``...`` costs one pass per secret over at most twice the length of that secret (``_fragment_spans``); (``...`` x secrets) above ``MAX_FRAGMENT_WORK`` (a count of pairs, not of characters; worst case about 2 x 10^8 character steps) replaces the whole line. A secret of one or two characters hides every such text in the line (garbling is the price of never leaving a short secret readable)."""
    chosen = tuple(v for v in secrets if v)
    if not chosen:
        return text
    dots = list(
        itertools.islice(_DOTS.finditer(text), MAX_FRAGMENT_HITS + 1)
    )  # found once for the whole line
    if len(dots) > MAX_FRAGMENT_HITS:
        return f"{MASK} (line with more than {MAX_FRAGMENT_HITS} '...' replaced: it cannot be checked for pieces of a value)"
    if len(dots) * len(chosen) > MAX_FRAGMENT_WORK:
        return f"{MASK} (line with too many '...' for the number of values replaced: it cannot be checked for pieces of a value)"
    hit = bytearray(len(text))
    for value in chosen:
        marked = 0  # the text before this index is already marked for this value: each character is marked once
        at = text.find(value)
        while at != -1:
            lo = max(at, marked)
            hit[lo : at + len(value)] = b"\x01" * (at + len(value) - lo)
            marked = at + len(value)
            at = text.find(value, at + 1)
    if dots:
        for value in chosen:
            for lo, hi in _fragment_spans(text, value, dots):
                hit[lo:hi] = b"\x01" * (hi - lo)
    out: list[str] = []
    for ch, bad in zip(text, hit, strict=True):
        if not bad:
            out.append(ch)
        elif not out or out[-1] != MASK:
            out.append(MASK)
    return "".join(out)


PROJECTION_MIN = 4  # a piece of a secret of this many characters is never part of what a projection shows (see ``_shows_a_piece``)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CLASS_HIDDEN = "[class not shown]"  # the fixed word for a class name that is no identifier or shares a piece with a secret
ID_HIDDEN = "[test id not shown]"
PARAMETERS_HIDDEN = "[parameters hidden]"  # replaces the ``[...]`` part of a parametrized test id


@functools.lru_cache(maxsize=16)
def _pieces(secrets: tuple[str, ...]) -> frozenset[str]:
    """Every ``PROJECTION_MIN``-character piece of every secret, lower case."""
    return frozenset(
        v.lower()[i : i + PROJECTION_MIN]
        for v in secrets
        for i in range(len(v) - PROJECTION_MIN + 1)
    )


def _shows_a_piece(text: str, secrets: Sequence[str]) -> bool:
    """True when ``text`` holds a piece of ``PROJECTION_MIN`` characters or more of any secret (any letter case): the one test that a field of a
    projection must pass. Exact for the short fields a projection shows (a class name, a file path and a function name)."""
    pieces = _pieces(tuple(v for v in secrets if v))
    low = text.lower()
    return any(low[i : i + PROJECTION_MIN] in pieces for i in range(len(low) - PROJECTION_MIN + 1))


def _shown_line(raw: str, secrets: Sequence[str], expect: str = "") -> str:
    """What the caller gets to see of the first ``E`` line of a child run. With no secret to hide the line as it is. With a secret (a passed
    environment variable is set) the child's text is NOT shown, because a denylist of forms of a secret cannot be complete (a slice, a base64 or hex
    copy, another encoding): only (a) the leading exception class name, when it is a plain identifier that shares no piece of ``PROJECTION_MIN`` characters
    with a secret (else ``CLASS_HIDDEN``), (b) a fixed word that says whether the caller's ``expect`` text was in the line, and (c) the caller's own
    ``expect`` text. The judge and ``crash_type`` read the raw line inside the runner; the result still goes through ``_masked`` (a second layer)."""
    if not any(secrets):
        return raw
    head = _leading_class(raw) if raw else ""
    cls = (
        head if _IDENTIFIER.fullmatch(head) and not _shows_a_piece(head, secrets) else CLASS_HIDDEN
    )
    if not raw:
        return ""
    word = (
        ""
        if not expect
        else (" [expect found] " if expect in raw else " [expect not found] ") + expect
    )
    return _masked(f"{cls}{word}", secrets)


def _shown_id(test_id: str, secrets: Sequence[str]) -> str:
    """The test id of a row as the caller sees it. With no secret as it is. With a secret: the file path and the function name only, the ``[...]``
    part of a parametrized test replaced by ``PARAMETERS_HIDDEN``, and ``ID_HIDDEN`` when what is left still shares a piece of ``PROJECTION_MIN``
    characters with a secret."""
    if not any(secrets):
        return test_id
    base, bracket, _rest = test_id.partition("[")
    shown = base + (PARAMETERS_HIDDEN if bracket else "")
    return ID_HIDDEN if _shows_a_piece(shown, secrets) else _masked(shown, secrets)


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
    """The folder of the lock files. POSIX: a folder of this user inside the temp folder (``hadavin_mutation_locks_<uid>``, mode 0700, made if it is
    missing and refused with ``RuntimeError`` unless it is a real folder, not a link, owned by this user with no access for group or others), so another
    user of a shared ``/tmp`` can neither read the lock names nor plant a file under one to stop a run. Windows: the temp folder itself (it is
    private to the account there)."""
    base = Path(tempfile.gettempdir())
    if _IS_WINDOWS:
        return base
    path = base / f"hadavin_mutation_locks_{os.getuid()}"
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass  # checked below
    except OSError as exc:
        raise RuntimeError(
            f"the lock folder of this run could not be made ({type(exc).__name__}): give the run a temp folder of its own with TMPDIR"
        ) from None
    info = os.lstat(path)
    if (
        not stat.S_ISDIR(info.st_mode)
        or os.getuid() != info.st_uid
        or stat.S_IMODE(info.st_mode) & 0o077
    ):
        raise RuntimeError(
            "the lock folder of this run is not a real folder of this user with mode 0700 (remove it as its owner, or give the run a temp folder of its own with TMPDIR), so the run cannot be proven alone on its database"
        )
    return path


_NO_ACCESS = "this user may not open it (it belongs to another user, the temp folder is closed to this user, or the temp folder is read-only; give the run a temp folder of its own with TMPDIR)"
_NOT_OPENED_BECAUSE = {
    errno.ELOOP: "it is a symbolic link",
    errno.EACCES: _NO_ACCESS,
    errno.EPERM: _NO_ACCESS,
    errno.EISDIR: "it is a folder",
    errno.ENOTDIR: "a part of its path is not a folder",
}


def _why_not_opened(code: int | None) -> str:
    if code is None:
        return f"errno {code}"
    return _NOT_OPENED_BECAUSE.get(code, f"errno {code}")


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
        or info.st_nlink > 1
    ):
        raise RuntimeError(
            "the lock file of this run is not a regular file of this user with one name, mode 0600 or narrower (remove it as its owner, or give the run a temp folder of its own with TMPDIR), so the run cannot be proven alone on its database"
        )


@contextlib.contextmanager
def _one_run_per_database(values: Sequence[str]) -> Iterator[None]:
    """Hold an exclusive lock named by a hash of where the passed values point (host, host address, port and database name as spelled; never the values) in the temp folder for the whole run. A second runner that
    uses the same temp folder (same machine and account, or the same ``TMPDIR``) with the same address (the same spelling of the four parts; the lock name depends on the address only, not on the rest of the value) is refused (``RuntimeError``) instead
    of sharing the database and its tables. It does not see a runner with another temp folder or on another machine; that stays the caller's
    job (a database of its own per run).

    The file is opened without following a symbolic link, without blocking (so a FIFO under the name is refused instead of hanging the run) and
    with mode 0600. It is never deleted: one empty file per distinct name (per spelling of an address, not per value) stays in the temp folder. After opening it is checked, and it is refused with a
    message that names the cause when it belongs to another user, has a wider mode, is not a regular file, or has more than one hard link. A temp
    folder on a network file system whose ``flock`` fails is refused as "could not be locked": use a local ``TMPDIR``.

    The file name holds the first 16 hex digits of a SHA-256 of the host, host address, port and database name that ``_address_parts`` reads from the values by a strict
    grammar (a password is never captured or hashed: only the four address parts are cut out of the value). It is a best-effort match on SPELLING: one database written two ways
    (``localhost`` and ``127.0.0.1``, a port written or left out, ``host=`` and ``hostaddr=``) gets two names and a second
    runner on the other spelling is NOT refused. Values outside the grammar (anything with a password word in a key=value address, a URL with a query,
    a second ``/``, or an ``@``, ``/``, ``?``, ``#`` or space in the password) share the name ``unparsed``, so such a second run is refused even on another database. A lock
    file that cannot be opened (another user's file) or locked for a reason other than "held by another run" is a ``RuntimeError`` with its own message."""
    digest = hashlib.sha256(
        "\0".join(sorted(_address_parts(v) for v in values)).encode()
    ).hexdigest()[:16]
    path = _lock_dir() / f"hadavin_mutation_{digest}.lock"
    # O_NONBLOCK: a FIFO planted under the name would block an open for reading for ever (it is then refused by the fstat check)
    # read-only on POSIX (``flock`` needs no write access, so a file narrowed to 0400 still works); Windows locks a byte, which needs write access
    flags = (
        (os.O_RDWR if _IS_WINDOWS else os.O_RDONLY)
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    try:
        fd = os.open(path, flags, 0o600)
        try:
            handle = os.fdopen(fd, "r+b" if _IS_WINDOWS else "rb")
        except OSError:
            os.close(fd)  # no file object took the descriptor over
            raise
    except OSError as exc:
        raise RuntimeError(
            f"the lock file of this run could not be opened ({type(exc).__name__}): {_why_not_opened(exc.errno)}, so the run cannot be proven alone on its database"
        ) from None
    with handle:
        _check_lock_file(handle.fileno())
        try:
            if _IS_WINDOWS:
                msvcrt = importlib.import_module(
                    "msvcrt"
                )  # by name: the module exists on Windows only, and a type checker on another system would not know its members

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
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
    environ: Mapping[str, str] | None = None,
) -> int:
    # an ALLOWLIST, not os.environ: a mutant run must not see a database DSN, a token or any other secret of the caller; PYTHONPATH also holds the tree root (tests may import tools.*)
    for operand in tests:  # the one place the caller's strings reach the argv: refuse here too, not only where the paths are first checked
        _plain_operand(operand)
    # ``environ`` is the snapshot that ``run_mutants`` took once at its start (see ``_env_snapshot``); a direct call without one reads ``os.environ`` now
    source = os.environ if environ is None else environ
    env = {k: source[k] for k in CHILD_ENV if k in source}
    env.update({k: source[k] for k in _checked_env_names(env_names) if k in source})
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
    forbid_skips: bool | None = None,
    throwaway_hosts: Sequence[str] = THROWAWAY_HOSTS,
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` when: the unmutated copy fails or times out; the baseline run was reaped by someone else (its exit status is unknown); the baseline skipped a test or left no readable JUnit file (``forbid_skips``); another runner holds the lock for the same database address (the lock file, see below); the lock file is not a regular file of the current user with a mode of 0600 or less, or cannot be opened or locked; a copy of the tree cannot be rebuilt for the canary run; or the canary run fails after a mutant (``CanaryFailed``, a subclass, with the rows so far in ``rows``); a call made while another is under way in the same thread is a ``RuntimeError`` too (below). A mutant whose temp copy cannot be built (after ``SETUP_TRIES`` tries) is ``(name, Verdict.ERROR, "SETUP FAILED: <error class>", False)``; a mutant run that exceeds
    ``timeout`` seconds is ``(name, Verdict.ERROR, "TIMEOUT", False)``. The unmutated baseline run gets ``baseline_timeout`` (default: ``timeout``; 0 is a real, immediate timeout and not "unset"),
    so a test can use a short mutant timeout without failing a slow baseline. ``on_result`` is called with each result as soon as that mutant
    finishes (stream it and a timeout of the whole run still leaves a kill list). Every ``tests`` and ``extra_dirs`` entry and every mutant file
    must name a file inside its tree (``ValueError``). ``first_lines``, if given, is emptied at the start and then filled with the first ``E`` line
    of each judged row that has one, masked (mutant name -> line; diagnostics, and what ``crash_type`` is checked against): it belongs to this call, so two
    runs in two threads never share it. ``conftest``, ``pass_env`` and ``forbid_skips`` are opt-in (see the module docstring; by default no plugin, no environment name and no skip check
    are added; the always-on changes in the module docstring still apply): a plugin file of the tree, allowlisted environment names for the child, and "a skipped test is an
    error, not a kill". A bad value, or a ``conftest`` that is not a file of the tree, is a ``ValueError`` before any temp folder exists. A SIGTERM or SIGHUP during the call ends it like Ctrl-C (see the module docstring).
    NOT re-entrant: the signal state is one module-level record, so on POSIX in the main thread a ``run_mutants`` call made while another is
    running in the same thread (from ``on_result``, say) raises ``RuntimeError`` and leaves the outer call untouched. Calls in other threads do not
    share that state, and each is handled by its own thread (the signal handling is then off, as the module docstring says)."""
    with _terminations_raise():
        return _run_mutants(
            root, mutants, tests, extra_dirs, only, timeout, baseline_timeout, on_result,
            {} if first_lines is None else first_lines, conftest, pass_env, forbid_skips, throwaway_hosts,
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


def _junit_text(junit: Path) -> str:
    """The text of a JUnit file, or ``""`` when there is none. Only a regular file is read (``lstat``, so a symbolic link is not followed; a FIFO
    would block the read for ever): anything else, or a file of more than ``MAX_JUNIT_CHARS`` bytes (``st_size`` counts bytes; testing.mutation counts characters, and a file has at least as many bytes as characters, so this ceiling is the stricter), is a ``ValueError``."""
    try:
        info = junit.lstat()
    except FileNotFoundError:
        return ""
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("junit path is not a regular file")
    if info.st_size > MAX_JUNIT_CHARS:  # looked at BEFORE the file is read
        raise ValueError("junit file over the ceiling")
    return junit.read_text(encoding="utf-8")


def _refuse_skips_in_baseline(junit: Path, secrets: Sequence[str] = ()) -> None:
    """``RuntimeError`` when the passing unmutated run skipped a test, or left no readable JUnit file to prove it did not (``forbid_skips``)."""
    try:
        skipped = skipped_tests(_junit_text(junit))
    except (OSError, *JUNIT_REFUSED) as exc:
        raise RuntimeError(
            f"the unmutated copy left no usable JUnit file to check for skips: {type(exc).__name__}"
        ) from None
    if skipped:
        raise RuntimeError(
            f"the unmutated copy skipped {len(skipped)} selected test(s): {[_shown_id(t, secrets) for t in skipped[:3]]}"
        )


def _baseline_failure(rc: int, junit: Path, secrets: Sequence[str]) -> str:
    """The message of a failed unmutated run: how it ended (exit code, timeout) and the first ``E`` line of its JUnit file when there is one. With a secret
    to hide (a passed name is set) the line is not shown: only its class name, as ``_shown_line`` gives it (a line of child text is a new free-text place)."""
    message = f"the unmutated copy does not pass its tests ({_run_end(rc)})"
    try:
        first = read_junit(_junit_text(junit)).first_line if junit.exists() else ""
    except (OSError, *JUNIT_REFUSED):
        first = ""
    if not first:
        return message
    if any(secrets):
        head = _leading_class(first)
        return f"{message}: {head if _IDENTIFIER.fullmatch(head) and not _shows_a_piece(head, secrets) else CLASS_HIDDEN}"
    return f"{message}: {first}"


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
        xml_text = _junit_text(junit)
        report = read_junit(xml_text) if xml_text else JunitReport("", "", [], [], False, False)
    except _UNUSABLE_JUNIT:  # refused or unreadable (a permission error, say): this mutant's ERROR, not the end of the run
        return (m.name, Verdict.ERROR, "JUNIT REFUSED", False)
    if (
        forbid_skips and not xml_text
    ):  # no record of what ran cannot prove nothing was skipped: never judged
        return (m.name, Verdict.ERROR, "JUNIT MISSING", False)
    if report.collection_failed:  # a test file that could not be imported or collected: no test ran, an assert at import time is no kill
        first_lines[m.name] = _shown_line(report.first_line, secrets)
        return (m.name, Verdict.ERROR, "COLLECTION ERROR", False)
    if report.fixture_failed:  # a fixture that failed in setup or teardown means the test never ran as written: never a kill
        first_lines[m.name] = _shown_line(report.first_line, secrets)
        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)
    if (
        forbid_skips and report.skipped
    ):  # a skipped test proves nothing: never a kill, whatever else failed in the same run
        why = (
            _shown_line(report.first_line, secrets)
            or f"skipped: {', '.join(_shown_id(t, secrets) for t in report.skipped[:3])}"
        )
        first_lines[m.name] = why
        return (m.name, Verdict.ERROR, "SKIPPED TESTS", False)
    v = judge_report(
        rc, report, expect=m.expect, pinned=m.pinned or None, crash_markers=m.crash_markers
    )
    if (
        report.first_line
    ):  # an entry only for a row that has a first ``E`` line (a kill or not), as the docstring says
        first_lines[m.name] = _shown_line(report.first_line, secrets, m.expect)
    declared = _leading_class(report.first_line) == m.crash_type
    crash_ok = v is Verdict.CRASH and m.allow_crash and declared
    # an ERROR row with no failing test id says why: exit 1 with no test named, or another exit code (usage error, internal error, a kill by the system)
    no_id = (NO_TEST_NAMED if rc == 1 else f"EXIT CODE {rc}") if v is Verdict.ERROR else ""
    shown = report.test_id or no_id
    return (
        m.name,
        v,
        _shown_id(shown, secrets) if report.test_id else shown,
        v is Verdict.KILLED or crash_ok,
    )


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
    forbid_skips: bool | None = None,
    throwaway_hosts: Sequence[str] = THROWAWAY_HOSTS,
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
    environ = _env_snapshot(env_names)  # the ONE read of the environment of this call
    secrets = _secret_values(env_names, environ)
    for env_name in env_names:  # before the lock and any temp folder: an address that is not a local, marked throwaway database is refused
        if env_name in environ:
            _refuse_unsafe_address(env_name, environ[env_name], throwaway_hosts)
    if (
        forbid_skips is None
    ):  # a passed database address implies it: a test that skips because the database is unreachable proves nothing
        forbid_skips = bool(env_names)
    canary = any(
        name in environ for name in env_names
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
    # the try starts before the lock is entered: a ``SystemExit`` right after the lock is taken (a signal, a caller) still reaches
    # ``held.close()`` in the ``finally``, so the lock is never left held until the garbage collector runs. A refusal (a path through
    # a link out of the tree, a missing ``src``) or a signal at any later point leaves no temp folder behind either
    try:
        if canary:  # before any temp folder: a second runner on the same database is refused
            held.enter_context(
                _one_run_per_database([environ[n] for n in env_names if n in environ])
            )
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
            tmp,
            tests,
            tmp / "base.xml",
            base_timeout,
            plugin=conftest,
            env_names=env_names,
            environ=environ,
        )
        if base_rc == REAPED_ELSEWHERE:
            raise RuntimeError(
                "the baseline run was reaped by someone else: its exit status is unknown"
            )
        if base_rc != 0:
            raise RuntimeError(_baseline_failure(base_rc, tmp / "base.xml", secrets))
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
            rc = _pytest(
                tmp,
                operands,
                junit,
                timeout,
                plugin=conftest,
                env_names=env_names,
                environ=environ,
            )
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
                    environ=environ,
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
