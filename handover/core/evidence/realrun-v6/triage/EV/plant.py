import json,sys,hashlib,subprocess,os,shutil
RR='/home/user/build/rr6'; T=RR+'/tree-EV2'; O=RR+'/out/EV'
names=sys.argv[1].split('+'); log=sys.argv[2]
muts={}
for f in ('r','k'):
    for n,fl,old,new in json.load(open(f'{RR}/src-v6/drivers/mutants/muts-{f}.json')):
        muts[n.split()[0] if False else n]=(fl,old,new)
# names given like R20,K6 -> match by prefix
def find(k):
    c=[v for n,v in muts.items() if n.split()[0]==k]; assert len(c)==1,k; return c[0]
saved={}
try:
    for k in names:
        fl,old,new=find(k); p=f'{T}/{fl}'
        if fl not in saved: saved[fl]=open(p,'rb').read()
        s=open(p,encoding='utf-8').read(); assert s.count(old)==1,(k,s.count(old))
        open(p,'w',encoding='utf-8').write(s.replace(old,new,1))
    env=dict(os.environ,TMPDIR=T+'/.tmp-run',PYTHONPATH=T+'/src')
    os.makedirs(T+'/.tmp-run',exist_ok=True)
    r=subprocess.run([RR+'/venv312/bin/python','-m','pytest','-q','-p','no:cacheprovider','-rfs','tests/test_survivor_r20_config_read.py','tests/test_survivor_keep_scan.py'],cwd=T,env=env,capture_output=True,text=True)
    open(log,'w').write(r.stdout+r.stderr)
finally:
    for fl,b in saved.items():
        open(f'{T}/{fl}','wb').write(b); print(fl,hashlib.sha256(b).hexdigest()==hashlib.sha256(open(f'{T}/{fl}','rb').read()).hexdigest())
