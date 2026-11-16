import os,shutil,subprocess,sys,tempfile
H='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/evidence-v25-independent/frozen/'
SRC='OWNER-SHEET-v25-SOURCE.md'
KEY='sk'+'-ant-'+'api03-'+'ABCDEFGHIJ'+'KLMNOPQRSTUVWX'
def rep(old,new): return ('src',old,new)
P=[
('N01','wrong time zone offset label (IST = UTC + 4:30)',rep('**IST** = UTC + 5:30','**IST** = UTC + 4:30')),
('N02','swapped UTC/IST in post-by line',rep('(by {{postby}};','(by Wed 25 Nov 2026 20:30 UTC = 15:00 IST;')),
('N03','key-looking string added (built from parts)',rep('**STOP RULE.**','**STOP RULE.** '+KEY+' ')),
('N04','step number off by one (7.4 -> 7.5)',rep('if 7.4 never happened','if 7.5 never happened')),
('N05','"archived" turned into "deleted" in R5',rep('will be deleted or archived,','will be deleted or deleted,')),
('N06','STOP RULE paragraph removed',('line20',)),
('N07','A text left in B (built B file edited)',('builtB','the older key is cancelled at 6.2 before you make the model key')),
('N08','wrong dollar amount: expected total 0.84',rep('{{total}}','0.84')),
('N09','broken pointer (7.9 -> 7.19)',rep('an exit code (7.9)','an exit code (7.19)')),
('N10','warning removed before the cancel step',rep(' (else do not press Enter: do the card)','')),
('N11','changed date Wed 25 -> Thu 26 Nov (weekday consistent)',rep('(by {{postby}};','(by Thu 26 Nov 2026 15:00 UTC = 20:30 IST;')),
('N12','second person turned passive in R7',rep('You delete only made-up contacts of this run','Only made-up contacts of this run are deleted')),
('N13','extra non-example address (example.org lookalike)',rep('`take-<run name>-a@example.com`','`take-<run name>-a@example.org`')),
('N14','shortened command: date -u -> date',rep('Run `date -u` in the read terminal','Run `date` in the read terminal')),
('N15','word count pushed over 6500 (filler words added)',rep('**STOP RULE.**',' '.join(['padding']*60)+' **STOP RULE.**')),
]
def run(d):
    subprocess.run([sys.executable,'-B',d+'build-v25.py',d],capture_output=True)
    r=subprocess.run([sys.executable,'-B',d+'check-v25.py'],capture_output=True,text=True,env=dict(os.environ,V24_DIR=d))
    return r
base=set()
caught=0
for pid,desc,spec in P:
    d=tempfile.mkdtemp(prefix='pl-')+'/'
    for f in os.listdir(H): shutil.copy(H+f,d+f)
    kind=spec[0]
    if kind=='src':
        s=open(d+SRC,encoding='utf-8').read()
        n=s.count(spec[1])
        if n==0: print(pid,'ANCHOR-NOT-FOUND',desc); continue
        open(d+SRC,'w',encoding='utf-8').write(s.replace(spec[1],spec[2],1))
        r=run(d)
    elif kind=='line20':
        L=open(d+SRC,encoding='utf-8').read().split('\n')
        i=[k for k,l in enumerate(L) if l.startswith('**STOP RULE.**')]
        if not i: print(pid,'ANCHOR-NOT-FOUND'); continue
        del L[i[0]]; open(d+SRC,'w',encoding='utf-8').write('\n'.join(L)); r=run(d)
    elif kind=='builtB':
        # take the A wording and put it into the built B file in place of the B wording
        b=open(d+'OWNER-SHEET-v25-B.md',encoding='utf-8').read()
        a=open(d+'OWNER-SHEET-v25-A.md',encoding='utf-8').read()
        if spec[1] not in a or spec[1] in b: print(pid,'ANCHOR-NOT-USABLE',spec[1] in a,spec[1] in b); continue
        # replace the line of B that corresponds (find B-variant text in source)
        s=open(d+SRC,encoding='utf-8').read()
        i=s.find('[[B:'); 
        import re
        m=re.search(r'\[\[B:\s?(the older k.*?)\]\]',s,flags=re.S)
        if not m: print(pid,'NO B variant'); continue
        bt=m.group(1)
        if bt not in b: print(pid,'B text not in built B'); continue
        open(d+'OWNER-SHEET-v25-B.md','w',encoding='utf-8').write(b.replace(bt,spec[1],1))
        r=subprocess.run([sys.executable,'-B',d+'check-v25.py'],capture_output=True,text=True,env=dict(os.environ,V24_DIR=d))  # no rebuild: planted into built file
    fails=[l for l in r.stdout.split('\n') if l.startswith('FAIL')]
    status='CAUGHT' if fails else 'MISSED'
    caught+= bool(fails)
    print(pid,status,'|',desc,'|',(fails[0][:150] if fails else 'no FAIL line; exit %d'%r.returncode),'| nfails',len(fails))
    shutil.rmtree(d,ignore_errors=True)
print('TOTAL caught',caught,'of',len(P))
