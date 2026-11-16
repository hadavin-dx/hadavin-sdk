import os,re,shutil,subprocess,sys
R=os.path.abspath('.'); SRC=R+'/h/core-hardening/steps-edits/'
files={f:open(SRC+f,encoding='utf-8').read() for f in ['EDITS.md','r18-OWNER-DAY-SHEET.md','r18-OWNER-APPENDIX-K.md','r18-CHANGES.md']}
def rep(f,old,new,all_=False,must=1):
    def fn(d):
        t=d[f]; c=t.count(old)
        assert c>=must,(f,old[:50],c)
        d[f]=t.replace(old,new) if all_ else t.replace(old,new,1)
    return fn
def multi(*fs): 
    def fn(d):
        for x in fs: x(d)
    return fn
def dup_row(d):
    t=d['EDITS.md']; i=t.index('\n### E-20:'); j=t.index('\n### E-21:'); d['EDITS.md']=t[:j]+t[i:j]+t[j:]
S='Shredding does not revoke the key, and it is not reliable on every disk, so it does not replace key step I.'
M=[
('M01 pair 18:19 UTC paired with 23:39 IST (one copy in EDITS)', rep('EDITS.md','18:19 UTC = 23:49 IST','18:19 UTC = 23:39 IST')),
('M02 day sheet alarm 3 pair 18:19 UTC = 23:39 IST (day sheet only)', rep('r18-OWNER-DAY-SHEET.md','Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST','Alarm 3: Mon 23 Nov 2026 18:19 UTC = 23:39 IST')),
('M03 wrong pair in EVERY copy (alarm 3 18:09 UTC = 23:49 IST), EDITS+day', multi(rep('EDITS.md','18:09 UTC = 23:39 IST','18:09 UTC = 23:49 IST',True),rep('r18-OWNER-DAY-SHEET.md','18:09 UTC = 23:39 IST','18:09 UTC = 23:49 IST',True))),
('M04 wrong weekday in every copy (Last day, Tue 23 Nov 2026), EDITS+day', multi(rep('EDITS.md','Last day, Mon 23 Nov 2026','Last day, Tue 23 Nov 2026',True),rep('r18-OWNER-DAY-SHEET.md','Last day, Mon 23 Nov 2026','Last day, Tue 23 Nov 2026',True))),
('M05 deleted safety sentence (shredding does not revoke) in every copy', multi(rep('EDITS.md',' '+S,'',True),rep('r18-OWNER-DAY-SHEET.md',' '+S,'',True))),
('M06 reversed default (new keys first: always) every copy', multi(rep('EDITS.md','Make new keys first only if key step H says so and at least 30 minutes remain.','Make new keys first always.',True),rep('r18-OWNER-DAY-SHEET.md','Make new keys first only if key step H says so and at least 30 minutes remain.','Make new keys first always.',True))),
('M07 removed confirmation step (read the removal list) every copy', multi(rep('EDITS.md',"read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write","write",True),rep('r18-OWNER-DAY-SHEET.md',"read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write","write",True))),
('M08 changed typed word `please stop looking` -> `please stop now` in EDITS+day', multi(rep('EDITS.md','`please stop looking`','`please stop now`',True),rep('r18-OWNER-DAY-SHEET.md','`please stop looking`','`please stop now`',True))),
('M09 duplicated row E-20 in EDITS', dup_row),
('M10 first Tue 24 Nov 2026 moved to Mon 23 Nov 2026 (EDITS only)', rep('EDITS.md','Tue 24 Nov 2026','Mon 23 Nov 2026')),
('M11 forged counts in CHANGES (21,492 -> 20,492; 198 -> 199 caught)', multi(rep('r18-CHANGES.md','20,436 -> 21,492','20,436 -> 20,492'),rep('r18-CHANGES.md','198 caught','199 caught'))),
('M12 deleted one HOLD block marker: row status Hold -> Apply now (E-04)', rep('EDITS.md','### E-04: OWNER-STEPS-realrun-v3.md, line 69, status Hold (gate G1)','### E-04: OWNER-STEPS-realrun-v3.md, line 69, status Apply now')),
('M13 seconds pair wrong 18:15:20 UTC = 23:55:20 IST', rep('EDITS.md','18:15:20 UTC = 23:45:20 IST','18:15:20 UTC = 23:55:20 IST')),
('M14 alarm 1 loses IST pair in EDITS+day (bare UTC)', multi(rep('EDITS.md','17:49 UTC = 23:19 IST','17:49 UTC',True),rep('r18-OWNER-DAY-SHEET.md','17:49 UTC = 23:19 IST','17:49 UTC',True))),
('M15 reversed meaning of `key revoked` reply (answers once -> never answers) EDITS+day', multi(rep('EDITS.md','the assistant answers it once with','the assistant never answers it with',True),rep('r18-OWNER-DAY-SHEET.md','the assistant answers it once with','the assistant never answers it with',True))),
('M16 weekday of take date: Wed 18 Nov 2026 -> Thu 18 Nov 2026 (EDITS only)', rep('EDITS.md','Wed 18 Nov 2026','Thu 18 Nov 2026')),
('M17 appendix K sentence deleted: K-A why-sentence (file+EDITS section)', None),
('M18 AGENT-SCOPE row: delete a safety sentence (E-26 NEW)', None),
('M19 day sheet: two cards steps swapped (2 and 3) day sheet only', None),
('M20 IST = UTC+6 error in minutes only in appendix file: 18:29 UTC = 23:59 IST -> 00:29 IST', rep('r18-OWNER-APPENDIX-K.md','18:29 UTC = 23:59 IST','18:29 UTC = 00:29 IST')),
]
# fill M17-19 dynamic
def m17(d):
    for f in ['EDITS.md','r18-OWNER-APPENDIX-K.md']:
        t=d[f]; i=t.index('K-A (detail of key step A).'); j=t.index('\n',i); line=t[i:j]; sents=line.split('. ')
        # delete the second sentence
        new='. '.join([sents[0]]+sents[2:]); d[f]=t[:i]+new+t[j:]
