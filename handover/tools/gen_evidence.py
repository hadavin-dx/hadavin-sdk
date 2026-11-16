#!/usr/bin/env python3
"""gen_evidence: run the evidence cells of one package at one head and write the evidence table.

RECONSTRUCTED. The original script (called "gen_evidence" in handover/evidence/P6a/d15e53a-cloud2/TABLE.md and in
handover/CLOUD-RESUME-2026-11-09.md) is lost; no copy of its text exists. What is KNOWN: it wrote the "hygiene cell"
(`tools/scan_repo.py`, rc 0, empty output) and the table `command | python | inner rc | counts | log` that the two
evidence READMEs show (handover/evidence/P6a/d15e53a-cloud2/TABLE.md, handover/evidence/P3a-2/2b0941b-cloud2/README.md),
with one log per cell whose first line names the head and whose last line is `exit=<inner rc>`.
Everything else below is RECONSTRUCTED from those two tables and from `.github/workflows/ci.yml`.

It only RECORDS raw output. It never says passed, failed, green or clean; the "inner rc not 0 / not run" list at the top
of the table is a mechanical list of rows, not a verdict. Judging is done by a reviewer who reads the logs.

Ambiguous items and the interpretation chosen:
  * "hygiene cell": read as `python tools/scan_repo.py` run at the head (secrets and banned names in tracked files;
    counts = number of hit lines, the matched text is never printed by that tool). LEAD-ORDERS also mentions "the
    evidence-p6a hygiene cell regex" without saying what was wrong; that is NOT reconstructed. As an addition, a second
    row `hygiene of the evidence logs` applies the PATTERNS dict of the root's own tools/scan_repo.py (imported, read
    only) to the cell logs written here and prints path:line:rule only.
  * "the cells the ticket defines": the standard cells are those of ci.yml (ruff check, ruff format --check, bandit,
    scan_repo, full suite, perf, stage mutants); the per-ticket extras are in TICKETS below. The P6a extras follow
    TABLE.md of d15e53a-cloud2 (client-profile file, the two Postgres files). The P3a-2 extras follow the README of
    2b0941b-cloud2 plus the reconstructed 66-mutant runner. The ticket file is read (handover/tickets/<id>.md) only to
    record that it exists and its size; its text is not parsed. Any other cell is added with --extra.
  * bandit is not in the test venv; it runs as `uvx bandit` unless --bandit gives another command (TABLE.md of
    d15e53a-cloud2 records the same deviation). Scope as ci.yml: `-q -r src demos tools -ll`.
  * Ruff scope is `src tests demos tools` (ci.yml); the d15e53a table used `src tests demos`; ci.yml wins.
  * Environment: variables whose names start with AWS_, AZURE_, GOOGLE_, GCP_, ANTHROPIC_, OPENAI_ are removed for
    every cell (repo rule: tests run with no cloud configuration). PYTHONPATH is set to <root>/src because the
    venvs here are editable installs of ANOTHER worktree; each pytest python's import path is checked and recorded.
    HADAVIN_REQUIRE_PINNED_UNIDATA=1 is set on 3.13 full-suite cells only (as ci.yml).
  * The heavy-slot wrapper of the old laptop (heavy_slot.py) does not exist here; cells run one after the other.
  * Cells that need a tool that is missing are written as NOT RUN with the reason, not skipped silently.

Usage:
    python gen_evidence.py TICKET HEAD --root WORKTREE --venv313 DIR [--venv312 DIR] --out DIR
           [--handover DIR] [--pys 3.13,3.12] [--skip id,id] [--only id,id] [--extra "label|py|command" ...]
           [--bandit "uvx bandit"] [--timeout SECONDS] [--list]
Exit 0 when the table was written (whatever the cells returned); 2 for a usage problem or a head that does not match.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

CLOUD_PREFIXES = ("AWS_", "AZURE_", "GOOGLE_", "GCP_", "ANTHROPIC_", "OPENAI_")
HERE = Path(__file__).resolve().parent


@dataclass
class Cell:
    id: str
    label: str  # the command as the table prints it
    py: str | None  # "3.13", "3.12" or None (no python version applies)
    argv: list[str] | None  # None = cannot run (see why)
    kind: str  # lint | format | bandit | hygiene | pytest | mutants
    env: dict[str, str] = field(default_factory=dict)
    why_not: str = ""
    note: str = ""


@dataclass
class Row:
    cell: Cell
    rc: str  # "0", "1", ..., "timeout", "NOT RUN"
    counts: str
    log: str


def pyexe(venv: Path | None) -> str | None:
    return str(venv / "bin" / "python") if venv and (venv / "bin" / "python").exists() else None


def build_cells(ticket: str, root: Path, venvs: dict[str, Path], pys: list[str], bandit_cmd: list[str]) -> list[Cell]:
    cells: list[Cell] = []
    top = pys[0] if pys else "3.13"
    p_top = pyexe(venvs.get(top))

    def tool(name: str):
        v = venvs.get(top)
        return str(v / "bin" / name) if v and (v / "bin" / name).exists() else shutil.which(name)

    def need(argv, why):
        return (argv, "") if argv and argv[0] else (None, why)

    ruff = tool("ruff")
    a, w = need([ruff, "check", "src", "tests", "demos", "tools"] if ruff else None, "ruff not found")
    cells.append(Cell("ruff-check", "ruff check src tests demos tools", top, a, "lint", why_not=w))
    a, w = need([ruff, "format", "--check", "src", "tests", "demos", "tools"] if ruff else None, "ruff not found")
    cells.append(Cell("ruff-format", "ruff format --check src tests demos tools", top, a, "format", why_not=w))
    cells.append(Cell("bandit", "bandit -q -r src demos tools -ll", top,
                      [*bandit_cmd, "-q", "-r", "src", "demos", "tools", "-ll"], "bandit",
                      note="" if bandit_cmd == ["bandit"] else f"bandit run as `{' '.join(bandit_cmd)}`"))
    cells.append(Cell("hygiene", "python tools/scan_repo.py (hygiene cell)", top,
                      [p_top, "tools/scan_repo.py"] if p_top and (root / "tools/scan_repo.py").exists() else None,
                      "hygiene", why_not="tools/scan_repo.py or python missing"))

    def pytest_cell(cid, label, py, args, extra_env=None, note=""):
        exe = pyexe(venvs.get(py))
        return Cell(cid, label, py, [exe, "-m", "pytest", *args] if exe else None, "pytest",
                    env=extra_env or {}, why_not=f"no venv for python {py}", note=note)

    for py in pys:
        unidata = {"HADAVIN_REQUIRE_PINNED_UNIDATA": "1"} if py == "3.13" else {}
        cells.append(pytest_cell(f"full-{py}", 'pytest -q -m "not live and not perf" -rs', py,
                                 ["-q", "-m", "not live and not perf", "-rs"], unidata))
    for py in pys:
        cells.append(pytest_cell(f"perf-{py}", "pytest -q -m perf -rs", py, ["-q", "-m", "perf", "-rs"]))
    if (root / "tests/stage_mutants.py").exists():
        cells.append(Cell("stage-mutants", "python tests/stage_mutants.py", top,
                          [p_top, "tests/stage_mutants.py"] if p_top else None, "mutants",
                          why_not="no python"))

    if ticket.startswith("P6a"):
        for py in pys:
            cells.append(pytest_cell(f"p6a1-client-profile-{py}", "pytest tests/test_client_profile.py -q -rA", py,
                                     ["tests/test_client_profile.py", "-q", "-rA"]))
        for py in pys:
            cells.append(pytest_cell(f"p6a1-pg-{py}", "pytest tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py -q -rA",
                                     py, ["tests/test_k3_pilot_env.py", "tests/test_k5_round8_postgres.py", "-q", "-rA"]))
    if ticket.startswith("P3a"):
        files = sorted(str(p.relative_to(root)) for p in (root / "tests").glob("test_migration_*.py"))
        for py in pys:
            cells.append(pytest_cell(f"p3a-migration-tests-{py}", "pytest tests/test_migration_*.py -q -rA", py,
                                     [*files, "-q", "-rA"]))
        if (root / "tests/migration_numbers_mutants.py").exists():
            cells.append(Cell("p3a1-mutants", "python tests/migration_numbers_mutants.py (P3a-1)", top,
                              [p_top, "tests/migration_numbers_mutants.py"] if p_top else None, "mutants",
                              why_not="no python"))
        runner = HERE / "p3a2_mutants.py"
        if ticket.startswith("P3a-2"):
            cells.append(Cell("p3a2-mutants", "p3a2_mutants.py (P3a-2, 66 mutants; plants into the tree, runs last)", top,
                              [p_top, str(runner), "--root", str(root), "--python", p_top] if p_top and runner.exists() else None,
                              "mutants", why_not="p3a2_mutants.py or python missing"))
    return cells


def parse_counts(kind: str, text: str, rc: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body = [ln for ln in lines if not ln.startswith(("exit=", "$ ")) and not re.fullmatch(r"[0-9a-f]{40}", ln)]
    if kind == "pytest":
        for ln in reversed(body):
            if re.search(r"\b(passed|failed|error|errors|skipped|deselected|no tests ran)\b", ln) and " in " in ln:
                return re.sub(r"\s+in\s+[\d.]+s.*$", "", ln.strip("= ")).strip()
        return "no pytest summary line"
    if kind == "lint":
        return next((ln for ln in reversed(body) if "All checks passed" in ln or "Found " in ln), "no summary line")
    if kind == "format":
        return next((ln for ln in reversed(body) if "formatted" in ln or "would reformat" in ln), "no summary line")
    if kind == "bandit":
        issues = sum(1 for ln in body if ln.startswith(">> Issue:"))
        return "no issue lines" if issues == 0 else f"{issues} issue lines"
    if kind == "hygiene":
        hits = [ln for ln in body if re.match(r"\S+:\d+: ", ln)]
        return "no hits" if not hits and not body else f"{len(hits)} hit lines"
    if kind == "mutants":
        return next((ln for ln in reversed(body) if re.search(r"\b\d+ of \d+\b", ln)), "no 'N of M' line")
    return ""


def run_cell(cell: Cell, root: Path, head: str, out: Path, base_env: dict[str, str], timeout: int) -> Row:
    log = out / f"{cell.id}.txt"
    cmdline = " ".join(shlex.quote(a) for a in cell.argv) if cell.argv else cell.label
    if cell.argv is None:
        log.write_text(f"{head}\n$ {cell.label}\nNOT RUN: {cell.why_not}\n", encoding="utf-8")
        return Row(cell, "NOT RUN", cell.why_not, log.name)
    env = dict(base_env, **cell.env)
    if cell.py:
        env["PYTHONPATH"] = str(root / "src")
    if not shutil.which(cell.argv[0]) and not Path(cell.argv[0]).exists():
        log.write_text(f"{head}\n$ {cmdline}\nNOT RUN: {cell.argv[0]} not found\n", encoding="utf-8")
        return Row(cell, "NOT RUN", f"{cell.argv[0]} not found", log.name)
    t0 = time.monotonic()
    try:
        p = subprocess.run(cell.argv, cwd=root, env=env, capture_output=True, text=True, errors="replace", timeout=timeout)
        rc, output = str(p.returncode), (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        raw = e.stdout or b""
        output = (raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw) + f"\n[timeout after {timeout}s]\n"
        rc = "timeout"
    exit_line = f"exit={rc if rc != 'timeout' else 'timeout'}"
    log.write_text(f"{head}\n$ {cmdline}\n{output.rstrip()}\n{exit_line}\n", encoding="utf-8")
    counts = parse_counts(cell.kind, output, rc)
    if cell.note:
        counts += f" ({cell.note})"
    return Row(cell, rc, f"{counts} [{time.monotonic() - t0:.0f}s]", log.name)


def hygiene_of_logs(root: Path, out: Path, head: str) -> Row:
    """Apply the secret patterns of the root's own tools/scan_repo.py to the logs written here. Prints path:line:rule only."""
    cell = Cell("hygiene-logs", "scan of these evidence logs with the PATTERNS of tools/scan_repo.py", None, [], "hygiene")
    log = out / "hygiene-logs.txt"
    path = root / "tools/scan_repo.py"
    if not path.exists():
        log.write_text(f"{head}\nNOT RUN: tools/scan_repo.py missing\n", encoding="utf-8")
        return Row(cell, "NOT RUN", "tools/scan_repo.py missing", log.name)
    spec = importlib.util.spec_from_file_location("scan_repo_for_logs", path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    hits: list[str] = []
    for f in sorted(out.glob("*.txt")):
        if f.name == log.name:
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for rule, rx in mod.PATTERNS.items():
                if rx.search(line) and mod.EXAMPLE_KEY not in line:
                    hits.append(f"{f.name}:{n}: {rule}")
    log.write_text(f"{head}\n$ PATTERNS of tools/scan_repo.py over {out.name}/*.txt\n" + "\n".join(hits) + f"\nexit={1 if hits else 0}\n", encoding="utf-8")
    return Row(cell, "1" if hits else "0", "no hits" if not hits else f"{len(hits)} hit lines", log.name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ticket", help="package id, for example P6a or P3a-2")
    ap.add_argument("head", help="full or short commit id the worktree must be at")
    ap.add_argument("--root", default=".")
    ap.add_argument("--venv313")
    ap.add_argument("--venv312")
    ap.add_argument("--out", required=True)
    ap.add_argument("--handover", default=None)
    ap.add_argument("--pys", default="3.13,3.12")
    ap.add_argument("--skip", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--extra", action="append", default=[], help='"label|python|command" (python: 3.13, 3.12 or -)')
    ap.add_argument("--bandit", default="uvx bandit")
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    out = Path(a.out).resolve()
    venvs = {v: Path(p) for v, p in (("3.13", a.venv313), ("3.12", a.venv312)) if p}
    pys = [p for p in a.pys.split(",") if p]
    bandit_cmd = a.bandit.split()
    cells = build_cells(a.ticket, root, venvs, pys, bandit_cmd)
    for spec in a.extra:
        label, py, cmd = (spec.split("|", 2) + ["", ""])[:3]
        py = None if py in ("-", "") else py
        exe = pyexe(venvs.get(py)) if py else None
        argv = shlex.split(cmd.replace("{python}", exe or sys.executable))
        cells.append(Cell(re.sub(r"\W+", "-", label).strip("-").lower(), label, py, argv, "pytest" if "pytest" in cmd else "other"))
    if a.list:
        for c in cells:
            print(c.id, "|", c.label, "|", c.py)
        return 0
    skip, only = set(filter(None, a.skip.split(","))), set(filter(None, a.only.split(",")))
    cells = [c for c in cells if c.id not in skip and (not only or c.id in only)]

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    if not head or not head.startswith(a.head) and not a.head.startswith(head[: len(a.head)]):
        print(f"STOP: worktree HEAD {head or '(none)'} does not match the head asked for ({a.head})")
        return 2
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, capture_output=True, text=True).stdout.strip()
    handover = Path(a.handover) if a.handover else next((p for p in (HERE.parent.parent.parent.parent / "hadavin-sdk" / "handover", Path("/home/user/hadavin-sdk/handover")) if p.exists()), None)
    ticket_file = (handover / "tickets" / (re.sub(r"-\d+$", "", a.ticket) + ".md")) if handover else None
    ticket_note = "ticket file NOT found"
    if ticket_file and ticket_file.exists():
        data = ticket_file.read_bytes()
        n_lines = data.count(b"\n")
        ticket_note = f"ticket read: tickets/{ticket_file.name} ({n_lines} lines, sha256 {hashlib.sha256(data).hexdigest()[:12]})"
    out.mkdir(parents=True, exist_ok=True)

    base_env = {k: v for k, v in os.environ.items() if not k.startswith(CLOUD_PREFIXES)}
    base_env["PYTHONDONTWRITEBYTECODE"] = "1"
    rows: list[Row] = []
    # a mutant runner plants into the tree: run it last, alone
    ordered = [c for c in cells if c.id != "p3a2-mutants"] + [c for c in cells if c.id == "p3a2-mutants"]
    for c in ordered:
        print(f"running {c.id} ...", flush=True)
        rows.append(run_cell(c, root, head, out, base_env, a.timeout))
        print(f"  rc={rows[-1].rc} {rows[-1].counts}", flush=True)
    rows.append(hygiene_of_logs(root, out, head))

    imp = {}
    for py in pys:
        exe = pyexe(venvs.get(py))
        if exe:
            r = subprocess.run([exe, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"], cwd=root, env=dict(base_env, PYTHONPATH=str(root / "src")), capture_output=True, text=True)
            imp[py] = r.stdout.strip()

    bad = [r for r in rows if r.rc != "0"]
    lines = [
        f"# {a.ticket} head {head} (evidence table written by gen_evidence; raw output only, no verdict)",
        "",
        f"Worktree {root}; HEAD checked = {head}; tracked files changed before the run: {'yes' if dirty else 'no'}. {ticket_note}.",
        f"HADAVIN_TEST_PG_DSN set: {'yes' if os.environ.get('HADAVIN_TEST_PG_DSN') else 'no'}; HADAVIN_TEST_VAULT_ADDR set: {'yes' if os.environ.get('HADAVIN_TEST_VAULT_ADDR') else 'no'}. Cloud variables removed ({', '.join(CLOUD_PREFIXES)}*).",
        "Import path per python: " + "; ".join(f"{k} -> {v}" for k, v in imp.items()),
        "Inner rc = the `exit=` line each log ends with. Cells not run are listed with the reason.",
        "",
        "Rows whose inner rc is not 0 or that were not run (a list of rows, not a judgement):",
    ]
    lines += [f"- {r.cell.id}: inner rc {r.rc}; {r.counts}; log {r.log}" for r in bad] or ["- none"]
    lines += ["", "| command | python | inner rc | counts | log |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.cell.label} | {r.cell.py or '-'} | {r.rc} | {r.counts} | {r.log} |")
    (out / "TABLE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out / 'TABLE.md'} ({len(rows)} rows, {len(bad)} with inner rc not 0 or not run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
