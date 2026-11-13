import re,subprocess,os,glob
code="\n".join(open(p,errors="replace").read() for p in subprocess.run(["git","ls-files"],capture_output=True,text=True).stdout.split() if os.path.isfile(p) and not p.endswith((".png",".lock")) and not p.startswith(("docs/","contract.md","README.md","versions.md","SECURITY.md")))
files=set(subprocess.run(["git","ls-files"],capture_output=True,text=True).stdout.split())
bad=[];n=0
for l in open("/home/user/hadavin-sdk/handover/demo3/evidence/raw/q9-added-lines.txt"):
    loc,_,t=l.partition(": ")
    if not loc.split(":")[0].endswith(".md"): continue
    for tok in set(re.findall(r"`([^`\n]+)`",t)):
        n+=1
        m=re.match(r"^((?:tests|src|scripts|docs|load_tools|demo_only|tools|n8n|\.github)/[\w./\-]+?)(?:::(\w+))?$",tok)
        if m:
            if m.group(1) not in files and not os.path.exists(m.group(1)): bad.append((loc,tok,"path missing"))
            continue
        if re.match(r"^test_\w+$",tok):
            if not re.search(r"def "+tok+r"\b",code): bad.append((loc,tok,"test def missing"))
            continue
        if re.match(r"^[A-Z][A-Z0-9_]{4,}$",tok):
            if not re.search(r"(?<![A-Za-z0-9_])"+tok+r"(?![A-Za-z0-9_])",code): bad.append((loc,tok,"CAPS not in code/tests"))
            continue
        if re.match(r"^[\w.]+\(\)$|^[a-z_]+\.[a-z_.]+$|^_[a-z_]\w+$|^[A-Z]\w+\.\w+$",tok):
            last=re.split(r"[.()]+",tok.rstrip("()"))[-1]
            if len(last)>3 and not re.search(r"(?<![A-Za-z0-9_])"+last+r"(?![A-Za-z0-9_])",code): bad.append((loc,tok,"identifier not in code/tests"))
print(n,"tokens;",len(bad),"not found");[print(b) for b in bad]
