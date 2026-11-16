#!/usr/bin/env python3
"""Read-only structural check of generated n8n flow JSON files. Nothing is run in n8n. Standard library only.

Usage:
  check_flows.py DIR [DIR ...] [options]
Options:
  --expect FILE=NODES:CONNS     expected node and connection count of one flow file (repeatable), e.g. mf-form.json=12:11
  --expect-json PATH            same as JSON {"mf-form.json": {"nodes": 12, "connections": 11}, ...}
  --files a.json,b.json,...     exact list of *.json files each DIR must hold (default: the four mf-*.json flow files)
  --baseline DIR                directory of the unpatched flows: an IF node that already lacks a branch there is only flagged (WARN), else FAIL
  --patch-checks F002,F008      assert the F-002 and/or F-008 patch content (names, links, settings) in the given DIRs
  --diff-base DIR --allow F002,F008 [--diff-out FILE]
                                node-level diff DIR vs DIR (patched vs unpatched); FAIL on any change the allowed patches do not explain
  --quiet-info                  do not print the type table and the placeholder list

Checks per file (FAIL = exit code 1): JSON parses; every node has name and type; no duplicate names; every connection
source and target exists; at least one trigger; every node reachable from a trigger (reachability walk over all output
types, so a node whose only incoming link comes from an orphan or from itself is unreachable); node/connection counts
equal the expected ones; onError=continueErrorOutput nodes have a non-empty main[1]; IF nodes have both branch outputs;
every $('Name') and $node["Name"] inside an expression names a node of the same file.
Trigger = exact type n8n-nodes-base.webhook, n8n-nodes-base.executeWorkflowTrigger, n8n-nodes-base.formTrigger, or a type
ending in 'Trigger'. respondToWebhook is NOT a trigger.
Exit code: 0 only if no FAIL; 1 otherwise."""
import json, os, re, sys, collections

FILES_DEFAULT = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
TRIGGER_EXACT = {"n8n-nodes-base.webhook", "n8n-nodes-base.executeWorkflowTrigger", "n8n-nodes-base.formTrigger"}
PLACEHOLDERS = ["PLACEHOLDER", "PG_CREDENTIAL_ID", "SMTP_CREDENTIAL_ID", "SUB_WORKFLOW_ID", "HS_CRED", "HUBSPOT_CREDENTIAL_ID"]
REF = re.compile(r"""\$\(\s*['"]([^'"]+)['"]\s*\)|\$node\[\s*['"]([^'"]+)['"]\s*\]""")
ENVTOK = re.compile(r"\$env\.[A-Za-z0-9_]+")
FAILS, WARNS = [], []

def fail(where, msg): FAILS.append("%s: %s" % (where, msg)); print("FAIL", where, msg)
def warn(where, msg): WARNS.append("%s: %s" % (where, msg)); print("WARN", where, msg)

def is_trigger(t): return t in TRIGGER_EXACT or t.endswith("Trigger")

def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

def load(path, tag):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception as e:
        fail(tag, "parse failure %s" % type(e).__name__); return None

def targets_of(outs):
    for typ, lists in (outs or {}).items():
        for idx, lst in enumerate(lists):
            for c in lst or []: yield typ, idx, c.get("node")

