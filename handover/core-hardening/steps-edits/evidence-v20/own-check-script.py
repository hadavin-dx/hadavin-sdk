import re,datetime as dt
from decimal import Decimal as D
D0='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
files=['OWNER-SHEET-v20.md','LEAD-RELEASE-NOTE-v4.md','v20-MAP.md','v20-OPEN-FOR-LEAD.md']
T={f:open(D0+f).read() for f in files}
print('price',(D(40000)*3+D(10000)*15)/D(10**6),'x3',((D(40000)*3+D(10000)*15)/D(10**6))*3,'sum',D('12.40')+D('0.81'))
def t(s):
    p=[int(x) for x in s.split(':')]+[0]; return dt.timedelta(hours=p[0],minutes=p[1],seconds=p[2])
def fmt(d):
    s=int(d.total_seconds())%86400; return '%02d:%02d:%02d'%(s//3600,s%3600//60,s%60)
n=0
for f,x in T.items():
    for m in re.finditer(r'(\d\d:\d\d(?::\d\d)?) UTC = (\d\d:\d\d(?::\d\d)?) IST',x):
        n+=1; a,b=m.groups(); r=fmt(t(a)+dt.timedelta(hours=5,minutes=30))
        ok=(r[:len(b)]==b); print('%-24s found %s UTC = %s IST  recomputed %s  %s'%(f,a,b,r,'OK' if ok else 'MISMATCH'))
print('pairs',n)
w=0
for f,x in T.items():
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* (\d{1,2}) Nov(?:ember)?( 2026)?',x):
        d=dt.date(2026,11,int(m.group(2))); r=d.strftime('%a'); w+=1
        print('%-24s found %s %s Nov  recomputed %s %s'%(f,m.group(1),m.group(2),r,'OK' if r==m.group(1) else 'MISMATCH'))
print('weekday mentions',w, 'Nov16', dt.date(2026,11,16).strftime('%A'))
we=t('18:29:00'); ls=we-dt.timedelta(seconds=860); print('latest start (program last start)',fmt(ls),'IST',fmt(ls+dt.timedelta(hours=5,minutes=30)))
for name,start in [('sample 11:30',t('11:30')),('limit case',ls)]:
    pass
# sample: LS 11:30 + 5+10+10=25 -> 11:55, +10 -> 12:05
print('sample alarm',fmt(t('11:30')+dt.timedelta(minutes=25)),'cancel-by',fmt(t('11:30')+dt.timedelta(minutes=35)))
# worst case on window end: LS=min(B, we-45min)
ls2=min(ls,we-dt.timedelta(minutes=45)); print('latest start at window end',fmt(ls2),'alarm',fmt(ls2+dt.timedelta(minutes=25)),'cancel-by',fmt(ls2+dt.timedelta(minutes=35)),'buffer to window end (min)',(we-(ls2+dt.timedelta(minutes=35))).seconds/60)
print('cancel-by IST',fmt(ls2+dt.timedelta(minutes=35)+dt.timedelta(hours=5,minutes=30)),'alarm IST',fmt(ls2+dt.timedelta(minutes=25)+dt.timedelta(hours=5,minutes=30)))
print('window IST',fmt(we+dt.timedelta(hours=5,minutes=30)),'post-by 15:00 UTC IST',fmt(t('15:00')+dt.timedelta(hours=5,minutes=30)),dt.date(2026,11,25).strftime('%a'))
print('cents: 3.00*100',3*100,'15*100',1500,'program limit 13.21 -> cents',int(D('13.21')*100),'per call cents calc',(40000*300+10000*1500)/1e6/100)
