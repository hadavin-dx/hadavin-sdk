# C8b round-2 reviews (condensed copies of two inline reports), 2026-11-16
Facts reviewer: numbers and per-mutant evidence hold (50 raw files; C-01 13 killed + 7 survived of 20; A-01 15 + 12 of 27; restore rc=0 everywhere). Not run: git status, tests.
- MAJOR REPORT.md:27 wrong explanation of 46 vs 104: v1 kill runs used `-x` and only the new A-01 test file; only v1 survivors ran the 104 set. v2 logs are clean.
- Nit: line 16 stale (A-01-m09/m08 proof exists: two failing tests). Nit: say the proof baseline is one file per lane. Nit: no end-of-loop diff of scratch trees vs fresh archive. Nit: `# noqa: F811` in proof-tests/test_a01_extra_proof.py lines 32, 123 (repo rule: no suppressions).
Design reviewer: not acceptable as merge evidence.
- BLOCKER B1: lane tests v1 patches, not v2 that will merge; proof tests match v1 message. Rerun whole lane on v2, label report v1-only meanwhile.
- MAJOR M1 missing mutants: NaN/Infinity price (biggest money gap), v2 _finite/is_finite/zero_ok/keyless_loopback, price boundaries, max_tokens literals, route position, drain ORDER BY and order, except order and widening, failed DELETE, failing-step rule (remaining>0), backlog exception swallowed, last_corrupt reset.
- MAJOR M2 run.py still leaves .restore-copy in the lane folder. M3 run.py crash/SIGKILL leaves mutation and the next run bakes it in (circular check): temp backup outside repo, hash baseline vs git show, refuse real-repo or dirty root, trap SIGTERM.
- MAJOR M4 claims without raw: diff -rq identity, overwritten first m18 proof run, full suite/ruff/bandit not run.
- Nits: yaml sort fragility, m15 killed only collaterally, hand-made mutants (consider mutmut), full-suite output not linked.
