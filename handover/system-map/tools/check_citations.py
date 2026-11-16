"""Check every  path:line "quote"  citation (PLAN-002 section 6). Never judges meaning.
Usage: python3 tools/check_citations.py <repo_root> <out_tsv> <file.md> [...]  (exit 1 if any not FOUND)"""
import re, sys, os

CITE = re.compile(r'`?([\w./\-]+):(\d+)\s+"([^"\n]{6,120})"`?')


def check(root, path, line, quote, window=5):
    base = os.path.realpath(root)
    full = os.path.realpath(os.path.join(base, path))
    if os.path.isabs(path) or not full.startswith(base + os.sep) or not os.path.isfile(full):
        return "NO-FILE"
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return "NO-FILE"
    q, n = quote.strip(), int(line)
    if 1 <= n <= len(lines) and q in lines[n - 1]:
        return "FOUND"
    for i in range(max(0, n - 1 - window), min(len(lines), n + window)):
        if q in lines[i]:
            return "LINE-DRIFT"
    return "MISMATCH"


def main(root, out, files):
    rows = []
    for f in files:
        for m in CITE.finditer(open(f, encoding="utf-8", errors="replace").read()):
            rows.append((os.path.basename(f), m.group(1), m.group(2), check(root, m.group(1), m.group(2), m.group(3))))
    with open(out, "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    counts = {}
    for r in rows:
        counts[r[3]] = counts.get(r[3], 0) + 1
    print(counts, "total", len(rows))
    return 0 if rows and set(counts) == {"FOUND"} else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3:]))
