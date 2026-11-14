"""Lease 45 s section (film-v4 flows): per point n, states, recovery and kill-to-final seconds (median, max). Own numbers only."""
import collections
import json
import statistics
K = "/home/user/work/kill"
g = collections.defaultdict(list)
for x in open(K + "/results.jsonl", encoding="utf-8"):
    r = json.loads(x)
    if str(r.get("label", "")).startswith(("fl45", "v4k")) and r.get("states") and r.get("recovery_s") is not None:
        s = r["states"][0]
        c = r["counts"][s[0]]
        g[(r["flows"], r["point"])].append((s[1], c["mail_to_intake"], c["alert"], c["crm_rows"], r["recovery_s"], r.get("kill_to_final_s")))
print("| flows | point | n | final state(s) | intake mails | alerts | CRM rows | recovery s median / max | kill to final s median / max |")
print("|---|---|---|---|---|---|---|---|---|")
for (fl, p), v in sorted(g.items()):
    f = lambda i: "/".join(sorted({str(t[i]) for t in v}))
    rec = [t[4] for t in v]
    ktf = [t[5] for t in v if t[5] is not None]
    print("| %s | %s | %d | %s | %s | %s | %s | %.1f / %.1f | %s |" % (fl, p, len(v), f(0), f(1), f(2), f(3), statistics.median(rec), max(rec),
          ("%.1f / %.1f" % (statistics.median(ktf), max(ktf))) if ktf else "not recorded"))
