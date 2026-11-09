"""Helper for the manual Evidence workflow (.github/workflows/evidence.yml). Standard library only.

Three commands, so that the workflow YAML holds no shell logic that cannot be tested:

* ``plan``   reads INPUT_REF, INPUT_PYTHONS and INPUT_MUTANTS from the environment, refuses anything outside the
             allowlists below and writes the checked values to $GITHUB_OUTPUT. Typed input never reaches a shell.
* ``run NAME -- CMD ...``  runs CMD, copies its output to the console and to evidence-logs/NAME.txt (first line:
             the commit under test), appends ``NAME<TAB>exit=<code>`` to evidence-logs/status.txt and exits with
             CMD's own code. A command that cannot start is recorded as exit=127 (same as a shell).
* ``report NAME ...``  prints a Markdown summary and exits 1 unless every NAME has a row with exit=0. A NAME with
             no row is shown as NOT RUN (a skipped or never-reached step cannot pass).

Allowlists: a Python version is dotted numbers 3.<minor> with minor at least 12 (pyproject requires-python); a
git ref is letters, digits and . _ / - only (git's own check-ref-format also bans '..', '//', a trailing '.' or '/'
and '.lock'); a runner is tests/<lowercase_name>_mutants.py.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

LOG_DIR = Path("evidence-logs")
STATUS = "status.txt"
MAX_PYTHONS = 4
MAX_MUTANTS = 8
MIN_MINOR = 12  # pyproject: requires-python >= 3.12
REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")
PY_RE = re.compile(r"3\.[0-9]+")
MUTANT_RE = re.compile(r"tests/[a-z0-9_]+_mutants\.py")
NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,60}")


class Refused(ValueError):
    """An input is outside the allowlist."""


def check_ref(ref: str) -> str:
    if not REF_RE.fullmatch(ref) or ".." in ref or "//" in ref or ref.endswith((".", "/", ".lock")):
        raise Refused(f"ref refused (letters, digits, . _ / - only, no '..'): {ref[:60]!r}")
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
        if (
            not isinstance(item, str)
            or not PY_RE.fullmatch(item)
            or int(item.split(".")[1]) < MIN_MINOR
        ):
            raise Refused(
                f"python version refused (need 3.{MIN_MINOR} or newer, like 3.13): {str(item)[:20]!r}"
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
    LOG_DIR.mkdir(exist_ok=True)
    code = 127
    with (LOG_DIR / f"{name}.txt").open("w", encoding="utf-8") as fh:

        def emit(text: str) -> None:
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


def cmd_report(expected: list[str]) -> int:
    rows: dict[str, str] = {}
    path = LOG_DIR / STATUS
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, _, status = line.partition("\t")
            rows[name] = status
    names = list(dict.fromkeys([*expected, *rows]))
    bad = 0
    out = ["| step | result |", "|---|---|"]
    for name in names:
        status = rows.get(name, "NOT RUN")
        if status != "exit=0":
            bad += 1
        out.append(f"| {name} | {status} |")
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
    text = "\n".join(out) + "\n"
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
    except Refused as exc:
        sys.stderr.write(f"refused: {exc}\n")
        return 2
    sys.stderr.write("usage: evidence_step.py plan | run NAME -- CMD... | report NAME...\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
