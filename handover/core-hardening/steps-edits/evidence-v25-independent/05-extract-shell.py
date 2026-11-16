import re,sys,subprocess,os
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
tot=0
for name in sys.argv[2:]:
    t=open(name,encoding='utf-8').read()
    spans=re.findall(r'```([a-zA-Z]*)\n(.*?)```',t,flags=re.S)
    print(name,'fenced blocks:',len(spans),'langs:',sorted(set(l for l,_ in spans)))
    for i,(lang,body) in enumerate(spans):
        p=os.path.join(out,'%s-%02d.%s.sh'%(os.path.basename(name)[:-3],i,lang or 'none'))
        open(p,'w').write(body)
        r=subprocess.run(['bash','-n',p],capture_output=True,text=True)
        print(' ',os.path.basename(p),'lines',body.count('\n'),'bash -n exit',r.returncode,r.stderr.strip()[:200])
        tot+=1
print('total spans',tot)
