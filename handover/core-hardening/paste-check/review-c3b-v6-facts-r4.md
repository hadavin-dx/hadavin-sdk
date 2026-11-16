# C3b v6 round 4, facts (egm codebase reviewer), condensed copy, 2026-11-16
Blockers none. Majors none. Marker lines 125, 258, 275, 433, 434, 585, 586 hold (17 markers on 10 lines, derived from hunk headers); counts 24 10 2 1 hold; R2 claims match evidence-c7g.md 12.2.
Not checked: could not run patch (read-only); did not hash the patch file now (evidence says 8a83abaa...0011d2, so it applies only if the file is unchanged since).
Minor: the early branch "pid gone but N group processes left: STOP" (patch line 60) has no test case (only ever stops). R2 evidence is Linux stand-ins, not WSL.
