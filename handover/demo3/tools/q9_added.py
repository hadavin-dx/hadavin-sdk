import subprocess,re,sys
d=subprocess.run(["git","diff","f3c39cf8","HEAD","-U0"],capture_output=True,text=True).stdout
f=None;ln=0
for l in d.splitlines():
    if l.startswith("+++ "): f=l[6:]; continue
    m=re.match(r"@@ -\S+ \+(\d+)",l)
    if m: ln=int(m.group(1)); continue
    if l.startswith("+") and not l.startswith("+++"):
        t=l[1:]
        if re.search(r"\d|`|\.py|\.md",t): print(f"{f}:{ln}: {t.strip()[:330]}")
        ln+=1
