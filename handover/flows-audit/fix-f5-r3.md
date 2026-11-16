# fix-f5-r3 (FIXER, final pass on RUNSHEET-WORDING.md), 2026-11-16
EGM skipped: final fix pass ordered by the lead after two review rounds; no further review round allowed by the brief. Static edit only; nothing ran. Only RUNSHEET-WORDING.md was edited, plus this note.

## Not done / uncertain (first)
- Not reviewed by anyone after this pass.
- Not verified against sources: I did not re-read VIDEO-RUNSHEET.md line by line; A-023a/b quotes come from grep of handover/demo/VIDEO-RUNSHEET.md (R:82 and R:90). A-088 may point at a sentence that does not exist (marked UNCHECKED in the row).
- N-8: the start commands, ports and the check commands of the three stand-in programs are UNCHECKED (crm_stub.py, stage_server.py, smtp_catcher.py live in n8n-mainframe/ and n8n-tests/, named in RUN-ON-LAPTOP.md lines 44 and 45, not in this checkout). Whether the take scripts do the flow-set switch is UNCHECKED and said so.
- Who decides D1 to D3 and who confirms D2 is my proposal (studio owner for D1 and D3, lead for D2 and P1 to P3); the lead may change it.
- Multi-sentence paste cells: kept as one string where the sentences are one spoken passage or one caption; split where they go to different places (A-008, A-033, A-050, A-010, A-023, A-087, A-097).
- Rows with a condition on P1 keep the condition in the last column only.

## Done
- Section 0 rebuilt: LEAD and PRESENTER on every step; lead-only steps (including the N-8 switch as steps 9.1 to 9.6 and the D/P checks) separate; A-016b moved to after filming; scene 9 now tags S5-b; S5-c is the same string as A-026a (pasted once); scene 10 says A-040/A-041/A-042 are lead notes, the screen is A-043/A-044a/A-044b; scene 11 optional and A-008b says scenes 5 to 10.
- D1 to D3 and P1 to P3 defined before first use, with default and who decides (section 0a). The list of held-back rows is built by script from the notes column (D1: 11 rows, D2: 14, D3: 2, P1: 9, P2: 4, P3: 1), so A-030, A-021, A-053, A-010, A-044a/b, A-050a (via A-087), A-007, A-036a are all listed.
- Terms before use (real-v5, film-v5, stand-in CRM, stand-in mail server, lease, stage service, recovery flow, claims row) in section 0; file locations named; scene-to-line rule and "no sentence today" explained; column "Type" renamed "Goes where" with the same words.
- Paste cells: no quote mark or apostrophe inside paste strings (script check found none); conditions moved to the note column.
- Overclaims: A-033a no longer says the server received the mail; A-030 and A-033 say use only if P1 is confirmed; A-016c now says only what the recording shows (burst 12 of 20 and 2 of 5 cited from B-195); A-050a/b closing card says the counts were reported by another test session and raw files not seen; viewer-readable relayed wording used everywhere; A-073a labelled relayed; A-073b/c carry D2.
- A-059 now names the two tests by what they do (model step failure and CRM error). R:34 reconciled with A-026a (new row A-026c).
- Nits: A-023 quote (R:90 13 min, R:82 separate row), A-087 now K1 only (about 62 s), V-11, B-145 (2 tries, 1 s wait, 10 s limit), B-101 (done with other than 1 CRM row or 1 mail), step 14 A-044a, A-036a says film-v5 re-read only, section 7 row count by script: 125 rows (64, 17, 44); claims rows 1 to 69 all present (script).
