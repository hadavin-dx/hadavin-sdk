#!/usr/bin/env python3
"""Read-only structural check of n8n flow JSON files. Usage: check_flows.py DIR [DIR2 ...]
Prints counts only: per file node count, parse ok, unique names, dangling connections, orphans.
Orphan = node with no incoming connection that is not a trigger (type name contains 'Trigger' or 'webhook' or 'executeWorkflowTrigger' or 'formTrigger')."""
import json, os, sys, collections

def check(path):
    r = {"file": os.path.basename(path)}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        r["parse"] = "FAIL " + type(e).__name__
        return r
    r["parse"] = "ok"
    nodes = d.get("nodes", [])
    names = [n.get("name") for n in nodes]
    r["nodes"] = len(nodes)
    r["dup_names"] = sorted(k for k, v in collections.Counter(names).items() if v > 1)
    nameset = set(names)
    conns = d.get("connections", {})
    bad, targets, ncon = [], set(), 0
    for src, outs in conns.items():
        if src not in nameset:
            bad.append("source:" + src)
        for typ, lists in outs.items():
            for lst in lists:
                for c in lst or []:
                    ncon += 1
                    t = c.get("node")
                    targets.add(t)
                    if t not in nameset:
                        bad.append("target:" + str(t))
    r["connections"] = ncon
    r["dangling"] = bad
    def trig(n):
        t = n.get("type", "").lower()
        return "trigger" in t or "webhook" in t
    r["orphans"] = sorted(n["name"] for n in nodes if n["name"] not in targets and not trig(n))
    s = d.get("settings", {})
    r["saveDataSuccess"] = s.get("saveDataSuccessExecution")
    r["saveDataError"] = s.get("saveDataErrorExecution")
    return r

def main():
    for arg in sys.argv[1:]:
        files = [arg] if os.path.isfile(arg) else sorted(os.path.join(arg, x) for x in os.listdir(arg) if x.endswith(".json"))
        for p in files:
            r = check(p)
            print(arg if os.path.isfile(arg) else arg, "|", " ".join(f"{k}={v}" for k, v in r.items()))
main()
