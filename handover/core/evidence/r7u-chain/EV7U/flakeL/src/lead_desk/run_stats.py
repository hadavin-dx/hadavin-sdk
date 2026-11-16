"""Optional counters file: an adapter that is given a path writes its counters there after every change (a temporary
file, then os.replace), so a run script can read what the adapter really did even when the desk process was stopped
hard. `write_stats` swallows a failed write on purpose (a counter file must never break a send); `write_stats_strict`
raises it, and the one write that must be known to have worked uses it: the open create (`create_open`, see
crm_hubspot.py) is on disk BEFORE its request leaves.
What a test checks (tests/test_r7t_findings.py, t10): with the JSON dump or the os.replace made to fail, the previous
whole file stays in place and the target name is only ever changed by os.replace. What no test does: stop a real
process in the middle of a write or fill a real disk; the guarantee for those cases is os.replace itself (an atomic
rename on the same folder), which is relied on and not re-tested here.
Counts only: no address, no key, no text."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from lead_desk.regfile import open_output, refuse_replacing_special


def write_stats_strict(path: Path | None, data: Mapping[str, int]) -> None:
    """The same write, but a failure is raised (an OSError) and not swallowed: for the one write that must be known to
    have worked (the open create is written BEFORE the request leaves; see crm_hubspot)."""
    if path is None:
        return
    tmp = Path(f"{path}.tmp")
    refuse_replacing_special(path)  # before any byte: a replace would turn a device or a pipe into a plain file
    with open_output(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(dict(data), sort_keys=True))
    os.replace(tmp, path)


def write_stats(path: Path | None, data: Mapping[str, int]) -> None:
    try:
        write_stats_strict(path, data)
    except OSError:
        pass  # a counters file must never break a send or a put
