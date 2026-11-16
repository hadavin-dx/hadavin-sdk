import random
from hadavin_sdk import tools
ESC="\x1b"; HAND="Qx7mLp"+"-9vRtzKw2"; KEY="AKIA"+"IOSFODNN7EXAMPLE"
HID=[ESC+"[0m",ESC+"[31m",ESC+"(B","​","‮","⁦","\x07","%1b","&#27;","\\u001b",ESC]
WORDS=["ok","error","Company","user","log line","10.0.0.1","done"]
def piece(r):
    k=r.random()
    if k<.25: return r.choice(WORDS)
    if k<.45: return HAND
    if k<.55: return KEY
    if k<.75:
        s=r.choice([HAND,KEY]); i=r.randrange(1,len(s)); return s[:i]+r.choice(HID)+s[i:]
    return r.choice(HID)
r=random.Random(20261112); N=3000; w=0; rd=0; exc={}; first=None
for _ in range(N):
    t=" ".join(piece(r) for _ in range(r.randrange(2,9)))
    try: o=tools.prepare_output(t,{},4000,[HAND])
    except Exception as e:
        exc[type(e).__name__]=exc.get(type(e).__name__,0)+1; first=first or repr(t)[:200]; continue
    if o.replace(tools.MARKER,"").replace(tools.TRUNCATED,"").strip()=="" or "withheld" in o: w+=1
    if any(s[i:i+8] in o for s in (HAND,KEY) for i in range(len(s)-7)): rd+=1
print("tree",tools.__file__); print(f"N={N} withheld={w} ({100*w/N:.1f}%) readable_secret_window_in_output={rd} exceptions={exc} first_exc_input={first}")
r=random.Random(20261112); shown=0; kinds={}
for _ in range(N):
    t=" ".join(piece(r) for _ in range(r.randrange(2,9)))
    try: o=tools.prepare_output(t,{},4000,[HAND])
    except Exception: continue
    ws=[s[i:i+8] for s in (HAND,KEY) for i in range(len(s)-7) if s[i:i+8] in o]
    if ws:
        k=tuple(sorted(h for h in ("%1b","&#27;","\\u001b") if h in t)) or ("no-spelled-escape",)
        kinds[k]=kinds.get(k,0)+1
        if shown<3: shown+=1; print("EXAMPLE in=",repr(t)[:160],"\n        out=",repr(o)[:160])
print("readable by spelled-escape kind in input:",kinds)
