"""P10: is defang_text a fixed point on the final card? usage: PYTHONPATH=<tree>/src python p10_fixpt.py"""
import sys
sys.argv = ["x", "A"]
exec(open("p10_props.py").read().split("which = ")[0])
xs = gen("TXT-A", A, 2000)
f = [x for x in xs if gate.defang_text(channel.clean(x)) != channel.clean(x)]
print("clean(x) not fixed by defang_text:", len(f))
for x in f[:6]:
    c = channel.clean(x); d = gate.defang_text(c)
    i = next(i for i in range(len(c)) if c[i] != d[i]); print(repr(c[max(0,i-30):i+30]), "=>", repr(d[max(0,i-30):i+34]))
