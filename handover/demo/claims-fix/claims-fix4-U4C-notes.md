U4C notes. Label L = "from the author's own run; no log is shipped". Audit verdict for every row below: U unless stated. Nothing run; all by reading (n8n/*.json, demo_only/fakes_server.py:243, tests/test_n8n_proof_result.py, tests/test_hubspot_probe.py).
n8n-recipe.md
- l.4 / l.10 (run of 2026-11-09, node ids, import): already labelled "tried once by the author, logs not shipped" | unchanged | W (already corrected)
- l.26 n8n with Node reached desk | + L | F
- l.34 id in body works, replayed true | + L | F
- l.36 execution id changes on re-run | now "expected to change... not checked, so it is not used" | F
- l.44 400/413 shows red | "showed red (L)" | F
- l.46/76 "caller always gets 200" | past tense "got 200", L, "other versions/settings not tried" | F
- l.50-54 steps list, retry 2nd try ~1 s, 3 tries ~2 s, 400/413 x3, 1 lead/1 CRM/1 email | list header labelled L; numbers unchanged | F
- l.54 "Retry On Fail cannot skip retries for 4xx" | "In that run the setting did not skip retries for 4xx (no n8n documentation was checked)" | F
- l.58 CRM default keyed | demo_only/fakes_server.py:243 default="keyed": true | S (no edit needed)
- l.68 executions list showed success | + L | F
- l.70 ten at once, 1 new/9 dup | + L; "same holds via web address" -> "author reports the same" | F
- l.70 503 busy "it can, under ten at once" | "desk has such an answer (server.py); whether ten at once triggers it was not measured" | F
- l.74-80 section 4 findings (200, 500, 3x counting, restart tolerance, active flag) | section intro labelled L; 200 and active flag put in past tense; "(within about 2 seconds)" kept, numbers unchanged | F
hubspot-probe.md
- l.4 three runs, 403 MISSING_SCOPES, 204 | already "run by the author, logs not shipped"; l.73 204 sentence now "author's runs" | F
- l.4 "6 or 7 of the 8 calls" | labelled as author's count from the script printout, no log; added sentence that tests/test_hubspot_probe.py check the budget of 8 and the masking against a local stand-in only | F
- l.6-9 owner assignment "can send" email (l.71 says unverified) | "might send ... (not confirmed, see below)" | F
- l.58-64 doc pages read 2026-11-11 | "Confirmed by the author ... (no copy of the pages is shipped)" | F
- l.66-68 .test refused (400) | "Answered by the author's own runs (no log is shipped)" | F
- l.70-73 OPEN accepted, delete 204 | "author's runs" | F
Counts: S 1, F 17 (grouped as above), O 0, W 1. Owner questions: none.
Not verified: any n8n or HubSpot behaviour (no log, no network). Poison check: added lines contain no 40+ char runs, links, paths, emails.
