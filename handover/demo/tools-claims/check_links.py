"""Throwaway: every markdown link, anchor and file reference in README.md, docs/*.md, versions.md (also SECURITY.md, contract.md)."""
import glob, os, re, sys
root = sys.argv[1]; os.chdir(root)
files = ["README.md", "SECURITY.md", "versions.md", "contract.md"] + sorted(glob.glob("docs/*.md"))
def slug(h):
    h = h.strip().lower()
    h = re.sub(r"[`*_]", "", h)
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")
anchors = {}
for f in files:
    a = set(); seen = {}
    for l in open(f, encoding="utf-8"):
        m = re.match(r"^#{1,6}\s+(.*)$", l)
        if m:
            s = slug(m.group(1)); n = seen.get(s, 0); seen[s] = n + 1
            a.add(s if n == 0 else f"{s}-{n}")
    anchors[f] = a
bad = []; ok = 0
for f in files:
    for ln, l in enumerate(open(f, encoding="utf-8"), 1):
        for m in re.finditer(r"\[([^\]]*)\]\(([^)\s]+)\)", l):
            tgt = m.group(2)
            if re.match(r"^(https?:|mailto:)", tgt): continue
            path, _, anc = tgt.partition("#")
            tf = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
            if path and not os.path.exists(tf): bad.append((f, ln, tgt, "file missing")); continue
            if anc:
                if tf.endswith(".md") and tf in anchors and anc.lower() not in anchors[tf]:
                    bad.append((f, ln, tgt, "anchor missing")); continue
            ok += 1
        # in-text references: see "Heading" under, docs/x.md, files in backticks handled elsewhere
        for m in re.finditer(r"(?<![\w/.-])((?:docs/|src/|tests/|scripts/|demo_only/|load_tools/|tools/|n8n/|\.github/)[\w./\-]+\.[A-Za-z0-9]+)", l):
            p = m.group(1).rstrip(".")
            if re.search(r"[<>*{}]", p): continue
            if os.path.exists(p): ok += 1
            else: bad.append((f, ln, p, "referenced file missing"))
        for m in re.finditer(r"`([A-Za-z0-9_.\-]+\.md)`", l):
            p = m.group(1)
            hits = [x for x in glob.glob("**/" + p, recursive=True)] + ([p] if os.path.exists(p) else [])
            if not hits: bad.append((f, ln, p, "named md file missing"))
            else: ok += 1
        for m in re.finditer(r'(?:see|See|under|in) (?:the )?(?:section )?"([^"]{3,60})"', l):
            h = slug(m.group(1))
            if not any(h in a for a in anchors.values()):
                bad.append((f, ln, m.group(1), "quoted section name: no heading with that name"))
print(f"ok references: {ok}; broken: {len(bad)}")
for b in bad: print("BROKEN", *b, sep=" | ")
