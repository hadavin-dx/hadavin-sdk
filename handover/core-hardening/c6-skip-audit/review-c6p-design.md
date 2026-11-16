# c6p design review, round 4 (egm-design, condensed copy of the inline report), 2026-11-16
Target: REPORT-c6p.md (94 rows). Read-only; nothing run. Verdict: NOT ready for "apply all defaults". 1 blocker, 7 majors (most of the 8 c6o design and 11 naive majors are fixed).

## BLOCKER
- B1 Default L-LEASE (reading 1) vs ORD:230 (L-Q22c: the lease sentence stays out of the public post). Rows 13/21 put the lease sentence on the video card and caption; the report glosses "post" as not the video (no file says so) and never asks. Reading 2 has the same problem. The claim "none reverses Q22(c)" is unsupported: Q22(c) says a sentence exists, L-Q22c says where it is not. Fix: ask "does public post include the video card and caption?"; until answered default = plain statement with no lease sentence on public video text; restate the none claim.

## MAJOR
- M1 Default incoherent: rehearsal item 13 needs gap under 30 s first send to repeat; scene 2 is planned 40 s; no row changes scene timing; apply-then-revert cycle likely. Report recommends reading 2 but defaults to reading 1. Fix: change default per B1, or add restructure rows, or order C-9 part 2 and one rehearsal before rows 13/21.
- M2 Card arithmetic right for (a) 115 words 46 s and (b) 87 words 35 s, but not costed for the recommended reading 2: (a)+reading 2 = 130 words about 52 s (over 50 s); (b)+reading 2 about 114 words 46 s (over 35 s). L-CARDLEN "add 16 s" is wrong (it replaces a sentence; net +15 words about +6 s). 46/50/200 hold only under reading 1. Fix: table reading x length -> words, seconds, budget, total.
- M3 New run-sheet text uses report-only labels ("reading 1/2", "the lease question", "this report holds no rows"); the no-internal-labels check misses them. Replace with real sentences. Stale "(This check needs n8n and is not run yet.)" in item 11.
- M4 Ignores the lead's newest block (L-A/B, L-LEN one sheet, L-FACTS): L-SHEET and section 9 line 639 stale (v25/v26 text); reword as "confirm the one final sheet"; rerun C-10c on it.
- M5 Row 6 item 15 second leak scan plants only fake values, so a real key or password saved in n8n would give 0 hits. State what is searched (real value read from the key file, counts only) or do not claim real-account coverage.
- M6 C-10b PASS/FAIL cells disagree on Q27 ("(b) shown" vs all of (a),(b),(c)); say once in the box: no take on Mon 23 Nov unless (a),(b),(c) shown.
- M7 REPORT.md:80 (this session) already records that real-v5 recovery re-claims an unfinished lead and G12 (approval of the lease sentence) waits for the lead; the "plausibly meant a second send" guess is stale. Reading-2 facts rest on files not in the checkout; must not be spoken as fact before C-9 part 2.

## MINOR
Row 90 "owned by" still attaches to "state" (end the new text at "database n8n"). Box "if steps 4 to 6 done by Tue evening" is an inference. 18:04 is a plan fact that may move when need_seconds is read. "plan line 1051 is stale" stated as fact (ORD:187 says UNVERIFIED). Departure from ORD:147 ("read-only" card line) should be stated. "seen in the take's own database" vs Q20.2 fresh container. Contact grep evidence copied from c6k run (state file dates). Section 9 lines 652/653 duplicate. Verify script is string-presence only.

## Checked
Card counts 36+35+22+22=115, (b)=87, reading 2 sentence 40; rows 49+42+3=94; wave 1 91; 5a lists 36 rows; weekdays and UTC/IST pairs; ORD cites; QUESTIONS.md:73 and :104; RES:97 "stored"; C-10c counts v19..v28; rows 6/8/11/13/21 fixes from c6o confirmed.

## Not checked
Run sheet, page statements, flows, mf.py (not in checkout); take script; anything needing n8n; lane3 numbers; rows 62-69, 92, 33-48, 60-61, 73-89 text; ORDERS.md before line 120.
