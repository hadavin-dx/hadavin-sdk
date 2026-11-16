# fix-claims61: fixes for reviews/claims-table-reader-r61.md (M1 to M16 and nits)
Fixer, non-security, beyond round 2. Edited only CLAIMS-TABLE.md. RUNSHEET-WORDING.md not touched (the pair check did not force it). No grade word and no total changed. Nothing was run except the checking scripts below; not committed, not pushed.

## Fixed (in CLAIMS-TABLE.md)
- M1: row 32 needs now names the re-pin check of the take scripts (same as rows 33 to 33d), P4c after the take.
- M2: row 48 needs now names the two gates (re-pin check, then APPROVED).
- M3: row 24 needs now names the Q16 psql four-column check besides Q7; the check has its own bullet "Q16 psql check" under "Checks" and is in WL-15.
- M4: row 27 needs = D2 for the new text, none for the two deletes (27b). Row 42: needs = D2; the other-branch cell now holds "Total: 19 statements." (RW A-083b); the note says which cell is used while D2 is open (19: A-073b applied, A-073a and A-073c not pasted) and when 20 applies.
- M5: rows 51, 69, 70, 72, 74 now say what releases them (51: qualify_stage.py exists and qs_01 passes at the re-pin, who runs them open, Q31 item 73; 69, 72, 74: D2; 70: P4a) and carry "DO NOT APPLY YET"; row 51 says B-045 and B-046 go together or not at all; row 70 says one string serves both copies (B-172, B-172b). Row 41 needs = D2 (RW A-059 HELD; same kind of disagreement, found while fixing).
- M6, M7: every Table 2 row named by the reader (41, 53 to 57, 68, 75 to 77) and every Table 1 row (26, 29, 30, 31, 34, 37, 38, 40) now has "Status of this row: WORD (RW id)" in its note, read from the RW table Status at a glance (none invented). Rows 54 to 56, 75 to 77 carry an INSTRUCTION naming exactly what is deleted (from the RW rows). Row 34 and row 81 (the mid-sentence colon) now carry an INSTRUCTION naming the exact old words replaced. The Table 2 header and the list at line 392 state the rule once. Row 30 needs (was none) now names the later-video decision and scene 9 rehearsal (RW B-077).
- M8: row 80 no longer says BLOCKED; it says the studio owner types y on camera (Q28 item 4) and the step is not yet written (WL-1). The Status words table says BLOCKED is a kind of waiting item, not a status word.
- M9: new bullet under "Where the files are" says which file receives each owner-steps edit (v3 today, v4 not yet written) and lists OWNER-STEPS-q16-rows.md; the file cell of rows 21, 32, 33 to 33d, 79 points to it. LEAD DECIDES: whether the archived v3 is also edited and when each replacement moves into v4 (written in the bullet; default: v3 only).
- M10: line 395 and the notes of rows 85 to 87 say what a section 0c step is (no RW table row; a step of the lead): row 85 = step 1b item (1), row 87 = step 1b item (3), row 86 = step 2b.
- M11: row 87 now covers the third placeholder HS_CRED_PLACEHOLDER (current words, why, replace text, note), as RW step 1b item (3) already says; I confirmed mf-sub-crm-mail.json:103 and V5-README.md:11 by grep. Which value replaces it stays UNVERIFIED.
- M12: row 86 location is "alert-column gate, before the first send (a check on the take machine, not a re-smoke)"; psql check is listed in item 4 and under Checks.
- M14: item 4 of "Five lines first" now lists P4a, P2, P4b and the Q16 psql check before the take, P4c after, P1 later video only.
- M15: gloss "new = done on the first send (node ReplyRan)" in the row 29 note and in the pointer list.
- M16: new bullet "Terms used in Tables 1 and 2 and explained elsewhere" defines or points to re-pin, decisions 1, 2, 10 (read from DECISIONS-2026-11-16.md), D1 to D3, WL-n, Q-F, RWQ, P-checks, order 017, fix-rwct21, "round N read rNN Mx". The last one says plainly that this file keeps no map from read numbers to files.
- Nits: "Round 1 fixes" note now labelled as a note on lane A; missing full stop in row 48 added; A-043/A-044 crossed pointers explained.

## REGRADE PROPOSALS (M13; no grade word changed)
RG-10 (B-024, X-4, B-059: "audit"), RG-11 (B-054), RG-12 (B-197, alternative to RG-6), RG-13 (B-016, with RG-3). The REGRADE block now cites r61 M13; its total line says RG-10 to RG-13 are not in it.

## Needs lead
LEAD DECIDES: RG-10 to RG-13; whether archived OWNER-STEPS v3 is also edited. Everything else open stays in WL-1 to WL-16.

## Not fixed
Nothing from M1 to M16 left. Not verified by me: the RW statuses were read from RW's table by script; the reader's words stay unverified; no file other than CLAIMS-TABLE.md was opened for edit.

## Check output (last lines)
- claims-count.py: verdicts OVERSTATED 110, SUPPORTED 78, RELAYED-ONLY 57, UNTRACED 79, UNSUPPORTED 6, total 330; lanes A 100, B 226 incl. X 4; to-do rows 87; offenders 0; ids 330 unique.
- check_rw_ct_pairs.py: paste strings in RW 144, found word for word in CT 144, not found in CT: 0.
- check_runsheet_paste.py: RESULT: PASS. check_refs: PASS 5190 references. check_names: PASS 655 rows. check_secrets: PASS 0 hits in 2971 files. check_counts: PASS 52 files / 655 nodes. ruff format --check: 1096 files already formatted.
