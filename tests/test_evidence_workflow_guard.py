"""Guard for the manual Evidence workflow (.github/workflows/evidence.yml) and its helper tools/evidence_step.py.

Classes guarded (sources: GitHub Actions security hardening guide: least-privilege GITHUB_TOKEN, pin actions to a full
commit SHA, no untrusted ${{ }} inside run scripts; the bash manual on `set -e`, pipelines and `$?`):
  1. permissions: read-only at the top and in every job;
  2. every `uses:` is a full 40-hex commit SHA;
  3. no `${{ }}` expression inside any `run:` script (script injection);
  4. concurrency never cancels a running evidence run, and the group carries the inputs;
  5. every job and every step has a timeout;
  6. no fixed Vault token, no Vault service container (the token is made fresh per run);
  7. every test/mutant step goes through the helper that records its exit code, and nothing hides a failure
     with `|| true`; the log upload runs even after a failure or a cancel;
  8. the helper itself: allowlists refuse odd input, a failing command is recorded and its exit code is kept,
     a step that did not run is NOT RUN and the report fails;
  9. stage names: only demo, pilot and prod appear (no "dev" or "staging" as a stage).
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from tools import evidence_step as es

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "evidence.yml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(text: str | None = None) -> dict:
    return yaml.safe_load(text if text is not None else WORKFLOW.read_text(encoding="utf-8"))


def problems(text: str) -> list[str]:
    """Every rule broken by this workflow text (empty list = clean). The plant tests feed it bad text."""
    wf = load(text)
    out: list[str] = []
    if wf.get("permissions") != {"contents": "read"}:
        out.append("top-level permissions must be exactly contents: read")
    conc = wf.get("concurrency") or {}
    if conc.get("cancel-in-progress") is not False:
        out.append("concurrency must set cancel-in-progress: false")
    if "inputs.ref" not in str(conc.get("group")) or "inputs.pythons" not in str(conc.get("group")):
        out.append("concurrency group must carry the ref and the pythons input")
    for jname, job in wf["jobs"].items():
        if job.get("permissions") != {"contents": "read"}:
            out.append(f"job {jname}: own permissions must be exactly contents: read")
        if "timeout-minutes" not in job:
            out.append(f"job {jname}: no timeout")
        if "vault" in (job.get("services") or {}):
            out.append(
                f"job {jname}: Vault must be a step with a random token, not a service with a fixed one"
            )
        for i, step in enumerate(job["steps"]):
            label = f"job {jname} step {i} ({step.get('name', step.get('uses'))})"
            if "uses" in step and not SHA40.match(step["uses"].split("@", 1)[1]):
                out.append(f"{label}: action not pinned to a full commit SHA")
            if "run" in step:
                if "${{" in step["run"]:
                    out.append(
                        f"{label}: ${{{{ }}}} expression inside a run script (script injection)"
                    )
                if "timeout-minutes" not in step:
                    out.append(f"{label}: no step timeout")
                if re.search(r"\|\|\s*true\b", step["run"]):
                    out.append(f"{label}: '|| true' hides a failure")
                for line in step["run"].splitlines():
                    if (
                        re.match(r"\s*(pytest|python3?)\s", line)
                        and "evidence_step.py" not in line
                        and "$TOOL" not in line
                    ):
                        out.append(
                            f"{label}: runs tests without the helper that records the exit code"
                        )
            if (
                str(step.get("uses", "")).startswith("actions/upload-artifact")
                and step.get("if") != "${{ always() }}"
            ):
                out.append(f"{label}: the upload must run with always()")
    text_all = text
    if re.search(r"VAULT_DEV_ROOT_TOKEN_ID:\s*root\b", text_all) or re.search(
        r"\btoken\W+root\b", text_all
    ):
        out.append("fixed Vault token 'root'")
    if re.search(r"\b(staging)\b|\bstage\W+dev\b", text_all, re.IGNORECASE):
        out.append("a stage name other than demo, pilot or prod")
    return out


def test_the_current_workflow_breaks_no_rule():
    assert problems(WORKFLOW.read_text(encoding="utf-8")) == []


def test_extra_runner_names_and_pythons_reach_the_jobs_only_through_the_plan_job():
    wf = load()
    text = WORKFLOW.read_text(encoding="utf-8")
    for jname, job in wf["jobs"].items():
        if jname == "plan":
            continue
        blob = json.dumps(job)
        assert "inputs." not in blob, f"job {jname} reads a raw input; use needs.plan.outputs"
    assert "needs.plan.outputs.pythons" in text
    assert "inputs.ref" not in json.dumps(wf["jobs"]["evidence"])


PLANTS = {
    "write permission": lambda t: t.replace(
        "permissions:\n  contents: read", "permissions:\n  contents: write", 1
    ),
    "cancel in progress": lambda t: t.replace(
        "cancel-in-progress: false", "cancel-in-progress: true"
    ),
    "unpinned action": lambda t: re.sub(r"(actions/upload-artifact)@[0-9a-f]{40}", r"\1@v7", t),
    "injection": lambda t: t.replace(
        "run: docker rm -f vault-evidence", "run: echo ${{ inputs.ref }}"
    ),
    "no step timeout": lambda t: t.replace(
        "        timeout-minutes: 2\n        run: docker rm", "        run: docker rm"
    ),
    "fixed vault token": lambda t: t.replace(
        "token=$(openssl rand -hex 24)", "token=root\n          # token root"
    ),
    "or true": lambda t: t.replace("exit $fail", "exit $fail || true"),
    "upload without always": lambda t: t.replace(
        "        if: ${{ always() }}\n        uses:", "        uses:"
    ),
    "bare pytest": lambda t: t.replace('run: python3 "$TOOL" run perf -- pytest', "run: pytest"),
    "staging stage": lambda t: t + "\n# stage: staging\n",
}


@pytest.mark.parametrize("name", sorted(PLANTS))
def test_each_rule_fails_on_a_planted_violation(name):
    text = WORKFLOW.read_text(encoding="utf-8")
    planted = PLANTS[name](text)
    assert planted != text, f"plant {name} did not change the text"
    assert problems(planted), f"plant {name} was not caught"


# --- the helper --------------------------------------------------------------------------------------


def test_allowlists_refuse_odd_input():
    for bad in ("", "-x", "a b", "a..b", "a;rm", "x$(id)", "a" * 201, "a/", "a.lock"):
        with pytest.raises(es.Refused):
            es.check_ref(bad)
    assert es.check_ref("core/ci-evidence") == "core/ci-evidence"
    for bad in (
        "not json",
        "{}",
        "[]",
        '["3.13","3.13","3.12","3.14","3.15"]',
        '["3.11"]',
        '["3.13; id"]',
        "[3.13]",
        '["4.0"]',
        '["3.x"]',
    ):
        with pytest.raises(es.Refused):
            es.check_pythons(bad)
    assert es.check_pythons('["3.13","3.12","3.13"]') == ["3.13", "3.12"]
    for bad in (
        "tests/x.py",
        "../tests/a_mutants.py",
        "tests/A_mutants.py",
        "tests/a_mutants.py;id",
        "tests/a b_mutants.py x",
    ):
        with pytest.raises(es.Refused):
            es.check_mutants(bad)
    with pytest.raises(es.Refused):
        es.check_mutants(" ".join(f"tests/m{i}_mutants.py" for i in range(9)))
    assert es.check_mutants("tests/stage_mutants.py  tests/stage_mutants.py") == [
        "tests/stage_mutants.py"
    ]


def helper(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full = {**os.environ, **(env or {})}
    return subprocess.run(  # noqa: S603  # our own interpreter and a file of this repository, no shell
        [sys.executable, str(ROOT / "tools" / "evidence_step.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=full,
        check=False,
    )


def test_a_failing_command_keeps_its_exit_code_and_a_later_step_still_runs(tmp_path):
    first = helper(
        tmp_path, "run", "bad", "--", sys.executable, "-c", "print('boom'); raise SystemExit(3)"
    )
    assert first.returncode == 3
    second = helper(tmp_path, "run", "good", "--", sys.executable, "-c", "print('fine')")
    assert second.returncode == 0
    status = (tmp_path / "evidence-logs" / "status.txt").read_text().splitlines()
    assert status == ["bad\texit=3", "good\texit=0"]
    log = (tmp_path / "evidence-logs" / "bad.txt").read_text().splitlines()
    assert "boom" in log and log[-1] == "exit=3"


def test_a_command_that_cannot_start_is_recorded_as_127(tmp_path):
    done = helper(tmp_path, "run", "gone", "--", "no-such-program-xyz")
    assert done.returncode == 127
    assert "gone\texit=127" in (tmp_path / "evidence-logs" / "status.txt").read_text()


def test_the_report_fails_on_a_non_zero_exit_and_on_a_step_that_never_ran(tmp_path):
    helper(tmp_path, "run", "ok", "--", sys.executable, "-c", "pass")
    assert helper(tmp_path, "report", "ok").returncode == 0
    missing = helper(tmp_path, "report", "ok", "perf")
    assert missing.returncode == 1 and "| perf | NOT RUN |" in missing.stdout
    helper(tmp_path, "run", "bad", "--", sys.executable, "-c", "raise SystemExit(5)")
    failed = helper(tmp_path, "report", "ok")
    assert failed.returncode == 1 and "| bad | exit=5 |" in failed.stdout


def test_the_plan_command_writes_only_checked_values(tmp_path):
    out = tmp_path / "out.txt"
    env = {
        "INPUT_REF": "main",
        "INPUT_PYTHONS": '["3.13"]',
        "INPUT_MUTANTS": "",
        "GITHUB_OUTPUT": str(out),
    }
    assert helper(tmp_path, "plan", env=env).returncode == 0
    assert out.read_text().splitlines() == ['pythons=["3.13"]', "mutants=", "ref=main"]
    env["INPUT_PYTHONS"] = '["3.13\\nx=1"]'
    assert helper(tmp_path, "plan", env=env).returncode == 2


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash needed for the exit-code lesson")
def test_the_old_pattern_lost_the_exit_code_under_bash_e():
    """Why the helper exists: under `bash -e` the old `cmd; rc=$?` never recorded exit= for a failing command."""
    old = "set -e; { false; rc=$?; echo exit=$rc; exit $rc; } | cat"
    bash = shutil.which("bash")
    done = subprocess.run([bash, "-c", old], capture_output=True, text=True, check=False)  # noqa: S603  # fixed argv
    assert "exit=" not in done.stdout
