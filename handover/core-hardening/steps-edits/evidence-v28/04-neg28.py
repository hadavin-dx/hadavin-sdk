import os, shutil, subprocess, sys, tempfile
H='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
OUT=H+'evidence-v28/04-negative-controls-raw/'; os.makedirs(OUT,exist_ok=True)
FILES=['facts-v28.py','build-v28.py','check-v28.py','newchecks-v28.py','OWNER-SHEET-v28-SOURCE.md','LEAD-RELEASE-NOTE-v12-SOURCE.md','v28-OPEN-FOR-LEAD-SOURCE.md','v28-CHANGES.md','pointers-v28.txt']
SRC='OWNER-SHEET-v28-SOURCE.md'; FACTS='facts-v28.py'; NOTE='LEAD-RELEASE-NOTE-v12-SOURCE.md'
K1='sk-ant-'+'api03-'+'Ab'*20; K2='AKIA'+'ZZZZ'+'1234'+'WXYZ'+'5678'; K3='AKIA'+'ABCDEFGH'+'IJKLMNOP'
C=[
('N01','facts: call ceiling 3 -> 4',FACTS,'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3','P_OUT_C, CEIL = 40000, 10000, 300, 1500, 4'),
('N02','facts: ledger 1240 -> 1250',FACTS,'LEDGER_C = 1240','LEDGER_C = 1250'),
('N03','facts: tokens out 10000 -> 11000 (the old AssertionError crash; must now be a FAIL line)',FACTS,'40000, 10000, 300, 1500, 3','40000, 11000, 300, 1500, 3'),
('N04','facts: post-by IST 20:30 -> 20:00',FACTS,"'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'","'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'"),
('N05','source: wrong UTC/IST pair in the sheet',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026 (written 09:00 UTC = 15:00 IST).'),
('N06','source: B fourth alarm removed',SRC,'[[B:, alarm 4 at the older-key time (do 7.11 now, whatever else is open)]]',''),
('N07','source: B 7.11 no longer passed by every exit',SRC,' passes 7.11 before 8.1.**','.**'),
('N08','source: minimum think time slot removed from the sample',SRC,'Minimum think time: {{think}} seconds   ',''),
('N09','source: typed-figure line removed',SRC,'Test program asks you to type a figure: no   ',''),
('N10','source: 5.9 must differ from the before-cancel word removed',SRC,"must differ from the look key's word before the cancel and from every live word","must differ from every live word"),
('N11','source: key-shaped string (from parts)',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026. Example key '+K1+'.'),
('N12','note source: "never deletes" turned into a delete instruction',NOTE,'the test program never deletes','the test program deletes; delete all contacts in the account now'),
('N13','source: wait hard-coded to 10 seconds',SRC,'Wait at least the "Minimum think time" of the message','Wait at least 10 seconds'),
('N14','facts: think 20 -> 10',FACTS,"'think': '20'","'think': '10'"),
('N15','source: AWS-style string with digits (from parts)',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026. Id '+K2+'.'),
('N16','source: wrong weekday',SRC,'Dated Mon 16 Nov 2026.','Dated Tue 16 Nov 2026.'),
('N17','source: AWS-style string, 16 capitals (from parts)',SRC,'Dated Mon 16 Nov 2026.','Dated Mon 16 Nov 2026. Id '+K3+'.'),
]
tmp=tempfile.mkdtemp(); only=sys.argv[1:]; bad=0
for cid,desc,f,old,new in C:
    d=tmp+'/'+cid+'/'; os.makedirs(d)
    for x in FILES: shutil.copy(H+x,d+x)
    t=open(d+f,encoding='utf-8').read()
    if old not in t: print(cid,'OLD TEXT NOT FOUND'); bad+=1; continue
    open(d+f,'w',encoding='utf-8').write(t.replace(old,new,1))
    rb=subprocess.run([sys.executable,'-B',d+'build-v28.py',d],capture_output=True,text=True)
    rc=subprocess.run([sys.executable,'-B',d+'check-v28.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=d))
    out=rc.stdout+rc.stderr
    open(OUT+cid+'.out.txt','w').write('desc: %s\nbuild rc=%d\ncheck rc=%d\n%s'%(desc,rb.returncode,rc.returncode,out))
    fl=[l for l in out.split('\n') if l.startswith('FAIL')]
    print(cid,'|',desc,'| check rc=%d | %s'%(rc.returncode,(fl[0][:100] if fl else out.strip()[-100:])))
    if rc.returncode!=1: bad+=1
shutil.rmtree(tmp); print('controls not exiting 1:',bad); sys.exit(1 if bad else 0)
