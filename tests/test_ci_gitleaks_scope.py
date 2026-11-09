"""Pin the two security-job downloads and the gitleaks scan in ci.yml.

The scan must cover only the history reachable from the checked-out head and must block; each pinned
binary download must retry transient errors and keep its checksum, TLS and protocol limits. The checks
parse the workflow as YAML, split each command into shell words and compare them with an exact list,
so a neutered scan (`|| true`, `--exit-code=0`, another config, `continue-on-error`) cannot pass.
"""

import copy
import re
import shlex
from pathlib import Path

import pytest
import yaml

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

GL = "Secrets in the history"  # step-name fragment of the gitleaks scan step
SCAN_WORDS = [
    '"$RUNNER_TEMP/gitleaks"',
    "git",
    "--redact",
    "--no-banner",
    "--exit-code",
    "1",
    "--config",
    ".gitleaks.toml",
    "--log-opts=HEAD",
    "--report-format",
    "json",
    "--report-path",
    '"$RUNNER_TEMP/gl.json"',
    ".",
    "||",
    "{",
]
CURL_FLAGS = [
    "-sSfL",
    "--retry",
    "5",
    "--retry-all-errors",
    "--retry-delay",
    "5",
    "--proto",
    '"=https"',
    "--tlsv1.2",
    "-o",
]
# step-name fragment -> (archive variable name, variable holding the expected sha256)
DOWNLOADS = {
    GL: ("gitleaks.tgz", "GITLEAKS_SHA256"),
    "Trivy": ("trivy.tgz", "TRIVY_SHA256"),
}


SECURITY_JOB_KEYS = {"if", "runs-on", "timeout-minutes", "steps"}
SECURITY_JOB_IF = "github.event_name != 'pull_request' || github.event.pull_request.draft == false"
WORKFLOW_ENV = {
    "GITLEAKS_VERSION": "8.30.1",
    "GITLEAKS_SHA256": "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    "TRIVY_VERSION": "0.76.0",
    "TRIVY_SHA256": "e24b1c51293c1b15e4ba8d45bbc7891ba053f90278ec2698f3562c993e145fe7",
}
SECURITY_STEP_NAMES = [
    None,  # actions/checkout
    None,  # astral-sh/setup-uv
    "Install the scanners (locked)",
    "Dependencies with known vulnerabilities (every locked package, hashes required)",
    "Python security lint",
    "Static analysis (Semgrep community rules)",
    "Workflow audit",
    "Stale gitleaks ignore entries (each commit must exist on a fetched branch and not on main; entries expire)",
    "Secrets in the history of the checked-out head (gitleaks, checksum-verified binary)",
    "Vulnerabilities, misconfigurations and secrets in the files (Trivy, checksum-verified binary)",
]
GOLDEN_COMMANDS = {
    "Secrets in the history": [
        (
            'curl -sSfL --retry 5 --retry-all-errors --retry-delay 5 --proto "=https" --tlsv1.2 -o "$RUNNER_TEMP/gitleaks.tgz"'
            '  "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"'
        ),
        'echo "${GITLEAKS_SHA256}  $RUNNER_TEMP/gitleaks.tgz" | sha256sum -c -',
        'tar -xzf "$RUNNER_TEMP/gitleaks.tgz" -C "$RUNNER_TEMP" gitleaks',
        (
            '"$RUNNER_TEMP/gitleaks" git --redact --no-banner --exit-code 1 --config .gitleaks.toml --log-opts=HEAD'
            '  --report-format json --report-path "$RUNNER_TEMP/gl.json" . || {'
        ),
        (
            'python3 -c \'import json,sys; [print(f["RuleID"], f["File"], f["StartLine"], f["Commit"][:10], f["Fingerprint"]) '
            'for f in json.load(open(sys.argv[1]))]\' "$RUNNER_TEMP/gl.json"'
        ),
        "exit 1",
        "}",
    ],
    "Trivy": [
        (
            'curl -sSfL --retry 5 --retry-all-errors --retry-delay 5 --proto "=https" --tlsv1.2 -o "$RUNNER_TEMP/trivy.tgz"'
            '  "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz"'
        ),
        'echo "${TRIVY_SHA256}  $RUNNER_TEMP/trivy.tgz" | sha256sum -c -',
        'tar -xzf "$RUNNER_TEMP/trivy.tgz" -C "$RUNNER_TEMP" trivy',
        '"$RUNNER_TEMP/trivy" fs --skip-dirs .venv --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 --no-progress .',
    ],
}


