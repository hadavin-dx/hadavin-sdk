"""G1 evidence (A): false-hit rate of textnorm.scan_holds on ordinary text. Run: uv run python ev/g1_false_hits.py [values] [chunks] [chunk_chars] [class-prefix,class-prefix]
No protected value is in any corpus text (the values are drawn at random; a hit is a false hit unless a value was drawn from the text itself,
which the generators below avoid by construction only statistically: names are synthetic/hand-listed; a value that equals a whole word
of the chunk is NOT filtered, it would be a true hit; this is reported as 'whole-word' count in the examples when it happens)."""
import ast, glob, os, random, sys, sysconfig, time, unicodedata, collections, json
if os.environ.get('HADAVIN_SRC'): sys.path.insert(0, os.environ['HADAVIN_SRC'])  # -I ignores PYTHONPATH: the export's src is put first here
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

# ======================= G1 split (round 2): where does a false hit sit in the ordinary text? =======================
# Everything above this line is g1_false_hits.py unchanged (same corpora, same seed 20261120, same chunking, same value draws), so the chunks and the
# values are the ones of run 1. scan_holds returns only a bool and reports NO span: the views are folded and keep no offsets. The location is therefore
# recomputed here: every character of the chunk is folded ON ITS OWN (the squeeze view and the two scan-key spellings act one character at a time, see
# the scan_keyset docstring), the pieces are joined with an index back to the original character, and the needles of the value are searched in the joined
# strings. The span of the match in the ORIGINAL text is then classified:
#   whole word   : every original character from the first to the last matched one is a letter/digit (str.isalnum), the character before and the one after
#                  are not (a "_" or any punctuation is a boundary; so `foo_cond` has the whole word `cond`)
#   inside word  : contiguous letters/digits, but at least one end touches another letter/digit (sub-split: prefix of a longer word / suffix / middle)
#   across       : the matched characters have at least one non-letter/digit (space, punctuation, newline, mark) between the first and the last
# A hit with several occurrences is put in the best class (whole > inside > across); occurrences are counted too. A hit whose needle is not found in
# the per-character projections is "unlocated" (the NFKC join is the one step that is not per character).
import re
def proj(chunk):
    sq, ka, kb = [], [], []   # (string, index-of-original) built as lists
    P = {"sq": ([], []), "ka": ([], []), "kb": ([], [])}
    for i, ch in enumerate(chunk):
        if ch.isascii() and ch.isalnum():
            lo = ch.lower(); s = ch.upper()
            a = lo.translate(textnorm._CLASS_MAP); 
            outs = {"sq": s, "ka": a, "kb": a}
        else:
            outs = {"sq": (textnorm.squeeze_views(ch) or ("",))[0],
                    "ka": textnorm._scan_key(ch, textnorm._pass_a), "kb": textnorm._scan_key(ch, textnorm._pass_b)}
        for k, o in outs.items():
            if o:
                P[k][0].append(o); P[k][1].extend([i] * len(o))
    return {k: ("".join(v[0]), v[1]) for k, v in P.items()}
def classify(chunk, p, needle, kind):
    s, idx = p[kind]; occ = []; st = s.find(needle)
    while st != -1:
        i0, i1 = idx[st], idx[st + len(needle) - 1]
        seg = chunk[i0:i1 + 1]
        if not all(c.isalnum() for c in seg): cls = "across spaces/punctuation"
        else:
            left = i0 > 0 and chunk[i0 - 1].isalnum(); right = i1 + 1 < len(chunk) and chunk[i1 + 1].isalnum()
            cls = "whole word" if not left and not right else ("inside word: prefix of a longer word" if not left else ("inside word: suffix of a longer word" if not right else "inside word: middle"))
        occ.append((cls, i0, i1)); st = s.find(needle, st + 1)
    return occ
