"""Pin the two security-job downloads and the gitleaks scan in ci.yml.

The scan must cover only the history reachable from the checked-out head and must block; each pinned
binary download must retry transient errors and keep its checksum, TLS and protocol limits. The checks
parse the workflow as YAML, split each command into shell words and compare them with an exact list,
so a neutered scan (`|| true`, `--exit-code=0`, another config, `continue-on-error`) cannot pass.
"""

import copy
import json
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
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
    "--connect-timeout",
    "30",
    "--proto",
    '"=https"',
    "--proto-redir",
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
    "System tools resolve outside the workspace",
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
            'curl -sSfL --retry 5 --retry-all-errors --retry-delay 5 --connect-timeout 30 --proto "=https" --proto-redir "=https" --tlsv1.2 -o "$RUNNER_TEMP/gitleaks.tgz"'
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
            'curl -sSfL --retry 5 --retry-all-errors --retry-delay 5 --connect-timeout 30 --proto "=https" --proto-redir "=https" --tlsv1.2 -o "$RUNNER_TEMP/trivy.tgz"'
            '  "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz"'
        ),
        'echo "${TRIVY_SHA256}  $RUNNER_TEMP/trivy.tgz" | sha256sum -c -',
        'tar -xzf "$RUNNER_TEMP/trivy.tgz" -C "$RUNNER_TEMP" trivy',
        '"$RUNNER_TEMP/trivy" fs --skip-dirs .venv --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 --no-progress .',
    ],
}


GOLDEN_FILE = Path(__file__).parent / "fixtures" / "ci_security_golden.json"


def check_golden(workflow):
    """The whole security job (every step, raw run text included, so a comment that ends in a backslash cannot hide a
    command), the workflow-level triggers, permissions, concurrency and env, and the id, name, runner and timeout of every job
    must equal the stored golden. An intended change to any of them means regenerating the golden in the same PR."""
    golden = json.loads(GOLDEN_FILE.read_text())
    top = {
        ("on" if k is True else k): workflow.get(k)
        for k in ("name", True, "permissions", "concurrency", "env")
    }
    assert top == golden["workflow"], (
        "workflow name/on/permissions/concurrency/env differ from the golden"
    )
    jobs = {
        jid: {k: j.get(k) for k in ("name", "runs-on", "timeout-minutes", "if")}
        for jid, j in workflow["jobs"].items()
    }
    assert jobs == golden["jobs"], "job ids, names, runners or timeouts differ from the golden"
    assert workflow["jobs"]["security"] == golden["security_job"], (
        "the security job differs from the golden"
    )


GITLEAKS_GOLDEN = Path(__file__).parent / "fixtures" / "gitleaks_config_golden.json"


