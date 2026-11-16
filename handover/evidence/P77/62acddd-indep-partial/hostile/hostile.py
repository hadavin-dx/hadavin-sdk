"""Hostile inputs for guard.redact.redact. All secrets are made up and built from parts. Prints counts only, never a secret."""
import os, sys, time
sys.path.insert(0, os.path.join(os.environ["WT"], "src"))
from hadavin_sdk.guard.redact import redact

def pieces(s, n=3):
    return {s[i:i+k] for k in range(n, len(s)+1) for i in range(len(s)-k+1)}

# text around the secret is fixed filler; filler pieces are excluded from the piece check
def run(label, text, secret, filler="log line: value is "):
    t = time.time(); out = redact(text).text; dt = time.time() - t
    whole = secret in out
    # pieces of the secret (>=3 chars) that appear in the output but not in the filler text
    base = redact(filler).text if filler else ""
    ps = [p for p in pieces(secret) if p in out and p not in base and p not in "[]<>_-REDACTED"]
    bad = whole or bool(ps)
    print(f"{label}: whole_leak={int(whole)} piece_leaks={len(ps)} secs={dt:.3f} {'OK' if not bad else 'NOT-OK'}", flush=True)
    return not bad

res = []
s1 = "AKIA" + chr(0x093E) + "IOSFODNN7EXAMPLE"
res.append(run("1 AKIA+Mc(U+093E)+rest", f"key={s1} end", s1))
s2 = "AKIAIOSFODNN7" + chr(0x02B0) + "EXAMPLE"
res.append(run("2 modifier letter U+02B0 inside", f"key={s2} end", s2))
s3 = chr(0x0391) + chr(0x0345) + "KIAIOSFODNN7EXAMPLE"
res.append(run("3 Greek Alpha+U+0345 start", f"key={s3} end", s3))
s4 = "sk-" + "a" * 10 + chr(0x0903) + "a" * 10
res.append(run("4 sk- with Mc U+0903", f"token {s4} end", s4))
# password with a Mc mark at each position
base = "Zq7mKp2xWv"
nok = 0; n = 0
for i in range(len(base) + 1):
    pw = base[:i] + chr(0x093E) + base[i:]
    n += 1
    nok += run(f"5.{i} password Mc at {i}", f"password: {pw}\nnext", pw, "password: \nnext") 
res.append(nok == n)
# PEM-style block, Cyrillic letter, overlapped by a PuTTY Private-Lines block
body = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC" + "Kx9" * 8
body_c = body[:10] + chr(0x0430) + body[11:]
pem = "-----BEGIN PRIVATE KEY-----\n" + body_c + "\n" + body[40:] + "\n-----END PRIVATE KEY-----"
putty = "PuTTY-User-Key-File-3: ssh-rsa\nPrivate-Lines: 2\n" + body_c + "\n" + body[40:] + "\nPrivate-MAC: 00"
text6 = pem[:60] + "\n" + putty + "\n" + pem[60:]
ok6 = True
t = time.time(); out6 = redact(text6).text; dt = time.time() - t
for lbl, sec in (("cyr-line", body_c), ("tail", body[40:])):
    if sec in out6: ok6 = False
ps6 = [p for p in pieces(body_c) if p in out6 and p not in "-----BEGIN PRIVATE KEY----- END PuTTY-User-Key-File-3: ssh-rsa Private-Lines: Private-MAC: 00" and len(p) >= 8]
print(f"6 PEM+Cyrillic overlapped by PuTTY block: whole_leak={int(not ok6)} piece8_leaks={len(ps6)} secs={dt:.3f} {'OK' if ok6 and not ps6 else 'NOT-OK'}", flush=True)
res.append(ok6 and not ps6)
# 5000 spacing marks on one line
spm = "key=" + "A" + chr(0x093E) * 5000 + "B"
t = time.time(); o = redact(spm).text; dt = time.time() - t
print(f"7 one line of 5000 spacing marks: secs={dt:.3f} len_out={len(o)}", flush=True)
# many spacing-mark lines
lines = "\n".join("line%d x%sy%sz" % (i, chr(0x093E) * 3, chr(0x0903)) for i in range(3000))
t = time.time(); o = redact(lines).text; dt = time.time() - t
print(f"8 3000 lines each with spacing marks: secs={dt:.3f} len_out={len(o)}", flush=True)
lines2 = "\n".join(("key%d=" % i) + "AKIA" + chr(0x093E) + "IOSFODNN7EXAMPLE" for i in range(500))
t = time.time(); o = redact(lines2).text; dt = time.time() - t
print(f"9 500 lines each with a made-up key and a mark: secs={dt:.3f} whole_leak={int('AKIA'+chr(0x093E)+'IOSFODNN7EXAMPLE' in o)}", flush=True)
# control characters inside a key
base_k = "AKIAIOSFODNN7EXAMPLE"
nok = n = 0
for c in [0x00, 0x01, 0x07, 0x08, 0x0B, 0x0C, 0x1B, 0x7F, 0x85, 0x200B, 0x200E, 0x202E, 0xFEFF]:
    for pos in (4, 10, 16):
        k = base_k[:pos] + chr(c) + base_k[pos:]
        n += 1; nok += run(f"10 control U+{c:04X} at {pos}", f"key={k} end", k)
        # also ensure the plain key doesn't leak either
print(f"10 summary: {nok}/{n} OK")
res.append(nok == n)
print(f"SUMMARY groups_ok={sum(1 for r in res if r)} groups_not_ok={sum(1 for r in res if not r)}")
