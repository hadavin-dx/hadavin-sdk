"""Static, read-only dump of n8n flow json (standard library only).
Usage:
  dump_nodes.py table <json> [<json>...]   one markdown row per node (machine columns)
  dump_nodes.py counts <root>              files and node counts under <root>/n8n-*/**.json
  dump_nodes.py diff <a.json> <b.json>     node/param/connection differences a -> b
Secret-looking parameter values are masked; only key names are printed."""
import json, re, sys, glob, os
SECRET_KEY = re.compile(r'(token|secret|password|passwd|apikey|api_key|authorization|bearer)', re.I)
SECRET_VAL = re.compile(r'(Bearer\s+\S+|[A-Za-z0-9_\-]{32,}|postgres(ql)?://\S+)')

def mask(v, key=''):
    if isinstance(v, dict): return {k: mask(x, k) for k, x in v.items()}
    if isinstance(v, list): return [mask(x, key) for x in v]
    if isinstance(v, str) and not v.startswith('=') and (SECRET_KEY.search(key) or SECRET_VAL.search(v)): return '<masked>'
    return v

def load(path):
    d = json.load(open(path))
    names = [n['name'] for n in d['nodes']]
    edges = {}
    for src, v in d.get('connections', {}).items():
        for kind, outs in v.items():
            for i, ts in enumerate(outs):
                for t in ts or []:
                    edges.setdefault(src, []).append((i, t['node']))
    return d, names, edges

def reachable(d, edges):
    """Dead rule: no incoming edge AND not a trigger AND not an Execute Workflow sub-entry AND not error-workflow target."""
    incoming = {t for l in edges.values() for _, t in l}
    entry = [n['name'] for n in d['nodes'] if 'trigger' in n['type'].lower() or n['type'].endswith('.webhook')
             or n['type'].endswith('executeWorkflowTrigger') or n['type'].endswith('errorTrigger')]
    seen, stack = set(entry), list(entry)
    while stack:
        for _, t in edges.get(stack.pop(), []):
            if t not in seen: seen.add(t); stack.append(t)
    return {n['name']: ('Y' if n['name'] in seen else ('NO-INCOMING' if n['name'] not in incoming else 'UNREACHED-FROM-TRIGGER')) for n in d['nodes']}

def table(path):
    d, names, edges = load(path)
    reach = reachable(d, edges)
    print(f"### {path} ({len(names)} nodes)  workflow={d.get('name')!r} settings={json.dumps(d.get('settings'))}")
    print("| # | node | type | parameters (masked) | downstream (out,node) | onError | retry/tries/wait | disabled | credential | reachable |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for k, n in enumerate(d['nodes'], 1):
        cred = ','.join(f"{a}:{b.get('name')}" for a, b in (n.get('credentials') or {}).items()) or 'none'
        p = json.dumps(mask(n.get('parameters', {})), ensure_ascii=False).replace('|', '\\|')
        print(f"| {k} | {n['name']} | {n['type']} v{n.get('typeVersion')} | {p} | {edges.get(n['name'], 'none')} | {n.get('onError')} | {n.get('retryOnFail')}/{n.get('maxTries')}/{n.get('waitBetweenTries')} | {n.get('disabled')} | {cred} | {reach[n['name']]} |")
    dang = [(s, t) for s, l in edges.items() for _, t in l if t not in names]
    print(f"dangling edges: {dang}; node names unique: {len(names) == len(set(names))}")

def counts(root):
    tot = 0
    for f in sorted(glob.glob(os.path.join(root, 'n8n-*/**/*.json'), recursive=True)):
        try: d = json.load(open(f))
        except Exception as e: print('PARSE-FAIL', f, e); continue
        if isinstance(d, dict) and 'nodes' in d:
            print(len(d['nodes']), os.path.relpath(f, root)); tot += len(d['nodes'])
    print('TOTAL nodes', tot)

def diff(a, b):
    da, na, ea = load(a); db, nb, eb = load(b)
    A = {n['name']: n for n in da['nodes']}; B = {n['name']: n for n in db['nodes']}
    for k in A.keys() - B.keys(): print('REMOVED node', k)
    for k in B.keys() - A.keys(): print('ADDED node', k)
    for k in A.keys() & B.keys():
        for f in ('type', 'typeVersion', 'parameters', 'credentials', 'onError', 'retryOnFail', 'maxTries', 'waitBetweenTries', 'alwaysOutputData', 'disabled'):
            if A[k].get(f) != B[k].get(f):
                print(f'CHANGED {k}.{f}: {json.dumps(mask(A[k].get(f)))[:300]} -> {json.dumps(mask(B[k].get(f)))[:300]}')
    sa = {(s, i, t) for s, l in ea.items() for i, t in l}; sb = {(s, i, t) for s, l in eb.items() for i, t in l}
    for e in sorted(sa - sb): print('REMOVED edge', e)
    for e in sorted(sb - sa): print('ADDED edge', e)
    print('settings equal:', da.get('settings') == db.get('settings'))

if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'table': [table(p) for p in args]
    elif cmd == 'counts': counts(args[0])
    elif cmd == 'diff': diff(*args)
    else: sys.exit(__doc__)
