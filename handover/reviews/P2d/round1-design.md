# P2d-2 plan review round 1: egm-design (condensed by the cloud session; verdict NOT CLEAN: 2 Blocker, 5 Major, 3 Nit)
Read: P1d.md rev 5, sibling report, template, orders 165-169, P2d.md lines 1-75 and 262-313 (rest by grep). Not read: design draft 11, P1 rev 16. Nothing run.
- B1 Blocker: P2d.md has no P2D2_APPLIED marker (constant, module, row, mutant, CHANGELOG, order of markers). P1d's startup test can never pass.
- B2 Blocker: marker would open the S6 gate too early. (a) S6 leaks through prepare_output AND error_reason; error_reason is in P2d-2b, so the marker must be set by the last S6 package or 2b folded in. (b) escape-code (`ESC [0m`) and `**` handed-secret rows missing; escape changes the scan key (a carrier), P2d-2 has no escape deletion (reuse P1d `_healing_views`). (c) handed-out secrets of 8-11 chars reach the model (floor 12) while the marker would close row 005; lower to 8 or keep the gate closed explicitly. (d) a bare boolean is weak: add an S6 start-up canary.
- M1: P1d and P2d-2 both implement the count rule in redact_text; P2d-2 raises LookalikeCopy on the model path (contradicts order 166 and P1d); two notices (SAFE_HEAD_NOTE vs WITHHELD_NOTICE); both define LookalikeCopy. Make one rule, one notice, P1d owns LookalikeCopy; add a caller table.
- M2: merge order P1d vs P2d-1/P2d-2 undefined; P2d-1 rows assert InputTooLarge/TooDeep raises that P1d turns into a withhold.
- M3: S13 owner inconsistent (sibling report: P2d-2; P1d: folded into P1d; P2d silent).
- M4: thresholds 8 vs 12 give two guarantees for one value; state a combined table.
- M5: P2d is FROZEN at rev 6; lead must unfreeze or record as errata.
- N1 fail-closed checks hold; say secrets never logged. N2 constants lack validated ranges and sources. N3 ticket does not say why it is over 250 lines.