def check_gitleaks_config(root=None, golden_path=None):
    """The scan reads .gitleaks.toml from the PR's own tree. The parsed file must equal the stored golden, every allowlist
    must be path-scoped with condition AND, and its paths may match tracked files only in the places the golden allows."""
    root = root or CI.parents[2]
    cfg = tomllib.loads((root / ".gitleaks.toml").read_text())
    assert cfg == json.loads((golden_path or GITLEAKS_GOLDEN).read_text()), (
        ".gitleaks.toml differs from the golden"
    )
    assert set(cfg) <= {"extend", "allowlists"}, f"unexpected top-level keys: {sorted(cfg)}"
    assert cfg.get("extend") == {"useDefault": True}, "must extend the default rules"
    tracked = subprocess.run(  # noqa: S603 (fixed argv, no shell)
        [shutil.which("git") or "git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    for al in cfg["allowlists"]:
        assert al.get("condition") == "AND" and al.get("paths"), "allowlist must be path-scoped"
        assert not al.get("commits") and not al.get("stopwords"), "no commit or stopword allowlists"
        for pat in al["paths"]:
            hit = [f for f in tracked if re.search(pat, f)]
            assert all(
                f in ALLOWED_HITS or re.match(r"handover/(reviews|tickets|evidence)/[^/]+\.md$", f)
                for f in hit
            ), f"allowlist path {pat!r} reaches {[f for f in hit if f not in ALLOWED_HITS][:3]}"


ALLOWED_HITS = {"tests/demo_askdata/test_demo_literals.py", "tests/fixtures/textnorm_golden.json"}


def check_other_workflows():
    """No other workflow file may carry a job that could stand in for a required check, or run with write power on forks."""
    wf_dir = CI.parent
    for f in sorted(wf_dir.glob("*.y*ml")):
        if f.name == CI.name:
            continue
        w = yaml.load(f.read_text(), Loader=_StrictLoader)  # noqa: S506 (SafeLoader subclass)
        trig = w.get(True) or w.get("on") or {}
        names = set(trig if isinstance(trig, (dict, list)) else [trig])
        assert "pull_request_target" not in names and "workflow_run" not in names, (
            f"{f.name}: unsafe trigger"
        )
        for jid, job in (w.get("jobs") or {}).items():
            assert jid not in REQUIRED_NAMES and job.get("name") not in REQUIRED_NAMES, (
                f"{f.name}: job {jid!r} reuses a required check name"
            )


REQUIRED_NAMES = {"security", "check", "tests-py312"}


def check_structure(workflow, golden=True):
    """Everything around the two steps: job keys, defaults, env, checkout, step order, and every command of both steps.
    golden=False skips the golden compare so the negative tests can prove the checks below it can fail on their own."""
    if golden:
        check_golden(workflow)
    check_other_workflows()
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
    for fragment, pinned in GOLDEN_COMMANDS.items():
        step = _step(workflow, fragment)
        assert set(step) == {"name", "run"}, f"step {fragment!r} has extra keys"
        assert _commands(step["run"]) == pinned, (
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


def check_scan(workflow, golden=True):
    check_structure(workflow, golden)
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


def check_downloads(workflow, golden=True):
    check_structure(workflow, golden)
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


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses a duplicate mapping key (PyYAML would silently keep the last one)."""


def _no_duplicates(loader, node, deep=False):
    keys = [loader.construct_object(k, deep=deep) for k, _ in node.value]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise AssertionError(f"duplicate YAML keys: {sorted(map(str, dup))}")
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def _load():
    return yaml.load(CI.read_text(), Loader=_StrictLoader)  # noqa: S506 (SafeLoader subclass)


def regenerate_goldens():
    """After an INTENDED change to ci.yml or .gitleaks.toml: `python tests/test_ci_gitleaks_scope.py`, then review the diff of
    tests/fixtures/*golden.json in the same PR (the reviewer reads that diff, not the test)."""
    w = _load()
    keep = {
        ("on" if k is True else k): w.get(k)
        for k in ("name", True, "permissions", "concurrency", "env")
    }
    jobs = {
        jid: {k: j.get(k) for k in ("name", "runs-on", "timeout-minutes", "if")}
        for jid, j in w["jobs"].items()
    }
    GOLDEN_FILE.write_text(
        json.dumps(
            {"workflow": keep, "jobs": jobs, "security_job": w["jobs"]["security"]},
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    cfg = tomllib.loads((CI.parents[2] / ".gitleaks.toml").read_text())
    GITLEAKS_GOLDEN.write_text(json.dumps(cfg, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    regenerate_goldens()


def test_real_ci_scan_is_limited_to_head_and_blocks():
    check_scan(_load())


def test_the_gitleaks_config_has_only_narrow_path_allowlists():
    check_gitleaks_config()


BAD_TOML = {
    "blanket": "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\npaths = ['''.*''']\n",
    "demos": "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\npaths = ['''^demos/''']\n",
    "no extend": "[[allowlists]]\ncondition = \"AND\"\npaths = ['''^handover/''']\n",
    "extra key": "[extend]\nuseDefault = true\n[allowlist]\npaths = ['x']\n",
    "or condition": "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"OR\"\npaths = ['''^handover/x\\.md$''']\n",
    "commit allowlist": "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\ncommits = [\"abc\"]\npaths = ['''^handover/x\\.md$''']\n",
    "stopwords": "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\nstopwords = [\"x\"]\npaths = ['''^handover/x\\.md$''']\n",
}


def _tracked_repo(tmp_path, toml):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    (tmp_path / ".gitleaks.toml").write_text(toml)
    (tmp_path / "demos").mkdir()
    (tmp_path / "demos" / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607
    # a golden equal to this config, so only the checks after the golden compare can fail
    golden = tmp_path / "golden.json"
    golden.write_text(json.dumps(tomllib.loads(toml)))
    return golden


@pytest.mark.parametrize("name", sorted(BAD_TOML))
def test_the_gitleaks_config_pin_rejects_a_widened_config(name, tmp_path):
    golden = _tracked_repo(tmp_path, BAD_TOML[name])
    with pytest.raises(AssertionError):
        check_gitleaks_config(tmp_path, golden)


def test_the_gitleaks_config_pin_reaches_the_tracked_file_check(tmp_path):
    ok = "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\npaths = ['''^demos/a\\.py$''']\n"
    golden = _tracked_repo(tmp_path, ok)
    with pytest.raises(AssertionError, match="reaches"):
        check_gitleaks_config(tmp_path, golden)  # a tracked file outside the allowed set is refused


def test_the_gitleaks_config_pin_accepts_an_allowed_tracked_file(tmp_path):
    ok = "[extend]\nuseDefault = true\n[[allowlists]]\ncondition = \"AND\"\npaths = ['''^tests/demo_askdata/test_demo_literals\\.py$''']\n"
    golden = _tracked_repo(tmp_path, ok)
    (tmp_path / "tests" / "demo_askdata").mkdir(parents=True)
    (tmp_path / "tests" / "demo_askdata" / "test_demo_literals.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)  # noqa: S603, S607
    check_gitleaks_config(tmp_path, golden)  # positive control


def test_another_workflow_cannot_reuse_a_required_check_name(tmp_path, monkeypatch):
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("name: x\n")
    (wf / "other.yml").write_text("name: o\non: push\njobs:\n  security:\n    runs-on: x\n")
    monkeypatch.setattr(sys.modules[__name__], "CI", wf / "ci.yml")
    with pytest.raises(AssertionError):
        check_other_workflows()
    (wf / "other.yml").write_text("name: o\non: pull_request_target\njobs:\n  a:\n    runs-on: x\n")
    with pytest.raises(AssertionError):
        check_other_workflows()


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
        check_scan(bad, golden=False)


@pytest.mark.parametrize(
    "extra", [{"continue-on-error": True}, {"if": "false"}, {"shell": "bash {0}"}]
)
def test_the_scan_pin_rejects_a_step_that_can_be_skipped_or_ignored(extra):
    bad = _mutate_step(_load(), GL, **extra)
    with pytest.raises(AssertionError):
        check_scan(bad, golden=False)


def test_the_scan_pin_needs_the_full_history():
    w = _load()
    _security_steps(w)[0]["with"]["fetch-depth"] = 1
    with pytest.raises(AssertionError):
        check_scan(w, golden=False)


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
        check_downloads(bad, golden=False)


@pytest.mark.parametrize("fragment", [GL, "Trivy"])
def test_the_download_pin_needs_the_checksum_line(fragment):
    w = _load()
    step = _step(w, fragment)
    step["run"] = "\n".join(ln for ln in step["run"].splitlines() if "sha256sum" not in ln) + "\n"
    with pytest.raises(AssertionError):
        check_downloads(w, golden=False)


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
    "comment backslash hides a command": lambda w: _step(w, GL).update(
        {"run": _step(w, GL)["run"].replace("# ", "# x \\\ntrap 'exit 0' EXIT\n# ", 1)}
    ),
    "setup-uv replaced": lambda w: _security_steps(w)[1].update(
        {"run": "echo bad >> $GITHUB_PATH"}
    ),
    "pip-audit neutered": lambda w: _step(w, "Dependencies with known").update(
        {"run": _step(w, "Dependencies with known")["run"].rstrip("\n") + " || true\n"}
    ),
    "stale-ignore skipped": lambda w: _step(w, "Stale gitleaks").update(
        {"continue-on-error": True}
    ),
    "trigger dropped": lambda w: w.pop(True),
    "runner changed": lambda w: w["jobs"]["security"].update({"runs-on": "self-hosted"}),
    "second security-named job": lambda w: w["jobs"].update(
        {"x": {"name": "security", "runs-on": "ubuntu-24.04"}}
    ),
    "tool shadow check dropped": lambda w: _security_steps(w).pop(3),
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


# These edits touch parts that only the golden pins (steps other than the two pinned commands, the runner, job names).
GOLDEN_ONLY = {
    "comment backslash hides a command",
    "pip-audit neutered",
    "runner changed",
    "second security-named job",
    "setup-uv replaced",
    "stale-ignore skipped",
}


@pytest.mark.parametrize("name", sorted(set(STRUCTURE_BAD) - GOLDEN_ONLY))
def test_the_structure_checks_reject_a_bypass_without_the_golden(name):
    bad = _edit(STRUCTURE_BAD[name])
    with pytest.raises(AssertionError):
        check_scan(bad, golden=False)
    with pytest.raises(AssertionError):
        check_downloads(bad, golden=False)


def test_the_golden_only_list_names_real_cases():
    assert GOLDEN_ONLY <= set(STRUCTURE_BAD)
