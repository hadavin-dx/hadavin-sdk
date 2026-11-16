import os, shutil, subprocess, sys, json
S='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ev27/'
BASE=S+'orig-copy/'
SRC='OWNER-SHEET-v27-SOURCE.md'; FACTS='facts-v27.py'; NOTE='LEAD-RELEASE-NOTE-v11-SOURCE.md'
K1='sk-ant-'+'api03-'+'Ab'*20
K2='AKIA'+'ZZZZ'+'1234'+'WXYZ'+'5678'
C=[
('N01','facts: call ceiling 3 -> 4 (0.27 x 3 = 0.81 / 13.21 arithmetic)',FACTS,'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3','P_OUT_C, CEIL = 40000, 10000, 300, 1500, 4'),
('N02','facts: ledger 1240 -> 1250 (limit 13.21 -> 13.31)',FACTS,'LEDGER_C = 1240','LEDGER_C = 1250'),
('N03','facts: price tokens out 10000 -> 11000 (0.27 -> 0.29)',FACTS,'TOK_IN, TOK_OUT, P_IN_C','TOK_IN, TOK_OUT, P_IN_C'),  # placeholder replaced below
('N04','facts: one IST time wrong (postby 20:30 -> 20:00)',FACTS,"'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'","'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'"),
('N05','source: hard-coded wrong UTC/IST pair inserted in sheet',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026 (written 09:00 UTC = 15:00 IST).'),
('N06','source: B fourth alarm removed',SRC,', alarm 4 at {{okb}} (do 7.11 now, whatever else is open)',''),
('N07','source: B 7.11 removed from the decline route',SRC,'[[B:(after your yes, 7.11 is still due by {{okb}})]]',''),
('N08','source: minimum think-time slot removed from the numbers-message slots',SRC,'Minimum think time: {{think}} seconds   ',''),
('N09','source: typed-figure line removed',SRC,'Test program asks you to type a figure: no   ',''),
('N10','source: look key step 5.9 cancel word removed',SRC,'the three words you see: cancel button, confirmation box (the button that really cancels) and cancelled word','the two words you see: cancel button and confirmation box (the button that really cancels)'),
('N11','source: key-shaped string (built from parts) inserted in sheet',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026. Example key '+K1+'.'),
('N12','lead note source: "never deletes" replaced by a delete instruction',NOTE,'the test program never deletes','the test program deletes; delete all contacts in the account now'),
('N13','source: think time wait hard-coded to 10 seconds',SRC,'Wait at least {{think}} seconds','Wait at least 10 seconds'),
('N14','facts: think 20 -> 10',FACTS,"'think': '20'","'think': '10'"),
('N15','source: second key-shaped string (AWS-style, built from parts) inserted',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026. Id '+K2+'.'),
('N16','source: deadline weekday wrong in sheet text',SRC,'Dated Mon 16 Nov 2026.','Dated Tue 16 Nov 2026.'),
]
res=[]
only=sys.argv[1:]
for cid,desc,f,old,new in C:
    if only and cid not in only: continue
    if cid=='N03': old,new='TOK_IN, TOK_OUT, P_IN_C, P_OUT_C, CEIL = 40000, 10000,','TOK_IN, TOK_OUT, P_IN_C, P_OUT_C, CEIL = 40000, 11000,'
    d=S+'neg/'+cid+'/'
    shutil.rmtree(d,ignore_errors=True); os.makedirs(S+'neg',exist_ok=True)
    shutil.copytree(BASE,d,ignore=shutil.ignore_patterns('evidence*','EDITS*','OWNER-STEPS*','LEAD-RELEASE-NOTE-v[1-9].md','__pycache__'))
    t=open(d+f,encoding='utf-8').read(); n=t.count(old)
    if n==0: res.append((cid,desc,'OLD TEXT NOT FOUND (control not applied)','-'));continue
    open(d+f,'w',encoding='utf-8').write(t.replace(old,new))
    rb=subprocess.run([sys.executable,'-B',d+'build-v27.py',d],capture_output=True,text=True)
    rc=subprocess.run([sys.executable,'-B',d+'check-v27.py'],capture_output=True,text=True,env=dict(os.environ,V26_DIR=d))
    out=(rb.stderr+rb.stdout if rb.returncode else '')+rc.stdout+rc.stderr
    open(S+'neg/'+cid+'.out.txt','w').write('desc: %s\nfile: %s occurrences replaced: %d\nbuild rc=%d\ncheck rc=%d\n%s'%(desc,f,n,rb.returncode,rc.returncode,out))
    fl=[l for l in out.split('\n') if l.startswith('FAIL') or 'stop' in l.lower() and rb.returncode]
    res.append((cid,desc,'build rc=%d check rc=%d (%d occ)'%(rb.returncode,rc.returncode,n),(fl[0][:110] if fl else (out.strip().split('\n')[-1][:110]))))
for r in res: print(' | '.join(map(str,r)))
