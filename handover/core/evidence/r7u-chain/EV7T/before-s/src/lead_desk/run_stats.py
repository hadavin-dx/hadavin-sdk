"""Optional counters file: an adapter that is given a path writes its counters there after every change (a temporary
file, then os.replace; no test checks atomicity), so a run script can read what the adapter really did even when the
desk process was stopped hard.
Counts only: no address, no key, no text."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from lead_desk.regfile import open_output, refuse_replacing_special


def write_stats(path: Path | None, data: Mapping[str, int]) -> None:
    if path is None:
        return
    tmp = Path(f"{path}.tmp")
    try:
        refuse_replacing_special(path)  # before any byte: a replace would turn a device or a pipe into a plain file
        with open_output(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(dict(data), sort_keys=True))
        os.replace(tmp, path)
    except OSError:
        pass  # a counters file must never break a send or a put
