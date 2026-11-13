"""Apply matrix without a working tree: a private index per run, `git apply --cached`, patches in a given order.
A failure counts against the P3 patch only when the same patch applies in the same order WITHOUT P3 (baseline)."""
import itertools, os, random, subprocess, sys, shutil, tempfile
REPO, BASE = sys.argv[1], sys.argv[3]
V2A, V2B = "/tmp/work/sn-p3f2/sonar-p3-final-v2-minors.patch", "/tmp/work/sn-p3f2/sonar-p3-final-v2-risky.patch"
P3 = V2A
N = int(sys.argv[4]); SEED = int(sys.argv[5])
D = "/tmp/demo-lead/handover/demo"
LIST = [f"{D}/sonar/{n}" for n in (
 "sonar-p2-regex-optional.patch", "sonar-p2-feed-optional.patch", "nodemo-ci-job-v4.patch",
 "nodemo-optional-hygiene-repo-v4.patch")] + [
 f"{D}/merge-ready/sonar-yaml-test-trimmed-v2.patch", f"{D}/semgrep/semgrep-on-db54e13-v5.1.patch"]
NAMES = {p: os.path.basename(p) for p in LIST}; NAMES[V2A] = "minors"; NAMES[V2B] = "risky"
tmp = tempfile.mkdtemp(prefix="mx-idx-")
def run_order(order, base_tree):
    idx = os.path.join(tmp, "idx"); env = dict(os.environ, GIT_INDEX_FILE=idx)
    subprocess.run(["git", "read-tree", base_tree], cwd=REPO, env=env, check=True)
    res = {}
    for p in order:
        r = subprocess.run(["git", "apply", "--cached", p], cwd=REPO, env=env, capture_output=True)
        res[p] = r.returncode == 0
    return res
def tree(rev):
    return subprocess.run(["git", "rev-parse", rev + "^{tree}"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
base_tree = tree(BASE)
# every series patch alone
ALL = LIST + [V2A, V2B]
alone = {p: run_order([p], base_tree)[p] for p in ALL}
print("ALONE on", BASE)
for p in ALL: print("  ", NAMES[p], "OK" if alone[p] else "FAIL(alone)")
bad = []
def check(order):
    with_v2 = run_order(order, base_tree)
    without = run_order([p for p in order if p not in (V2A, V2B)], base_tree)
    for p in order:
        if p in (V2A, V2B):
            # v2b needs v2a first; v2a alone must always apply
            if p == V2A and not with_v2[p]: bad.append((tuple(NAMES[x] for x in order), "minors itself"))
            if p == V2B and V2A in order[:order.index(V2B)] and not with_v2[p]: bad.append((tuple(NAMES[x] for x in order), "risky itself"))
        elif without[p] and not with_v2[p]:
            bad.append((tuple(NAMES[x] for x in order), NAMES[p]))
def shuffled(rnd):
    o = LIST[:]; rnd.shuffle(o)
    i = rnd.randrange(len(o) + 1); o.insert(i, V2A)
    j = rnd.randrange(i + 1, len(o) + 1); o.insert(j, V2B)
    return o
n = 0
for a, b in itertools.permutations(ALL, 2):
    if a == V2B and b == V2A: continue
    n += 1; check([a, b])
print("ordered pairs checked:", n)
rnd = random.Random(SEED)
for i in range(N): check(shuffled(rnd))
print("random orders checked:", N, "seed", SEED)
check([V2A, V2B] + LIST); check(LIST + [V2A, V2B]); check([V2A] + LIST + [V2B]); check([V2A, V2B] + LIST[::-1]); check(LIST[::-1] + [V2A, V2B])
print("attributable failures:", len(bad))
for b in bad[:30]: print("  ", b)
shutil.rmtree(tmp, ignore_errors=True)
