# Fix report, batch 46 (fixer), 2026-11-16 UTC / 2026-11-17 IST (IST = UTC+5:30)
Scope: only REVIEW.md, this file and checkpoint-r46.md were edited. No git, no patch-copies change. All text is static; nothing was run in n8n, Postgres or HubSpot.

## Failures and gaps first
- NOT re-read after editing: I did not re-read REVIEW.md end to end after the scripted edits; the checks below are the evidence. Unverified: that every edited sentence reads well in place.
- The edit script printed two failures on its first run (commit id not found; the "login count" insertion anchor appeared 5 times). Both were fixed by a second script (commit id replaced in 3 places; the count block placed after the login table). Result: `grep -c` of that id in REVIEW.md prints 0; it stays only in `../reviews/incident-g5-patch-copy.md`.
- Q1 (which program makes the take's model call) could NOT be answered: no flow files in this checkout. OL-10 (ssh-keygen facts) could NOT be read: `ssh-keygen` is not installed. Both stay open.
- The 9364 against 9389 pass gap is explained only by arithmetic (both runs total 9846); which 26 tests were deselected was not read.
- I did not fix the count of lines cited by number elsewhere; line cites go stale (added a warning in the header).
- Design review m-items and stranger minors: I applied the ones I could locate with a unique anchor; I did NOT individually confirm each of the 17 stranger minors one by one. Minors not listed below are not claimed fixed.

## Fixed, per finding id
- Design B1 (override needs both release key and next key): Z1 part 5, new negative test (y); tests 24 to 26.
- Design B2 (log host admin can rewrite the log): Z1 part 8(a) marked advisory, object-lock store named as the control, Z6 (vii), weakness restated, second log trigger moved to "before the first signed pilot note", OL-20.
- Design M1 (next key denial of service): Z2 wording corrected; countersign suggestion contested (below); accepted cost stated.
- Design M2 (running process outlives a revocation): Z1 part 4 timer now stops the process when the log is reachable; maximum run time (default 24 hours, lead to confirm); test (z).
- Design M3 (ratchet state file writable): new identity `verifier-state` in Z6 (iv), test extended, Z6 test count entry updated.
- Design M4 (five mechanical reads): new section "Reads done in batch 46" (Decimal vs integer money in Decision 19, chain.py in Z8, baseline gap, Q1, OL-10).
- Design M5 (verdict vocabulary, Z11 default): verdict bullets and headings now APPLY AFTER FIXES for A-01 and G5, DO NOT APPLY for C-01; Z11/OL-11 recommended default added.
- Design M6 (Z is a proposal): status paragraph and rung note added to the glossary line; moving Z to its own draft is NOT done (lead to confirm).
- Design m1 (G5 file not on disk), m2 and m3 (OL-13 mailbox, OL-8 fallback answerer), m4 (OL-24 count note), m5 (login count), m6 (Z3 step order), m7 (nonce on wiped host), m8 (triggers for signature tool and key vendors), m9 (headline says read from source, not run).
- Stranger M1 (one table of `git apply --check` results), M2 (secrets claim limited to the three patch copies), M4 (login and identity count block), M5 (verdict wording), M8 (OL id map), M9 and M10 (term table and one-line studio rules), commit id removed (4 places) and replaced by a pointer, date format sentence, repeated "IST" duplicates, result labels 1 to 6, criterion (9) and (2) wording, "estimate not maximum", A-6 added to Decision 20 and its count changed to 7 / 10 / 11 in both places, History SUPERSEDED mark and "(superseded, old text)" on repeated headings.

## Contested (no edit, with reason)
- Design M1 countersignature: a lost or stolen release key cannot sign its own revocation; recorded as accepted cost.
- Stranger minor 6 (`:27` and `:28` cites): they name two different lines (def line and match line) and are labelled.
- Stranger minor 11 ("goes back to Major"): not found in the file.

## Counts
Decision 20 now reads 7 / 10 / 11 (A-6 counted as Major under that option). Table counts unchanged: 28 rows, Major 4 / Minor 13 / Nit 11, PROPOSE FIX 25 / DECLINE 3.

## Evidence (own commands, from handover/flows-audit, at the end of batch 46)
- count_review.py: `rows 28`, `severity {'Nit': 11, 'Minor': 13, 'Major': 4}`, `decision {'DECLINE': 3, 'PROPOSE FIX': 25}`.
- check_refs PASS 5193 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2865 files; check_counts PASS 52 files / 655 nodes.
- `ruff format --check .`: 990 files already formatted.
- Lines 5 and 77 together: sha256 cf231d4e11d4400dd5c78d5035b12ae6a61593e538d83c8d5f4a6390ed90f9a3, same as the original.
- Patch sha256 prefixes: A-01 64fdf315, C-01-price-only e7ff677e, C-01 ca4982eb (unchanged).
- git apply --check (run by me, 2026-11-16 19:02 UTC / 00:32 IST): HEAD 9a83c75b3: A-01 0, C-01 1, price-only 1 (all 0 with -C1); b4cce5b: all 0.

## Lead decisions needed
1. Q1: where are the take's flow files? 2. Name the Z owners. 3. Confirm the commit meant by "the commit named in the G5 row" (only the incident file keeps an id). 4. DEAD-MAN-CHECK.md D4/D7 mailbox wording (not edited). 5. Adopt the OL-11/Z11 default. 6. Move D, O and Z into their own design draft. 7. Confirm 24 hour maximum run time. 8. `fix-review15.md` also prints a commit id. 9. Protected line 77 still says "DO NOT APPLY NOW".

Token use: not measured by me; roughly one large context plus one compaction. Rules cited: fix-dont-defer-be-honest, least-privilege-hard-rule, no-single-dependency, wording-clear-for-everyone, tool-ladder-before-code, honest-tamper-evidence-claims.
