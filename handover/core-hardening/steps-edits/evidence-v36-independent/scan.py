import ast,glob,re
tree=ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read())
words=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='BANNED' for x in n.targets): words=[str(x) for x in ast.literal_eval(n.value)]
print('banned list size',len(words))
files=sorted(set(glob.glob('*v36*')+glob.glob('LEAD-RELEASE-NOTE-v20*.md')))
files=[f for f in files if f.endswith(('.md','.txt','.py'))]
SEC=[('aws-key',r'\b(AKIA|ASIA)[0-9A-Z]{16}\b'),('sk-key',r'\bsk-[A-Za-z0-9_\-]{20,}'),('ghp',r'\bgh[pousr]_[A-Za-z0-9]{30,}'),('slack',r'\bxox[abprs]-[A-Za-z0-9\-]{10,}'),
     ('pem',r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),('jwt',r'\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.'),('long-hex40+',r'\b[0-9a-fA-F]{40,}\b'),('long-b64-40+',r'\b[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9])'),
     ('email',r'\b[\w.+-]+@(?!example\.com\b)[\w-]+\.[\w.]+\b'),('assign-secret',r'(?i)\b(password|secret|token|api[_-]?key)\s*[=:]\s*["\']?[A-Za-z0-9/+_\-]{12,}'),('acct-12digit',r'(?<![\d.:-])\d{12}(?![\d.:-])')]
bt={};st={}
for f in files:
    t=open(f,encoding='utf-8').read().lower()
    c=sum(t.count(w.lower()) for w in words)
    if c: bt[f]=c
    tt=open(f,encoding='utf-8').read()
    for k,p in SEC:
        m=len(re.findall(p,tt))
        if m: st[(k,f)]=m
print('files scanned',len(files))
print('banned-word hits: files',len(bt),'total',sum(bt.values()))
for f,c in bt.items(): print('  BANNED',f,c)
print('secret-shaped hits (pattern,file,count):')
for (k,f),c in sorted(st.items()): print('  ',k,f,c)
print('literal AKIAIOSFODNN7EXAMPLE count',sum(open(f,encoding='utf-8').read().count('AKIAIOSFODNN7EXAMPLE') for f in files))
