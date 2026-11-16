"""Check 4: every evidence-file name in the two docs exists, or the doc line labels it as not existing yet. Own code."""
import re, os, sys
A = sys.argv[1]; docs = ["CORE-PR-HANDOFF-v14.md", "CORE-PR-HANDOFF-v14-other-tracks.md"]
E = os.path.join(A, "evidence-handoff-v14")
have = {}
for d, _, fs in os.walk(E):
    for f in fs: have.setdefault(f, []).append(os.path.relpath(os.path.join(d, f), E))
LABEL = re.compile(r"(?i)does[- ]not[- ]exist|not exist|does not yet|not yet|doesn.t exist|will be (?:written|made|created|added)|to be (?:written|made|created)|planned|builder writes|new file|not in the folder|future|later")
names = {}
for doc in docs:
    for n, line in enumerate(open(os.path.join(A, doc), encoding="utf-8").read().split("\n"), 1):
        for tok in re.findall(r"`([^`\n]+)`", line):
            t = tok.strip()
            t = re.sub(r":\d+(-\d+)?(,\d+)*$", "", t)
            if re.fullmatch(r"(?:evidence-handoff-v14/)?(?:held-sql/)?[\w.-]+\.(?:txt|py|sql|sh|tsv|json|log)", t) or re.fullmatch(r"evidence-handoff-v1\d(?:-independent)?/[\w./-]+", t):
                names.setdefault((doc, t), []).append((n, bool(LABEL.search(line))))
ex = miss_lab = miss_unlab = other = 0
for (doc, t), occ in sorted(names.items()):
    base = t.split("/")[-1]
    p_a = os.path.join(A, t); p_e = os.path.join(E, t.replace("evidence-handoff-v14/", ""))
    if os.path.exists(p_a) or os.path.exists(p_e) or (base in have and "/" not in t.replace("evidence-handoff-v14/", "").replace("held-sql/", "")) or os.path.exists(os.path.join(E, "held-sql", base)) and "held-sql" in t:
        ex += 1; continue
    # older evidence folders (v13 etc.) or repo files
    alt = [os.path.join(A, d, base) for d in os.listdir(A) if d.startswith("evidence-handoff") and os.path.exists(os.path.join(A, d, base))]
    repo = os.popen(f"find /home/user/hadavin-sdk/src /home/user/hadavin-sdk/tests /home/user/hadavin-sdk/.github -name '{base}' 2>/dev/null | head -1").read().strip()
    lab = any(l for _, l in occ)
    if alt or repo: other += 1; print(f"EXISTS-ELSEWHERE {doc} lines {[n for n,_ in occ][:4]} {t} -> {(alt or [repo])[0].replace(A,'audit-r460')}"); continue
    if lab: miss_lab += 1; print(f"MISSING-LABELLED {doc} lines {[n for n,_ in occ][:4]} {t}")
    else: miss_unlab += 1; print(f"MISSING-NOT-LABELLED-ON-ITS-LINE {doc} lines {[n for n,_ in occ][:6]} {t}")
print(f"names checked {len(names)}: exist in v14 evidence folder {ex}; exist elsewhere {other}; missing and line labels not-yet {miss_lab}; missing and no label on any of its lines {miss_unlab}")
# files in the builder folder that no doc line names (info)
alltxt = "".join(open(os.path.join(A, d), encoding="utf-8").read() for d in docs)
unn = sorted(f for f in have if f not in alltxt)
print(f"INFO files in builder evidence folder never named in either doc: {len(unn)}: {unn[:30]}")
