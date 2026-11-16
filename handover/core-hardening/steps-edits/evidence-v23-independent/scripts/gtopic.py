import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
rd=lambda n:open(DIR+n,encoding='utf-8').read()
K={1:['delete','re-pin','archive','reader','grep','f-01'],2:['checksum','flow'],3:['n8n','credential','connection value','sign in'],4:['call ceiling','ceiling','retries'],5:['usage','lag','gap'],6:['exit','person c','unknown'],7:['port'],8:['n8n','kill'],9:['shutdown','order'],10:['time','formula','alarm','run length','need_seconds','lease','run date'],11:['helper','human','film','editor','post check','role'],12:['claim','lease','sentence','ban'],13:['contact','list','source','id'],14:['money','balance','180','189','price','program limit','ceiling','figure','studio'],15:['rehears','loopback','stamp','printed result','smoke'],16:['end-date','refusal','deadline','model program','started','restart','process'],17:['notice','wording','printed result','mask','delete wording','prompt'],18:['wrong line','ctrl','film pause','refused','cancel','prompt','end','lock','stage'],19:['clean start','fresh','database','caption','postgres'],20:['one-store','one database','postgres','two databases','database'],21:['hubspot','permission','read-only','identit','key'],22:['roles','decision 7','owner','task','list'],23:['account','gmail','sender'],24:['place','tool','recording','post','film','box','editor'],25:['yes','go','compare','word for word'],26:['checksum','key-list','readings','key list','go'],27:['contact','list','clean-up','delete','demo mail'],28:['retire','clean-up','order','revoked'],29:['claim','printed result','post','sentence','film'],30:['timer','no lead','alarm','cancel'],31:['other channel','channel','second way'],32:['older key','nothing uses','file'],33:['spend lock','marker','go marker','spend'],34:['cancel race','after `end`','never calls','cancel','error','exit code','order'],35:['figure','type','typed','prompt'],36:['film cue','cue','timing','n8n','offset'],37:['key file','path','file per run','erase'],38:['demo mail','subject','prep','filter','label'],39:['start line','-i'],40:['times','run length','need_seconds','three','lines','y '],41:['cancelled','state word','word','button','last-resort','confirmation'],42:['hubspot','app secret','revoke','private app','apps']}
for n in ['LEAD-RELEASE-NOTE-v7.md','v23-OPEN-FOR-LEAD.md','v23-CHANGES.md','OWNER-SHEET-v23.md','checkpoint-v23.md']:
    t=rd(n); tot=0; sus=0
    for m in re.finditer(r'\bG(\d+)\b',t):
        g=int(m.group(1)); tot+=1
        ls=t.rfind('\n',0,m.start())+1
        if t[ls:].startswith('| G%d |'%g) and m.start()-ls<8: continue
        c=t[max(0,m.start()-110):m.end()+70].lower()
        if not any(k in c for k in K[g]):
            sus+=1; print('SUSPECT',n[:14],'G%d'%g,'|',c.replace('\n',' '))
    print(n,'mentions',tot,'suspect',sus)
