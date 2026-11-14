"""Prints, per test, the raw counts a runner must report: sample size, lost, doubled, unknown, failed, kill point reached, extras, money.  python count_table.py OUTDIR
Reads OUTDIR/*/mf_result_*.json (written by mf.py). Several runs of the same test are listed one under the other, never merged."""
import json, os, sys
for d in sorted(os.listdir(sys.argv[1])):
    for f in sorted(os.listdir(os.path.join(sys.argv[1], d))):
        if not f.startswith("mf_result_"): continue
        for t, r in json.load(open(os.path.join(sys.argv[1], d, f))).items():
            rows = r.get("per_lead") or []
            c = lambda fn: sum(1 for o in rows if isinstance(o, dict) and fn(o))
            print("%s [%s] %s sample=%d lost=%d doubled=%d unknown=%d failed=%d not_reached=%d" % (t, d, "PASS" if r.get("pass") else "FAIL", len(rows), c(lambda o: o.get("lost")), c(lambda o: o.get("doubled")),
                  c(lambda o: o.get("unknown")), c(lambda o: o.get("row", {}).get("state") == "failed"), c(lambda o: o.get("kill_point_reached") is False)))
            print("    ", str(r.get("why"))[:600])
