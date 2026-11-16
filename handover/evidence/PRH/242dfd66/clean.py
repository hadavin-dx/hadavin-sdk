"""EVIDENCE RUNNER own clean corpus: ordinary text that holds no secret. Usage: clean.py <tree> <out.json>. Seeded, so the corpus is the same for every tree."""
import json, os, random, sys, hashlib
tree, outp = sys.argv[1], sys.argv[2]
sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools
assert os.path.realpath(tools.__file__).startswith(os.path.realpath(tree))
rnd = random.Random(20261112)
WORDS = "error warning request response timeout retry user order invoice payment batch worker queue cache index table column row file path folder server client token expired valid invalid started finished stopped loaded saved deleted created updated pending approved rejected the a of to in on at for with from by and or not is was".split()
OTHER = ["नमस्ते दुनिया यह एक परीक्षण है", "این یک آزمایش است ‌می‌رود", "これはテストです。ログを確認してください", "Zażółć gęślą jaźń", "naïve café résumé coöperate", "😀 done ✅ ok 👍"]
PATHS = ["C:\\env\\config.ini", "C:\\Users\\err\\x.log", "C:\\Documents\\error_logs\\a.txt", "/var/log/app/error.log", "D:\\envs\\prod\\run.bat", "\\\\server\\share\\err\\e.txt", "~/.config/env/e"]
ANSI = ["\x1b[0m", "\x1b[31m", "\x1b[1;32m", "\x1b[0;33m", "\x1b(B\x1b[m", "\x1b[K", "\x1b[2J"]
def line():
    k = rnd.random()
    w = " ".join(rnd.choice(WORDS) for _ in range(rnd.randint(3, 12)))
    if k < .12: return f"2026-11-{rnd.randint(1,12):02d}T{rnd.randint(0,23):02d}:{rnd.randint(0,59):02d}:00Z INFO {w}"
    if k < .22: return json.dumps({"event": w, "id": rnd.randint(1, 10**6), "ok": rnd.random() < .5})
    if k < .30: return f"open {rnd.choice(PATHS)} failed: {w}"
    if k < .38: return rnd.choice(ANSI) + w + rnd.choice(ANSI)
    if k < .44: return rnd.choice(OTHER)
    if k < .50: return f"GET https://example.invalid/a/b?q={'%20'.join(rnd.sample(WORDS,3))}&page={rnd.randint(1,9)} 200"
    if k < .56: return "sha " + hashlib.sha256(w.encode()).hexdigest()
    if k < .62: return f"| {w} | {rnd.randint(1,999)} | {rnd.choice(WORDS)} |"
    if k < .68: return "\t".join(rnd.choice(WORDS) for _ in range(5))
    if k < .72: return f"Traceback (most recent call last):\n  File \"app.py\", line {rnd.randint(1,300)}, in run\n    {w}\nValueError: {w}"
    if k < .76: return "progress: " + "\r".join(f"{i*10}%" for i in range(rnd.randint(2, 8)))
    if k < .80: return "a b c d e f g h i j k l m n o p"
    if k < .84: return "S  T  A  T  U  S    O  K"
    if k < .88: return f"id: {'-'.join(str(rnd.randint(1000,9999)) for _ in range(4))}"
    return w
texts = ["\n".join(line() for _ in range(rnd.randint(1, 30))) for _ in range(6000)]
EVERYDAY = "wintergardentablecloud"
HAND = "".join(["vK4n", "Ts8Q", "w2Ld", "Rm6x", "Bf9H", "jYc3", "pZ5g"])
def withheld(out): return out.startswith(tools.MARKER) and len(out) <= len(tools.MARKER) + len(tools.TRUNCATED)
res = {"A": 0, "D": 0, "A_err": 0, "D_err": 0}
for i, t in enumerate(texts):
    try:
        if withheld(tools.prepare_output(t, {}, 4000, [HAND])): res["A"] += 1
    except BaseException as e: res["A_err"] += 1
    t2 = t + '\n"' + EVERYDAY + '" is the word; again ' + EVERYDAY
    try:
        if withheld(tools.prepare_output(t2, {}, 4000, [EVERYDAY])): res["D"] += 1
    except BaseException as e: res["D_err"] += 1
res["n"] = len(texts)
res["corpus_sha256"] = hashlib.sha256("\x00".join(texts).encode()).hexdigest()[:16]
json.dump(res, open(outp, "w")); print(tree.split("/")[-1], res)
