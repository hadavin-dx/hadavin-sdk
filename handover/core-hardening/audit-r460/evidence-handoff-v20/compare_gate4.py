"""Compare one gate4 run with the saved baseline (readiness major Ma1 of the v18 review).
usage: python -I compare_gate4.py <prefix-of-new-run>   (files <prefix>-ruff.txt, -format.txt, -pytest.txt, -perf.txt, -bandit.txt)
Exit 0 only if: ruff, format, perf and bandit end rc=0, AND every failing test name in the new pytest output
is also a failing test name in baseline/raw-gate4-base-pytest.txt (same or fewer failures).
The failing names are the '____ test_name ____' headings of the FAILURES section (this repository's pytest
config prints no FAILED lines in the short summary, so -rfs alone gives no ids: found while writing this)."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = re.compile(r"^_{3,} (\S+) _{3,}$")

def names(path):
    out, on = [], False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("=") and " FAILURES " in line:
                on = True
            elif line.startswith("=") and on and " short test summary" in line:
                on = False
            elif on:
                m = HEAD.match(line)
                if m:
                    out.append(m.group(1))
    return out

def last(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [x.rstrip("\n") for x in f if x.strip()]
    return lines[-1] if lines else "(empty)"

def main(argv):
    if len(argv) != 2:
        print("usage: compare_gate4.py <prefix>", file=sys.stderr)
        return 2
    p = argv[1] if os.path.isabs(argv[1]) else os.path.join(HERE, argv[1])
    bad = 0
    for n in ("ruff", "format", "perf", "bandit"):
        rc = last(f"{p}-{n}.txt")
        print(f"{n}: {rc}")
        bad |= rc != "rc=0"
    base = set(names(os.path.join(HERE, "baseline", "raw-gate4-base-pytest.txt")))
    new = names(f"{p}-pytest.txt")
    extra = sorted(set(new) - base)
    print(f"pytest failing names in baseline: {len(base)}; in this run: {len(set(new))}; new ones: {len(extra)}")
    for e in extra:
        print("NEW FAILURE:", e)
    bad |= bool(extra)
    print("pytest last line:", last(f"{p}-pytest.txt"))
    # a collection error or a crash prints no failure heading: read the summary line too
    def summ(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            hits = [x for x in f if re.search(r"\d+ (passed|failed)", x) and " in " in x]
        return hits[-1] if hits else ""
    for label, path in (("this run", f"{p}-pytest.txt"), ("baseline", os.path.join(HERE, "baseline", "raw-gate4-base-pytest.txt"))):
        line = summ(path)
        print(f"pytest summary ({label}):", line.strip() or "(none found)")
    new_line = summ(f"{p}-pytest.txt")
    if not new_line or re.search(r"\d+ errors?", new_line):
        print("PROBLEM: no summary line or an error count in the pytest summary")
        bad = 1
    m = re.search(r"(\d+) failed", new_line)
    mb = re.search(r"(\d+) failed", summ(os.path.join(HERE, "baseline", "raw-gate4-base-pytest.txt")))
    if m and mb and int(m.group(1)) > int(mb.group(1)):
        print("PROBLEM: more failed tests than the baseline")
        bad = 1
    return 1 if bad else 0

sys.exit(main(sys.argv))
