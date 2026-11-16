"""Every complete `raw-*.txt` name the two v22 documents cite must exist in some evidence-handoff-*/raw/ (or the folder itself). Prints the missing ones."""
import re, glob, os
docs = ["../CORE-PR-HANDOFF-v22.md", "../CORE-PR-HANDOFF-v22-other-tracks.md", "../v22-CHANGES.md", "../v22-OPEN-FOR-LEAD.md"]
have = {os.path.basename(p) for p in glob.glob("../evidence-handoff-*/raw/*") + glob.glob("../evidence-handoff-*/*") + glob.glob("../*")}
cited = {}
for d in docs:
    for m in re.finditer(r"(?<![A-Za-z0-9_-])((?:raw-)[A-Za-z0-9._-]*\.txt)", open(d).read()): cited.setdefault(m.group(1), d)
miss = sorted(n for n in cited if n not in have)
print(f"cited {len(cited)} distinct complete raw names; missing {len(miss)}")
for n in miss: print("MISSING", n, "cited in", os.path.basename(cited[n]))
