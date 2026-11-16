import subprocess, glob, os, re, sys, datetime, json
ROOT="/home/user/hadavin-sdk"; os.chdir(ROOT)
OUT="handover/flows-audit/evidence-2.md"
BASE="3bf5ae299cebac78963780895af5c585cab8473c"
sections=[]; table=[]
def run(cmd, shell=True, stdin=None):
    p=subprocess.run(cmd,shell=shell,capture_output=True,text=True,executable="/bin/bash")
    return p.returncode,(p.stdout+p.stderr)
def trunc(t):
    L=t.splitlines()
    if len(L)>200:
        return "\n".join(L[:40])+f"\n[... TRUNCATED: {len(L)-50} lines omitted of {len(L)} ...]\n"+"\n".join(L[-10:])
    return t.rstrip("\n")
def rec(label,cmd,rc,out,tbl=True):
    sections.append(f"## {label}\n\nCommand: `{cmd}`\nExit code: {rc}\n\n```\n{trunc(out)}\n```\n")
    if tbl: table.append((label+" "+cmd,rc))
date=run("date -u")[1].strip(); sha=run("git rev-parse HEAD")[1].strip()
rc,o=run("date -u; git rev-parse HEAD; git status --porcelain"); rec("(0)","date -u; git rev-parse HEAD; git status --porcelain",rc,o)
for k,c in [("(a)","python3 handover/flows-audit/tools/check_counts.py"),("(b)","python3 handover/flows-audit/tools/check_names.py"),("(c)","python3 handover/flows-audit/tools/check_refs.py"),("(d1)","sh handover/flows-audit/tools/check_patches.sh")]:
    rc,o=run(c); rec(k,c,rc,o)
for p in sorted(glob.glob("handover/flows-audit/patches/*")):
    c=f"git apply --check {p}; echo $?"; rc,o=run(c); rec("(d2)",c,rc,o)
rc,o=run("python3 handover/flows-audit/tools/check_secrets.py"); rec("(e)","python3 handover/flows-audit/tools/check_secrets.py",rc,o)
c1="git status --porcelain"; rc,o=run(c1); rec("(f1)",c1,rc,o or "(empty)")
c2=f"git diff --stat {BASE} HEAD -- . ':!handover/flows-audit'"; rc,o=run(c2); rec("(f2)",c2,rc,o or "(empty)")
rc,o=run("python3 handover/flows-audit/tools/test_dump_nodes.py"); rec("(g)","python3 handover/flows-audit/tools/test_dump_nodes.py",rc,o)
c="python3 handover/flows-audit/tools/dump_nodes.py counts handover/demo | tail -3"; rc,o=run(c); rec("(h)",c,rc,o)
# (i)
files=[f for f in sorted(glob.glob("handover/demo/n8n-*/**/*.json",recursive=True)) if "/n8n-tests/" not in f and not f.startswith("handover/demo/n8n-tests/")]
files=[f for f in files if re.match(r"handover/demo/n8n-[^/]*/",f)]
bad=[];lines=[]
for f in files:
    rc,o=run(f"python3 handover/flows-audit/tools/dump_nodes.py check '{f}'")
    if rc!=0: bad.append(f); lines.append(f"{f} exit={rc}: {o.strip()[:300]}")
rec("(i)","for f in handover/demo/n8n-*/**/*.json (not n8n-tests): dump_nodes.py check <f>",len(bad),("\n".join(lines)+"\n" if lines else "")+f"files checked: {len(files)}; failures: {len(bad)}")
# (j)
F=open("handover/flows-audit/FINDINGS.md").read().splitlines()
frows=[l for l in F if l.startswith("| F-")]
out=[f"FINDINGS.md rows (^| F-): {len(frows)}"]
srcs=" ".join(l.split("|")[8] for l in frows if len(l.split("|"))>8)
lane_ids=[];tot=0
for fn in sorted(glob.glob("handover/flows-audit/lanes/*.findings.md")):
    ids=[re.match(r"\| (L[0-9a-z]+-[0-9]+) ",l).group(1) for l in open(fn).read().splitlines() if re.match(r"^\| L[0-9a-z]+-[0-9]+ ",l)]
    out.append(f"{fn}: {len(ids)}"); tot+=len(ids); lane_ids+=ids
