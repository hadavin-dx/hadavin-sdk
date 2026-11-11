"""Guard for the manual Evidence workflow (.github/workflows/evidence.yml) and its helper tools/evidence_step.py.

Classes guarded (sources: GitHub Actions security hardening guide: least-privilege GITHUB_TOKEN, pin actions to a full
commit SHA, no untrusted ${{ }} inside run scripts; the bash manual on `set -e`, pipelines and `$?`):
  1. permissions: read-only at the top and in every job;
  2. every `uses:` is a full 40-hex commit SHA;
  3. no `${{ }}` expression inside any `run:` script (script injection);
  4. concurrency never cancels a running evidence run, and the group carries the inputs;
  5. every job and every `run:` step has a timeout (the upload step is a `uses:` step and has none);
  6. no fixed Vault token, no Vault service container (the token is made fresh per run);
  7. every test/mutant step goes through the helper that records its exit code, and nothing hides a failure
     with `|| true`; the log upload runs even after a failure or a cancel;
  8. the helper itself: allowlists refuse odd input, a failing command is recorded and its exit code is kept,
     a step that did not run is NOT RUN and the report fails;
  9. stage names: only demo, pilot and prod appear; the check refuses the two old stage words in the workflow
     (a bare use of the old test-stage word elsewhere is not caught; none appears in the workflow today).
  10. names: extra runners are prefixed extra-, a repeated step name is refused, the verdict lists every step.
  11. the logs and the helper live under the runner temp directory (outside the checkout), never in the tested tree.

This is a best-effort text check of the workflow, not a proof: it catches the known ways the rules above get broken
(and each rule has a planted violation that proves it fires), but it cannot prove that no other way exists. The real
protection is the review of every change to the workflow files.
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
    for needed in ("inputs.ref", "inputs.pythons", "inputs.mutant_scripts"):
        if needed not in str(conc.get("group")):
            out.append(f"concurrency group must carry {needed}")
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
                    runs_tests = re.search(
                        r"\bpytest\b|\bpython3?\s+(-m\b|tests/|\"?\$s\b)|\buv\s+run\b", line
                    )
                    if runs_tests and "evidence_step.py" not in line and "$TOOL" not in line:
                        out.append(
                            f"{label}: runs tests without the helper that records the exit code"
                        )
                if (
                    "docker" in step["run"]
                    and " rm " in step["run"]
                    and step.get("if") != "${{ always() }}"
                ):
                    out.append(f"{label}: the Vault removal must run with always()")
                if re.search(r"\$TOOL\"? report\b", step["run"]):
                    cond = str(step.get("if"))
                    if "!cancelled()" not in cond and "always()" not in cond:
                        out.append(
                            f"{label}: the verdict must run after a failed step (!cancelled() or always())"
                        )
                waits = re.search(
                    r"\$TOOL\"? run (pytest|perf|stage-mutants)\b|run \"\$name\"", step["run"]
                )
                if waits and "steps.install.outcome == 'success'" not in str(step.get("if")):
                    out.append(
                        f"{label}: must wait for a successful install (steps.install.outcome)"
                    )
            if (
                str(step.get("uses", "")).startswith("actions/upload-artifact")
                and step.get("if") != "${{ always() }}"
            ):
                out.append(f"{label}: the upload must run with always()")
    steps = [st for job in wf["jobs"].values() for st in job["steps"] if "run" in st]
    literal = [m for st in steps for m in re.findall(r'\$TOOL" run ([a-z0-9-]+) --', st["run"])]
    reports = [st["run"] for st in steps if re.search(r'\$TOOL" report\b', st["run"])]
    if len(reports) != 1:
        out.append("exactly one verdict (report) step is needed")
    else:
        for name in literal:
            if name not in reports[0]:
                out.append(
                    f"the verdict does not list the step {name!r}, so it could not fail on NOT RUN"
                )
        if "extra-$(basename" not in reports[0]:
            out.append("the verdict must list the extra runners under the extra- prefix")
    for st in steps:
        if 'run "$name"' in st["run"] and "name=extra-$(basename" not in st["run"]:
            out.append(
                "extra runner step names must start with extra- (no clash with built-in steps)"
            )
    if "vault-token-reader" not in literal:
        out.append(
            "the tested ref must be checked for the HADAVIN_TEST_VAULT_TOKEN reader (step vault-token-reader)"
        )
    for st in steps:
        if "docker ps" in st["run"] and "xargs" in st["run"] and "name=^vault-ci$" not in st["run"]:
            out.append("the docker name filter must be an exact match ('name=^vault-ci$')")
        if "run vault-token-reader" in st["run"] and "[^#]*(environ|getenv)" not in st["run"]:
            out.append("vault-token-reader must look for a code line, not a comment")
    tr_form = 'extra-$(basename "$s" .py | tr _ -)'
    for st in steps:
        if "extra-$(basename" in st["run"] and st["run"].count(tr_form) != st["run"].count(
            "extra-$(basename"
        ):
            out.append(
                "the extra- name must be built the same way (with tr _ -) in the loop and in the verdict"
            )
    job = wf["jobs"]["evidence"]
    total = sum(st.get("timeout-minutes", 0) for st in job["steps"])
    if f"{total} minutes" not in text:
        out.append(
            f"the comment on the job timeout must say {total} minutes (the sum of the step timeouts)"
        )
    if total > job["timeout-minutes"]:
        out.append("the step timeouts add up to more than the job timeout")
    text_all = text
    if re.search(r"VAULT_DEV_ROOT_TOKEN_ID:\s*root\b", text_all) or re.search(
        r"\btoken\W+root\b", text_all
    ):
        out.append("fixed Vault token 'root'")
    if re.search(r"\b(staging)\b|\bstage\W+dev\b", text_all, re.IGNORECASE):
        out.append("a stage name other than demo, pilot or prod")
    for jname, jb in wf["jobs"].items():
        for st in jb["steps"]:
            if str(st.get("uses", "")).startswith("actions/upload-artifact"):
                path = str((st.get("with") or {}).get("path", ""))
                if not path.startswith("${{ runner.temp }}/"):
                    out.append(
                        f"job {jname}: the upload path must be under runner.temp, not the checkout"
                    )
            if str(st.get("uses", "")).startswith("actions/checkout") and (
                st.get("with") or {}
            ).get("path"):
                out.append(f"job {jname}: a second checkout inside the workspace is not allowed")
    if ".evidence-tools" in text_all:
        out.append("the helper must not live inside the checkout (.evidence-tools)")
    if "EVIDENCE_DIR=$RUNNER_TEMP/" not in text_all:
        out.append("EVIDENCE_DIR must be set to a folder under $RUNNER_TEMP")
    cols = str((wf["jobs"]["evidence"].get("env") or {}).get("COLUMNS", ""))
    if not cols.isdigit() or int(cols) < 200:
        out.append(
            "COLUMNS must be wide (at least 200) so that pytest does not cut a printed value"
        )
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
        "run: docker ps -aq --filter 'name=^vault-ci$' | xargs -r docker rm -f",
        "run: echo ${{ inputs.ref }}",
    ),
    "no step timeout": lambda t: t.replace(
        "        timeout-minutes: 2\n        run: docker ps -aq", "        run: docker ps -aq"
    ),
    "fixed vault token": lambda t: t.replace(
        "token=$(openssl rand -hex 24)", "token=root\n          # token root"
    ),
    "or true": lambda t: t.replace("exit $fail", "exit $fail || true"),
    "upload without always": lambda t: t.replace(
        "        if: ${{ always() }}\n        uses:", "        uses:"
    ),
    "bare pytest": lambda t: t.replace('run: python3 "$TOOL" run perf -- pytest', "run: pytest"),
    "verdict only on success": lambda t: t.replace(
        "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n        if: ${{ !cancelled() }}",
        "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n        if: ${{ success() }}",
    ),
    "vault removal without always": lambda t: t.replace(
        "      - name: Remove the Vault development server\n        if: ${{ always() }}",
        "      - name: Remove the Vault development server\n        if: ${{ success() }}",
    ),
    "tests not waiting for install": lambda t: t.replace(
        "        if: ${{ !cancelled() && steps.install.outcome == 'success' }}\n        timeout-minutes: 20\n        run: python3 \"$TOOL\" run perf",
        '        if: ${{ !cancelled() }}\n        timeout-minutes: 20\n        run: python3 "$TOOL" run perf',
    ),
    "report forgets a step": lambda t: t.replace(
        "report install psql-present vault-token-reader pytest perf",
        "report install psql-present vault-token-reader pytest",
    ),
    "uv run bare": lambda t: t.replace(
        'run: python3 "$TOOL" run pytest -- pytest -q -m "not live and not perf" -rfEs',
        "run: uv run ruff check",
    ),
    "python -m bare": lambda t: t.replace(
        'run: python3 "$TOOL" run perf -- pytest -q -m perf -rfEs', "run: python -m json.tool x"
    ),
    "python tests path bare": lambda t: t.replace(
        'run: python3 "$TOOL" run stage-mutants -- python tests/stage_mutants.py',
        "run: python tests/stage_mutants.py",
    ),
    "python runner variable bare": lambda t: t.replace(
        "          exit $fail", '          python "$s"\n          exit $fail'
    ),
    "tr changed on one side": lambda t: t.replace(
        'extra="$extra extra-$(basename "$s" .py | tr _ -)"',
        'extra="$extra extra-$(basename "$s" .py)"',
    ),
    "token reader matches a comment": lambda t: t.replace(
        "grep -Eq '^[^#]*(environ|getenv)[^#]*HADAVIN_TEST_VAULT_TOKEN'",
        "grep -q HADAVIN_TEST_VAULT_TOKEN",
    ),
    "docker filter substring": lambda t: t.replace("'name=^vault-ci$'", "name=vault-ci"),
    "timeout comment wrong": lambda t: t.replace("147 minutes", "135 minutes"),
    "concurrency without runners": lambda t: t.replace(
        "-${{ inputs.mutant_scripts }}\n  cancel", "\n  cancel"
    ),
    "extra runner without prefix": lambda t: t.replace("name=extra-$(basename", "name=$(basename"),
    "no token reader check": lambda t: t.replace(
        "run vault-token-reader --", "run vault-token-reader-x --"
    ),
    "staging stage": lambda t: t + "\n# stage: " + "stag" + "ing\n",
    "logs inside the checkout": lambda t: t.replace(
        "path: ${{ runner.temp }}/evidence-logs/", "path: evidence-logs/"
    ),
    "evidence dir not under runner temp": lambda t: t.replace(
        "EVIDENCE_DIR=$RUNNER_TEMP/evidence-logs", "EVIDENCE_DIR=evidence-logs"
    ),
    "helper inside the checkout": lambda t: t + "\n# path: .evidence-tools\n",
    "narrow terminal": lambda t: t.replace('COLUMNS: "300"', 'COLUMNS: "80"'),
    "second checkout in the workspace": lambda t: t.replace(
        "      - name: Artifact name and runner facts",
        "      - uses: actions/checkout@"
        + "0" * 40
        + "\n        with:\n          path: .evidence-x\n"
        "      - name: Artifact name and runner facts",
        1,
    ),
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
    inherited = {k: v for k, v in os.environ.items() if k != "EVIDENCE_DIR"}
    full = {**inherited, **(env or {})}
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
    assert missing.returncode == 1 and "| perf | NOT RUN (never finished" in missing.stdout
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
def test_bash_demo_the_old_pattern_lost_the_exit_code_under_bash_e():
    """Not a check of this repo: a demonstration of why the helper exists. Under `bash -e` the old `cmd; rc=$?` never recorded exit= for a failing command."""
    old = "set -e; { false; rc=$?; echo exit=$rc; exit $rc; } | cat"
    bash = shutil.which("bash")
    done = subprocess.run([bash, "-c", old], capture_output=True, text=True, check=False)  # noqa: S603  # fixed argv
    assert "exit=" not in done.stdout


def test_a_repeated_step_name_is_refused_and_the_first_log_is_kept(tmp_path):
    assert (
        helper(
            tmp_path, "run", "stage-mutants", "--", sys.executable, "-c", "raise SystemExit(4)"
        ).returncode
        == 4
    )
    again = helper(tmp_path, "run", "stage-mutants", "--", sys.executable, "-c", "pass")
    assert again.returncode == 2 and "already used" in again.stderr
    assert (tmp_path / "evidence-logs" / "stage-mutants.txt").read_text().splitlines()[
        -1
    ] == "exit=4"
    assert helper(tmp_path, "report", "stage-mutants").returncode == 1


def test_the_report_fails_on_repeated_rows_even_when_the_last_one_is_green(tmp_path):
    logs = tmp_path / "evidence-logs"
    logs.mkdir()
    (logs / "status.txt").write_text("a\texit=1\na\texit=0\n")
    done = helper(tmp_path, "report", "a")
    assert done.returncode == 1 and "DUPLICATE" in done.stdout


def test_the_report_shows_skip_counts_and_fails_on_a_missing_test_variable(tmp_path):
    helper(
        tmp_path,
        "run",
        "pytest",
        "--",
        sys.executable,
        "-c",
        "print('SKIPPED [2] tests/x.py:1: slow')",
    )
    ok = helper(tmp_path, "report", "pytest")
    assert ok.returncode == 0 and "| pytest | exit=0 | 2 |" in ok.stdout
    code = "print('SKIPPED [3] tests/x.py:1: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)')"
    helper(tmp_path, "run", "perf", "--", sys.executable, "-c", code)
    bad = helper(tmp_path, "report", "pytest", "perf")
    assert (
        bad.returncode == 1
        and "3 test(s) skipped for a reason that names a HADAVIN_TEST_ variable" in bad.stdout
    )


def test_a_step_that_never_finished_says_so(tmp_path):
    done = helper(tmp_path, "report", "perf")
    assert "never finished: skipped, timed out or cancelled" in done.stdout and done.returncode == 1


def test_odd_versions_and_long_runner_names_are_refused_with_exit_2():
    for bad in (
        f'["3.{"9" * 5000}"]',
        '["3.012"]',
        '["3.0013"]',
        '["3.7"]',
        '["3.99"]',
        '["3.15"]',
    ):
        with pytest.raises(es.Refused):
            es.check_pythons(bad)
    with pytest.raises(es.Refused):
        es.check_mutants("tests/" + "a" * 41 + "_mutants.py")
    with pytest.raises(es.Refused, match="pull/N/head"):
        es.check_ref("bad ref")


@pytest.mark.parametrize(
    "reason",
    [
        "is unset",
        "is missing",
        "not defined",
        "is empty",
        "not set",
        "cannot connect",
        "needs it",
        "",
    ],
)
def test_every_wording_of_a_missing_test_variable_fails_the_report(tmp_path, reason):
    code = f"print('SKIPPED [1] tests/x.py:1: HADAVIN_TEST_VAULT_ADDR {reason}')"
    helper(tmp_path, "run", "pytest", "--", sys.executable, "-c", code)
    assert helper(tmp_path, "report", "pytest").returncode == 1


# --- the Vault development server in every workflow (ci.yml and evidence.yml) ---------------------------------


def workflow_files(folder: Path) -> list[Path]:
    """Every workflow file of a folder: GitHub reads both .yml and .yaml."""
    return sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])


WORKFLOWS = workflow_files(ROOT / ".github" / "workflows")
IMAGE_RE = re.compile(r"hashicorp/vault:[0-9.]+@sha256:[0-9a-f]{64}")
VALUE_REF_RE = r"\$\{?(token|HADAVIN_TEST_VAULT_TOKEN|VAULT_DEV_ROOT_TOKEN_ID)\b"
MASK_LINE = 'echo "::add-mask::$token"'
ENV_LINE = 'echo "HADAVIN_TEST_VAULT_TOKEN=$token" >> "$GITHUB_ENV"'
TEST_ENV = "HADAVIN_TEST_VAULT_ADDR"


def docker_run_lines(script: str) -> list[str]:
    """Each `docker run ...` command of a script as one string (line continuations joined)."""
    joined = re.sub(r"\\\n\s*", " ", script)
    return [
        ln.strip() for ln in joined.splitlines() if re.match(r"\s*(sudo\s+)?docker\s+run\b", ln)
    ]


def vault_problems(text: str) -> list[str]:
    """Rules for any workflow job that uses a Vault server: one random value, made in a step, masked before it is
    written anywhere, handed to the container and to the tests, never printed and never a literal; the container is
    published on loopback only, removed by name after the last test step, and the image is one pinned digest.
    A service cannot read a step's output, so there is no `vault` service."""
    wf = load(text)
    out: list[str] = []
    if re.search(r"VAULT_DEV_ROOT_TOKEN_ID:\s*\S", text) or re.search(
        r"HADAVIN_TEST_VAULT_TOKEN:\s*\S", text
    ):
        out.append("a literal Vault token is set in an env block")
    if re.search(r"\btoken\W+root\b", text):
        out.append("the literal token 'root' appears")
    digests = set(IMAGE_RE.findall(text))
    if len(digests) > 1:
        out.append(f"more than one Vault image digest in one workflow: {sorted(digests)}")
    for jname, job in wf["jobs"].items():
        steps = job["steps"]
        if "vault" in (job.get("services") or {}):
            out.append(f"job {jname}: Vault is a service (its token cannot be generated)")
        for st in steps:
            run = st.get("run", "")
            if re.search(r"(^|\s)set\s+-\w*x|xtrace|bash\s+-\w*x", run):
                out.append(f"job {jname}: shell tracing (set -x) would print the token")
            if st.get("shell"):
                out.append(f"job {jname}: a shell: override changes how the script is run")
            code_lines = [ln for ln in run.splitlines() if not ln.lstrip().startswith("#")]
            for line in code_lines:
                if re.match(
                    r"\s*(env|printenv|export\s*(-p)?\s*$|set\s*$|declare\s+-x|cat|tee)\b", line
                ):
                    out.append(
                        f"job {jname}: a line could print the environment or the token: {line.strip()[:40]}"
                    )
                if "<<<" in line and re.search(VALUE_REF_RE, line):
                    out.append(f"job {jname}: a here-string passes the token to a command")
                if re.search(
                    r"\bsudo\b|docker\s+exec\b|docker\.sock|--pid[= ]host|--ipc[= ]host|--cap-add",
                    line,
                ):
                    out.append(
                        f"job {jname}: sudo, docker exec, docker.sock or extra rights: {line.strip()[:40]}"
                    )
                if re.match(r"\s*curl\b", line) and re.search(
                    r"\s(-[a-zA-Z]*v[a-zA-Z]*|--verbose|--trace\S*|--dump-header)\b", line
                ):
                    out.append(f"job {jname}: curl in verbose mode would print the token header")
            for line in run.splitlines():
                if (
                    re.match(r"\s*(echo|printf)\b", line)
                    and re.search(VALUE_REF_RE, line)
                    and line.strip() not in (MASK_LINE, ENV_LINE)
                ):
                    out.append(f"job {jname}: a line prints the token: {line.strip()[:50]}")
        uses_server = TEST_ENV in json.dumps(job)
        starts = [
            i
            for i, st in enumerate(steps)
            if docker_run_lines(st.get("run", ""))
            and ("hashicorp/vault" in st["run"] or "$VAULT_IMAGE" in st["run"])
        ]
        if uses_server and not starts:
            out.append(f"job {jname}: the tests use a Vault server but no step starts one")
        if not starts:
            continue
        job_text = json.dumps(wf.get("env", {})) + json.dumps(job.get("env", {}))
        if any("$VAULT_IMAGE" in steps[i]["run"] for i in starts) and not IMAGE_RE.search(job_text):
            out.append(f"job {jname}: $VAULT_IMAGE is not defined as a pinned digest in env")
        for i in starts:
            script = steps[i]["run"]
            label = f"job {jname} step {i}"
            if "openssl rand" not in script:
                out.append(f"{label}: the Vault token is not generated with openssl rand")
            if MASK_LINE not in script or ENV_LINE not in script:
                out.append(
                    f"{label}: missing the mask line or the line that hands the token to the tests"
                )
            elif script.index(MASK_LINE) > script.index(ENV_LINE):
                out.append(
                    f"{label}: the mask line must come before the token is written to GITHUB_ENV"
                )
            if 'export VAULT_DEV_ROOT_TOKEN_ID="$token"' not in script:
                out.append(f"{label}: the container does not get the same $token")
            if script.count("token=") != 1:
                out.append(f"{label}: more than one token value")
            for cmd in docker_run_lines(script):
                if re.search(r"VAULT_DEV_ROOT_TOKEN_ID=|--env\b|--env-file", cmd):
                    out.append(
                        f"{label}: the container gets its token by value or by file, not by -e NAME"
                    )
                if (
                    len(re.findall(r"(?:^|\s)(?:-p|--publish)(?:\s|=)", cmd)) != 1
                    or "-p 127.0.0.1:8200:8200 " not in cmd + " "
                ):
                    out.append(f"{label}: exactly one port, -p 127.0.0.1:8200:8200, is allowed")
                if re.search(
                    r"(?:^|\s)(-P|--publish-all|--privileged|--network[= ]host|--net[= ]host)(?:\s|$)",
                    cmd,
                ):
                    out.append(f"{label}: -P, --privileged or host networking is not allowed")
                if "-e VAULT_DEV_ROOT_TOKEN_ID " not in cmd:
                    out.append(
                        f"{label}: the container must get -e VAULT_DEV_ROOT_TOKEN_ID (no value)"
                    )
                if re.search(
                    r"--security-opt\s+\S*(unconfined|seccomp|apparmor)|--cap-add|--device|(^|\s)(-v|--volume|--mount)\b|--user\s+0|--pid|--ipc",
                    cmd,
                ):
                    out.append(f"{label}: extra container rights or mounts are not allowed")
                if '"$VAULT_IMAGE"' not in cmd:
                    out.append(f'{label}: the image must be given as "$VAULT_IMAGE"')
                if "--name vault-ci " not in cmd:
                    out.append(f"{label}: the container must be named vault-ci")
            code = [ln.strip() for ln in script.splitlines() if not ln.lstrip().startswith("#")]
            if not any(
                ln.startswith("curl ")
                and "X-Vault-Token" in ln
                and "127.0.0.1:8200" in ln
                and ln.endswith("&& exit 0")
                for ln in code
            ):
                out.append(
                    f"{label}: no readiness probe from the host with the token (as a code line)"
                )
            if [ln for ln in code if ln][-1:] != ["exit 1"]:
                out.append(
                    f"{label}: the step must end with exit 1 after the waiting loop times out"
                )
            if re.search(r"hashicorp/vault", "\n".join(code)):
                out.append(
                    f"{label}: the image must come from $VAULT_IMAGE, not a literal in the script"
                )
            if "docker logs" not in script or "docker ps" not in script:
                out.append(f"{label}: no container diagnostics on failure")
            if "docker inspect" not in script:
                out.append(f"{label}: no fast failure when the container has exited")
        is_test = re.compile(r"\bpytest\b|\$TOOL\"? run (perf|stage-mutants|\"\$name\")")
        test_steps = [i for i, st in enumerate(steps) if is_test.search(st.get("run", ""))]
        last_test = max(test_steps or [-1])
        first_test = min(test_steps or [10**6])
        if first_test < starts[0]:
            out.append(f"job {jname}: a test step runs before the Vault step")
        removal = [
            i for i, st in enumerate(steps) if "docker" in st.get("run", "") and " rm " in st["run"]
        ]
        if not removal:
            out.append(f"job {jname}: the Vault container is never removed")
        for i in removal:
            if steps[i].get("if") != "${{ always() }}":
                out.append(f"job {jname}: the Vault removal must run with always()")
            if "name=^vault-ci$" not in steps[i]["run"]:
                out.append(f"job {jname}: the Vault removal must target name=^vault-ci$")
            if i < last_test:
                out.append(f"job {jname}: the Vault removal comes before the last test step")
    return out


