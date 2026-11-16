import re,os,ast,sys
root=sys.argv[1]
src=open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read()
tree=ast.parse(src);banned=None
for nd in ast.walk(tree):
    if isinstance(nd,ast.Assign) and any(getattr(x,'id',None)=='BANNED' for x in nd.targets):
        banned=[s for s in ast.literal_eval(nd.value)]
print('banned strings loaded',len(banned))
sec=[r'AKIA[0-9A-Z]{16}',r'sk-[A-Za-z0-9]{20,}',r'ghp_[A-Za-z0-9]{20,}',r'xox[bap]-[A-Za-z0-9-]{10,}',r'-----BEGIN [A-Z ]*PRIVATE KEY',r'(?i)password\s*[:=]\s*\S{6,}',r'AIza[0-9A-Za-z_-]{30,}',r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.',r'\b\d{12}\b']
mail=re.compile(r'[A-Za-z0-9._%+-]+@(?!example\.|\S*example)[A-Za-z0-9.-]+\.[a-z]{2,}')
bh={};sh={};mh={};files=0
for dp,dn,fn in os.walk(root):
    if 'evidence-r17-independent' in dp: continue
    for f in fn:
        p=os.path.join(dp,f)
        try:t=open(p,encoding='utf-8',errors='replace').read()
        except: continue
        files+=1
        lo=t.lower()
        c=sum(lo.count(b.lower()) for b in banned)
        if c: bh[p]=c
        c=0
        for s in sec: c+=len(re.findall(s,t))
        if c: sh[p]=c
        c=len(mail.findall(t))
        if c: mh[p]=c
print('files scanned',files)
print('banned-string hits (case-insens): files',len(bh),'total',sum(bh.values()))
print('secret-shape hits: files',len(sh),'total',sum(sh.values()))
for p,c in sorted(sh.items())[:15]: print('  secret-shape',os.path.relpath(p,root),c)
print('non-example email hits: files',len(mh),'total',sum(mh.values()))
for p,c in sorted(mh.items())[:10]: print('  email',os.path.relpath(p,root),c)
for p,c in sorted(bh.items())[:10]: print('  banned-in',os.path.relpath(p,root),c)
