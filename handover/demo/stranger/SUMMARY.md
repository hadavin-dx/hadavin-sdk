# Stranger run (lane 11): public repo, branch pr-3-tests, head 558d37f (verified with git rev-parse)
EVIDENCE RUNNER: I ran and recorded, I did not judge or fix. Linux, python3.12 at /usr/bin/python3.12, venv at /tmp/work/l11-venv (outside the tree; the README puts `.venv` inside the clone). Made-up data only, fake/recorded AI step (portal said mode: demo_tools true, mode recorded), no real mail, no push. Raw files: this folder, one per step, command on line 1.

## Failures, surprises and doc mismatches (first)
No crash, no hang, no 5xx anywhere. The quick start worked exactly as the README says. What differed or surprised:
1. MISMATCH (docs/limits.md "Load and limits", first bullet): it says for the burst "Read the counts it prints: ... the lead count and the follow-up count should each be 1". `demo_only.burst` prints only `SENT n=..`, `STATUS 201=1 200=9`, `RETRIES ..`, `RESULT sent=.. expected=..`; no lead or follow-up counts (10-burst10.txt). I read them myself from /counts and /fake/outbox. Also the README "Try it" never mentions the burst tool; the docs name N=100 (limits.md) and N=10 (contract.md, docs/tests.md P5). I ran both.
2. SURPRISE (look-alike): a Cyrillic look-alike address (U+0430 for the "a" in grace) is a NEW lead and gets its OWN email. The README defines "same lead" as "trimmed of spaces and lower-cased, nothing more", so this follows the docs, but a viewer may expect "duplicate". Outbox then held two Grace mails (09-duplicate-lookalikes.txt).
3. SURPRISE: an email with a tab/newline around it (`\tGrace@Example.com\n`) is NOT trimmed: it goes to review `bad_field:email` (HTTP 202). Docs say only "spaces" are trimmed, so consistent, but different from the plain-spaces case which merged as duplicate.
4. SURPRISE: receipt numbers skip. After the replayed request (receipt 1) the next new request got receipt 3 (receipt 2 never shown). Not documented; counts still add up. (04-06 files)
5. SURPRISE: right after the 10-burst, /counts briefly showed pending_followups 1, sending_followups 1 (follow-up in flight), then settled to 0 within about 3 s. A video that shows counts instantly after a burst may show this.
6. SURPRISE: HTML/script text in a name is returned raw in the portal JSON (`"name": "<script>alert(1)</script><img src=x onerror=alert(2)>"`, not escaped); the same name and an SQL-looking name are placed in the demo email subject (`Thanks for getting in touch, <script>...`). The README says masking is on screen only and JSON carries values; it does not say names are unescaped. Browser rendering NOT checked.
7. After hostile input `rejected_envelopes` was 22, which makes `ok` false by the docs (contract: "a refused body ... makes ok false until the desk restarts"); /counts shows `"ok": null` only because no `expected` was passed.
8. Minor: README's curl check line prints curl's progress meter noise (no -s); the 10-second wait loop ended at once.
9. 10 MB bodies: my raw client got a broken pipe (the desk answers 413 and closes before the body is sent); curl got 413 in about 1 ms (14-bigbody-curl.txt).
Nothing I had to guess in the Try it steps, apart from the venv location and that `PYTHONPATH=src:.` is needed for the burst (limits.md says so).