def test_all_vault_image_digests_are_equal_across_workflows():
    found = {m for path in WORKFLOWS for m in IMAGE_RE.findall(path.read_text(encoding="utf-8"))}
    assert len(found) == 1, found


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_makes_its_vault_token_fresh(path):
    assert vault_problems(path.read_text(encoding="utf-8")) == []


def test_ci_workflow_starts_vault_in_both_test_jobs():
    wf = load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    for jname in ("check", "tests-py312"):
        names = [st.get("name", "") for st in wf["jobs"][jname]["steps"]]
        assert names.count("Start a throwaway Vault development server") == 1, jname
        assert "vault" not in (wf["jobs"][jname].get("services") or {})


VAULT_PLANTS = {
    "literal token in a service": lambda t: t.replace(
        "    steps:\n",
        "    services:\n      vault:\n        image: x\n        env:\n          VAULT_DEV_ROOT_TOKEN_ID: abc\n    steps:\n",
        1,
    ),
    "vault service alone": lambda t: t.replace(
        "    steps:\n", "    services:\n      vault:\n        image: x\n    steps:\n", 1
    ),
    "literal env token": lambda t: t.replace(
        "    steps:\n", "    env:\n      HADAVIN_TEST_VAULT_TOKEN: abc\n    steps:\n", 1
    ),
    "fixed value instead of openssl": lambda t: t.replace(
        "token=$(openssl rand -hex 24)", "token=abc123"
    ),
    "no mask line": lambda t: t.replace('          echo "::add-mask::$token"\n', ""),
    "mask after env write": lambda t: t.replace(
        MASK_LINE + "\n          " + ENV_LINE, ENV_LINE + "\n          " + MASK_LINE
    ),
    "tests not given the token": lambda t: t.replace(
        'echo "HADAVIN_TEST_VAULT_TOKEN=$token"', 'echo "OTHER=$token"'
    ),
    "container not given the same value": lambda t: t.replace(
        'export VAULT_DEV_ROOT_TOKEN_ID="$token"',
        'export VAULT_DEV_ROOT_TOKEN_ID="$(openssl rand -hex 8)"',
    ),
    "second value": lambda t: t.replace(
        MASK_LINE, "token=$(openssl rand -hex 4)\n          " + MASK_LINE
    ),
    "token printed by echo": lambda t: t.replace(MASK_LINE, "echo $token\n          " + MASK_LINE),
    "token printed by printf": lambda t: t.replace(
        MASK_LINE, 'printf "%s\\n" "$token"\n          ' + MASK_LINE
    ),
    "token printed in text": lambda t: t.replace(
        MASK_LINE, 'echo "t=$token"\n          ' + MASK_LINE
    ),
    "token printed with braces": lambda t: t.replace(
        MASK_LINE, 'echo "${token}"\n          ' + MASK_LINE
    ),
    "shell tracing": lambda t: t.replace(
        "          token=$(openssl", "          set -x\n          token=$(openssl"
    ),
    "port on all interfaces": lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 8200:8200"),
    "second port": lambda t: t.replace(
        "-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 -p 8201:8201"
    ),
    "publish all": lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 -P"),
    "host network": lambda t: t.replace(
        "-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 --network host"
    ),
    "token by value": lambda t: t.replace(
        "-e VAULT_DEV_ROOT_TOKEN_ID -e", "-e VAULT_DEV_ROOT_TOKEN_ID=$token -e"
    ),
    "container renamed": lambda t: t.replace("--name vault-ci", "--name vault-x"),
    "no host probe": lambda t: t.replace("curl -fsS", "echo -fsS"),
    "no diagnostics": lambda t: t.replace("docker logs", "docker version #"),
    "no exit check": lambda t: t.replace("docker inspect", "docker version #"),
    "image digest differs": lambda t: t + "\n# hashicorp/vault:2.2.0@sha256:" + "0" * 64,
    "no removal": lambda t: re.sub(
        r"(Remove the Vault development server\n\s+)if: \$\{\{ always\(\) \}\}",
        r"\1if: ${{ success() }}",
        t,
    ),
    "removal by substring": lambda t: t.replace("'name=^vault-ci$'", "name=vault"),
    "docker exec": lambda t: t.replace(
        MASK_LINE, MASK_LINE + "\n          docker exec vault-ci env"
    ),
    "environment printed": lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          env"),
    "printenv": lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          printenv"),
    "curl verbose": lambda t: t.replace("curl -fsS", "curl -v -fsS"),
    "curl long verbose": lambda t: t.replace("curl -fsS", "curl --verbose -fsS"),
    "shell override": lambda t: t.replace(
        "      - name: Start a throwaway Vault development server\n",
        "      - name: Start a throwaway Vault development server\n        shell: bash -x {0}\n",
    ),
    "docker run with two spaces": lambda t: t.replace(
        "docker run -d --name vault-ci", "docker  run -d --name vault-x -p 8200:8200"
    ),
    "sudo docker": lambda t: t.replace("docker run -d", "sudo docker run -d"),
    "literal image": lambda t: t.replace(
        '"$VAULT_IMAGE" > /dev/null', "hashicorp/vault:2.2.0 > /dev/null"
    ),
    "docker socket": lambda t: t.replace(
        "-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true -v /var/run/docker.sock:/var/run/docker.sock"
    ),
    "host pid": lambda t: t.replace("-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true --pid=host"),
    "added capability": lambda t: t.replace(
        "-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true --cap-add SYS_ADMIN"
    ),
    "probe only in a comment": lambda t: t.replace(
        'curl -fsS -o /dev/null -H "X-Vault-Token: $token"',
        '# curl -fsS -H "X-Vault-Token: $token"\n            true "$token"',
    ),
    "probe cannot succeed": lambda t: t.replace(" && exit 0", ""),
    "no exit 1 after the loop": lambda t: re.sub(
        r"(Start a throwaway Vault development server[\s\S]*?)exit 1\n(?=\s+- )", r"\1true\n", t
    ),
    "cat prints the token": lambda t: t.replace(
        MASK_LINE, 'cat <<< "$token"\n          ' + MASK_LINE
    ),
    "here-string": lambda t: t.replace(MASK_LINE, 'tr a b <<< "$token"\n          ' + MASK_LINE),
    "never removed": lambda t: re.sub(
        r"      - name: Remove the Vault development server\n(?:        .*\n){3}", "", t
    ),
}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
@pytest.mark.parametrize("name", sorted(VAULT_PLANTS))
def test_each_vault_rule_fails_on_a_planted_violation(path, name):
    text = path.read_text(encoding="utf-8")
    planted = VAULT_PLANTS[name](text)
    assert planted != text, f"plant {name} changed nothing in {path.name}"
    assert vault_problems(planted), f"plant {name} was not caught in {path.name}"


