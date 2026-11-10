"""Helper for the manual Evidence workflow (.github/workflows/evidence.yml). Standard library only.

Commands, so that the workflow YAML holds no shell logic that cannot be tested:

* ``plan``   reads INPUT_REF, INPUT_PYTHONS and INPUT_MUTANTS from the environment, refuses anything outside the
             allowlists below and writes the checked values to $GITHUB_OUTPUT. Typed input never reaches a shell.
* ``run NAME -- CMD ...``  runs CMD, copies its output to the console and to $EVIDENCE_DIR/NAME.txt (first lines: the
             commit under test, where the workflow file came from, and which test settings are present), appends
             ``NAME<TAB>exit=<code>`` to $EVIDENCE_DIR/status.txt and exits with CMD's own code. A command that does
             not exist is recorded as exit=127 and one that exists but cannot be started (not executable, wrong
             format) as exit=126, the same two codes a shell uses.
* ``outcome NAME``  records a step that is not run through ``run`` (the Vault start): exit=0 if $OUTCOME is
             ``success``, otherwise exit=1.
* ``facts``  writes the runner facts (commit, Python, CPU count, workflow origin, which test settings are present) to
             $EVIDENCE_DIR/env.txt through the masking.
* ``report NAME ...``  prints a Markdown summary (passed, skipped and deselected test counts) and exits 1 unless every
             NAME has exactly one row, that row is exit=0, no test was skipped for a reason that is not on
             ALLOWED_SKIPS, and a test step ran at least as many tests as FLOORS says. A NAME with no row is shown as
             NOT RUN (skipped, timed out or cancelled steps cannot pass); a repeated row fails. A row for a step that
             is not in the NAME list is shown too, and it fails the report unless it is exit=0.
* ``token-reader FILE``  exits 0 only if FILE has a code line (not a comment) that reads HADAVIN_TEST_VAULT_TOKEN from
             the environment; otherwise it prints the reason and exits 1.

The status file is written by the same user and in the same job as the tested code, so tested code could write a
passing row itself: the report catches mistakes (a step that did not run, a failing exit code, a skip, a shrunken
run), it is not proof against code that sets out to forge it. The same holds for this helper when the workflow is
started from a branch: GitHub attributes the run to that branch and commit, and the helper records both (see
provenance) so that a reader can see the run did not come from the default branch.

Allowlists: a Python version is one of PYTHONS (the lowest is the pyproject requires-python, a test checks it); a git
ref is letters, digits and . _ / - only (git's own check-ref-format also bans '..', '//', a trailing '.' or '/', and
any part between slashes that starts with '.' or ends with '.lock'; this helper also refuses a last part that is the
name of a GitHub commits endpoint, see API_WORDS); a runner is tests/<lowercase_name>_mutants.py.
"""

from __future__ import annotations

import ast
import asyncio
import functools
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# The workflow sets EVIDENCE_DIR to a folder under the runner temp directory, outside the checkout, so that no log can
# become part of the tested tree. Without it (tests, a laptop) the folder is evidence-logs/ in the current directory.
LOG_DIR = Path(os.environ.get("EVIDENCE_DIR") or "evidence-logs")
STATUS = "status.txt"
MAX_PYTHONS = 4
MAX_MUTANTS = 8
REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
PYTHONS = ("3.12", "3.13", "3.14")  # the lowest is pyproject requires-python (a test compares them)
PY_RE = re.compile("|".join(re.escape(v) for v in PYTHONS))
MUTANT_RE = re.compile(r"tests/[a-z0-9_]{1,40}_mutants\.py")  # step name extra-<stem> fits NAME_RE
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,60}")
# A step called "status" would write its log to status.txt, the file of the result rows, and wipe them.
RESERVED_NAMES = {STATUS.removesuffix(".txt")}
# The workflow asks GitHub for repos/<repo>/commits/<ref>. A ref that ends in one of these words would instead reach
# another endpoint under the commit (for example commits/main/status, which also answers with a sha).
API_WORDS = {
    "status",
    "statuses",
    "check-runs",
    "check-suites",
    "comments",
    "branches-where-head",
    "pulls",
}


