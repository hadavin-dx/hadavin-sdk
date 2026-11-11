"""Hostile inputs for tools/mutation_runner masking. Secrets are made up and built from parts. Prints counts only, never a secret."""
import sys, time, os
sys.path.insert(0, os.environ["WT"])
sys.path.insert(0, os.path.join(os.environ["WT"], "src"))
from tools import mutation_runner as mr

def pieces(s, n=3):
    return {s[i:i+k] for k in range(n, len(s)+1) for i in range(len(s)-k+1)} if len(s) <= 60 else {s[i:i+n] for i in range(len(s)-n+1)}

results = []
def check(label, env_value, secret_hint, extra_secrets=()):
    """env_value goes in as pass_env; secret_hint: the strings that must not appear whole; pieces of length>=3 of secret_hint also checked."""
    os.environ["HX_ADDR"] = env_value
    t = time.time()
    try:
        secs = mr._secret_values(["HX_ADDR"])
    except ValueError as e:
        results.append((label, "REFUSED-BEFORE-RUN", type(e).__name__, 0, 0)); return
    TOK = "<<T>>"
    forms = []
    s = secret_hint
    forms.append(s)                                   # plain
    forms.append(repr(s)[1:-1])                      # repr layer (no quotes inside by construction, so same)
    forms.append(f"E   assert 'x' == '{s}'")          # pytest-ish
    forms.append(f"{env_value}")                      # whole value
    forms.append(f"E   AssertionError: {s} != other")
    for cut in range(2, len(s)-1, max(1, len(s)//17)):  # pytest-style head...tail shortening
        forms.append(f"E   assert '{s[:cut]}...{s[-max(2,len(s)-cut-1):]}'")
        forms.append(f"E   assert '{s[:cut]}...' got")
        forms.append(f"E   assert '...{s[cut:]}' got")
    leaks = 0; bad_rows = 0; maxsec = 0
    for line in forms:
        ts = time.time(); out = mr._masked(line, secs); maxsec = max(maxsec, time.time()-ts)
        # template = the line with the whole-secret removed; any >=3-char piece of the secret in out that is not in the template's own fixed text counts
        fixed = line
        for chunk in sorted(pieces(s) if len(s) <= 60 else [], key=len, reverse=True):
            pass
        found = [p for p in (pieces(s) if len(s) <= 60 else {s[i:i+8] for i in range(0, len(s)-7, 7)}) if p in out and p not in "E   assert  == != other got '..." and p != mr.MASK and p not in mr.MASK]
        if s in out: leaks += 1
        if found: bad_rows += 1
    results.append((label, "OK" if (leaks == 0 and bad_rows == 0) else "LEAK", f"lines={len(forms)} whole_secret_in_output={leaks} lines_with_3plus_piece={bad_rows}", len(secs), round(maxsec, 4)))

def A(*p): return "".join(p)
# 1 password with @ / ? # space %
pw1 = A("pa", "@ss", "/w", "?rd", "#", " 9", "%", "Zq")
check("pw-special-@/?#space%", A("postgresql://usr:", pw1.replace("@","%40").replace("/","%2F").replace("?","%3F").replace("#","%23").replace(" ","%20").replace("%Zq","%25Zq"), "@db.example.invalid:5432/app"), pw1)
check("pw-special-raw-value", pw1, pw1)
# 2 2000 all special chars + 1000 dot line (timing)
special = "@/?# %&;=+:!$*(),<>[]{}|^~-_"
pw2 = (special * 100)[:2000]
check("pw-2000-special-value", pw2, pw2[:2000])
# 1000-dot line timing with that env value set, and with normal secret
os.environ["HX_ADDR"] = A("postgresql://usr:", "Zq9x", "K2mP7w", "@h.example.invalid/db")
secs = mr._secret_values(["HX_ADDR"])
for n in (999, 1000, 1001, 5000):
    line = "E   assert '" + "." * n + "' tail Zq9xK2mP7w"
    t = time.time(); out = mr._masked(line, secs); dt = time.time() - t
    results.append((f"dots-{n}-line", "OK" if "Zq9xK2mP7w" not in out else "LEAK", f"seconds={dt:.4f} out_len={len(out)}", len(secs), round(dt, 4)))
# same with the 2000-char all-special secret and 1000-dot line
os.environ["HX_ADDR"] = pw2
try:
    secs2 = mr._secret_values(["HX_ADDR"])
    line = "E   assert '" + pw2[:900] + "." * 1000 + pw2[-50:] + "'"
    t = time.time(); out = mr._masked(line, secs2); dt = time.time() - t
    results.append(("special2000+dots1000-line", "OK" if pw2[:20] not in out and pw2[-20:] not in out else "LEAK", f"seconds={dt:.4f} secrets={len(secs2)}", len(secs2), round(dt, 4)))
except ValueError as e:
    results.append(("special2000+dots1000-line", "REFUSED-BEFORE-RUN", type(e).__name__, 0, 0))
# 3 repeating secrets
for rep in ("aabaaab", "aabaaabaabaaab", "abababab" + "Xq", "aaaaaaaa", "abcabcabcabcZ"):
    check(f"repeat-{rep}", A("postgresql://u:", rep, "@h.example.invalid/d"), rep)
    check(f"repeat-raw-{rep}", rep, rep)
# 4 URL passwords 12 / 45 / 12/45
for pw in ("12", "45", "12/45", "12%2F45"):
    v = A("postgresql://u:", pw, "@h.example.invalid/d")
    check(f"urlpw-{pw}", v, pw)
for label, status, detail, n, mx in results:
    print(f"{status:20} {label:34} secrets={n:<4} max_line_s={mx:<8} {detail}")
print("TOTAL", len(results), "non-OK:", sum(1 for r in results if r[1] not in ("OK",)))