def test_a_second_docker_run_step_is_inspected_too():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    extra = (
        "      - name: Another server\n        timeout-minutes: 2\n        run: |\n"
        "          docker run -d --name vault-ci -p 8200:8200 $VAULT_IMAGE\n"
    )
    planted = text.replace(
        "      - uses: astral-sh/setup-uv@", extra + "      - uses: astral-sh/setup-uv@", 1
    )
    assert planted != text and vault_problems(planted)


def test_a_removal_step_before_the_last_test_step_is_caught():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    removal = (
        "      - name: Remove the Vault development server\n        if: ${{ always() }}\n        timeout-minutes: 2\n"
        "        run: docker ps -aq --filter 'name=^vault-ci$' | xargs -r docker rm -f\n"
    )
    assert removal in text
    planted = text.replace(removal, "", 1).replace(
        "      - uses: astral-sh/setup-uv@", removal + "      - uses: astral-sh/setup-uv@", 1
    )
    assert vault_problems(planted)


def test_a_job_that_uses_vault_without_starting_one_is_caught():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    planted = text.replace("Start a throwaway Vault development server", "Something else", 1)
    planted = planted.replace("docker run -d --name vault-ci", "echo", 1)
    assert vault_problems(planted)


def test_the_file_search_covers_yaml_files_too(tmp_path):
    (tmp_path / "a.yml").write_text("x: 1\n")
    (tmp_path / "b.yaml").write_text("x: 1\n")
    (tmp_path / "c.txt").write_text("x\n")
    assert [p.name for p in workflow_files(tmp_path)] == ["a.yml", "b.yaml"]
    assert WORKFLOWS, "no workflow file found"


