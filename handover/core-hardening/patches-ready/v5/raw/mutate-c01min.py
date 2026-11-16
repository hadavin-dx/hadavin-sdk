"""Hand-made mutants for C-01-MINIMAL v5. Usage: python mutate.py <work tree>. Each mutant: edit one file, run the
two test files, record the first failing test (or SURVIVED), restore the file. Run alone: it rewrites src/ files."""
import pathlib, subprocess, sys

W = pathlib.Path(sys.argv[1])
CFG, REP, DEF = "src/hadavin_sdk/config.py", "src/hadavin_sdk/k1b/replay.py", "src/hadavin_sdk/defaults.py"
GUARD = 'refused += _route_refusals(self.routes, self.max_route_tokens)'
MUTANTS = [
    ("M1 input price >0 -> >=0", CFG, "route.input_usd_per_mtok > 0 and", "route.input_usd_per_mtok >= 0 and"),
    ("M2 output price >0 -> >=0", CFG, "and route.output_usd_per_mtok > 0", "and route.output_usd_per_mtok >= 0"),
    ("M3 ceiling > -> >=", CFG, "r.max_tokens > max_route_tokens", "r.max_tokens >= max_route_tokens"),
    ("M4 only -1 kills: >0 -> != 0 on both prices", CFG,
     "route.input_usd_per_mtok > 0 and route.output_usd_per_mtok > 0",
     "route.input_usd_per_mtok != 0 and route.output_usd_per_mtok != 0"),
    ("M5 route refusals dropped", CFG, "            " + GUARD, "            pass"),
    ("M6 refused += turned into =", CFG, "            " + GUARD, "            refused = _route_refusals(self.routes, self.max_route_tokens)"),
    ("M7 default ceiling 2_000_000", DEF, "MAX_ROUTE_TOKENS = 200_000", "MAX_ROUTE_TOKENS = 2_000_000"),
    ("M8 rule also applied in dev (moved out of the non-dev block)", CFG,
     "            " + GUARD + "\n        refused += _anchor_refusals", "        " + GUARD + "\n        refused += _anchor_refusals"),
    ("M9 ceiling read from the constant, not from config", CFG, "_route_refusals(self.routes, self.max_route_tokens)", "_route_refusals(self.routes, defaults.MAX_ROUTE_TOKENS)"),
    ("M10 replay keeps a private zero-only rule (negative passes)", REP,
     "not route_prices_above_zero(route)", "(route.input_usd_per_mtok == 0 or route.output_usd_per_mtok == 0)"),
    ("M11 replay fake exemption inverted", REP, 'llm_kind != "fake" and not route_prices', 'llm_kind == "fake" and not route_prices'),
    ("M12 shared predicate checks input price only", CFG, " and route.output_usd_per_mtok > 0", ""),
]
TESTS = ["tests/test_c01_minimal_route_limits.py", "tests/test_k1b_replay.py"]


def run():
    r = subprocess.run(["uv", "run", "--all-extras", "--group", "test", "pytest", "-x", "-q", "-p", "no:cacheprovider", *TESTS],
                       cwd=W, capture_output=True, text=True)
    fails = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    return r.returncode, (fails[0] if fails else "")


rc, _ = run()
print(f"BASELINE (unmutated) rc={rc}", flush=True)
for label, rel, old, new in MUTANTS:
    p = W / rel
    orig = p.read_text(encoding="utf-8")
    if orig.count(old) != 1:
        print(f"{label} | NOT APPLIED (pattern count {orig.count(old)})", flush=True)
        continue
    p.write_text(orig.replace(old, new), encoding="utf-8")
    try:
        rc, first = run()
    finally:
        p.write_text(orig, encoding="utf-8")
    print(f"{label} | {'KILLED' if rc != 0 else 'SURVIVED'} | {first}", flush=True)
rc, _ = run()
print(f"AFTER RESTORE rc={rc}", flush=True)
