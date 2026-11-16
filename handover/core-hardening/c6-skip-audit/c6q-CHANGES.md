# c6q-CHANGES (round 5, one batched fix pass; stamped 2026-11-16T16:33:00Z = 22:03:00 IST)

## What failed or is not done (first)
- REPORT-c6q.md has NOT been reviewed by anyone but its own scripts. evidence-c6q/verify-c6q.py is mine: it proves the new text matches what I wrote and that listed slips are gone, not that a statement is true. The studio lead runs the EGM review.
- Nothing is applied. No n8n, flow, harness or stopwatch run exists. Card seconds are estimates (words / 150 x 60).
- The audited files are a read-only copy (scratchpad), not in the repo checkout; they were byte-identical to origin/cloud/flows-audit e32408c3cf84 in c6p and I did not re-prove it in c6q.
- OWNER-SHEET-v29-SOURCE.md was still being written by someone else (changed 16:30:33Z). C-10c was rerun at 16:32:07Z (evidence-c6q/static-checks-output.txt); verify-c6q.py FAILS if any sheet changes after the stated check time, so rerun static-checks.sh then build_c6q.py before use.
- Lease answer 2 facts are not run; they stay marked "not to be spoken as fact before C-9 part 2".
- I did not re-read each grouped naive-review minor word by word; the ones I worked from are listed below. Any I missed is the studio lead's to name.

## Output files
- REPORT-c6q.md sha256 e9b5a06b3b83602cc3c7289363f976722e1601f41b50e4c06c4296e3e793f686 (94 rows: 49 ready, 42 on defaults, 3 wait for a check, 0 NOT FILMABLE; wave 1 = 91). Box 2,768 words (c6p box was about 4,500).
- REPORT-c6o.md and REPORT-c6p.md untouched (modification times 15:54:14Z and 16:10:53Z).
- evidence-c6q/: build_c6q.py, build_c6q_text.py, verify-c6q.py (92 checks), neg_controls_c6q.py, static-checks.sh/-output.txt, contact-grep-output.txt, void-check*, verify-c6q-output.txt (0 failed), verify-c6q-on-c6p-output.txt (31 failed, as required), neg-output.txt (55 copies, 0 wrong), neg/.

## Fixes by finding id
- Design B1 (lease sentence on public video text against ORD:230): default is NONE; one new yes/no question L-POST ("does 'public post' include the closing card and caption?"); the limit then lives in the owner sheet and release note only; the claim of 'none' is restated honestly (what it does not cover: crashed contacts the recovery flow re-claims).
- Design M1, naive M4: item 13 of the rehearsal list applies the 30 s rule only if card or caption carries the 45 s limit; label 'setting: lease 45 s' and 'other lease settings' named in L-POST.
- Design M2, naive M1: table lease answer x card length (words, seconds, budget, total) in the box, recomputed from the quoted lines by the verifier; answer 2 REPLACES answer 1 (net +15 words, about +6 s); "add 16 s" gone. Card default 90 words, about 36 s, budget 40 s, about 190 s.
- Design M3: report words removed from new texts of rows 6, 8, 13, 17, 21, 25, 37, 47, 57, 70, 72, 90, 91; 'needs n8n' sentence removed from item 11; label check now covers all 94 rows, new and viewer cells, and C-n, KEY:digits cites, 'reading 1/2', 'this report', 'the lease question', PLAN, RES.
- Design M4: L-SHEET = "confirm the one final sheet", v29 is coming; section 9 updated; C-10c rerun (v19 to v29-SOURCE).
- Design M5: item 15 says the second scan searches the real key values (read from the key file, not printed, counts only) plus made-up names.
- Design M6: C-10b pass and fail cells agree; the "no take on Mon 23 Nov unless (a), (b), (c)" line is in the box once.
- Design M7: G12 (LRN:33) and LREP:80 named open with the studio lead; "plausibly meant a second send" withdrawn; answer 2 facts marked not to be spoken before C-9 part 2.
- Design minors: row 90 ends at database n8n; Tue evening inference removed; 18:04 UTC called a plan fact; plan line 1051 called stale by the studio lead, UNVERIFIED; ORD:147 departure stated (section 0, L-DEL, row 8); fresh container (ORD:146) in row 8, C-9, box; contact grep rerun (0 hits); duplicate section 9 lines merged.
- Naive M2 (box length): shorter box, second word list moved to section 1. Naive M3 (undefined labels): each word defined before first use, checked case-insensitively. Naive M5: all four card lines printed in the box. Naive M6: placeholder names, exception form, L-SHEET apart, what happens if C-9 part 2 fails, steps 4 to 6 have no duration.
- Evidence summary: L-SCENES gone from 3e (kept only in section 8 history); "ready" and "n8n" defined first; C-8, RES:97, PLAN:125 removed from new texts; C-10c rerun after v28 changed.

## Questions for the studio lead (exact)
1. L-POST: does "public post" include the closing card and the scene 3 caption? (default yes)
2. G12: may "processed once" stand beside a crash scene given recovery re-claims a crashed contact (LREP:80)?
3. L-SHEET: which sheet is final once v29 is rendered?
4. Who adds the 45 s limit sentence to the owner sheet and release note (no row does)?
5. If L-POST = no and L-LEASE = 1: name a builder to restructure scenes 2 and 3.
6. Q27 (a), (b), (c) of the take script at the re-pin; and do you want the ORD:147 card line anyway?
