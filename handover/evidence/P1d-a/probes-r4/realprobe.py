import sys, re, importlib
sys.argv=[sys.argv[0], sys.argv[1], "fix"]
exec(open("probe.py").read().split("SV_A=")[0])
sys.path.insert(0,".")
from real import REAL
P=re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")
bad=0
for line, secs in REAL:
    exp=line
    for s in secs: exp=exp.replace(s,"<P>",1)
    for path,f in (("model",lambda t: runmap.redact_text(t, runmap.RunMap())),("card",channel.clean)):
        out=P.sub("<P>", f(line)).replace("[.]",".").replace("​","")
        if out!=exp: bad+=1; print("MISMATCH",path,repr(line),"->",repr(out),"exp",repr(exp))
print("lines",len(REAL),"mismatches",bad)
