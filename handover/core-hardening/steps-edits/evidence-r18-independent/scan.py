import ast,re,os,sys
src=open('/home/user/hadavin-sdk/tests/test_no_reference_material.py',encoding='utf-8').read()
tree=ast.parse(src); B=None
for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='BANNED' for t in n.targets): B=ast.literal_eval(n.value)
print('BANNED entries',len(B))
base='h/core-hardening/steps-edits/'
fs=['EDITS.md','r18-OWNER-DAY-SHEET.md','r18-OWNER-APPENDIX-K.md','r18-CHANGES.md','scratch18/scratch-apply11/OWNER-STEPS-realrun-v3.md','scratch18/scratch-apply11/AGENT-SCOPE-DO-AND-DONT.md','scratch18/scratch-apply11/DECISION-one-store.md','scratch18/scratch-all11/OWNER-STEPS-realrun-v3.md']
shapes=[r'AKIA[0-9A-Z]{16}',r'sk-[A-Za-z0-9_\-]{20,}',r'ghp_[A-Za-z0-9]{30,}',r'gh[ousr]_[A-Za-z0-9]{30,}',r'xox[baprs]-[A-Za-z0-9\-]{10,}',r'-----BEGIN [A-Z ]*PRIVATE KEY',r'AIza[0-9A-Za-z_\-]{30,}',r'eyJ[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{10,}\.',r'[A-Za-z0-9+/]{40,}={0,2}',r'\b[0-9]{12}\b',r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}']
for f in fs:
    t=open(base+f,encoding='utf-8').read().lower()
    bc=sum(t.count(b.lower()) for b in B)
    tt=open(base+f,encoding='utf-8').read()
    print(f.split('/')[-1] if 'scratch' not in f else f[8:], 'banned hits',bc,'| key-shape counts',[len(re.findall(p,tt)) for p in shapes])
