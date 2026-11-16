# P1d plan review round 4: design critic (condensed by the lead session)
Verdict: 1 Blocker, 8 Major, 5 Nit. Rulings 165/166/167 not reopened. Nothing run; reading only.
Blocker
- B1 approve-time re-check is not the same computation as the card-time decision (card used seeded map, neutralise with withhold_commands, and a second joined redact_text pass; approve re-runs redact_text on stored summary with none of that; run map may differ). A withheld card could pass approve. Fix: (a) one shared function used by clean and approve with identical arguments incl. the joined pass, or (b) store a one-bit result (ORDER 167 item 4). Add a parametrised test: every row clean withholds (H01-H25, H28, H30, H40, C01-C10) must be refused on approve; absent or shorter run map at approve fails closed.
Major
- M-1 fast path contradicts noise step (b2 deletes * ~ ` _ and line breaks, all printable ASCII): AKIA**IOSF takes the fast path, H37a not learnable there. Define fast path as "no char any step touches"; add row for ** on fast path; BS-4 reports hit rate on multi-line corpus.
- M-2 _healing_views returns 6 views but asserts <= PIPELINE_VIEWS = 5. Fix constant or merge steps (see zoom-out M-1); state max incl. A8; state views x values cost bound for _finish.
- M-3 stale mutant/row cross-references (line 73 M10-M12 should be M7/M8/M9/M25; line 144 M13 should be M11; line 230 M6 should be M4; line 238 M4 is killed by H25). Renumber; add test that every M<n> cited exists with same meaning.
- M-4 hard dependency enforced only by P1D_APPLIED, which covers P1d only; S6 (P2d-2) and S11/S16 (P1d-b) stay open when client profile starts. Add P2D2_APPLIED and P1DB_APPLIED markers with refusal tests, or state lead enforces by process with date and owner. Consider start-up canary self-check (AKIA**IOSF... must be withheld) instead of a presence constant.
- M-5 cost bound covers one call, not a run: cost scales with known values and leaf count (redact_value). BS-4 measure with 10/200/2000 known values; add aggregate char cap for redact_value and one tool result, or precomputed key set; state worst-structure latency target.
- M-6 fail-before not achievable for rows needing new names (LookalikeCopy, WITHHELD_NOTICE, is_withheld, on_residue=, P1D_APPLIED) on base: they error, not assert. Give every row a group; mark new-surface rows and prove another way (stub of base behaviour or sentinel helper); keep never-import-error rule only where achievable.
- M-7 CHANGELOG over-claims: unknown-secret coverage for letter case and inserted characters is AKIA/ASIA only (best effort). Fix CHANGELOG and G1; add H37 variants for case and "." to measure the gap.
- M-8 withholding in redact_value destroys audit record. Store notice plus char count and reason code (and digest of withheld text only if lead agrees); test that the stored record shows something was withheld and its size.
Nit
- N-1 _withhold(reason) called with two args; "_finish only place that logs" false for size/error; specify logged counts for those reasons.
- N-2 "plus what the first call learned" undefined (learned values are never masked); define or delete.
- N-3 rung table says no second normaliser but delete_noise, squeezed view and exact fallback are one; say so. Add a P1d test pinning scan_holds ignoring non-alphanumerics (R1).
- N-4 missing mutants: first learning loop, second form in _finish, seed exclusion from known.
- N-5 wording: Tier C and carrier undefined; line 4 paragraph too long; "Not done, first" should say "Nothing has been run yet"; lookalike-leak.md section 5 not visible, copy the two formulas.
