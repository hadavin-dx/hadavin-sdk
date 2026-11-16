import re,os,datetime as dt,collections
D='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
files=[f for f in os.listdir(D) if re.search(r'(OWNER-(SHEET|CARD|APPENDIX)-v33-[AB]|OWNER-FILM-PERSON-v33|OWNER-HELPER-v33|LEAD-RELEASE-NOTE-v17|v33-OPEN-FOR-LEAD)\.md$',f)]
pair=re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2}))? UTC = (\d{1,2}):(\d{2})(?::(\d{2}))? IST')
loneutc=re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?) UTC(?! = \d)')
loneist=re.compile(r'(?<!= )(\d{1,2}:\d{2}(?::\d{2})?) IST')
wd=re.compile(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* (\d{1,2}) (Nov|Dec|Oct)\w*(?: (\d{4}))?')
MON={'Oct':10,'Nov':11,'Dec':12}
tp=bp=tw=bw=0; bad=[]; loneu=collections.Counter(); wdc=collections.Counter()
for f in sorted(files):
    s=open(D+f,encoding='utf-8').read(); np=nw=0
    for m in pair.finditer(s):
        np+=1; u=int(m.group(1))*60+int(m.group(2)); i=int(m.group(4))*60+int(m.group(5))
        if (u+330)%1440!=i or (m.group(6) is not None and (m.group(3) or '0')!=m.group(6)) or (m.group(6) is None and m.group(3) not in (None,'00')): bad.append((f,m.group(0)))
    for m in wd.finditer(s):
        nw+=1; y=int(m.group(4) or 2026); d=dt.date(y,MON[m.group(3)],int(m.group(2)))
        if d.strftime('%a')!=m.group(1): bad.append((f,'WEEKDAY '+m.group(0)+' real '+d.strftime('%a')))
        wdc[(m.group(1),m.group(2),m.group(3))]+=1
    s2=pair.sub('',s); lu=[m.group(0) for m in loneutc.finditer(s2)]; li=[m.group(0) for m in re.finditer(r'\d{1,2}:\d{2}(?::\d{2})? IST',s2)]
    print('%-30s pairs %3d  weekday-dates %3d  lone-UTC %3d  lone-IST %3d'%(f,np,nw,len(lu),len(li)))
    for x in lu[:4]: 
        k=s2.index(x); print('      lone UTC:',repr(s2[max(0,k-60):k+len(x)+20]))
    for x in li[:4]:
        k=s2.index(x); print('      lone IST:',repr(s2[max(0,k-60):k+len(x)+20]))
print('BAD pairs/weekdays:',len(bad)); [print('  ',b) for b in bad[:20]]
req={('Mon','16','Nov'),('Wed','18','Nov'),('Sun','22','Nov'),('Mon','23','Nov'),('Wed','25','Nov')}
print('required dates seen:',{k:wdc[k] for k in req}); print('all weekday-dates seen:',sorted(wdc))
