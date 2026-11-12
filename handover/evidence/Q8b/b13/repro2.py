import sys, random, importlib
R = importlib.import_module("hadavin_sdk.guard.redact")
A = "xkvmzwhtrpnqbdfglscyaeuJQKZ"
def val(r, n):
    return "".join(r.choice(A) for _ in range(n))
r = random.Random(7)
def tok(groups):
    parts = [r.choice(["Ab","Correct","Horse","Cd","Ef","Licence","Key","Zx"]) + "".join(r.choice("0123456789") for _ in range(r.choice([0,2]))) + "".join(r.choice("abcdefghjk") for _ in range(r.choice([2,5,8]))) for _ in range(groups)]
    return "-".join(parts)
tot=bad=0; cells=[]
for g in (1,2,3):
  for i in range(30):
    t = tok(g)
    for after in (" retried_after_backoff", "\nAccept: shown\n", " ok", "\n  next\nHost: x"):
        for pre in ("Authorization: ", "authorization=", '"Authorization": "'):
            text = pre + t + after
            out = R.redact(text).text
            tot+=1
            if t in out or t[:8] in out and len(t)>=8:
                bad+=1; cells.append(text[:60])
print("cells", tot, "token readable", bad, cells[:3])
