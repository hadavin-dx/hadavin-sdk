# c6p-CHANGES (round 4, one batched fix pass; stamped 2026-11-16T16:12:00Z = 21:42:00 IST)

## What failed or is not done (first)
- REPORT-c6p.md has NOT been reviewed by anyone but its own scripts. The checks in evidence-c6p/verify-c6p.py are mine; they prove the new text matches what I wrote, not that it is right. The studio lead runs the independent review.
- The naive-review minors were only partly worked through: I did not re-read each of its grouped minors (words with two meanings, 'prepared send note', 'go marker', 'rehearsal data' used before they are defined) against the new text. Those undefined-where-used terms may remain. Next step: the naive reviewer reads REPORT-c6p.md.
- The new card line 1 forces the repeat send to come within 45 s of the first send. Scene 2 is planned at 40 s and rehearsal item 13 asks for under 30 s, so scenes 2 and 3 may need restructuring if the studio lead keeps the default; this report holds no rows for that (the question L-SCENES was dropped). Recommended answer: L-LEASE 2 after check C-9 part 2.
- Seconds and totals (115 words, about 46 s, budget 50 s, about 200 s; option (b) 87 words, about 35 s) are estimates from word counts at 150 words a minute. No stopwatch run exists.
- Newest owner sheet is v28 at 16:01:45Z = 21:31:45 IST and was still being written; 'newest' can change; C-10c must be rerun on the sheet the owner reads.
- Nothing applied; no n8n run; no spend; no real file outside the allowed list was edited.

## Output files
- REPORT-c6p.md sha256 efc2dbbbdc90e555c3381e103b3fb0e9d9404273b9b558c9a1080c6a53f7c6b5 (94 rows: 49 ready, 42 on defaults, 3 wait for a check, 0 NOT FILMABLE; wave 1 = 91 rows).
- REPORT-c6o.md untouched (modification time 2026-11-16T15:54:14Z, before this pass started).

## Fixes by review item
- Naive B1 and design M2: one definite card under the defaults (rows 11, 13, 14); box states 115 words, about 46 s; row 11 recomputed.
- Naive B2 and design M1: L-LEASE restated against Q22 (c) (ORD:186) and ORD:230; default 1 (reading 1); both sentences written out; 'none' reverses Q22 (c); recommendation 2; lease definition corrected in Words.
- Design M3: section 5a generated from the table (36 rows, page rows included).
- Design M4: C-10c rerun over v19 to v28 (evidence-c6p/static-checks-output.txt).
- Design M5: row 90 ends before ' owned by', 'third place' removed; row 91 says some bookkeeping files stay files.
- Design M6: row 6 item 16 says it is not verified that deletion erases data.
- Design M7, M8: no 'row N' and no 'accepted' in new text; row 76 'design intent, relayed'; 'stored' in rows 25, 37, 38; 18:04 UTC = 23:34 IST and (a), (b), (c) in row 8, box and C-10b.
- Design m1 (L-SAVE states what the owner approved: successful runs only), m3, m4 (144.3 s from n8n coming back up), m6, m7, m8 (new checks).
- Naive M1 to M11 and the box: box rewritten (words first, question table with defaults, one answer line, three lists, one ordered step list); L-SCENES removed; deletion gate described once (five entries); key scope separated from the take script's identity.
- Evidence caveats: stated in section 0 (audited tree is a read-only copy in the build session's scratchpad, not the repo checkout).

## Evidence (evidence-c6p/)
- verify-c6p-output.txt: 77 checks, 0 failed on REPORT-c6p.md (exit 0).
- verify-c6p-on-c6o-output.txt: the same script on REPORT-c6o.md: 30 of 77 fail (exit 1), so the new checks catch the c6o faults.
- neg-output.txt: 35 changed copies, 0 wrong (V0 control exits 0; every change exits 1; includes c6o itself).
- static-checks-output.txt, contact-grep-output.txt, void-check-output.txt: reruns at 16:01 to 16:05Z.
- Banned-vendor scan and secret-shape scan run inside verify-c6p.py (counts only: 0 and 0).