def check_flow(d, tag, expect, baseline_d):
    nodes = d.get("nodes")
    if not isinstance(nodes, list): fail(tag, "no nodes list"); return
    bad = [i for i, n in enumerate(nodes) if not n.get("name") or not n.get("type")]
    if bad: fail(tag, "node(s) at index %s lack name or type" % bad); nodes = [n for n in nodes if n.get("name") and n.get("type")]
    names = [n["name"] for n in nodes]; nameset = set(names)
    dups = sorted(k for k, v in collections.Counter(names).items() if v > 1)
    if dups: fail(tag, "duplicate names %s" % dups)
    conns = d.get("connections", {}); ncon = 0; adj = collections.defaultdict(set); incoming = set()
    for src, outs in conns.items():
        if src not in nameset: fail(tag, "connection source %r is not a node" % src)
        for typ, idx, t in targets_of(outs):
            ncon += 1
            if t not in nameset: fail(tag, "dangling target %r from %r" % (t, src))
            else: adj[src].add(t); incoming.add(t)
    trig = [n["name"] for n in nodes if is_trigger(n["type"])]
    if not trig: fail(tag, "no trigger node in file")
    seen, stack = set(trig), list(trig)
    while stack:
        for t in adj[stack.pop()]:
            if t not in seen: seen.add(t); stack.append(t)
    orphans = sorted(n for n in names if n not in incoming and n not in trig)
    unreach = sorted(n for n in names if n not in seen)
    if orphans: fail(tag, "orphan nodes (no incoming link, not a trigger) %s" % orphans)
    if unreach: fail(tag, "unreachable from any trigger %s" % unreach)
    if expect:
        if "nodes" in expect and len(nodes) != expect["nodes"]: fail(tag, "node count %d != expected %d" % (len(nodes), expect["nodes"]))
        if "connections" in expect and ncon != expect["connections"]: fail(tag, "connection count %d != expected %d" % (ncon, expect["connections"]))
    base_nodes = {n.get("name"): n for n in (baseline_d or {}).get("nodes", [])}
    base_conns = (baseline_d or {}).get("connections", {})
    for n in nodes:
        outs = conns.get(n["name"], {}).get("main", [])
        def has(i): return i < len(outs) and bool(outs[i])
        if n.get("onError") == "continueErrorOutput" and not has(1):
            fail(tag, "node %s has onError=continueErrorOutput but main[1] is missing or has no target" % n["name"])
        if n["type"] == "n8n-nodes-base.if":
            miss = [i for i in (0, 1) if not has(i)]
            if miss:
                bo = base_conns.get(n["name"], {}).get("main", [])
                base_missing = n["name"] in base_nodes and [i for i in (0, 1) if not (i < len(bo) and bo[i])] == miss
                (warn if base_missing else fail)(tag, "IF node %s lacks output(s) %s%s" % (n["name"], miss, " (baseline already lacks the same)" if base_missing else ""))
    for n in nodes:
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2)
                if ref not in nameset: fail(tag, "node %s: expression refers to $('%s') which is not a node of this file" % (n["name"], ref))
    return {"nodes": len(nodes), "connections": ncon, "triggers": trig}

def info(d, tag):
    tc = collections.Counter((n.get("type"), n.get("typeVersion")) for n in d.get("nodes", []))
    print("  types:", "; ".join("%s v%s x%d" % (t, v, c) for (t, v), c in sorted(tc.items(), key=str)))
    raw = json.dumps(d); where = collections.defaultdict(set)
    for n in d.get("nodes", []):
        s = json.dumps(n)
        for p in PLACEHOLDERS:
            if p in s: where[p].add(n.get("name"))
        for e in ENVTOK.findall(s): where[e].add(n.get("name"))
    for k in sorted(where): print("  placeholder/env %-34s count=%d nodes=%s" % (k, len(re.findall(re.escape(k), raw)), sorted(where[k])))
    if not where: print("  placeholder/env: none")

