from lib import *
print("## import", path_src())
V = "<made-up-value-B>"
LOGV = {"message": f"seen {V} here"}
def show(name, inp, out, secrets):
    print(f"[{name}] in={js(inp)[:200]}\n   out={js(out)[:260]}\n   readable={[s for s in secrets if readable(s, out)]}")
# F3 case folding: key words and Secret kind spelled with special letters
keyspell = {"ASCII password": "password", "ſ (U+017F) paſſword": "paſſword", "ſ in token (toĸen K-kra)": "toĸen", "İ (U+0130) in ApİKey": "ApİKey", "İ in SECRET key sEcrİt": "sİcret", "ı (U+0131) apıkey": "apıkey", "ı passwıord": "passwıord", "Kelvin K (U+212A) TOKEN": "TOKEN", "ſecret": "ſecret", "ſecret_key": "ſecret_key", "PASSWORD upper": "PASSWORD", "ß in paßword": "paßword", "fullwidth password": "ｐassword", "dotted capital İ Authorization": "Authorİzation"}
for n, k in keyspell.items():
    o = {k: V}; out = walk(o)
    c = clean(f"{k}={V}")
    show("F3 key " + n, o, {"walk": out, "card": c}, [V])
kinds = {"ASCII Secret": "Secret", "ſecret lower long s": "ſecret", "ſecret capital S": "ſECRET", "SECRET": "SECRET", "secret": "secret", "Secret + İ": "Sİcret", "Secret + ı": "Secretı", "Kelvin none": "SecretK", "Secret NBSP": "Secret ", "Secret ZWSP": "Sec​ret", "Secret NFKC fullwidth": "Ｓecret"}
for n, kd in kinds.items():
    sec = {"kind": kd, "data": {"UNLISTED": b64(V)}}
    out = walk([sec, LOGV])
    show("F3 kind " + n, sec, out, [V, b64(V)])
# 256 cap bypass: entries
for N in (255, 256, 257, 300, 1000):
    data = {f"E{i:04d}": b64(f"zqentry-{i:05d}-secretvalue") for i in range(N)}
    sec = {"kind": "Secret", "data": data}
    logs = [{"message": f"leak zqentry-{i:05d}-secretvalue"} for i in range(N)]
    try:
        out = walk([sec] + logs)
        repeats_readable = [i for i in range(N) if f"zqentry-{i:05d}-secretvalue" in js(out[1 + i])]
        under_key_readable = [k for k, v in out[0]["data"].items() if v == data[k]]
        print(f"[CAP entries N={N}] repeat copies readable={len(repeats_readable)} first={repeats_readable[:1]} last={repeats_readable[-1:]} ; values under own key unchanged={len(under_key_readable)}; fixed-mask entries={sum(1 for v in out[0]['data'].values() if v=='<SECRET_REDACTED>')}")
    except Exception as e: print(f"[CAP entries N={N}] EXC {type(e).__name__} {e}")
# 256-entry cap bypass: second Secret with same data split / spec mix / many Secrets (is the cap per Secret?)
data1 = {f"A{i:03d}": b64(f"zqsplitA-{i:04d}-valuexx") for i in range(256)}
data2 = {f"B{i:03d}": b64(f"zqsplitB-{i:04d}-valuexx") for i in range(256)}
secs = [{"kind": "Secret", "data": data1}, {"kind": "Secret", "data": data2}, {"kind": "Secret", "spec": {"data": data2}, "stringData": {f"S{i}": f"zqstr-{i:04d}-valuexxx" for i in range(300)}}]
logs = [{"message": f"leak zqsplitA-{i:04d}-valuexx zqsplitB-{i:04d}-valuexx"} for i in range(256)]
out = walk(secs + logs); t = js(out[3:])
print("[CAP two Secrets + spec] readable repeats:", sum(1 for i in range(256) if f"zqsplitA-{i:04d}-valuexx" in t), sum(1 for i in range(256) if f"zqsplitB-{i:04d}-valuexx" in t))
# value length cap under a credential key / in a Secret
for L in (254, 255, 256, 257, 300, 1000):
    v = "q" + "Zk9" * ((L - 1) // 3) ; v = v[:L]
    o = [{"password": v}, {"message": f"leak {v} end"}]
    out = walk(o)
    print(f"[CAP value length {L}] repeat readable={v in js(out[1])} key masked={out[0]['password'] != v}")
    sec = {"kind": "Secret", "data": {"UNLISTED": b64(v)}}
    out = walk([sec, {"message": f"leak {v} end"}])
    print(f"[CAP Secret entry length {L}] repeat readable={v in js(out[1])} key masked={out[0]['data']['UNLISTED'] != b64(v)}")
# spaces: 255-char value with spaces
v = ("alpha bravo " * 30)[:255].strip()
for L in (len(v),):
    o = [{"password": v}, {"message": f"leak {v} end"}]; out = walk(o)
    print(f"[CAP spaced value {L}] out_pw={js(out[0])[:100]} repeat={js(out[1])[:120]}")
