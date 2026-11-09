"""Helper for the manual Evidence workflow (.github/workflows/evidence.yml). Standard library only.

Four commands, so that the workflow YAML holds no shell logic that cannot be tested:

* ``plan``   reads INPUT_REF, INPUT_PYTHONS and INPUT_MUTANTS from the environment, refuses anything outside the
             allowlists below and writes the checked values to $GITHUB_OUTPUT. Typed input never reaches a shell.
* ``run NAME -- CMD ...``  runs CMD, copies its output to the console and to $EVIDENCE_DIR/NAME.txt (first line:
             the commit under test), appends ``NAME<TAB>exit=<code>`` to $EVIDENCE_DIR/status.txt and exits with
             CMD's own code. A command that does not exist is recorded as exit=127 and one that exists but cannot be
             started (not executable, wrong format) as exit=126, the same two codes a shell uses.
* ``report NAME ...``  prints a Markdown summary (with skipped-test counts) and exits 1 unless every NAME has exactly
             one row, that row is exit=0, and no test was skipped for a reason that names a HADAVIN_TEST_ variable or says HADAVIN_REQUIRE_PINNED_UNIDATA is required but not set. A NAME with
             no row is shown as NOT RUN (skipped, timed out or cancelled steps cannot pass); a repeated row fails. A row
             for a step that is not in the NAME list is shown too, and it fails the report unless it is exit=0.
* ``token-reader FILE``  exits 0 only if FILE has a code line (not a comment) that reads HADAVIN_TEST_VAULT_TOKEN from
             the environment; otherwise it prints the reason and exits 1.

The status file is written by the same user and in the same job as the tested code, so tested code could write a
passing row itself: the report catches mistakes (a step that did not run, a failing exit code, a hidden skip), it is not
proof against code that sets out to forge it.

Allowlists: a Python version is 3.12, 3.13 or 3.14 (the lowest is the pyproject requires-python; widen PY_RE when
the CI test matrix gains a version); a git ref is letters, digits and . _ / - only (git's own check-ref-format also bans
'..', '//', a trailing '.' or '/', and any part between slashes that starts with '.' or ends with '.lock'; this helper
also refuses a last part that is the name of a GitHub commits endpoint, see API_WORDS); a runner is
tests/<lowercase_name>_mutants.py.
"""

from __future__ import annotations

import ast
import functools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# The workflow sets EVIDENCE_DIR to a folder under the runner temp directory, outside the checkout, so that no log can
# become part of the tested tree. Without it (tests, a laptop) the folder is evidence-logs/ in the current directory.
LOG_DIR = Path(os.environ.get("EVIDENCE_DIR") or "evidence-logs")
STATUS = "status.txt"
MAX_PYTHONS = 4
MAX_MUTANTS = 8
REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
PY_RE = re.compile(r"3\.1[2-4]")  # 3.12 to 3.14: the lowest is pyproject requires-python
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
    return 0


def _head() -> str:
    git = shutil.which("git")
    if git is None:
        return "no-git"
    try:
        argv = [git, "rev-parse", "HEAD"]
        done = subprocess.run(argv, capture_output=True, text=True, check=False)  # noqa: S603  # fixed argv, no shell
    except OSError:
        return "no-git"
    return done.stdout.strip() or "no-commit"


def _record(name: str, status: str) -> None:
    with (LOG_DIR / STATUS).open("a", encoding="utf-8") as fh:
        fh.write(f"{name}\t{status}\n")


