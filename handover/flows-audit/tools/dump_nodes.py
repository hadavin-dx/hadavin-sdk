"""Static dump of n8n flow json: one block per node (type, params, creds, edges). Read-only."""
import json, sys
def dump(path):
    d = json.load(open(path))
    names = {n['name'] for n in d['nodes']}
    out = {}
    for src, v in d.get('connections', {}).items():
        for kind, outs in v.items():
            for i, targets in enumerate(outs):
                for t in targets or []:
                    out.setdefault(src, []).append((i, t['node']))
    incoming = {t for lst in out.values() for _, t in lst}
    print(f"## {path}  name={d.get('name')!r} nodes={len(d['nodes'])} settings={json.dumps(d.get('settings'))}")
    for n in d['nodes']:
        nm = n['name']
        flags = []
        if nm not in incoming and 'trigger' not in n['type'].lower() and 'Trigger' not in n['type']:
            flags.append('NO-INCOMING')
        if nm not in out: flags.append('TERMINAL')
        print(f"- {nm} | {n['type']} v{n.get('typeVersion')} | onError={n.get('onError')} retry={n.get('retryOnFail')} tries={n.get('maxTries')} wait={n.get('waitBetweenTries')} alwaysOut={n.get('alwaysOutputData')} disabled={n.get('disabled')} | creds={json.dumps(n.get('credentials'))} | {','.join(flags)}")
        print(f"    params={json.dumps(n.get('parameters'), ensure_ascii=False)}")
        print(f"    edges={out.get(nm)}")
    dangling = [(s, t) for s, l in out.items() for _, t in l if t not in names]
    print('dangling edges:', dangling)
for p in sys.argv[1:]:
    dump(p)
