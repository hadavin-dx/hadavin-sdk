import re,sys,hashlib
H='/home/user/hadavin-sdk/handover/core-hardening/'
src=open(H+'inputs/plan-wp6-resmoke-v5.md').read()
md=open(H+'paste-check/plan-v10-real-v5-edits.md').read()
print('plan list sha256',hashlib.sha256(open(H+'paste-check/plan-v10-real-v5-edits.md','rb').read()).hexdigest())
print('input sha256 prefix before',hashlib.sha256(open(H+'inputs/plan-wp6-resmoke-v5.md','rb').read()).hexdigest()[:16])
hdr=re.search(r'This list has (\d+) edits',md).group(1)
blocks=re.findall(r'## Edit (\d+): .*?\n~~~~old\n(.*?)\n~~~~\n~~~~new\n(.*?)\n~~~~\n',md,re.S)
print('header says',hdr,'parsed',len(blocks))
cur=src; bad=0; last=-1
for i,o,n in blocks:
    c=src.count(o); pos=src.index(o) if c else -1
    ok = c==1 and cur.count(o)==1 and pos>last
    print('edit',i,'occurs in original',c,'in current',cur.count(o),'order ok',pos>last,'OK' if ok else 'FAIL')
    bad+= (not ok); last=pos
    cur=cur.replace(o,n,1)
open(sys.argv[1],'w').write(cur)
print('lines before',src.count('\n'),'after',cur.count('\n'),'fails',bad)
print("input sha256 prefix after",hashlib.sha256(open(H+"inputs/plan-wp6-resmoke-v5.md","rb").read()).hexdigest()[:16])
sys.exit(1 if bad or int(hdr)!=len(blocks) else 0)