def cmd_run(name: str, command: list[str]) -> int:
    if not NAME_RE.fullmatch(name) or not command:
        raise Refused("run needs a lowercase step name and a command")
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
    code = 127  # a command that does not exist (a shell says 127)
    with (LOG_DIR / f"{name}.txt").open("w", encoding="utf-8") as fh:

        def emit(text: str) -> None:
            text = mask(text)
            fh.write(text)
            fh.flush()
            sys.stdout.write(text)
            sys.stdout.flush()

        emit(f"{_head()}\n")
        try:
            proc = subprocess.Popen(  # noqa: S603  # list argv, no shell
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
        except OSError as exc:
            if not isinstance(exc, FileNotFoundError):
                code = 126  # found but cannot be started: not executable, wrong format (a shell says 126)
            emit(f"cannot start {command[0]!r}: {exc}\n")
        else:
            for line in proc.stdout or ():
                emit(line)
            code = proc.wait()
            if code < 0:  # killed by a signal: shells show 128 + signal
                code = 128 - code
        emit(f"exit={code}\n")
    _record(name, f"exit={code}")
    return code


READ_VAR = "HADAVIN_TEST_VAULT_TOKEN"
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

    def is_name(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and node.value == READ_VAR

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and any(is_name(a) for a in node.args)
            and re.search(r"environ|getenv", ast.unparse(node.func))
        ):
            return True
        if (
            isinstance(node, ast.Subscript)
            and is_name(node.slice)
            and "environ" in ast.unparse(node.value)
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
# A skip whose reason names a HADAVIN_TEST_ variable is a missing setting, not an ordinary skip: the run fails.
HIDDEN_SKIP_WORDS = ("HADAVIN_TEST_",)
# HADAVIN_REQUIRE_PINNED_UNIDATA is set on the Python 3.13 leg only and deliberately unset on the others, where a
# test may skip and name it. Only this exact sentence (the variable is required but not set) fails the run.
PINNED_SKIP_TEXT = "HADAVIN_REQUIRE_PINNED_UNIDATA is required but not set"
NEVER = "NOT RUN (never finished: skipped, timed out or cancelled)"


def _skips(log: Path) -> tuple[int, int]:
    """(all skipped tests, skipped tests whose reason names one of HIDDEN_SKIP_WORDS)."""
    total = hidden = 0
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SKIP_RE.match(line)
        if m:
            total += int(m.group(1))
            reason = m.group(2)
            if any(word in reason for word in HIDDEN_SKIP_WORDS) or PINNED_SKIP_TEXT in reason:
                hidden += int(m.group(1))
    return total, hidden


def cmd_report(expected: list[str]) -> int:
    rows: dict[str, list[str]] = {}
    path = LOG_DIR / STATUS
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, _, status = line.partition("\t")
            rows.setdefault(name, []).append(status)
    names = list(dict.fromkeys([*expected, *rows]))
    bad = 0
    out = ["| step | result | skipped tests |", "|---|---|---|"]
    for name in names:
        found = rows.get(name, [])
        skipped = "-"
        if not found:
            result = NEVER
        elif len(found) > 1:
            result = "DUPLICATE rows: " + ", ".join(found)
        else:
            result = found[0]
        log = LOG_DIR / f"{name}.txt"
        if log.is_file():
            total, hidden = _skips(log)
            skipped = str(total)
            if hidden and result == "exit=0":
                result = f"FAIL: {hidden} test(s) skipped for a reason that names a HADAVIN_TEST_ variable or says HADAVIN_REQUIRE_PINNED_UNIDATA is required but not set"
        if result != "exit=0":
            bad += 1
        out.append(f"| {name} | {result} | {skipped} |")
    out.append("")
    for name in names:
        log = LOG_DIR / f"{name}.txt"
        if not log.is_file():
            continue
        pick = [
            ln
            for ln in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if re.match(r"(FAILED|ERROR) |\d+ (passed|failed)|exit=", ln)
        ]
        out += [f"#### {name}", "```", *pick[-40:], "```"]
    out.append("RESULT: " + (f"FAIL, {bad} step(s) not green" if bad else "all steps exit=0"))
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
        if argv[:1] == ["report"]:
            return cmd_report(argv[1:])
        if argv[:1] == ["token-reader"] and len(argv) == 2:
            return cmd_token_reader(argv[1])
    except Refused as exc:
        sys.stderr.write(f"refused: {exc}\n")
        return 2
    sys.stderr.write(
        "usage: evidence_step.py plan | run NAME -- CMD... | report NAME... | token-reader FILE\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
