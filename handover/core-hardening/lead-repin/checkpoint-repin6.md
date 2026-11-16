# Checkpoint repin6 (builder, lead re-pin v6)

Time: 15:33 UTC (21:03 IST). Started 15:10 UTC. Hard stop 16:10 UTC (21:40 IST).

Done (script, not yet frozen):
- v5 kept as lead-repin-verify.v5.sh and LEAD-REPIN-VERIFY.v5.md.
- Baseline: v5 shows 13 of 13 values on the security review's forms (evidence-repin6/baseline-v5-result.txt).
- v6 script: password-in-URL forms, password flags after commands, multi-line values (pre-stage), non-ASCII names fail closed, per-line length guard, dotted/CamelCase fix, planned counts (canary 1167, whole self-test 1191), signal cleanup of every program below the script, zombie-safe stray check, new self-tests (planned-count forging, pre-main TERM promptness, time limit).
- Self-test: 1191 passed, 0 failed under dash and bash. The same v6 cases run against the v5 filter: 136 fail (evidence-repin6/selftest-v6-cases-against-v5.txt).
Found and fixed on the way: a stray-program check that counted an uncollected finished program (state Z) as running; multi-line hiding that swallowed the closing bracket of a JSON list.

Next: rewrite LEAD-REPIN-VERIFY.md, set the 4 citation rows, freeze, final evidence (syntax, self-test x2, signals, non-root, 49+ probe lines, mutation run, timing, banned-string count, sha256), v6-CHANGES.md, report.
Not run: busybox, macOS, WSL, Windows, the real test program.
