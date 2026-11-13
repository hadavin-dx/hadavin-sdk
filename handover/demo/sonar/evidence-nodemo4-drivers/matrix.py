import subprocess, os, random, itertools, sys, tempfile
G="/tmp/work/nm4/base"
V4="/tmp/demo-lead/handover/demo/sonar/nodemo-optional-hygiene-repo-v4.patch"
L=[l.strip() for l in open("/tmp/work/nm4-list.txt")]
names={p:os.path.basename(p) for p in L+[V4]}
idx=tempfile.mktemp()
def seq(order):
    env=dict(os.environ,GIT_INDEX_FILE=idx)
    subprocess.run(["git","read-tree","db54e13"],cwd=G,env=env,check=True)
    res=[]
    for p in order:
        r=subprocess.run(["git","apply","--cached",p],cwd=G,env=env,capture_output=True,text=True)
        res.append(r.returncode==0)
    return res
base_cache={}
def solo(p):
    return seq([p])[0]
out=[]
bad=0
# pairs
allp=L+[V4]
solo_ok={p:solo(p) for p in allp}
for p,ok in solo_ok.items(): print("alone",names[p],ok)
pair_bad=[]
for a,b in itertools.permutations(allp,2):
    r=seq([a,b])
    if V4 in (a,b) and not all(r):
        # compare with other: does the non-v4 patch apply alone? 
        pair_bad.append((names[a],names[b],r))
    elif V4 not in (a,b) and not all(r):
        pass
print("pairs involving v4 failing:",len(pair_bad))
for x in pair_bad: print(x)
# random orders: v4 inserted vs same order without v4
random.seed(4)
cnt=0;diff=0
for i in range(300):
    o=L[:]; random.shuffle(o)
    pos=random.randint(0,len(o)); o2=o[:pos]+[V4]+o[pos:]
    r0=seq(o); r2=seq(o2)
    r2n=[x for x,p in zip(r2,o2) if p!=V4]
    v4ok=r2[pos]
    cnt+=1
    if not v4ok or r2n!=r0:
        diff+=1; print("ORDER DIFF",i,[names[p] for p in o2],r2)
print("random orders",cnt,"with v4 problem",diff)
# valid-order sample: v3.2 before delta
random.seed(7); ok_orders=0; badv=0
for i in range(300):
    o=L[:]; random.shuffle(o)
    a=o.index(L[0]); b=o.index(L[1])
    if a>b: o[a],o[b]=o[b],o[a]
    pos=random.randint(0,len(o)); o2=o[:pos]+[V4]+o[pos:]
    r=seq(o2)
    if all(r): ok_orders+=1
    else: badv+=1; print("FAIL valid order",[names[p] for p in o2],r)
print("valid orders (v3.2 before delta)",300,"all applied",ok_orders,"failed",badv)