# --- the helper removes the token from files and from the summary -----------------------------------------


def test_the_helper_removes_the_token_value_from_logs_and_the_summary(tmp_path):
    token = "tok" + "-" + "a1b2c3d4e5f6"  # built from parts; a made-up value
    env = {"HADAVIN_TEST_VAULT_TOKEN": token, "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md")}
    code = f"print('hvac error with header X-Vault-Token: {token}'); print('FAILED t.py::x - {token}'); raise SystemExit(1)"
    helper(tmp_path, "run", "pytest", "--", sys.executable, "-c", code, env=env)
    done = helper(tmp_path, "report", "pytest", env=env)
    saved = (tmp_path / "evidence-logs" / "pytest.txt").read_text()
    for blob in (
        saved,
        done.stdout,
        (tmp_path / "summary.md").read_text(),
        (tmp_path / "evidence-logs" / "status.txt").read_text(),
    ):
        assert token not in blob
    assert "***" in saved and "FAILED t.py::x - ***" in done.stdout


def test_a_short_value_is_not_masked_so_that_ordinary_words_survive(tmp_path):
    env = {"HADAVIN_TEST_VAULT_TOKEN": "abc"}
    helper(tmp_path, "run", "x", "--", sys.executable, "-c", "print('abc def')", env=env)
    assert "abc def" in (tmp_path / "evidence-logs" / "x.txt").read_text()


