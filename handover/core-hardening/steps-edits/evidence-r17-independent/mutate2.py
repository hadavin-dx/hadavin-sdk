import re,os,subprocess,sys,importlib.util
spec=importlib.util.spec_from_file_location('m',os.path.dirname(os.path.abspath(__file__))+'/mutate.py')
src_text=open(os.path.dirname(os.path.abspath(__file__))+'/mutate.py').read().split("os.makedirs(EV+'/mut'")[0]
ns={'__file__':os.path.abspath('mutate.py')}
exec(src_text,ns)
MUT=ns['MUT'];src=ns['src'];M=ns['M'];EV=ns['EV']
lines=src.split('\n')
# fence map by char offset
infence=[];pos=0;inb=False
for ln in lines:
    if ln=='~~~~': inb=not inb
    infence.append(inb and ln!='~~~~'); pos+=len(ln)+1
starts=[];p=0
for ln in lines: starts.append(p); p+=len(ln)+1
import bisect
def fenced(off):
    return infence[bisect.bisect_right(starts,off)-1]
missed=sys.argv[1:]
for name,kind,old,new in MUT:
    if not any(name.startswith(s) for s in missed): continue
    offs=[m.start() for m in re.finditer(re.escape(old),src)]
    res=[]
    for o in offs:
        mut=src[:o]+new+src[o+len(old):]
        mp=EV+'/mut/'+name+'-occ.md'; open(mp,'w',encoding='utf-8').write(mut)
        env=dict(os.environ,EDITS_PATH=mp,NO_NEG='1')
        out=subprocess.run([sys.executable,'-I',M+'/verify17.py'],env=env,capture_output=True,text=True,cwd=M).stdout
        c=any(l.startswith('FAIL ') for l in out.split('\n'))
        res.append((fenced(o),c))
    f=[r for r in res if r[0]]; nf=[r for r in res if not r[0]]
    print(name,'occ',len(res),'| in NEW fences:',len(f),'caught',sum(c for _,c in f),'| outside fences (notes):',len(nf),'caught',sum(c for _,c in nf),flush=True)
