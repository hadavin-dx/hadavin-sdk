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
  --diff-base DIR --allow F002,F008 (--allow requires --patch-checks naming at least the same patches) [--diff-out FILE]
                                node-level diff DIR vs DIR (patched vs unpatched); FAIL on any change the allowed patches do not explain
  --quiet-info                  do not print the type table and the placeholder list (the credential list per flow is always printed)
  --require-webhook-auth        a webhook or form trigger without authentication is a FAIL (default: WARN-LEAD-DECISION line, exit stays 0, counted as a known open problem)
  --expect-credential KIND=NAME a node credential of this kind (for example postgres, smtp) must have exactly this name, else FAIL (repeatable)
  --block-env-access            a node that reads $env.X is a FAIL (default: WARN-LEAD-DECISION): use when the take switches off env access inside nodes
  --require-real-credential-ids a credential id or sub-workflow id that is still a placeholder is a FAIL (default: always printed as WARN, even with --quiet-info)

F8 EXTENSION (flow-check/): started from patch-apply/check_flows.py (F4 round 3), nothing removed. New checks are listed in
flow-check/REPORT.md. New options: --require-webhook-auth (webhook without authentication = FAIL, default WARN), --table (print
the error-settings table per file), --files all (every *.json in each DIR). Nothing is run in n8n.

Checks per file (FAIL = exit code 1): JSON parses; every node has name and type; no duplicate names; every connection
source and target exists; at least one trigger; every node reachable from a trigger (reachability walk over all output
types, so a node whose only incoming link comes from an orphan or from itself is unreachable); node/connection counts
equal the expected ones; onError=continueErrorOutput nodes have a non-empty main[1]; IF nodes have both branch outputs;
every $('Name') and $node["Name"] inside an expression names a node of the same file.
Trigger = exact type n8n-nodes-base.webhook, n8n-nodes-base.executeWorkflowTrigger, n8n-nodes-base.formTrigger, or a type
ending in 'Trigger'. respondToWebhook is NOT a trigger.
F-002 alwaysOutputData/onError on Claim is only printed with a WARN (UNPROVEN until test T19): exit 0 does NOT clear F-002.
Exit code: 0 only if no FAIL; 1 otherwise; 2 for a usage error (unknown option, missing value, unknown patch name, bad --expect)."""
import json, os, re, sys, collections
OPTS = {"webhook_auth": False, "table": False, "block_env": False, "real_ids": False, "cred_names": {}}
LEAD = {"webhook": 0, "env": 0}  # open lead decisions seen in this run (printed in the closing block)

FILES_DEFAULT = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
TRIGGER_EXACT = {"n8n-nodes-base.webhook", "n8n-nodes-base.executeWorkflowTrigger", "n8n-nodes-base.formTrigger", "n8n-nodes-base.cron"}
PLACEHOLDERS = ["PLACEHOLDER", "PG_CREDENTIAL_ID", "SMTP_CREDENTIAL_ID", "SUB_WORKFLOW_ID", "HS_CRED", "HUBSPOT_CREDENTIAL_ID"]
REF = re.compile(r"""\$\(\s*['"`]([^'"`]+)['"`]\s*\)|\$node\[\s*['"`]([^'"`]+)['"`]\s*\]|\$items\(\s*['"`]([^'"`]+)['"`]|\$node\.([A-Za-z_][A-Za-z0-9_]*)""")
DYNREF = re.compile(r"""\$\(\s*(?!['"`])[^)\s]|\$node\[\s*(?!['"`])[^\]\s]""")  # a node name that is not one plain quoted text: cannot be checked statically
PREV = re.compile(r"\$prevNode\b")
STICKY = "n8n-nodes-base.stickyNote"
KEY_COND = "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}"
WANT_CONN = {
    "Valid": {"main": [[{"node": "KeyOk", "type": "main", "index": 0}]]},
    "KeyOk": {"main": [[{"node": "Claim", "type": "main", "index": 0}], [{"node": "ReplyBadKey", "type": "main", "index": 0}]]},
    "Claim": {"main": [[{"node": "Claimed", "type": "main", "index": 0}], [{"node": "ReplyStoreFail", "type": "main", "index": 0}]]},
}
F002_UNPROVEN = "F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)"
ENVTOK = re.compile(r"\$env\s*\?\.\s*[A-Za-z0-9_]+|\$env\s*\?\.\s*\[[^\]]*\]|\$env\s*\.\s*[A-Za-z0-9_]+|\$env\s*\[[^\]]*\]|\$env\b|\bprocess\.env\b(?:\.[A-Za-z0-9_]+|\s*\[[^\]]*\])?")  # $env.X, $env?.X, $env["X"], bare $env, process.env.X, process.env["X"]
FAILS, WARNS, KNOWN = [], [], []
UNV = "n8n rule UNVERIFIED"  # rules about n8n itself that no source in this repo backs; they never FAIL a file, they only WARN

def fail(where, msg): FAILS.append("%s: %s" % (where, msg)); print("FAIL", where, msg)
def warn(where, msg, known=False):
    """known=True marks a defect we already know is open (it is counted in the closing block 'Known open problems')."""
    WARNS.append("%s: %s" % (where, msg)); print("WARN", where, msg)
    if known: KNOWN.append("%s: %s" % (where, msg))

def lead(where, msg):
    """An open decision for the lead or owner: its own WARN-LEAD-DECISION line, exit code unchanged, counted as a known open problem."""
    WARNS.append("%s: %s" % (where, msg)); KNOWN.append("%s: %s" % (where, msg)); print("WARN-LEAD-DECISION", where, msg)

def final_block():
    print("OPEN LEAD DECISIONS: %d webhook(s) without auth, %d $env node(s)  (exit 0 does NOT mean authentication was checked)" % (LEAD["webhook"], LEAD["env"]))
    print("Known open problems: %d" % len(KNOWN))
    for k in KNOWN: print("  - " + k)
    print("Not proven: that n8n accepts these files on import; what n8n really does when a step fails (F-002, tests T19 and T20); the SQL inside the postgres nodes; "
          "expression syntax beyond node names; secrets in a shape this scan does not list; every rule marked '%s' (retry limits, onError values, position of the error output)." % UNV)
    print("Passing this check does NOT mean the flows are ready to film.")

HEADER = """# ===== READ THIS FIRST (plain words; every line of this header starts with '#') =====
# What this is: a read-only check of the exported n8n flow files (text files). It never started n8n.
# Verdict: exit code 0 does NOT mean the flows are ready to film. It only means the checker found no structural FAIL.
#   Safe to import into n8n?  NOT KNOWN. Import was never tried. Test ONE import first (the owner or the laptop lead).
# Exit code: 0 = no FAIL line (WARN lines may still exist). 1 = at least one FAIL line (a definite fault in a file). 2 = wrong command line.
# FAIL = a definite fault in the file. WARN = something a person must read; a WARN can be serious and does not change the exit code.
# "Known open problems" (closing block) counts WARN lines that are real defects we already know: no password on a web address,
#   a step whose failure leaves the caller with no answer (reply gap), $env reads, and F-002 (repeat lead key, unproven).
#   Unpatched flows ("pristine") give 6; patched flows give 8 because patch F-002 adds 2 lines (one per flow file mf-form and mf-hook) saying F-002 is unproven.
# Three decisions are open (details in REPORT.md, box "Start here"):
#   1. Web addresses (webhooks) of mf-form and mf-hook have no password: accept for the take, or add one (run with --require-webhook-auth to see the effect).
#   2. Four steps read environment variables ($env): allow that in the take, or change the steps (run with --block-env-access to see the effect).
#   3. Two yes/no steps (StuckRow, AlertRow in mf-recovery) lack a second branch: project rule says FAIL; --baseline excuses them as WARN only because the unpatched flows already had it.
# =============================================================================
"""

def is_trigger(t): return t in TRIGGER_EXACT or t.endswith("Trigger")

def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

class DupKey(Exception): pass
def _no_dups(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)): raise DupKey(sorted({k for k in keys if keys.count(k) > 1})[0])
    return dict(pairs)

def load(path, tag):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f, object_pairs_hook=_no_dups)
    except DupKey as e:
        fail(tag, "parse failure: duplicate JSON key %r (n8n keeps only the last one, so the file says two different things)" % str(e)); return None
    except Exception as e:
        fail(tag, "parse failure %s" % type(e).__name__); return None

