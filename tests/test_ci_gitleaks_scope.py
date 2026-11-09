"""The CI secret scan covers only commits reachable from the checked-out head, never every fetched branch, and still blocks."""

import re
from pathlib import Path

import pytest

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
START = '"$RUNNER_TEMP/gitleaks" git '


def _scan_command(text: str) -> str:
    """The scan command with continuation lines joined the way bash joins them.

    Bash continues a line only when the backslash is the very last character; a comment line or a trailing space
    inside the span ends the command, so either one makes this parser fail instead of guessing.
    """
    lines = text.splitlines()
    start = [i for i, ln in enumerate(lines) if ln.lstrip().startswith(START)]
    assert len(start) == 1, "exactly one gitleaks scan command is expected in ci.yml"
    parts = []
    for ln in lines[start[0] :]:
        assert not ln.lstrip().startswith("#"), (
            "a comment line inside the scan command ends it in bash"
        )
        assert ln == ln.rstrip(), "trailing space after the last character ends the command in bash"
        parts.append(ln.strip().removesuffix("\\").strip())
        if not ln.endswith("\\"):
            break
    return " ".join(parts)


def check_scan(text: str) -> None:
    cmd = _scan_command(text)
    assert re.findall(r"--log-opts\S*", cmd) == ["--log-opts=HEAD"], (
        "the scope must be exactly the head history"
    )
    assert not re.search(r"--(?:all|branches|remotes|tags)\b", cmd)
    assert re.findall(r"--exit-code\s+\S+", cmd) == ["--exit-code 1"], (
        "the scan must block on a finding"
    )
    assert "#" not in cmd, "a comment inside the command swallows the rest of its line in bash"
    assert "--config .gitleaks.toml" in cmd
    assert "|| true" not in cmd and "|| :" not in cmd


def test_real_ci_scan_is_limited_to_head_and_blocks():
    check_scan(CI.read_text(encoding="utf-8"))


def _variant(old: str, new: str) -> str:
    text = CI.read_text(encoding="utf-8")
    assert old in text
    head, _sep, tail = text.rpartition(
        old
    )  # the last occurrence: the scan command, not a comment above it
    return head + new + tail


def test_the_pin_rejects_wrong_scopes_and_neutered_scans():
    bad = [
        _variant("--log-opts=HEAD", "--log-opts=HEAD~1000"),
        _variant("--log-opts=HEAD", '--log-opts="HEAD --branches"'),
        _variant("--log-opts=HEAD", "--log-opts=HEAD --log-opts=--all"),
        _variant("--log-opts=HEAD \\", ""),
        _variant("--exit-code 1 --config", "--exit-code 0 --config"),
        _variant("--log-opts=HEAD \\", "--log-opts=HEAD \\ "),
        _variant("--log-opts=HEAD \\\n", "# note \\\n            --log-opts=HEAD \\\n"),
        _variant(" . || {", " . || true || {"),
    ]
    for text in bad:
        try:
            check_scan(text)
        except AssertionError:
            continue
        raise AssertionError("a wrong or neutered scan command passed the pin")


def _curl_commands(text):
    """Every `curl ...` command in the workflow, with its continuation lines joined."""
    out, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if cur is None and re.match(r"curl\s", s):
            cur = s
        elif cur is not None:
            cur += " " + s
        if cur is not None and not cur.endswith("\\"):
            out.append(cur.replace("\\", " "))
            cur = None
        elif cur is not None:
            cur = cur[:-1]
    return out


def check_curl_retries(text):
    cmds = _curl_commands(text)
    assert cmds, "no curl download found: the pin would check nothing"
    for cmd in cmds:
        for flag in ("--retry 5", "--retry-all-errors", "--retry-delay 5", "-f"):
            assert re.search(rf"(^|\s){re.escape(flag)}(\s|$)", cmd) or (
                flag == "-f" and re.search(r"\s-\w*f\w*\s", cmd)
            ), f"curl without {flag}: {cmd}"
    return len(cmds)


def test_every_curl_download_retries_transient_errors():
    # A 504 from the release host must not fail a pull request (class fix).
    assert check_curl_retries(CI.read_text()) == 2


def test_the_curl_pin_rejects_a_download_without_retry():
    text = CI.read_text()
    for old, new in (
        ("--retry 5 ", ""),
        ("--retry-all-errors ", ""),
        ("--retry-delay 5 ", ""),
        ("curl -sSfL", "curl -sSL"),
    ):
        bad = text.replace(old, new, 1)
        assert bad != text
        with pytest.raises(AssertionError):
            check_curl_retries(bad)
