"""Printable-share sweep (ticket G4, section 11, Phase 4). Read-only, in-process.

For `defaults.B64_PRINTABLE_SHARE` in 0.85, 0.875, 0.90, 0.925, 0.95 it computes, for every probe base64 row (`leak_of` verdict), every
MUST_KEEP_B64 row (digest against the fixture) and a set of TB-3 inputs (the output) whether the result differs from the 0.90 run.
Expected: no row changes. Usage (from the repo root): PYTHONPATH=. python handover/core-c/evidence/g4_share_sweep.py
"""

from __future__ import annotations

import base64
import json
import textwrap
from pathlib import Path

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
from tests import p1c_cases as pc

ROOT = Path(__file__).resolve().parents[3]
BASE = json.loads((ROOT / "tests/fixtures/p1c_base_digests.json").read_text())["rows"]
S12 = "Zq9" + "xW4" + "mT7" + "pL2"


def b64(x) -> str:
    return base64.b64encode(x.encode() if isinstance(x, str) else x).decode()


SB = b64("password=" + S12)
TB3 = [
    SB,
    SB + " and later " + S12 + " alone",
    b64(b64(b64(b64("status ok")))),
    b64(b64(b64("pwd=Zq9xW4m"))),
    "ADEAMAAuADIAMAAuADMAMAAuADQAMA==",
    b64("pwd=Kp7rTq2W"),
    "\n".join(textwrap.wrap(b64("2026-11-20 deploy db_password=" + S12 + " applied"), 32)),
    b64("http://u:Kp7rTq2W@h.io"),
    b64("curl -u user:Kp7rTq2W"),
    b64("this is just a status message"),
    b64("ok status 200"),
]


def results(share: float) -> list[str]:
    defaults.B64_PRINTABLE_SHARE = share
    out: list[str] = []
    for _id, protected, text in pc.build().b64:
        out.append(pc.leak_of(protected, runmap.redact_text(text, {}))[0])
    for k, text in pc.MUST_KEEP_B64:
        m: dict[str, str] = {}
        out.append(pc.digest(runmap.redact_text(text, m), m) == BASE[f"mustkeep-b64-{k}/text"])
    for text in TB3:
        m = {}
        out.append(runmap.redact_text(text, m) + json.dumps(sorted(m)))
    return out


def main() -> None:
    keep = defaults.B64_PRINTABLE_SHARE
    ref = results(0.90)
    for share in (0.85, 0.875, 0.90, 0.925, 0.95):
        got = results(share)
        changed = [i for i, (a, b) in enumerate(zip(ref, got, strict=True)) if a != b]
        print(f"share {share}: {len(changed)} of {len(got)} rows differ from 0.90", changed[:20])
    defaults.B64_PRINTABLE_SHARE = keep


if __name__ == "__main__":
    main()
