import subprocess, os, random, itertools, tempfile
G="/tmp/work/sn-v4"
S="/tmp/demo-lead/handover/demo/sonar/"
V4="/tmp/work/nodemo-ci-job-v4.patch" if not os.path.exists(S+"nodemo-ci-job-v4.patch") else S+"nodemo-ci-job-v4.patch"
L=[l.strip() for l in open("/tmp/work/nm4-list.txt") if "ci-job-v3" not in l]+[S+"nodemo-optional-hygiene-repo-v4.patch"]
nm=lambda p: os.path.basename(p)
idx=tempfile.mktemp()
def seq(order,base):
    env=dict(os.environ,GIT_INDEX_FILE=idx)
    subprocess.run(["git","read-tree",base],cwd=G,env=env,check=True)
    return [subprocess.run(["git","apply","--cached",p],cwd=G,env=env,capture_output=True,text=True).returncode==0 for p in order]
print("== v4 alone");
for b in ("db54e13","9c53207"): print(b, seq([V4],b))
print("== on db54e13 + P1 v3.2 + P2 v2.1 (applied in turn):", seq([L[0],L[5],V4],"db54e13"))
print("== on 9c53207 with fix-v3, isort, optional-v4, then v4 in each position:")
for perm in itertools.permutations([S+"nodemo-fix-v3.patch",S+"nodemo-ruff-isort.patch",S+"nodemo-optional-hygiene-repo-v4.patch",V4]):
    r=seq(list(perm),"9c53207"); print([nm(p) for p in perm][:4].index(nm(V4)),r) if not all(r) else None
print("   (silence = all 24 orders applied)")
print("== v4 vs v3 (expected conflict: same new file):", seq([S+"nodemo-ci-job-v3.patch",V4],"db54e13"))
print("== pairs with v4 on db54e13")
bad=[]
for p in L:
    for o in ([p,V4],[V4,p]):
        r=seq(o,"db54e13")
        base=seq([p],"db54e13")[0]
        if not all(r) and base: bad.append((nm(o[0]),nm(o[1]),r))
print("pairs where v4 breaks a patch that applies alone:",bad)
random.seed(29); ok=0; fail=0
for i in range(300):
    o=L[:]; random.shuffle(o)
    a=o.index(L[0]); b=o.index(L[1])
    if a>b: o[a],o[b]=o[b],o[a]
    pos=random.randint(0,len(o)); o2=o[:pos]+[V4]+o[pos:]
    r=seq(o2,"db54e13")
    if all(r): ok+=1
    else: fail+=1; print("FAIL",[nm(p) for p in o2],r)
print("300 random orders (v3.2 before delta), v4 anywhere, 11 patches: all applied",ok,"failed",fail)