def _checked_argv(argv: Sequence[str]) -> list[str]:
    if (
        isinstance(argv, str)
        or not argv
        or not all(isinstance(a, str) and "\0" not in a for a in argv)
        or not argv[0]
    ):
        raise ValueError("a command is a non-empty list of strings whose first item is not empty")
    return list(argv)


# A process is started in this one place (two functions below), through asyncio, which hands the argument list to the
# operating system without a shell. The list is checked first (never a shell string, no NUL, a program name).
# There is no lint suppression: ruff's rule for the subprocess module (S603) is about that module, and a started
# process that reads this list is the whole job of `run`, so the module is not used at all (a test checks both).
CHUNK = 1 << 16  # bytes read at a time from a child's output
# A line longer than this many bytes is passed on in pieces, so one huge line cannot fill memory.
MAX_PENDING_LINE = 1 << 20


async def _stream_fixed(
    argv: Sequence[str],
    on_text: Callable[[str], None],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: dict[str, str] | None = None,
) -> int:
    """Start argv (stderr joined to stdout), pass its output to on_text one complete line at a time (a piece of a
    line only when the line is longer than MAX_PENDING_LINE) and return its exit code. A command that cannot be
    started raises OSError (FileNotFoundError when it does not exist)."""
    proc = await asyncio.create_subprocess_exec(
        *_checked_argv(argv),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
        env=env,
    )
    if proc.stdout is None:  # cannot happen with PIPE; keeps the type checker and a reader sure
        raise RuntimeError("no output pipe")
    pending = b""
    while chunk := await proc.stdout.read(CHUNK):
        pending += chunk
        *lines, pending = pending.split(b"\n")
        for line in lines:
            on_text(line.decode("utf-8", errors="replace") + "\n")
        if len(pending) > MAX_PENDING_LINE:
            on_text(pending.decode("utf-8", errors="replace"))
            pending = b""
    if pending:
        on_text(pending.decode("utf-8", errors="replace"))
    return await proc.wait()


async def _run_fixed(
    argv: Sequence[str],
    cwd: str | os.PathLike[str] | None,
    env: dict[str, str] | None,
) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        *_checked_argv(argv),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    out, err = await proc.communicate()
    return proc.returncode if proc.returncode is not None else 1, out, err