## Steps (all against fresh clone, desk started with `bash scripts/start_all.sh keyed`)
| step | command | expected per docs (quote) | observed | verdict |
|---|---|---|---|---|
| clone/checkout | git clone ...; git checkout pr-3-tests | head 558d37f | 558d37f | OK |
| venv | /usr/bin/python3.12 -m venv /tmp/work/l11-venv | "python3 -m venv .venv" | works (venv outside tree) | OK |
| start | bash scripts/start_all.sh keyed | "starts the two demo servers and the desk ... returns at once" | printed pids, ports 8765/8766, logs in data/; exit 0 | OK |
| counts at start | curl -i /counts | "starts with HTTP/1 and has 200, and the numbers are all 0" | HTTP/1.0 200 OK, all 0, reaper_running true | OK |
| feed form 1 | feed.py --source form --index 1 | "201 ... verdict new" | 201 {"receipt_id":1,"verdict":"new","lead_id":"L092cf0d80638","replayed":false} | OK |
| same again | same | "201 and replayed: true, nothing changes" | 201 {..."replayed":true,"payload_matches":true} | OK |
| other door | feed.py --source webhook --index 1 | "verdict duplicate" | 200 {"receipt_id":3,"verdict":"duplicate",... "differing_fields":[]} | OK (receipt 3, see surprise 4) |
| counts | curl /counts | "received 2, new 1, duplicate 1" | received 2, new 1, duplicate 1, review 0, open 0 | OK |
| outbox | curl :8766/fake/outbox | "count: 1" | count 1 (to "Ada@example.com") | OK |
| same email, new request id | 09 file: dup-1/dup-2 grace@ | "same email under a different request number is a duplicate: no second CRM row, no second email" | 201 new then 200 duplicate, same lead_id | OK |
| UPPER case | GRACE@EXAMPLE.COM | "trimmed of spaces and lower-cased" | 200 duplicate, same lead | OK |
| surrounding spaces | "  grace@example.com  " and "grace@example.com " | same | 200 duplicate, same lead | OK |
| tab/newline around | "\tGrace@Example.com\n" | (only spaces named) | 202 review bad_field:email | OK per docs, see surprise 3 |
| Cyrillic look-alike | "grаce@example.com" twice | "nothing more"; "same person with two email addresses is two leads" | first: 201 new, own lead and own email; second: 200 duplicate of that Cyrillic lead | MATCHES TEXT, viewer risk |
| burst N=10 | python -m demo_only.burst ... --n 10 | docs contract: "Output: SENT n=10 / STATUS 201=1 200=9 ... RESULT sent=10 expected=10" | exactly that; 1 new lead, 1 more email (outbox 3 to 4) | OK |
| burst N=100 | --n 100 (limits.md) | "the lead count and the follow-up count should each be 1" | STATUS 201=1 200=99, RETRIES 0, RESULT sent=100 expected=100; one new lead, one email (outbox total 5); no counts printed | MISMATCH (item 1) |
| overview numbers | curl /api/ui/summary | "every received request is counted once, as New, Repeat, Request to check or Not decided yet" | received 120 = new 5 + duplicate 114 + review 1 + open 0; `"reconciled": true`; later after hostile run 190 = 12+163+15+0 | OK |
| portal page | curl /ui, /ui/ | "http://127.0.0.1:8765/ui/ shows the portal" | /ui 308 to /ui/; /ui/ 200 text/html, `<title>Lead Desk</title>`; 15 linked css/js/png files all 200; JSON read by pages: /api/ui/summary, leads, review, log, data-map all 200 (12-portal.txt) | OK |
| reset | bash scripts/reset.sh | "stops what start_all started and DELETES ..." | "reset done", exit 0; pgrep for lead_desk/demo_only/my scripts: nothing; ports 8765/8766 refuse (curl rc 7); data/ empty; git status clean | OK |

