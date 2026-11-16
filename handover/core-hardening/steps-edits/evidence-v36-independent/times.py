import re,glob,datetime as dt
files=sorted(glob.glob('OWNER-*v36-*.md')+['OWNER-FILM-PERSON-v36.md','OWNER-HELPER-v36.md','LEAD-RELEASE-NOTE-v20.md','v36-OPEN-FOR-LEAD.md','v36-CHANGES.md'])
files=[f for f in dict.fromkeys(files) if 'SOURCE' not in f]
M={m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
W=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
mism=0;pairs=0;wd=0;lone=0
for f in files:
    t=open(f,encoding='utf-8').read()
    for m in re.finditer(r'(\d{1,2}):(\d\d)(?::(\d\d))?\s*UTC\s*(?:=|/|,|is)?\s*(\d{1,2}):(\d\d)(?::(\d\d))?\s*IST',t):
        pairs+=1
        u=int(m[1])*3600+int(m[2])*60+int(m[3] or 0); i=int(m[4])*3600+int(m[5])*60+int(m[6] or 0)
        if (u+19800)%86400!=i: mism+=1; print('MISMATCH',f,m[0])
    # IST times not directly preceded by a UTC pair
    n_ist=len(re.findall(r'\d{1,2}:\d\d(?::\d\d)? IST',t)); n_pair=len(re.findall(r'UTC\s*=\s*\d{1,2}:\d\d(?::\d\d)? IST',t))
    if n_ist!=n_pair: lone+=1; print('INFO',f,'IST times',n_ist,'in pairs',n_pair)
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?: (\d{4}))?',t):
        wd+=1; d=dt.date(int(m[4] or 2026),M[m[3]],int(m[2]))
        if W[d.weekday()]!=m[1]: mism+=1; print('WEEKDAY MISMATCH',f,m[0])
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2})\b',t):
        wd+=1; d=dt.date(2026,M[m[2]],int(m[3]))
        if W[d.weekday()]!=m[1]: mism+=1; print('WEEKDAY MISMATCH',f,m[0])
    for m in re.finditer(r'\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (?:2026 )?\((Mon|Tue|Wed|Thu|Fri|Sat|Sun)',t):
        wd+=1; d=dt.date(2026,M[m[2]],int(m[1]))
        if W[d.weekday()]!=m[3]: mism+=1; print('WEEKDAY MISMATCH',f,m[0])
    # ISO dates followed/preceded by weekday
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (2026-\d\d-\d\d)',t):
        wd+=1; d=dt.date.fromisoformat(m[2])
        if W[d.weekday()]!=m[1]: mism+=1; print('WEEKDAY MISMATCH',f,m[0])
print('files',len(files),'pairs',pairs,'weekday-dates',wd,'mismatches',mism,'files with lone IST',lone)
print('16 Nov 2026 weekday:',W[dt.date(2026,11,16).weekday()])
