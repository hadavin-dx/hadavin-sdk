import json, re, sys, hashlib, datetime
BASE = sys.argv[1]
SCRIPT = sys.argv[2]
DIRS = ["real-v5", "film-v5"]
FILES = ["mf-hook.json", "mf-form.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
SENS = re.compile(r"(pass|secret|token|apikey|api_key|authorization|bearer|credential|key)", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)")
LONG = re.compile(r"[A-Za-z0-9_\-]{32,}")
LEASE = re.compile(r"(45|interval|seconds|lease|cap|count|limit|backoff)", re.I)
out = []
def P(s=""): out.append(s)
def mstr(s, key=""):
    if SENS.search(key) and not s.startswith("="):
        return "[MASKED]"
    def em(m):
        d = m.group(1).lower()
        return m.group(0) if (d.endswith(".example") or d.endswith("example.com") or d=="example.com") else "[MASKED]"
    s = EMAIL.sub(em, s)
    return LONG.sub("[MASKED]", s)
def mask(o, key=""):
    if isinstance(o, dict): return {k: mask(v, k) for k, v in o.items()}
    if isinstance(o, list): return [mask(v, key) for v in o]
    if isinstance(o, str): return mstr(o, key)
    return o
def J(o): return json.dumps(mask(o), ensure_ascii=False, indent=1, sort_keys=True)
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from walk(v, f"{path}[{i}]")
    else:
        yield path, o
def edges(conn, name):
    r = {}
    for typ, outs in conn.get(name, {}).items():
        for i, lst in enumerate(outs):
            r[f"{typ}[{i}]"] = [e["node"] for e in (lst or [])]
    return r
paths = [(d, f, f"{BASE}/handover/demo/n8n-flows-{d}/{f}") for d in DIRS for f in FILES]
hdr = ["date UTC: " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
       "script path: " + SCRIPT, "sha256 of the 8 files (read-only target " + BASE + "):"]
for d, f, p in paths:
    hdr.append(f"- {d}/{f}: {hashlib.sha256(open(p,'rb').read()).hexdigest()}")
out.extend(hdr); P("")
for d, f, p in paths:
    w = json.load(open(p))
    nodes = w["nodes"]; conn = w.get("connections", {})
    inc = {n["name"]: [] for n in nodes}
    for s, tv in conn.items():
        for typ, outs in tv.items():
            for i, lst in enumerate(outs):
                for e in (lst or []): inc.setdefault(e["node"], []).append(f"{s}:{typ}[{i}]")
    P(f"# {d}/{f}  (workflow name: {w.get('name')})"); P()
    P("## (1) Respond-to-Webhook nodes")
    for n in nodes:
        if n["type"].endswith("respondToWebhook"):
            pr = n["parameters"]
            P(f"- {n['name']} | fed by: {inc.get(n['name'])}")
            P(f"  responseCode: {json.dumps(pr.get('options',{}).get('responseCode', pr.get('responseCode','(not set)')))}")
            P("  parameters (masked): " + J(pr).replace("\n", "\n  "))
    P("## (2) Code/Function nodes and IF/Switch conditions")
    for n in nodes:
        t = n["type"].lower()
        if t.endswith(".code") or t.endswith("function") or t.endswith("functionitem"):
            P(f"#### {n['name']} ({n['type']}) full body:"); P(mstr(str(n['parameters'].get('jsCode', n['parameters'].get('functionCode', J(n['parameters']))))))
        elif t.endswith(".if") or t.endswith(".switch") or t.endswith("filter"):
            P(f"#### {n['name']} ({n['type']}) conditions/parameters:"); P(J(n["parameters"]))
    P("## (3) Schedule/cron/interval triggers")
    found = False
    for n in nodes:
        if re.search(r"schedule|cron|interval", n["type"], re.I):
            found = True; P(f"- {n['name']} ({n['type']}): " + json.dumps(mask(n["parameters"]), sort_keys=True))
    if not found: P("(none by node type)")
    P("## (4) Values/expressions matching lease/alert-cap/counter patterns (45, interval, seconds, lease, cap, count, limit, backoff)")
    for n in nodes:
        for pth, v in walk(n["parameters"]):
            sv = str(v)
            if LEASE.search(sv) or LEASE.search(pth):
                for ln in (sv.splitlines() or [""]):
                    if LEASE.search(ln) or LEASE.search(pth):
                        P(f"- node={n['name']} field={pth} value-line: {mstr(ln.strip(), pth)}")
        for k in ("retryOnFail","maxTries","waitBetweenTries"):
            if k in n: P(f"- node={n['name']} field(node-level)={k} value={n[k]}")
    P("## (5) Workflow settings (full)")
    P(J(w.get("settings"))); P("other top-level keys: " + json.dumps(list(w.keys())))
    for k in w:
        if k not in ("nodes","connections","settings","name"): P(f"top-level {k}: {J(w[k])}")
    P("## (6) Disabled nodes; continueOnFail / alwaysOutputData / onError per node")
    for n in nodes:
        P(f"- {n['name']}: disabled={n.get('disabled','(absent)')} continueOnFail={n.get('continueOnFail','(absent)')} alwaysOutputData={n.get('alwaysOutputData','(absent)')} onError={n.get('onError','(absent)')}")
    P("## (7) Literal strings >3 chars in mail/alert/log text (nodes whose name/type matches mail|alert|log|email|slack|notify; plus any string key named subject/text/message/body/html/bodyText)")
    for n in nodes:
        nm = re.search(r"mail|alert|log|email|slack|notify", n["name"] + n["type"], re.I)
        for pth, v in walk(n["parameters"]):
            if isinstance(v, str) and len(v) > 3:
                leaf = pth.split(".")[-1]
                if nm or re.search(r"subject|text|message|body|html|toemail|fromemail|to$|from$", leaf, re.I):
                    P(f"- node={n['name']} field={pth}: {mstr(v, pth)!r}")
    P("## (8) Webhook nodes")
    for n in nodes:
        if n["type"].endswith(".webhook"):
            pr = n["parameters"]
            P(f"- {n['name']}: path={mstr(str(pr.get('path')))} httpMethod={pr.get('httpMethod','(default)')} authentication={pr.get('authentication','(not set)')} responseMode={pr.get('responseMode','(not set)')} webhookId={'present' if n.get('webhookId') else 'absent'}")
            P("  options: " + J(pr.get("options", "(absent)")))
            P("  full parameters: " + J(pr).replace("\n", "\n  "))
    P("## (9) Appendix: full parameters JSON of every node (masked)")
    for n in nodes:
        P(f"#### {n['name']} ({n['type']} v{n.get('typeVersion')})"); P(J(n["parameters"]))
    P()
open(sys.argv[3], "w").write("# evidence-A2b (raw facts only; nothing rated)\n\n" + "\n".join(out) + "\n")
print(len(out), "lines")
