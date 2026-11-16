import re
D='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
T={f:open(D+f).read() for f in ['OWNER-SHEET-v20.md','LEAD-RELEASE-NOTE-v4.md','v20-MAP.md','v20-OPEN-FOR-LEAD.md']}
S,N,M,O=T.values()
rd=re.findall(r'^\| (R\d+) \|',S,re.M); gd=re.findall(r'^\| (G\d+) \|',N,re.M); od=re.findall(r'^\| (\d+) \|',O,re.M)
print('R defs',len(rd),len(set(rd)),'G defs',len(gd),len(set(gd)),'Open defs',len(od),len(set(od)))
import collections
print('dup G',[k for k,v in collections.Counter(gd).items() if v>1],'dup Open',[k for k,v in collections.Counter(od).items() if v>1])
for f,x in T.items():
    rs=set(re.findall(r'\bR(\d+)\b',x)); gs=set(re.findall(r'\bG(\d+)\b',x)); os_=set(re.findall(r'\bOpen (\d+)\b',x))
    print(f,'R miss',[r for r in rs if 'R'+r not in rd],'G miss',[g for g in gs if 'G'+g not in gd],'Open miss',[o for o in os_ if o not in od])
# item pointers
items={};cur=None
for l in S.splitlines():
    h=re.match(r'## (\d)\.',l)
    if h:cur=int(h.group(1));items[cur]=0;continue
    if cur and re.match(r'\d+\. ',l):items[cur]+=1
print(items)
for f,x in T.items():
    xx=re.sub(r'`[^`]*`','',x)
    miss=[(a,b) for a,b in set(re.findall(r'(?<![\d.:/-])\b([5-8])\.(\d)\b(?![\d:])',xx)) if int(b)<1 or int(b)>items.get(int(a),0)]
    print(f,'item ptr miss',miss, 'ptrs',sorted(set(re.findall(r'(?<![\d.:/-])\b([5-8]\.\d)\b(?![\d:])',xx))))
