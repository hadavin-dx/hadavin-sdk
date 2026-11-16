import ast,sys,pathlib
src=open('/home/user/hadavin-sdk/tests/test_no_reference_material.py').read()
tree=ast.parse(src)
words=None
for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='BANNED' for t in n.targets):
        words=[w for w in ast.literal_eval(n.value)]
print('banned entries:',len(words))
root=pathlib.Path(sys.argv[1]);tot=0;nf=0
for p in sorted(root.rglob('*')):
    if p.is_file() and p.suffix in('.md','.txt','.py'):
        t=p.read_text(errors='replace').lower();nf+=1
        c=sum(t.count(w.lower()) for w in words)
        tot+=c
        if c: print('HIT',p.name,c)
print('files scanned',nf,'total hits',tot)
