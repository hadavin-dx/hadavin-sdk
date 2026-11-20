# MIX build notes (reconciliation builder, 2026-11-20)

Tree: worktree /tmp/core-c-mix, branch wip-mix, base ad17e3e7b (G9 + G4 Phases 0-3 + E14 + G8 + G10). Code commits: "re-pin TB-2.8, TB-2.11, TB-3.4", "G9 review fixes ...", "feasibility-window test names the failing check". Pushed to wip/cloud-core-c/mix.

## A. The three merged-tree failures (E20), re-pinned to measured output
No secret value is readable in any output below (every output is placeholders only; measured with direct `enforce_map` / bare `_Redactor.sweep` calls).

TB-2.8 (tests/test_b64_scan.py), text `x ab-cd-ef y`; enforce_map and the bare sweep give the same string in every row:
| map | before (pin, G4 base) | after (measured, G9 merged) |
| 1 `{TENANT_1: cd-ef, SECRET_1: ab-cd}` | `x ab-<TENANT_1> y` | `x <SECRET_1><TENANT_1> y` |
| 2 `{SECRET_1: ab-cd, TENANT_1: cd-ef}` | `x <SECRET_1>-ef y` | `x <SECRET_1><TENANT_1> y` |
| 3 `{TENANT_1: ab-cd, SECRET_1: cd-ef}` | `x <TENANT_1>-ef y` | `x <TENANT_1><SECRET_1> y` |
| 4 `{SECRET_1: cd-ef, TENANT_1: ab-cd}` | `x ab-<SECRET_1> y` | `x <TENANT_1><SECRET_1> y` |
| 5 `{TENANT_1: cd-ef, SECRET_1: ab-cd, SECRET_2: cd-ef}` (sweep and enforce_map) | `x <SECRET_1>-ef y` | `x <SECRET_1><SECRET_2> y` |
(The G4 base outputs left half a value readable in the identifier rows; G9's sweep masks an overlap with the existing placeholders, in text order.)

TB-2.11 (tests/test_runmap_enforce_map.py `test_e5b_...`): `x <SECRET_1>-ef y` -> `x <SECRET_1><TENANT_1> y` (enforce_map). With R8 applied the same string.

R8 (gate_mutants.py): `python tests/gate_mutants.py R8` -> `BAD SURVIVED`. Equivalent under G9: 36,000 random small maps (3 to 6 entries, 6 kinds incl. secret and identifier kinds, 13 values, 6 texts; 4,878 with `_rules_conflict` true), plus 768 structured maps: 0 outputs differ with `_rules_conflict` patched to False. No map found to re-point R8 to. Left as is (not deleted, MIN_MUTANTS 105 not lowered, runner not changed): lead decision in ESCALATIONS E20 update. The TB-2.11 docstring says so.

TB-3.4 (test_no_run_no_extra_work): measured sequence of (redact calls, clock reads): (2,3) (2,3) (2,3) (2,3) (1,1) (1,1) (1,3) (1,3) (1,1) (1,160) (1,1) (1,160) (1,1) (1,1); only indices 9 and 11 changed, 154 -> 160 (the `redact_untrusted` rows of the marker texts `<HIGHENTROPY_7>` and `<CREDITCARD_12>`). Cause bisected with worktrees: 154 at b61804542 and at 6a852c7d3^, 160 at 6a852c7d3 (G8 glued-rest commit: the look-behind pattern edits of IPV4 / CREDITCARD change the segment count), and 160 unchanged through G10, E14, G9 and G4 Phase 3. (E20 blamed G9: not so.) The on == off assert is unchanged (the base64 step adds no read).

Batch (-n 2): test_b64_scan, test_runmap_enforce_map, test_model_gate, test_redact_settle_loop, test_redact_mutants_meta, test_gate_mutants_picked_up: 495 passed, 1 skipped, 4 xfailed.

## C. Window scan counted (G9 review MAJOR 2)
`_deep_hits`: `self._spend(work, hi - lo, deadline)` once per distinct window (inside `if at is None`, the `found` key holds the clamped lo/hi). zwsp shape (`pass`+U+200B+`word=` x N), peak work of one sweep (bisected over SPELLED_MAX_WORK, 1,024 resolution, and by instrumenting `_spend`): N = 400: 36,621 -> 38,909; N = 16,000: 1,331,328 -> 1,333,617 (instrumented 1,333,114). (G9 notes' 1,811,011 was another counting of the same shape.) test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse (perf, alone): passed, 42.9 s.
Pins shifted by the charge (re-derived): G9-20's test `test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep`: first text 21,027 -> 22,052 (+1,025: window [18,975, 20,000)); second text 43,079 -> 84,104 (+41,025: three edges, windows of 1,025, 20,000 and 20,000 characters; the left edge of the second token can read the whole 20,000-character rule); mutant G9-20 expect `[63079]` -> `[104104]` (+20,000 for the second search, as before). G9-22 and G9-23 unchanged (killed).

## B. Feasibility-window test and mutants (MAJOR 1)
`test_g9_the_anchored_check_searches_only_the_feasibility_window_and_counts_it` (non-perf, exact units, no clock): (a) `x<SECRET_2>` with a 1,030-character value: window [0,1025), 6,169 units, hit found; (b) plus a 1,100-character rule that cannot fit: window [69,1025) shorter than the anchor, adds exactly 1,101 units (7,270), no hit; (c) `<SECRET_1>x`, 1,100 rule, window [75,1100): 6,379, hit found. Derivation of each sum is in the docstring.
Mutants G9-25 (skip removed), G9-26/G9-27 (lo -1/+1), G9-28/G9-29 (hi -1/+1), G9-30 (scan not counted): all KILLED (6 of 6); EXPECTED_COUNT 117 -> 123. Not a mutant: the `if k > can_left or len(w) - k > can_right: continue` line is redundant given the window (the window is its exact inverse), so removing it is EQUIVALENT; left in as a belt-and-braces check. Runner list unchanged (test_redact_settle_loop.py is already in it).

## D. Cap-sized periodic shape (MAJOR 3), no limit changed
zwsp shape at the 262,144-character cap (26,214 repetitions, 262,140 characters): 2,180,876 units = 54.5 percent of SPELLED_MAX_WORK (4,000,000), not refused, 10 s under load; 8.33 units per character at 160,000 and at 262,140 characters: linear, not quadratic; headroom 1.83 times. Others: `p`+ZWSP+`=` x 131,072: 0 units; 60-character period: 518,780. Written into ESCALATIONS (E17 update).

## E. Nits
`_deep_hits` docstring (feasibility window and the units list); redact.py comments (`_spell` comment and docstring: a G9 union never passes `_spell`); runmap.py enforce_map docstring and model_gate.py docstring (the net checks secret kinds only; a held-back identifier's rest passes silently); defaults.py comment (SPELLED_MAX_UNION_CHARS 1,000,000 > MAX_MAP_CHARS 524,288, not the effective bound). Constants: a convention exists (E14 pins constants in tests) so `test_g9_constants_hold_sane_values` (passes >= 2, reach 1..65,536, limits > 0, union limit >= MAX_REDACT_CHARS). Not done: N4 (`_masked` one placeholder where two), N5 (kind-rule mutant), N6, N7 numbering: outside the task list.

## Mutant and test follow-ups on the merged tree
- b64 mutant "b64 tie-break as v3's sort key" SURVIVED after the TB-2.8 re-pin (G9's read-back makes maps 1-5 order-independent; 172 of 64,000 random map x text probes differ between the two sort keys, 170 of them in the bare sweep, where an identifier value glued to a same-length secret value stays readable). Added a SIXTH TB-2.8 map `{EMAIL_1: abcd, SECRET_1: efgh}` on `abcdefgh`, bare sweep `abcd<SECRET_1>` (measured; the identifier `abcd` stays by its boundary rule, no SECRET value is readable; the mutant gives `<EMAIL_1><SECRET_1>`): the mutant is KILLED again, b64_mutants.py 39 of 39 killed.
- G8 mutant runner (`g8_mutants.py`): NOT RUN, the unmutated copy fails `tests/test_redact_glued_rest.py::test_glued_patterns_are_linear[underscore digits-redact_text]`: ratio of 262,144 to 65,536 characters of `_4155550132` x n through `redact_text` is 6.18 in pytest (5.81 in a plain loop), bound 6.0. Bisected: passes at e75871df3 (G9 alone, ratio 3.6) and at G4 Phase 2 (4250d14d2, 3.99), fails from G4 Phase 3 (35a068f2a, 6.19): large text 0.92 s -> 1.35 s, small unchanged: the base64 view's cost on one 262,144-character base64url-alphabet run. Not touched (no test loosened): lead decision, see E20 update.
- Gate mutants: 103 of 105; survivors R8 (equivalent under G9, E20) and R15 (survives at the G4 base too, G4 notes). E14 8 of 8, textnorm deadline 15 of 15, redact_mutants.py whole file 123 of 123 (after the G9-25..30 messages fix; the first whole-file run had 121 of 123: G9-27/G9-28 failed on an unnamed assert, fixed).

## Results
See the report; mutant summary lines and the lead decisions: E20 update (R8), E17 update (cap shape).
