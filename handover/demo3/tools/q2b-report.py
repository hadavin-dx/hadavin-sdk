#!/usr/bin/env python3
"""Q2b: build evidence/identity-fuzz-b.md from the JSON files in /home/user/work/q2b-logs (records only)."""
import json, sys, glob, os
L = "/home/user/work/q2b-logs"
seeds = [7001, 7002, 7003, 7004, 7005]
rows, body = [], []
und_total = {}
for s in seeds:
    for c in "abcd":
        f = f"{L}/s{s}-{c}.json"
        if not os.path.exists(f):
            rows.append(f"| {s} | {c} | NOT RUN / no file | - | - | - |"); continue
        d = json.load(open(f))
        cases = d.get("variants_sent") or d.get("pairs") or d.get("replays") or d.get("requests_sent")
        und = sum(v for k, v in d["label_counts"].items() if k.startswith("UNDOCUMENTED"))
        rows.append(f"| {s} | {c} | {cases} | {d['violations']} | {und} | {d['wall_s']} s |")
        body.append((s, c, d))
out = ["# Identity fuzz, second seed set (Q2b)", "",
       "Evidence runner output; records only, no judgement. Base: public main f3c39cf8. Harness: `tools/q2b-fuzz.py` (copy of q2-fuzz.py; campaigns a, b, c unchanged; campaign d added with the extra generators). Driver: `tools/q2b-run.sh`.", "",
       "Case column: a = variants sent, b = pairs (2 requests each), c = replays, d = total requests (base + 4 name variants + about 55 extra-form variants per base).",
       "Sizes were reduced from Q2's defaults to fit the time box: b = 40000 pairs (Q2: 200000), c = 5000 replays (Q2: 20000), a = 2400 bases, d = 1200 bases.", "",
       "| seed | campaign | cases | violations | undocumented | wall |", "|---|---|---|---|---|---|"] + rows + [""]
out.append("## Counterexamples (verbatim, up to 50 per campaign and seed; ascii() so invisible characters show)\n")
for s, c, d in body:
    out.append(f"### seed {s}, campaign {c}: listed {d['counterexamples_listed']} of {d['counterexamples_total']}")
    out.append("label counts: " + json.dumps(d["label_counts"], ensure_ascii=True))
    for ce in d["counterexamples"]:
        out.append("- `" + json.dumps(ce, ensure_ascii=True) + "`")
    if c == "d":
        out.append("per-class tally: `" + json.dumps(d["tally"], ensure_ascii=True) + "`")
        for k, v in d["doc_samples"].items():
            for x in v[:1]:
                out.append(f"- sample [{k}] `" + json.dumps(x, ensure_ascii=True) + "`")
    out.append("")
open(sys.argv[1], "w").write("\n".join(out))
