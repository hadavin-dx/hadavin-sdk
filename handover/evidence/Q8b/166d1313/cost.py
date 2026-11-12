import sys, time, random, json
src, mode = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
from hadavin_sdk.guard.redact import redact
def hostile(n):
    rnd = random.Random(5); parts = []; size = 0
    al = "abcdefghijklmnopqrstuvwxyz0123456789"
    pieces = [lambda: "Authorization: Basic" + " " * rnd.randint(1, 200) + "".join(rnd.choice(al) for _ in range(rnd.randint(8, 60))) + "\n",
              lambda: "Authorization: Digest a=b,\n" + "".join(" f=\"%s\",\n" % "".join(rnd.choice(al) for _ in range(20)) for _ in range(rnd.randint(1, 30))),
              lambda: "Token" + "\n" * rnd.randint(1, 50) + "x" * rnd.randint(1, 80) + "\n",
              lambda: "bypass compass overpass cookiejar possession_id " + "pass" * rnd.randint(1, 30) + "\n",
              lambda: "".join(rnd.choice(al) for _ in range(rnd.randint(100, 2000))) + " ",
              lambda: " " * rnd.randint(50, 500) + "\r\n" * rnd.randint(1, 10),
              lambda: "key=" + "".join(rnd.choice(al) for _ in range(rnd.randint(5, 40))) + "; secret: " + "a.b~c:d-" * rnd.randint(1, 10) + "\n"]
    while size < n:
        s = rnd.choice(pieces)(); parts.append(s); size += len(s)
    return "".join(parts)[:n]
def prose(n):
    rnd = random.Random(6)
    w = "the quick brown fox jumps over a lazy dog while compass and overpass encompass possession of every passage in the cookie jar near the bypass road and the token booth".split()
    out = []; size = 0
    while size < n:
        s = " ".join(rnd.choice(w) for _ in range(rnd.randint(6, 16))) + rnd.choice([".\n", ". ", ", "]); out.append(s); size += len(s)
    return "".join(out)[:n]
redact("warm up Authorization: Basic abcdefgh12345678 ok")
sizes = [int(x) for x in sys.argv[3].split(",")]
res = {}
for n in sizes:
    t = (hostile if mode == "hostile" else prose)(n)
    ts = []
    for _ in range(int(sys.argv[4])):
        a = time.perf_counter(); redact(t); ts.append(round(time.perf_counter() - a, 3))
    res[n] = ts
print(json.dumps(res))
