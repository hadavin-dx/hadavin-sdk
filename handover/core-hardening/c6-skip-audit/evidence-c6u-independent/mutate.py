import re,sys,os,subprocess,json
BASE=sys.argv[1]; OUT=sys.argv[2]; VER=sys.argv[3]
t0=open(BASE,encoding='utf-8').read()
def rep(a,b,count=0): return ('rep',a,b,count)
M=[]  # (id, category, kind, spec)
def add(i,cat,fn): M.append((i,cat,fn))
def R(a,b,n=0):
    def f(t):
        if a not in t: return None
        return t.replace(a,b) if n==0 else t.replace(a,b,n)
    return f
def rx(p,b,flags=0,n=0):
    def f(t):
        if not re.search(p,t,flags): return None
        return re.sub(p,b,t,count=n,flags=flags)
    return f
# counts
add('M01','count',R('96 rows','97 rows'))
add('M02','count',R('READY (49','READY (48'))
add('M03','count',R('ON DEFAULT (38','ON DEFAULT (39'))
add('M04','count',R('WAITS FOR A CHECK (3','WAITS FOR A CHECK (2'))
add('M05','count',R('WAITS FOR THE OWNER (6','WAITS FOR THE OWNER (5'))
add('M06','count',R('87 wave 1 rows to 10 files','88 wave 1 rows to 10 files'))
add('M07','count',R('This box holds 2381 words','This box holds 2380 words'))
add('M08','count',R('This box holds 2381 words','This box holds 2499 words'))
add('M09','count',lambda t: t.replace('This box holds 2381 words;','This box holds 2381 words; '+' '.join(['filler']*150)+';',1))
add('M10','count',R(' This box holds 2381 words; detail moved out of it, nothing deleted, is in section 1c.',''))
add('M11','count',rx(r'^(\| 5 \| NOT APPLIED; )ready',r'\1on the default of L-CARD',re.M))
add('M12','count',rx(r'^\| 50 \| NOT APPLIED[^\n]*\n','',re.M))
add('M13','count',lambda t: (lambda m: t.replace(m.group(0),m.group(0)+m.group(0),1))(re.search(r'^\| 50 \| NOT APPLIED[^\n]*\n',t,re.M)))
add('M14','count',R('(91 of 96 rows name files this branch does not hold)','(all rows name files this branch holds)'))
add('M15','count',R('applies the 87 wave 1 rows to 10 files','applies the 87 wave 1 rows to 12 files'))
add('M16','count',R('Total 90 words','Total 91 words'))
add('M17','count',R('line 2 (35 words)','line 2 (36 words)'))
add('M18','count',R('about 36 s, budget 40 s','about 36 s, budget 35 s'))
add('M19','count',lambda t: t.replace('The made-up name and e-mail address sent to n8n may stay','The made-up name and e-mail address sent to n8n may very often stay',1))
# safe defaults reversed
add('D01','default-rev',R('| L-CARD | Does the closing card stay as the last card of the video? | Yes. |','| L-CARD | Does the closing card stay as the last card of the video? | No. |'))
add('D02','default-rev',R("(an estimate no data of this take backs)? | Yes, cut. |","(an estimate no data of this take backs)? | No, keep. |"))
add('D03','default-rev',R('| (a). |','| (b). |',1))
add('D04','default-rev',R("instead of the cut number? | No. |","instead of the cut number? | Yes. |"))
add('D05','default-rev',R('| No; both stay in the file, marked not for the page. |','| Yes; both go on the page. |'))
add('D06','default-rev',R('| No (rows 90, 91 edit only the decision file). |','| Yes (rows 90, 91 edit viewer text). |'))
add('D07','default-rev',R('| OPEN (OWNER ONLY). Until he answers, the builder keeps failed runs unsaved','| Yes. Until he answers, the builder saves failed runs'))
add('D08','default-rev',R('| As answered. |','| Yes, the take deletes contacts. |'))
add('D09','default-rev',R('ANSWERED by you: no, never.','ANSWERED by you: yes, sometimes.'))
add('D10','default-rev',R('| Yes, they count as public.','| No, they do not count as public.'))
add('D11','default-rev',R('| none. No row puts the 45-second limit sentence on the card','| 1. A row puts the 45-second limit sentence on the card'))
add('D12','default-rev',R('I do not approve it.','I approve it.'))
add('D13','default-rev',R('G12 OPEN, so card line 1','G12 CLOSED, so card line 1'))
add('D14','default-rev',R('does not approve the lease wording','approves the lease wording'))
add('D15','default-rev',R('runs no check, spends nothing, imports nothing into n8n','runs checks, spends up to US$5, imports flows into n8n'))
add('D16','default-rev',R('NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE.','EVERYTHING IN THIS REPORT HAS BEEN APPLIED TO ALL FILES.'))
add('D17','default-rev',R('It changes no running n8n.','It changes the running n8n.'))
add('D18','default-rev',R('the take script has NO delete call','the take script has a delete call'))
add('D19','default-rev',R('a HubSpot identity with archive_contacts \'no\'','a HubSpot identity with archive_contacts \'yes\''))
add('D20','default-rev',R('NOT APPLIED; ready','APPLIED; ready',1))
# sentence removal
add('S01','delete',R(" PUBLIC POST = your phrase in ORDERS.md ('the lease sentence stays out of the public post').",''))
add('S02','delete',R("Does 'public post' (your answer: the lease sentence stays out of it) include","Does 'public post' include"))
add('S03','delete',R("'no, the lease sentence stays out of the public post'","''"))
add('S04','delete',R(" Those words are filmed only after your written approval; otherwise you cut them by hand.",''))
# times / dates
add('T01','time',R('18:29 UTC = 23:59 IST','18:29 UTC = 23:29 IST'))
add('T02','time',R('18:04 UTC = 23:34 IST','18:04 UTC = 23:04 IST'))
add('T03','time',R('the latest start 18:04 UTC = 23:34 IST','the latest start 18:14 UTC = 23:34 IST'))
add('T04','time',R('Mon 23 Nov','Tue 23 Nov'))
add('T05','time',R('Wed 18 Nov','Thu 18 Nov'))
add('T06','time',R('Wed 25 Nov 2026','Fri 25 Nov 2026'))
add('T07','time',R('2026-11-17T00:10:00 IST','2026-11-17T00:40:00 IST'))
add('T08','time',R('(written 18:11:46 UTC = 23:41:46 IST)','(written 18:11:46 UTC = 23:11:46 IST)',1))
add('T09','time',R('Mon 23 Nov 2026','Mon 24 Nov 2026'))
add('T10','time',R('the money stop is 18:29 UTC','the money stop is 18:39 UTC'))
add('T11','time',R('the owner cancels the paid key by 18:19 UTC = 23:49 IST','the owner cancels the paid key by 18:19 UTC = 23:59 IST'))
# status
add('V01','status',R('UNVERIFIED','VERIFIED'))
add('V02','status',R('UNVERIFIED','VERIFIED',1))
add('V03','status',R('(the take script\'s identity; UNVERIFIED,','(the take script\'s identity; VERIFIED,'))
add('V04','status',R('equality with the real files is UNVERIFIED','equality with the real files is verified'))
add('V05','status',R('ASSUMPTION, never checked','CHECKED'))
add('V06','status',R('nothing in this report is verified','everything in this report is verified') )
# secret / email shapes (built from parts at run time)
em='jane.doe'+chr(64)+'mail'+chr(46)+'example'+chr(46)+'org'
ak='AK'+'IA'+'ZXCVBNMASDFGHJKL'
gh='gh'+'p_'+'a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8'
sk='sk'+'-ant-'+'api03-'+'AbCdEfGhIjKlMnOpQrStUvWxYz0123456789'
add('X01','shape',lambda t: t.replace('## 6. The contact gate','Contact: '+em+'\n\n## 6. The contact gate',1))
add('X02','shape',lambda t: t.replace('## 6. The contact gate','Key: '+ak+'\n\n## 6. The contact gate',1))
add('X03','shape',lambda t: t.replace('## 6. The contact gate','Token: '+gh+'\n\n## 6. The contact gate',1))
add('X04','shape',lambda t: t.replace('## 6. The contact gate','Key: '+sk+'\n\n## 6. The contact gate',1))
add('X05','shape',lambda t: t.replace('## 6. The contact gate','Example key: AKIAIOSFODNN7EXAMPLE\n\n## 6. The contact gate',1))
add('X06','shape',lambda t: t.replace('0 FAILED','0 FAILED',1)+'\nowner: '+em+'\n')
env=dict(os.environ)
os.makedirs(OUT,exist_ok=True)
res=[]
for i,cat,fn in M:
    t=fn(t0)
    if t is None or t==t0:
        res.append((i,cat,'NOT-APPLIED','','')); continue
    p=os.path.join(OUT,i+'.md'); open(p,'w',encoding='utf-8').write(t)
    r=subprocess.run(['python3','-B','-I',VER,p],capture_output=True,text=True,env=env)
    out=r.stdout.strip().split('\n')
    summ=[l for l in out if l.startswith('SUMMARY')]
    s=summ[-1] if summ else (out[-1] if out else r.stderr[-200:])
    m=re.match(r'SUMMARY: (\d+) checks, (\d+) FAILED',s)
    nf=int(m.group(2)) if m else -1
    res.append((i,cat,'CAUGHT' if (r.returncode!=0) else 'MISSED',str(r.returncode)+' f='+str(nf), s[:150] ))
for r in res: print('\t'.join(r))
json.dump(res,open(OUT+'/results.json','w'))
