import ast,glob
n=0;fs=set();names=[]
for p in glob.glob('/home/user/hadavin-sdk/tests/**/*.py',recursive=True):
    t=ast.parse(open(p,encoding='utf-8').read())
    for c in ast.walk(t):
        if isinstance(c,ast.ClassDef) and any(isinstance(b,(ast.FunctionDef,ast.AsyncFunctionDef)) and b.name=='chat' for b in c.body):
            n+=1;fs.add(p);names.append(p.split('/tests/')[1]+':'+c.name)
print('classes defining chat in tests/**:',n,'files:',len(fs)); print(names)
