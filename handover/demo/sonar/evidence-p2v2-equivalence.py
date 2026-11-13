"""Old vs new patterns (P2 v2): _ADDRESS (run_real_check) and MAIL (scrub). Old patterns are read from git (db54e13).
Compares .sub output AND every match span. Run: python evidence-p2v2-equivalence.py <repo>"""
import importlib, itertools, random, re, subprocess, sys, time
repo = sys.argv[1]
sys.path[:0] = [repo + "/scripts", repo + "/src", repo]
rrc = importlib.import_module("run_real_check")
scrub = importlib.import_module("tools.scrub_n8n_export")

def old_src(path, name):
    src = subprocess.check_output(["git", "-C", repo, "show", "db54e13:" + path], text=True)
    m = re.search(r"^" + name + r" = re\.compile\(\s*(r\".*?\")\s*\)$", src, re.M | re.S)
    return re.compile(eval(m.group(1)))

OLD_ADDR = old_src("scripts/run_real_check.py", "_ADDRESS")
OLD_MAIL = old_src("tools/scrub_n8n_export.py", "MAIL")
NEW_ADDR, NEW_MAIL = rrc._ADDRESS, scrub.MAIL
print("old addr:", OLD_ADDR.pattern); print("new addr:", NEW_ADDR.pattern)
print("old mail:", OLD_MAIL.pattern); print("new mail:", NEW_MAIL.pattern)
assert OLD_ADDR.pattern != NEW_ADDR.pattern and OLD_MAIL.pattern != NEW_MAIL.pattern

def spans(p, s): return [m.span() for m in p.finditer(s)]
bad = cases = 0
def cmp(s):
    global bad, cases
    cases += 1
    if spans(OLD_ADDR, s) != spans(NEW_ADDR, s) or spans(OLD_MAIL, s) != spans(NEW_MAIL, s) \
       or OLD_ADDR.sub("<>", s) != NEW_ADDR.sub("<>", s) or OLD_MAIL.sub("<>", s) != NEW_MAIL.sub("<>", s):
        bad += 1
        if bad <= 10: print("DIFF", repr(s))

# 1. exhaustive, small alphabet: address-class edges and mail edges
A1 = ["a", "@", ".", " ", ":", ",", ";", "<", '"', "'", "\n"]
for n in range(0, 7):
    for t in itertools.product(A1, repeat=n): cmp("".join(t))
print("exhaustive A1 (11 symbols, len<=6) done, cases", cases)
A2 = ["a", "@", "＠", ".", "-", "%", "+", " ", "_", "é"]
for n in range(0, 7):
    for t in itertools.product(A2, repeat=n): cmp("".join(t))
print("exhaustive A2 (10 symbols, len<=6) done, cases", cases)
A3 = ["a", "@", ".", "example", "com", "test", "invalid", "-", " "]
for n in range(0, 6):
    for t in itertools.product(A3, repeat=n): cmp("".join(t))
print("exhaustive A3 (domain tokens, <=5 tokens) done, cases", cases)

# 2. random token strings
random.seed(20261113)
TK = A1 + A2 + ["example", ".com", "example.com", "example.test", "example.invalid", "x.", "..", "ex", "EXAMPLE.COM",
                "日本語", "ß", "\r", "\x00", " ", "mailto:", "Name <", ">", "jane.doe", "o'brien", "+tag", "%20"]
for _ in range(600_000):
    cmp("".join(random.choice(TK) for _ in range(random.randint(0, 16))))
print("random done, cases", cases)

# 3. realistic corpus
REAL = ["Write to jane.doe@corp.test, thanks", "Name <x@y.example>, other@x.org;third@y.z", "mailto:a@b.co?subject=hi",
        '"quoted local"@x.test', "ada@example.com", "ada@sub.example.com", "ada@example.com.evil.org", "ada@notexample.com",
        "a@example.invalid. and b@example.test.", "日本語@例え.jp x@y.jp", "first+tag@corp.test", "o'brien@corp.test",
        "a@b@c", "@@@", "x@", "@y", "user@host:8080/path", "http://u:p@host.test/", "a" * 300 + "@" + "b" * 300 + ".com",
        "a@" + "b." * 1000 + "com", "x\ty@z.test\nq@r.test", "ＡＢ＠ｃｄ.com", "a＠b.test", "a%b+c@d-e.f_g", ".@.", "-@-"]
for s in REAL:
    cmp(s); cmp(" " + s + " "); cmp(s + s)
print("realistic done, cases", cases, "DIFFERENCES:", bad)
assert bad == 0

# 4. speed (new patterns only; the old ones are quadratic on a)
def ms(f): t = time.perf_counter(); f(); return (time.perf_counter() - t) * 1000
print("new patterns, ms:")
for n in (4000, 16000, 64000, 128000):
    for label, s in (("a*n", "a" * n), ("a@*n", "a@" * (n // 2)), ("a.*n", "a." * (n // 2)),
                     ("a@b.*n", "a@" + "b." * (n // 2)), ("a@example.*n", "a@" + "example." * (n // 8))):
        print(f"  n={n:6d} {label:13s} addr {ms(lambda: NEW_ADDR.sub('x', s)):7.2f}  mail {ms(lambda: NEW_MAIL.sub('x', s)):7.2f}")
print("old patterns, ms (addr quadratic; mail not slow on these):")
for n in (1000, 4000, 16000):
    for label, s in (("a*n", "a" * n), ("a.*n", "a." * (n // 2))):
        print(f"  n={n:6d} {label:6s} addr {ms(lambda: OLD_ADDR.sub('x', s)):8.2f}  mail {ms(lambda: OLD_MAIL.sub('x', s)):7.2f}")
