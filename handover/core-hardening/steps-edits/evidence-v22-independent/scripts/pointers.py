import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
rd=lambda n:open(DIR+n,encoding='utf-8').read()
S=rd('OWNER-SHEET-v22.md'); N=rd('LEAD-RELEASE-NOTE-v6.md'); O=rd('v22-OPEN-FOR-LEAD.md'); C=rd('v22-CHANGES.md')
SL=S.splitlines()
# sheet sections items
sec={}; cur=None
for l in SL:
    h=re.match(r'## (\d)\.',l)
    if h: cur=int(h.group(1)); sec[cur]={}; continue
    m=re.match(r'(\d+)\. ',l)
    if cur and m: sec[cur][int(m.group(1))]=l
print('sheet items per section',{k:len(v) for k,v in sec.items() if v})
nocode=lambda t:re.sub(r'`[^`]*`','',t)
# 1. numeric N.M pointers anywhere
for name,t in (('S',S),('N',N),('O',O),('C',C)):
    tt=nocode(t)
    for m in re.finditer(r'(?<![\d.:/\-])\b(\d)\.(\d{1,2})\b(?![\d:%])',tt):
        a,b=int(m.group(1)),int(m.group(2))
        ctx=tt[max(0,m.start()-60):m.end()+40].replace('\n',' ')
        exists = a in sec and b in sec[a]
        print('%s %s.%s exists=%s | %s'%(name,a,b,exists,ctx))
