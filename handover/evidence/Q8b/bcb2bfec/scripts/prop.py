import random, string, collections
from lib import *
print("## import", path_src())
rng = random.Random(20261111)
prefixes = {"none": "", "word": "login failed for user ", "email": "bob.smith@example.com", "email sp": "bob.smith@example.com ", "host": "db01.corp.internal", "host sp": "db01.corp.internal ", "ip": "10.20.30.40", "url": "https://example.com/x ", "zwsp+email": "bob.smith@example.com​", "bearer": "Authorization: Bearer ", "bearer+email": "Authorization: Bearer bob.smith@example.com ", "json": '{"user": "a", ', "markdown": "# head\n> quote\n- item ", "ansi": "\x1b[31m", "uppercase email": "BOB@EXAMPLE.COM", "email dot": "bob@example.com.", "percent": "user%40example.com"}
keys = ["password", "passwd", "token", "secret", "api_key", "apikey", "client_secret", "access_token", "PASSWORD", "Token", "db_password", "auth_token", "private_key", "pwd"]
seps = ["=", ": ", " = ", "=\"", "='", "%3D", ":", "\t=\t", "\":\""]
suff = ["", " ok", ".", ", next", "\"", "'", "\nmore", " and more words"]
def secret():
    n = rng.randint(10, 22); a = string.ascii_letters + string.digits
    return "zq" + "".join(rng.choice(a) for _ in range(n)) + rng.choice("0123456789")
N = 3000
res = {"walk": collections.Counter(), "card": collections.Counter()}
bypfx = {"walk": collections.Counter(), "card": collections.Counter()}
examples = {"walk": [], "card": []}
for i in range(N):
    pn, p = rng.choice(list(prefixes.items())); k = rng.choice(keys); s = rng.choice(seps); sf = rng.choice(suff); S = secret()
    text = f"{p}{k}{s}{S}{sf}"
    rep = rng.random() < 0.5
    repeat = f"note: saw {S} again" if rep else None
    for path in ("walk", "card"):
        try:
            if path == "walk":
                recs = [{"message": text}] + ([{"message": repeat}] if rep else [])
                out = walk(recs); a_out = js(out[0]); r_out = js(out[1]) if rep else ""
                again = walk(out); idem = (again == out)
            else:
                a_o = clean(text); a_out = a_o; r_out = clean(repeat) if rep else ""
                idem = clean(a_o) == a_o
        except Exception as e:
            res[path]["exceptions"] += 1; examples[path].append(("EXC", text, repr(e))); continue
        a_read = readable(S, a_out)
        r_read = rep and readable(S, r_out)
        if a_read: res[path]["assignment_readable"] += 1; bypfx[path][pn] += 1; examples[path].append(("ASSIGN", text, a_out))
        elif r_read: res[path]["repeat_only_readable"] += 1
        if not idem: res[path]["not_idempotent"] += 1; examples[path].append(("NONIDEM", text, a_out))
        res[path]["texts"] += 1
for path in res:
    print(f"## {path}: {dict(res[path])}")
    print("   assignment-readable by prefix:", dict(bypfx[path]))
    for e in examples[path][:25]: print("   ", e[0], repr(e[1])[:110], "->", repr(e[2])[:130])
