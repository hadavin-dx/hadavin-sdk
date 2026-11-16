import re,sys,datetime as dt
files=sys.argv[1:]
bad=0;tot=0;unp=0
for f in files:
    t=open(f,encoding='utf-8').read()
    for m in re.finditer(r'(\d{1,2}):(\d{2}) UTC',t):
        tot+=1
        tail=t[m.end():m.end()+30]
        p=re.match(r'\s*(?:=|/|,|or|\()\s*(\d{1,2}):(\d{2}) IST',tail)
        if not p:
            unp+=1; print('UNPAIRED',f.split('/')[-1],repr(t[max(0,m.start()-30):m.end()+35])); continue
        u=int(m.group(1))*60+int(m.group(2)); i=int(p.group(1))*60+int(p.group(2))
        if (u+330)%1440!=i: bad+=1; print('BADPAIR',f.split('/')[-1],repr(t[max(0,m.start()-30):m.end()+35]))
    for m in re.finditer(r'(\d{1,2}):(\d{2}) IST',t):
        head=t[max(0,m.start()-14):m.start()]
        if not re.search(r'(UTC\s*(=|/|,|or|\()\s*)$',head): print('IST-not-after-UTC',f.split('/')[-1],repr(t[max(0,m.start()-40):m.end()+10]))
    # weekday-date
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (\d{1,2}) (Nov|Dec|Oct|Jan) (\d{4})',t):
        d=dt.datetime.strptime(f'{m.group(2)} {m.group(3)} {m.group(4)}','%d %b %Y')
        if d.strftime('%a')!=m.group(1): bad+=1; print('BADWEEKDAY',f.split('/')[-1],m.group(0))
print('utc tokens',tot,'unpaired',unp,'bad',bad)
