# fix-tcfp5 (fixer log, round 4 readiness findings, TAKE-CHECKLIST.md and FIX-PLAN.md)
Static work only; nothing run. Backups: scratchpad bak-tcfp5/. Edit script: scratchpad edit5.py (67 exact-text replacements, each asserted to match once).
Findings checked against flow-check/take_check.sh, flow-check/take-warns.pin and ORDERS.md by grep/read before editing.
1. Unsupported "I ran this one command ... printed true": deleted in TAKE-CHECKLIST Step 0 and FIX-PLAN step 0; now says plainly it was not run and not confirmed.
2. Script line cites replaced by text cites (274, 139, 171-189, 227, 53-79, 10/175/176, run_all.sh 57; check_flows.py 156). Exit 5 (override with test flag, never a pass) added to check 1.
3. Pin "# flows sha256" rule added (check 1, GO row 4, FIX-PLAN step 4 and step 9); route for the UNFILLED copy via --write-warn-pin "$NEW_PIN". Exit 4 text quoted from script. Not checked: whether the committed pin sha equals a regenerated copy (nothing regenerated).
4. Placeholder table: added $PATCH_BRANCH, $TOOL, $VALUES, $FILLED1, $FILLED, $NEW_PIN, $EXPORT_PIN, $STUDIO; $BRANCH meaning stated; $SHA_R20-R23 source now Inputs items 7 and 10 (item 13 was wrong). Inline assignments and hard-coded $HOME/keep paths removed from commands. Inputs item 18 added (planned by the audit, lead to confirm).
5. cd "$REPO" && or cd "$STUDIO" && added: GO row 3 pytest, row 4, row 5(b), row 6, check 2(a), step 4, step 9, ledger line.
6. F-007 grep: -i, SUPERSEDED mark does not remove a hit, allowed list not an authority until lead writes it, VIDEO-RUNSHEET.md:90 must be edited. Same wording applied to the F-041 grep allowance.
Nits: Q17 item 4 line cite 115 -> 117; IST added to Mon 23 Nov 12:00Z (17:30 IST) in 3 places.
Not done: the claim that exit 0 needs a matching pin for the new folder is read from script text only.
