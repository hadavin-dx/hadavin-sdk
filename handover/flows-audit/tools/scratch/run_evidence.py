import subprocess, glob, os, re, sys, datetime, json
ROOT="/home/user/hadavin-sdk"; os.chdir(ROOT)
OUT="handover/flows-audit/evidence-1.md"
BASE="3bf5ae299cebac78963780895af5c585cab8473c"
sections=[]; table=[]
def run(cmd, shell=True, stdin=None):
    p=subprocess.run(cmd,shell=shell,capture_output=True,text=True,executable="/bin/bash")
    return p.returncode,(p.stdout+p.stderr)
def trunc(t):
    L=t.splitlines()
    if len(L)>60:
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
hdr=f"EVIDENCE RUNNER output, {date}, head {sha}\n\n"
tb="## Summary\n\ncheck | exit code\n--- | ---\n"+"\n".join(f"{a} | {b}" for a,b in table)+"\n"
open(OUT,"w").write(hdr+"\n".join(sections)+"\n"+tb)
print(tb)
