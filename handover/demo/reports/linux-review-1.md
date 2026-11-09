# linux-review-1 (ORDER 199) - read-only adversarial review, round 1
Reviewer: egm:egm-codebase-details (sonnet), tree /tmp/dpld (dpld-fix1-aed689a). Saved by the cloud session. The reviewer had Read/Grep/Glob only: it RAN NOTHING, every finding is from reading code and is UNRUN until the confirmation section at the end says otherwise. Not read by it: config.py, contract.py, hooks.py, loader.py, fakes_server.py, tests/, scripts/. Counts: 1 Blocker, 6 Major, 8 Nit.

## Findings (summary; full detail below the table is the reviewer's text, shortened only in layout)
| id | sev | one line | where |
|---|---|---|---|
| F1 | Blocker | name starting with NUL passes Python check, fails SQL CHECK length(): 500, receipt open forever; same for source_ref "\u0000x" (500, receipt null) | identity.py:76-79, schema.sql:33 and :7, desk.py:249-254 |
| F2 | Major | reply write fails (client reset) after commit: run_followup never called; follow-up stays pending until restart/replay/Retry | server.py:151,164,242 |
| F3 | Major | (a) 503 in transaction 2 leaves receipt open, no runtime repair; (b) follow-up stuck in 'sending' (swallowed busy, non-busy OperationalError, kill) repaired only at restart; retry() can return 200 state=sending | desk.py:217,313,496-499,544 |
| F4 | Major | outbox mode mismatch after a 2xx reply is recorded 'failed' (retryable) though the mail is stored: Retry sends a second email on blind outbox | adapters.py:94-95, desk.py:445-446 |
| F5 | Major | PRAGMA journal_mode=WAL result never checked; silent rollback-journal mode gives busy storms | db.py:44 |
| F6 | Major | outbox outage: every lead ends 'failed' after one try, nothing retries automatically | desk.py:447-450,199-202 |
| F7 | Major (conditional) | with --crm blind a second CRM row is possible on Retry / concurrent drive / sweep | desk.py:375,386-392,538 |
| F8 | Nit-Major | 500 instead of 400/404/413: Content-Length of 4301+ digits, request target "http://[/", item id with 20+ digits | server.py:136,142, desk.py:515 |
| F9 | Major (load) | 100+ threads: one connection+thread per request, ~5 serial write transactions, fsync FULL, 5 s busy wait; 503s with open receipts, pending/sending rows left behind; EMFILE/listen-queue 64 edges | server.py:49, db.py:17-20, desk.py:128-133 |
| F10 | Nit/Major | /counts ok ignores pending/failed/unknown/sending follow-ups; rejected counter in memory only | desk.py:623,124 |
| F11 | Nit | o'brien@example.test refused as invalid_email | identity.py:12 |
| F12 | Nit | replay with same request id and different payload discards new data silently | desk.py:324-331 |
| F13 | Nit | start-up sweep blocks serving (100 pending + slow fakes = minutes) | desk.py:199-202, server.py:324 |
| F14 | Nit | lockfile: any OSError reported as "another desk is using this database"; lock name from unresolved path (symlink gives a second desk); deleted lock file | lockfile.py:17, server.py:309-312 |
| F15 | Nit | startup() has no guard against being called with live handlers | desk.py:177-202 |

Vectors checked with nothing found (reviewer's words): second lead per email closed by unique index + BEGIN IMMEDIATE; claim UPDATE is compare-and-set; no committed 'new' lead without follow-up row; flock released by kernel on kill -9; allow_reuse_address on Linux correct; WAL + synchronous=FULL rolls back uncommitted frames; hook A2 sits inside the transaction. Reviewer note: pytest tmp_path may be tmpfs where fsync is a no-op, so durability claims need a real-disk directory.

## Detail (reviewer, per finding: trigger, expected vs actual, fix at choke point, test)
F1 trigger: POST /leads {"source":"form","source_ref":"r1","payload":{"name":"\u0000Ada","email":"a@example.test"}}. SQLite length() counts text only up to the first NUL; Python strip() keeps NUL; stored payload is escaped, json.loads turns it back into NUL in _decide (desk.py:224). Expected verdict review/202 (P3). Actual sqlite3.IntegrityError -> 500 {"error":"internal","receipt_id":n}; receipt outcome NULL; replay fails the same way; start-up sweep logs "receipt left open" at every restart; review list shows an "O" item whose hint cannot work. Fix: reject Cc/Cs/Cn code points in check_payload for name/phone/company/message and NUL in source_ref (envelope check); safety net: non-busy ValueError/IntegrityError in _decide writes outcome='review' reason 'internal_unstorable'. Tests: fuzz over the full code-point range (never 500, no open receipt) plus the two literal inputs; prove they fail on old code.
F2 interleaving: client sends POST then RST (SO_LINGER 0) before the reply; process() commits transaction 2; _send_reply raises; assignment `follow = ...` never completes, run_followup never called. Fix: take drive_lead_id before writing the reply and run the follow-up in finally, or a background sweeper of 'pending' rows older than N s. Test: raw socket + SO_LINGER(1,0) close; assert outbox count 1 within seconds.
F3 fix: bounded runtime reaper for 'sending' rows older than send_timeout + 3 x busy wait and open receipts older than stall_seconds; use _locked_retry for transactions 1 and 2. Tests: external BEGIN IMMEDIATE held 20 s; fault-injecting connection raising "disk I/O error" at the record step.
F4 trigger: fakes restarted in the other mode while the desk runs (capability cached at construction, adapters.py:61-75). Fix: treat OutboxModeMismatch as ambiguous -> 'unknown'; re-read /fake/info at each start-up sweep. Test: keyed -> restart fakes blind -> post lead -> Retry; assert 1 email, state unknown.
F5 fix: read the pragma return row, raise unless 'wal', check at each connect.
F6 fix: bounded automatic retry with backoff for the two nothing-was-sent errors; 'failed' only after the cap (R368 backpressure/terminal state). Test: refuse outbox for 20 first sends then restore; all 20 end 'sent' without manual call.
F7 fix: refuse to start with a blind CRM, or record crm_done inside the claim transaction. Test: --crm blind, outbox failing once, Retry, CRM count 1.
F8 fix: _content_length returns None on ValueError / over 20 digits; wrap urlsplit; cap item-id digits at 19. Tests: the three literal inputs.
F9 tests: 150 threads distinct emails with slowed fsync (zero open receipts / sending after burst without restart); 150 threads same email (1 lead, 1 email, 1 CRM row); ulimit -n 256 run (no 500, no busy spin).
F10-F15: see table; fixes as stated there (ok requires pending_followups==0 and no failed/unknown; accept apostrophe per RFC 5322; surface payload_matches=false replays; serve before sweep or sweep in background; resolve() lock path and distinguish EWOULDBLOCK; startup guard).

## Gate suggested by reviewer
New tests for F1, F2, F3, F4, F5, F7, F8 must fail on current code and pass on fixed code. F1, F3, F9 are on the no-lost-message path (uncapped rounds).

## Confirmation runs by the cloud session
(see below; added after the load runs finish)
