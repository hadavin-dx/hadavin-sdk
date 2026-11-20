import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
d = [k for k in a["out"] if a["out"][k] != b["out"].get(k)]
print("changed:", d)
for k in d: print(" ", k, repr(a["out"][k])[:110], "->", repr(b["out"][k])[:110])
print("non-idempotent in B:", [k for k, v in b["idem"].items() if not v])
