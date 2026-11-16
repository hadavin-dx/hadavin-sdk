# Contradiction sweep r1 (read-only; 2026-11-16 UTC). Inputs: DECISIONS-2026-11-16.md (12 items) vs OWNER-STEPS-realrun-v13, OWNER-DAY-CARD-v13, plan-v10-real-v5-edits, REPORT-c7b-fix3, REPORT-repin-v6.
Not checked: steps-edits/OWNER-STEPS-v13-APPENDIX.md only grepped (not read in full); no command was run except greps; v13 and plan-v10 may still change.

## Failures first
| # | Dec | Finding | Where |
|---|---|---|---|
| F1 | 4 | The one full run (9514 passed) was made on a tree that has C-01 AND A-01 applied (A-01 is DEFERRED, C-01 extras are CUT). No run exists on the scope the lead kept (G5 plus the id fix only). The 9514 figure does not describe the kept scope. | patches-ready/v3/REPORT-c7b-fix3.md:11 (tree built with C-01, A-01, G5); raw-c7b-fix3/tree-manifest.log:2,4,12 |
| F2 | 10 | DECISION-one-store line 14 still says "ONE database for everything we own: the single Postgres instance"; item 10 orders it fixed to "one server with two databases". Not fixed in the file. (v13 uses the right wording at :52 and :142.) | inputs/DECISION-one-store.md:14 |
| F3 | 6 | inputs plan-wp6-resmoke-v5.md:121 lists "take n8n 5690" (the rehearsal port) as the take port; item 6 says the real take uses its own free port and the plan names it in one place. plan-v10 has no port edit (grep: only Z1 lines 315/318 mention 5678/5679). v13 leaves the port to a blank (card :14) and never names 5690. No single place names the real port yet. | plan-wp6 :121; plan-v10 (no hit); card :14 |
| F4 | 5 | S9-2 honest sentence ("the program does not print these figures") is not in v13: A.1 (:95) and A.2 (:96) only say compare; no such sentence found by grep. | OWNER-STEPS-v13:95-96 |
| F5 | 5 | S9-5/S9-12 text (lead reads only masked take outputs, never owner-only secrets or real-run folders; "rules A, E, F, I not overridable mid-take") not found in v13, card, or plan-v10 (greps for masked, S9, not overridable: no hit). v13 uses numbered rules ("Rule 9", "rule 10"), not letters A/E/F/I, so the item's rule names have no anchor. | v13 whole; plan-v10 |
| F6 | 2 | Step 0 (a separate live HubSpot probe) creates one contact and "tries to delete it"; line 88 says the delete line "does not matter". If delete fails, that contact is not on the take's deletion list (list comes from mf_leads export, plan-v10:447-452). Not a hard contradiction of "take never deletes", but a leftover-contact gap. | v13:80,88; plan-v10:447 |
| F7 | 11 | "BRANCH ARTEFACT" label is not on the fix3 report or v3 README (grep: none). fix3 does say the tree was clean (git archive, handover removed), so the clean-tree half holds. | REPORT-c7b-fix3.md:11; v3/README.md |
| F8 | 12 | No file states the first-rehearsal time or "target tonight/tomorrow IST"; STATUS-BOARD and ORDERS grep: no hit. v13 stamp and card :6 are blank (correct for a draft). REPORT-repin-v6 gives no IST times. | card:6; ORDERS.md |

## Per decision (1-12): contradiction / unbacked number or date / duplicated job
| Dec | Contradiction | Unbacked number or date | Duplicate rule that can drift |
|---|---|---|---|
| 1 scope | none in v13/card. plan-v10 :162 (film-v5 `2.1` fill) is the "before" text of edit 8; :88 is the after. Not verified edit by edit | "13 sends (A twice, B ten times, C once)" card:49 / v13:37: no file read for it | claim wording: plan-v10 :457-459 carries Text A and Text B both, lead pick open |
| 2 identity | none for the take (v13:48, card:55,58 consistent). See F6 | none | "no delete call" statement: v13:48 and card:55 ("lead verifies at re-pin") |
| 3 roles | none; no v13/card/plan-v10 mention of roles proposal or group L | none | none |
| 4 C5 | F1. v3/README.md:5-12 matches the item; but A-01.patch, C-01.patch (with extras) still ship in the folder | "9514 passed, 455 skipped, 240.35 s": backed (full-run.log:145). "23 passed", "11 failed, 12 passed": backed (g4-v-new-code.log:35, old-code-run.log:42). Hash 0dbf8c4a: backed. Patch hash 12e4be6f: .sha256 file exists. Real head `de6b574`: only named in reports, no file shows it | scope cut stated in README:5-12 and item 4 |
| 5 S9 | F4, F5. v13:37 does NOT claim "nothing can spend": says "No closed gate exists" (consistent with item 5). v13:37 says lead imported flows before the run (no "lead activates after y": consistent). v13:117 owner cancels model key same day (S9-3 ok) | none | money rule: "the only one", pointed to from A, card and I.0 (v13:57); A.0b cancel-old-keys in v13:94 and I.0: keep the two in step |
| 6 ports | F3 | none | 5678/5679 stated in v13:108 and card:14 (both say "never those"): same text twice; plan-v10 :315,:318 a third time |
| 7 n8n setup | v13:37 consistent (lead imports). "n8n_api.py" is named in no owner file or plan-v10 (grep). FACTS-ALREADY-DONE not re-read | none | who starts/stops n8n: v13:37, card:3, card:49, v13 I.5 |
| 8 smoke | none; plan-v10:341 says real HubSpot not run (consistent) | none | none |
| 9 counts proof | none found; no mention of the screen in v13/card | none | none |
| 10 wording | F2 | none | "one Postgres server, two databases" in v13:52 and :142, plan-v10:355: three copies |
| 11 licences | F7. No file touched promotion-inputs in these 5 files | none | none |
| 12 rehearsal | F8 | none | stamp rule in v13:5 and card:6 (same sentence twice) |

## Other notes
- REPORT-repin-v6 is about the stand-in/kill-script checklist (plan-wp6 re-pin), not about any of the 12 decisions: no contradiction with them found. Its claim counts (24 10 2 1; 18 bash blocks; 270 lines, 15 hunks) were not re-run here.
- plan-v10 is 488 lines and may still be edited; findings on it are for the version read at 2026-11-16.
