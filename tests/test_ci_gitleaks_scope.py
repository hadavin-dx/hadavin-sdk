"""The CI secret scan covers only commits reachable from the checked-out head, never every fetched branch."""

import re
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _scan_command() -> str:
    """The whole gitleaks scan command, continuation lines joined (the step ends at the first line without a trailing backslash)."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    start = [
        i for i, ln in enumerate(lines) if ln.lstrip().startswith('"$RUNNER_TEMP/gitleaks" git ')
    ]
    assert len(start) == 1, "exactly one gitleaks scan command is expected in ci.yml"
    parts = []
    for ln in lines[start[0] :]:
        parts.append(ln.strip().rstrip("\\").strip())
        if not ln.rstrip().endswith("\\"):
            break
    return " ".join(parts)


def test_gitleaks_scan_is_limited_to_the_head_history():
    cmd = _scan_command()
    assert re.findall(r"--log-opts\S*", cmd) == ["--log-opts=HEAD"], (
        "the scope must be exactly the head history"
    )
    assert not re.search(r"--(?:all|branches|remotes|tags)\b", cmd)
