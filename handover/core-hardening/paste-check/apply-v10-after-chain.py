import re,sys
H='/home/user/hadavin-sdk/handover/core-hardening/paste-check/'
rx=r'## Edit (\d+): .*?\n~~~~old\n(.*?)\n~~~~\n~~~~new\n(.*?)\n~~~~\n'
rx2=r'## Edit (\d+) \(corrected[^\n]*\n~~~~old\n(.*?)\n~~~~\n~~~~new\n(.*?)\n~~~~\n'
old=re.findall(rx,open(H+'plan-v10-real-v5-edits.md').read(),re.S)
new={i:(o,n) for i,o,n in re.findall(rx2,open(H+'plan-v10-corrections-after-chain.md').read(),re.S)}
print(len(old),sorted(new,key=int)); cur=open(sys.argv[1]).read(); bad=[]
for i,o,n in old:
    if i in new: o,n=new[i]
    if cur.count(o)!=1: bad.append((i,cur.count(o)))
    else: cur=cur.replace(o,n,1)
print('failing',bad); open(sys.argv[2],'w').write(cur)
