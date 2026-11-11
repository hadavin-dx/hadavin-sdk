import sys, random, runpy, importlib.util
root = sys.argv[1]
sys.path.insert(0, root)
spec = importlib.util.spec_from_file_location("mm", root + "/tests/mutation_runner_mutants.py")
src = open(root + "/tests/mutation_runner_mutants.py").read().split('if __name__ == "__main__":')[0]
ns = {"__file__": root + "/tests/mutation_runner_mutants.py", "__name__": "mm"}
exec(compile(src, "mutants", "exec"), ns)
M = ns["M"]
print("total mutants", len(M), flush=True)
random.seed(89)
kw = [m for m in M if m.test_file.endswith("keywords.py")]
oth = [m for m in M if not m.test_file.endswith("keywords.py")]
sample = random.sample(kw, 45) + random.sample(oth, min(15, len(oth)))
print("sample", len(sample), "kw", 45, flush=True)
def show(row):
    n, v, t, g = row
    print(("ok " if g else "BAD"), f"{v:12}", n, "[", t.split("::")[-1][:60], "]", flush=True)
res = ns["run_mutants"](root, sample, [ns["TEST"], ns["KW"]], extra_dirs=("tests/fixtures", "tools"), conftest="tests/conftest.py", on_result=show)
bad = [n for n, _, _, g in res if not g]
print(f"{len(res)-len(bad)} of {len(res)} good; problems: {bad}")
sys.exit(1 if bad else 0)
