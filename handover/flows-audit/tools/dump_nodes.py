"""Static, read-only dump of n8n flow json (standard library only).
Usage:
  dump_nodes.py table <json> [<json>...]   one markdown row per node (machine columns)
  dump_nodes.py counts <root>              files and node counts under <root>/n8n-*/**.json
  dump_nodes.py diff <a.json> <b.json>     node/param/connection differences a -> b
Secret-looking parameter values are masked; only key names are printed."""

import glob
import json
import os
import re
import sys

_P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mask_patterns.json")))
SECRET_KEY = re.compile(_P["key_name_regex"], re.IGNORECASE)
VALUE_RES = [re.compile(r) for r in _P["value_regexes"]]
EXPR_RES = [re.compile(r) for r in _P["expression_regexes"]]
WHOLE = re.compile(_P["whole_token_regex"])
ALLOW = [re.compile(r) for r in _P["allow_regexes"]]


def _secret_value(v, key):
    if v.startswith("="):
        return any(r.search(v) for r in EXPR_RES)
    if SECRET_KEY.search(key):
        return True
    if any(r.search(v) for r in VALUE_RES):
        return True
    return bool(WHOLE.fullmatch(v)) and not any(r.fullmatch(v) for r in ALLOW)


def mask(v, key=""):
    if isinstance(v, dict):
        return {k: mask(x, k) for k, x in v.items()}
    if isinstance(v, list):
        return [mask(x, key) for x in v]
    if isinstance(v, str) and _secret_value(v, key):
        return "<masked>"
    return v


def load(path):
    d = json.load(open(path))
    names = [n["name"] for n in d["nodes"]]
    edges = {}
    for src, v in d.get("connections", {}).items():
        for outs in v.values():
            for i, ts in enumerate(outs):
                for t in ts or []:
                    edges.setdefault(src, []).append((i, t["node"]))
    return d, names, edges


def reachable(d, edges):
    """Dead rule: no incoming edge AND not a trigger AND not an Execute Workflow sub-entry AND not error-workflow target."""
    incoming = {t for l in edges.values() for _, t in l}
    entry = [
        n["name"]
        for n in d["nodes"]
        if not n.get("disabled")
        and (
            "trigger" in n["type"].lower()
            or n["type"].endswith(".webhook")
            or n["type"].endswith("executeWorkflowTrigger")
            or n["type"].endswith("errorTrigger")
        )
    ]
    seen, stack = set(entry), list(entry)
    while stack:
        for _, t in edges.get(stack.pop(), []):
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return {
        n["name"]: (
            "ENTRY"
            if n["name"] in entry
            else "Y"
            if n["name"] in seen
            else ("NO-INCOMING" if n["name"] not in incoming else "UNREACHED-FROM-TRIGGER")
        )
        for n in d["nodes"]
    }


def table(path):
    d, names, edges = load(path)
    reach = reachable(d, edges)
    print(
        f"### {path} ({len(names)} nodes)  workflow={d.get('name')!r} settings={json.dumps(d.get('settings'))}"
    )
    print(
        "| # | node | type | parameters (masked) | downstream (out,node) | onError | retry/tries/wait | disabled | credential | reachable |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for k, n in enumerate(d["nodes"], 1):
        cred = (
            ",".join(f"{a}:{b.get('name')}" for a, b in (n.get("credentials") or {}).items())
            or "none"
        )
        p = json.dumps(mask(n.get("parameters", {})), ensure_ascii=False).replace("|", "\\|")
        print(
            f"| {k} | {n['name']} | {n['type']} v{n.get('typeVersion')} | {p} | {edges.get(n['name'], 'none')} | {n.get('onError')} | {n.get('retryOnFail')}/{n.get('maxTries')}/{n.get('waitBetweenTries')} | {n.get('disabled')} | {cred} | {reach[n['name']]} |"
        )
    dang = [(s, t) for s, l in edges.items() for _, t in l if t not in names]
    print(f"dangling edges: {dang}; node names unique: {len(names) == len(set(names))}")


JUDGE = [
    "purpose",
    "trigger or upstream",
    "inputs",
    "outputs",
    "error path",
    "idempotency key",
    "writes (store, table or file)",
    "secrets (names only)",
    "identity it runs as",
    "logs to",
    "what a person sees",
    "stop condition",
    "finding id",
]


def skeleton(path):
    """table rows plus 13 judgement columns marked TODO (lane agents replace TODO only)."""
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        table(path)
    for l in buf.getvalue().splitlines():
        if l.startswith("| # |"):
            print(l + " " + " | ".join(JUDGE) + " |")
        elif l.startswith("|---"):
            print(l + "---|" * len(JUDGE))
        elif re.match(r"\| \d+ \|", l):
            print(l + " TODO |" * len(JUDGE))
        else:
            print(l)


def flow_files(root):
    return [
        f
        for f in sorted(glob.glob(os.path.join(root, "n8n-*/**/*.json"), recursive=True))
        if "/n8n-tests/" not in f.replace(os.sep, "/")
    ]


def check(path):
    """exit 1 on unparsable file, duplicate node names or dangling edges"""
    try:
        _d, names, edges = load(path)
    except Exception as e:
        print("PARSE-FAIL", path, e)
        return 1
    dang = [(s, t) for s, l in edges.items() for _, t in l if t not in names]
    dup = sorted({n for n in names if names.count(n) > 1})
    print(path, "dangling:", dang, "duplicate names:", dup)
    return 1 if dang or dup else 0


def counts(root):
    tot = 0
    for f in flow_files(root):
        try:
            d = json.load(open(f))
        except Exception as e:
            print("PARSE-FAIL", f, e)
            continue
        if isinstance(d, dict) and "nodes" in d:
            print(len(d["nodes"]), os.path.relpath(f, root))
            tot += len(d["nodes"])
    print("TOTAL nodes", tot)


def diff(a, b):
    da, _na, ea = load(a)
    db, _nb, eb = load(b)
    A = {n["name"]: n for n in da["nodes"]}
    B = {n["name"]: n for n in db["nodes"]}
    for k in A.keys() - B.keys():
        print("REMOVED node", k)
    for k in B.keys() - A.keys():
        print("ADDED node", k)
    for k in A.keys() & B.keys():
        for f in (
            "type",
            "typeVersion",
            "parameters",
            "credentials",
            "onError",
            "retryOnFail",
            "maxTries",
            "waitBetweenTries",
            "alwaysOutputData",
            "disabled",
        ):
            if A[k].get(f) != B[k].get(f):
                print(
                    f"CHANGED {k}.{f}: {json.dumps(mask(A[k].get(f)))[:300]} -> {json.dumps(mask(B[k].get(f)))[:300]}"
                )
    sa = {(s, i, t) for s, l in ea.items() for i, t in l}
    sb = {(s, i, t) for s, l in eb.items() for i, t in l}
    for e in sorted(sa - sb):
        print("REMOVED edge", e)
    for e in sorted(sb - sa):
        print("ADDED edge", e)
    print("settings equal:", da.get("settings") == db.get("settings"))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "table":
        [table(p) for p in args]
    elif cmd == "counts":
        counts(args[0])
    elif cmd == "diff":
        diff(*args)
    elif cmd == "skeleton":
        [skeleton(p) for p in args]
    elif cmd == "check":
        sys.exit(max([check(p) for p in args] or [0]))
    else:
        sys.exit(__doc__)