out.append(f"lane findings rows total: {tot}")
missing=[i for i in lane_ids if not re.search(r"(?<![0-9A-Za-z-])"+re.escape(i)+r"(?![0-9])",srcs)]
out.append("lane ids not in FINDINGS.md sources column: "+(", ".join(missing) if missing else "none"))
rec("(j)","python (count rows, lane ids vs sources)",0,"\n".join(out),tbl=False)
table.append(("(j) python findings count",0))
# (k)
per={};tot=0
for l in open("handover/flows-audit/tools/out/counts.txt"):
    m=re.match(r"(\d+) (\S+)",l)
    if m:
        n=int(m.group(1)); d=m.group(2).split("/")[0]; per[d]=per.get(d,0)+n; tot+=n
k=[f"counts.txt lines (files): {sum(1 for _ in open('handover/flows-audit/tools/out/counts.txt'))}",f"counts.txt folders: {len(per)}",f"counts.txt total nodes: {tot}"]
k+= [f"  {d}: {n}" for d,n in sorted(per.items())]
rc,o=run("grep -noE '(52 files|655 nodes|525|130|40 files|11 folders)[^|]{0,60}' handover/flows-audit/FINDINGS.md")
k.append("FINDINGS.md matching claims:"); k.append(o)
rec("(k)","python (sum counts.txt per folder) + grep claims",0,"\n".join(k),tbl=False)
table.append(("(k) python counts",0))

# (m)
import shutil, json as J
R="handover/flows-audit/tools/scratch/rb2"; shutil.rmtree(R,ignore_errors=True)
GEN="handover/demo/n8n-mainframe/build_mainframe.py"
out=[]
for side in ("patched","unpatched"):
    d=f"{R}/{side}/handover/demo/n8n-mainframe"; os.makedirs(d)
    shutil.copy(GEN,d)
    if side=="patched":
        rc,o=run(f"cd {R}/patched && patch -p1 < {ROOT}/handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch"); out.append(f"patch -p1 exit {rc}\n{o}")
        mrc=rc
os.makedirs(f"{R}/repo",exist_ok=True); shutil.copy(GEN,f"{R}/repo/")
builds={}
if mrc==0:
    for side in ("patched","unpatched"):
        g=f"{R}/{side}/handover/demo/n8n-mainframe/build_mainframe.py"
        for kind in ("real","film"):
            od=f"{R}/out-{side}-{kind}"; os.makedirs(od)
            if kind=="real": c=f"MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 {g} {od} PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER"
            else: c=f"MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 {g} {od} PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45"
            rc,o=run(c); out.append(f"$ {c}\nexit {rc}\n{o}\nfiles: {sorted(os.listdir(od))}")
            builds[(side,kind)]=od
else:
    out.append("patch failed; stopped on this item")
def load(p):
    try: return J.load(open(p))
    except Exception as e: return {"nodes":[],"connections":{},"_err":str(e)}
def dang(w):
    names={n["name"] for n in w.get("nodes",[])}; bad=[]
    for src,v in w.get("connections",{}).items():
        if src not in names: bad.append(f"source {src}")
        for typ,outs in v.items():
            for o in outs:
                for c in (o or []):
                    if c["node"] not in names: bad.append(f"{src} -> {c['node']}")
    return bad
def find(od,key):
    r=[f for f in sorted(os.listdir(od)) if key in f and f.endswith(".json")]
    return r
