# C3b re-pin v6, round 3, facts reviewer (codebase-details), condensed copy, 2026-11-16
Verdict: 0 Blockers, 1 Major, 5 Minor/Nit. Not checked: nothing run (patch, git apply, bash -n, awk, stand-in); patched-plan line numbers from hunk arithmetic; Git Bash/WSL/PowerShell not tested.
Confirmed by reading: 15 hunks, all headers match; counts 24/10/2/1 on patched plan and 0/0/2/0 unpatched are consistent; acc5.sh traced by hand against 18 cases; round-2 majors 1-4 fixed.
## Major
- LEAD-FILL-list-v5.md marker-places column (rows 1,1b,2,4,6,7): every number below line 4 is 2 too low (list says 123, 256, 273, 431, 432, 583, 584; patched plan has 125, 258, 275, 433, 434, 585, 586). 256 is the P-3b line, not P-4b. Fails safe (checklist A7 grep lists true places) but is a false statement. Fix: renumber or drop numbers.
## Minor / Nit
evidence-c7g.md:493 says "scanned separately below" but no scan follows (claim 0 hits is true by reviewer's own scan). REPORT-repin-v6.md item 5 zombie-leader case untested in evidence. Checklist C6 uses $PC set only in A3. grep -c exit 1 on a 0 count is normal (nit). R5 sentence "differs from the first v5 text" still present. acc5.sh does not enforce block order (accepted/rejected cases unaffected).