def test_a_cut_off_piece_of_the_value_is_masked_too(tmp_path):
    token = "tok" + "-" + "a1b2c3d4e5f6a7b8c9d0"
    env = {"HADAVIN_TEST_VAULT_TOKEN": token}
    code = f"print('cut: {token[:12]}'); print('tail: {token[-9:]}'); print('short: {token[:5]}')"
    helper(tmp_path, "run", "x", "--", sys.executable, "-c", code, env=env)
    saved = (tmp_path / "evidence-logs" / "x.txt").read_text()
    assert token[:12] not in saved and token[-9:] not in saved
    assert "short: " + token[:5] in saved


def test_the_folder_comes_from_evidence_dir_when_it_is_set(tmp_path):
    target = tmp_path / "elsewhere" / "logs"
    helper(
        tmp_path,
        "run",
        "x",
        "--",
        sys.executable,
        "-c",
        "print(1)",
        env={"EVIDENCE_DIR": str(target)},
    )
    assert (target / "x.txt").exists() and (target / "status.txt").exists()
    assert not (tmp_path / "evidence-logs").exists()


def test_the_helper_source_masks_in_emit_and_in_the_report():
    src = (ROOT / "tools" / "evidence_step.py").read_text(encoding="utf-8")
    assert "text = mask(text)" in src and 'mask("\\n".join(out)' in src


