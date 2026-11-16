# fix-rswording12.md (fixer for read r5, reviews/rw-r5-reader.md Majors 1 to 9), 2026-11-16

Edited only RUNSHEET-WORDING.md (RW). CLAIMS-TABLE.md (CT) not touched (another fixer, a0ac58a, is editing it). Nothing committed. A copy of RW before the edit is in the scratchpad (RW.before.md). RW went from 501 to 504 lines (new paragraph "Short names", one added paragraph in section 6).

## What failed or is open (first)
- python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md now FAILS for 4 ids (expected, until the SYNC LIST below is applied in CT): B-003a, B-003d, B-011, B-088.
- Not decided by me (unknown in every file): who types y / the challenge number / end (Q31 item 43); the wait and the expected attempts value (Q31 item 45, set at rehearsal); who reads the proof if the lead hands it over (Q31 item 33); the channel for that (Q-I has no Q31 item; item 9 is a different chat); who checks the stage service (Q-J, no Q31 item; item 25 is only the nearest). These are written as "unknown: lead answers (...)".
- No new RW rows added for item 9 (see below).

## Changes per item
1. Who: added the definition "the person at the keyboard" (Q-A; unknown, Q31 item 43). Step 10 no longer tells the lead to tell the lead: it says the lead decides, and a handed-over reader tells the lead (person: Q31 item 33; channel: Q-I). Rows A-016b, A-016f no longer say "tell the lead". "lead fills in" replaced by "unknown: lead answers (Q31 item 43)" in the typed-answers line and in step 4.
2. Waits and who judges: "the wait" and "expected attempts value" now say "unknown: lead answers at the rehearsal (Q31 item 45); rehearsal 1 planned Wed 18 Nov 07:40Z = 13:10 IST (Q31 item 13)". The lead judges the proof (holds only when both parts are on screen). Mailbox pane and table screenshot defined in step 10. Notes of A-016b, A-016f, A-016h, B-003b, B-219 now say who reads the proof and that the two values are unset.
3. HELD rows: notes of B-045, B-046 (qualify_stage.py and test qs_01; Q31 item 25), A-004 (Q-J), and section 7 rows A-043, A-092, A-097a, A-097b, N-2, N-4c, B-077, A-001L, S5-a, S5-b, S5-c now name what they wait for (lead's decision to film the later video; table screen or alert scene or scene 5 run once in rehearsal, laptop agent runs, lead reads).
4 to 6. Paste strings made honest (these change the pasted text):
   - B-003a: "is refused" became "is built to be refused ... and to get the stored state back" (empty-ID caveat was already there).
   - B-003d: empty-ID caveat added; "is not started a second time" became "is built ... not to be started a second time".
   - B-011: no longer "built to send at most one": now "built to claim the send once per lead ID and not to retry, so it is meant to send at most one"; added "Whether a slow live run taken over after the 45 s lease can send a second e-mail message is not measured" (same as B-156).
   - B-088: "the studio owner did not answer y" became "the answer y was not typed" (the file says "you did not answer y"; who types is unknown, Q31 item 43).
7. Fragments: B-016, B-019, B-024 marked "FILE EDIT, not paste-ready" (several cells of one table row; lead types the cells by hand). V-11 marked "part of a sentence". Their strings are unchanged, so no sync needed. SetCrmId and CrmIdOk defined in plain words in the new paragraph "Short names".
8. Terms: new paragraph "Short names" before the status words defines RW, CT, R:, P:, PLAN:, ONS:, CRM, real-v5, film-v5, K1, SetCrmId, CrmIdOk. X described once: X-1 to X-4 are claim ids in CT; X-5a, X-5b, X-6a, X-6b, X-6c exist only in RW (checked: CT lists X-1 to X-4 only as ids). Lines 22 and 173 now say the same.
9. See "Other files holding processed once" below.

## SYNC LIST for CLAIMS-TABLE.md (replace word for word; 4 ids)
Cells to change, found by the old string (CT line numbers moved while I worked; search by text). B-003a and B-003d are both in the B-003 row of Part 3 (the "Paste strings, word for word" sentence) and the same B-003 row also holds earlier "PLAN:9 gets" and "ONS:135 gets" sentences that differ from RW (they lack the last sentence of B-003a and say "is not run a second time"): make them match too.

1. B-003a (CT row B-003). Old: "the same lead ID sent twice (a resend or a repeat submit) is refused by the n8n claim row and gets the stored state back, as long as the lead ID is not empty; an empty lead ID is not stopped by the claim row today. This is how the flow is built, not a measured guarantee."
   New: "the same lead ID sent twice (a resend or a repeat submit) is built to be refused by the n8n claim row and to get the stored state back, as long as the lead ID is not empty; an empty lead ID is not stopped by the claim row today. This is how the flow is built, not a measured guarantee."
2. B-003d (CT row B-003). Old: "the same lead ID sent twice (a resend or a repeat submit) gets the stored state back and is not started a second time; this is how the flow is built, not a measured guarantee"
   New: "the same lead ID sent twice (a resend or a repeat submit) is built to get the stored state back and not to be started a second time, as long as the lead ID is not empty (an empty lead ID is not stopped by the claim row today); this is how the flow is built, not a measured guarantee"
3. B-011 (CT row B-011, and CT Table row 47 for PLAN:38, column of the replacement). Old: "The flow is built to send at most one e-mail message per lead ID. If the send is cut off, the table row ends unknown (the e-mail message may or may not have arrived) and an alert is sent. This is the design, not a measured guarantee."
   New: "The flow is built to claim the send once per lead ID and not to retry the send, so it is meant to send at most one e-mail message per lead ID. Whether a slow live run taken over after the 45 s lease can send a second e-mail message is not measured. If the send is cut off, the table row ends unknown (the e-mail message may or may not have arrived) and an alert is sent. This is the design, not a measured guarantee."
4. B-088 (CT row B-088, and CT Table row 80 for FAILED-TAKE-NOTE.md:6). Old: "Exit code 1 normally means the script stopped before calling anything (the studio owner did not answer y, or there was no terminal). An unexpected error after the question also gives exit code 1: look for sent e-mail messages and made-up contacts before you say nothing was called."
   New: "Exit code 1 normally means the script stopped before calling anything (the answer y was not typed, or there was no terminal). An unexpected error after the question also gives exit code 1: look for sent e-mail messages and made-up contacts before you say nothing was called."
   Also in CT row 80 the sentence "who answers y at the take is BLOCKED (WL-1)" stays true.

After the sync, rerun: python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md (expect 136 found, 0 not found).

## Other files holding "processed once" (item 9)
Searched handover/ (excluding fix-*, reviews, lanes, snapshot, tools/scratch). Hits:
- With an RW row: demo/VIDEO-RUNSHEET.md lines 4, 32, 41 (A-002, A-015, A-016c, A-016e, A-049); demo/PLAN-4-NLITE-FROM-LEAD.md lines 9, 57 (B-003a, B-003b); flows-audit/inputs/OWNER-STEPS-realrun-v3.md lines 131, 135 (B-219, B-003c, B-003d).
- No RW row: demo/n8n-kill-between-steps.md:11 (test description, other meaning); lead-owned: inputs/DECISIONS-2026-11-16.md:2, ORDERS.md:58 and :76, ANSWER-Q15-lead.md:2 (QUESTIONS.md L26 says the lead corrects DECISIONS); the audit's own notes that quote the phrase to reject it: QUESTIONS.md (82, 124, 279, 303, 332, 362, 404, 577), QUEUE.md:8, LEDGER-ROWS.md:3-4, OWNER-STEPS-q16-rows.md:362, FIX-PLAN.md:114 and :121, flow-check/README.md:13, flow-check/REPORT.md:49, FINDINGS.md:109-110, FLOWS-AUDIT.md:1337, SCENE-FLOW-MAP.md:39, RUNBOOK.md:215, F6-AUDIT.md:43, inputs/plan-wp6-resmoke-v5.md (lines 14, 412, 413, 490, 519), patches/review-r2-patches.md:9, patches/REGENERATED-NOTE.md:5 and :11.
- Not added as rows: a row needs a CT claim id, a verdict and a target sentence to replace in every column; these lines are lead-owned or are the audit's own quotes, not sentences a viewer sees. I did not open every one to confirm each is a quote (not checked). The summary is also in RW section 6.

## Checks run (raw)
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: total rows 185; 86 flagged ids, none without a row; RESULT: PASS (exit 0).
- python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: paste strings in RW 136, found in CT 132, not found 4 (B-003a, B-003d, B-011, B-088): FAIL, expected until the sync.
- python3 -I tools/check_refs.py (from repo handover/..): PASS 5166 references.
- python3 -I tools/check_secrets.py RUNSHEET-WORDING.md: PASS 0 hits in 1932 files.
- python3 -I tools/check_counts.py: PASS 52 files / 655 nodes.
- ruff format --check: no .py file touched, not run.