def targets_of(outs):
    for typ, lists in (outs or {}).items():
        for idx, lst in enumerate(lists):
            for c in lst or []: yield typ, idx, c.get("node")

def shape_ok(d, tag):
    """FAIL (not a traceback) when the JSON is not the n8n shape this checker reads. True = safe to read further."""
    if not isinstance(d, dict): fail(tag, "top level is not a JSON object"); return False
    nodes, conns, ok = d.get("nodes"), d.get("connections", {}), True
    if not isinstance(nodes, list): fail(tag, "no nodes list"); return False
    for i, n in enumerate(nodes):
        if not isinstance(n, dict): fail(tag, "node at index %d is not an object" % i); ok = False
        elif not isinstance(n.get("name"), str) or not n.get("name") or not isinstance(n.get("type"), str) or not n.get("type"): fail(tag, "node at index %d lacks a text name or type" % i); ok = False
        elif "parameters" in n and not isinstance(n["parameters"], dict): fail(tag, "node %s: parameters is not an object" % n["name"]); ok = False
    if "settings" in d and not isinstance(d["settings"], dict): fail(tag, "settings is not an object"); ok = False
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and n.get("type") == "n8n-nodes-base.webhook" and "webhookId" in n and not isinstance(n["webhookId"], str): fail(tag, "node %s: webhookId is not text" % n.get("name")); ok = False
    if not isinstance(conns, dict): fail(tag, "connections is not an object"); return False
    for src, outs in conns.items():
        if not isinstance(outs, dict): fail(tag, "connections of %r are not an object" % src); ok = False; continue
        for typ, lists in outs.items():
            if not isinstance(lists, list): fail(tag, "connections of %r: %r is not a list" % (src, typ)); ok = False; continue
            for lst in lists:
                if lst is None: continue
                if not isinstance(lst, list): fail(tag, "connections of %r: an output is not a list" % src); ok = False; continue
                for c in lst:
                    if not isinstance(c, dict) or not isinstance(c.get("node"), str): fail(tag, "connections of %r: a link has no text 'node'" % src); ok = False
    return ok

