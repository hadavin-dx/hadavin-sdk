# One-place sweep r1 (lane c, read-only), 2026-11-16 UTC. Nothing run; text read with grep and line views only.
Scope: steps-edits, paste-check, patches-ready, cross-read, c6-skip-audit, mutation-lane under handover/core-hardening/ (plus ORDERS.md, which holds the lead's answers). Path prefix omitted below. Not read in full: any v1-v9 sheet, raw logs, the 2.3 MB of patch and evidence files.

## A. Copies that disagree RIGHT NOW (failures first)
1. **Four different lease sentences, and the lead's own ruling is contradicted.** ORDERS.md:152 (Q21.2): "no takeover after expiry"; "a gap longer than the lease is not claimed".
   - steps-edits/OWNER-STEPS-realrun-v13.md:141 (box NOT APPROVED): flows re-claim after the lease, "differs from Q21.2".
   - paste-check/plan-v10-real-v5-edits.md:458 (Text A): "inside the lease (45 seconds in real-v5) is processed once".
   - paste-check/plan-v10-real-v5-edits.md:459 (Text B): says it follows Q21.2 but the sentence says "Recovery re-claims an unfinished lead".
   - cross-read/CLAIM-EVIDENCE-Q21.md:11: a fifth wording ("the system may pick it up again").
   - Single source: ONE sentence in DECISIONS (the lead writes it; owner approves). Open item L11 (steps-edits/v13-OPEN-FOR-LEAD.md:17) is still open.
2. **Lease length: 45 s / 20 s / 120 s, and "read" vs "second-hand".**
   - c6-skip-audit/REPORT-c6f.md:53 and REPORT-c6e.md:39: "older tests 20 s, lane3 45 s, one older series 120 s". cross-read/CROSS-READ.md:39: system-map files say "120 s".
   - paste-check/claims-check-c14.md:7: 45 s "only second-hand"; paste-check/plan-v10-real-v5-edits.md:459 and cross-read/CLAIM-EVIDENCE-Q21.md:5: "read" at mf-form.json:97.
   - steps-edits/OWNER-DAY-CARD-v13.md:10 leaves the lease as a blank; steps-edits/OWNER-STEPS-realrun-v13.md:141 hard-codes 45.
   - Source: the flow file at the take's commit (mf-form.json:97 and mf-recovery.json:26), copied into run-card row 3 only. Nothing in the 45 s claim has been re-read from the take head.
3. **Port 5690 is called the take port.** paste-check/plan-v5-repin-v6.patch:81 says "take n8n 5690, broker 5691; control 5692/5693". The lead's decision 6 (cross-read/contradiction-sweep-r1-summary.md F3) says 5690 is the REHEARSAL port and the take has its own. v13 sheet and card correctly leave it blank (card:14, appendix:31). The same label sits in plan-v5-repin-v3, -v4, -v5 patches and the gate-rows patches (the shell function default `GPORTS=5690|5691`). Source: run-card row 13 for the take; one "rehearsal ports" table in the newest repin patch only.
4. **Money stop has three names.** steps-edits/OWNER-STEPS-realrun-v13.md:3 "money stop"; :65 and :101 and card:62 "window end"; v8:28 "stop time". One time, three words. The last-start time is also typed twice: appendix:95 hard-codes "18:14:40 UTC = 23:44:40 IST" while the same line says "row 3 has the exact time", and the card:38 asks for 20 minutes margin (so the effective last start is 17:54:40). If the date moves, appendix:95 and sheet:101 go stale. Source: run-card row 3 / A.6 line; appendix 95 should say only "row 3".
5. **Amounts 180 and 189.** v10 (OWNER-STEPS-realrun-v10.md:87) and v11 (citation-check-v11.md:14) state "180 backstop, 189 credit". v13 appendix:140 says the reverse is "not clear" and the sheet uses neither. BRIEF-PREAMBLE.md rule 18 calls US$189 the "live-model TESTING budget". Three readings, no file with the source. Source: the lead's step A message (open L18, v13-OPEN-FOR-LEAD.md:24).
6. **Cancel-key timing differs by version, and old versions are not marked superseded.** v13 (sheet:114-118, card:12/:67, appendix:80): same day, right after F.4, no waiting. v10:204 / v11:182: wait for "model program stopped", deadline 60 minutes after F.2. DECISIONS item 5 (cross-read/review-cross-read-r1.md): "at clean-up". ORDERS.md:150 (Q21.1): "right after the take, same day" = v13. Risk: the owner prints an old file. Source: ORDERS.md Q21.1; add a one-line "SUPERSEDED by v13" header to v4-v12 sheets and cards (not done; I may only write one file).
7. **"One Postgres server, two databases": stated as the caption, but not proven.** v13 sheet:143 and appendix:66 say it as fact; appendix:90 item 8 says "aim ... not proven until the rehearsal shows it"; ORDERS.md:152 (Q21.3) says caption "one Postgres server, two databases" plus a second record (journal file). Source: Q21.3; the caption stays blocked until the rehearsal shows it (names are UNVERIFIED, appendix:66).
8. **Test counts for the take patches.** 9514 (c7b tree with full C-01 and A-01), 9491 (v3, all three), 9413 (v4), 9418 (v5 final, patches-ready/v5/README.md:66), baseline 9389 or 9391 plus 2 repo-guard failures. Only v5 (C-01-MINIMAL + G5, A-01 deferred) is the kept scope. patches-ready/README.md:3 still says "STATUS: UNVERIFIED, nothing run" and lists the older C-01/A-01 set, so the top README and v5/README.md:5 disagree on which patches apply. Source: patches-ready/v5/README.md only; retire or banner the top README.
9. **Mutation evidence is on patches that were cut.** mutation-lane/REPORT.md:7,10,11 (C-01 13 of 20 killed, A-01 15 of 27) ran on full C-01 and A-01. MUTANTS-V2-PLAN.md:3 is marked STALE for v5. The kept patch C-01-MINIMAL has its own count (v4 "8/8", v5 "12 hand-made mutants", v5/README.md:69), a different list. Source: one mutation table in patches-ready/v5/README.md; mutation-lane files get a "does not apply to the kept scope" banner.

## B. Values stated in many files, consistent today, can still drift
| Item | Single source | Where it is repeated (agrees now) |
|---|---|---|
| 18:29 UTC = 23:59 IST (23 Nov), post by 25 Nov 15:00 UTC = 20:30 IST | ORDERS.md:150 | steps-edits v13 sheet:3,:101,:136; appendix:95; card:12; ~10 citation-check and review files; check-v13.py:73 greps the string |
| 13 sends (A 2, B 10, C 1), 3 paid calls | the take program's own printed notice (not read) | v13 sheet:37, appendix:51,:57, card:49, v10-v12 copies. "13" is also the number of post-ban items (sheet:143), appendix section 13 and run-card row 13: three unrelated 13s. The send count itself is unbacked (summary F1 note) |
| 23 run-card rows (rows 8 and 9 "not used") | appendix 2 list | v13 sheet:8, appendix:15; older reviews say "17 rows" |
| 5678/5679 are the owner's own n8n | DECISIONS item 6 | v13 sheet C.3, card:14, appendix:98, plan patches |
| 14 minute start margin (860 s) | the take program | appendix:95, citation-check-v11.md:30 |

## C. What no reviewer has checked yet
- OWNER-STEPS-realrun-v13.md, OWNER-DAY-CARD-v13.md, OWNER-STEPS-v13-APPENDIX.md: no review-v13 or citation-check-v13 file exists (STATUS-BOARD.md:12 says 4 reviews are "under way"; none is on disk). The v12 reviews failed the sheet 3 times.
- plan-v10-real-v5-edits.md was last reviewed by paste-check/review-v10-r6.md only; its Text A and Text B contradict each other and Q21.2 (A.2).
- cross-read/CLAIM-EVIDENCE-Q21.md and cross-read/contradiction-sweep-r1.md have no review (review-cross-read-r1.md covers CROSS-READ.md only).
- patches-ready/v5: no codebase review of v5 after design-r5-c5v5.md (last codebase review is codebase-r4-c5v4.md). v6-extra FIX patch: reviewed only in the c7b rounds, not the final pass on its own.
- No file anywhere shows the flow JSON read at the take's commit; Postgres paths (455 skipped tests) and the unique index ("index not seen") are unverified.
- Sheet text was never walked by the owner or a stranger on v13 (no dry run), and none of the sheet commands has been run.
- Not read in full by me: v13 appendix beyond the lines cited, c6-skip-audit raw files, 2.3 MB of patch and evidence files. A drift outside the grep terms would be missed.

## D. Next step (for the lead)
Decide the lease sentence (A.1) and the 180/189 meaning (A.5); add superseded banners (A.6, A.8, A.9); then one reviewer pass on v13 with this file as the checklist. EGM skipped: read-only sweep and one report file; no code, plan or config changed.