def run_fixed(
    argv: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command to its end and return its exit code and its captured output (text)."""
    _checked_argv(argv)  # refuse a bad list before any event loop exists
    code, out, err = asyncio.run(_run_fixed(argv, cwd, env))
    return subprocess.CompletedProcess(
        list(argv),
        code,
        out.decode("utf-8", errors="replace"),
        err.decode("utf-8", errors="replace"),
    )


SECRET_ENV = (
    "HADAVIN_TEST_VAULT_TOKEN",
)  # values that must never reach a log file, the artifact or the summary
MASK = "***"
MIN_PIECE = 8


@functools.lru_cache(maxsize=8)
def _pattern(value: str) -> re.Pattern[str]:
    """One compiled pattern per secret value (the longest piece first), built once and not for every output line."""
    pieces = {value}
    for size in range(MIN_PIECE, len(value)):
        pieces.add(value[:size])
        pieces.add(value[-size:])
    return re.compile("|".join(re.escape(p) for p in sorted(pieces, key=len, reverse=True)))


def mask(text: str) -> str:
    """Replace the value of every secret environment variable, and every piece of it of at least 8 characters taken
    from its start or its end, with ***.

    `::add-mask::` hides a value only in the live Actions log; the files in the evidence folder are uploaded as an
    artifact and the summary is a separate page, so the helper must remove the value itself. Pieces cover a value
    that a tool cut off at a line width. A value split by a line break in the middle, or changed (for example
    encoded), is NOT recognised: this is best effort for plain text, which is what a test run prints."""
    for name in SECRET_ENV:
        value = os.environ.get(name, "")
        if len(value) < MIN_PIECE:
            continue
        text = _pattern(value).sub(MASK, text)
    return text


class Refused(ValueError):
    """An input is outside the allowlist."""


PULL_REF_RE = re.compile(r"(refs/)?pull/.*")


def check_ref(ref: str) -> str:
    if PULL_REF_RE.fullmatch(ref):
        raise Refused(
            "ref refused: pull/N/head (and refs/pull/...) is not supported, pass the branch name or the commit SHA"
        )
    parts = ref.split("/")
    if (
        not REF_RE.fullmatch(ref)
        or ".." in ref
        or "//" in ref
        or ref.endswith((".", "/"))
        or any(p.startswith(".") or p.endswith(".lock") for p in parts)
    ):
        raise Refused(
            f"ref refused (letters, digits, . _ / - only, no '..'; pull/N/head is not supported, pass the branch or commit): {ref[:60]!r}"
        )
    if parts[-1] in API_WORDS and len(parts) > 1:
        raise Refused(
            f"ref refused: its last part {parts[-1]!r} is the name of a GitHub commits endpoint; pass the commit SHA"
        )
    return ref


def check_pythons(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Refused(f"pythons is not JSON: {exc}") from None
    if not isinstance(value, list) or not value or len(value) > MAX_PYTHONS:
        raise Refused(f"pythons must be a list of 1 to {MAX_PYTHONS} version strings")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not PY_RE.fullmatch(item):
            raise Refused(
                f"python version refused (only 3.12 to 3.14, like 3.13): {str(item)[:20]!r}"
            )
        if item not in out:
            out.append(item)
    return out


def check_mutants(raw: str) -> list[str]:
    names = raw.split()
    if len(names) > MAX_MUTANTS:
        raise Refused(f"at most {MAX_MUTANTS} extra mutant runners")
    for name in names:
        if not MUTANT_RE.fullmatch(name):
            raise Refused(f"runner name refused (need tests/<name>_mutants.py): {name[:60]!r}")
    return list(dict.fromkeys(names))


def cmd_plan(env: dict[str, str]) -> int:
    ref = check_ref(env.get("INPUT_REF", ""))
    pythons = check_pythons(env.get("INPUT_PYTHONS", ""))
    mutants = check_mutants(env.get("INPUT_MUTANTS", ""))
    lines = {"pythons": json.dumps(pythons), "mutants": " ".join(mutants), "ref": ref}
    text = "".join(f"{k}={v}\n" for k, v in lines.items())
    target = env.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"{provenance()}\n\n")
    return 0


def _head() -> str:
    git = shutil.which("git")
    if git is None:
        return "no-git"
    try:
        done = run_fixed([git, "rev-parse", "HEAD"])
    except OSError:
        return "no-git"
    return done.stdout.strip() or "no-commit"


# Settings whose presence decides what the tests do (a test that needs one skips or uses an in-process fake when it is
# missing). The log records only set or unset, never a value.
RECORDED_ENV = (
    "HADAVIN_TEST_PG_DSN",
    "HADAVIN_TEST_VAULT_ADDR",
    "HADAVIN_TEST_VAULT_TOKEN",
    "COLUMNS",
    "PYTHONUNBUFFERED",
)


def env_facts() -> str:
    flags = ", ".join(f"{n}={'set' if os.environ.get(n) else 'unset'}" for n in RECORDED_ENV)
    return f"settings: {flags}; python {sys.version.split()[0]} on {sys.platform}"


def provenance() -> str:
    """Where the workflow file and this helper came from. A manual run executes the workflow file of the branch it was
    started from, so a run started from a feature branch used that branch's workflow and helper, not the default
    branch's. GitHub fills GITHUB_REF and GITHUB_SHA (the branch and its latest commit at the start); the workflow
    passes DEFAULT_BRANCH. The text is written into every step log, the runner facts and the summary."""
    ref = os.environ.get("GITHUB_REF", "")
    sha = os.environ.get("GITHUB_SHA", "")
    default = os.environ.get("DEFAULT_BRANCH", "")
    if not (ref and sha and default):
        return "workflow origin: not recorded (not run by GitHub Actions)"
    where = (
        "the default branch"
        if ref == f"refs/heads/{default}"
        else f"NOT the default branch ({default}): this run used that branch's workflow and helper"
    )
    return f"workflow origin: {ref} at commit {sha}, {where}"


def from_other_branch() -> bool:
    """True only when GitHub's values are present and the workflow did not come from the default branch."""
    ref, default = os.environ.get("GITHUB_REF", ""), os.environ.get("DEFAULT_BRANCH", "")
    return bool(ref and default and os.environ.get("GITHUB_SHA") and ref != f"refs/heads/{default}")


def _record(name: str, status: str) -> None:
    with (LOG_DIR / STATUS).open("a", encoding="utf-8") as fh:
        fh.write(f"{name}\t{status}\n")


def _open_step(name: str) -> Path:
    """Check a step name (lowercase, not reserved, not used before in this run) and return the path of its log."""
    if not NAME_RE.fullmatch(name):
        raise Refused("a step needs a lowercase name")
    if name in RESERVED_NAMES:
        raise Refused(f"step name {name!r} is reserved (its log would be the result file)")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    status_file = LOG_DIR / STATUS
    if status_file.is_file() and any(
        line.partition("\t")[0] == name
        for line in status_file.read_text(encoding="utf-8").splitlines()
    ):
        raise Refused(
            f"step name {name!r} was already used in this run (a log would be overwritten)"
        )
    return LOG_DIR / f"{name}.txt"


def cmd_run(name: str, command: list[str]) -> int:
    if not command or not command[0]:
        raise Refused("run needs a command")
    log = _open_step(name)
    code = 127  # a command that does not exist (a shell says 127)
    with log.open("w", encoding="utf-8") as fh:
        # A child that prints no final newline must not get "exit=" glued to its last line.
        ended_line = [True]

        def emit(text: str) -> None:
            text = mask(text)
            if text:
                ended_line[0] = text.endswith("\n")
            fh.write(text)
            fh.flush()
            sys.stdout.write(text)
            sys.stdout.flush()

        emit(f"{_head()}\n{provenance()}\n{env_facts()}\n")
        try:
            code = asyncio.run(_stream_fixed(command, emit))
        except OSError as exc:
            if not isinstance(exc, FileNotFoundError):
                code = 126  # found but cannot be started: not executable, wrong format (a shell says 126)
            emit(f"cannot start {command[0]!r}: {exc}\n")
        else:
            if code < 0:  # killed by a signal: shells show 128 + signal
                code = 128 - code
        emit(("" if ended_line[0] else "\n") + f"exit={code}\n")
    _record(name, f"exit={code}")
    return code


def cmd_outcome(name: str, env: dict[str, str]) -> int:
    """Record a step that does not run through ``run`` (the Vault start): exit=0 only if $OUTCOME is ``success``. A
    step that failed, was skipped or was cancelled has another outcome and gets exit=1, so the verdict shows it."""
    log = _open_step(name)
    outcome = env.get("OUTCOME", "")
    code = 0 if outcome == "success" else 1
    text = mask(f"{provenance()}\noutcome={outcome or 'missing'}\nexit={code}\n")
    log.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    _record(name, f"exit={code}")
    return code


def cmd_facts() -> int:
    """Write the runner facts to env.txt (through the masking) and to the console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    text = mask(f"{_head()}\n{provenance()}\n{env_facts()}\ncpus {os.cpu_count()}\n")
    (LOG_DIR / "env.txt").write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


READ_VAR = "HADAVIN_TEST_VAULT_TOKEN"
# The exact ways to read one variable: `pop`, `setdefault`, `get` on another mapping or a call that merely has
# "environ" in its name are not reads of the process environment.
READ_CALLS = {"os.environ.get", "os.getenv", "environ.get", "getenv"}
READ_MAPS = {"os.environ", "environ"}
READER_RE = re.compile(
    r"^[^#]*(environ|getenv)[^#]*" + READ_VAR
)  # fallback for a file that does not parse


def _reads_token(source: str) -> bool:
    """True if the code reads the token from the environment: a call such as os.environ.get("NAME") or
    os.getenv("NAME"), or os.environ["NAME"], written on one line or several. Comments, docstrings and other strings
    do not count. A file that does not parse falls back to a one-line text match."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return any(READER_RE.match(line) for line in source.splitlines())

    # A module or function can name the variable once and read it by that name: NAME = "HADAVIN_TEST_VAULT_TOKEN".
    names = {
        t.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and isinstance(node.value, ast.Constant)
        and node.value.value == READ_VAR
        for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(t, ast.Name)
    }

    def is_name(node: ast.AST) -> bool:
        return (isinstance(node, ast.Constant) and node.value == READ_VAR) or (
            isinstance(node, ast.Name) and node.id in names
        )

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and node.args
            and is_name(node.args[0])
            and ast.unparse(node.func) in READ_CALLS
        ):
            return True
        if (
            isinstance(node, ast.Subscript)
            and is_name(node.slice)
            and ast.unparse(node.value) in READ_MAPS
        ):
            return True
    return False


