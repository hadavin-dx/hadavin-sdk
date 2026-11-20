"""G9 v3 evidence: compare two dumps of g9_corpus_diff.py (argv[1] = the base's, argv[2] = the build's)."""
import json, sys
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
diff = [k for k in a if a[k][1:] != b[k][1:]]
print("inputs", len(a), "rows that differ", len(diff))
for k in diff[:8]: print(" ", k, "\n   head", str(a[k][1:])[:300], "\n   build  ", str(b[k][1:])[:300])
rf = lambda d, i: sum(1 for v in d.values() if isinstance(v[1], list) and v[1][i] is False)
print("restore failures head/build", rf(a, 1), rf(b, 1), "| second redact changes head/build", rf(a, 2), rf(b, 2))
print("raised head/build", sum(isinstance(v[1], str) or isinstance(v[2], str) for v in a.values()), sum(isinstance(v[1], str) or isinstance(v[2], str) for v in b.values()))
print("second redact_text changes head/build", sum(1 for v in a.values() if isinstance(v[2], list) and v[2][0] != v[2][1]), sum(1 for v in b.values() if isinstance(v[2], list) and v[2][0] != v[2][1]))
