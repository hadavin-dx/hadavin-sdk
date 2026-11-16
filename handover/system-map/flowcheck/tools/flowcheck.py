"""flowcheck.py: offline mechanical check of n8n workflow JSON files. Standard library only, no network.
Usage: python3 -I flowcheck.py FILE.json [FILE.json ...]   -> Markdown on stdout. Self-test: python3 -I flowcheck.py --selftest
Checks: parses; duplicate node names; connections name existing nodes; orphan nodes (no way in, not a trigger); unreachable from a trigger;
$('Name') references name an existing node; error settings table; alwaysOutputData with continueErrorOutput (the F-002 pattern);
continueErrorOutput with the error output (index 1) not wired; external-call ancestors of every mail or CRM write and how their errors are handled;
$env reads; credentials per node; webhooks without authentication; saveExecution settings."""
import json, re, sys, os
TRIG = re.compile(r"(Trigger$|\.webhook$|\.cron$|\.start$)")
REF = re.compile(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)")
ENV = re.compile(r"\$env\.([A-Za-z0-9_]+)|\$env\[['\"]([^'\"]+)['\"]\]")
WRITE_T = ("emailSend", "hubspot", "httpRequest")
EXT_T = ("postgres", "httpRequest", "hubspot", "emailSend", "executeWorkflow")
def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
def short(t): return t.split(".")[-1]
def is_write(n):
    t = short(n["type"])
    if t in ("emailSend", "hubspot"): return True
    if t == "httpRequest": return str(n.get("parameters", {}).get("method", "GET")).upper() != "GET"
    return False
def check(w):
    """returns dict of findings and tables for one parsed workflow"""
    R = {"fail": [], "info": {}}
    nodes = w.get("nodes", []); names = [n["name"] for n in nodes]; S = set(names)
    dup = sorted({x for x in names if names.count(x) > 1})
    if dup: R["fail"].append("duplicate node names: " + ", ".join(dup))
    edges = []; con = w.get("connections", {})
    for a, outs in con.items():
        if a not in S: R["fail"].append("connection source names no node: " + a)
        for k, lists in outs.items():
            for i, lst in enumerate(lists):
                for e in lst or []:
                    edges.append((a, i, e["node"]))
                    if e["node"] not in S: R["fail"].append("connection %s[%d] targets missing node: %s" % (a, i, e["node"]))
    inc = {n: 0 for n in names}
    for a, i, b in edges:
        if b in inc: inc[b] += 1
    trig = [n["name"] for n in nodes if TRIG.search(n["type"])]
    orph = [n for n in names if inc[n] == 0 and n not in trig]
    if orph: R["fail"].append("orphan nodes (no way in, not a trigger): " + ", ".join(orph))
    seen = set(trig); st = list(trig)
    while st:
        x = st.pop()
        for a, i, b in edges:
            if a == x and b not in seen and b in S: seen.add(b); st.append(b)
    unr = [n for n in names if n not in seen and n not in orph]
    if unr: R["fail"].append("unreachable from a trigger: " + ", ".join(unr))
    if not trig: R["fail"].append("no trigger node")
    bad = []
    for n in nodes:
        for s in strings(n.get("parameters", {})):
            for m in REF.findall(s):
                if m not in S: bad.append("%s -> $('%s')" % (n["name"], m))
    if bad: R["fail"].append("$('Name') names no node: " + "; ".join(sorted(set(bad))))
    rows = []; envs = {}; creds = []; webh = []
    wired = {(a, i) for a, i, b in edges}
    for n in nodes:
        oe = n.get("onError", "(default: stop)"); rt = "yes x%s" % n.get("maxTries", 3) if n.get("retryOnFail") else "no"; ao = "yes" if n.get("alwaysOutputData") else "no"
        flag = []
        if n.get("alwaysOutputData") and n.get("onError") == "continueErrorOutput":
            flag.append("alwaysOutputData+continueErrorOutput"); R["fail"].append("%s: alwaysOutputData together with continueErrorOutput (F-002 pattern)" % n["name"])
        if n.get("onError") == "continueErrorOutput" and (n["name"], 1) not in wired:
            flag.append("error output not wired"); R["fail"].append("%s: continueErrorOutput but output 1 (error) is not wired" % n["name"])
        rows.append((n["name"], short(n["type"]), oe, rt, ao, "; ".join(flag) or "-"))
        for s in strings(n.get("parameters", {})):
            for m in ENV.findall(s): envs.setdefault(m[0] or m[1], set()).add(n["name"])
        for k, v in (n.get("credentials") or {}).items(): creds.append((n["name"], short(n["type"]), k, v.get("name"), v.get("id")))
        if short(n["type"]) == "webhook":
            au = n.get("parameters", {}).get("authentication", "none")
            webh.append((n["name"], n.get("parameters", {}).get("httpMethod", "GET"), n.get("parameters", {}).get("path"), au))
            if au in ("none", None): R["fail"].append("%s: webhook without authentication" % n["name"])
    R["info"]["rows"] = rows; R["info"]["env"] = {k: sorted(v) for k, v in envs.items()}; R["info"]["creds"] = creds; R["info"]["webhooks"] = webh
    s = w.get("settings", {}); R["info"]["save"] = {k: s.get(k) for k in ("saveDataSuccessExecution", "saveDataErrorExecution", "saveManualExecutions", "executionOrder", "errorWorkflow")}
    # ancestors of every write node
    parents = {n: [] for n in names}
    for a, i, b in edges:
        if b in parents: parents[b].append(a)
    byname = {n["name"]: n for n in nodes}; paths = []
    for n in nodes:
        if not (is_write(n) or short(n["type"]) in ("emailSend", "hubspot")): continue
        anc = set(); st = [n["name"]]
        while st:
            x = st.pop()
            for p in parents.get(x, []):
                if p not in anc: anc.add(p); st.append(p)
        ext = [byname[a] for a in sorted(anc) if short(byname[a]["type"]) in EXT_T]
        paths.append((n["name"], short(n["type"]), n.get("onError", "(stop)"), [(e["name"], e.get("onError", "(stop)"), "alwaysOutputData" if e.get("alwaysOutputData") else "") for e in ext]))
    R["info"]["write_paths"] = paths
    return R
