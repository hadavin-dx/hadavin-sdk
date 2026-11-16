#!/usr/bin/env python3
"""Extract every ``` fenced block from the two v10 documents; compile python blocks with compile() (and ast.parse,
wrapped in `def f(self):` when the fence is an indented method body fragment), run bash -n on sh/bash blocks.
Also report inline-code python-looking statements? (no: fences only)."""
import re, subprocess, sys, ast, tempfile, os
A="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/"
res=[]
for doc in ["CORE-PR-HANDOFF-v10.md","CORE-PR-HANDOFF-v10-other-tracks.md"]:
    txt=open(A+doc,encoding="utf-8").read().split("\n")
    i=0
    while i<len(txt):
        m=re.match(r"^(\s*)```(\w*)\s*$",txt[i])
        if m:
            lang=m.group(2); start=i+1; j=i+1
            while j<len(txt) and not re.match(r"^\s*```\s*$",txt[j]): j+=1
            body="\n".join(txt[start:j])
            res.append((doc,i+1,lang,body))
            i=j
        i+=1
print("fences found:",len(res))
for doc,ln,lang,body in res:
    print(f"--- {doc}:{ln} lang={lang!r} lines={body.count(chr(10))+1}")
    if lang in ("python","py",""):
        try:
            compile(body,"<fence>","exec"); print("   python compile: OK (module level)")
        except SyntaxError as e:
            print("   python compile as module: FAIL",e)
            wrapped="class C:\n"+"\n".join("    "+l for l in body.split("\n"))
            try:
                compile(wrapped,"<fence>","exec"); print("   python compile wrapped in class: OK")
            except SyntaxError as e2:
                print("   python compile wrapped in class: FAIL",e2)
        # names used but undefined (informational)
    elif lang in ("sh","bash","shell"):
        with tempfile.NamedTemporaryFile("w",suffix=".sh",delete=False) as f: f.write(body); p=f.name
        r=subprocess.run(["bash","-n",p],capture_output=True,text=True); print("   bash -n rc",r.returncode,r.stderr[:200]); os.unlink(p)
    else:
        print("   (not code we compile)")