BEST = ["whole word", "inside word", "across spaces/punctuation"]
def rank(c): return 0 if c.startswith("whole") else (1 if c.startswith("inside") else 2)
def locate(chunk, p, value):
    needle_pairs = textnorm._needle_pairs(value)
    occ = []; path = None
    for kd, nd in needle_pairs:
        if kd == "squeeze":
            o = classify(chunk, p, nd, "sq")
            if o: occ, path = o, "exact (squeeze needle)"; break
    if not occ:
        for key in sorted(textnorm.scan_keyset(value)):
            for kind in ("ka", "kb"):
                o = classify(chunk, p, key, kind)
                if o: occ, path = o, "scan key (look-alike / class map)"; break
            if occ: break
    return path, occ
RS = random.Random(7)
res = {}   # class -> dict
SPLIT_ONLY = ("name-4", "name-5", "name-6", "street/host (corpus word", "digits-6", "short ascii id")
t0 = time.process_time(); allres = {}
for cname, (kind, vals) in classes().items():
    if not cname.startswith(SPLIT_ONLY): continue
    if ONLY and not any(cname.startswith(o) for o in ONLY): continue
    per = {}; refused = 0; scans = hits = 0
    buckets = collections.Counter(); occb = collections.Counter(); paths = collections.Counter(); sub = collections.Counter()
    samples = collections.defaultdict(list); seen = collections.Counter(); hitvals = collections.defaultdict(set); wwv = collections.Counter()
    for corp, cl in LATIN.items() if False else CH_LATIN.items():
        for chunk in cl:
            p = None
            with textnorm.scan_cache():
                for v in vals:
                    try: h = textnorm.scan_holds(text=chunk, value=v)
                    except textnorm.TextnormError: refused += 1; continue
                    scans += 1
                    if not h: continue
                    hits += 1
                    if p is None: p = proj(chunk)
                    path, occ = locate(chunk, p, v)
                    if not occ: b = "unlocated"; sb = b; paths["unlocated"] += 1
                    else:
                        best = min(occ, key=lambda o: rank(o[0])); sb = best[0]; b = BEST[rank(sb)]; paths[path] += 1
                        for o in occ: occb[o[0].split(":")[0]] += 1
                        i0, i1 = best[1], best[2]
                        ctx = chunk[max(0, i0 - 25):i0] + "[[" + chunk[i0:i1 + 1] + "]]" + chunk[i1 + 1:i1 + 26]
                        sm = (corp, v, ctx.replace("\n", "\\n"))
                    buckets[(corp, b)] += 1; buckets[("ALL", b)] += 1; sub[sb] += 1
                    if occ:
                        seen[sb] += 1; k = seen[sb]
                        if len(samples[sb]) < 5: samples[sb].append(sm)
                        else:
                            j = RS.randrange(k)
                            if j < 5: samples[sb][j] = sm
                        hitvals[b].add(v)
    print(f"\n== {cname}: hits {hits}/{scans} = {100*hits/max(scans,1):.4f}%  refused {refused}  [{time.process_time()-t0:.0f}s cpu]", flush=True)
    for b in BEST + ["unlocated"]:
        print(f"   {b:28s} ALL {buckets[('ALL', b)]:6d}  " + "  ".join(f"{c.split('(')[0]}:{buckets[(c, b)]}" for c in CH_LATIN) + f"   distinct values {len(hitvals[b])}")
    print("   sub-split:", dict(sub)); print("   occurrences:", dict(occb)); print("   path:", dict(paths))
    for k, lst in samples.items():
        for s in lst: print("   SAMPLE", k, "|", s[0].split("(")[0], "| value", repr(s[1]), "|", repr(s[2]))
    allres[cname] = dict(hits=hits, scans=scans, refused=refused, buckets={f"{a}|{b}": n for (a, b), n in buckets.items()}, sub=dict(sub), occ=dict(occb), paths=dict(paths),
                         samples={k: v for k, v in samples.items()})
json.dump(allres, open(os.environ.get("G1_SPLIT_OUT", "g1_split.json"), "w"), ensure_ascii=False, indent=1)
