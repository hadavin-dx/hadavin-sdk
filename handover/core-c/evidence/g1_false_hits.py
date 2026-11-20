"""G1 evidence (A): false-hit rate of textnorm.scan_holds on ordinary text. Run: uv run python ev/g1_false_hits.py [values] [chunks] [chunk_chars] [class-prefix,class-prefix]
No protected value is in any corpus text (the values are drawn at random; a hit is a false hit unless a value was drawn from the text itself,
which the generators below avoid by construction only statistically: names are synthetic/hand-listed; a value that equals a whole word
of the chunk is NOT filtered, it would be a true hit; this is reported as 'whole-word' count in the examples when it happens)."""
import ast, glob, os, random, sys, sysconfig, time, unicodedata, collections, json
from hadavin_sdk.guard import textnorm
from hadavin_sdk import defaults
print("module:", textnorm.__file__, "python:", sys.version.split()[0], "unidata:", unicodedata.unidata_version)
NV = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
NC = int(sys.argv[2]) if len(sys.argv) > 2 else 200
CH = int(sys.argv[3]) if len(sys.argv) > 3 else 10_000
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else None  # class-name prefixes to run (run 2 of the evidence)
R = random.Random(20261120)
ROOT = os.getcwd()

# ---------- corpora ----------
def read(paths):
    out = []
    for p in sorted(paths):
        try: out.append(open(p, encoding="utf-8").read())
        except Exception: pass
    return "\n".join(out)
repo_files = [p for d in ("README.md","CHANGELOG.md","docs","src","tests","tools","demos","SECURITY.md","THIRD-PARTY-NOTICES.md")
              for p in ([d] if os.path.isfile(d) else glob.glob(d + "/**/*", recursive=True))
              if os.path.isfile(p) and p.endswith((".py",".md",".toml",".yml",".yaml",".txt",".json")) and "textnorm_corpus" not in p and "/.venv/" not in p]
repo = read(repo_files)
def docstrings(root):
    out = []
    for p in glob.glob(root + "/**/*.py", recursive=True):
        if "/test" in p or "site-packages" in p or "idlelib" in p: continue
        try: t = ast.parse(open(p, encoding="utf-8").read())
        except Exception: continue
        for n in ast.walk(t):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                d = ast.get_docstring(n)
                if d: out.append(d)
    return "\n\n".join(out)
stdlib = docstrings(sysconfig.get_paths()["stdlib"])
sharedoc = read([p for p in glob.glob("/usr/share/doc/**/*", recursive=True) if os.path.isfile(p) and not p.endswith(".gz") and os.path.getsize(p) < 400_000 and any(k in os.path.basename(p) for k in ("copyright","README","NEWS","changelog"))])
# Markov word-level (order 2) text from stdlib docstrings + share/doc
words = (stdlib + " " + sharedoc).split()
tri = collections.defaultdict(list)
for a, b, c in zip(words, words[1:], words[2:]): tri[(a, b)].append(c)
keys = list(tri)
def markov(n):
    a, b = R.choice(keys); out = [a, b]; ln = len(a) + len(b) + 2
    while ln < n:
        c = R.choice(tri.get((a, b)) or tri[R.choice(keys)]) if (a, b) in tri else R.choice(words)
        out.append(c); ln += len(c) + 1; a, b = b, c
    return " ".join(out)
