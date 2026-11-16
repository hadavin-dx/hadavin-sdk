import re,sys,datetime as dt
t=open(sys.argv[1],encoding='utf-8').read()
mon=dict(Jan=1,Feb=2,Mar=3,Apr=4,May=5,Jun=6,Jul=7,Aug=8,Sep=9,Oct=10,Nov=11,Dec=12)
wd=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
bad=[];n=0
# pairs HH:MM UTC = HH:MM IST
for m in re.finditer(r'(\d{1,2}):(\d{2}) UTC\s*(?:=|/|and|\()\s*(\d{1,2}):(\d{2}) IST',t):
    n+=1
    u=int(m[1])*60+int(m[2]);i=int(m[3])*60+int(m[4])
    if (u+330)%1440!=i: bad.append(('pair',m[0],t.count('\n',0,m.start())+1))
print('UTC/IST pairs checked',n,'bad',len(bad))
# weekday-date
w=0;wb=[]
for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (20\d\d)',t):
    w+=1
    d=dt.date(int(m[4]),mon[m[3]],int(m[2]))
    if wd[d.weekday()]!=m[1][:3]: wb.append((m[0],t.count('\n',0,m.start())+1))
for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]* (20\d\d-\d\d-\d\d)',t):
    w+=1
    d=dt.date.fromisoformat(m[2])
    if wd[d.weekday()]!=m[1][:3]: wb.append((m[0],t.count('\n',0,m.start())+1))
print('weekday-date pairs',w,'bad',len(wb))
for b in bad+wb: print('BAD',b)
# any UTC time not near an IST on same line
c=0
for ln_no,ln in enumerate(t.split('\n'),1):
    for m in re.finditer(r'\b(\d{1,2}):(\d{2}) UTC',ln):
        if 'IST' not in ln[m.end():m.end()+40]:
            c+=1; print('UTC without IST within 40 chars: line',ln_no,ln[max(0,m.start()-30):m.end()+30].replace('\n',' '))
print('UTC without IST',c)
