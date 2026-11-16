import ast, pathlib, random, sys
from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
root = pathlib.Path("tests")
files = ["warden_port/test_gate.py","warden_port/test_gate_render.py","warden_port/test_gate_review2.py","warden_port/test_gate_review3.py","test_g4_parity.py","test_k5_round9.py","test_k5_round11.py","test_p5p6_followups.py"]
lits=set()
for f in files:
    p=root/f
    if not p.exists(): continue
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Constant) and isinstance(n.value,str) and len(n.value)>2:
            lits.add(n.value)
ESC=chr(27)
extra=["password=Tq7mZ4xKp2Vb9Lr3NcW8dYh6uJs then Tq7mZ**4xKp2Vb9Lr3NcW8dYh6uJs**", "key AKIA**IOSFODNN7EXAMPLE** here", "AKIA"+ESC+"[0mIOSFODNN7EXAMPLE", "run `kubectl delete pod x`\n## head", "&lt;!channel&gt; evil.com"]
rng=random.Random(1)
pool=list(lits)+extra
alph=list("ab *_~`<>#-1.\n\r&;:/@")+[ESC,"​","́","\x08"]
for i in range(2000):
    pool.append("".join(rng.choice(alph) for _ in range(rng.randint(1,40))))
bad=0; badph=0
for x in pool:
    a=channel._neutralise(x); b=channel._neutralise(a)
    if a!=b:
        bad+=1
        if bad<=5: print("NONIDEM", repr(x)[:80], "|", repr(a)[:80], "|", repr(b)[:80])
    # placeholder survival
    out=runmap.redact_text(x, channel._seeded(x), neutralise=channel._neutralise)
    phs=set(runmap.PLACEHOLDER.findall(out))
    n2=channel._neutralise(out)
    if set(runmap.PLACEHOLDER.findall(n2))!=phs:
        badph+=1
        if badph<=3: print("PH", repr(out)[:80], repr(n2)[:80])
print("inputs",len(pool),"non-idempotent",bad,"placeholder-changed",badph)