generated = markov(len(stdlib) // 3 if len(stdlib) // 3 < 3_000_000 else 3_000_000)

# non-Latin: NO running text exists on the box (grep of /usr /opt /root /home and the venv found no 20-char run of Han, Cyrillic, Arabic or Devanagari);
# SYNTHETIC models are built here from letter-frequency tables written in this script (not measured on real language).
def zipf_pick(pool, s=1.0):
    w = [1 / (i + 1) ** s for i in range(len(pool))]
    return lambda: R.choices(pool, w)[0]
HAN_N = 3500
han_pool = [chr(0x4E00 + i) for i in range(HAN_N)]; R.shuffle(han_pool)
han_z = zipf_pick(han_pool); han_u = lambda: R.choice(han_pool)
def han_text(n, pick):
    out = []; ln = 0
    while ln < n:
        k = R.randint(4, 14); out.append("".join(pick() for _ in range(k))); ln += k + 1
    return "。".join(out)
CYR = "оеаинтсрвлкмдпуяыьгзбчйхжшюцщэф"; CYR_W = [90,72,62,62,53,53,45,40,38,35,35,32,30,28,26,25,20,19,17,16,15,14,10,9,7,6,4,3,2,2,3][:len(CYR)]
ARA = "اليمنوبرتسدةكفعقحهجصخشزطذثضغظء"; ARA_W = [120,90,70,60,60,50,45,45,40,35,32,30,28,27,25,22,20,18,15,12,12,10,8,8,7,6,5,4,3,2,2][:len(ARA)]
DEV = "कतरनमसलहपवदयबजगअ"; DEV_W = [10,9,9,8,8,7,7,6,6,5,5,5,4,3,3,3,2,2][:len(DEV)]
MATRA = "ािीुूेैोौ्ं"
def alpha_text(alpha, w, n, extra=""):
    out = []; ln = 0
    while ln < n:
        k = R.randint(2, 9); wd = "".join(R.choices(alpha, w, k=k)); out.append(wd); ln += k + 1
    return " ".join(out)
def dev_text(n):
    out = []; ln = 0
    while ln < n:
        wd = "".join(R.choices(DEV, DEV_W)[0] + (R.choice(MATRA) if R.random() < .55 else "") for _ in range(R.randint(2, 6))); out.append(wd); ln += len(wd) + 1
    return " ".join(out)
BIG = 400_000
nonlatin = {
  "han-zipf": han_text(BIG, han_z), "han-uniform": han_text(BIG, han_u),
  "cyrillic-freq": alpha_text(CYR, CYR_W, BIG), "arabic-freq": alpha_text(ARA, ARA_W, BIG), "devanagari-freq": dev_text(BIG),
}
corpora = {"repo(prose+code)": repo, "stdlib-docstrings": stdlib, "generated-markov": generated, **nonlatin}
print("CORPUS sizes (chars):", {k: len(v) for k, v in corpora.items()}, "repo files:", len(repo_files), "share/doc chars:", len(sharedoc))
def chunks(text, n, size):
    if len(text) < size * n: n = max(1, len(text) // size)
    starts = sorted(R.sample(range(0, len(text) - size + 1, size), n)) if len(text) >= size * n else [0]
    return [text[s:s + size] for s in starts]

# ---------- values ----------
V, C = "bcdfghjklmnprstvwz", "aeiou"
def pron(L):
    s = ""
    while len(s) < L: s += R.choice(V) + R.choice(C) + (R.choice("nrsl") if R.random() < .3 else "")
    return s[:L]
FIRST = "Mary Anna John Peter Susan Michael Sarah David Laura Robert Emma Thomas Julia Daniel Helen Oliver Sophie Martin Claire Andrew Hannah Marco Elena Stefan Katrin Johann Ingrid Lukas Maria Pavel Nadia Hassan Fatima Omar Yusuf Ahmed Priya Rahul Anita Kenji Yuki Akira Carlos Lucia Pedro Sofia Giulia Matteo Chiara Fabian Jonas Marta Simone Daniela Alexander Katharina Christopher Elizabeth Jacqueline Maximilian Konstantin Wilhelmina Bartholomew Alessandro Margarethe".split()
def digits(L): return "".join(R.choice("0123456789") for _ in range(L))
def ascii_id(): 
    L = R.choice((4, 5)); return "".join(R.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(L))
STREET = [w for w in set(words) if w.isalpha() and w.isascii() and 5 <= len(w) <= 10]
def han_name(n, pick): return "".join(pick() for _ in range(n))
def pron_alpha(alpha, w, L): return "".join(R.choices(alpha, w, k=L))
def classes():
    c = {}
    for L in (4, 5, 6, 8, 12):
        pool = [n for n in FIRST if len(n) == L]
        c[f"name-{L} (hand list+synth)"] = ("latin", [ (R.choice(pool) if pool and R.random() < .3 else pron(L).capitalize()) for _ in range(NV)])
    c["street/host (corpus word, 5-10)"] = ("latin", [R.choice(STREET).capitalize() for _ in range(NV)])
    c["street/host (word-word 8-14)"] = ("latin", [R.choice(STREET) + "-" + R.choice(STREET) for _ in range(NV)])
    for L in (6, 8, 12, 16): c[f"digits-{L}"] = ("latin", [digits(L) for _ in range(NV)])
    c["short ascii id (4-5)"] = ("latin", [ascii_id() for _ in range(NV)])
    for L in (2, 3, 4):
        c[f"han-{L} (zipf names)"] = ("han-zipf", [han_name(L, han_z) for _ in range(NV)])
        c[f"han-{L} (uniform names)"] = ("han-uniform", [han_name(L, han_u) for _ in range(NV)])
    c["cyrillic 4-8"] = ("cyrillic-freq", [pron_alpha(CYR, CYR_W, R.randint(4, 8)).capitalize() for _ in range(NV)])
    c["arabic 3-6"] = ("arabic-freq", [pron_alpha(ARA, ARA_W, R.randint(3, 6)) for _ in range(NV)])
    c["devanagari 3-5 syll"] = ("devanagari-freq", ["".join(R.choices(DEV, DEV_W)[0] + (R.choice(MATRA) if R.random() < .55 else "") for _ in range(R.randint(3, 5))) for _ in range(NV)])
    return c
LATIN = {k: corpora[k] for k in ("repo(prose+code)", "stdlib-docstrings", "generated-markov")}
CH_LATIN = {k: chunks(t, NC // 3 + (1 if i == 0 else 0), CH) for i, (k, t) in enumerate(LATIN.items())}
CH_NL = {k: chunks(corpora[k], NC, CH) for k in nonlatin}
print("chunks per latin corpus:", {k: len(v) for k, v in CH_LATIN.items()}, "non-latin:", {k: len(v) for k, v in CH_NL.items()}, "chunk chars", CH)

def why(chunk, value):
    """The matched substring only: the needle of the value that sits in a view of the chunk (or 'insertion')."""
    needles = textnorm.scan_needles(value)
    for v in textnorm.scan_views(chunk, value):
        for n in needles:
            if n in v: return ("needle in view", n)
    return ("one-inserted-letter match", "")
rows = []; examples = {}
t0 = time.process_time()
for cname, (kind, vals) in classes().items():
    if ONLY and not any(cname.startswith(o) for o in ONLY): continue
    chs = CH_LATIN if kind == "latin" else {kind: CH_NL[kind]}
    per = {}; refused = 0; hitvals = set(); ex = []
    for corp, cl in chs.items():
        scans = hits = 0
        for chunk in cl:
            with textnorm.scan_cache():
                for v in vals:
                    try: h = textnorm.scan_holds(text=chunk, value=v)
                    except textnorm.TextnormError as e: refused += 1; continue
                    scans += 1
                    if h:
                        hits += 1; hitvals.add(v)
                        if len(ex) < 3: ex.append(why(chunk, v))
        per[corp] = (hits, scans)
    tot_h = sum(h for h, s in per.values()); tot_s = sum(s for h, s in per.values())
    rows.append((cname, per, tot_h, tot_s, len(hitvals), refused)); examples[cname] = ex
    print(f"{cname:34s} hits {tot_h}/{tot_s} = {100*tot_h/max(tot_s,1):.4f}%  distinct values hit {len(hitvals)}/{len(vals)} refused {refused}  per-corpus {per}  [{time.process_time()-t0:.0f}s cpu]", flush=True)
    for e in ex: print("     example:", e[0], repr(e[1]))
# ---- the quoted examples ----
print("\nQUOTED EXAMPLES")
for t, v in [("a summary of the work", "Mary"), ("Hannah went home", "Anna"), ("(tab) 12 apples", "ab12"), ("the summary", "Mary"), ("my own name is Hannah", "Anna"), ("Hanna", "Anna"), ("ab 12", "ab12")]:
    try: r = textnorm.scan_holds(text=t, value=v)
    except Exception as e: r = type(e).__name__
    print(f"  scan_holds(text={t!r}, value={v!r}) -> {r}")
han_sample = chunks(corpora["han-zipf"], 1, 200)[0]
bg = [han_sample[i:i+2] for i in range(len(han_sample)-1)]
b = next(x for x in bg if x.isalpha()); print("  Han bigram present in 200-char synthetic Chinese text:", textnorm.scan_holds(text=han_sample, value=b))
json.dump({"rows": [(r[0], {k: list(v) for k, v in r[1].items()}, r[2], r[3], r[4], r[5]) for r in rows], "examples": examples}, open("/tmp/core-c-ev/ev/fh.json", "w"), ensure_ascii=False)