def check_structure(workflow):
    """Everything around the two steps: job keys, defaults, env, checkout, step order, and every command of both steps."""
    assert set(workflow) == {"name", True, "permissions", "concurrency", "env", "jobs"}, (
        "unexpected workflow keys"
    )
    assert workflow["env"] == WORKFLOW_ENV, "workflow env (versions, checksums) changed"
    job = workflow["jobs"]["security"]
    assert set(job) == SECURITY_JOB_KEYS, (
        f"unexpected security job keys: {sorted(set(job) ^ SECURITY_JOB_KEYS)}"
    )
    assert job["if"] == SECURITY_JOB_IF
    steps = job["steps"]
    assert [s.get("name") for s in steps] == SECURITY_STEP_NAMES, (
        "security steps changed or reordered"
    )
    assert steps[0]["with"] == {"persist-credentials": False, "fetch-depth": 0}, (
        "checkout inputs changed"
    )
    assert set(steps[0]) == {"uses", "with"}
    for fragment, golden in GOLDEN_COMMANDS.items():
        step = _step(workflow, fragment)
        assert set(step) == {"name", "run"}, f"step {fragment!r} has extra keys"
        assert _commands(step["run"]) == golden, (
            f"commands of the {fragment!r} step differ from the pinned list"
        )


def _security_steps(workflow):
    return workflow["jobs"]["security"]["steps"]


def _step(workflow, fragment):
    found = [s for s in _security_steps(workflow) if fragment in s.get("name", "")]
    assert len(found) == 1, f"expected exactly one security step naming {fragment!r}"
    return found[0]


def _commands(run):
    """Join backslash continuations; return the non-empty, non-comment logical lines."""
    joined = re.sub(r"\\\n\s*", " ", run)
    return [
        ln.strip() for ln in joined.splitlines() if ln.strip() and not ln.strip().startswith("#")
    ]


def _words(command):
    return shlex.split(command, posix=False)


def _check_step_is_plain(step):
    for key in ("continue-on-error", "if", "shell", "working-directory", "env"):
        assert key not in step, f"step {step.get('name')!r} must not set {key}"


def check_scan(workflow):
    check_structure(workflow)
    step = _step(workflow, GL)
    _check_step_is_plain(step)
    cmds = _commands(step["run"])
    scan = [c for c in cmds if "gitleaks" in c and " git " in c]
    assert len(scan) == 1, "exactly one gitleaks scan command"
    assert _words(scan[0]) == SCAN_WORDS, f"scan command is not the pinned one: {scan[0]}"
    # the failure handler: a python3 report line, then `exit 1`, then the closing brace, nothing else
    start = cmds.index(scan[0])
    handler = cmds[start + 1 :]
    assert handler[-2:] == ["exit 1", "}"], f"failure handler must end with exit 1: {handler}"
    assert len(handler) == 3 and handler[0].startswith("python3 -c "), (
        f"unexpected handler body: {handler}"
    )
    # nothing after the closing brace, nothing that rewrites the exit status between the lines
    assert not any(re.search(r"\b(exit\s+0|true|set\s+\+e)\b", c) for c in handler)
    checkout = _security_steps(workflow)[0]
    assert str(checkout["uses"]).startswith("actions/checkout@")
    assert checkout["with"]["fetch-depth"] == 0, "the ignore-list checks need the full history"


def check_downloads(workflow):
    check_structure(workflow)
    for fragment, (archive, sha_var) in DOWNLOADS.items():
        step = _step(workflow, fragment)
        _check_step_is_plain(step)
        run = step["run"]
        assert len(re.findall(r"\bcurl\b", run)) == 1, (
            "exactly one curl, at the start of its own command"
        )
        assert not re.search(r"\b(wget|sudo)\b|--insecure|\s-k\b|--retry-max-time|--max-time", run)
        cmds = _commands(run)
        curl = [c for c in cmds if c.startswith("curl ")]
        assert len(curl) == 1, f"the {fragment} download must be one plain curl command"
        words = _words(curl[0])
        assert words[0] == "curl"
        assert words[1 : 1 + len(CURL_FLAGS)] == CURL_FLAGS, f"curl flags differ: {curl[0]}"
        assert words[1 + len(CURL_FLAGS)] == f'"$RUNNER_TEMP/{archive}"'
        url = words[2 + len(CURL_FLAGS) :]
        assert len(url) == 1 and url[0].startswith('"https://github.com/'), url
        want = f'echo "${{{sha_var}}}  $RUNNER_TEMP/{archive}" | sha256sum -c -'
        assert want in cmds, f"checksum line missing for {fragment}"
        assert cmds.index(want) == cmds.index(curl[0]) + 1, (
            "checksum must directly follow the download"
        )
    return len(DOWNLOADS)


def _load():
    return yaml.safe_load(CI.read_text())


def test_real_ci_scan_is_limited_to_head_and_blocks():
    check_scan(_load())


def test_every_pinned_download_retries_and_keeps_its_checksum():
    assert check_downloads(_load()) == 2


def _mutate_run(workflow, fragment, old, new):
    w = copy.deepcopy(workflow)
    step = _step(w, fragment)
    if old not in step["run"]:
        raise ValueError(f"fixture: {old!r} not in the step")
    head, _sep, tail = step["run"].rpartition(old)
    step["run"] = head + new + tail
    return w


def _mutate_step(workflow, fragment, **extra):
    w = copy.deepcopy(workflow)
    _step(w, fragment).update(extra)
    return w


