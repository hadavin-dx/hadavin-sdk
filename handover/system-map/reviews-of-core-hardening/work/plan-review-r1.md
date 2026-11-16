# Plan review round 1 (of max 3) for reviews-of-core-hardening/PLAN.md. Saved by the session lead from hand-backs.

## Zoom-out (0 Blocker, 3 Major, 4 Nit) - completed
- Z-M1: the miss-hunters H1, H2 and V5 must not be given the target's findings or verdict columns (they would anchor). Brief H1/H2 with area and rules only; diff their candidates against AUDIT-FINDINGS afterwards. V5 classifies each item itself from callers and importers first, then compares.
- Z-M2: verification favours confirmation. (a) A quote that exists does not prove the conclusion follows. (b) Lead also samples WRONG and UNVERIFIABLE lines of agents, not only CONFIRMED. (c) Each of the 5 Blockers needs a second look (a second verifier or the lead). (d) Add a column "severity agrees / too high / too low".
- Z-M3: evidence runner checks only quote existence. Add: count and list of findings or MASTER-MAP statements with no `path:line "quote"`; count of citations whose file or line does not exist in snap/, separate from quote mismatch.
- Z-N1: list the 22 src files that differ between b4cce5b and my branch head; flag any cited file or dead-module claim in them (mechanical, in the evidence runner).
- Z-N2: "at least 50 of 80" versus "60 percent" disagree; "no program is run" vs the runner running Python (say "no product program"); `check_citations.py-style` unclear (reuse unchanged); justify the count script or use grep -c.
- Z-N3: plan omits register-before-start, status block every 10 minutes, 60-minute builder box (ORDER 002 rules unchanged).
- Z-N4: name the "part 1 result" file; say verifiers read handover files with `git show origin/cloud/core-hardening:path`.
- Coverage nit: "generic building blocks" only thin in H2: add one line to H2 to flag demo-local generic code without a promotion entry.

## Implementation-readiness: pending
