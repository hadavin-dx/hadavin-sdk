import re,sys
t=open(sys.argv[1]).read(); W=sys.argv[2]
out=[]
for i,m in enumerate(re.finditer(r'^```(\w*)\n(.*?)^```',t,re.M|re.S)):
    open(f'{W}/blocks/b{i:02d}.sh','w').write(m.group(2))
    pre=t[:m.start()].rstrip().split('\n')[-1][:90]
    out.append(f'b{i:02d}\t{m.group(1)}\t{pre}')
open(f'{W}/index.tsv','w').write('\n'.join(out)+'\n')