# ---------------- F8 additions ----------------
ONERROR_OK = {None, "stopWorkflow", "continueRegularOutput", "continueErrorOutput"}
EXTERNAL = ("postgres", "httpRequest", "hubspot", "emailSend", "executeWorkflow")
CRED_KIND = {"postgres": ("postgres",), "emailSend": ("smtp",), "hubspot": ("hubspotAppToken", "hubspotApi", "hubspotOAuth2Api")}  # credential kind(s) n8n expects on these node types
WEBHOOK_AUTH = {"basicAuth": "httpBasicAuth", "headerAuth": "httpHeaderAuth", "jwtAuth": "jwtAuth"}  # n8n webhook node: authentication value -> credential kind (none = no credential)
FORM_AUTH = {"basicAuth": "httpBasicAuth"}  # n8n form trigger: only none or basicAuth
CRED_TYPES = ("postgres", "emailSend", "hubspot")  # these always need an attached credential
# secret shapes are built from parts so this file holds no secret-looking literal (the one allowed literal is the AWS example key)
AWS_EXAMPLE = "AKIA" + "IOSFODNN7EXAMPLE"
SECRET_RX = [("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")), ("sk- style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
             ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
             ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")), ("private key block", re.compile("-----" + "BEGIN [A-Z ]*PRIVATE KEY")),
             ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")), ("password inside a URL", re.compile(r"://[^/\s:@{}]+:[^/\s:@{}]{3,}@")),
             ("literal Bearer value", re.compile(r"Bearer\s+(?![{$=])[A-Za-z0-9._~+/-]{12,}"))]
SECRET_KEY_ENDS = ("password", "passwd", "secret", "token", "apikey", "authorization", "privatekey", "accesskey", "clientsecret")
EXPR_BLOCK = re.compile(r"\{\{(.*?)\}\}", re.S)
OK_WORDS = {"bearer", "basic", "token"}
def key_is_secretish(k):
    kk = re.sub(r"[-_\s]", "", str(k)).lower()
    return kk == "pass" or kk.endswith(SECRET_KEY_ENDS)
def value_is_safe(v):
    """A value is safe only when it is a reference to $env/$credentials/$secrets/$vars/$json/$('..') (alone or after Bearer/Basic) or one of the repo placeholder tokens, exactly."""
    if v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "": return True
    body = v[1:] if v.startswith("=") else v
    blocks = EXPR_BLOCK.findall(body)
    if not blocks or not all(re.match(r"\s*\$(env|credentials|secrets|vars|json|node|\(|items)", b) for b in blocks): return False
    for b in blocks:   # a quoted text of 6+ characters inside the expression (other than a node or variable name in $('..') or [".."]) is a literal value
        b2 = re.sub(r"""\$\(\s*['"][^'"]*['"]\s*\)|\[\s*['"][^'"]*['"]\s*\]|\$items\(\s*['"][^'"]*['"]""", " ", b)
        if re.search(r"""['"`][^'"`]{6,}['"`]""", b2): return False
    rest = EXPR_BLOCK.sub(" ", body)
    return all(w.lower() in OK_WORDS for w in re.findall(r"[A-Za-z0-9+/_-]{6,}", rest))

