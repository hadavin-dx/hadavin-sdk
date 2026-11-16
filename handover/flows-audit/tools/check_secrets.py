"""Check (e). Scans every file under handover/flows-audit except tools/scratch, tools/fixtures, tools/mask_patterns.json and tools/test_dump_nodes.py for the patterns in mask_patterns.json: bearer text, credential-bearing connection strings, and whole 32+ character key-like tokens (git shas are allowed). 0 hits = pass. Run from repo root. Exit 0/1."""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..'); P = json.load(open(os.path.join(H, 'mask_patterns.json')))
vals = [re.compile(r) for r in P['value_regexes']]; whole = re.compile(P['whole_token_regex']); allow = [re.compile(r) for r in P['allow_regexes']]
ident = re.compile(r'-{32,}|[A-Za-z]{1,14}\d{0,3}([_-]([A-Za-z]{1,14}\d{0,3}|\d{1,4})){3,}')  # plain-word identifiers (test names, headings, table rules); a random token has long mixed segments and still hits
skip = ('tools/scratch/', 'tools/fixtures/', 'tools/mask_patterns.json', 'tools/test_dump_nodes.py'); hits = []; n = 0
for d, _, fs in os.walk(R):
    for f in fs:
        p = os.path.join(d, f); rel = os.path.relpath(p, R).replace(os.sep, '/')
        if rel.startswith(skip) or rel.startswith('.git'): continue
        try: t = open(p, encoding='utf-8').read()
        except Exception: continue
        n += 1
        for i, l in enumerate(t.splitlines(), 1):
            if any(r.search(l) for r in vals): hits.append(f'{rel}:{i} pattern')
            for tok in re.split(r'[\s"\'`|,;()\[\]{}<>=:]+', l):
                if whole.fullmatch(tok) and not any(a.fullmatch(tok) for a in allow) and not ident.fullmatch(tok): hits.append(f'{rel}:{i} token-like (length {len(tok)})')
print(f'FAIL {len(hits)} hits: ' + '; '.join(hits[:20]) if hits else f'PASS 0 hits in {n} files'); sys.exit(1 if hits else 0)
