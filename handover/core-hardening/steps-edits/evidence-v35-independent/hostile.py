"""Independent hostile edits for v35 (evidence runner). Works only in scratch copies; the originals are never written."""
import os, re, shutil, subprocess, sys, tempfile, ast
H = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
BP = '/home/user/hadavin-sdk/tests/test_no_reference_material.py'
t = ast.parse(open(BP, encoding='utf-8').read()); BANNED = []
for n in ast.walk(t):
    if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets): BANNED = [e.value for e in n.value.elts]
print('banned entries read at run time:', len(BANNED))
B0 = BANNED[0]
def red(s):
    for b in BANNED: s = s.replace(b, '<BANNED>')
    return s
SRCF = ['facts-v35.py','build-v35.py','check-v35.py','OWNER-SHEET-v35-SOURCE.md','LEAD-RELEASE-NOTE-v19-SOURCE.md','v35-OPEN-FOR-LEAD-SOURCE.md','v35-CHANGES.md','pointers-v35.txt','headings-v35.txt','factuse-v35.txt','newchecks-v35.py']
def run(d):
    rb = subprocess.run([sys.executable,'-B',d+'build-v35.py',d],capture_output=True,text=True)
    if rb.returncode: return {'FAIL BUILD stopped: '+(rb.stderr.strip().split('\n') or [''])[-1][:100]}
    r = subprocess.run([sys.executable,'-B',d+'check-v35.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=d,V31_BANNED_TEST=BP))
    return set(l for l in r.stdout.split('\n') if l.startswith('FAIL'))
S='OWNER-SHEET-v35-SOURCE.md'; FA='facts-v35.py'
sk = 'sk-' + 'ant-' + 'api03-' + 'Zq8' * 12
ak = 'AK' + 'IA' + 'ABCDEFGHIJKLMNOP'
E = [
('H01',S,'Text between backticks is typed without the backticks;','The key is made at 11:30 UTC = 16:30 IST. Text between backticks is typed without the backticks;','add a wrong UTC/IST pair (11:30 UTC is 17:00 IST)',0),
('H02',S,'{{dl_day}}','Tue 23 Nov 2026','first {{dl_day}} replaced by a wrong weekday (Tue 23 Nov)',0),
('H03',S,'Sun 22 Nov','Sat 22 Nov','first "Sun 22 Nov" -> Sat',0),
('H04',S,'Text between backticks is typed without the backticks;','Fri 19 Nov 2026 is the day. Text between backticks is typed without the backticks;','wrong weekday-date added (19 Nov 2026 is Thu)',0),
('H05',S,'the latest start minus 5 minutes (sample {{enter}})','the latest start minus 4 minutes (sample {{enter}})','5-minute boundary changed to 4 in card definition',0),
('H06',FA,'ENTER = LS - dt.timedelta(minutes=5)','ENTER = LS - dt.timedelta(minutes=6)','5-minute boundary changed in facts',0),
('H07',S,'(on Sun 22 Nov: at or before {{sun_cb}})','(on Sun 22 Nov: at or before {{cb}})','Sunday cancel-by bound replaced by weekday bound',0),
('H08',S,'(on Sun 22 Nov: before {{bs_pair}}, the time of alarm 5)','(on Sun 22 Nov: before {{rv22}}, the time of alarm 5)','Sunday older-key bound moved to 18:19 (backstop)',0),
('H09',FA,'LAST_DAY = (DEADLINE.date() - dt.timedelta(days=1))','LAST_DAY = (DEADLINE.date() - dt.timedelta(days=2))','last run day moved from Sun to Sat',0),
('H10',FA,'RV23 = dt.datetime(2026, 11, 23, 18, 19)','RV23 = dt.datetime(2026, 11, 23, 18, 20)','18:19 revoke time -> 18:20',0),
('H11',FA,'BM = dt.datetime(2026, 11, 23, 18, 9)','BM = dt.datetime(2026, 11, 23, 18, 8)','18:09 Monday reminder -> 18:08',0),
('H12',FA,'BS = dt.datetime(2026, 11, 22, 18, 9)','BS = dt.datetime(2026, 11, 22, 18, 10)','18:09 Sunday reminder -> 18:10',0),
('H13',FA,'DEADLINE = dt.datetime(2026, 11, 23, 18, 29)','DEADLINE = dt.datetime(2026, 11, 23, 18, 28)','deadline 18:29 -> 18:28',0),
('H14',FA,"IST = dt.timedelta(hours=5, minutes=30)","IST = dt.timedelta(hours=5, minutes=31)",'IST offset +1 minute',0),
('H15',FA,"'dl_iso': '2026-11-23T18:29:00Z'","'dl_iso': '2026-11-23T18:39:00Z'",'ISO deadline string only',0),
('H16',S,'press cancel again on the same named row and reload','','cancel step sentence deleted (card step 4)',0),
('H17',S,'press cancel again on the same named row and reload',"press cancel again on the same named row and reload; then never press cancel at all",'cancel step contradicted',0),
('H18','SWAP',None,None,'swap every [[A: and [[B: condition marker',0),
('H19',S,"and only if the 7-day rule of 5.1 holds (read the older key's last-used time again right","and (read the older key's last-used time again right",'7-day rule removed from 6.7/7.11 condition (place 1)',0),
('H20',S,"that the 7-day rule of 5.1 holds (read the last-used time again now","that the key is old (read the last-used time again now",'7-day rule removed from card L2 (place 2)',0),
('H21',S,'at least 168 hours (7 days)','at least 120 hours (5 days)','7-day rule changed to 5 days',0),
('H22',S,'Text between backticks is typed without the backticks;','Text between backticks is typed without the backticks; token '+sk+';','secret-shaped string (sk-ant-style, built from parts) added',0),
('H23',S,'Text between backticks is typed without the backticks;','Text between backticks is typed without the backticks; id '+ak+';','secret-shaped AWS-style id added (not the allowed example)',0),
('H24',S,'Text between backticks is typed without the backticks;','Text between backticks is typed without the backticks; see '+B0+';','banned entry #0 from the list added',0),
('H25',S,'Text between backticks is typed without the backticks;','Text between backticks is typed without the backticks; '+B0.upper()+';','banned entry #0 uppercased',0),
('H26',S,'Text between backticks is typed without the backticks;','Text between backticks is typed without the backticks; '+B0[:1]+'​'+B0[1:]+';','banned entry #0 with a zero-width space inside',0),
('H27',FA,"'cf': 'cancel failed'","'cf': 'cancel faild'",'typed phrase "cancel failed" broken in facts (all uses)',0),
('H28',S,'"{{ph_cf}}"','"cancel fail"','one typed phrase use broken in source',0),
('H29',FA,'CEIL = 40000, 10000, 300, 1500, 3','CEIL = 40000, 10000, 300, 1500, 2','call count 3 -> 2',0),
('H30',FA,'HELPER_SCOPE = "the keys named on the helper\'s paper (at most three:','HELPER_SCOPE = "the keys named on the helper\'s paper (at most four:','count: helper keys at most three -> four',0),
('H31',S,'Four phone alarms on the run day','Five phone alarms on the run day','count: four alarms -> five (text only)',0),
('H32',S,'(normally 1, plus the look key)','(normally 2, plus the look key)','count: normally 1 key -> 2',0),
('H33',S,'Paste once (Ctrl+Shift+V','Paste twice (Ctrl+Shift+V','paste once -> twice',0),
('H34',S,'Sunday run day: a run on Sun 22 Nov is allowed only if','Sunday run day: a run on Sun 22 Nov is allowed even if','Sunday condition loosened',0),
('H35',FA,"SEVENBACK = EK - dt.timedelta(hours=168)","SEVENBACK = EK - dt.timedelta(hours=144)",'7-day constant 168h -> 144h in facts',0),
('H36',FA,"OKB = dt.datetime.combine(DAY, dt.time(16, 0))","OKB = dt.datetime.combine(DAY, dt.time(17, 0))",'older-key time B 16:00 -> 17:00',0),
('H37',FA,"LS23 = dt.datetime(2026, 11, 23, 18, 4)","LS23 = dt.datetime(2026, 11, 23, 18, 14)",'Monday latest start 18:04 -> 18:14',0),
('H38',FA,"HW = 30","HW = 45","helper wait 30 -> 45 min",0),
]
PAGEE = [  # edits to BUILT pages in a copy (source untouched): C01 should fire
('G01','OWNER-SHEET-v35-A.md','18:29 UTC = 23:59 IST','18:29 UTC = 23:49 IST','built sheet A: deadline pair changed'),
('G02','OWNER-SHEET-v35-B.md','Mon 23 Nov 2026','Tue 23 Nov 2026','built sheet B: weekday changed'),
('G03','OWNER-CARD-v35-A.md','minus 5 minutes','minus 4 minutes','built card A: 5-minute boundary'),
('G04','OWNER-APPENDIX-v35-A.md','18:19 UTC = 23:49 IST','18:18 UTC = 23:48 IST','built appendix A: 18:19 pair'),
('G05','OWNER-SHEET-v35-A.md','Paste once','Paste twice','built sheet A: paste once'),
('G06','OWNER-HELPER-v35.md',None,'\nkey text sk-'+'ant-'+'api03-'+'Zq8'*12+'\n','built helper page: secret-shaped string appended'),
]
tmp = tempfile.mkdtemp()
base = tmp+'/base/'; os.mkdir(base)
for f in SRCF + [x for x in os.listdir(H) if re.match(r'OWNER-.*v35|LEAD-RELEASE-NOTE-v19|v35-OPEN',x)]:
    if os.path.isfile(H+f): shutil.copy(H+f, base+f)
b0 = run(base); print('baseline FAIL lines in scratch copy: %d' % len(b0))
norm = lambda x: re.sub(r'\d+ words','N words',x)
b0n = set(map(norm,b0)); caught=missed=anc=0; MISS=[]
def code(l):
    m = re.match(r'FAIL (\S+)', l); return m[1] if m else '?'
for pid,f,o,n,what,ra in E:
    d = tmp+'/'+pid+'/'; shutil.copytree(base,d)
    if f=='SWAP':
        s=open(d+S,encoding='utf-8').read(); s=s.replace('[[A:','[[@:').replace('[[B:','[[A:').replace('[[@:','[[B:'); open(d+S,'w',encoding='utf-8').write(s)
    else:
        s=open(d+f,encoding='utf-8').read()
        if o not in s: print(pid,'ANCHOR-NOT-FOUND',what); anc+=1; continue
        open(d+f,'w',encoding='utf-8').write(s.replace(o,n,1))
    got = run(d); new = sorted(set(map(norm,got))-b0n)
    if new: caught+=1; cs=sorted(set(code(l) for l in new)); print('%s CAUGHT by %s | %s | first: %s' % (pid,','.join(cs),what,red(new[0])[:150]))
    else: missed+=1; MISS.append(pid); print('%s MISSED (no new FAIL line) | %s' % (pid,what))
    shutil.rmtree(d)
for pid,f,o,n,what in PAGEE:
    d = tmp+'/'+pid+'/'; shutil.copytree(base,d)
    s=open(d+f,encoding='utf-8').read()
    if o is None: s=s+n
    elif o not in s: print(pid,'ANCHOR-NOT-FOUND',what); anc+=1; continue
    else: s=s.replace(o,n,1)
    open(d+f,'w',encoding='utf-8').write(s)
    # run check only (no rebuild), as a person editing the printed page would
    r = subprocess.run([sys.executable,'-B',d+'check-v35.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=d,V31_BANNED_TEST=BP))
    got=set(l for l in r.stdout.split('\n') if l.startswith('FAIL')); new=sorted(set(map(norm,got))-b0n)
    if new: caught+=1; print('%s CAUGHT by %s | %s | first: %s' % (pid,','.join(sorted(set(code(l) for l in new))),what,red(new[0])[:150]))
    else: missed+=1; MISS.append(pid); print('%s MISSED | %s' % (pid,what))
    shutil.rmtree(d)
print('TOTAL hostile edits %d: caught %d, missed %d %s, anchor-not-found %d' % (len(E)+len(PAGEE),caught,missed,MISS,anc))
shutil.rmtree(tmp)