def kv_items(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from kv_items(v, path + "." + str(k))
            if isinstance(v, str): yield str(k), v, path + "." + str(k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, dict) and "name" in v and isinstance(v.get("value"), str): yield str(v["name"]), v["value"], "%s[%s]" % (path, v["name"])
            yield from kv_items(v, "%s[%d]" % (path, i))

def secret_scan(n, tag):
    hits = []
    for s in strings(n):
        s2 = s.replace(AWS_EXAMPLE, "")
        for label, rx in SECRET_RX:
            if rx.search(s2): hits.append(label)
    for k, v, p in kv_items({x: y for x, y in n.items() if x != "credentials"}):
        if key_is_secretish(k) and len(v) >= 6 and not value_is_safe(v) and str(k).lower() not in ("authentication", "genericauthtype", "nodecredentialtype"):
            hits.append("literal value under key %r" % k)
    for h in sorted(set(hits)): fail(tag, "node %s: secret-looking value (%s); keep secrets in n8n credentials or $env" % (n["name"], h))

def secret_scan_top(d, tag):
    """Top-level keys other than nodes/connections (pinData, staticData, meta, name, settings ...)."""
    top = {k: v for k, v in d.items() if k not in ("nodes", "connections")}
    hits = set()
    for s in strings(top):
        for label, rx in SECRET_RX:
            if rx.search(s.replace(AWS_EXAMPLE, "")): hits.add(label)
    for k, v, p in kv_items(top):
        if key_is_secretish(k) and len(v) >= 6 and not value_is_safe(v): hits.add("literal value under key %r" % k)
    for h in sorted(hits): fail(tag, "top-level data (not a node): secret-looking value (%s)" % h)

def webhook_paths(n, nodes, adj, tag):
    """Every path from a responseNode webhook must end in respondToWebhook. Walk is stopped at respond nodes."""
    mode = (n.get("parameters") or {}).get("responseMode", "onReceived")
    if mode != "responseNode":
        print("  [%s] webhook %s responseMode=%s (n8n answers by itself, no respondToWebhook needed)" % (tag, n["name"], mode)); return
    byname = {x["name"]: x for x in nodes}; isresp = lambda x: byname[x]["type"] == "n8n-nodes-base.respondToWebhook" and byname[x].get("disabled") is not True  # a disabled reply node sends nothing
    seen, stack, bare = {n["name"]}, [n["name"]], []
    while stack:
        x = stack.pop()
        if isresp(x): continue
        nxt = [t for t in adj.get(x, ()) if t in byname]
        if not nxt and x != n["name"]: bare.append(x)
        for t in nxt:
            if t not in seen: seen.add(t); stack.append(t)
    if not nxt_any(n["name"], adj): bare.append(n["name"])
    resp = [x for x in seen if isresp(x)]
    if bare: fail(tag, "webhook %s (responseNode): path(s) end WITHOUT respondToWebhook at %s" % (n["name"], sorted(bare)))
    if not resp: fail(tag, "webhook %s (responseNode): no respondToWebhook reachable" % n["name"])
    risky = sorted(x for x in seen if not isresp(x) and byname[x]["type"].split(".")[-1] in EXTERNAL + ("code", "function") and byname[x].get("disabled") is not True and byname[x].get("onError") in (None, "", "stopWorkflow"))
    if risky: warn(tag, "webhook %s: REPLY GAP: if %s fails the run stops and the caller gets no answer (error path has no reply; read from the file, n8n not run)" % (n["name"], risky), known=True)
    print("  [%s] webhook %s: %d respondToWebhook node(s) reachable %s; paths without a reply: %s" % (tag, n["name"], len(resp), sorted(resp), sorted(bare) or "none"))

def nxt_any(x, adj): return bool(adj.get(x))

def extra_checks(d, tag, nodes, adj, trig, sticky):
    byname = {x["name"]: x for x in nodes}; conns = d.get("connections", {})
    # shape of connections, trigger inputs, sticky notes
    for src, outs in conns.items():
        if not isinstance(outs, dict) or any(not isinstance(l, list) or any(l2 is not None and not isinstance(l2, list) for l2 in l) for l in outs.values()):
            fail(tag, "connections of %r are not {type: [[{node,type,index}]]}" % src); continue
        if src in sticky: fail(tag, "sticky note %r has a connection" % src)
        for typ, lists in outs.items():
            for lst in lists:
                for c in lst or []:
                    if not isinstance(c, dict) or not isinstance(c.get("index"), int) or c.get("index") < 0 or not c.get("type"): fail(tag, "connection %s -> %s lacks a valid type/index" % (src, c.get("node") if isinstance(c, dict) else c))
                    elif c.get("node") in trig: fail(tag, "incoming link %s -> %s into a trigger node (a trigger has no input)" % (src, c["node"]))
    real = [n for n in nodes if n["type"] != STICKY]
    if sticky: print("  [%s] sticky notes: %d %s" % (tag, len(sticky), sorted(sticky)))
    if not real: fail(tag, "sticky-note-only file: no executable node")
    elif not [n for n in real if n["name"] not in trig]: fail(tag, "file holds only trigger and sticky notes: nothing to run")
    for n in nodes:
        if n["type"] == STICKY: secret_scan(n, tag)
    secret_scan_top(d, tag)
    ids = [n["id"] for n in nodes if "id" in n]
    di = sorted(k for k, v in collections.Counter(ids).items() if v > 1)
    if di: fail(tag, "duplicate node ids %s" % di)
    norm = collections.defaultdict(set)
    for n in nodes: norm[re.sub(r"\s+", " ", n["name"].strip().lower())].add(n["name"])
    near = sorted(k for k, v in norm.items() if len(v) > 1)
    if near: fail(tag, "names that differ only by case or spaces %s" % near)
    # per node settings
    noretry, silent = [], []
    for n in real:
        nm, short = n["name"], n["type"].split(".")[-1]
        pos = n.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in pos)): fail(tag, "node %s lacks position [x, y]" % nm)
        if not isinstance(n.get("typeVersion"), (int, float)) or isinstance(n.get("typeVersion"), bool): fail(tag, "node %s lacks a numeric typeVersion" % nm)
        if n.get("onError") not in ONERROR_OK: warn(tag, "node %s onError=%r is not one of stopWorkflow, continueRegularOutput, continueErrorOutput (%s: value list from memory of the n8n UI, no source in this repo)" % (nm, n.get("onError"), UNV))
        if "retryOnFail" in n and not isinstance(n["retryOnFail"], bool): fail(tag, "node %s retryOnFail=%r is not a boolean" % (nm, n["retryOnFail"]))
        if n.get("retryOnFail"):
            mt, wb = n.get("maxTries", 3), n.get("waitBetweenTries", 1000)
            if not isinstance(mt, int) or isinstance(mt, bool) or not 2 <= mt <= 5: warn(tag, "node %s maxTries=%r (2 to 5 is the n8n screen limit, not a proven import rule; %s)" % (nm, mt, UNV))
            if not isinstance(wb, int) or isinstance(wb, bool) or not 0 <= wb <= 5000: warn(tag, "node %s waitBetweenTries=%r (0 to 5000 ms is the n8n screen limit, not a proven import rule; %s)" % (nm, wb, UNV))
        elif "maxTries" in n or "waitBetweenTries" in n: warn(tag, "node %s sets maxTries/waitBetweenTries but retryOnFail is not true (ignored by n8n)" % nm)
        if "alwaysOutputData" in n and not isinstance(n["alwaysOutputData"], bool): fail(tag, "node %s alwaysOutputData=%r is not a boolean" % (nm, n["alwaysOutputData"]))
        if n.get("alwaysOutputData") and n.get("onError") == "continueErrorOutput": fail(tag, "node %s has alwaysOutputData together with continueErrorOutput: a failure may then go down the normal output as an empty result instead of the failure output (work order 017 F8: failures must reach the FAILED line; what n8n really does is NOT proven until test T19)" % nm)
        if n.get("onError") == "continueRegularOutput" and short in EXTERNAL: silent.append(nm)
        if short in EXTERNAL and not n.get("retryOnFail"): noretry.append(nm)
        if n.get("disabled") is True: warn(tag, "node %s is disabled (n8n passes data through it; it sends and writes nothing)" % nm)
        # credentials
        cr = n.get("credentials")
        need = short in CRED_TYPES or (short == "httpRequest" and (n.get("parameters") or {}).get("authentication") not in (None, "none", ""))
        if need and (not isinstance(cr, dict) or not cr): fail(tag, "node %s (%s) has no credentials block" % (nm, short))
        for k, v in (cr or {}).items():
            if not isinstance(v, dict) or not str(v.get("name") or "").strip(): fail(tag, "node %s credential %r has no name" % (nm, k))
            elif not str(v.get("id") or "").strip(): fail(tag, "node %s credential %r has no id (name %r)" % (nm, k, v.get("name")))
            elif k in OPTS["cred_names"] and v.get("name") != OPTS["cred_names"][k]: fail(tag, "node %s credential %r has name %r, expected %r (--expect-credential)" % (nm, k, v.get("name"), OPTS["cred_names"][k]))
        if short in CRED_KIND and isinstance(cr, dict) and cr and not set(CRED_KIND[short]) & set(cr): fail(tag, "node %s (%s) credential kind(s) %s do not include the expected kind %s" % (nm, short, sorted(cr), " or ".join(repr(k) for k in CRED_KIND[short])))
        for k, v in (cr or {}).items():
            idv = str((v or {}).get("id") or "") if isinstance(v, dict) else ""
            if idv and any(p in idv for p in PLACEHOLDERS):
                msg = "node %s credential %r id %r is still a placeholder: replace it in n8n before import" % (nm, k, idv)
                if OPTS["real_ids"]: fail(tag, msg + " (--require-real-credential-ids)")
                else: warn(tag, msg + " [run with --require-real-credential-ids to make it a FAIL]")
        wf = (n.get("parameters") or {}).get("workflowId") if isinstance(n.get("parameters"), dict) else None
        for wv in (list(strings(wf)) if wf is not None else []):
            if any(p in wv for p in PLACEHOLDERS):
                msg = "node %s sub-workflow id %r is still a placeholder: replace it in n8n before import" % (nm, wv)
                if OPTS["real_ids"]: fail(tag, msg + " (--require-real-credential-ids)")
                else: warn(tag, msg + " [run with --require-real-credential-ids to make it a FAIL]")
        secret_scan(n, tag)
        envs = sorted({e for s_ in strings(n.get("parameters", {})) for e in ENVTOK.findall(s_)})
        if envs:
            msg = "node %s reads %s; if the take blocks environment-variable access inside nodes (n8n setting, name not verified here: %s) this node stops working" % (nm, ", ".join(envs), UNV)
            if OPTS["block_env"]: fail(tag, msg)
            else: LEAD["env"] += 1; lead(tag, msg + " [run with --block-env-access to make it a FAIL]")
        if n["type"] in ("n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger"):
            isw = n["type"] == "n8n-nodes-base.webhook"; what = "webhook" if isw else "form trigger"; table = WEBHOOK_AUTH if isw else FORM_AUTH
            au = (n.get("parameters") or {}).get("authentication", "none")
            if au in ("none", None, ""):
                msg = "%s %s has no authentication (anyone who knows the address can %s)" % (what, nm, "post" if isw else "submit")
                if not isw: msg += "; the n8n parameter name is itself %s" % UNV
                LEAD["webhook"] += 1
                if OPTS["webhook_auth"]: fail(tag, msg)
                else: lead(tag, msg + " [open web address: the owner decides, see REPORT.md; run with --require-webhook-auth to make it a FAIL]")
            elif au not in table: fail(tag, "%s %s authentication=%r is not one n8n accepts here (allowed: none, %s)" % (what, nm, au, ", ".join(sorted(table))))
            elif not isinstance(cr, dict) or not cr: fail(tag, "%s %s says authentication=%r but the node has no credentials block (the password is not attached)" % (what, nm, au))
            elif table[au] not in cr: fail(tag, "%s %s authentication=%r needs a credential of kind %r but the node has %s" % (what, nm, au, table[au], sorted(cr)))
            if isw:
                if n.get("disabled") is True: print("  [%s] webhook %s is disabled: no reply check" % (tag, nm))
                else: webhook_paths(n, nodes, adj, tag)
    if noretry: warn(tag, "external-call nodes without retryOnFail: %s" % sorted(noretry))
    if silent: warn(tag, "external-call nodes with onError=continueRegularOutput (an error becomes normal-looking data): %s" % sorted(silent))
    # references: upstream check (a node that is not upstream may not have run when the expression reads it)
    anc = {}
    rev = collections.defaultdict(set)
    for a, ts in adj.items():
        for t in ts: rev[t].add(a)
    def ancestors(x):
        if x in anc: return anc[x]
        out, st = set(), [x]
        while st:
            for p in rev.get(st.pop(), ()):
                if p not in out: out.add(p); st.append(p)
        anc[x] = out; return out
    for n in real:
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                if ref in byname and ref != n["name"] and ref not in ancestors(n["name"]) and not (n["type"].endswith("Trigger")): warn(tag, "node %s reads $('%s') which is not upstream of it (it may not have run)" % (n["name"], ref))
                if ref == n["name"]: warn(tag, "node %s reads its own output $('%s')" % (n["name"], ref))
    # a mail/CRM write whose own error, or an earlier external call's error, is swallowed (same idea as system-map M1; write = emailSend, hubspot, or httpRequest with a method other than GET)
    for n in real:
        short = n["type"].split(".")[-1]
        if short in ("emailSend", "hubspot") or (short == "httpRequest" and str((n.get("parameters") or {}).get("method", "GET")).upper() != "GET"):
            up = sorted(x for x in ancestors(n["name"]) if x in byname and byname[x]["type"].split(".")[-1] in EXTERNAL and byname[x].get("onError") == "continueRegularOutput")
            if n.get("onError") == "continueRegularOutput": warn(tag, "write node %s continues on error" % n["name"])
            if up: warn(tag, "write node %s has upstream external call(s) that continue on error: %s" % (n["name"], up))
    if OPTS["table"]:
        print("  error settings [%s]:" % tag)
        print("    %-18s %-18s %-22s %-10s %s" % ("node", "type", "onError", "retry", "alwaysOutputData"))
        for n in nodes: print("    %-18s %-18s %-22s %-10s %s" % (n["name"], n["type"].split(".")[-1], n.get("onError") or "(default stop)", ("x%s/%sms" % (n.get("maxTries", 3), n.get("waitBetweenTries", 1000))) if n.get("retryOnFail") else "no", "yes" if n.get("alwaysOutputData") else "no"))

