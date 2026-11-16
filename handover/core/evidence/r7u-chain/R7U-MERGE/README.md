# R7U merge tools (rehearsed on dummy diffs only; real A/B/C diffs not yet used)
1. `./merge.sh <new-tree>`  copies tree-R7T, dry-runs then applies out/R7U-{A,C,B}/r7u-X.diff in order A, C, B (`patch -p1 --fuzz=0 --binary`).
   Override with env DIFF_A/DIFF_B/DIFF_C, BASE, TREE_A/B/C. Refuses if `<new-tree>` exists (exit 3); a rejected hunk stops it (exit 5, names file and hunk, tree left as is).
   Prints overlapping files, per-builder "same/differs in merged tree" and files changed in a builder tree but missing from its diff, then `diff -rq` vs tree-R7T. Report files: `<new-tree>-merge-report/`.
2. `./guard_run.sh <tree> [--name N] [--list FILE] [--wait]`  staged git copy (git init + add, no commit) in out/R7U-MERGE/N/stage, no network, timeout 2400 s, detached.
   Default list = load tests + test_r7k_findings, the r7t guard list (out/R7T/guard-files-r7t.txt), test_r7u_a/b/c_findings, tests/test_*loopback*.py; files missing from the tree are left out with a WARN (N/guard.warn).
   Results: N/guard.log, N/guard.wrap (start/end), N/guard.rc (appears at the end; a killed run has no rc file). Default name `guard`; refuses if N exists.
3. `./package.sh <tree-R7U> [outdir]`  builds the 3 patches (.gz via gzip -9 -n, unpacked sha256 asserted), sha256-r7u.txt, apply-matrix-r7u.txt (a-crlf, b-crlf, c-lf, plus delta check), snapshot-r7u/ with MANIFEST.txt. Default outdir out/R7U-MERGE/pkg; refuses if it exists.
Typical: `./merge.sh /home/user/build/rr6/tree-R7U && ./guard_run.sh /home/user/build/rr6/tree-R7U && ./package.sh /home/user/build/rr6/tree-R7U` (package after the guard run is green, wait for N/guard.rc).
Rehearsal logs: dummy/*.log. Needs about 7 MB per tree copy and about 25 MB for package.sh scratch (removed at the end).
