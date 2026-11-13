import re,random,sys
sys.path.insert(0,'src'); sys.path.insert(0,'tools'); sys.path.insert(0,'scripts')
from lead_desk.identity import PLAIN_ADDRESS as PN,_EMAIL_RE as EN
from scrub_n8n_export import MAIL as MN
import importlib.util
spec=importlib.util.spec_from_file_location('rrc','scripts/run_real_check.py')
AO=re.compile(r"[^\s,;:<>\"']+@[^\s,;<>\"']+")
PO=re.compile(r'^[^\s<>\r\n\x00,;"()]+@[^\s<>\r\n\x00,;"()]+$')
EO=re.compile(r"[^@\s<>\",;]+@[^@\s<>\"',;]+\.[^@\s<>\"',;]+")
MO=re.compile(r"(?<![\w.%+-])[\w.%+-]+[@＠](?!(?:[\w-]+\.)*example\.(?:com|test|invalid)(?![\w-]|\.[\w-]))[\w.-]+")
src=open('scripts/run_real_check.py').read()
an=re.search(r'^_ADDRESS = re\.compile\((.*)\)$',src,re.M).group(1); AN=re.compile(eval(an))
random.seed(7)
al=['a','b','.','@','@','@',' ',',',';',':','<','>','"',"'",'(',')','\n','\x00','-','_','%','+','＠','é','1']
mt=['example.','com','test','invalid','example.com','.','@','a','-','x','＠',' ','_']
bad=0
def chk(name,o,n,f,s):
    global bad
    a,b=f(o,s),f(n,s)
    if a!=b:
        bad+=1
        if bad<15: print('DIFF',name,repr(s),a,b)
N=int(sys.argv[1])
for _ in range(N):
    s=''.join(random.choice(al) for _ in range(random.randint(0,14)))
    chk('addr',AO,AN,lambda p,s:p.sub('<A>',s),s)
    chk('plain',PO,PN,lambda p,s:bool(p.fullmatch(s)),s)
    chk('email',EO,EN,lambda p,s:bool(p.fullmatch(s)),s)
    s2=''.join(random.choice(mt) for _ in range(random.randint(0,10)))
    chk('mail',MO,MN,lambda p,s:p.sub('<M>',s),s2)
    s3='a@'+''.join(random.choice(mt) for _ in range(random.randint(0,8)))
    chk('mail2',MO,MN,lambda p,s:p.sub('<M>',s),s3)
    chk('mail3',MO,MN,lambda p,s:p.sub('<M>',s),''.join(random.choice(al+mt) for _ in range(random.randint(0,16))))
print('cases',N,'diffs',bad)
import itertools
bad=0;cnt=0;hit=[0,0,0,0]
for L in range(0,8):
    for t in itertools.product('a@. :\n',repeat=L):
        s=''.join(t)
        for i,(o,n,f) in enumerate(((AO,AN,lambda p,s:p.sub('<A>',s)),(PO,PN,lambda p,s:bool(p.fullmatch(s))),(EO,EN,lambda p,s:bool(p.fullmatch(s))))):
            a=f(o,s);b=f(n,s);cnt+=1
            if a!=b: bad+=1; print('EXH',i,repr(s),a,b)
            if a and a!=s.replace(s,'') : hit[i]+=1
for L in range(0,9):
    for t in itertools.product(['a','.','@','-','example.','com',' '],repeat=min(L,6)):
        s=''.join(t); a=MO.sub('<M>',s);b=MN.sub('<M>',s); cnt+=1
        if a!=b: bad+=1; print('EXH mail',repr(s),a,b)
print('exhaustive',cnt,'diffs',bad,'nontrivial',hit)