def cross_file(dr, files):
    seen = {}
    for fn in files:
        p = os.path.join(dr, fn)
        try:
            with open(p, encoding="utf-8") as fh: d = json.load(fh)
        except Exception: continue
        for n in d.get("nodes", []) if isinstance(d, dict) and isinstance(d.get("nodes"), list) else []:
            if isinstance(n, dict) and n.get("type") == "n8n-nodes-base.webhook":
                pr = n.get("parameters") if isinstance(n.get("parameters"), dict) else {}   # a wrong shape is reported by shape_ok; here it is only skipped
                key = (str(pr.get("httpMethod", "GET")).upper(), str(pr.get("path")).strip().strip("/").lower())
                if key in seen: fail(dr, "two webhooks share method+path %s: %s and %s" % (key, seen[key], fn))
                else: seen[key] = fn
                wid = n.get("webhookId")
                if isinstance(wid, str) and wid:
                    if ("id", wid) in seen: fail(dr, "two webhooks share webhookId %r: %s and %s" % (wid, seen[("id", wid)], fn))
                    else: seen[("id", wid)] = fn

def check_flow(d, tag, expect, baseline_d):
    if not shape_ok(d, tag): return
    nodes = d["nodes"]
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
    trig_all = [n["name"] for n in nodes if is_trigger(n["type"])]
    trig = [n["name"] for n in nodes if is_trigger(n["type"]) and n.get("disabled") is not True]
    if not trig: fail(tag, "no enabled trigger node in file")
    seen, stack = set(trig), list(trig)
    while stack:
        for t in adj[stack.pop()]:
            if t not in seen: seen.add(t); stack.append(t)
    sticky = {n["name"] for n in nodes if n["type"] == STICKY}
    orphans = sorted(n for n in names if n not in incoming and n not in trig_all and n not in sticky)
    unreach = sorted(n for n in names if n not in seen and n not in sticky and n not in trig_all)
    if orphans: fail(tag, "orphan nodes (no incoming link, not a trigger) %s" % orphans)
    if unreach: fail(tag, "unreachable from any trigger %s" % unreach)
    if expect:
        if "nodes" in expect and len(nodes) != expect["nodes"]: fail(tag, "node count %d != expected %d" % (len(nodes), expect["nodes"]))
        if "connections" in expect and ncon != expect["connections"]: fail(tag, "connection count %d != expected %d" % (ncon, expect["connections"]))
    extra_checks(d, tag, nodes, adj, trig_all, sticky)
    base_nodes = {n.get("name"): n for n in (baseline_d or {}).get("nodes", [])}
    base_conns = (baseline_d or {}).get("connections", {})
    for n in nodes:
        outs = conns.get(n["name"], {}).get("main", [])
        def has(i): return i < len(outs) and bool(outs[i])
        kind = n["type"].split(".")[-1].lower()
        # how many normal outputs the node has (None = cannot tell)
        pr = n.get("parameters") or {}
        if n["type"] == "n8n-nodes-base.if": normal = 2
        elif n["type"] == "n8n-nodes-base.filter": normal = 1
        elif n["type"] == "n8n-nodes-base.switch":
            rules = (pr.get("rules") or {}).get("values") or (pr.get("rules") or {}).get("rules") or []
            normal = len(rules) + (1 if (pr.get("options") or {}).get("fallbackOutput") == "extra" else 0) or None
        else: normal = 1
        if n.get("onError") == "continueErrorOutput":
            if normal is None: warn(tag, "node %s: cannot tell which output is its error output (%s)" % (n["name"], UNV))
            elif not has(normal): fail(tag, "node %s has onError=continueErrorOutput but its error output main[%d] (the last output; %s) is missing or has no target" % (n["name"], normal, UNV))
        if n["type"] == "n8n-nodes-base.if":
            miss = [i for i in (0, 1) if not has(i)]
            if miss:
                bo = base_conns.get(n["name"], {}).get("main", [])
                base_missing = n["name"] in base_nodes and [i for i in (0, 1) if not (i < len(bo) and bo[i])] == miss
                (warn if base_missing else fail)(tag, "IF node %s lacks output(s) %s%s (project rule: every IF branch leads somewhere)" % (n["name"], miss, " (baseline already lacks the same)" if base_missing else ""))
        elif n["type"] == "n8n-nodes-base.switch":
            if not normal: warn(tag, "switch node %s: cannot tell its output count" % n["name"])
            else:
                miss = [i for i in range(normal) if not has(i)]
                if miss: warn(tag, "SWITCH node %s has unwired output(s) %s (legal in n8n, items on them stop silently)" % (n["name"], miss))
    for n in nodes:
        if n["type"] == STICKY: continue   # note text is prose, not an expression
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                if ref not in nameset: fail(tag, "node %s: expression refers to $('%s') which is not a node of this file" % (n["name"], ref))
            if PREV.search(s): warn(tag, "node %s uses $prevNode (cannot be resolved statically)" % n["name"])
            if DYNREF.search(s): warn(tag, "node %s reads a node by a computed name (not one plain quoted text); the name cannot be checked" % n["name"])
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

