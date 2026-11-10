"""P10: round trip on 2,000 TXT-B texts with len(clean) <= 2900. usage: PYTHONPATH=<tree>/src python p10_rt.py
(1) first pass, card is a fixed point of the redactor: redact_text(a with [.] read as ., map seeded with a's placeholders) adds no EMAIL or HOSTNAME placeholder;
(2) b == a, or b shows no fixture secret that a did not show. Prints counts and the shortest failing inputs."""
import re, sys
sys.argv = ["x", "B"]
exec(open("p10_props.py").read().split("which = ")[0])
PHK = re.compile(r"<([A-Z][A-Z0-9]*)_\d+>")
def fixed_point_new(a):
    u = a.replace("[.]", ".")
    seeded = runmap.RunMap({ph: "\0seed" + ph for ph in (m.group(0) for m in runmap.PLACEHOLDER.finditer(u))})
    out = runmap.redact_text(u, seeded)
    return [m.group(0) for m in runmap.PLACEHOLDER.finditer(out) if m.group(0) not in u and m.group(1) in ("EMAIL", "HOSTNAME")]
xs = gen("TXT-B", B, 2000)
n = 0; f1 = []; f2 = []; diff = 0
SECRETS = (SV_B, EM)
for x in xs:
    a = channel.clean(x)
    if len(a) > 2900: continue
    n += 1
    if fixed_point_new(a): f1.append(x)
    b = second(a)
    if b != a:
        diff += 1
        if any(s in b and s not in a for s in SECRETS): f2.append(x)
print("texts", n, "| first-pass fixed-point failures", len(f1), "| b != a", diff, "| b shows a secret a did not", len(f2))
for x in sorted(f1, key=len)[:3]:
    a = channel.clean(x); print("MIN1", repr(x)[:120], "->", repr(a)[:140], fixed_point_new(a))
for x in xs:
    a = channel.clean(x)
    if len(a) <= 2900 and second(a) != a:
        print("DIFF a:", repr(a)[:200]); print("     b:", repr(second(a))[:200]); print("     x:", repr(x)[:200])
