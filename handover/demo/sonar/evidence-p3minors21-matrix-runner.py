"""Apply matrix without a working tree: a private index per run, `git apply --cached`, patches in a given order.
A failure is attributable to one of OUR four patches only when (a) it is a prerequisite-respecting order for ours
(minors < risky; minors < minors-delta; risky < risky-delta) and the patch fails although the same order WITHOUT our four
applies the others; or (b) another patch fails with ours in the order although it applies in the same order without them."""
import itertools, os, random, subprocess, sys, shutil, tempfile
REPO, BASE, N, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
S = "/tmp/demo-push/handover/demo/sonar"; D = "/tmp/demo-lead/handover/demo"
MIN, RSK, MD, RD = (f"{S}/sonar-p3-final-v2-minors.patch", f"{S}/sonar-p3-final-v2-risky.patch",
                    f"{S}/sonar-p3-final-v2-minors-v21-delta.patch", f"{S}/sonar-p3-final-v2-risky-v21-delta.patch")
OURS = [MIN, RSK, MD, RD]
OTHERS = [f"{D}/sonar/{n}" for n in ("nodemo-ci-job-v4.patch", "sonar-p2-optional-gaps-delta.patch", "sonar-p2-feed-constants-delta.patch")] + [
    f"{D}/merge-ready/sonar-yaml-test-trimmed-v2.patch", f"{D}/semgrep/semgrep-on-db54e13-v5.1.patch"]
EXTRA = [f"{D}/sonar/{n}" for n in ("sonar-p2-regex-optional.patch", "sonar-p2-feed-optional.patch", "nodemo-optional-hygiene-repo-v4.patch")]  # alone-checks only
NAMES = {p: os.path.basename(p).replace("sonar-p3-final-v2-", "") for p in OURS + OTHERS + EXTRA}
PREREQ = {RSK: MIN, MD: MIN, RD: RSK}
tmp = tempfile.mkdtemp(prefix="mx21-")
def tree(rev): return subprocess.run(["git", "rev-parse", rev + "^{tree}"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
BT = tree(BASE)
def run_order(order):
    idx = os.path.join(tmp, "idx"); env = dict(os.environ, GIT_INDEX_FILE=idx)
    subprocess.run(["git", "read-tree", BT], cwd=REPO, env=env, check=True)
    res = {}
    for p in order:
        res[p] = subprocess.run(["git", "apply", "--cached", p], cwd=REPO, env=env, capture_output=True).returncode == 0
    return res
print("ALONE on", BASE)
for p in OURS + OTHERS + EXTRA: print("  %-40s %s" % (NAMES[p], "OK" if run_order([p])[p] else "fails alone"))
bad = []; stats = {"orders": 0, "ours_all_applied": 0}
def check(order):
    stats["orders"] += 1
    w = run_order(order); wo = run_order([p for p in order if p not in OURS])
    for p in order:
        if p in OURS:
            pre = PREREQ.get(p)
            if pre is None or pre in order[:order.index(p)] and w[pre]:
                if not w[p]: bad.append((tuple(NAMES[x] for x in order), NAMES[p] + " (ours fails with its prerequisite present)"))
        elif wo[p] and not w[p]:
            bad.append((tuple(NAMES[x] for x in order), NAMES[p] + " (another patch broken by ours)"))
    if all(p in w and w[p] for p in OURS): stats["ours_all_applied"] += 1
pool = OTHERS + EXTRA
def shuffled(rnd):
    o = pool[:]; rnd.shuffle(o)
    ours = [MIN, RSK, MD, RD]
    pos = sorted(rnd.sample(range(len(o) + len(ours)), len(ours)))
    # our four in a random relative order that respects their prerequisites
    while True:
        seq = ours[:]; rnd.shuffle(seq)
        if seq.index(MIN) < seq.index(RSK) and seq.index(MIN) < seq.index(MD) and seq.index(RSK) < seq.index(RD): break
    out = []; it = iter(o); sit = iter(seq)
    for i in range(len(o) + len(ours)): out.append(next(sit) if i in pos else next(it))
    return out
for a, b in itertools.permutations(OURS + OTHERS, 2): check([a, b])
print("ordered pairs checked:", stats["orders"])
rnd = random.Random(SEED)
for i in range(N): check(shuffled(rnd))
for fixed in ([MIN, RSK, MD, RD] + OTHERS, OTHERS + [MIN, RSK, MD, RD], [MIN, MD, RSK, RD] + OTHERS[::-1], [MIN, RSK, RD, MD] + OTHERS, [MIN, MD] + OTHERS + [RSK, RD]):
    check(fixed)
print("random orders:", N, "seed", SEED, "| orders checked in total:", stats["orders"], "| orders where all four of ours applied:", stats["ours_all_applied"])
print("attributable failures:", len(bad))
for b in bad[:30]: print("  ", b)
shutil.rmtree(tmp, ignore_errors=True)
