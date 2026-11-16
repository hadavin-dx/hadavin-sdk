import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
rd=lambda n:open(DIR+n,encoding='utf-8').read()
F={'S':'OWNER-SHEET-v23.md','N':'LEAD-RELEASE-NOTE-v7.md','O':'v23-OPEN-FOR-LEAD.md','C':'v23-CHANGES.md','K':'checkpoint-v23.md'}
T={k:rd(v) for k,v in F.items()}
SL=T['S'].splitlines()
sec={}; cur=None
for l in SL:
    h=re.match(r'## (\d)\.',l)
    if h: cur=int(h.group(1)); sec[cur]={}; continue
    m=re.match(r'(\d+)\. ',l)
    if cur and m: sec[cur][int(m.group(1))]=l
print('sheet items per section',{k:len(v) for k,v in sec.items() if v})
nocode=lambda t:re.sub(r'`[^`]*`','',t)
for name,t in T.items():
    tt=nocode(t)
    for m in re.finditer(r'(?<![\d.:/\-])\b(\d)\.(\d{1,2})\b(?![\d:%])',tt):
        a,b=int(m.group(1)),int(m.group(2))
        # skip decimals: preceded by "USD " or followed by digits handled; mark money-ish
        ctx=tt[max(0,m.start()-70):m.end()+50].replace('\n',' ')
        exists = a in sec and b in sec[a]
        title=(sec[a][b][:60] if exists else '')
        print('%s %s.%s exists=%s | %s || TARGET: %s'%(name,a,b,exists,ctx,title))
