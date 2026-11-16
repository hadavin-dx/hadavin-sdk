# fix-review56 (FIXER round 56, static only, security path)

Inputs: review-md-design-r56.md (M1-M5, m1-m5, nits) and review-md-codebase-r56.md (M1, M2, m3-m7). Backup: scratchpad REVIEW.before56. Only REVIEW.md and this file were written. All text is the audit's own proposals; nothing was built or run. Lines 5 and 77 unchanged (e6db355c, a3ab18f0). Four rows were inserted into the signing authority map, so lines after L682 moved down by 4 (MINIMUM COUNTER now L695, VERIFIER NEGATIVE TESTS and its figures L696, history sentence L833); other edits are inside existing lines (L626, 628, 633, 635, 636, 639, 644, 649, 466, 666-667/670).

## Items
- design M1 (case 5 "every check of case 4"): FIXED, L636: the checks that apply are named (4.1, 4.3-4.7, 4.9, the file (ii) check in place of 4.10); 4.2 and 4.8 compare with the record and hash of the entry the verifier appends; L635 4.2 points to cases 2(ii) and 5; test (cu) reworded (succession signed by the new key starts).
- design M2 (nonce used vs unknown): FIXED, L639 NONCE RULE: the process keeps each nonce with its state until the process ends; phrases 'nonce already used' ((ad), (ca)), 'nonce expired' ((bh)), 'nonce not made by this process' ((ae), (af)) are now each reachable; no new test needed.
- design M3 (no alarm for RECORD-RESET/SEED): FIXED, L649 Z6(b): OVERRIDE, SEED, RECORD-RESET and LINEAGE entries always alarm, never throttled; test (de).
- design M4 (issue of secrets, LINEAGE): FIXED, L628 re-provisioning and L649 identity (vii): the one right to issue/revoke a secret, written request, LINEAGE written by the issue step, alarm on every LINEAGE, no append secret of its own; tests (de), (df), (dg). Honest remainder (impossible now, part (8)(a)): the log host's administrator is root and can still mint a secret and write START/STOP as that host; the alarm shows it, nothing prevents it.
- design M5 (signing map): FIXED: release key and next key rows (L667, L670) name the four typed purposes; four new map rows (L683-686); MINIMUM COUNTER bullet updated. Separation tests (cj)-(cm) were not re-read by me and not changed.
- design m1 (cv): FIXED: (cv) is the one-signature (B); new (dh) is the one-signature typed string; L633 check 4.2 looks at both objects (also codebase M2).
- design m2: FIXED, L628 (a generation with no pin counts as no key; order item (4)); (ct) reworded.
- design m3: FIXED, L628/639: SEED fields now include epoch number and genesis hash; refusals 'seed for a client id that has entries' (di) and 'seed names another epoch' (dj).
- design m4: FIXED by a log-side check, L628: 'log host: nonce already used' for OVERRIDE and RECORD-RESET entries (dk); the log host still cannot know that the verifier made the nonce, stated.
- design m5 and codebase M1/m4: FIXED, L649: throttle key is cause + client id + host per window of `refusal_alarm_minutes`; subject lines defined; record stated as advisory (not chained, deletable); OL-22 (L466) lists the value; test (dl). The record itself is still not tamper-evident: stated, not fixed (rule: part (8)(a) limit; alarm is the detector).
- codebase M2: FIXED (see m1).
- codebase m3: FIXED, L628/639: an override start writes only an OVERRIDE entry, counted as the start entry for the START-ENTRY LIMIT; test (dm).
- codebase m5: FIXED, L644: new class ALARM (tests (dd), (de), (dl)); (dd) no longer counted as a refusal.
- codebase m6: FIXED, L639: append RECORD-RESET first, lower S only after acceptance, phrase 'record reset not written to the log'; test (dn).
- codebase m7: FIXED, L628 order list uses full 'log host:' phrases once.
- nits: "types below" -> "types above" FIXED; case 2(i) vs override for empty log FIXED (L633, L639); identity negative tests (vi), (viii), (ix) added to Z6 list, now 16.
- NOT FIXED / LEAD: no LEAD DECIDES added (no new value invented). The proposed `refusal_alarm_minutes` 60 keeps its old "lead to confirm with OL-22".

## New tests (10, (de) to (dn))
(de) alarm table SEED/RECORD-RESET/LINEAGE; (df) revoked secret; (dg) log-admin login, no secret; (dh) typed first release one signature; (di) SEED for client id with entries; (dj) SEED other epoch/genesis (table); (dk) nonce reuse at log host (table); (dl) alarm per host; (dm) override start, no START entry (it must START); (dn) record reset, append refused, S unchanged.

## Totals (updated at L626, L644, L649, L696 figures, L833)
Z1 108 + 10 = 118 (102 refusals + 13 starts + 3 alarms); distinct events 116 (100 + 3 + 13). Z6 13 + 3 = 16. Z block 155 + 10 + 3 = 168; all 39 + 168 = 207; distinct 166 and 205. Letters: 26+26+26+26+14 = 118.

## Checks run (from handover/flows-audit)
- python check, lettered list in the test line: 118 entries, complete and in order: True; Z6 list items counted: 16.
- line 5 sha256 prefix e6db355c; line 77 a3ab18f0.
- count_review.py: 28 rows, Major 4, Minor 13, Nit 11, PROPOSE FIX 25, DECLINE 3.
- 40-hex lines: 0; 32-hex strings: 3 occurrences, same as in the backup.
- check_refs PASS 5190 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 3027 files; check_counts PASS 52 files / 655 nodes; ruff format --check: 1152 files already formatted.

## Not checked
No design was run or built. Text outside the edited lines (including tests (a)-(cs) bodies, Z2-Z5, Z7-Z16) was not re-read; I did not check the cross-line phrase 'log host: secret was revoked' against any other file. The new text was read only against the sentences it touches.
