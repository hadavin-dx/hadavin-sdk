"""Check every  path:line "quote"  citation (PLAN-002 section 6). Never judges meaning.
Usage: python3 tools/check_citations.py <repo_root> <out_tsv> <file.md> [...]  (exit 1 if any not FOUND)"""
import re, sys, os

CITE = re.compile(r'`?([\w./\-]+):(\d+)\s+"([^"\n]{12,120})"`?')
LIKE = re.compile(r'[\w./\-]+:\d+\s+"')  # anything that looks like a citation start
# quotes shorter than 12 characters do not parse, so they are counted as UNPARSED


def check(root, path, line, quote, window=5):
    base = os.path.realpath(root)
    full = os.path.realpath(os.path.join(base, path))
    if os.path.isabs(path) or not full.startswith(base + os.sep) or not os.path.isfile(full):
        return "NO-FILE"
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
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
        text = open(f, encoding="utf-8", errors="replace").read()
        found = list(CITE.finditer(text))
        if not found:
            rows.append((os.path.basename(f), "-", "0", "NO-CITATION"))  # every input file must cite something
        for m in found:
            rows.append((os.path.basename(f), m.group(1), m.group(2), check(root, m.group(1), m.group(2), m.group(3))))
        n_like = len(LIKE.findall(text))
        if n_like > len(found):
            rows.append((os.path.basename(f), "-", str(n_like - len(found)), "UNPARSED"))  # citation-like text the pattern did not parse
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
