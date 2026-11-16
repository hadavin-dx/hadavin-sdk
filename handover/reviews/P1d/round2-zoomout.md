# P1d plan review round 2: egm-zoom-out (Sonnet), condensed by me from the inline report

Verdict of reviewer: right problem, size not right. Not verified by reviewer: designs/lookalike-leak.md, P1b branch contents, V-number evidence, runtime numbers. `textnorm` is not on core/cloud-handover (only P1b).
Reuse checked present: gate._views/_rendered/_ANSI_AS_TEXT/normalise, runmap.undo/_views, redact.strip_ansi. LookalikeCopy is new (name from frozen draft).

MAJOR
1. Scope creep: H34 (& grammar), H35 + unknown-key learning H31-H33, S11/S16, H26-H27 defang order are separate classes; split into own packages (still fixed, not deferred). [CONFLICTS with ORDER 165 item 9: H31-H35 fixed in P1d -> CONTEST for H31-H35; S11/S16 cut is open question 4.]
2. healing_views fixed point + P1D_MAX_VIEWS is speculative; use fixed short pipeline (decode, delete, fold, delete), loop only if a measured combination is missed.
3. Windows/overlap/P1D_MAX_TEXT_CHARS (W, X rows, M28) rest on unmeasured V9 prototype; use one char cap + existing REDACT_BUDGET_S deadline, fail closed; add windows only if BS-4 shows need.
4. Squeezed/case-folded learning pass has highest false-learn risk; make it conditional on BS-2 (build only if false-learn rate 0). [Consistent with ORDER 165 "measure first".]
5. Residue rule has two tests (dropped form + put-back count, P1D_MIN_KEY_CHARS); one test (known value in any view of shown text) may suffice for first cut.
6. Too many new public names (healing_views, finish, defang_text, sanitise_text(defang=), five P1D_* constants); make healing_views/finish private until P2d-2 needs them; drop T-API.
7. Two modes (withhold/raise), card, summary fallback, log line = product design inside a redaction ticket; single mode if possible. [Partly mandated by ORDER 165 item 3.]
8. 32 mutants too many; ~12 (one per mechanism) cover the risk; M5 equivalent, M6~M3/M4, M16/M17~M15, M25/M32 duplicates.
9. ~90 named tests; use parametrised tests per view family.
10. Depends on unmerged P1b; reduce surface to textnorm.fold + plain `in`, exact fallback for all lengths, so ViewTooShort / B rows vanish.
NITS: 11 rung-table summary should say reuse covers view-building, new code is residue check + wiring; 12 ticket is 270+ lines, put problem first, appendix tables; 13 state which doc owns name LookalikeCopy; 14 ledger label fine.
Reviewer's recommended cut: P1d-core (fixed-order views + residue check in redact_text, one fail-closed outcome, private helpers, ~10 mutants, parametrised tests) and separate packages for defang order, learning pass, & grammar, S11/S16, windows, public API for P2d-2.
