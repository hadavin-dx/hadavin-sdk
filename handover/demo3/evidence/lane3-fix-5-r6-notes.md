# lane3-fix-5 round 6 notes (builder B12) - checkpoint 1, 2026-11-14 ~04:25Z
Done: tests first (raw/b12-fails-before.log: 15 failed on the r5 tree), fixes in reset.sh, reset.ps1, README, tests/support.py. Targeted run 162 passed 6 skipped; ruff check and format clean.
Next: mutation run (running), re-make patch, apply check on fresh base, one full serial run.
Open: A-M2 (reset.ps1 never run on Windows: no PowerShell here).

## Checkpoint 2 (lead request applied)
Scripts and tests are done. Patch re-made BEFORE the full run: /home/user/hadavin-sdk/handover/demo3/evidence/lane3-fix-5-r6.patch (git diff --cached --binary -U1 from f3c39cf8; -U1 so it applies on base AND on base+claims-stack-on-f3c39cf8.patch; both git apply --check rc=0). reset.ps1 exit 7 on a pid folder is in it. Added test: two threads as gw0/gw1 call free_port 200 times each at once: distinct, inside 40000-44999 and 45000-49999 (a mutant giving every worker range 0 fails it). Full run still waits for a heavy slot (>=3 pytest runs machine-wide).
full run started 2026-11-14T04:08:48Z, slot count was 2 (<3)

## Checkpoint 3 (04:35Z): FIRST FULL RUN FAILED (honest)
Run 1 on b12-tree: 15 failed, 3818 passed, 176 skipped, rc=1 (raw/b12-full-run1-15failed.log). Causes, both mine or environment:
- 14 in tests/test_reset_ps1_links.py: its order guard required `Get-Content` in reset.ps1 (my new bounded .NET read replaced it). Fixed: the guard now names `[System.IO.File]::Open` as the pid read and still refuses a `Get-Content` before the refusal. My targeted run had not included that file.
- 1 in test_hygiene_scan_public: (a) my new test used `threading.local` / `.local`, which the repository's pattern scan reports (fixed: dict keyed by thread id); (b) gitleaks `git` scans ALL refs of the shared repo, and remotes/origin/n8n-evidence-rerun (commit ad612e2, not an ancestor of the base) holds hash lines in demo_only/n8n_evidence: not from this patch. `gitleaks git --log-opts=HEAD` finds no leaks. Not fixed in the shared repo (not my branch). The final run therefore uses a clean repo b12-chk-final (history of f3c39cf8 only) with the patch applied; tree id equals b12-tree.
Patch re-made: lane3-fix-5-r6.patch sha256 0117c654be77c9b9d9b1e9902c8141660a959035be038a897082e8f910c40eba; git apply --check rc=0 on base and on base+claims-stack.
Final full run started 04:35Z in b12-chk-final.

## Final: full serial run on final head (b12-chk-final, tree d144d6d9): 3833 passed, 176 skipped in 1267.36s, rc=0 (raw/b12-full-final.log)
