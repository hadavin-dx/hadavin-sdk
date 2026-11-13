# notes-v8-C (builder, text only; edited docs/settings.md and docs/portal.md in /tmp/v8work)

Studio folder not present in this container: no R-numbers looked up or cited. No tests, no linters, no network, no commit.
Facts were checked against: src/lead_desk/config.py (real_services, public_bind_problem, send_timeout checks), constants.py (OUTBOX_STAND_INS, CALL_DEADLINE_MAX_SECONDS, LIVE_MAX_TOKENS_MAX), loader.py (load_demo_portal), crm_hubspot.py and smtp_provider.py (stats_file, ca_file), desk.py (reminder subject uses the first 8 characters of the lead id). out-d8.md rows 1 and 8 concern other files (server.py test and mirror constants), none of them cited in my two docs (grep found no hit): not mine.

| row id | file:line | problem | verdict | edit (old -> new) |
|---|---|---|---|---|
| d6 s3 | settings:3 | "every setting has a default" | TRUE-PROBLEM (c) | -> "can be set by an environment variable; where a default exists the table shows it"; column meaning and "this computer's own address" defined once |
| d6 s8 | settings:8 | smtp not in the real-service list | TRUE-PROBLEM (c) | code: OUTBOX_STAND_INS = http, smtp, so smtp is NOT real; added "DESK_OUTBOX=smtp does not count"; split sentences; 0.0.0.0 named once |
| d6 s10 | settings:10 | "only demo exists" vs real services | TRUE-PROBLEM (c) | -> "only one set of parts exists, called demo; real services are chosen with the next rows" |
| d6 s12 | settings:12 | smtp wording, real-mail promise | TRUE-PROBLEM (b,d) | smtp = mail server on this computer only (host must be loopback); added "no shipped evidence shows sending to a real mail account" |
| d6 s16/s17 | settings:16-17 | hidden risk; 3rd refusal missing | TRUE-PROBLEM (d,c) | WARNING reworded; nudge_to now lists all three refusals (line 60 rule) |
| d6 s28/s36 | settings:28,36 | 600 vs 9 seconds | TRUE-PROBLEM (c,d) | code: send deadline capped at 9. Both places now say "above 9 is accepted but has no effect" |
| d6 s70 | settings:70 | SMTP_TIMEOUT contradicts row 36 | TRUE-PROBLEM (c) | now "no practical effect; real wait is DESK_SEND_TIMEOUT_SECONDS, capped at 9" |
| d6 s68 | settings:68 | one author run turned into "must" | TRUE-PROBLEM (d) | -> "In one run by the author ... was refused ... So give ... a real domain" |
| d6 s83 | settings:83 | "only ledger survives restarts" vs stats files | TRUE-PROBLEM (c) | code: nothing reads stats files back (only write_stats exists). -> "Only the ledger is read back after a restart; the stats file is only written" |
| d6 s78 | settings:78 | two names, no meaning | TRUE-PROBLEM (a) | stats file and CA file explained from code comments (ca_file: extra trusted certificate authorities, verification stays on) |
| d6 s97/s104 | settings:104 | "caps bound the total" vs provider may charge | TRUE-PROBLEM (d) | -> "caps limit the total the desk records; the provider's own bill may differ"; paragraph split in 5 |
| d6 s121 | settings:121 | "never a traceback" then "a traceback is possible" | TRUE-PROBLEM (c) | scoped: "Three cases are the exception and can still print a Python error trace"; split into sub-bullets; run_live_check moved to its own bullet; n8n and loopback defined |
| d6 s122 | settings:122 | "replaces every address" vs long not-cleaned list | TRUE-PROBLEM (d) | -> "removes the common kinds of address ... read the result by eye"; split into sub-bullets; "look-alike" and "over-cleaning" reworded |
| d6 p23 | portal:23 | bind advice omits DESK_ALLOWED_HOSTS | TRUE-PROBLEM (d) | added "put the name the container uses into DESK_ALLOWED_HOSTS, or every request gets 403" (settings line 24 says it) |
| d6 p21 | portal:21 | Host "names this computer" incomplete; Origin missing | TRUE-PROBLEM (c) | now: this computer or its bind address or DESK_ALLOWED_HOSTS; foreign Host or Origin gets 403 |
| d6 p7/9/19 | portal | "demo tools" vs "demo extension" | TRUE-PROBLEM (c) | one term: demo extension (the optional demo_only folder); loader.py confirms it loads only with demo adapters and no real service |
| d6 p17 | portal:17 | "blind mail system" | TRUE-PROBLEM (a,b) | plain sentence about pressing "it was not sent" |
| d6 p19 | portal:19 | "either" with no antecedent, understated | TRUE-PROBLEM (a,d) | "They need no login, so anyone who can reach the desk can use them" |
| d6 p5 | portal:5 | masking sold as privacy; 336-word paragraph | TRUE-PROBLEM (d,e) | now leads with "changes only what is shown on screen; values are still sent to the browser"; page list as bullets; test notes in own paragraph; "only the main log was checked" own sentence; "adds up" dropped |
| d6 p3 | portal:3 | "stage of any deployment" undefined | TRUE-PROBLEM (a) | repo has no deployment-stage text, so -> "nothing to do with how the desk is run (demo or live)" |
| d6 p11 | portal:11 | thin support wording | TRUE-PROBLEM (d) | "one test tries a write and it fails" |
| d6 p13 | portal:13 | exceptions before the main fact; vague "another page" | TRUE-PROBLEM (a) | notice sentence moved first; "Leads list or Request log" |
| d6 s128 timing | settings:28 | cmd.exe, plain-SMTP/send | TRUE-PROBLEM (b) | rewritten in plain words |
| d6 other jargon rows | settings 7,9,11,13,14,16,19,22,23,35,41,51,54,60,62,74,76,77,84,97,102 | jargon/unclear | TRUE-PROBLEM (a,b) | one short plain-word edit each (bind-cell and 600/9 rows above included); live max tokens row split with the number 1000000 from constants |
| d6 s15 | settings:15 | name says path, variable says FILE | TRUE-PROBLEM (a) | one sentence under line 3 on what the columns are |
| d6 s24 | settings:24 allowed_hosts | 130-word cell | NOT-A-PROBLEM of fact; readability not chased (not in my 8) | unchanged |
| d6 s46, s68 "banner" | settings | "demo banner" unexplained | not chased (outside the 8) | unchanged |
| d9 | settings:125 | LEAD_DESK_PATH_ROOTS rows | see NOT-ADDED | none |
| d8 | - | rows 1 and 8 | not my files | none |

