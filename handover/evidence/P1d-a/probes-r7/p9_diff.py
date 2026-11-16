"""P9 S8 differential over a real population: every line of the repo's own files that holds a key word (the lines the changed entries can touch).
usage: python p9_diff.py <base_tree> <new_tree>   Runs each tree in a subprocess; compares redact_text(line, RunMap()) per line."""
import sys, subprocess, json, pathlib, re, os, collections
if len(sys.argv) == 4 and sys.argv[1] == "--worker":
    sys.path.insert(0, sys.argv[2] + "/src")
    from hadavin_sdk.guard import runmap
    lines = json.load(open(sys.argv[3]))
    out = []
    for l in lines:
        try: out.append(runmap.redact_text(l, runmap.RunMap()))
        except Exception as e: out.append("ERR " + type(e).__name__)
    json.dump(out, sys.stdout); sys.exit()
KW = re.compile(r"(?i)password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session")
root = pathlib.Path("/home/user/hadavin-sdk")
files = [p for d in ("src", "tests", "tools", ".github", "demos", "docs", "handover") for p in (root / d).rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".json", ".cfg", ".ini", ".sh"} and ".venv" not in p.parts and "snapshot" not in str(p) and "evidence" not in p.parts]
lines, src = [], []
for p in files:
    try:
        for l in p.read_text(encoding="utf-8").splitlines():
            if KW.search(l) and ("=" in l or ":" in l) and len(l) < 2000: lines.append(l); src.append(p.relative_to(root).parts[0])
    except Exception: pass
tmp = "/tmp/p9_lines.json"; json.dump(lines, open(tmp, "w"))
res = [json.loads(subprocess.run([sys.executable, __file__, "--worker", t, tmp], capture_output=True, text=True, check=True).stdout) for t in sys.argv[1:3]]
flip = collections.Counter(); tot = collections.Counter(); ex = collections.defaultdict(list)
for l, s, a, b in zip(lines, src, *res):
    tot[s] += 1
    if a != b:
        flip[s] += 1
        if len(ex[s]) < 3: ex[s].append((l[:110], a[:110], b[:110]))
print("lines with a key word and = or :", len(lines), dict(tot)); print("flips base->new:", sum(flip.values()), dict(flip))
for s, v in ex.items():
    for l, a, b in v: print(s, "|", repr(l), "\n   base", repr(a), "\n   new ", repr(b))
ph = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
fewer = [(l, a, b) for l, a, b in zip(lines, *res) if a != b and len(ph.findall(b)) < len(ph.findall(a))]
more = sum(1 for l, a, b in zip(lines, *res) if a != b and len(ph.findall(b)) > len(ph.findall(a)))
same = sum(1 for l, a, b in zip(lines, *res) if a != b and len(ph.findall(b)) == len(ph.findall(a)))
print("flips with more placeholders in new:", more, "| same count:", same, "| FEWER placeholders in new (possible exposure):", len(fewer))
for l, a, b in fewer[:6]: print("  line", repr(l[:100]), "\n   base", repr(a[:100]), "\n   new ", repr(b[:100]))
