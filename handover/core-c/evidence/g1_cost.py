"""G1 evidence (B): cost of textnorm.scan_holds and the injection RegexDetector. Run: uv run python ev/g1_cost.py [part]
CPU seconds = time.process_time(); best of 3 where a run is under ~60 s, otherwise ONE run (stated per row). Memory: peak of tracemalloc in a
separate run (tracemalloc slows the run, so its time is never reported) and ru_maxrss of the process (high-water mark, cumulative)."""
import sys, time, random, resource, tracemalloc, unicodedata
from hadavin_sdk.guard import textnorm, injection
from hadavin_sdk import defaults
print("module:", textnorm.__file__, "python:", sys.version.split()[0], "unidata:", unicodedata.unidata_version, "cap:", defaults.TEXTNORM_MAX_CHARS, "MAX_MAP_ENTRIES:", defaults.MAX_MAP_ENTRIES)
R = random.Random(7)
N = 262_144
words = "the quick brown fox jumps over a lazy dog while incident report shows that service latency rose after deploy and pods restarted".split()
def ascii_text(n):
    out = []; ln = 0
    while ln < n: w = R.choice(words); out.append(w); ln += len(w) + 1
    return " ".join(out)[:n]
ASCII = ascii_text(N)
t = list(ASCII)
for i in R.sample(range(N), N // 100): t[i] = R.choice("éüñßжщ中漢ا")   # 1 percent non-ASCII
MIXED = "".join(t)   # may be refused by the weighted size rule (TextTooLong); reported as such
t = list(ASCII)
for i in R.sample(range(N), N // 100): t[i] = R.choice("\u00e9\u00fc\u00f1\u0436\u0449\u4e2d")
MIXED2 = "".join(t)   # 1 percent non-ASCII without the characters that expand
cps = []
cp = 0x80
while len(cps) < N:
    cp += 1
    c = chr(cp)
    if 0xD800 <= cp <= 0xDFFF: continue
    if unicodedata.category(c) in ("Cn", "Cc", "Cs"): continue  # Co (private use) IS kept: there are fewer than 262,144 assigned non-private code points
    cps.append(c)
DISTINCT = "".join(cps)
assert len(set(DISTINCT)) == N
print('DISTINCT text: private-use characters', sum(unicodedata.category(c)=='Co' for c in DISTINCT), 'of', N)
def fit(text):
    """The longest prefix of text that textnorm._checked accepts (the weighted size rule: a text over the cap is refused with TextTooLong)."""
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        try: textnorm._checked(text[:mid], "abcdef1"); lo = mid
        except textnorm.TextTooLong: hi = mid - 1
    return text[:lo]
MIXED_F, MIXED2_F, DISTINCT_F = fit(MIXED), fit(MIXED2), fit(DISTINCT)
print("FIT prefixes accepted by the size rule: 1%% non-ASCII (sharp s etc.) %d of %d; 1%% non-ASCII (no expanding) %d of %d; DISTINCT %d of %d" % (len(MIXED_F), len(MIXED), len(MIXED2_F), len(MIXED2), len(DISTINCT_F), len(DISTINCT)))
VALS = ["".join(R.choices("abcdefghijklmnopqrstuvwxyz", k=R.randint(6, 12))) + str(R.randint(100, 999)) for _ in range(2000)]
def best(fn, runs=3):
    out = []
    for _ in range(runs):
        a = time.process_time(); r = fn(); out.append(time.process_time() - a)
    return min(out), out, r
def one(fn):
    a = time.process_time(); r = fn(); return time.process_time() - a, r
def peak(fn):
    tracemalloc.start(); fn(); p = tracemalloc.get_traced_memory()[1]; tracemalloc.stop(); return p / 1e6
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
def row(name, secs, extra="", mem=None):
    print(f"ROW | {name} | {secs} | tracemalloc peak {mem if mem is None else f'{mem:.0f} MB'} | maxrss so far {rss():.0f} MB | {extra}", flush=True)

def scan_one(text, v): return lambda: textnorm.scan_holds(text=text, value=v)
def scan_many_nocache(text, vs): 
    def f():
        for v in vs: textnorm.scan_holds(text=text, value=v)
    return f
def scan_many_cache(text, vs):
    def f():
        with textnorm.scan_cache():
            for v in vs: textnorm.scan_holds(text=text, value=v)
    return f
part = sys.argv[1] if len(sys.argv) > 1 else "all"
if part in ("all", "a"):
    for name, text in (("ASCII", ASCII), ("1% non-ASCII (with sharp s, Han, Arabic)", MIXED), ("1% non-ASCII (e-acute u-diaeresis n-tilde zhe shcha Han)", MIXED2)):
        try: b, runs, r = best(scan_one(text, VALS[0])); row(f"1 value, 262,144 chars {name}", f"best {b:.2f} s of {[round(x,2) for x in runs]}", f"result {r}", peak(scan_one(text, VALS[0])))
        except Exception as e: row(f"1 value, 262,144 chars {name}", f"raised {type(e).__name__}: {str(e)[:120]}")
    for name, text in ((f"1% non-ASCII (sharp s...) FITTED to {len(MIXED_F):,} chars", MIXED_F), (f"1% non-ASCII (no expanding) FITTED to {len(MIXED2_F):,} chars", MIXED2_F)):
        b, runs, r = best(scan_one(text, VALS[0])); row(f"1 value, {name}", f"best {b:.2f} s of {[round(x,2) for x in runs]}", f"result {r}", peak(scan_one(text, VALS[0])))
    # DISTINCT non-ASCII text: ASCII value, Han value
    for vname, v in (("ascii value", VALS[0]), ("Han value", "张伟明")):
        try:
            b, runs, r = best(scan_one(DISTINCT_F, v)); row(f"1 value ({vname}), DISTINCT non-ASCII chars (all of them kept: fitted prefix, see FIT line)", f"best {b:.2f} s of {[round(x,2) for x in runs]}", f"result {r}", peak(scan_one(DISTINCT_F, v)))
        except Exception as e: row(f"1 value ({vname}), DISTINCT non-ASCII chars (all of them kept: fitted prefix, see FIT line)", f"raised {type(e).__name__}: {str(e)[:150]}")
if part in ("all", "b"):
    for name, text in (("ASCII", ASCII), ("1% non-ASCII FITTED", MIXED2_F)):
        vs = VALS[:100]
        s, r = one(scan_many_nocache(text, vs)); row(f"100 values, {name} (ASCII: 262,144 chars; FITTED rows: the fitted prefix, about 260,800 chars), NO cache", f"{s:.1f} s (one run; {s/100:.2f} s per call)")
        b, runs, _ = best(scan_many_cache(text, vs)); row(f"100 values, {name} (ASCII: 262,144 chars; FITTED: about 260,800 chars), WITH scan_cache", f"best {b:.2f} s of {[round(x,2) for x in runs]}", mem=peak(scan_many_cache(text, vs)))
if part in ("all", "c"):
    vs = VALS[:20]; s, _ = one(scan_many_nocache(ASCII, vs)); row("2000 values, ASCII 262,144, NO cache: 20 values MEASURED, x100 EXTRAPOLATED", f"20 values {s:.1f} s -> 2000 values about {s*100:.0f} s (extrapolated, NOT run)")
    b, runs, _ = best(scan_many_cache(ASCII, VALS)); row("2000 values, ASCII 262,144, WITH scan_cache", f"best {b:.2f} s of {[round(x,2) for x in runs]}", mem=peak(scan_many_cache(ASCII, VALS)))
    vs = VALS[:20]; s, _ = one(scan_many_nocache(MIXED2_F, vs)); row("2000 values, 1% non-ASCII FITTED (~260,800), NO cache: 20 MEASURED, x100 EXTRAPOLATED", f"20 values {s:.1f} s -> about {s*100:.0f} s (extrapolated, NOT run)")
    b, runs, _ = best(scan_many_cache(MIXED2_F, VALS)); row("2000 values, 1% non-ASCII FITTED (~260,800), WITH scan_cache", f"best {b:.2f} s of {[round(x,2) for x in runs]}", mem=peak(scan_many_cache(MIXED2_F, VALS)))
if part in ("all", "e"):
    # hostile: distinct non-ASCII, WITH cache. The first full run of 2,000 values with the cache ran over 30 minutes of CPU and was killed (not finished), so 100 values are measured and x20 extrapolated.
    vs = VALS[:20]; s, _ = one(scan_many_nocache(DISTINCT_F, vs)); row("20 values, DISTINCT non-ASCII (fitted 236,879), NO cache (x100 -> 2000 values EXTRAPOLATED, NOT run)", f"{s:.1f} s -> about {s*100:.0f} s")
    s, _ = one(scan_many_cache(DISTINCT_F, VALS[:100])); row("100 values, DISTINCT non-ASCII (fitted 236,879), WITH scan_cache (one run; x20 -> 2000 values EXTRAPOLATED)", f"{s:.1f} s -> about {s*20:.0f} s for 2000", mem=peak(scan_many_cache(DISTINCT_F, VALS[:20])))
if part in ("all", "d"):
    big = ascii_text(2_000_000)
    det = injection.RegexDetector(0.5)
    for name, text in (("ASCII", big), ("1% non-ASCII (latin accents/cyrillic/han)", None)):
        if text is None:
            t = list(big)
            for i in R.sample(range(len(big)), len(big) // 100): t[i] = R.choice("éüñßжщ中漢ا")
            text = "".join(t)
        s, v = one(lambda: det.check(text, "t")); row(f"RegexDetector.check, {len(text):,} chars {name}", f"{s:.1f} s (one run)", f"flagged={v.flagged} reason={v.reason_code}", peak(lambda: det.check(text, "t")) if len(text) else None)