for kind in ("real","film"):
  if (("patched",kind) in builds):
    for key in ("mf-form","mf-hook","mf-recovery","mf-sub-crm-mail"):
        pa=find(builds[("patched",kind)],key); un=find(builds[("unpatched",kind)],key)
        out.append(f"--- {kind} {key}: patched files {pa}, unpatched files {un}")
        for fa,fu in zip(pa,un):
            a=load(f"{builds[('patched',kind)]}/{fa}"); u=load(f"{builds[('unpatched',kind)]}/{fu}")
            an={n["name"]:n for n in a["nodes"]}; un_={n["name"]:n for n in u["nodes"]}
            out.append(f"{fa}: patched nodes {len(an)}, unpatched nodes {len(un_)}")
            out.append("  added: "+str(sorted(set(an)-set(un_))))
            out.append("  removed: "+str(sorted(set(un_)-set(an))))
            out.append("  params changed: "+str(sorted(n for n in set(an)&set(un_) if an[n].get("parameters")!=un_[n].get("parameters"))))
            out.append("  dangling patched: "+str(dang(a)))
            out.append("  dangling unpatched: "+str(dang(u)))
    # compare with saved
    saved=f"handover/demo/n8n-flows-{kind}-v5"
    for key in ("mf-form","mf-hook","mf-recovery","mf-sub-crm-mail"):
        ua=find(builds[("unpatched",kind)],key)
        sv=find(saved,key)
        out.append(f"--- unpatched {kind} vs saved {saved} {key}: gen {ua} saved {sv}")
        for fa,fs in zip(ua,sv):
            g=load(f"{builds[('unpatched',kind)]}/{fa}"); s=load(f"{saved}/{fs}")
            gn=[n["name"] for n in g["nodes"]]; sn=[n["name"] for n in s["nodes"]]
            out.append(f"  gen nodes {len(gn)}, saved nodes {len(sn)}; only in gen {sorted(set(gn)-set(sn))}; only in saved {sorted(set(sn)-set(gn))}")
rec("(m)","F-002 rebuild in scratch (patch -p1, build patched/unpatched real-v5/film-v5, compare)",0,"\n".join(out),tbl=False); table.append(("(m) F-002 rebuild",mrc))
# (n)
fs=["handover/demo/n8n-flows/mf_leads.sql","handover/demo/n8n-flows-v3/mf_leads.sql","handover/demo/n8n-flows-v4/mf_leads.sql"]
o=[]
for i in range(3):
    for j in range(i+1,3):
        rc,x=run(f"cmp {fs[i]} {fs[j]}; echo $?"); o.append(f"cmp {fs[i]} {fs[j]}: {x.strip()}")
for f in fs+["handover/flows-audit/patches/F-001-one-ddl.patch"]:
    rc,x=run(f"grep -c 'alert_sent\\|alert_token\\|alert_until\\|alert_attempts' {f}"); o.append(f"grep -c {f}: rc={rc} count={x.strip()}")
    rc,x=run(f"grep -n 'alert_sent\\|alert_token\\|alert_until\\|alert_attempts' {f}"); o.append(x)
rec("(n)","cmp pairs + grep counts",0,"\n".join(o),tbl=False); table.append(("(n) cmp/grep",0))
# (o)
for p in sorted(glob.glob("handover/flows-audit/patches/*.patch")):
    c=f"git apply --stat {p}"; rc,o=run(c); rec("(o)",c,rc,o)
# (p)
for c in ["git status --porcelain",f"git diff --stat {BASE} HEAD -- . ':!handover/flows-audit'"]:
    rc,o=run(c); rec("(p)",c,rc,o or "(empty)")

hdr=f"EVIDENCE RUNNER output (round 2), {date}, BASE {BASE}, head {sha}\n\n"
tb="## Summary\n\ncheck | exit code\n--- | ---\n"+"\n".join(f"{a} | {b}" for a,b in table)+"\n"
open(OUT,"w").write(hdr+"\n".join(sections)+"\n"+tb)
print(tb)