def cmd_token_reader(path: str) -> int:
    """Exit 0 only if the file has a code line that reads the per-run Vault token. Prints the reason when it has not,
    so the saved log of the step says why the run stopped."""
    try:
        source = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        sys.stdout.write(f"cannot read {path}: {exc}\n")
        return 1
    if _reads_token(source):
        sys.stdout.write(f"{path} reads HADAVIN_TEST_VAULT_TOKEN\n")
        return 0
    sys.stdout.write(
        f"{path} has no code line that reads HADAVIN_TEST_VAULT_TOKEN from the environment: the tested ref is older "
        "than this workflow and would send a fixed token to a server that has a random one (its Vault tests would "
        "fail with a 403). Test a newer ref.\n"
    )
    return 1


SKIP_RE = re.compile(r"SKIPPED \[(\d+)\] (.*)")
SKIP_WHERE_RE = re.compile(r"(?P<path>[^:]+):\d+: (?P<reason>.*)", re.DOTALL)
NEVER = "NOT RUN (never finished: skipped, timed out or cancelled)"


def _always() -> bool:
    return True


def _on_windows() -> bool:
    return os.name == "nt"


def _without_bash() -> bool:
    return shutil.which("bash") is None


# The skips that may appear in the pytest and performance logs: (test file, exact reason, when it may happen, how many).
# Every other skip fails the run: a missing HADAVIN_TEST_ setting, a missing program (psql, docker), a missing extra
# (importorskip), a changed marker. The first entry is the whole baseline on the evidence runner (one test, run for the
# Bedrock kind only); the other three are the guard tests that cannot run on Windows or without bash, so on the
# Linux runner they never skip and a skip there fails the run.
ALLOWED_SKIPS: tuple[tuple[str, str, Callable[[], bool], int], ...] = (
    (
        "tests/contracts/test_llm.py",
        "Stubber refuses a malformed Converse shape before the kind sees it",
        _always,
        1,
    ),
    (
        "tests/test_evidence_workflow_guard.py",
        "the execute bit is a POSIX notion",
        _on_windows,
        1,
    ),
    (
        "tests/test_evidence_workflow_guard.py",
        "bash needed for the exit-code check",
        _without_bash,
        1,
    ),
    (
        "tests/test_evidence_workflow_guard.py",
        "bash needed for the exit-code lesson",
        _without_bash,
        1,
    ),
)
# The fewest tests (passed, failed, errored and skipped, not deselected) a test step must run. A run that selects
# fewer (a changed addopts, a --deselect, a marker edit, a deleted test) fails. The numbers are the count at the head
# the workflow was last checked at (`pytest --collect-only -q` with the step's own -m); raise them when tests are
# added, lower them only for tests that were deliberately removed. This is the only place that holds them.
FLOORS = {"pytest": 10910, "perf": 28}
SUMMARY_RE = re.compile(r"^(?:=+ )?((?:\d+ [a-z]+(?:, )?)+) in \d+(?:\.\d+)?s\b")
COUNT_NAMES = {"error": "errors", "warning": "warnings"}
SKIP_FAIL = "skipped for a reason that is not on the allowed list"
FLOOR_FAIL = "fewer tests ran than the recorded floor"
NO_SUMMARY = "no pytest summary line to count the tests from"


