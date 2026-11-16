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
  --quiet-info                  do not print the type table and the placeholder list

Checks per file (FAIL = exit code 1): JSON parses; every node has name and type; no duplicate names; every connection
source and target exists; at least one trigger; every node reachable from a trigger (reachability walk over all output
types, so a node whose only incoming link comes from an orphan or from itself is unreachable); node/connection counts
equal the expected ones; onError=continueErrorOutput nodes have a non-empty main[1]; IF nodes have both branch outputs;
every $('Name') and $node["Name"] inside an expression names a node of the same file.
Trigger = exact type n8n-nodes-base.webhook, n8n-nodes-base.executeWorkflowTrigger, n8n-nodes-base.formTrigger, or a type
ending in 'Trigger'. respondToWebhook is NOT a trigger.
F-002 alwaysOutputData/onError on Claim is only printed with a WARN (UNPROVEN until test T19): exit 0 does NOT clear F-002.
Exit code: 0 only if no FAIL; 1 otherwise; 2 for a usage error."""

import collections
import json
import os
import re
import sys

FILES_DEFAULT = ["mf-form.json", "mf-hook.json", "mf-recovery.json", "mf-sub-crm-mail.json"]
TRIGGER_EXACT = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.executeWorkflowTrigger",
    "n8n-nodes-base.formTrigger",
}
PLACEHOLDERS = [
    "PLACEHOLDER",
    "PG_CREDENTIAL_ID",
    "SMTP_CREDENTIAL_ID",
    "SUB_WORKFLOW_ID",
    "HS_CRED",
    "HUBSPOT_CREDENTIAL_ID",
]
REF = re.compile(
    r"""\$\(\s*['"]([^'"]+)['"]\s*\)|\$node\[\s*['"]([^'"]+)['"]\s*\]|\$items\(\s*['"]([^'"]+)['"]"""
)
PREV = re.compile(r"\$prevNode\b")
IFLIKE = ("n8n-nodes-base.if", "n8n-nodes-base.filter", "n8n-nodes-base.switch")
KEY_COND = "={{ /^[A-Za-z0-9_-]{1,64}$/.test($json.lead_key) }}"
WANT_CONN = {
    "Valid": {"main": [[{"node": "KeyOk", "type": "main", "index": 0}]]},
    "KeyOk": {
        "main": [
            [{"node": "Claim", "type": "main", "index": 0}],
            [{"node": "ReplyBadKey", "type": "main", "index": 0}],
        ]
    },
    "Claim": {
        "main": [
            [{"node": "Claimed", "type": "main", "index": 0}],
            [{"node": "ReplyStoreFail", "type": "main", "index": 0}],
        ]
    },
}
F002_UNPROVEN = (
    "F-002 Claim alwaysOutputData/onError UNPROVEN until T19 (repeat key still gets its answer)"
)
ENVTOK = re.compile(r"\$env\.[A-Za-z0-9_]+")
FAILS, WARNS = [], []


def fail(where, msg):
    FAILS.append(f"{where}: {msg}")
    print("FAIL", where, msg)


def warn(where, msg):
    WARNS.append(f"{where}: {msg}")
    print("WARN", where, msg)


def is_trigger(t):
    return t in TRIGGER_EXACT or t.endswith("Trigger")


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def load(path, tag):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(tag, f"parse failure {type(e).__name__}")
        return None


def targets_of(outs):
    for typ, lists in (outs or {}).items():
        for idx, lst in enumerate(lists):
            for c in lst or []:
                yield typ, idx, c.get("node")


def check_flow(d, tag, expect, baseline_d):
    nodes = d.get("nodes")
    if not isinstance(nodes, list):
        fail(tag, "no nodes list")
        return
    bad = [i for i, n in enumerate(nodes) if not n.get("name") or not n.get("type")]
    if bad:
        fail(tag, f"node(s) at index {bad} lack name or type")
        nodes = [n for n in nodes if n.get("name") and n.get("type")]
    names = [n["name"] for n in nodes]
    nameset = set(names)
    dups = sorted(k for k, v in collections.Counter(names).items() if v > 1)
    if dups:
        fail(tag, f"duplicate names {dups}")
    conns = d.get("connections", {})
    ncon = 0
    adj = collections.defaultdict(set)
    incoming = set()
    for src, outs in conns.items():
        if src not in nameset:
            fail(tag, f"connection source {src!r} is not a node")
        for typ, idx, t in targets_of(outs):
            ncon += 1
            if t not in nameset:
                fail(tag, f"dangling target {t!r} from {src!r}")
            else:
                adj[src].add(t)
                incoming.add(t)
    trig = [n["name"] for n in nodes if is_trigger(n["type"])]
    if not trig:
        fail(tag, "no trigger node in file")
    seen, stack = set(trig), list(trig)
    while stack:
        for t in adj[stack.pop()]:
            if t not in seen:
                seen.add(t)
                stack.append(t)
    orphans = sorted(n for n in names if n not in incoming and n not in trig)
    unreach = sorted(n for n in names if n not in seen)
    if orphans:
        fail(tag, f"orphan nodes (no incoming link, not a trigger) {orphans}")
    if unreach:
        fail(tag, f"unreachable from any trigger {unreach}")
    if expect:
        if "nodes" in expect and len(nodes) != expect["nodes"]:
            fail(tag, f"node count {len(nodes)} != expected {expect['nodes']}")
        if "connections" in expect and ncon != expect["connections"]:
            fail(tag, f"connection count {ncon} != expected {expect['connections']}")
    base_nodes = {n.get("name"): n for n in (baseline_d or {}).get("nodes", [])}
    base_conns = (baseline_d or {}).get("connections", {})
    for n in nodes:
        outs = conns.get(n["name"], {}).get("main", [])

        def has(i):
            return i < len(outs) and bool(outs[i])

        if n.get("onError") == "continueErrorOutput" and not has(1):
            fail(
                tag,
                "node {} has onError=continueErrorOutput but main[1] is missing or has no target".format(n["name"]),
            )
        if n["type"] in IFLIKE:
            if n["type"] == "n8n-nodes-base.switch":
                pr = n.get("parameters", {})
                rules = (
                    (pr.get("rules") or {}).get("values")
                    or (pr.get("rules") or {}).get("rules")
                    or []
                )
                need = list(
                    range(
                        len(rules)
                        + (1 if (pr.get("options") or {}).get("fallbackOutput") == "extra" else 0)
                    )
                )
                if not need:
                    warn(tag, "switch node {}: cannot tell its output count".format(n["name"]))
            else:
                need = [0, 1]
            kind = n["type"].split(".")[-1].upper()
            miss = [i for i in need if not has(i)]
            if miss:
                bo = base_conns.get(n["name"], {}).get("main", [])
                base_missing = (
                    n["name"] in base_nodes
                    and [i for i in need if not (i < len(bo) and bo[i])] == miss
                )
                (warn if base_missing else fail)(
                    tag,
                    "{} node {} lacks output(s) {}{}".format(
                        kind if kind != "IF" else "IF",
                        n["name"],
                        miss,
                        " (baseline already lacks the same)" if base_missing else "",
                    ),
                )
    for n in nodes:
        for s in strings(n.get("parameters", {})):
            for m in REF.finditer(s):
                ref = m.group(1) or m.group(2) or m.group(3)
                if ref not in nameset:
                    fail(
                        tag,
                        "node {}: expression refers to $('{}') which is not a node of this file".format(n["name"], ref),
                    )
            if PREV.search(s):
                warn(tag, "node {} uses $prevNode (cannot be resolved statically)".format(n["name"]))
    return {"nodes": len(nodes), "connections": ncon, "triggers": trig}


def info(d, tag):
    tc = collections.Counter((n.get("type"), n.get("typeVersion")) for n in d.get("nodes", []))
    print(
        "  types:", "; ".join(f"{t} v{v} x{c}" for (t, v), c in sorted(tc.items(), key=str))
    )
    raw = json.dumps(d)
    where = collections.defaultdict(set)
    for n in d.get("nodes", []):
        s = json.dumps(n)
        for p in PLACEHOLDERS:
            if p in s:
                where[p].add(n.get("name"))
        for e in ENVTOK.findall(s):
            where[e].add(n.get("name"))
    for k in sorted(where):
        print(
            f"  placeholder/env {k:<34} count={len(re.findall(re.escape(k), raw))}"
            f" nodes={sorted(where[k])}"
        )
    if not where:
        print("  placeholder/env: none")


def deep_diff(a, b, path=""):
    """Paths (no values) where a and b differ. Lists of dicts that carry 'name' are aligned by name."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = path + "." + k if path else k
            if k not in a:
                out.append(p + " (added)")
            elif k not in b:
                out.append(p + " (removed)")
            else:
                out += deep_diff(a[k], b[k], p)
    elif isinstance(a, list) and isinstance(b, list):
        if all(isinstance(x, dict) and "name" in x for x in a + b) and (a or b):
            da, db = {x["name"]: x for x in a}, {x["name"]: x for x in b}
            for k in sorted(set(da) | set(db)):
                p = f"{path}[{k}]"
                if k not in da:
                    out.append(p + " (added)")
                elif k not in db:
                    out.append(p + " (removed)")
                else:
                    out += deep_diff(da[k], db[k], p)
        elif len(a) != len(b):
            out.append(f"{path} (list length {len(a)} -> {len(b)})")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += deep_diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(path)
    return out


def get(d, name):
    return next((n for n in d["nodes"] if n["name"] == name), None)


def patch_checks(d, fname, which, tag):
    form = fname in ("mf-form.json", "mf-hook.json")
    main = lambda nm: d["connections"].get(nm, {}).get("main", [])
    tg = lambda nm, i: sorted(c["node"] for c in (main(nm)[i] if i < len(main(nm)) else []))
    if "F002" in which:
        new = ["KeyOk", "ReplyBadKey", "ReplyStoreFail"]
        if not form:
            for nm in new:
                if get(d, nm):
                    fail(tag, f"F-002 node {nm} must exist only in mf-form and mf-hook")
        else:
            for nm in new:
                if not get(d, nm):
                    fail(tag, f"F-002 node {nm} missing")
            if all(get(d, nm) for nm in new):
                links = [
                    ("Valid", 0, ["KeyOk"]),
                    ("KeyOk", 0, ["Claim"]),
                    ("KeyOk", 1, ["ReplyBadKey"]),
                    ("Claim", 0, ["Claimed"]),
                    ("Claim", 1, ["ReplyStoreFail"]),
                ]
                for s, i, want in links:
                    if tg(s, i) != want:
                        fail(tag, f"F-002 link {s} out{i} -> {tg(s, i)} expected {want}")
                for nm, want in WANT_CONN.items():
                    if d["connections"].get(nm) != want:
                        fail(
                            tag,
                            "F-002 connection structure of {} is {} expected {}".format(nm, json.dumps(d["connections"].get(nm)), json.dumps(want)),
                        )
                cl = get(d, "Claim")
                if cl.get("onError") != "continueErrorOutput":
                    fail(tag, "Claim onError is {!r}".format(cl.get("onError")))
                print(
                    "  [{}] Claim alwaysOutputData={!r} onError={!r}".format(fname, cl.get("alwaysOutputData"), cl.get("onError"))
                )
                warn(tag, F002_UNPROVEN)
                conds = get(d, "KeyOk")["parameters"].get("conditions", {}).get("conditions") or []
                print(f"  [{fname}] KeyOk IF condition: {json.dumps(conds)}")
                if (
                    len(conds) != 1
                    or conds[0].get("leftValue") != KEY_COND
                    or conds[0].get("operator")
                    != {"type": "boolean", "operation": "true", "singleValue": True}
                ):
                    fail(
                        tag,
                        f"F-002 KeyOk condition is not the expected string {KEY_COND!r} with boolean-true operator",
                    )
                for nm, code in (("ReplyBadKey", 422), ("ReplyStoreFail", 503)):
                    p = get(d, nm)["parameters"]
                    print(
                        "  [{}] {} status={} body={}".format(
                            fname,
                            nm,
                            p.get("options", {}).get("responseCode"),
                            p.get("responseBody"),
                        )
                    )
                    if p.get("options", {}).get("responseCode") != code:
                        fail(
                            tag,
                            f"F-002 {nm} responseCode is "
                            f"{p.get('options', {}).get('responseCode')!r} expected {code}",
                        )
                if "$('Valid')" not in str(
                    get(d, "ReplyStoreFail")["parameters"].get("responseBody")
                ):
                    fail(tag, "F-002 ReplyStoreFail body lacks the $('Valid') reference")
                print(
                    "  [{}] Valid lead_key assignment: {}".format(
                        fname,
                        [
                            a.get("value")
                            for a in get(d, "Valid")["parameters"]["assignments"]["assignments"]
                            if a.get("name") == "lead_key"
                        ],
                    )
                )
    if "F008" in which:
        want = "none" if fname == "mf-recovery.json" else "all"
        s = d.get("settings", {})
        for k in ("saveDataSuccessExecution", "saveDataErrorExecution"):
            if s.get(k) != want:
                fail(tag, f"F-008 {k} is {s.get(k)!r} expected {want!r}")


ALLOW_NODES = {  # allowed changes by patch: (flow files, node, changed path prefixes or None for added)
    "F002": [
        (("mf-form.json", "mf-hook.json"), "KeyOk", None),
        (("mf-form.json", "mf-hook.json"), "ReplyBadKey", None),
        (("mf-form.json", "mf-hook.json"), "ReplyStoreFail", None),
        (
            ("mf-form.json", "mf-hook.json"),
            "Valid",
            ("parameters.assignments.assignments[lead_key].value",),
        ),
        (("mf-form.json", "mf-hook.json"), "Claim", ("onError", "alwaysOutputData")),
    ]
}
ALLOW_CONN = {"F002": ("Valid", "KeyOk", "Claim")}
ALLOW_SETTINGS = {
    "F008": {
        "mf-form.json": ("saveDataSuccessExecution", "saveDataErrorExecution"),
        "mf-hook.json": ("saveDataSuccessExecution", "saveDataErrorExecution"),
        "mf-sub-crm-mail.json": ("saveDataSuccessExecution", "saveDataErrorExecution"),
    }
}


def node_diff(base, patched, fname, allow, tag, out):
    bn = {n["name"]: n for n in base["nodes"]}
    pn = {n["name"]: n for n in patched["nodes"]}
    allowed = [r for a in allow for r in ALLOW_NODES.get(a, []) if fname in r[0]]
    allow_added = {r[1] for r in allowed if r[2] is None}
    allow_changed = {r[1]: r[2] for r in allowed if r[2] is not None}
    out.append(f"== {tag} ==")
    for nm in sorted(set(pn) - set(bn)):
        out.append("  node ADDED   {} ({} v{})".format(nm, pn[nm]["type"], pn[nm]["typeVersion"]))
        if nm not in allow_added:
            fail(tag, f"unexplained added node {nm}")
    for nm in sorted(set(bn) - set(pn)):
        out.append(f"  node REMOVED {nm}")
        fail(tag, f"unexplained removed node {nm}")
    for nm in sorted(set(bn) & set(pn)):
        ch = deep_diff(bn[nm], pn[nm])
        if ch:
            out.append("  node CHANGED {}: {}".format(nm, ", ".join(ch)))
            pref = allow_changed.get(nm)
            for c in ch:
                if pref is None or c.split(" (")[0] not in pref:
                    fail(tag, f"unexplained change in node {nm} at {c}")
    bc, pc = base.get("connections", {}), patched.get("connections", {})
    for src in sorted(set(bc) | set(pc)):
        if bc.get(src) != pc.get(src):
            out.append(f"  connections CHANGED for source {src}")
            if not any(src in ALLOW_CONN.get(a, ()) for a in allow):
                fail(tag, f"unexplained connection change for source {src}")
    bs, ps = base.get("settings", {}), patched.get("settings", {})
    for k in sorted(set(bs) | set(ps)):
        if bs.get(k) != ps.get(k):
            out.append(f"  settings CHANGED {k}: {bs.get(k)!r} -> {ps.get(k)!r}")
            if not any(k in ALLOW_SETTINGS.get(a, {}).get(fname, ()) for a in allow):
                fail(tag, f"unexplained settings change {k}")
    for k in sorted(set(base) | set(patched)):
        if k not in ("nodes", "connections", "settings") and base.get(k) != patched.get(k):
            out.append(f"  top-level key {k} CHANGED")
            fail(tag, f"unexplained top-level change {k}")


def main(argv):
    dirs, expect, files, baseline, pc, diffbase, allow, diffout, quiet = (
        [],
        {},
        FILES_DEFAULT,
        None,
        set(),
        None,
        [],
        None,
        False,
    )
    i = 0
    while i < len(argv):
        a = argv[i]

        def val():
            nonlocal i
            i += 1
            return argv[i]

        if a == "--expect":
            try:
                k, v = val().split("=", 1)
                n, c = v.split(":")
                expect[k] = {"nodes": int(n), "connections": int(c)}
            except (ValueError, IndexError):
                print("bad --expect value, want FILE=NODES:CONNS")
                return 2
        elif a == "--expect-json":
            expect.update(json.load(open(val(), encoding="utf-8")))
        elif a == "--files":
            files = val().split(",")
        elif a == "--baseline":
            baseline = val()
        elif a == "--patch-checks":
            pc = set(val().split(","))
        elif a == "--diff-base":
            diffbase = val()
        elif a == "--allow":
            allow = [x for x in val().split(",") if x]
        elif a == "--diff-out":
            diffout = val()
        elif a == "--quiet-info":
            quiet = True
        elif a.startswith("--"):
            print("unknown option", a)
            return 2
        else:
            dirs.append(a)
        i += 1
    if not dirs:
        print(__doc__)
        return 2
    for k, v in expect.items():
        if k not in files:
            fail("--expect", f"unknown file key {k!r} (known: {sorted(files)})")
        if not isinstance(v, dict) or set(v) - {"nodes", "connections"}:
            fail("--expect", f"bad entry for {k!r}: {v!r}")
    if allow and not set(allow) <= pc:
        fail(
            "args",
            "--allow {} needs --patch-checks to name the same patches (got {})".format(",".join(allow), ",".join(sorted(pc)) or "none"),
        )
    diffsum = []
    for dr in dirs:
        print(f"### {dr}")
        if not os.path.isdir(dr):
            fail(dr, "not a directory")
            continue
        have = sorted(x for x in os.listdir(dr) if x.endswith(".json"))
        if have != sorted(files):
            fail(dr, f"file list {have} != expected {sorted(files)}")
        for fn in files:
            p = os.path.join(dr, fn)
            tag = f"{dr}/{fn}"
            if not os.path.isfile(p):
                continue
            d = load(p, tag)
            if d is None:
                continue
            bd = (
                load(os.path.join(baseline, fn), "baseline/" + fn)
                if baseline and os.path.isfile(os.path.join(baseline, fn))
                else None
            )
            r = check_flow(d, tag, expect.get(fn), bd)
            if r:
                print(
                    f"{fn} nodes={r['nodes']} connections={r['connections']} "
                    f"triggers={r['triggers']} "
                    f"saveDataSuccess={d.get('settings', {}).get('saveDataSuccessExecution')} "
                    f"saveDataError={d.get('settings', {}).get('saveDataErrorExecution')}"
                )
            if r and not quiet:
                info(d, tag)
            if pc:
                patch_checks(d, fn, pc, tag)
            if diffbase:
                bd2 = load(os.path.join(diffbase, fn), "diff-base/" + fn)
                if bd2:
                    node_diff(bd2, d, fn, allow, tag, diffsum)
    if diffbase:
        text = "\n".join(diffsum) + "\n"
        print(text)
        if diffout:
            open(diffout, "w", encoding="utf-8").write(
                "# node-level diff, unpatched generator output vs patched (paths only, no values)\n# allowed patches: {}\n{}".format(",".join(allow) or "none", text)
            )
    print(f"RESULT: {len(FAILS)} FAIL, {len(WARNS)} WARN")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
