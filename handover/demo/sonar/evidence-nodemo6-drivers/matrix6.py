import subprocess, os, random, itertools, sys, tempfile
G="/tmp/work/sn-v5/gh"
D="/tmp/demo-lead/handover/demo/"
V5="/tmp/work/sn-v5/nodemo-optional-hygiene-repo-v5.patch"
BASE=sys.argv[1]; N=int(sys.argv[2])
L=[D+p for p in ["sonar/sonar-p1-quickwins-v3.2.1-delta.patch","sonar/sonar-p1-quickwins-v3.2.2-delta.patch","sonar/sonar-p2-regex-http-bug-v2.2-delta.patch","sonar/sonar-p2-regex-http-bug-v2.3-delta.patch","sonar/sonar-p2-regex-optional.patch","sonar/sonar-p2-feed-optional.patch","merge-ready/sonar-yaml-test-trimmed-v2.patch","semgrep/semgrep-on-db54e13-v5.1.patch","sonar/nodemo-ci-job-v4.patch","skips/crlf-guard-v7.1.patch"]]
names={p:os.path.basename(p) for p in L+[V5]}
idx=tempfile.mktemp(); env=dict(os.environ,GIT_INDEX_FILE=idx)
def seq(order):
    subprocess.run(["git","read-tree",BASE],cwd=G,env=env,check=True)
    return [subprocess.run(["git","apply","--cached",p],cwd=G,env=env,capture_output=True).returncode==0 for p in order]
print("base",BASE,"others",len(L),"| v5 alone:",seq([V5])[0])
print("alone:",{names[p]:seq([p])[0] for p in L})
bad=[]
for o in L:
    for a,b in ((o,V5),(V5,o)):
        r=seq([a,b]); oa=seq([o])[0]
        if oa and not all(r): bad.append((names[a],names[b],r))
print("ordered pairs with v5 where v5 breaks a patch that applies alone:",len(bad)); [print("  ",x) for x in bad]
# crlf v7.1 in both orders with v5 (explicit)
print("crlf-v7.1 then v5:",seq([L[-1],V5]),"| v5 then crlf-v7.1:",seq([V5,L[-1]]))
random.seed(7); d=0; vok=0
for i in range(N):
    o=L[:]; random.shuffle(o); pos=random.randint(0,len(o)); o2=o[:pos]+[V5]+o[pos:]
    r0=seq(o); r2=seq(o2); r2n=[x for x,p in zip(r2,o2) if p!=V5]
    if r2[pos]: vok+=1
    if not r2[pos] or r2n!=r0:
        d+=1
        if d<=5: print("DIFF",[names[p] for p in o2],r0,r2)
print("random orders",N,"v5 applied",vok,"diffs (others' results differ from the same order without v5):",d)
