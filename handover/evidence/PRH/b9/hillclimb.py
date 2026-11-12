"""Group 3: the 60 second hill-climb for the pass count (repeat of the 2026-11-11 measurement). Usage: python hillclimb.py <seconds> <seed>.
Start from seeded texts (`tests.test_prh_spans.Gen`), mutate by inserting or deleting hidden-character, encoding and value snippets,
keep a text when its pass count does not fall. Prints the worst pass count and whether any text reached the bound."""
import random, sys, time
sys.path.insert(0, ".")
from hadavin_sdk.guard import runmap
from tests.test_prh_spans import Gen
from tests.test_prh_steps import _seeded_text

SNIP = ["\x1b(B", "\x1b[0m", "\x1b", "\x1b]0;t\x07", "%1b[0m", "&#27;[0m", "\\u001b[0m", "​", "\x9b", "\x90", "\x07", "AKIA", "IOSFODNN7EXAMPLE",
        "<SECRET_1>", "%41", "&#65;", "\\x41", "é", "日本", "password=", "x y z a b c d e f g h", "ﷺ", "\x1bM", "\x1bK", "ghp_", " ", "\n"]
real = runmap._Work.count_pass
st = {"n": 0, "bound": 0}
def spy(self):
    try:
        real(self)
    except runmap.InputTooLarge:
        st["bound"] += 1
        raise
    st["n"] = self.passes
runmap._Work.count_pass = spy
ok_peak = {"n": 0}
def score(t):
    st["n"] = 0
    b0 = st["bound"]
    try:
        runmap.redact_untrusted(t, {})
    except runmap.RedactionError:
        pass
    if st["bound"] == b0:
        ok_peak["n"] = max(ok_peak["n"], st["n"])
    return st["n"]
secs, seed = float(sys.argv[1]), int(sys.argv[2])
r = random.Random(seed)
t0 = time.time()
pool = [_seeded_text(Gen(i)) for i in range(40)]
best, bt = 0, ""
tried = 0
while time.time() - t0 < secs:
    cur = r.choice(pool)
    c = score(cur)
    for _ in range(30):
        s = list(cur)
        for _ in range(r.randint(1, 3)):
            i = r.randint(0, len(s))
            if r.random() < 0.7 or not s:
                s[i:i] = list(r.choice(SNIP))
            else:
                del s[i:i + r.randint(1, 4)]
        cand = "".join(s)
        tried += 1
        n = score(cand)
        if n >= c:
            cur, c = cand, n
        if n > best:
            best, bt = n, cand
    pool.append(cur)
print(f"seconds={secs} seed={seed} texts_tried={tried} worst_passes_incl_refused={best} worst_passes_of_texts_not_refused_by_the_bound={ok_peak["n"]} cap={runmap.defaults.MAX_REDACT_PASSES} reached_bound={st['bound']}")
print("worst text (repr, 300 chars):", repr(bt[:300]))
