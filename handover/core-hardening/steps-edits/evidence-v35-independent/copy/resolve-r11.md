# Round 11 resolve (builder pass; EGM steps are the lead's)

Written 2026-11-16 by the builder. Nothing committed, nothing spent, no sub-agents. Raw check output: `resolve-r11-check-output.txt` (`verify11.py`, 0 failures, 28 negative controls caught). Build script: `build-r11.py` (reads `EDITS.round10b.md`, every anchor asserted to occur once). The egm:egm-resolve skill was NOT used; this file is the builder's own list, to be checked by the lead.

## Not fixed or UNVERIFIED (first)
- Whether the take program deletes contacts (Q23): still UNVERIFIED; no text states it as fact.
- Crash-stop on key revoke, when the program can first spend, refusal after the end date (Q27): UNVERIFIED; E-12 now says the assistant asks for no take on 23 Nov until the lead's written reading of these three points is shown.
- Take id rule (E-12), Docker volume (E-16), settings-file location (E-51), `n8n.env` handling (ND1), Start-menu path to a WSL terminal (E-09): builder choices or unchecked clicks, marked UNVERIFIED in the text.
- Credentials: three in n8n now; confirmation g asks the lead to confirm no flow node calls the model with its own credential (missing input: plan v5 flow list, read only by grep of two line numbers).
- ND6 option B needs a new AGENT-SCOPE row first (stated in ND6); not written, owner/lead decision.
- Naive/design minors not done: none known skipped except those needing inputs not read (codebase review, WP6 runbook).

## Fixed, by finding
- Naive B1: E-09 rewritten as steps a to g with how to open a WSL terminal, cd, nano, save, umask, chmod, three names filled by the assistant's message, start only after "Create the password file".
- Naive B2: E-12 form has a crash-check slot, never counted in N1, N2, missed, not run.
- Naive M1: E-12 allows other messages before the reply; E-14 uses it.
- Naive M2/M3: take id rule, Linux user explained (E-12, E-52).
- Naive M4: E-16 question place, time, silence = No; result-copy folder; Docker volume case.
- Naive M5/M9: E-48 revoke timing, "Make a screenshot", receiver mailbox, key wording; E-55 heading.
- Naive M6: "web address" in E-06, E-07, E-08, E-11, E-25, E-49, E-53.
- Naive M7/M8: E-37 rewritten (heading, two accepted summaries, step 8 split, no internal words).
- Naive M9 and minors: E-03, E-04, E-15, E-22, E-41, E-42, E-51, E-52, E-54.
- Design M1: three credentials (E-09, E-37, confirmation g).
- Design M2: E-53 plain MUST NOT; E-49 alternative removed; ND6 B needs a new row.
- Design M3: E-48, E-55 and new E-57 (step 21), E-58 (send table line 147): key revoked right after last accepted take, by 18:19 UTC = 23:49 IST.
- Design M4: E-13 labels `NEW [HOLD G3: DO NOT APPLY] (1)` and `(2)`.
- Design minors: E-17 clause shortened (E-36, R1 follow), ND14 answered (a), confirmation h confirmed, header counts.
- Independent evidence (E-36): text N is now quoted in the Why, not a NEW block. Every Apply now row has exactly one NEW block; 13 HOLD-labelled blocks (12 Hold rows, E-13 two), stated in the header and checked.

## Numbers
56 rows (Apply now 44, Hold 12): OWNER-STEPS 37, AGENT-SCOPE 15, DECISION-one-store 4. Banned-list hits 0 (count only). Secret-like strings 0.
