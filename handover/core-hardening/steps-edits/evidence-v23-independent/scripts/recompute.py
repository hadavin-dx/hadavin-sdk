# independent recompute (own code; not check-v22.py)
import re, datetime as dt, glob
from decimal import Decimal as D, ROUND_CEILING
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
files={n:open(DIR+n,encoding='utf-8').read() for n in ['OWNER-SHEET-v23.md','LEAD-RELEASE-NOTE-v7.md','v23-OPEN-FOR-LEAD.md','v23-CHANGES.md','checkpoint-v23.md']}
fail=[]
def chk(name,cond,detail=''):
    print(('PASS ' if cond else 'FAIL ')+name+(' '+detail if detail else ''))
    if not cond: fail.append(name)
# money
p=(D(40000)*3+D(10000)*15)/D(1000000); chk('price per call 0.27',p==D('0.27'),str(p))
chk('ceiling 3 x 0.27 = 0.81',3*p==D('0.81'),str(3*p))
pl=D('12.40')+D('0.81'); chk('12.40+0.81=13.21',pl==D('13.21'),str(pl))
chk('13.21 USD = 1321 cents',int(pl*100)==1321)
S=files['OWNER-SHEET-v23.md']
chk('sheet PROGRAM_LIMIT_CENTS = 1321','PROGRAM_LIMIT_CENTS = 1321' in S)
chk('sheet PRICE_IN_CENTS 300 / OUT 1500','PRICE_IN_CENTS = 300' in S and 'PRICE_OUT_CENTS = 1500' in S)
# cents-per-million to USD per token path with integers
tin,tout,pin,pout=40000,10000,300,1500   # cents per million
cents_times_1e6=tin*pin+tout*pout        # = cents*1e6
chk('integer path: (tin*pin+tout*pout)=27,000,000 => 27 cents',cents_times_1e6==27_000_000)
# times
def T(s):
    p=[int(x) for x in s.split(':')]+[0]*(3-len(s.split(':')))
    return dt.timedelta(hours=p[0],minutes=p[1],seconds=p[2])
def f(t,sec=False):
    s=int(t.total_seconds()); h,r=divmod(s,3600); m,x=divmod(r,60)
    return '%02d:%02d:%02d'%(h,m,x) if sec or x else '%02d:%02d'%(h,m)
IST=dt.timedelta(hours=5,minutes=30)
Y,RL,FP,M,Z=5,15,10,10,10
chk('Y+RL+FP = 30',Y+RL+FP==30)
dl=T('18:29'); need=860
chk('860 s = 14.333.. min; rounded up to 1 decimal 14.4',(D(need)/60*10).to_integral_value(rounding=ROUND_CEILING)/10==D('14.4'),str(D(need)/60))
chk('15 min >= 860 s',RL*60>=need, '900>=860')
B=dl-dt.timedelta(seconds=need); chk('B = 18:14:40',f(B,True)=='18:14:40',f(B,True))
chk('B IST 23:44:40',f(B+IST,True)=='23:44:40')
lim=dl-dt.timedelta(minutes=Y+RL+FP+M+Z); chk('deadline-50min = 17:39:00',f(lim,True)=='17:39:00',f(lim,True))
LS1=min(T('11:30'),B,lim); LF1=LS1+dt.timedelta(minutes=30); CB1=LF1+dt.timedelta(minutes=M)
chk('ex1 LS/LF/CB = 11:30/12:00/12:10',(f(LS1),f(LF1),f(CB1))==('11:30','12:00','12:10'),str((f(LS1),f(LF1),f(CB1))))
chk('ex1 IST 17:00/17:30/17:40',(f(LS1+IST),f(LF1+IST),f(CB1+IST))==('17:00','17:30','17:40'))
chk('ex1 CB >= 10 min before deadline',dl-CB1>=dt.timedelta(minutes=10))
LS2=min(T('18:10'),B,lim); LF2=LS2+dt.timedelta(minutes=30); CB2=LF2+dt.timedelta(minutes=M)
chk('ex2 (23 Nov) LS=17:39:00 LF=18:09:00 CB=18:19:00',(f(LS2,True),f(LF2,True),f(CB2,True))==('17:39:00','18:09:00','18:19:00'))
chk('ex2 IST 23:09/23:39/23:49',(f(LS2+IST),f(LF2+IST),f(CB2+IST))==('23:09','23:39','23:49'))
chk('ex2 deadline - CB = 10 min',dl-CB2==dt.timedelta(minutes=10))
chk('23:59 IST = 18:29 UTC',f(dl+IST)=='23:59')
chk('earliest key 11:00=16:30',f(T('11:00')+IST)=='16:30')
chk('15:00 UTC=20:30 IST',f(T('15:00')+IST)=='20:30')
# the owner sheet check 3 wording: alarm=LS+Y+RL+FP
# UTC=IST pairs
for n,t in files.items():
    pairs=re.findall(r'(\d\d:\d\d(?::\d\d)?) UTC\s*=\s*(\d\d:\d\d(?::\d\d)?) IST',t)
    for a,b in pairs:
        ok=(T(a)+IST)%dt.timedelta(days=1)==T(b)
        chk('pair %s: %s UTC = %s IST'%(n[:14],a,b),ok)
    # also 'UTC = IST' forms with only one time? list lines containing UTC but no IST pair