SCAN_BAD = [
    ("--log-opts=HEAD", "--log-opts=HEAD~1000"),
    ("--log-opts=HEAD", '--log-opts="HEAD --branches"'),
    ("--log-opts=HEAD", "--log-opts=--all"),
    ("--log-opts=HEAD ", ""),
    ("--exit-code 1", "--exit-code 0"),
    ("--exit-code 1", "--exit-code 1 --exit-code=0"),
    ("--config .gitleaks.toml", "--config .gitleaks.toml.bak"),
    (" || {", " ||  true || {"),
    (" || {", " ||true || {"),
    (" || {", " || exit 0 || {"),
    (" || {", " | cat || {"),
    ("  exit 1\n", "  exit 0\n"),
    ("  exit 1\n", ""),
    (' "$RUNNER_TEMP/gl.json" ', ' "$RUNNER_TEMP/gl.json" --baseline-path x '),
]


@pytest.mark.parametrize(("old", "new"), SCAN_BAD)
def test_the_scan_pin_rejects_a_neutered_scan(old, new):
    bad = _mutate_run(_load(), GL, old, new)
    with pytest.raises(AssertionError):
        check_scan(bad)


@pytest.mark.parametrize(
    "extra", [{"continue-on-error": True}, {"if": "false"}, {"shell": "bash {0}"}]
)
def test_the_scan_pin_rejects_a_step_that_can_be_skipped_or_ignored(extra):
    bad = _mutate_step(_load(), GL, **extra)
    with pytest.raises(AssertionError):
        check_scan(bad)


def test_the_scan_pin_needs_the_full_history():
    w = _load()
    _security_steps(w)[0]["with"]["fetch-depth"] = 1
    with pytest.raises(AssertionError):
        check_scan(w)


CURL_BAD = [
    ("--retry 5 ", ""),
    ("--retry 5 ", "--retry 0 --retry 5 "),
    ("--retry 5 ", "--retry 5 --retry 0 "),
    ("--retry-all-errors ", ""),
    ("--retry-delay 5 ", ""),
    ("--retry-delay 5 ", "--retry-delay 5 --retry-max-time 1 "),
    ("-sSfL", "-sSL"),
    ("-sSfL", "-sSfLk"),
    ("-sSfL", "-sSfL --insecure"),
    ("--tlsv1.2", ""),
    ('--proto "=https"', ""),
    ("curl ", "sudo curl "),
    ("sha256sum -c -", "sha256sum -c - || true"),
]


@pytest.mark.parametrize("fragment", [GL, "Trivy"])
@pytest.mark.parametrize(("old", "new"), CURL_BAD)
def test_the_download_pin_rejects_a_neutered_download(fragment, old, new):
    bad = _mutate_run(_load(), fragment, old, new)
    with pytest.raises(AssertionError):
        check_downloads(bad)


@pytest.mark.parametrize("fragment", [GL, "Trivy"])
def test_the_download_pin_needs_the_checksum_line(fragment):
    w = _load()
    step = _step(w, fragment)
    step["run"] = "\n".join(ln for ln in step["run"].splitlines() if "sha256sum" not in ln) + "\n"
    with pytest.raises(AssertionError):
        check_downloads(w)


def _edit(fn):
    w = copy.deepcopy(_load())
    fn(w)
    return w


STRUCTURE_BAD = {
    "job continue-on-error": lambda w: w["jobs"]["security"].update({"continue-on-error": True}),
    "job defaults shell": lambda w: w["jobs"]["security"].update(
        {"defaults": {"run": {"shell": "bash {0}"}}}
    ),
    "workflow defaults": lambda w: w.update({"defaults": {"run": {"shell": "bash {0}"}}}),
    "extra step": lambda w: w["jobs"]["security"]["steps"].append({"name": "x", "run": "true"}),
    "checkout ref": lambda w: w["jobs"]["security"]["steps"][0]["with"].update({"ref": "main"}),
    "job if": lambda w: w["jobs"]["security"].update({"if": "false"}),
    "env checksum": lambda w: w["env"].update({"GITLEAKS_SHA256": "0" * 64}),
    "set +e first": lambda w: _step(w, GL).update({"run": "set +e\n" + _step(w, GL)["run"]}),
    "exit 0 suffix": lambda w: _step(w, GL).update(
        {"run": _step(w, GL)["run"].rstrip("\n") + "\nexit 0\n"}
    ),
    "trivy or true": lambda w: _step(w, "Trivy").update(
        {"run": _step(w, "Trivy")["run"].rstrip("\n") + " || true\n"}
    ),
    "other url": lambda w: _step(w, GL).update(
        {"run": _step(w, GL)["run"].replace("github.com/gitleaks", "example.invalid/gitleaks")}
    ),
}


@pytest.mark.parametrize("name", sorted(STRUCTURE_BAD))
def test_the_structure_pin_rejects_a_bypass(name):
    bad = _edit(STRUCTURE_BAD[name])
    with pytest.raises(AssertionError):
        check_scan(bad)
    with pytest.raises(AssertionError):
        check_downloads(bad)