def _skip_problems(log: Path) -> tuple[int, list[str]]:
    """(all skipped tests, descriptions of the skips that are not allowed). A line that does not parse as
    ``path:line: reason`` is not allowed either."""
    seen: dict[tuple[str, str], int] = {}
    total = 0
    bad: list[str] = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SKIP_RE.match(line)
        if not m:
            continue
        count = int(m.group(1))
        total += count
        where = SKIP_WHERE_RE.fullmatch(m.group(2))
        if not where:
            bad.append(f"{count} x unreadable skip line: {m.group(2)[:60]}")
            continue
        key = (where["path"].replace("\\", "/"), where["reason"].strip())
        seen[key] = seen.get(key, 0) + count
    for (path, reason), count in seen.items():
        allowed = [
            limit for p, r, when, limit in ALLOWED_SKIPS if (p, r) == (path, reason) and when()
        ]
        if not allowed or count > max(allowed):
            bad.append(f"{count} x {path}: {reason[:60]}")
    return total, bad


def parse_summary(text: str) -> dict[str, int] | None:
    """The counts of pytest's last summary line ("10838 passed, 1 skipped, 28 deselected in 388.62s"), also for a run
    with only skips or only errors ("3 skipped in 0.1s", "1 error in 0.2s"); None if there is no such line."""
    found: dict[str, int] | None = None
    for line in text.splitlines():
        m = SUMMARY_RE.match(line)
        if m:
            found = {}
            for part in m.group(1).split(", "):
                number, _, word = part.partition(" ")
                word = COUNT_NAMES.get(word, word)
                found[word] = found.get(word, 0) + int(number)
    return found


