import re,sys,os
R='/home/user/hadavin-sdk'
A=R+'/handover/core-hardening/audit-r460/'
cands=['src/hadavin_sdk/','tests/','demos/','','.github/']
def resolve(p):
    if os.path.isfile(os.path.join(R,p)): return p
    for pre in ['src/hadavin_sdk/','demos/ask-your-data/askdata/','tests/','demos/ask-your-data/','src/hadavin_sdk/llm/','src/hadavin_sdk/store/','src/hadavin_sdk/guard/']:
        if os.path.isfile(os.path.join(R,pre+p)): return pre+p
    return None
pat=re.compile(r'([\w./-]+\.(?:py|sql|yaml|yml|md))?(:\d+(?:-\d+)?(?:,:\d+(?:-\d+)?)*|(?<=\.py):\d+)')
out=[]
for f in sys.argv[1:]:
    cur=None
    for n,line in enumerate(open(A+f,encoding='utf-8'),1):
        for m in re.finditer(r'(?:`([\w./-]+\.(?:py|sql|ya?ml|md))(:\d+(?:-\d+)?)`)|(?:`(:\d+(?:-\d+)?)`)|([\w./-]+\.(?:py|sql|ya?ml)):(\d+(?:-\d+)?)',line):
            if m.group(1): cur=m.group(1); rng=m.group(2)[1:]
            elif m.group(4): cur=m.group(4); rng=m.group(5)
            else: rng=m.group(3)[1:]
            out.append((f,n,cur,rng,line.strip()[:0]))
import json
json.dump(out,open(sys.argv[0]+'.json','w'))
print(len(out))