def md(path, w, R):
    o = ["### %s" % path, "- nodes: %d; connections: %d; triggers: %s" % (len(w.get("nodes", [])), sum(len(l or []) for o_ in w.get("connections", {}).values() for lst in o_.values() for l in lst), ", ".join(n["name"] for n in w["nodes"] if TRIG.search(n["type"])))]
    o.append("- FAIL: " + (" | ".join(R["fail"]) if R["fail"] else "none"))
    o.append("- save settings: " + ", ".join("%s=%s" % kv for kv in R["info"]["save"].items()))
    o.append("- webhooks: " + ("; ".join("%s %s /%s auth=%s" % x for x in R["info"]["webhooks"]) or "none"))
    o.append("- $env reads: " + ("; ".join("%s (%s)" % (k, ", ".join(v)) for k, v in R["info"]["env"].items()) or "none"))
    o.append("- credentials: " + ("; ".join("%s [%s] %s=%s" % (a, b, c, d) for a, b, c, d, e in R["info"]["creds"]) or "none"))
    o += ["", "| node | type | onError | retry | alwaysOutputData | flag |", "|---|---|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in R["info"]["rows"]]
    o += ["", "Write nodes (mail or CRM) and the external-call nodes upstream of each:", "", "| write node | type | its onError | upstream external nodes (name: onError) |", "|---|---|---|---|"]
    for a, b, c, ext in R["info"]["write_paths"]: o.append("| %s | %s | %s | %s |" % (a, b, c, "; ".join("%s: %s%s" % (x, y, " +" + z if z else "") for x, y, z in ext) or "none"))
    return "\n".join(o) + "\n"
def selftest():
    w = {"nodes": [{"name": "T", "type": "n8n-nodes-base.webhook", "parameters": {"httpMethod": "POST", "path": "x"}}, {"name": "A", "type": "n8n-nodes-base.postgres", "parameters": {"query": "x"}, "alwaysOutputData": True, "onError": "continueErrorOutput"},
                  {"name": "A", "type": "n8n-nodes-base.set", "parameters": {"v": "={{ $('Ghost').item.json.a + $env.K }}"}}, {"name": "O", "type": "n8n-nodes-base.set", "parameters": {}}],
         "connections": {"T": {"main": [[{"node": "A", "type": "main", "index": 0}, {"node": "Nope", "type": "main", "index": 0}]]}}}
    R = check(w); t = " | ".join(R["fail"])
    for k in ("duplicate node names: A", "targets missing node: Nope", "orphan nodes", "Ghost", "alwaysOutputData together", "error) is not wired", "webhook without authentication"): assert k in t, (k, t)
    ok = {"nodes": [{"name": "T", "type": "n8n-nodes-base.webhook", "parameters": {"authentication": "headerAuth"}}, {"name": "B", "type": "n8n-nodes-base.set", "parameters": {}}], "connections": {"T": {"main": [[{"node": "B", "type": "main", "index": 0}]]}}}
    assert check(ok)["fail"] == [], check(ok)["fail"]
    print("selftest ok")
if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit(0)
    bad = 0
    for p in sys.argv[1:]:
        try: w = json.load(open(p))
        except Exception as e: print("### %s\n- FAIL: does not parse: %s\n" % (p, e)); bad += 1; continue
        R = check(w); print(md(p, w, R)); bad += bool(R["fail"])
    sys.exit(1 if bad else 0)
