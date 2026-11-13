#!/usr/bin/env python3
"""Builds the counterexample/tally sections of identity-fuzz.md from the JSON results (no judging). Usage: q2-report.py R1 [R2...]"""

import json
import sys
from pathlib import Path

L = Path("/home/user/work/q2-logs")
out = []
for r in sys.argv[1:]:
    out.append(f"\n## Round {r}: raw results\n")
    for c in "abc":
        p = L / f"r{r}-{c}.json"
        if not p.exists():
            out.append(f"### Campaign {c}: NO RESULT FILE ({p.name} missing)\n")
            continue
        d = json.loads(p.read_text())
        head = {k: v for k, v in d.items() if k not in ("counterexamples", "tally", "doc_samples", "pair_types", "label_counts", "kinds", "rows")}
        out.append(f"### Campaign {c} (seed {d['seed']})\n")
        out.append("Summary: `" + json.dumps(head) + "`\n")
        for k in ("label_counts", "pair_types", "kinds", "rows"):
            if k in d:
                out.append(f"{k}: `{json.dumps(d[k])}`\n")
        out.append(f"Counterexamples: {d['counterexamples_total']} total, {d['counterexamples_listed']} listed verbatim below (ascii() of each input).\n")
        if d["counterexamples"]:
            out.append("```")
            for x in d["counterexamples"]:
                out.append(json.dumps(x, ensure_ascii=True))
            out.append("```\n")
        out.append("Outcome tally per class: `" + json.dumps(d.get("tally", {})) + "`\n")
        if d.get("doc_samples"):
            out.append("Samples of documented-different / documented-rejected forms (up to 3 per class):\n```")
            for k, v in d["doc_samples"].items():
                for x in v:
                    out.append(k + " " + json.dumps(x, ensure_ascii=True))
            out.append("```\n")
print("\n".join(out))
