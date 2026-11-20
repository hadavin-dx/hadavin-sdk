"""Writes tests/fixtures/p1c_base_digests.json: the digests of what the BASE commit's redactor does with the P1c rows (ticket G4, section 11).

Run it in the base worktree (a checkout of the commit before G4), never on the branch under test:

    python tests/fixtures/make_p1c_base_digests.py > tests/fixtures/p1c_base_digests.json

Schema: {"base": "<base sha, 40 hex>", "python": "<x.y.z>", "rows": {"<key>": "<sha256 hex>"}}. Keys are `<id>/text` and
`<id>/untrusted` (the output of `redact_text` / `redact_untrusted` for a fresh `{}` map) for the ids of tests/test_p1c_gaps.py.
Digests, not outputs: no fake secret value is written. Not collected by pytest.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from hadavin_sdk.guard import runmap
from tests import p1c_cases
from tests.warden_port import privacy_corpus


def privacy_rows() -> list[tuple[str, str]]:
    """`masked-NN` (every text of MASKED in dict order, values flattened, 1-based) then `kept-NN` (KEPT)."""
    rows = [f for texts in privacy_corpus.MASKED.values() for f in texts]
    out = [(f"masked-{k:02d}", t) for k, t in enumerate(rows, start=1)]
    return out + [(f"kept-{k:02d}", t) for k, t in enumerate(privacy_corpus.KEPT, start=1)]


def all_inputs() -> list[tuple[str, str]]:
    c = p1c_cases.build()
    rows: list[tuple[str, str]] = [(i, t) for i, _p, t in c.b64]
    rows += [(i, t) for i, _n, t in c.hosts]
    rows += [(i, t) for i, _n, t in c.numbers]
    rows += [(f"mustkeep-b64-{k}", t) for k, t in p1c_cases.MUST_KEEP_B64]
    rows += privacy_rows()
    rows += [(f"hostkeep-{k}", t) for k, t in p1c_cases.HOST_MUST_KEEP]
    return rows


def run(fn, text: str) -> str:
    mapping: dict[str, str] = {}
    try:
        out = fn(text, mapping)
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        return p1c_cases.digest(f"RAISED {type(exc).__name__}", {})
    return p1c_cases.digest(out, mapping)


def main() -> None:
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607 - fixed argv
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    rows: dict[str, str] = {}
    for row_id, text in all_inputs():
        rows[f"{row_id}/text"] = run(runmap.redact_text, text)
        rows[f"{row_id}/untrusted"] = run(runmap.redact_untrusted, text)
    print(
        json.dumps(
            {"base": base, "python": platform.python_version(), "rows": rows},
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