# --- the test-side Vault target never falls back to a fixed token ---------------------------------------------


def test_vault_target_needs_the_token_when_a_server_address_is_set(monkeypatch):
    from tests.contracts.kinds.secrets_neutral import vault_target

    monkeypatch.setenv("HADAVIN_TEST_VAULT_ADDR", "http://127.0.0.1:1")
    monkeypatch.delenv("HADAVIN_TEST_VAULT_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HADAVIN_TEST_VAULT_TOKEN"):
        vault_target()
    monkeypatch.setenv("HADAVIN_TEST_VAULT_TOKEN", "x" * 12)
    assert vault_target() == ("http://127.0.0.1:1", "x" * 12)


def test_vault_target_without_an_address_is_the_local_fake(monkeypatch):
    from tests.contracts.kinds.secrets_neutral import vault_target

    monkeypatch.delenv("HADAVIN_TEST_VAULT_ADDR", raising=False)
    address, token = vault_target()
    assert address.startswith("http://127.0.0.1:") and token


def test_the_vault_test_files_do_not_skip_on_a_connection_failure():
    for rel in (
        "tests/contracts/kinds/secrets_neutral.py",
        "tests/contracts/kinds/audit_neutral.py",
    ):
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert "pytest.skip" not in src and "skipif" not in src, rel
