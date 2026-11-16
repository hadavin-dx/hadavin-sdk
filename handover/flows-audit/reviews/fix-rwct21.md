# fix-rwct21: fixes for read r20 (RW / CT), static, nothing run

Failures and uncertainty first
- tools/check_secrets.py prints FAIL (6 hits), all in reviews-of-core-patches/patch-copies/README.md (a "pattern" hit at line 10 and 64-character hash values at lines 95 to 97, 112 and 113 that look like SHA-256 file hashes). I did not touch that file (not in my edit scope), so I did not change it. I did not check whether the hit existed before this pass. Next step: the lead decides whether the file needs an allowlist entry or a rewording.
- Every string changed here is unread by a fresh reader. The reader r20 words were checked against the cited lines; all 9 Majors were real.
- A-077a changed PASTE to HELD (counts updated). No new Q31 item needed beyond what is below.

Finding -> result
1. V-57 (RW 288): the cell now holds the whole R:57 sentence ("real-v4 and v5 use 45 s, DESIGN-A-README says 120 s for its flows folder"), so the string replaces all of it and the 120 s clause is no longer written twice. Not partial, so line 12 needs no change.
2. A-077a: PASTE -> HELD until the lane3 report is read (CT A-022). Counts updated: PASTE 54 -> 53, HELD 88 -> 89 (Status at a glance, both id lists; total 195). CT row 23 status line, CT row 274 sub-row status and CT A-077 "RW status" updated. RW line 215 (K3B/K3 glossary) now says the mapping is unconfirmed.
3. "same sentence" (A-050c, A-036b, N-1): A-050c in RW and the A-050 and A-036-family string in CT (2 places) said "table row in the table"; all now say "table row of that lead", identical to A-036b and N-1.
4. Relayed numbers with "Keep": CT A-028, A-047, A-058, A-060, A-061, A-063, A-068, A-069, A-070, A-078, A-079, A-080, A-082, A-089, A-093, A-094 now read "Keep only after D2 ... then only with the words 'reported by another test session; we have not seen its raw files' and its run count n; until D2 nothing is spoken, shown or published". A-070 no longer says "relayed" for a reader. Sibling search covered every CT row with SUPPORTED ONLY BY RELAYED NUMBER whose to-do said Keep.
5. A-026 (CT): the first safe string ("a real CRM has no switch...") is deleted and explained as the claim A-025 rejects; only the three "our real CRM account" strings remain; the verdict cell now says why OVERSTATED differs from A-025 UNTRACED. "(if the shorter text above differs...)" replaced by "(RW wins)" in that row.
6. Rule 7 (RW 231): reworded: two recovery numbers may stand in one sentence only when each is tied to its own stop point and run count (as in A-073a); never a pooled range. A-073a left as is.
7. Voice rows: RW line 3 now says N-6, A-016d, A-016a wait for APPROVED and for the answer to RWQ-10 (who speaks); input-table row (c) gives no speaking default (a Claude session cannot speak live; BLOCKER until a person is named; the lead remains the default only for typing); line 92 and RWQ-10 text aligned with the existing step-0c text; line 239 names where "presenter" is defined.
8. R:90 counts: RW A-023a note now says R:90 is covered by three rows (A-019a, A-023a, A-021 later video); line 77 now names A-019a (R:90 caption) and A-081b (P:161, K1 median figure) separately.
9. A-008a: note starts "HELD until P4a has been read and has passed (step 3 of section 0c), because the card says the CRM service is real."

Smaller points (same pass)
- RW 315: now names rows A-050a, A-051a, V-41, A-053, A-091 as the ones that delete card lines; the others are records or notes (A-023a deletes a sentence of R:90, not a card line).
- "8 of 18 ended unknown": RW A-019a, RW A-076c note and CT A-076 now carry "reported by another test session; we have not seen its raw files".
- RW 67 and 90: "Mon 23 Nov 18:29 UTC" now followed by "= 23:59 IST".
- CT 174 now points to the Verdicts bullet of "Words used"; CT 177 says item 4 describes Table 1 and Table 2 only and lists the 7 lane-table columns.

Proposed Q31 item (not added; the lead decides): "Who speaks the voice rows N-6, A-016d, A-016a (and A-016b, A-016g, N-5a if released)? A Claude session cannot speak live; name the person (same as RWQ-10 and input-table row (o))."

Raw output (run in handover/flows-audit)
- check_runsheet_paste.py: total rows 195; 96 flagged ids with no missing row; 64 UNTRACED, 53 without a row (by design); RESULT: PASS
- check_rw_ct_pairs.py: paste strings in RW: 140 | found word for word in CT: 140; not found in CT: 0
- claims-count.py: verdicts UNSUPPORTED 15, OVERSTATED 84, UNTRACED 65, SUPPORTED 102, RELAYED-ONLY 64, total 330; to-do rows 87; offenders 0; ids 330 unique 330
- check_refs.py: PASS 5176 references
- check_names.py: PASS 655 rows
- check_secrets.py: FAIL 6 hits (patch-copies README only, see above)
- ruff format --check . . : 817 files already formatted
- Own count of RW statuses: HELD 89, PASTE 53, DELETE 30, SUPERSEDED 14, NO PASTE 9 = 195 (matches the table).

Files changed: RUNSHEET-WORDING.md, CLAIMS-TABLE.md, this report. No commits.
