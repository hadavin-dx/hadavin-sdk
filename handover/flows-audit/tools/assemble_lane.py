"""Assemble a lane file mechanically so machine columns are never retyped.
Run from repo root:  python3 handover/flows-audit/tools/assemble_lane.py <lane-name> <path-rel-handover/demo.json> [more paths...]
Reads  handover/flows-audit/lanes/<lane>.judge.jsonl   (one JSON object per line):
   {"file": "<path>", "row": <n>, "cells": [13 strings in the section-4 judgement order]}
   {"file": "<path>", "row": <n>, "same_as": "<text put in every judgement cell>"}
 and optional handover/flows-audit/lanes/<lane>.header.md (put first: inputs, absent files, notes).
Writes handover/flows-audit/lanes/<lane>.md = header + skeleton table per file with TODO replaced by the given cells.
Rows without an entry stay TODO; the script prints how many TODO rows remain per file. A cell may not contain a newline; '|' is escaped."""
import json, os, re, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)); LANES = os.path.join(H, '..', 'lanes'); DEMO = os.path.join(H, '..', '..', 'demo')
lane, files = sys.argv[1], sys.argv[2:]
J = {}
jp = os.path.join(LANES, lane + '.judge.jsonl')
if os.path.exists(jp):
    for n, l in enumerate(open(jp, encoding='utf-8'), 1):
        if not l.strip(): continue
        o = json.loads(l)
        cells = [o['same_as']] * 13 if 'same_as' in o else o['cells']
        assert len(cells) == 13, f'{jp}:{n} needs exactly 13 cells, has {len(cells)}'
        J[(o['file'], int(o['row']))] = [str(c).replace('\n', ' ').replace('|', '\\|') for c in cells]
out = []
hp = os.path.join(LANES, lane + '.header.md')
if os.path.exists(hp): out.append(open(hp, encoding='utf-8').read().rstrip() + '\n')
todo_total = 0
for f in files:
    t = subprocess.run([sys.executable, os.path.join(H, 'dump_nodes.py'), 'skeleton', f], capture_output=True, text=True, cwd=DEMO, check=True).stdout.splitlines()
    todo = 0
    for l in t:
        m = re.match(r'\| (\d+) \|', l)
        if m and l.endswith(' TODO |' * 13):
            c = J.get((f, int(m.group(1))))
            if c: l = l[:-len(' TODO |' * 13)] + ''.join(f' {x} |' for x in c)
            else: todo += 1
        out.append(l)
    out.append(f'<!-- {f}: {todo} rows still TODO -->'); out.append('')
    print(f'{f}: {todo} TODO'); todo_total += todo
open(os.path.join(LANES, lane + '.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('TOTAL TODO', todo_total)