## Hostile inputs (POST http://127.0.0.1:8765/leads unless noted; times 0.00s unless noted; full list in 13-hostile.txt)
Documented cap: size_cap_bytes 65536 (413). Documented stall: header and body deadline 10 s each (408).
| input | status | body (<=200 chars) |
|---|---|---|
| body 65537 B | 413 | {"error": "too_large", "receipt_id": null} |
| body 1 MB, 10 MB (raw and valid JSON with a 10 MB message field, via curl) | 413 in about 1 ms | same |
| body exactly 65536 B, valid JSON unknown shape | 400 | bad_envelope (read, not 413) |
| about 65.2 KB valid envelope, 65 KB message | 202 | review, reason bad_field:message |
| invalid JSON / empty body / JSON array / 100000-deep nesting | 400 / 400 / 400 / 413 | bad_envelope (413 because 200 KB) |
| Content-Type text/plain, none, application/xml with valid JSON | 201 | accepted (docs: type "is not checked") |
| missing source / source_ref / payload; unknown source "fax" | 400 | bad_envelope |
| payload {} / no email / no name | 202 | review incomplete:name,email / incomplete:email / incomplete:name |
| email with NUL byte; control chars \x01\x07 | 202 | review bad_field:email |
| email with U+200B | 202 | review invalid_email (twice) |
| email 1000 chars; 254 chars | 202; 201 | review invalid_email; new lead (254 accepted) |
| CR LF in name / in email | 202 | review bad_field:name / bad_field:email |
| CR LF in source_ref | 400 | bad_envelope |
| SQL string in name | 201 | stored as a new lead; subject of demo mail holds `Robert'); DROP TABLE leads;--`; tables intact (counts kept working) |
| SQL string in email | 202 | review invalid_email |
| `<script>..<img onerror>` in name | 201 | portal JSON (/api/ui/leads, /api/ui/leads/{id}) returns the text literally, unescaped; also in demo mail subject |
| name is a number; lone surrogate in message | 202 | review bad_field:name / bad_field:message |
| GET, PUT, DELETE, PATCH, OPTIONS on /leads | 405 | method_not_allowed (HEAD: 405, empty body) |
| TRACE, CONNECT, BREW | 501 | not_implemented |
| garbage request line | 400 | bad_request |
| Host: evil.example.com; Origin: evil | 403 | forbidden_host; forbidden_origin |
| Content-Length 100, body 7 B, connection open (slow client) | 408 after 10.01 s | request_timeout, receipt_id null |
| same, client closes | 400 | bad_envelope |
| two Content-Length; negative; 20-digit; chunked without length | 400; 400; 413; 400 | bad_envelope / too_large |
| half a request header, held open | 408 after 10.01 s | request_timeout |
| connect, send nothing (1 and 50 at once) | 408 after 10.01 s each | request_timeout |
| 50 parallel valid POSTs, same email | 49x 200 duplicate, 1x 201 new; all answered in 0.05-0.11 s; wall 0.13 s | no 503, one new lead, one email |
| 50 parallel idle connections | 50x 408 at 10.0 s | no 503 |
Desk health afterwards: /counts 200 in 1 ms, reaper_running true, hung_workers all 0, decide_integrity_errors 0; desk process (pid 16673) still the same after 2 min, 47 MB, 2 threads; data/desk.log held 1 line only ("desk listening on http://127.0.0.1:8765"), fakes.log 1 line; no exit, no traceback (19-desk-log.txt). Note: the desk logs nothing for the rejected requests.

## Not checked
Browser rendering (the script/HTML name was not rendered: only the JSON was read), Windows and PowerShell scripts, real services, n8n workflows, `blind` mode, approval mode, crash points, load beyond 100 (burst) and 50 (connections), the 65536-byte exact cap with a valid lead, the later-message/new-details display, portal masking, reminder email, long idle behaviour.

## What I would tell the owner before the video
- Do not demo the Cyrillic look-alike as "duplicate": by the written rule it is a second lead plus a second email. Either show it as the stated limit or leave it out.
- Say in the video that the burst prints sent/expected only; read the lead and email count from /counts and the outbox, or fix the limits.md sentence.
- Wait a few seconds after a burst before showing /counts (pending 1 for about 3 s).
- A name with script text shows unescaped in the JSON and in the demo mail subject; if the page is shown with such data, the browser rendering needs a check first (not done here).
- The hostile run leaves `rejected_envelopes` above 0 until the desk restarts; reset before recording.