# weekdays
wdn=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
for n,t in files.items():
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b,? (\d{1,2}) Nov\b',t):
        d=dt.date(2026,11,int(m.group(2))); chk('weekday %s: %s %s Nov'%(n[:14],m.group(1),m.group(2)),wdn[d.weekday()]==m.group(1))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) Nov (\d{1,2})\b',t):
        d=dt.date(2026,11,int(m.group(2))); chk('weekday(ps) %s: %s Nov %s'%(n[:14],m.group(1),m.group(2)),wdn[d.weekday()]==m.group(1))
    # any weekday word followed by something else
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b (?!\d{1,2} Nov|Nov \d)',t):
        print('  info weekday-other',n[:14],t[m.start()-20:m.end()+25].replace('\n',' '))
print('FAILS:',fail)
# --- extras for v23
S=files['OWNER-SHEET-v23.md']
chk('sheet 860 s = 14.33 min written',  '860 seconds = 14.33 minutes' in S)
for n,t in files.items():
    for m in re.finditer(r'14\.4\b',t):
        print('INFO 14.4 in',n,':',t[max(0,m.start()-70):m.end()+30].replace('\n',' '))
    for m in re.finditer(r'14\.33',t):
        print('INFO 14.33 in',n,':',t[max(0,m.start()-50):m.end()+20].replace('\n',' '))
chk('3.90-3.10=0.80 not over 0.81',D('3.90')-D('3.10')==D('0.80') and D('0.80')<=D('0.81'))
chk('4.00-3.10=0.90 over',D('4.00')-D('3.10')>D('0.81'))
chk('13.00 ok (<=13.21), 13.50 not',D('13.00')<=D('13.21') and D('13.50')>D('13.21'))
chk('sheet PRICE_IN/OUT/PROGRAM/TOKENS settings','PRICE_IN_CENTS = 300' in S and 'PRICE_OUT_CENTS = 1500' in S and 'PROGRAM_LIMIT_CENTS = 1321' in S and 'TOKENS_IN = 40000' in S and 'TOKENS_OUT = 10000' in S)
chk('sheet DEADLINE 2026-11-23T18:29:00Z is Mon',dt.date(2026,11,23).weekday()==0)
chk('sheet date Mon 16 Nov 2026',dt.date(2026,11,16).weekday()==0)
chk('Wed 18 Nov, Wed 25 Nov',dt.date(2026,11,18).weekday()==2 and dt.date(2026,11,25).weekday()==2)
# ps / ls examples times between earliest key 11:00 and latest start 11:30, and ls before ps
chk('example times 11:06:55 < 11:08:07 <= 11:30 and >=11:00', T('11:00')<=T('11:06:55')<T('11:08:07')<=T('11:30'))
# every "UTC" time without IST pair in all files (info)
for n,t in files.items():
    for m in re.finditer(r'\b\d\d:\d\d(?::\d\d)? UTC\b(?! = \d\d:\d\d(?::\d\d)? IST)',t):
        print('INFO lone UTC time',n[:16],'|',t[max(0,m.start()-50):m.end()+30].replace('\n',' '))
print('FAILS:',fail)
