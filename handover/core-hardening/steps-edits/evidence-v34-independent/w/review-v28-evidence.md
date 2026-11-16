# v28 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: steps-edits/evidence-v28-independent/00-SUMMARY.md. Recorded, not judged.
## Failures and caveats first
1. Runner's checker: 1 FAIL on unchanged originals: LEAD-RELEASE-NOTE-v12.md line 202 lists "18:14 UTC" with no source on that line (source on lines 11, 75, 77).
2. Owner pages use R1, R4-R10, W1-W9, L1-L5 (defined); no C-/G-ids or ledger words.
3. Sheet page 6,054 (A) / 6,033 (B) words (limit met); package A 8,555 / B 8,530 (not met if 6,300 meant the whole package).
4. "Three credentials" read as three kinds (model key, Gmail app passwords, HubSpot app secrets); no fourth found.
5. No owner page says "never typed into n8n"; numbers line says "none (the lead checked n8n's credential store)"; the note line 24 says FACTS records a model credential already in n8n (unverified).
6. No unpaired UTC time on owner pages; lead note has 3, open list 4.
7. Placeholders: only two bracket labels; the 38 angle slots are labelled only by the sample heading; sample shows 20 s and 15 min under a LEAD FILLS label.
8. 18:19 UTC = 23:49 IST not on any owner page; 18:04 appears once (open list, as a conflicting answer).
## Results
sha256 of 104 files unchanged; runner K01-K10 1 FAIL; builder check-v28 0 failures; builder mut28 166 plants, 165 caught, 0 missed; runner mutations 42/42 caught; build-v28.py twice gives identical sha256 for all 9 files; A/B differ only in older-key wording, A/B letters in pointers, alarm count (3 in A, 4 in B); film page identical; banned scan 0.
## Not done
No wording or safety judgement; v28-fail-proof not run; nothing run against n8n, HubSpot, Gmail or a model account.
