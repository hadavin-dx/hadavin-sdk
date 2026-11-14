# lane3-fix-5 round 6 notes (builder B12) - checkpoint 1, 2026-11-14 ~04:25Z
Done: tests first (raw/b12-fails-before.log: 15 failed on the r5 tree), fixes in reset.sh, reset.ps1, README, tests/support.py. Targeted run 162 passed 6 skipped; ruff check and format clean.
Next: mutation run (running), re-make patch, apply check on fresh base, one full serial run.
Open: A-M2 (reset.ps1 never run on Windows: no PowerShell here).

## Checkpoint 2 (lead request applied)
Scripts and tests are done. Patch re-made BEFORE the full run: /home/user/hadavin-sdk/handover/demo3/evidence/lane3-fix-5-r6.patch (git diff --cached --binary -U1 from f3c39cf8; -U1 so it applies on base AND on base+claims-stack-on-f3c39cf8.patch; both git apply --check rc=0). reset.ps1 exit 7 on a pid folder is in it. Added test: two threads as gw0/gw1 call free_port 200 times each at once: distinct, inside 40000-44999 and 45000-49999 (a mutant giving every worker range 0 fails it). Full run still waits for a heavy slot (>=3 pytest runs machine-wide).
full run started 2026-11-14T04:08:48Z, slot count was 2 (<3)
