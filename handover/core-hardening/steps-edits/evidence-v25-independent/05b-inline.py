import re,sys,subprocess,os,tempfile
for name in sys.argv[1:]:
    t=open(name,encoding='utf-8').read()
    t=re.sub(r'```.*?```','',t,flags=re.S)
    spans=re.findall(r'`([^`\n]+)`',t)
    u=sorted(set(spans)); bad=0
    print(name,'inline spans',len(spans),'unique',len(u))
    for s in u:
        r=subprocess.run(['bash','-n','-c',s],capture_output=True,text=True)
        if r.returncode!=0:
            bad+=1; print('  SYNTAX-FAIL exit',r.returncode,'|',s[:150],'|',r.stderr.strip()[:100])
    print(' unique spans failing bash -n:',bad)