Readability top 8 done: portal:5, settings:121, 122, 104, portal:23, portal:3, settings:10, settings:83. Also rewritten as a bonus because they were true problems: settings:8, 12, 28.

CODE-LOOKS-WRONG: none found. (Observation, not a code fault: DESK_SMTP_TIMEOUT_SECONDS accepts up to 600 but never changes the wait; doc now says so.)

NOT-ADDED (out-d9 "findings no doc mentions" for my files):
- #7 path object with an int or None from its file-name method raises TypeError: not added; only the sibling evidence file holds it, and no test or comment in this repository does (not checked in code; I did not search tests). Next step: lead decides on a "reported by a separate run; no log is shipped" sentence or a code fix.
- #8 hard links bypass the folder limit: same reason, not added.
- #10 LEAD_DESK_PATH_ROOTS set to the root folder removes the limit: not added; it is a true consequence of the rule at settings line 125 but no repository test or comment states it. Next step: the lead may add one sentence marked "reported by a separate run of the desk's tests; no log is shipped".
- basetemp / Linux 3.13 / skip counts / timing (#1-6, 11): belong to docs/tests.md and README, not my files.

Not checked: nothing was run; the Markdown was only re-read for odd backticks (script, none found) and 40+ character runs (none). Settings.md lines 116-120 (the real-services script, word "book") and other low-ranked rows were not edited.
