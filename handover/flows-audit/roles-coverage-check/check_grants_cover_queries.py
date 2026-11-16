"""Text-only check: do the proposed column grants (ROLES-PROPOSAL.md section 4)
cover every Postgres query in the flow folders? Reads JSON only; no database.
Usage: python3 -I check_grants_cover_queries.py <flow_folder> [<flow_folder> ...]
Rough parser: it can miss unusual SQL. The real proof is the database tests."""
import json, re, sys, pathlib

COLS = ("lead_key email name state claimed_until claim_token attempts crm_id mail_sent "
        "created_at updated_at alert_sent alert_token alert_until alert_attempts").split()
G = {  # login -> (select, insert, update)  copied from section 4
 "mf_door": ("lead_key state claim_token", "lead_key email name state claimed_until claim_token attempts", ""),
 "mf_sub": ("lead_key claim_token state mail_sent", "", "crm_id mail_sent state updated_at"),
 "mf_recover": ("lead_key email claim_token state claimed_until attempts created_at mail_sent", "",
                "claimed_until claim_token attempts state updated_at"),
 "mf_alert": ("lead_key state created_at alert_sent alert_token alert_until alert_attempts", "",
              "alert_until alert_token alert_attempts alert_sent updated_at"),
}
G = {k: tuple(set(x.split()) for x in v) for k, v in G.items()}
NODE_LOGIN = {("mf-form", "Claim"): "mf_door", ("mf-form", "Stored"): "mf_door",
              ("mf-hook", "Claim"): "mf_door", ("mf-hook", "Stored"): "mf_door",
              ("mf-recovery", "ClaimStuck"): "mf_recover", ("mf-recovery", "MarkFailed"): "mf_recover",
              ("mf-recovery", "AlertClaim"): "mf_alert", ("mf-recovery", "AlertBackoff"): "mf_alert",
              ("mf-recovery", "AlertMark"): "mf_alert"}
SUB = "mf_sub"

def toks(s):
    return re.findall(r"[a-z_]+", s)

def analyse(sql):
    s = re.sub(r"'[^']*'", "''", sql)  # drop string literals
    writes_i, writes_u = set(), set()
    m = re.search(r"insert\s+into\s+\w+\s*\(([^)]*)\)", s, re.I)
    ins_tokens = []
    if m:
        ins_tokens = toks(m.group(1))
        writes_i = {t for t in ins_tokens if t in COLS}
    set_tokens = []
    for m in re.finditer(r"\bset\b(.*?)(?=\bwhere\b|\breturning\b|\bfrom\b|$)", s, re.I | re.S):
        # split assignments on top-level commas
        depth, cur, parts = 0, "", []
        for ch in m.group(1):
            depth += ch == "("; depth -= ch == ")"
            if ch == "," and depth == 0: parts.append(cur); cur = ""
            else: cur += ch
        parts.append(cur)
        for p in parts:
            t = re.match(r"\s*([a-z_]+)\s*=", p, re.I)
            if t and t.group(1) in COLS:
                writes_u.add(t.group(1)); set_tokens.append(t.group(1))
    all_tokens = [t for t in toks(s) if t in COLS]
    reads = set()
    skip = list(ins_tokens) + set_tokens
    for t in all_tokens:
        if t in skip: skip.remove(t)
        else: reads.add(t)
    return writes_i, writes_u, reads

bad = 0
for folder in sys.argv[1:]:
    n = 0
    for f in sorted(pathlib.Path(folder).glob("mf-*.json")):
        flow = f.stem
        for node in json.load(open(f)).get("nodes", []):
            if node.get("type") != "n8n-nodes-base.postgres": continue
            q = node.get("parameters", {}).get("query", "")
            login = NODE_LOGIN.get((flow, node["name"])) or (SUB if flow == "mf-sub-crm-mail" else None)
            n += 1
            if login is None: print("NO LOGIN MAPPED", flow, node["name"]); bad += 1; continue
            wi, wu, rd = analyse(q)
            sel, ins, upd = G[login]
            miss = [("INSERT", c) for c in wi - ins] + [("UPDATE", c) for c in wu - upd] + [("SELECT", c) for c in rd - sel]
            if miss: bad += 1
            print(f"{folder.rstrip('/').split('/')[-1]} {flow} {node['name']} -> {login}: "
                  f"{'UNCOVERED ' + str(miss) if miss else 'covered'}")
    print(f"{folder}: {n} postgres nodes")
print("TOTAL UNCOVERED OR UNMAPPED:", bad)
sys.exit(1 if bad else 0)