def creds(d):
    cr = [(n.get("name"), k, (v or {}).get("name"), (v or {}).get("id")) for n in d.get("nodes", []) for k, v in (n.get("credentials") or {}).items() if isinstance(v, dict)]
    print("  credentials (node, kind, name, id): " + ("; ".join("%s %s %s %s" % c for c in cr) if cr else "none"))

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
                for nm, want in WANT_CONN.items():
                    if d["connections"].get(nm) != want: fail(tag, "F-002 connection structure of %s is %s expected %s" % (nm, json.dumps(d["connections"].get(nm)), json.dumps(want)))
                cl = get(d, "Claim")
                if cl.get("onError") != "continueErrorOutput": fail(tag, "Claim onError is %r" % cl.get("onError"))
                print("  [%s] Claim alwaysOutputData=%r onError=%r" % (fname, cl.get("alwaysOutputData"), cl.get("onError")))
                warn(tag, F002_UNPROVEN, known=True)
                conds = get(d, "KeyOk")["parameters"].get("conditions", {}).get("conditions") or []
                print("  [%s] KeyOk IF condition: %s" % (fname, json.dumps(conds)))
                if len(conds) != 1 or conds[0].get("leftValue") != KEY_COND or conds[0].get("operator") != {"type": "boolean", "operation": "true", "singleValue": True}:
                    fail(tag, "F-002 KeyOk condition is not the expected string %r with boolean-true operator" % KEY_COND)
                for nm, code in (("ReplyBadKey", 422), ("ReplyStoreFail", 503)):
                    p = get(d, nm)["parameters"]; print("  [%s] %s status=%s body=%s" % (fname, nm, p.get("options", {}).get("responseCode"), p.get("responseBody")))
                    if p.get("options", {}).get("responseCode") != code: fail(tag, "F-002 %s responseCode is %r expected %d" % (nm, p.get("options", {}).get("responseCode"), code))
                if "$('Valid')" not in str(get(d, "ReplyStoreFail")["parameters"].get("responseBody")): fail(tag, "F-002 ReplyStoreFail body lacks the $('Valid') reference")
                print("  [%s] Valid lead_key assignment: %s" % (fname, [a.get("value") for a in get(d, "Valid")["parameters"]["assignments"]["assignments"] if a.get("name") == "lead_key"]))
    if "F008" in which:
        want = "none" if fname == "mf-recovery.json" else "all"
        s = d.get("settings", {})
        for k in ("saveDataSuccessExecution", "saveDataErrorExecution"):
            if s.get(k) != want: fail(tag, "F-008 %s is %r expected %r" % (k, s.get(k), want))