def deep_diff(a, b, path=""):
    """Paths (no values) where a and b differ. Lists of dicts that carry 'name' are aligned by name."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = path + "." + k if path else k
            if k not in a: out.append(p + " (added)")
            elif k not in b: out.append(p + " (removed)")
            else: out += deep_diff(a[k], b[k], p)
    elif isinstance(a, list) and isinstance(b, list):
        if all(isinstance(x, dict) and "name" in x for x in a + b) and (a or b):
            da, db = {x["name"]: x for x in a}, {x["name"]: x for x in b}
            for k in sorted(set(da) | set(db)):
                p = "%s[%s]" % (path, k)
                if k not in da: out.append(p + " (added)")
                elif k not in db: out.append(p + " (removed)")
                else: out += deep_diff(da[k], db[k], p)
        elif len(a) != len(b): out.append(path + " (list length %d -> %d)" % (len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)): out += deep_diff(x, y, "%s[%d]" % (path, i))
    elif a != b: out.append(path)
    return out

def get(d, name): return next((n for n in d["nodes"] if n["name"] == name), None)

def patch_checks(d, fname, which, tag):
    form = fname in ("mf-form.json", "mf-hook.json"); main = lambda nm: d["connections"].get(nm, {}).get("main", [])
    tg = lambda nm, i: sorted(c["node"] for c in (main(nm)[i] if i < len(main(nm)) else []))
    if "F002" in which:
        new = ["KeyOk", "ReplyBadKey", "ReplyStoreFail"]
        if not form:
            for nm in new:
                if get(d, nm): fail(tag, "F-002 node %s must exist only in mf-form and mf-hook" % nm)
        else:
            for nm in new:
                if not get(d, nm): fail(tag, "F-002 node %s missing" % nm)
            if all(get(d, nm) for nm in new):
                links = [("Valid", 0, ["KeyOk"]), ("KeyOk", 0, ["Claim"]), ("KeyOk", 1, ["ReplyBadKey"]), ("Claim", 0, ["Claimed"]), ("Claim", 1, ["ReplyStoreFail"])]
                for s, i, want in links:
                    if tg(s, i) != want: fail(tag, "F-002 link %s out%d -> %s expected %s" % (s, i, tg(s, i), want))
                cl = get(d, "Claim")
                if cl.get("onError") != "continueErrorOutput": fail(tag, "Claim onError is %r" % cl.get("onError"))
                if cl.get("alwaysOutputData") is not False: fail(tag, "Claim alwaysOutputData is %r (expected False)" % cl.get("alwaysOutputData"))
                print("  [%s] KeyOk IF condition: %s" % (fname, json.dumps(get(d, "KeyOk")["parameters"].get("conditions", {}).get("conditions"))))
                for nm in ("ReplyBadKey", "ReplyStoreFail"):
                    p = get(d, nm)["parameters"]; print("  [%s] %s status=%s body=%s" % (fname, nm, p.get("options", {}).get("responseCode"), p.get("responseBody")))
                print("  [%s] Valid lead_key assignment: %s" % (fname, [a.get("value") for a in get(d, "Valid")["parameters"]["assignments"]["assignments"] if a.get("name") == "lead_key"]))
    if "F008" in which:
        want = "none" if fname == "mf-recovery.json" else "all"
        s = d.get("settings", {})
        for k in ("saveDataSuccessExecution", "saveDataErrorExecution"):
            if s.get(k) != want: fail(tag, "F-008 %s is %r expected %r" % (k, s.get(k), want))

ALLOW_NODES = {  # allowed changes by patch: (flow files, node, changed path prefixes or None for added)
    "F002": [(("mf-form.json", "mf-hook.json"), "KeyOk", None), (("mf-form.json", "mf-hook.json"), "ReplyBadKey", None), (("mf-form.json", "mf-hook.json"), "ReplyStoreFail", None),
             (("mf-form.json", "mf-hook.json"), "Valid", ("parameters.assignments.assignments[lead_key]",)),
             (("mf-form.json", "mf-hook.json"), "Claim", ("onError", "alwaysOutputData"))]}
ALLOW_CONN = {"F002": ("Valid", "KeyOk", "Claim")}
ALLOW_SETTINGS = {"F008": {"mf-form.json": ("saveDataSuccessExecution", "saveDataErrorExecution"), "mf-hook.json": ("saveDataSuccessExecution", "saveDataErrorExecution"), "mf-sub-crm-mail.json": ("saveDataSuccessExecution", "saveDataErrorExecution")}}

def node_diff(base, patched, fname, allow, tag, out):
    bn = {n["name"]: n for n in base["nodes"]}; pn = {n["name"]: n for n in patched["nodes"]}
    allowed = [r for a in allow for r in ALLOW_NODES.get(a, []) if fname in r[0]]
    allow_added = {r[1] for r in allowed if r[2] is None}; allow_changed = {r[1]: r[2] for r in allowed if r[2] is not None}
    out.append("== %s ==" % tag)
    for nm in sorted(set(pn) - set(bn)):
        out.append("  node ADDED   %s (%s v%s)" % (nm, pn[nm]["type"], pn[nm]["typeVersion"]))
        if nm not in allow_added: fail(tag, "unexplained added node %s" % nm)
    for nm in sorted(set(bn) - set(pn)):
        out.append("  node REMOVED %s" % nm); fail(tag, "unexplained removed node %s" % nm)
    for nm in sorted(set(bn) & set(pn)):
        ch = deep_diff(bn[nm], pn[nm])
        if ch:
            out.append("  node CHANGED %s: %s" % (nm, ", ".join(ch)))
            pref = allow_changed.get(nm)
            for c in ch:
                if pref is None or not any(c.startswith(p) or c.split(" ")[0].startswith(p) for p in pref): fail(tag, "unexplained change in node %s at %s" % (nm, c))
    bc, pc = base.get("connections", {}), patched.get("connections", {})
    for src in sorted(set(bc) | set(pc)):
        if bc.get(src) != pc.get(src):
            out.append("  connections CHANGED for source %s" % src)
            if not any(src in ALLOW_CONN.get(a, ()) for a in allow): fail(tag, "unexplained connection change for source %s" % src)
    bs, ps = base.get("settings", {}), patched.get("settings", {})
    for k in sorted(set(bs) | set(ps)):
        if bs.get(k) != ps.get(k):
            out.append("  settings CHANGED %s: %r -> %r" % (k, bs.get(k), ps.get(k)))
            if not any(k in ALLOW_SETTINGS.get(a, {}).get(fname, ()) for a in allow): fail(tag, "unexplained settings change %s" % k)
    for k in sorted(set(base) | set(patched)):
        if k not in ("nodes", "connections", "settings") and base.get(k) != patched.get(k): out.append("  top-level key %s CHANGED" % k); fail(tag, "unexplained top-level change %s" % k)

def main(argv):
    dirs, expect, files, baseline, pc, diffbase, allow, diffout, quiet = [], {}, FILES_DEFAULT, None, set(), None, [], None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        def val():
            nonlocal i; i += 1; return argv[i]
        if a == "--expect":
            k, v = val().split("=", 1); n, c = v.split(":"); expect[k] = {"nodes": int(n), "connections": int(c)}
        elif a == "--expect-json": expect.update(json.load(open(val(), encoding="utf-8")))
        elif a == "--files": files = val().split(",")
        elif a == "--baseline": baseline = val()
        elif a == "--patch-checks": pc = set(val().split(","))
        elif a == "--diff-base": diffbase = val()
        elif a == "--allow": allow = [x for x in val().split(",") if x]
        elif a == "--diff-out": diffout = val()
        elif a == "--quiet-info": quiet = True
        elif a.startswith("--"): print("unknown option", a); return 2
        else: dirs.append(a)
        i += 1
    if not dirs: print(__doc__); return 2
    diffsum = []
    for dr in dirs:
        print("### %s" % dr)
        if not os.path.isdir(dr): fail(dr, "not a directory"); continue
        have = sorted(x for x in os.listdir(dr) if x.endswith(".json"))
        if have != sorted(files): fail(dr, "file list %s != expected %s" % (have, sorted(files)))
        for fn in files:
            p = os.path.join(dr, fn); tag = "%s/%s" % (dr, fn)
            if not os.path.isfile(p): continue
            d = load(p, tag)
            if d is None: continue
            bd = load(os.path.join(baseline, fn), "baseline/" + fn) if baseline and os.path.isfile(os.path.join(baseline, fn)) else None
            r = check_flow(d, tag, expect.get(fn), bd)
            if r: print("%s nodes=%d connections=%d triggers=%s saveDataSuccess=%s saveDataError=%s" % (fn, r["nodes"], r["connections"], r["triggers"], d.get("settings", {}).get("saveDataSuccessExecution"), d.get("settings", {}).get("saveDataErrorExecution")))
            if r and not quiet: info(d, tag)
            if pc: patch_checks(d, fn, pc, tag)
            if diffbase:
                bd2 = load(os.path.join(diffbase, fn), "diff-base/" + fn)
                if bd2: node_diff(bd2, d, fn, allow, tag, diffsum)
    if diffbase:
        text = "\n".join(diffsum) + "\n"
        print(text)
        if diffout: open(diffout, "w", encoding="utf-8").write("# node-level diff, unpatched generator output vs patched (paths only, no values)\n# allowed patches: %s\n%s" % (",".join(allow) or "none", text))
    print("RESULT: %d FAIL, %d WARN" % (len(FAILS), len(WARNS)))
    return 1 if FAILS else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
