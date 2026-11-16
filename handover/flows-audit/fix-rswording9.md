# fix-rswording9 (FIXER round 3, RUNSHEET-WORDING.md), 2026-11-16

Edited only RUNSHEET-WORDING.md (backup: /tmp/RUNSHEET-WORDING.md.bak). Source: reviews/runsheet-wording-r3-reader.md. The reader's words are unverified; so is this log. Nothing here is a claim of "verified".

## Changes by finding
- M1: step 7 now says "Apply the DELETE row A-016c" (no NOT USED).
- M2: the card line is A-016h everywhere (step 10, step 7, 0b Q-F row, card paragraph, card table line 1, Q-F in section 4 and in the open-labels table). Card table: "Left out", "1 mail" and "(the claim)" replaced.
- M3: banned status words removed from prose: CUT (lines 73, 103, 118, 120, 125, 138), PROPOSED (line 33 now "draft text"), NOT USED (step 7), "Left out" (card table). A-017b, A-019b, A-051b, A-053b are called SUPERSEDED, A-051a and A-053 DELETE. The only remaining CUT, NOT USED, Left out and PROPOSED are inside the status-word definitions (lines 11 and 15).
- M4: step 8, the 0b D1 row, line 73 and A-019a wording now say "four sentences of the old caption in R:90; the rest of the line stays".
- M5: 0b D2 row no longer lists A-087a and A-087b as waiting and no longer has the "paste A-087c and A-087d" default (they are PASTE, wait for nothing). D1 row: B-032 is HELD until the re-pin; X-6 is X-6a, X-6b, X-6c. P2 row lists A-010c; P4a row lists B-172b.
- M6: A-012 note now names the real conditions (APPROVED, P4a read, Q22 item 3 preparation, Gmail filter).
- M7: the intake-mailbox replace-list (line 25) includes A-012 and says the mailbox pane on screen carries a visible label with the same word (placeholder until the lead names it).
- M8: "claim" alone removed from the 0-words list and the claim definition (now claim id and claim row); "the claim" and "the A-016f scoped sentence" replaced; rule 2 says "scoped sentence". A-098 paste now says "alert hold" (it said "claim window"), matching the alert-hold word.
- M9: B-195 and B-197 changed from PASTE to HELD (wait for D2: counts come from raw files not in the checkout); added to the 0b D2 row. The text "12 of 20 and 2 of 5 runs" in all notes now carries "(reported by another test session; not confirmed, D2)"; "our own bursts" wording removed. B-130 paste now says "as reported by another test session; we have not seen its raw files".
- M10: B-156 paste no longer claims a safe unknown or no second e-mail message at 45 s; it says whether a takeover can send a second e-mail message is not measured.
- M11: B-214 changed from NO PASTE to HELD (paste cell stays NO PASTE: no string yet). BLOCKED: the take script text (FAILED-TAKE-NOTE.md line 24), which the lead reads at the re-pin.
- Nits fixed: "lead record" gone; step 6 has the [PRESENTER] tag; the "mail" leftovers in prose and paste strings found by grep (B-016, B-038, B-088, B-150b, B-154, B-182, A-008a, A-057, A-033c grammar "an", and notes on lines 53, 94, 136, 145, 160, 162, 164, 168, 383, 414, 420, 428, 435, 440, 458 to 467, 495); line 145 no longer defines "mail" the opposite way to line 23; Q-B names N-11a and N-11b; Q21 no longer ends in "Missing input"; Q31 is explained as the open list in QUESTIONS.md; A-012 paste says "lead table row"; A-016d paste explains the lead ID as naming "one made-up person who asked for contact".
- Quoted old sentences (old-sentence cells and quotes from other files) keep the word mail on purpose; not changed.

## Status at a glance (recounted by script from the first cell of every row)
PASTE 54, DELETE 30, HELD 84, NO PASTE 5, SUPERSEDED 12, total 185 (before: 56, 30, 81, 6, 12). The table rows were regenerated from the script's lists.

## Commands run from handover/flows-audit (output summary)
- python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS (185 rows; 86 flagged ids, none without a row).
- python3 tools/check_refs.py: PASS 5166 references.
- python3 -I tools/check_secrets.py: FAIL 1 hit, flow-check/evidence-f8-r8.md:55 (not my file; it was 2 hits before my edit, the second one, flow-check/raw/test-take-check.txt:178, is gone without my action, so another agent changed files). No hit in RUNSHEET-WORDING.md.
- ruff format --check .: 606 files already formatted.
- python3 -I tools/check_rw_ct_pairs.py (extra): 66 paste strings are not found word for word in CLAIMS-TABLE.md. Not all are caused by this fix (the older state already differed); my paste-string changes add to it (A-008a, A-012, A-016d, A-057, A-098, B-016, B-038, B-088, B-130, B-150b, B-154, B-156, B-182). BLOCKED: CLAIMS-TABLE.md is edited by another agent; the lead must have those rows copied from this file (this file wins until then).

## Not checked
- The reader's other points: the word "check" has six meanings (Nit, not changed). "re-pin", Q25 item N, Q22, Q13, Q28 pointers and the files outside this folder were not opened.
- No fresh reader has read the changed strings.
