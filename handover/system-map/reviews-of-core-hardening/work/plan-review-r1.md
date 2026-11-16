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

## Implementation-readiness (2 Blocker, 9 Major, 6 Nit) - completed
- R-B1: paths undefined: snapshot path (scratch folder snap/ has no absolute path and no owner), the checker ("check_citations.py-style"), the count script.
- R-B2: part 1 result file is never named; how target files are fetched (git show origin/cloud/core-hardening:handover/core-hardening/<file>) and where copies sit; exact target file list (MASTER-MAP.md, AUDIT-FINDINGS.md, patches/).
- R-M1: output file names, report format (columns, "what was not checked" header) and input list per agent (V1-V5, H1, H2, runner).
- R-M2: ORDER 002 process rules missing: register each agent in REPORT.md before starting; status block every 10 minutes (UTC and IST); check at expected end; close; end-of-work sweep with counts. (the plan says a 20-minute checkpoint note.)
- R-M3: sampling rule ambiguous: ids not defined ("odd ids"), "50 of 80" vs "60 percent" (48), "if time allows" not a guarantee; lanes A, X, D1, D2, D3 not defined. Pick one hard floor and say what happens on a shortfall.
- R-M4: no criteria: CONFIRMED / WRONG / UNVERIFIABLE (line moved, claim true but severity wrong, needs a runtime); H1 patterns (vendor SDK list, kind-module dir, secret patterns, wildcard policies, roots); H2 definition of dead and duplicate; quote rule for H1/H2.
- R-M5: sample size and selection of the lead's check of agent lines; reviewer line-up and files each reads; reviewers return inline so the lead saves reports; how resolve output is applied to the three deliverables.
- R-M6: "claims without evidence" not covered (owner and method: statements without path:line or stated verified without a command).
- R-M7: no RUNG TABLE (component | need | rung tried | evidence | what only our code gives | verdict); check whether grep -c covers the count script.
- R-M8: CORRECTIONS.md format: patch files (unified diffs in reviews-of-core-hardening/patches/, one per finding id).
- R-M9: stop rule incomplete: what happens when a Blocker or Major remains after round 2; 09:30 UTC hard stop (partial output, FINAL says so); REVIEW.md verdict scale and thresholds.
- Nits: who lists the 22 differing src files; the runner runs a script it did not write; LEDGER status values, id scheme, date format (UTC); egm-resolve runs on opus via the Skill, no haiku; dependency order and parallelism; add shell hygiene to MUST-NOT.
