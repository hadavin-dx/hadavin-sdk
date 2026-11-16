import re,sys,os,subprocess,json
BASE=sys.argv[1]; OUT=sys.argv[2]; VER=sys.argv[3]
t0=open(BASE,encoding='utf-8').read()
def rep(a,b,count=0): return ('rep',a,b,count)
M=[]  # (id, category, kind, spec)
def add(i,cat,fn): M.append((i,cat,fn))
def R(a,b,n=0):
    def f(t):
        if a not in t: return None
        return t.replace(a,b) if n==0 else t.replace(a,b,n)
    return f
def rx(p,b,flags=0,n=0):
    def f(t):
        if not re.search(p,t,flags): return None
        return re.sub(p,b,t,count=n,flags=flags)
    return f
em='jane.doe'+chr(64)+'mail'+chr(46)+'example'+chr(46)+'org'
ak='AK'+'IA'+'ZXCVBNMASDFGHJKL'

def cell(prefix,idx,new,occ=1):
    def f(t):
        L=t.split('\n'); n=0
        for k,l in enumerate(L):
            if l.startswith(prefix):
                c=l.split(' | '); 
                if idx>=len(c): continue
                c[idx]=new; L[k]=' | '.join(c); n+=1
                if n==occ: break
        return '\n'.join(L) if n else None
    return f
def line(prefix,a,b):
    def f(t):
        L=t.split('\n')
        for k,l in enumerate(L):
            if l.startswith(prefix) and a in l:
                L[k]=l.replace(a,b); return '\n'.join(L)
        return None
    return f
add('B01','default-rev',R('I do not approve it.','I approve it.'))
add('B02','default-rev',R('G12 OPEN','G12 CLOSED'))
add('B03','default-rev',R('NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE.','Row 1 to row 30 have been applied.'))
add('B04','count',R('we did not measure for how long','we did not measure for how long at all in any of the runs'))
add('B05','count',line('| 14 | NOT APPLIED','it sends an alert, a warning mail that asks a person to look','it sends an alert, a warning mail that asks a person to look at it straight away'))
add('B06','default-rev',R('no delete call','a delete call'))
add('B07','default-rev',R("archive_contacts 'no'","archive_contacts 'yes'"))
add('B08','default-rev',R('You delete only made-up contacts of this run','You delete any contacts of any run'))
add('B09','default-rev',cell('| L-CARDCUT (was Q1, part 2)',3,'No, keep them.'))
add('B10','default-rev',cell('| L-APPROX (was L-ROUND)',3,'Yes, say about a minute.'))
add('B11','default-rev',cell('| L-PAGE',3,'Yes, both go on the page.'))
add('B12','default-rev',cell('| L-ONEDB',3,'Yes, say it.'))
add('B13','default-rev',cell('| L-SAVEERR',3,'Yes, failed runs are saved.'))
add('B14','default-rev',cell('| L-DEL (ANSWERED',3,'Yes, the take deletes contacts.'))
add('B15','default-rev',cell('| L-POST (new in c6q)',3,'No, they do not count as public.'))
add('B16','default-rev',cell('| L-CUT',3,'Yes, mark them.'))
add('B17','default-rev',cell('| L-CARD (was Q1, part 1)',3,'No, it is cut.'))
add('B18','default-rev',cell('| L-LEASE',3,'1. The 25-word sentence goes on the card.'))
add('B19','default-rev',cell('| L-KILL (was Q2)',3,'(b) yes, say it.'))
add('B20','default-rev',cell('| L-LEASE',4,'Yes'))
add('B21','status',rx(r'^(\| 6[0-9] \| NOT APPLIED; )waits for the answer of L-SAVEERR \(default no\)',r'ready',re.M,1))
add('B22','count',R('twelve numbered TASKS','ten numbered TASKS'))
add('B23','time',R('IST = UTC + 5:30','IST = UTC + 5:00'))
add('B24','time',R('2026-11-16T18:40:00Z = 2026-11-17T00:10:00 IST','2026-11-16T18:40:00Z = 2026-11-16T23:40:00 IST'))
add('B25','time',R('Mon 23 Nov','Tue 23 Nov',1))
add('B26','time',R('18:04 UTC = 23:34 IST','18:04 UTC = 23:35 IST',1))
add('B27','time',R('18:29 UTC = 23:59 IST','18:29 UTC = 23:58 IST',1))
add('B28','status',R('the exact command of the test program is not in the audited files: UNVERIFIED','the exact command of the test program is not in the audited files: verified'))
add('B29','status',rx(r'(\| (?:ASSUMPTION[^|]*|[^|]*UNVERIFIED[^|]*) \|)$',lambda m:m.group(0).replace('UNVERIFIED','VERIFIED'),re.M))
#add('B30','shape',lambda t: t.replace('WHAT TO TYPE','Send questions to '+em+'. WHAT TO TYPE',1) if False else None)
add('B31','count',lambda t: t.replace(' STUDIO LEAD = you',' '+' '.join(['word']*20)+' STUDIO LEAD = you',1))
add('B32','count',R(' NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE.','',1))
add('B33','count',R('The two OPEN questions','The three OPEN questions',1))
add('B34','default-rev',R('lease sentence stays out of the public post','lease sentence goes into the public post'))
add('B35','delete',R('G12 holds every lease word a viewer would see','G12 holds nothing'))
add('B36','count',R('(49: applicable now)','(50: applicable now)'))
add('B37','count',R('(38: applied unless you answer a question differently)','(37: applied unless you answer a question differently)'))
add('B38','default-rev',R('(1: the 25-word limit sentence of your earlier answer;','(1: the 25-word limit sentence of your earlier answer, in force;'))
add('B39','default-rev',R('| ANSWERED by you','| ANSWERED by you'))
add('B40','time',R('| 40 s EST','| 30 s EST',1))

add('B41','shape',lambda t: t.replace('WHAT TO TYPE','Send questions to '+em+'. WHAT TO TYPE',1))
add('B42','shape',lambda t: t.replace('WHAT TO TYPE','Key '+ak+' WHAT TO TYPE',1))
add('B43','shape',lambda t: t.replace('| L-CARD | Does','| L-CARD '+em+' | Does',1))
env=dict(os.environ)
os.makedirs(OUT,exist_ok=True)
res=[]
for i,cat,fn in M:
    t=fn(t0)
    if t is None or t==t0:
        res.append((i,cat,'NOT-APPLIED','','')); continue
    p=os.path.join(OUT,i+'.md'); open(p,'w',encoding='utf-8').write(t)
    r=subprocess.run(['python3','-B','-I',VER,p],capture_output=True,text=True,env=env)
    out=r.stdout.strip().split('\n')
    summ=[l for l in out if l.startswith('SUMMARY')]
    s=summ[-1] if summ else (out[-1] if out else r.stderr[-200:])
    m=re.match(r'SUMMARY: (\d+) checks, (\d+) FAILED',s)
    nf=int(m.group(2)) if m else -1
    res.append((i,cat,'CAUGHT' if (r.returncode!=0) else 'MISSED',str(r.returncode)+' f='+str(nf), s[:150] ))
for r in res: print('\t'.join(r))
json.dump(res,open(OUT+'/results.json','w'))
