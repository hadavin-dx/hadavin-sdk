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
    assert old in step["run"], f"fixture: {old!r} not in the step"
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
    with pytest.raises(AssertionError):
        check_scan(_mutate_run(_load(), GL, old, new))


@pytest.mark.parametrize(
    "extra", [{"continue-on-error": True}, {"if": "false"}, {"shell": "bash {0}"}]
)
def test_the_scan_pin_rejects_a_step_that_can_be_skipped_or_ignored(extra):
    with pytest.raises(AssertionError):
        check_scan(_mutate_step(_load(), GL, **extra))


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
    with pytest.raises(AssertionError):
        check_downloads(_mutate_run(_load(), fragment, old, new))


@pytest.mark.parametrize("fragment", [GL, "Trivy"])
def test_the_download_pin_needs_the_checksum_line(fragment):
    w = _load()
    step = _step(w, fragment)
    step["run"] = "\n".join(ln for ln in step["run"].splitlines() if "sha256sum" not in ln) + "\n"
    with pytest.raises(AssertionError):
        check_downloads(w)
