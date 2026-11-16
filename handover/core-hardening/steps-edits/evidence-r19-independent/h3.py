import os,subprocess,sys
SE=os.path.abspath('treeB/root/core-hardening/steps-edits')+'/'
P=open(SE+'r19-pins.txt',encoding='utf-8').read()
L=P.split('\n')
i=[k for k,l in enumerate(L) if 'no more takes' in l and l.startswith('3\t')][0] if any('no more takes' in l and l.startswith('3\t') for l in L) else 5
cases={'p1-delete-one-pin-row':'\n'.join(L[:i]+L[i+1:]),'p2-count-3-to-4':'\n'.join(L[:i]+[L[i].replace(L[i].split('\t')[0],'9',1)]+L[i+1:]),'p3-empty-pin-file':''}
for n,v in cases.items():
    try:
        open(SE+'r19-pins.txt','w',encoding='utf-8').write(v)
        env=dict(os.environ,NO_NEG='1')
        o=subprocess.run([sys.executable,'-I',SE+'verify19.py'],env=env,capture_output=True,text=True,cwd=SE).stdout
    finally: open(SE+'r19-pins.txt','w',encoding='utf-8').write(P)
    f=[l for l in o.split('\n') if l.startswith('FAIL ')]
    print(n,'FAIL lines',len(f),[x[:90] for x in f[:2]])