ALLOW_NODES = {  # allowed changes by patch: (flow files, node, changed path prefixes or None for added)
    "F002": [(("mf-form.json", "mf-hook.json"), "KeyOk", None), (("mf-form.json", "mf-hook.json"), "ReplyBadKey", None), (("mf-form.json", "mf-hook.json"), "ReplyStoreFail", None),
             (("mf-form.json", "mf-hook.json"), "Valid", ("parameters.assignments.assignments[lead_key].value",)),
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
                if pref is None or c.split(" (")[0] not in pref: fail(tag, "unexplained change in node %s at %s" % (nm, c))
    bc, pc = base.get("connections", {}), patched.get("connections", {})
    for src in sorted(set(bc) | set(pc)):
        if bc.get(src) != pc.get(src):
            out.append("  connections CHANGED for source %s" % src)
            if not any(src in ALLOW_CONN.get(a, ()) and fname in ("mf-form.json", "mf-hook.json") for a in allow): fail(tag, "unexplained connection change for source %s" % src)
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
            nonlocal i; i += 1
            if i >= len(argv): raise IndexError(a)
            return argv[i]
        try:
            if a == "--expect":
                try: k, v = val().split("=", 1); n, c = v.split(":"); expect[k] = {"nodes": int(n), "connections": int(c)}
                except ValueError: print("usage error: bad --expect value, want FILE=NODES:CONNS"); return 2
            elif a == "--expect-json":
                try:
                    with open(val(), encoding="utf-8") as fh: ej = json.load(fh)
                    if not isinstance(ej, dict): raise TypeError("not an object")
                    expect.update(ej)
                except (OSError, ValueError, TypeError, AttributeError): print("usage error: bad --expect-json file"); return 2
            elif a == "--expect-credential":
                try: k, v = val().split("=", 1)
                except ValueError: print("usage error: bad --expect-credential value, want KIND=NAME (for example postgres=my-credential)"); return 2
                OPTS["cred_names"][k] = v
            elif a == "--files": files = val().split(",")  # "all" = every *.json of each DIR
            elif a == "--baseline": baseline = val()
            elif a == "--patch-checks": pc = set(x for x in val().split(",") if x)
            elif a == "--diff-base": diffbase = val()
            elif a == "--allow": allow = [x for x in val().split(",") if x]
            elif a == "--diff-out": diffout = val()
            elif a == "--quiet-info": quiet = True
            elif a == "--require-webhook-auth": OPTS["webhook_auth"] = True
            elif a == "--table": OPTS["table"] = True
            elif a == "--block-env-access": OPTS["block_env"] = True
            elif a == "--require-real-credential-ids": OPTS["real_ids"] = True
            elif a.startswith("--"): print("usage error: unknown option", a); return 2
            else: dirs.append(a)
        except IndexError: print("usage error: option %s needs a value" % a); return 2
        i += 1
    if not dirs: print(__doc__); return 2
    for k, v in expect.items():
        if files != ["all"] and k not in files: print("usage error: --expect: unknown file key %r (known: %s)" % (k, sorted(files))); return 2
        if not isinstance(v, dict) or set(v) - {"nodes", "connections"}: print("usage error: --expect: bad entry for %r: %r" % (k, v)); return 2
    if pc - {"F002", "F008"}: print("usage error: unknown --patch-checks name(s) %s (known: F002, F008)" % sorted(pc - {"F002", "F008"})); return 2
    if set(allow) - {"F002", "F008"}: print("usage error: unknown --allow name(s) %s (known: F002, F008)" % sorted(set(allow) - {"F002", "F008"})); return 2
    if allow and not set(allow) <= pc: print("usage error: --allow %s needs --patch-checks to name the same patches (got %s)" % (",".join(allow), ",".join(sorted(pc)) or "none")); return 2
    if files == [""] or not files or any(not f.endswith(".json") for f in files if f != "all"): print("usage error: --files wants 'all' or a comma list of *.json names"); return 2
    diffsum = []
    print(HEADER, end="")
    for dr in dirs:
        print("### %s" % dr)
        if not os.path.isdir(dr): fail(dr, "not a directory"); continue
        have = sorted(x for x in os.listdir(dr) if x.endswith(".json"))
        dfiles = have if files == ["all"] else files
        if files == ["all"] and not have: fail(dr, "--files all: this folder holds no *.json file, so nothing was checked"); continue
        if have != sorted(dfiles): fail(dr, "file list %s != expected %s" % (have, sorted(dfiles)))
        for fn in dfiles:
            p = os.path.join(dr, fn); tag = "%s/%s" % (dr, fn)
            if not os.path.isfile(p): continue
            d = load(p, tag)
            if d is None: continue
            bd = load(os.path.join(baseline, fn), "baseline/" + fn) if baseline and os.path.isfile(os.path.join(baseline, fn)) else None
            try: r = check_flow(d, tag, expect.get(fn), bd)
            except Exception as e:
                fail(tag, "checker could not read this file (%s: %s); treat the file as broken" % (type(e).__name__, e)); continue
            if r: print("%s nodes=%d connections=%d triggers=%s saveDataSuccess=%s saveDataError=%s" % (fn, r["nodes"], r["connections"], r["triggers"], d.get("settings", {}).get("saveDataSuccessExecution"), d.get("settings", {}).get("saveDataErrorExecution")))
            if not r: continue
            try:
                creds(d)
                if not quiet: info(d, tag)
                if pc: patch_checks(d, fn, pc, tag)
                if diffbase:
                    bd2 = load(os.path.join(diffbase, fn), "diff-base/" + fn)
                    if bd2 and shape_ok(bd2, "diff-base/" + fn): node_diff(bd2, d, fn, allow, tag, diffsum)
            except Exception as e:
                fail(tag, "checker could not finish this file (%s: %s)" % (type(e).__name__, e))
        try: cross_file(dr, dfiles)
        except Exception as e: fail(dr, "cross-file check could not finish (%s: %s)" % (type(e).__name__, e))
    if diffbase:
        text = "\n".join(diffsum) + "\n"
        print(text)
        if diffout: open(diffout, "w", encoding="utf-8").write("# node-level diff, unpatched generator output vs patched (paths only, no values)\n# allowed patches: %s\n%s" % (",".join(allow) or "none", text))
    print("RESULT: %d FAIL, %d WARN" % (len(FAILS), len(WARNS)))
    final_block()
    return 1 if FAILS else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