M[16]=(M[16][0],m17)
def m18(d):
    t=d['EDITS.md']; i=t.index('### E-26:'); j=t.index('### E-27:'); blk=t[i:j]
    a=blk.index('NEW'); new=blk[a:]
    print('E-26 NEW:',new[:400].replace('\n',' | '))
    d['EDITS.md']=t
M[17]=('M18 deleted safety sentence The assistant never opens the files, EDITS+day',multi(rep('EDITS.md',' The assistant never opens the files.','',True),rep('r18-OWNER-DAY-SHEET.md',' The assistant never opens the files.','',True)))
def m19(d):
    t=d['r18-OWNER-DAY-SHEET.md']; a=[l for l in t.split('\n') if l.startswith('2. You:')][0]; b=[l for l in t.split('\n') if l.startswith('3. You:')][0]
    t=t.replace(a,'@@A').replace(b,'@@B').replace('@@A',b.replace('3. You:','2. You:',1)).replace('@@B',a.replace('2. You:','3. You:',1)); d['r18-OWNER-DAY-SHEET.md']=t
M[18]=(M[18][0],m19)
def m22(d):
    for f in ['EDITS.md','r18-OWNER-APPENDIX-K.md']:
        t=d[f]; i=t.index('K-D (detail of key step D).'); j=t.index('\n',i); line=t[i:j]; sents=line.split('. ')
        d[f]=t[:i]+'. '.join([sents[0]]+sents[2:])+t[j:]
M+=[('M21 10 minutes -> 20 minutes (last-day window length) EDITS+day',multi(rep('EDITS.md','there are only 10 minutes','there are only 20 minutes',True),rep('r18-OWNER-DAY-SHEET.md','there are only 10 minutes','there are only 20 minutes',True))),
('M22 deleted 2nd sentence of K-D (file+EDITS section)',m22),
('M23 deleted (never its content) EDITS+day',multi(rep('EDITS.md',' (never its content)','',True),rep('r18-OWNER-DAY-SHEET.md',' (never its content)','',True))),
('M24 reversed default: neither written treated as shred done (EDITS+day)',multi(rep('EDITS.md','If you write neither, the assistant treats it as `shred not done key copies` or `shred not done other files`.','If you write neither, the assistant treats it as `shred done key copies` or `shred done other files`.',True),rep('r18-OWNER-DAY-SHEET.md','If you write neither, the assistant treats it as `shred not done key copies` or `shred not done other files`.','If you write neither, the assistant treats it as `shred done key copies` or `shred done other files`.',True)))]
only=sys.argv[1:]
out=[]
for name,fn in M:
    k=name.split()[0]
    if only and k not in only: continue
    d=dict(files); fn(d)
    base=R+'/m/'+k; shutil.rmtree(base,ignore_errors=True)
    se=base+'/h/core-hardening/steps-edits/'; os.makedirs(se)
    os.symlink(R+'/h/core-hardening/inputs',base+'/h/core-hardening/inputs'); os.symlink(R+'/tests',base+'/tests')
    shutil.copy(SRC+'verify18.py',se)
    for f,t in d.items(): open(se+f,'w',encoding='utf-8').write(t)
    changed=[f for f in d if d[f]!=files[f]]
    env=dict(os.environ,NO_NEG='1')
    p=subprocess.run([sys.executable,'-I',se+'verify18.py'],env=env,capture_output=True,text=True)
    fails=[l for l in p.stdout.split('\n') if l.startswith('FAIL ')]
    last=[l for l in p.stdout.split('\n') if l.startswith('FAILURES')]
    print(k,'CAUGHT' if fails or p.returncode not in (0,) and 'Traceback' not in p.stderr else ('CRASH' if 'Traceback' in p.stderr else 'MISSED'),'| changed',changed,'| nfail',len(fails),'| rc',p.returncode,'|',(fails[0][:110] if fails else (p.stderr[-120:] if p.stderr else '')))
    out.append((k,name,bool(fails),changed))