def selected(counts: dict[str, int]) -> int:
    return sum(
        counts.get(k, 0) for k in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed")
    )


def cmd_report(expected: list[str]) -> int:
    rows: dict[str, list[str]] = {}
    path = LOG_DIR / STATUS
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, _, status = line.partition("\t")
            rows.setdefault(name, []).append(status)
    names = list(dict.fromkeys([*expected, *rows]))
    bad = 0
    out = [
        provenance(),
        "",
        "| step | result | passed | skipped | deselected |",
        "|---|---|---|---|---|",
    ]
    for name in names:
        found = rows.get(name, [])
        passed = skipped = deselected = "-"
        if not found:
            result = NEVER
        elif len(found) > 1:
            result = "DUPLICATE rows: " + ", ".join(found)
        else:
            result = found[0]
        log = LOG_DIR / f"{name}.txt"
        if log.is_file():
            total, problems = _skip_problems(log)
            counts = parse_summary(log.read_text(encoding="utf-8", errors="replace"))
            if counts is not None:
                passed = str(counts.get("passed", 0))
                deselected = str(counts.get("deselected", 0))
                skipped = str(counts.get("skipped", 0))
            elif total:
                skipped = str(total)
            if problems and result == "exit=0":
                result = f"FAIL: {SKIP_FAIL}: " + "; ".join(problems[:3])
            if name in FLOORS and result == "exit=0":
                if counts is None:
                    result = f"FAIL: {NO_SUMMARY}"
                elif selected(counts) < FLOORS[name]:
                    result = f"FAIL: {FLOOR_FAIL}: {selected(counts)} ran, floor {FLOORS[name]}"
        if result != "exit=0":
            bad += 1
        out.append(f"| {name} | {result} | {passed} | {skipped} | {deselected} |")
    out.append("")
    for name in names:
        log = LOG_DIR / f"{name}.txt"
        if not log.is_file():
            continue
        pick = [
            ln
            for ln in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if re.match(r"(FAILED|ERROR) |\d+ [a-z]+(, \d+ [a-z]+)* in |exit=", ln)
        ]
        out += [f"#### {name}", "```", *pick[-40:], "```"]
    out.append("RESULT: " + (f"FAIL, {bad} step(s) not green" if bad else "all steps exit=0"))
    if from_other_branch():
        out.append(
            "NOTE: this run did not use the default branch's workflow and helper (see the first line); it shows what "
            "that branch's workflow did, not what the default branch's would do."
        )
    text = mask("\n".join(out) + "\n")
    sys.stdout.write(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text)
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    try:
        if argv[:1] == ["plan"]:
            return cmd_plan(dict(os.environ))
        if argv[:1] == ["run"] and len(argv) >= 4 and argv[2] == "--":
            return cmd_run(argv[1], argv[3:])
        if argv[:1] == ["outcome"] and len(argv) == 2:
            return cmd_outcome(argv[1], dict(os.environ))
        if argv[:1] == ["facts"] and len(argv) == 1:
            return cmd_facts()
        if argv[:1] == ["report"]:
            return cmd_report(argv[1:])
        if argv[:1] == ["token-reader"] and len(argv) == 2:
            return cmd_token_reader(argv[1])
    except Refused as exc:
        sys.stderr.write(f"refused: {exc}\n")
        return 2
    sys.stderr.write(
        "usage: evidence_step.py plan | run NAME -- CMD... | outcome NAME | facts | report NAME... | token-reader FILE\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
