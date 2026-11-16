import re,os,subprocess,sys,time
EV=os.path.dirname(os.path.abspath(__file__))
M=EV+'/mirror/handover/core-hardening/steps-edits'
src=open(M+'/EDITS.md',encoding='utf-8').read()
# (name, kind, old, new, which) which: 'all','first','last','nth:k'
MUT=[
('m01-end-time-all','all','18:29 UTC = 23:59 IST','18:39 UTC = 00:09 IST'),
('m02-end-time-last','last','18:29 UTC = 23:59 IST','18:49 UTC = 00:19 IST'),
('m03-lastrevoke-all','all','18:19 UTC = 23:49 IST','18:09 UTC = 23:39 IST'),
('m04-lastrevoke-mid','nth:17','18:19 UTC = 23:49 IST','18:25 UTC = 23:55 IST'),
('m05-end-wrongpair','first','18:29 UTC = 23:59 IST','18:29 UTC = 23:29 IST'),
('m06-REVERSE-keyrevoked-never','first','`key revoked` never confirms anything','`key revoked` always confirms everything'),
('m07-keyrevoked-confirms-last','first','(1) `key revoked` never confirms anything','(1) `key revoked` confirms the last take'),
('m08-30min-all-to-10','all','at least 30 minutes remain','at least 10 minutes remain'),
('m09-20min-to-5','first','unless fewer than 20 minutes remain','unless fewer than 5 minutes remain'),
('m10-delete-only-exact-1','first','You delete a contact only if its e-mail address is exactly','You delete a contact if its e-mail address is similar to'),
('m11-delete-only-exact-2','last','You delete a contact only if its e-mail address is exactly','You delete a contact if its e-mail address ends with'),
('m12-same-exact-address','first','the rule is the same exact address, at most 3','the rule is the same domain, at most 30'),
('m13-weekday-monday-all','all','Mon 23 Nov 2026','Tue 23 Nov 2026'),
('m14-weekday-wed-mid','nth:9','Wed 18 Nov 2026','Thu 18 Nov 2026'),
('m15-ist-offset-text','first','UTC plus 5 hours 30 minutes','UTC plus 5 hours'),
('m16-start-limit-all','all','18:00 UTC = 23:30 IST','18:00 UTC = 23:00 IST'),
('m17-REVERSE-route-ab','first','Route A is the safer one for keeping secrets safe; route B keeps','Route B is the safer one for keeping secrets safe; route A keeps'),
('m18-REVERSE-route-default','first','and does nothing else until you answer','and picks route B and goes on'),
('m19-reply-word-typo-mid','nth:12','`no more takes`','`no more take`'),
('m20-keygone-trunc-mid','nth:10','key gone, no more decisions','key gone'),
('m21-REVERSE-readonly','first','D2 take is read-only, never deletes contacts','D2 take is read-write, deletes contacts'),
('m22-REVERSE-idempotent','first','a lead sent twice with the same id is processed once','a lead sent twice with the same id is processed twice'),
('m23-REVERSE-no-start-later','first','no start later than 18:00 UTC = 23:30 IST','no start earlier than 18:00 UTC = 23:30 IST'),
('m24-unverified-flag','first','stops safely (UNVERIFIED)','stops safely (VERIFIED)'),
('m25-step21-heading','first','Mon 23 Nov before 18:29 UTC: you watch','Mon 23 Nov before 18:49 UTC: you watch'),
('m26-delete-30min-sentence','first','Make no new key now unless at least 30 minutes remain after you have answered (key step H)','Make a new key now'),
('m27-REVERSE-same-key','first','`key revoked` never confirms','`key revoked` confirms'),
('m28-weekday-23-all-to-sun','all','Mon 23 Nov','Sun 23 Nov'),
]
os.makedirs(EV+'/mut',exist_ok=True)
sel=sys.argv[1:] 
for name,kind,old,new in MUT:
    if sel and not any(name.startswith(s) for s in sel): continue
    c=src.count(old)
    if c==0: print(name,'ANCHOR MISSING'); continue
    if kind=='all': mut=src.replace(old,new)
    elif kind=='first': mut=src.replace(old,new,1)
    elif kind=='last':
        i=src.rindex(old); mut=src[:i]+new+src[i+len(old):]
    else:
        k=min(int(kind.split(':')[1]),c)-1
        i=-1
        for _ in range(k+1): i=src.index(old,i+1)
        mut=src[:i]+new+src[i+len(old):]
    assert mut!=src
    mp=EV+'/mut/'+name+'.md'; open(mp,'w',encoding='utf-8').write(mut)
    env=dict(os.environ,EDITS_PATH=mp,NO_NEG='1')
    t=time.time()
    out=subprocess.run([sys.executable,'-I',M+'/verify17.py'],env=env,capture_output=True,text=True,cwd=M).stdout
    fails=[l for l in out.split('\n') if l.startswith('FAIL ')]
    fl=[l for l in out.split('\n') if l.startswith('FAILURES')]
    print(name,'occ=%d'%c,'CAUGHT' if fails else 'MISSED',len(fails),'|',(fails[0][:110] if fails else ''),'|',int(time.time()-t),'s',flush=True)
