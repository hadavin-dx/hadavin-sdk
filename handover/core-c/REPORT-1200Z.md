# core-c report to the lead, 12:00Z (written to handover because the cross-session reply is refused: HTTP 401 / elevated_session_untrusted_device)

## Built, merged on cloud/core-c, under or past result review (all counts TESTED by the builders in their worktrees unless marked)
- E9 (1)(2)(3): built, merged, result review rounds 1 and 2 done (0 leak, 0 vacuous killer; doc fixes + 1 test merged). Fresh round 3 after the last redactor merge.
- G7 round 7, Q9 (E13 resolved), Q16: merged earlier; merged-tree batches 6 and 7 green (2772 passed; 175 passed).
- G8 (glued-rest gap, E-class): built from v6, merged; result review round 1 (design: 1 Major = E16 below; codebase 0 Major), fixes merged; round 2 codebase: 0 Blocker/Major. 451 passed 43 xfailed in the G8 file, 35 of 35 mutants.
- G10 (E11 text-fold deadline): built from v4, merged; result review round 1 (2 Majors fixed), fixes merged; round 2 design: 0 Blocker/Major. 25 of 25 deadline mutants good; hash 5938ea86 verified.

## Building now
- G4 (P1c redactor gaps, ticket v8): builder acdb3947 since 11:21Z, Phases 0-2 committed (/tmp/core-c-g4, wip-g4). Round 8 plan findings sent to it as deviations.
- G9 (E10 fixed point, ticket v3): builder a2a7bac8 since ~11:49Z (/tmp/core-c-g9, wip-g9), first code commit done.

## Will NOT be built and result-reviewed by 12:30Z, exact next steps
1. G4 and G9 result reviews: builders report ~12:15-12:40Z; then cherry-pick onto cloud/core-c (order: G9 first then G4? G8 already in; G9 and G4 both edit redact.py _build/sweep: expect textual conflicts at _build, the module docstring and the shared model_gate/runmap docstring bullet), run ONE merged-tree batch (15 files + the new files, -n 3), then fresh design + codebase result reviews on that tree.
2. E16 (G8 opaque-token regression vs the base: UUID/10-11 digits cut a long token): merged as pinned limit L15 (rows OL1-OL7, no pattern changed). LEAD DECISION: accept, or ticket G11 (candidates measured by agent a9730a72, report pending). SECURITY wording must state the limit either way.
3. E14 (finder memory for large plain values, ~1 GB in one call): NOT built; needs a ticket + one plan review + lead decision; G4's round 8 design review proposes a run-level `max_map_chars` check as well.
4. E15 (entity-spelled placeholder `&lt;TENANT_..&gt;` returns a decoded placeholder shape): not investigated; a small probe is the next step.
5. Docs pass after G4/G9 merge: G8 nits (OL3 base record, L15 wording "or a letter", redact.py comment on phone words, F5/F6 docstring), G10 nits (D-8b docstring, NotText docstring, fold-only budget statement); SECURITY-README v6 and the SECURITY/CHANGELOG lines for G7 round 6-7, E9, G8, G10, G9, G4 (SECURITY lane; v5 is stale).
6. Whole-suite, Python 3.12, PostgreSQL 17, full perf on the merged tree: NOT RUN anywhere.
7. Lead decisions open: gate L-D1 (G9 default: mask, never refuse), G9 L-D6' reach/deep overlaps, L-D7 union cap, G8 L-D15/L-D13/L-D17, G10 D1-D10 (D4 30 s per check), G4 L24-L28 (R8 kept, loose blocks, lazy line fallback, ENCODED memory per run), E9 option (a) vs (b).
