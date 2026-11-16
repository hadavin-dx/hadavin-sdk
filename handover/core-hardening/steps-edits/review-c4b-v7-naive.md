# C4b v7 naive-owner review, round 2 (condensed copy of the inline report), 2026-11-16
Target: steps-edits/OWNER-STEPS-realrun-v7.md (317 lines, read in full). Ran nothing. NOTES-FOR-LEAD not read. Verdict: MAJOR, no blocker. Round-1 findings mostly fixed.

## Majors
1. Step 0 (L136-151) is a live HubSpot write (create, change, delete a contact, key in the shell) with no boxed warning and no stated safe default; boxes exist only above E, F, G, I. Stop cases come only at L151. Unclear if the general go-ahead (L7) covers step 0.
2. Step 0 item 6 (L144): exit 0 means every line PASS or SKIPPED; item 7 (L146-149): SKIPPED create/delete = "delete not shown". Owner will read exit 0 as success. Say exit 0 does not mean delete works; the studio lead decides.
3. Step 0 call count: an 8th-call fallback delete (L136) vs "--yes-spend-calls 7 must equal the planned count" (L142). Not said whether the 8th is allowed or what the owner does.
4. `cat <path>` of stage.env (L158, L206) may put a secret on screen; sheet never says the file holds none; no stop-and-do-not-paste rule for A and E; no check that the screen is not being filmed.
5. Model key: the one paid secret with no owner step. I.6 (L258) "unless the studio lead says in writing the model key is cancelled by you": who cancels? I.5 only says the lead messages. Retire check does not test it (L31). Nothing says the key stays live until 23 Nov.
6. Who stops/restarts n8n and who films are deferred to run card rows 4 and 5 (L48, L85, L87); no cue for the named person; nothing on stopping n8n when the owner does not touch Docker (L7). Round-1 finding 1 only partly fixed.
7. C.3 (L176) has the owner copy connection values from WSL into n8n via the clipboard; L7 says the owner does not rebuild connections. Table row (L77) shows only "sign in".

## Minors / nits
- Editor text left in owner prose: L3 "Nothing was run to write this sheet"; L19 "(source: the scope sheet ... figures were not re-checked)"; L12 "stand-in re-smoke"; L136 "The studio lead says the script should make..."; L112 "the aim is missed". CHANGES (L11) claims none remain.
- Undefined terms: "re-smoke", "Postgres program" (L271), "n8n's connections", "saved runs", "database container" (L176, L257).
- Table vs prose: rows C.1 (L75), E.0 omit "only if run card row 13 lists it"; send-table (L276) silent on how screenshots reach the lead; I.1, send-table, I.3 disagree (take/send/save); step 0 "key-like text in table" message missing from send-table; "Rehearsal values" row (L79) sits after D though A and E need it.
- Contact count (L15, L223): does an "unknown" C leave a contact? where does the alert mail go?
- Two-meaning words: "run", "check", "pass".
- I.1 (L247): which browser profile for the sender sign-in; D.2 says do not film the sender account.
- Can a run name be reused if the run stops at a bad login before the typed answers (L213-214)?
- CHANGES line numbers off by 1-2 (E box L194 not L193; G box L228 not L227); "open absent from owner text" cannot be literally true.

## Round-1 check
1 partly fixed; 2 fixed; 3 fixed; 4 fixed (small gaps); 5 partly (L3, L12, L19, L136); 6 fixed; 7 mostly; 8 mostly (US$180 of US$189 source opaque). Round-1 minors fixed.
Not checked: click paths, existence of hubspot_probe.py / run_real_check_n8n.py / --retire-check, run card, dates against studio notes. Weekday and UTC/IST arithmetic consistent.
