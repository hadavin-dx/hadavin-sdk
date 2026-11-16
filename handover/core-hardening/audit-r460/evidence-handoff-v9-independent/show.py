import json,os,re,sys
R='/home/user/hadavin-sdk'
A=R+'/handover/core-hardening/audit-r460/'
cites=json.load(open('/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/extract_cites.py.json'))
def resolve(p):
    for pre in ['','src/hadavin_sdk/','demos/ask-your-data/askdata/','tests/','src/hadavin_sdk/llm/','src/hadavin_sdk/approvals/','src/hadavin_sdk/runtime/','src/hadavin_sdk/store/migrations/','src/hadavin_sdk/k1b/','src/hadavin_sdk/store/','src/hadavin_sdk/guard/','src/hadavin_sdk/audit/','src/hadavin_sdk/actions/','src/hadavin_sdk/backends/','.github/workflows/']:
        if os.path.isfile(os.path.join(R,pre+p)): return pre+p
    return None
docs={}
for i,(f,n,cur,rng,_) in enumerate(cites):
    docs.setdefault(f,open(A+f,encoding='utf-8').read().split('\n'))
    rp=resolve(cur) if cur else None
    a=rng.split('-'); s=int(a[0]); e=int(a[-1])
    ctx=docs[f][n-1]
    k=ctx.find(cur+':'+rng) if cur else -1
    c=ctx[max(0,k-90):k+len(str(cur))+len(rng)+3] if k>=0 else ctx[:160]
    print(f'#{i} {f[-14:-3]}:{n} {cur}:{rng} -> {rp}')
    print('   DOC: '+c.replace('\n',' '))
    if not rp: print('   UNRESOLVED'); continue
    L=open(R+'/'+rp,encoding='utf-8').read().split('\n')
    if s>len(L): print(f'   BEYOND EOF ({len(L)} lines)'); continue
    for j in range(s,min(e,s+2)+1): print(f'   {j}: {L[j-1].strip()[:150]}')
    if e>s+2: print(f'   ... {e}: {L[min(e,len(L))-1].strip()[:100]}')
