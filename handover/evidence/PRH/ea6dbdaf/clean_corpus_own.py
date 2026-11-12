"""EVIDENCE RUNNER: clean-corpus withheld share. Usage: python clean_corpus_own.py <tree-root>. Texts: every line of the repository's own
prose/source in <tree-root> (README, CHANGELOG, SECURITY, docs, src), grouped into texts of 8 lines, plus ordinary hidden items
(colour codes, tabs, joiners). Each text is run through tools.prepare_output with a handed-out made-up secret that is NOT in the text.
Counts withheld outputs."""
import sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "src"))
from hadavin_sdk import tools
HAND = "Qx7mLp" + "-9vRtzKw2"
lines = []
for top in ("README.md", "CHANGELOG.md", "SECURITY.md", "docs", "src"):
    p = root / top
    fs = [p] if p.is_file() else sorted(p.rglob("*")) if p.exists() else []
    for f in fs:
        if f.is_file() and f.suffix in {".md", ".py", ".txt"} and "__pycache__" not in f.parts:
            try: lines += f.read_text(encoding="utf-8").splitlines()
            except Exception: pass
ESC = "\x1b"
texts = []
for i in range(0, len(lines) - 8, 8):
    t = "\n".join(lines[i:i + 8]); texts.append(t)
    texts.append(ESC + "[1;32m" + t.replace("\n", ESC + "[0m\n", 1) + ESC + "[0m")
    texts.append(t.replace(" ", "​ ", 2))
n = bad = 0; ex = []
for t in texts:
    n += 1
    try: o = tools.prepare_output(t, {}, 100000, [HAND])
    except Exception as e: bad += 1; ex.append(type(e).__name__); continue
    if "withheld" in o or o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "":
        bad += 1
        if len(ex) < 5: ex.append(t[:60])
print("tree", tools.__file__); print(f"texts={n} withheld_or_error={bad} share={bad/max(n,1):.5f}"); print(ex)
