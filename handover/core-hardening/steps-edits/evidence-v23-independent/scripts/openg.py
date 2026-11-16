import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
rd=lambda n:open(DIR+n,encoding='utf-8').read()
N=rd('LEAD-RELEASE-NOTE-v7.md');O=rd('v23-OPEN-FOR-LEAD.md');C=rd('v23-CHANGES.md');S=rd('OWNER-SHEET-v23.md');K=rd('checkpoint-v23.md')
rows=re.findall(r'^\| (\d+) \|',O,re.M)
print('open rows',len(rows),'in order',[int(x) for x in rows]==list(range(1,len(rows)+1)))
# rows text map
orow={}
for l in O.splitlines():
    m=re.match(r'\| (\d+) \|',l)
    if m: orow[int(m.group(1))]=l
for nm,t in (('N',N),('O',O),('C',C),('K',K),('S',S)):
    for m in re.finditer(r'\b(?:Open|Open rows?|rows?) (\d+(?:(?:, | and |, and )\d+)*)',t):
        nums=[int(x) for x in re.findall(r'\d+',m.group(1))]
        for n in nums:
            print('%s Open %d resolves=%s | ctx: %s || ROW: %s'%(nm,n,n in orow,t[max(0,m.start()-90):m.end()+50].replace('\n',' '),orow.get(n,'')[:130]))
# G defs
gd=re.findall(r'^\| (G\d+) \|',N,re.M)
print('G defs',len(gd),sorted(set(gd),key=lambda x:int(x[1:]))==['G%d'%i for i in range(1,43)], 'dups',[g for g in set(gd) if gd.count(g)>1])
grow={}
for l in N.splitlines():
    m=re.match(r'\| (G\d+) \|',l)
    if m: grow[m.group(1)]=l
for nm,t in (('N',N),('O',O),('C',C),('S',S),('K',K)):
    for m in re.finditer(r'\bG(\d+)\b',t):
        g='G%s'%m.group(1)
        if nm=='N' and re.match(r'\| G\d+ \|',t[t.rfind('\n',0,m.start())+1:m.end()+3]) and t[t.rfind('\n',0,m.start())+1:].startswith('| '+g+' |') and m.start()-t.rfind('\n',0,m.start())<8: continue
        print('%s %s resolves=%s | %s || DEF: %s'%(nm,g,g in grow,t[max(0,m.start()-85):m.end()+40].replace('\n',' '),grow.get(g,'')[:110]))
