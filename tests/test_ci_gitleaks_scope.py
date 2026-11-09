"""The CI secret scan covers only commits reachable from the checked-out head, never every fetched branch."""

import re
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _scan_command() -> str:
    text = CI.read_text(encoding="utf-8")
    m = re.search(r'"\$RUNNER_TEMP/gitleaks" git [^\n]*\\\n[^\n]*', text)
    assert m, "the gitleaks scan command is missing from ci.yml"
    return m.group(0)


def test_gitleaks_scan_is_limited_to_the_head_history():
    cmd = _scan_command()
    assert "--log-opts=HEAD" in cmd
    assert "--all" not in cmd
