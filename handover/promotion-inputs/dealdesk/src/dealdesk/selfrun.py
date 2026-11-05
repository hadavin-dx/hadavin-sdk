"""Deterministic self-run used by the segregation test (segregation): runs one fixed scenario on the committed synthetic data and prints the sha256 of every
output (store contents + audit head). `--root` is the demo folder; an audit hook records every file this process OPENS under the parent of the root and
fails if any lies outside the root (a sibling demo's folder must never be read). Output is byte-identical whether other demos exist or not."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]).resolve()
    parent, outside = root.parent, []

    def hook(event, args):
        if event == "open" and isinstance(args[0], (str, Path)):
            try:
                p = Path(args[0]).resolve()
            except OSError:
                return
            if parent in p.parents and root not in p.parents and p != root:
                outside.append(str(p))

    sys.addaudithook(hook)
    sys.path[:0] = [str(root / "tests"), str(root / "src")]
    from engine_kit import STD, Kit, mk_deal  # test builders reused so the scenario equals the tested one

    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works", seats=40)])
    r = k.propose("deal-7001", {**STD, "discount_bps": 1500}, ["liability_cap_2x"])
    k.desk.request_approval("agent_runtime", r["quote_id"])
    k.approve_all(r["quote_id"], {"commercial": "p-sm-01", "legal": "p-lc-01"})
    k.desk.draft_quote("draft_writer", r["quote_id"])
    k.ex.commit("commit_executor", r["quote_id"], dry_run=False)
    blob = json.dumps(k.store.all_items(), sort_keys=True).encode()
    print(
        json.dumps(
            {"store_sha256": hashlib.sha256(blob).hexdigest(), "audit_head": k.desk.audit.head(), "outside_reads": outside}
        )
    )
    return 1 if outside else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
