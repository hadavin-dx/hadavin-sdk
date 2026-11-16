import ast,re,glob,os
D='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
t=ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read())
words=[]
for n in ast.walk(t):
    if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='BANNED' for x in n.targets):
        words=[e.value for e in n.value.elts]
print('banned list length read at run time:',len(words))
names=[f for f in os.listdir(D) if '33' in f and f.endswith(('.md','.py','.txt')) and not os.path.isdir(D+f)]+['LEAD-RELEASE-NOTE-v17.md','LEAD-RELEASE-NOTE-v17-SOURCE.md']
tot=0
for f in sorted(set(names)):
    s=open(D+f,encoding='utf-8').read().lower()
    c=sum(s.count(w.lower()) for w in words if w)
    if c: print('  banned hits',f,c)
    tot+=c
print('files scanned',len(set(names)),'banned hits total',tot)
# secret shaped
pat=[r'AKIA[0-9A-Z]{16}',r'ASIA[0-9A-Z]{16}',r'sk-[A-Za-z0-9_-]{20,}',r'ghp_[A-Za-z0-9]{20,}',r'github_pat_\w{20,}',r'xox[bap]-[\w-]{10,}',r'-----BEGIN [A-Z ]*PRIVATE KEY',r'AIza[0-9A-Za-z_-]{30,}',r'pat-[a-z]{2,3}\d?-[0-9a-f-]{20,}',r'\b[0-9a-f]{40,}\b',r'eyJ[A-Za-z0-9_-]{15,}\.']
hits=0
for f in sorted(set(names)):
    s=open(D+f,encoding='utf-8').read()
    for p in pat:
        for m in re.finditer(p,s):
            if m.group(0)=='AKIAIOSFODNN7EXAMPLE': continue
            hits+=1; print('  secret-shaped',f,p[:20],len(m.group(0)))
print('secret-shaped hits (excluding AKIAIOSFODNN7EXAMPLE):',hits)
print('AKIAIOSFODNN7EXAMPLE occurrences:',sum(open(D+f,encoding='utf-8').read().count('AKIAIOSFODNN7EXAMPLE') for f in set(names)))
