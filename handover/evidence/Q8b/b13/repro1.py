import sys, random, importlib, itertools
R = importlib.import_module("hadavin_sdk.guard.redact")
print("module:", R.__file__, file=sys.stderr)
sys.path.insert(0, "/home/user/build/b13-notes")
A = "xkvmzwhtrpnqbdfglscyaeuJQKZ"
def val(seed, n=20):
    r = random.Random(seed); return "".join(r.choice(A) for _ in range(n))
pairs = [("pass","session"),("access","sessid"),("access","secret"),("pass","sas_token"),("client","token"),("secret","token"),("pass","sas"),("key","credential"),("access","session")]
pairs += [("xpass","session"),("access","session")]
res = []
for a,b in pairs:
    for sep in ("=", ": ", "='"):
        v = val(hash((a,b,sep))&0xffff)
        # glue: a + (suffix overlap)
        for k in range(1, min(len(a),len(b))+1):
            pass
        name = a+b
        text = f"{name}{sep}{v}"
        out = R.redact(text).text
        res.append((name, sep, v[:8] in out or v[-8:] in out))
# overlap joins: suffix of a == prefix of b
words = ["pass","pwd","secret","access","account","shared","private","api","auth","sas","key","cert","sessid","phpsessid","jsessionid","connect","client","credential","token","signing","encryption","session","bearer","protection"]
n=0; bad=[]
for a in words:
    for b in words:
        for k in range(1, min(len(a),len(b))):
            if a.endswith(b[:k]):
                joined = a + b[k:]
                for sep in ("=", ": "):
                    v = val(n); n+=1
                    out = R.redact(f"{joined}{sep}{v}").text
                    if v[:8] in out: bad.append(joined+sep)
print("overlap joins tried", n, "readable", len(bad), sorted(set(bad))[:40])
