# T19 terms (one page for all T19 pages; written Mon 16 Nov 2026 by the system-map session)
Who is who: owner = the human who runs the studio (older pages also say studio head). Studio lead = the Claude session that does the technical steps and messages the owner. System-map session = the Claude session that wrote this page and writes only in handover/system-map/. Paths on this page are relative to handover/system-map/work/.
STATUS: T19 cannot be run yet. Four things are missing. The studio lead owes all four by Tue 17 Nov 12:00 UTC / 17:30 IST (a proposal, not agreed): A) the POST address, B) the POST body, C) the SQL that counts stored rows, D) how the mail and the HubSpot write are counted.
RULE (one rule, one actor): the terms marked NOT RECORDED below stay undefined until the studio lead defines them. They are: freeze input, STOP class, smk_count, drive.py, hex tool, CUT, EV, $T, c/c20, film-v5, F8, owner clean-up, 7.5 s, C1, E2. If a term is still undefined at the due time, the system-map session removes every sentence that uses it from t19-gap-facts.md, t19-gaps-r2.md and t19-row-and-steps-r3.md.
CHECK: an UNVERIFIED row is checked only by reading the file named in it or by running T19.
Used by: t19-gap-facts.md, t19-gaps-r2.md, t19-row-and-steps-r3.md, t19-and-stored-data-steps.md, row-dm-plain.md. Only meanings found in files are given; every other term says NOT RECORDED and whom to ask (the studio lead, the Claude session doing the technical steps).

## Test in one sentence
T19 posts the same made-up lead twice to the demo's n8n form address and expects exactly 1 mail, 1 HubSpot write (a contact create or update) and 1 stored row. It has not run. Proposed pass rule (from the system-map session; the studio lead confirms or changes it by Tue 17 Nov 12:00 UTC / 17:30 IST): pass = 1 mail AND 1 HubSpot write AND 1 stored row after the two identical posts. Not confirmed.

## Terms
| term | meaning | status |
|---|---|---|
| take | the one filmed run of the lead-intake demo on made-up data | defined in work/GLOSSARY.md |
| lead key / lead id | the id that marks a lead as the same one when sent twice (field name not recorded here) | partly recorded |
| mf_leads | probably the table that stores leads, in the demo's own Postgres database (not n8n's); which CREATE TABLE is authoritative: NOT RECORDED | UNVERIFIED |
| state | the status column of a stored lead; six values exist (list NOT RECORDED here); "done" = the last step finished, "unknown" = never marked | UNVERIFIED |
| alert | a mail that tells a person a run failed | UNVERIFIED |
| film-v5 | the unpatched set of n8n flow files the plan imports | NOT RECORDED beyond that |
| patched copy | a copy of the flow files with the patches applied; its folder is unknown | NOT RECORDED |
| freeze input | NOT RECORDED | ask the studio lead |
| STOP class | NOT RECORDED | ask the studio lead |
| smk_count, drive.py, hex tool, CUT, EV, $T, c/c20 | NOT RECORDED (drive.py and the hex tool are helper programs; hex tool: NOT RECORDED. Ask the studio lead) | ask the studio lead |
| F8 | the check after the owner clean-up that no row with the test lead id is left in n8n's tables; actor, table list and time NOT SET | UNVERIFIED |
| row DM | the test that kills n8n between storing the lead mail and marking the lead done, to prove no second mail goes out | UNVERIFIED |
| HIT / MISSED (row DM) | HIT = the kill landed in the gap (under 7.5 s after the mail); MISSED = it did not; two MISSED = "not tested", never a pass | UNVERIFIED |
| C1, E2, line 555 item 9 | labels into a plan file that this session has not seen | NOT RECORDED |

Rule for the NOT RECORDED terms: see RULE under STATUS at the top.

## Open items for the studio lead (owner: the studio lead; due Tue 17 Nov 12:00 UTC / 17:30 IST; both proposed by the system-map session, not agreed)
1. The studio lead names the patched copy's folder.
2. Give A, B and C (POST address, POST body, SQL that counts stored rows) and D (how the mail and the HubSpot write are counted).
3. Say what "freeze input" and "STOP class" mean.
4. Say who runs T19 and F8.
