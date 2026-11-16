"""usage: python -I fences_counts_v13.py fences|counts <doc>... ; parses python fences; counts PR ids and stale names."""
import ast, re, sys, os
mode = sys.argv[1]
if mode == "fences":
    n = bad = 0
    for doc in sys.argv[2:]:
        t = open(doc, encoding="utf-8").read().split("\n"); i = 0
        while i < len(t):
            if t[i].strip().startswith("```python"):
                j = i + 1
                while not t[j].strip().startswith("```"): j += 1
                n += 1
                try: ast.parse("\n".join(t[i+1:j])); print("%s:%d python fence parses (%d lines)" % (os.path.basename(doc), i+1, j-i-1))
                except SyntaxError as e: bad += 1; print("%s:%d SYNTAX ERROR %s" % (os.path.basename(doc), i+1, e))
                i = j
            i += 1
    print("python fences=%d syntax_errors=%d" % (n, bad)); sys.exit(1 if bad else 0)
else:
    main = open(sys.argv[2], encoding="utf-8").read(); other = open(sys.argv[3], encoding="utf-8").read()
    d = os.path.dirname(os.path.abspath(sys.argv[2])) + "/evidence-handoff-v13/"
    print("main lines:", main.count("\n"), "other lines:", other.count("\n"))
    print("mentions of 'v12' in main:", main.count("v12"), "in other:", other.count("v12"))
    names = set(re.findall(r"`((?:raw-|cites-table|[a-z_0-9]+_v13)[A-Za-z0-9_.\-*]*)`", main + other))
    missing = []
    for nme in sorted(names):
        if "*" in nme:
            import glob; ok = bool(glob.glob(d + nme))
        else: ok = os.path.exists(d + nme)
        if not ok: missing.append(nme)
    print("evidence names cited:", len(names), "missing from evidence-handoff-v13:", len(missing)); [print("  MISSING", m) for m in missing]
    sys.exit(1 if missing else 0)
