"""Independent plants X01-X15 (evidence runner). Counts only; applies each to a scratch copy of the SOURCE files, rebuilds, runs check-v33.py."""
import os, re, shutil, subprocess, sys, tempfile
H = '/tmp/ev33/steps-edits/'; BP = '/tmp/ev33/tests/test_no_reference_material.py'
FILES = ['facts-v33.py','build-v33.py','check-v33.py','newchecks-v33.py','OWNER-SHEET-v33-SOURCE.md','LEAD-RELEASE-NOTE-v17-SOURCE.md','v33-OPEN-FOR-LEAD-SOURCE.md','v33-CHANGES.md','pointers-v33.txt','headings-v33.txt','factuse-v33.txt']
S,N,FA='OWNER-SHEET-v33-SOURCE.md','LEAD-RELEASE-NOTE-v17-SOURCE.md','facts-v33.py'
P=[
('X01',S,'at least 168 hours (7 days) before','at least 24 hours (1 day) before','7-day rule shortened in the sheet'),
('X02',S,'a later use: use sheet B','a later use: use sheet A','A/B choice reversed'),
('X03',S,'auto-reload** = the account tops itself up when low (must be off)','auto-reload** = the account tops itself up when low (must be on)','auto-reload safe default reversed'),
('X04',S,'key revoked by {{rv23}} even if','key revoked by 18:29 UTC = 23:59 IST even if','cancel-by on 23 Nov moved to the deadline'),
('X05',S,'**Backstop time** = {{dl_day}} {{rv23}}: ten minutes before the deadline','**Backstop time** = {{dl_day}} {{dl}}: ten minutes before the deadline','backstop time set equal to the deadline'),
('X06',S,'You delete only made-up contacts of this run and demo mails, by hand, one by one.','You delete made-up contacts, demo mails and any other mail that looks like a demo mail, in bulk.','R7 delete rule widened'),
('X07',S,'search the exact address, see exactly one result whose page shows it, then delete','search the start of the address, then delete all results','contact delete widened to many results'),
('X08',S,'; if nobody answers within 10 more minutes, do the last-resort step yourself, only in the model account','','last-resort step after failed cancel removed (waiting chain)'),
('X09',S,'**Near the deadline you do not wait:** once a deadline reminder of 5.8 has rung, or after the deadline, do the last-resort step at once','**Near the deadline you do not wait:** once a deadline reminder of 5.8 has rung, or after the deadline, keep waiting','near-deadline last-resort replaced by waiting'),
('X10',S,'Post only the video and the lead\'s exact sentences, after','Post the video, the lead\'s exact sentences and the text of the lease line of the numbers message, after','extra internal sentence allowed in the public post'),
('X11',FA,"'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'","'postby': 'Wed 25 Nov 2026 15:00 UTC'",'post-by IST half dropped'),
('X12',FA,"'dl': pair(DEADLINE)","'dl': DEADLINE.strftime('%H:%M') + ' UTC'",'deadline IST half dropped everywhere'),
('X13',FA,"'postby': 'Wed 25 Nov 2026","'postby': 'Thu 25 Nov 2026",'post-by weekday changed'),
('X14',FA,"'bm': 'Mon 23 Nov 2026 '","'bm': 'Sun 23 Nov 2026 '",'reminder weekday changed'),
('X15',N,'Wed 18 Nov','Thu 18 Nov','run-day weekday changed in the lead note'),
]
def run(d):
    rb=subprocess.run([sys.executable,'-B',d+'build-v33.py',d],capture_output=True,text=True)
    if rb.returncode: return None,'BUILD STOPPED: '+(rb.stderr.strip().split('\n') or [''])[-1][:120]
    r=subprocess.run([sys.executable,'-B',d+'check-v33.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=d,V31_BANNED_TEST=BP))
    return set(re.sub(r'\d+ words','N words',l) for l in r.stdout.split('\n') if l.startswith('FAIL')),r
tmp=tempfile.mkdtemp(); base=tmp+'/base/'; os.mkdir(base)
for f in FILES: shutil.copy(H+f,base+f)
b0,_=run(base); print('baseline FAIL lines:',len(b0))
caught=missed=stopped=absent=0
for pid,f,old,new,what in P:
    d=tmp+'/'+pid+'/'; shutil.copytree(base,d); s=open(d+f,encoding='utf-8').read()
    if old not in s: print(pid,'ANCHOR-ABSENT',what); absent+=1; continue
    open(d+f,'w',encoding='utf-8').write(s.replace(old,new,1)); got,r=run(d)
    if got is None: print(pid,'CAUGHT-BY-BUILD-STOP |',what,'|',r); stopped+=1; continue
    nw=got-b0; codes=sorted(set(re.match(r'FAIL (C\d+[a-z]?|BUILD)',l)[1] for l in nw if re.match(r'FAIL (C\d+[a-z]?|BUILD)',l)))
    if nw: print(pid,'CAUGHT by',','.join(codes),'(%d line(s)) |'%len(nw),what); caught+=1
    else: print(pid,'MISSED (no new FAIL line) |',what); missed+=1
print('TOTAL 15: caught by checker %d, caught by build stop %d, MISSED %d, anchor absent %d'%(caught,stopped,missed,absent))
shutil.rmtree(tmp)
