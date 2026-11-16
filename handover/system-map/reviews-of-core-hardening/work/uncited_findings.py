import re,sys
L=open(sys.argv[1],encoding='utf-8').read().split('\n')
cite=re.compile(r'[\w./-]+\.(?:py|md|sql|yml|yaml|json|toml|sh):\d+')
hd=re.compile(r'^\*\*([A-Z]\d?-\d+) \| (Blocker|Major|Nit)')
row=re.compile(r'^([A-Z]\d?-\d+) \| (Blocker|Major|Nit) \|')
blocks=[];cur=None
for l in L:
    m=hd.match(l) or row.match(l)
    if m:
        cur=[m.group(1),m.group(2),l];blocks.append(cur)
        if row.match(l): cur=None
        continue
    if cur is not None:
        if l.startswith('## ') or l.startswith('### '): cur=None
        else: cur[2]+='\n'+l
no=[b[0] for b in blocks if not cite.search(b[2])]
print(len(blocks),len(no),no)
