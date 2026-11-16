import re,sys,datetime as D
t=open(sys.argv[1],encoding='utf-8').read()
def s(x):
    p=[int(v) for v in x.split(':')]; return p[0]*3600+p[1]*60+(p[2] if len(p)>2 else 0)
def f(x,n): # n seconds, with day roll, same precision as x
    d,r=divmod(x,86400); h,m,sec=r//3600,r%3600//60,r%60
    return h,m,sec
ok=bad=0; badl=[]
T=r'(\d{1,2}:\d{2}(?::\d{2})?)'
pairs=re.findall(T+r'\s*UTC\s*(?:=|\()\s*'+T+r'\s*IST',t)
for u,i in pairs:
    su=s(u); si=s(i); exp=(su+19800)%86400
    if si==exp: ok+=1
    else: bad+=1; badl.append((u,i))
print('time pairs',len(pairs),'ok',ok,'bad',bad,badl[:10])
iso=re.findall(r'(20\d\d-\d\d-\d\d)T(\d\d:\d\d:\d\d)Z\s*=\s*(20\d\d-\d\d-\d\d)T(\d\d:\d\d:\d\d)\s*IST',t)
ok2=0;bad2=[]
for d1,t1,d2,t2 in iso:
    u=D.datetime.fromisoformat(d1+'T'+t1)+D.timedelta(hours=5,minutes=30)
    if u.isoformat()==d2+'T'+t2: ok2+=1
    else: bad2.append((d1,t1,d2,t2))
print('iso pairs',len(iso),'ok',ok2,'bad',bad2)
print('lone IST iso stamps',re.findall(r'20\d\d-\d\d-\d\dT[\d:]+ IST',t))
wd=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']; mo={m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
ws=re.findall(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) ([A-Z][a-z]{2})[a-z]*(?: (20\d\d))?',t)
okw=0;badw=[]
for w,d,m,y in ws:
    y=int(y) if y else 2026
    if wd[D.date(y,mo[m],int(d)).weekday()]==w: okw+=1
    else: badw.append((w,d,m,y))
print('weekday-dates',len(ws),'ok',okw,'bad',badw)
print('2026-11-16 weekday',wd[D.date(2026,11,16).weekday()])
# L-23NOV
for m in re.finditer(r'.{0,60}L-23NOV.{0,300}',t): pass
print('L-23NOV 18:04 UTC=23:34 IST mentions',len(re.findall(r'18:04(?::\d\d)? UTC = 23:34',t)),' 18:29 UTC=23:59',len(re.findall(r'18:29(?::\d\d)? UTC = 23:59',t)))
