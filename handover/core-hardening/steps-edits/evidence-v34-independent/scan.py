import ast,re,sys,glob,os
D=sys.argv[1]
t=ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py').read())
B=[]
for n in ast.walk(t):
    if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='BANNED' for x in n.targets):
        B=[e.value for e in n.value.elts if isinstance(e,ast.Constant)]
print('banned terms loaded:',len(B))
files=[f for f in glob.glob(D+'/*') if os.path.isfile(f) and re.search(r'v34|LEAD-RELEASE-NOTE-v18',os.path.basename(f))]
tot=0
for f in sorted(files):
    s=open(f,encoding='utf-8',errors='replace').read().lower()
    c=sum(s.count(b.lower()) for b in B)
    if c: print('BANNED hits',os.path.basename(f),c)
    tot+=c
print('files scanned',len(files),'banned total',tot)
pats={'aws_akia':r'AKIA[0-9A-Z]{16}','github':r'gh[pousr]_[A-Za-z0-9]{36}','sk':r'sk-[A-Za-z0-9]{20,}','slack':r'xox[baprs]-[A-Za-z0-9-]{10,}','privkey':r'-----BEGIN [A-Z ]*PRIVATE KEY','jwt':r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.','email':r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}','acct12':r'(?<!\d)\d{12}(?!\d)','longhex40':r'\b[0-9a-f]{40,}\b','b64long':r'[A-Za-z0-9+/]{40,}={0,2}'}
for k,p in pats.items():
    c=0;cs=0
    for f in files:
        for m in re.findall(p,open(f,encoding='utf-8',errors='replace').read()):
            if k=='aws_akia' and m=='AKIAIOSFODNN7EXAMPLE': cs+=1; continue
            c+=1
    print('secret-shape',k,'count',c,'(allowed example literal',cs,')')
