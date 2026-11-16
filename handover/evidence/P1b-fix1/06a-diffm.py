import sys, importlib.util
def load(p, root):
    sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location("m"+str(abs(hash(p))), p); m = importlib.util.module_from_spec(spec)
    src = open(p).read().split("if __name__")[0]
    g = {"__file__": p, "__name__": "x"}
    exec(compile(src, p, "exec"), g); sys.path.pop(0)
    return g["M"]
new = load("/home/user/build/B-P1b/tests/textnorm_mutants.py", "/home/user/build/B-P1b")
old = load("/tmp/claude-0/old_mut.py", "/home/user/build/B-P1b")
key = lambda m: (m.file, m.old, m.new, m.only_test, m.expect, getattr(m,'test_file',None))
od = {m.name: key(m) for m in old}
ch = [m.name for m in new if m.name not in od or od[m.name] != key(m)]
gone = [n for n in od if n not in {m.name for m in new}]
print(len(old), len(new), "changed_or_new", len(ch), "removed", len(gone))
open("/tmp/claude-0/changed_mutants.txt","w").write("\n".join(ch))
print("\n".join("NEW/CHG: "+n for n in ch)); print("\n".join("GONE: "+n for n in gone))
