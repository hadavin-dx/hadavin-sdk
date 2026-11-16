import os, re, shutil, subprocess, sys, tempfile
W = os.path.dirname(os.path.abspath(__file__)) + '/work/'
FILES = ['facts-v24.py','build-v24.py','check-v24.py','OWNER-SHEET-v24-SOURCE.md','LEAD-RELEASE-NOTE-v8-SOURCE.md','v24-OPEN-FOR-LEAD-SOURCE.md','v24-CHANGES.md','pointers-v24.txt']
S='OWNER-SHEET-v24-SOURCE.md'; N='LEAD-RELEASE-NOTE-v8-SOURCE.md'; O='v24-OPEN-FOR-LEAD-SOURCE.md'; Fa='facts-v24.py'
SECRET = 'sk' + '-' + 'ab12' * 10          # built from parts, never a real key
P = [
('Q01',S,'= {{price}}; call ceiling x','= 0.28; call ceiling x','wrong price per call hardcoded'),
('Q02',S,'here {{ceil}} x {{price}} = {{total}}','here {{ceil}} x {{price}} = 0.84','wrong total hardcoded'),
('Q03',S,'Tokens in and out per call: {{tok_in}} and {{tok_out}}','Tokens in and out per call: {{tok_in}} and 12,000','wrong output tokens in sample'),
('Q04',S,'Alarm time: {{lf}}','Alarm time: 12:00 UTC = 17:00 IST','wrong IST pair'),
('Q05',S,'**Deadline** = {{dl_day}} {{dl}}','**Deadline** = Mon 23 Nov 2026 18:29 UTC = 23:49 IST','wrong deadline IST pair'),
('Q06',S,'see the card (7.3)','see the card (7.2)','pointer to wrong step'),
('Q07',S,'"go" (5.8)','"go" (5.7)','pointer to wrong step in R8'),
('Q08',S,'(1) if a key is alive, do the card now; (2) then FREEZE','(2) then FREEZE','STOP RULE step deleted (key alive: card)'),
('Q09',S,'you typed `end` (do not wait','you typed `end (do not wait','stray backtick'),
('Q10',S,'press the cancel button; if a box asks, press the confirmation word','press the cancel button; if a box asks, press close','cancel rule changed'),
('Q11',S,'(f) the test terminal shows a prompt (a line like `name@computer:~$`) before you typed `end`; ','','card gate (f) deleted'),
('Q12',S,'with auto-reload off and a balance at least the expected total','with auto-reload on and a balance at least the expected total','auto-reload rule flipped in R4'),
('Q13',S,'`Type y to start`.','`Type y to start`. Key: ' + SECRET,'secret-shaped string (built from parts) in sheet'),
('Q14',Fa,'BALANCE_C = 18900','BALANCE_C = 18090','balance changed'),
('Q15',S,'Give-up minutes: 40','Give-up minutes: 30','give-up minutes sample changed'),
('Q16',S,'Silence minutes: 3','Silence minutes: 5','silence minutes sample changed'),
('Q17',S,'B submitted 10 times','B submitted 9 times','expected count changed'),
('Q18',S,'Contacts: those in the clean-up message (addresses ending `@example.com`','Contacts: those in the clean-up message (addresses ending `@example.org`','delete domain guard changed (one copy)'),
('Q19',S,'back on in 8.7','back on in 8.6','pointer wrong in R1'),
('Q20',N,'program limit = 12.40 + 0.81 = 13.21','program limit = 12.40 + 0.81 = 13.12','lead note limit wrong'),
('Q21',N,'default 860 s = 14.33 minutes','default 860 s = 14.30 minutes','lead note minutes wrong'),
('Q22',S,'Exit codes accepted: 0 only','Exit codes accepted: 0 or 1','accepted exit codes widened'),
('Q23',S,'the card first, then R1, then R10, then the rest','the card first, then R10, then R1, then the rest','rule priority order swapped'),
('Q24',S,'Only five words in a lead message','Only four words in a lead message','word count in R8'),
('Q25',N,'default lease 860 s gives 18:14:40 UTC = 23:44:40','default lease 860 s gives 18:14:40 UTC = 23:14:40','lead note last start IST wrong'),
]
def run(d):
    subprocess.run([sys.executable,'-B',d+'build-v24.py',d],capture_output=True)
    r=subprocess.run([sys.executable,'-B',d+'check-v24.py'],capture_output=True,text=True,env=dict(os.environ,V24_DIR=d))
    return [l for l in r.stdout.split('\n') if l.startswith('FAIL') or 'FAIL' in l[:6]], r
c=m=nf=0
for pid,f,old,new,what in P:
    d=tempfile.mkdtemp(prefix='own25_')+'/'
    for x in os.listdir(W):
        if os.path.isfile(W+x): shutil.copy(W+x,d+x)
    t=open(d+f,encoding='utf-8').read()
    if t.count(old)<1: print(pid,'ANCHOR-NOT-FOUND',what); nf+=1; shutil.rmtree(d); continue
    open(d+f,'w',encoding='utf-8').write(t.replace(old,new,1))
    fl,r=run(d)
    built=''.join(open(d+x,encoding='utf-8').read() for x in os.listdir(d) if x.startswith(('OWNER-SHEET-v24-A','OWNER-SHEET-v24-B','LEAD-RELEASE-NOTE-v8.md','v24-OPEN-FOR-LEAD.md')))
    probe=re.sub(r'\{\{\w+\}\}','',new)[:25]
    print('   [in-built-output: %s]'%(probe in built or f==Fa))
    if r.returncode!=0 or fl: c+=1; print(pid,'CAUGHT',what,'| rc=%d |'%r.returncode,(fl[0] if fl else r.stdout.strip().split('\n')[-1])[:150])
    else: m+=1; print(pid,'MISSED',what)
    shutil.rmtree(d)
print('TOTAL own plants %d: caught %d, missed %d, anchor-not-found %d'%(len(P),c,m,nf))
