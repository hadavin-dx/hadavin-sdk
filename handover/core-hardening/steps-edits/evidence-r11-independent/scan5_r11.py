#!/usr/bin/env python3
"""List-only scan of Apply-now NEW texts. Prints hits, never judges."""
import re, sys
lines = open(sys.argv[1], encoding='utf-8').read().split('\n')
H = re.compile(r'^### (E-\d+): .*?, status (.+?), type ')
cur = None; st = None; inb = False; label = None; last = None; buf = []; blocks = []
for ln in lines:
    if not inb:
        m = H.match(ln)
        if m: cur, st = m.group(1), m.group(2); last = None; continue
        if ln == '~~~~': inb = True; label = last; buf = []; continue
        if ln.strip(): last = ln
    else:
        if ln == '~~~~':
            inb = False
            if cur and st.startswith('Apply now') and (label or '').startswith('NEW'): blocks.append((cur, '\n'.join(buf)))
        else: buf.append(ln)
print('Apply-now NEW blocks scanned:', len(blocks))
def sentences(t):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n', t) if s.strip()]
A = {
 'A1 model key + typed/pasted/entered into n8n (same sentence)': re.compile(r'(?i)(secret key for the model|model key|key for the model|model.{0,20}key|api key|anthropic).{0,160}(typ|paste|enter|put|save|store).{0,120}n8n|n8n.{0,120}(typ|paste|enter|put|save|store).{0,120}(secret key for the model|model key|key for the model|api key)'),
 'A2 fourth credential / four credentials / 4 credentials': re.compile(r'(?i)\b(fourth|4th|four|4)\b.{0,20}credential|credential.{0,20}\b(fourth|4th)\b'),
 'A3 "credentials" with a number word': re.compile(r'(?i)\b(three|3|two|2|five|5|six|6)\b.{0,12}credentials?'),
 'A4 n8n credential mentions with model key words': re.compile(r'(?i)credential.{0,100}(model|anthropic|claude)|(model|anthropic|claude).{0,100}credential'),
 'B1 delete / deletes / deleted / deletion': re.compile(r'(?i)\bdelet(e|es|ed|ing|ion)\b'),
 'B2 archive / archives / archived': re.compile(r'(?i)\barchiv(e|es|ed|ing)\b'),
 'B3 erase / purge / remove(s) with take or contact': re.compile(r'(?i)\b(erase[sd]?|purge[sd]?|wipe[sd]?)\b'),
}
counts = {}
for k, rx in A.items():
    n = 0
    for rid, body in blocks:
        for s in sentences(body):
            if rx.search(s):
                n += 1
                print('%s | %s | %s' % (k.split(' ')[0], rid, s[:300]))
    counts[k] = n
print('--- hit counts (sentences):')
for k, v in counts.items(): print(v, k)
