import ast,os,sys
t=ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read())
words=None
for n in ast.walk(t):
    if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='BANNED' for x in n.targets):
        words=[e.value for e in n.value.elts]
print('banned entries:',len(words))
root='/home/user/hadavin-sdk/handover/core-hardening/steps-edits'
tot=0
for dp,dn,fn in os.walk(root):
    for f in fn:
        p=os.path.join(dp,f)
        try: s=open(p,encoding='utf-8',errors='replace').read().lower()
        except Exception: continue
        c=sum(s.count(w.lower()) for w in words)
        if c: tot+=c; print('HITS',c,p)
print('total hits',tot)
