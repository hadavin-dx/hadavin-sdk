# Kill test: one n8n flow vs the desk's own design, three kill points

Written by the demo cloud session. Everything below is "in my runs": n8n 2.46.6 (regular mode, not queue mode), Node 24, Docker Postgres 16, one Linux machine, loopback only, made-up data, small stand-in programs for the CRM (customer-record system) and the mail system. No independent rerun exists yet, so nothing here goes into the post draft (owner rule of 2026-11-12: a number is published only after an independent rerun reproduces it).

## How the kills differ (read this before the table)

- **Desk:** the desk ends itself. A flag file names a code point and the desk's test hook calls an immediate exit (exit code 137) exactly there. Each of its kills ran on a freshly started stack (new database, new desk, new stand-ins), then the desk was restarted and the same request sent again, then 12 seconds of waiting for its background job.
- **n8n:** n8n is killed from outside, 1.5 seconds after the call, as a whole process group (the end is confirmed). The tested flow has a 4 second Wait that I put in so the kill lands between steps. The 5 kills of the n8n-only series and the 10 kills of point 1 each ran one after another on ONE stack (counts are per lead id), not on a fresh stack each. After the restart I waited 7 to 10 seconds.
- So the two sides are not like for like: a self-exit at a named code point against a timed outside kill, and different flows. The table lines them up by "where in the story the process stops", nothing more.
- **Sample size:** 5 kills per point. These are counts, not rates.

## Terms used

- **Lead id**: the id of one incoming lead. **Receipt**: the desk's first write, made before any work, so it can resend later. **Point A**: receipt written, no verdict yet. **C0**: the first answer is sent, the follow-up work (CRM write, e-mail) has not started. **D2**: the e-mail has been sent, the desk ends before it records that. **D1b**: the desk ends just before the e-mail is sent. **Keyed mail system**: a stand-in that drops a repeat send with the same key (a simulation). **Blind mail system**: a stand-in that cannot say whether a send happened. **UNKNOWN**: the desk's follow-up state meaning "may or may not have been sent", listed for a person and not resent by the desk. **201 replayed**: the desk's answer to a repeated request: it already has this lead. **Variant e**: an earlier test of an n8n flow with a status column and a re-send job (see `n8n-owns-vs-desk-owns.md`). **P1a**: n8n inserts first, waits, then calls the desk. **P1b**: n8n waits, then calls the desk, no n8n insert. **Lost** (below): the lead record or CRM row exists nowhere and nothing will do the work, or the work is never done for a recorded lead. More terms in the glossary of `n8n-owns-vs-desk-owns.md`.

## Plain result (in these runs only)

- **The one n8n flow I tested LOST the lead** when n8n was killed after its own insert and before the work: 5 of 5 kills. The flow was: webhook, Postgres insert that skips repeats, 4 s Wait, then the work, no status column, n8n's default settings. Same with the desk behind it and n8n inserting first (P1a): 5 of 5, the desk never contacted. Cause in these runs: the inserted row survives, n8n marks the run "crashed" after the restart and does not run it again, and the repeated request is answered "duplicate". This says nothing about flows with a status column or a re-send job, or about other n8n settings or versions; those were not killed at this point.
- **The desk kept the lead record and did the work once in 25 of 25 kills** (A, C0, D2 keyed; D2, D1b blind). Not a clean sweep: at D1b on a blind mail system 0 e-mails had gone out and the follow-up sits UNKNOWN until a person acts (5 of 5); at D2 blind the e-mail went out once and the follow-up is UNKNOWN (5 of 5). On the keyed mail system the desk at D2 and C0 resent with the same key (follow-up attempts 2) and the single e-mail is the stand-in dropping the repeat; a real mail system may not do that.
- **The caller has to send again** at point A (first call lost its connection 5 of 5, the repeat got 201 replayed) and in P1b (nothing recorded before the restart; the repeat created the lead, so P1b is the caller's resend, not a desk recovery). If nothing sends again, no flow in this test brings that lead back.

## The three points and how each was covered

| Where the story stops | n8n side | Desk (own design) | Covered by |
|---|---|---|---|
| 1. after the first insert, before the desk has the request | n8n-only flow (insert, Wait, work): LOST 5 of 5. P1a (n8n insert then desk): LOST 5 of 5. P1b (n8n forwards to the desk, no n8n insert): 0 of 5 lost, with the caller sending again | not reached | NEW: `skipd.py` (10 kills), `n8n-kill-between-steps.md` (5 kills) |
| 2. after the desk receipt, before the work | no receipt step in n8n; nearest is variant e, an earlier test that killed at the two e-mail points (e-mail resent in every kill run; second CRM row in 1 of 50), not this point | A (receipt, no verdict): 5 of 5 one lead, one CRM row, one e-mail. C0 (answer sent, work not started): 5 of 5, 0 e-mails before the restart, 1 after | NEW real kills; the published desk tests simulate these points with an exception |
| 3. after the first answer, during the follow-up work (the desk's work runs after its reply) | NOT tested for n8n alone (my n8n kill was before the work, in the Wait) | D2 keyed 5 of 5 one e-mail, sent. D2 blind 5 of 5 one e-mail, UNKNOWN. D1b blind (just before the e-mail) 5 of 5 zero e-mails, UNKNOWN | D2 was also covered by the repo's own real-kill tests and my earlier runs (keyed 3, blind 1); only the 5-each rows are counted below |

## Raw counts (every kill, per lead)

| Series | Stack | Kills | First call | Repeat call | Desk leads | Receipts | CRM rows | E-mails | Follow-up state | Lost | Work done twice |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n8n-only flow, kill in the Wait | one stack, in a row | 5 | dropped 5 | "duplicate" 5 | n/a | n/a | n/a | 0 (stand-in outbox calls 0) | n/a | 5 of 5 | 0 (work never done) |
| n8n P1a | one stack, in a row | 5 | dropped 5 | "duplicate" 5 | 0 | 0 | 0 | 0 | n/a | 5 of 5 | 0 |
| n8n P1b (no n8n insert) | one stack, in a row | 5 | dropped 5 | new 5 | 1 each | 1 each | 1 each | 1 each | n/a | 0 of 5 | 0 |
| Desk A (keyed) | fresh each | 5 | dropped 5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | sent | 0 of 5 | 0 |
| Desk C0 (keyed) | fresh each | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each (0 before the restart) | sent 5 (attempts 2) | 0 of 5 | 0 |
| Desk D2 (keyed) | fresh each | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | sent 5 (attempts 2) | 0 of 5 | 0 |
| Desk D2 (blind) | fresh each | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | UNKNOWN 5 | 0 of 5 | 0 |
| Desk D1b (blind) | fresh each | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 0 | UNKNOWN 5 (e-mail waits for a person) | 0 of 5 | 0 |

"n/a" = that part was not in the flow. Raw files: `n8n-kill-between-steps.md`, `n8n-rerun/desk-p1/`, `n8n-rerun/desk-kill/` (per-kill table, series summary, scripts as .txt).

## What went wrong in my own run (kept visible)

My first D2 and D1b "blind" series ran against a mail server still in keyed mode (a stale server; a new one could not bind its port while the old connections were closing). Those files are kept, renamed NOTBLIND, and not used. The driver now waits for both ports and requires the server mode to equal the series and its counters to be empty. The rows above are the reruns on fresh servers.

## Not claimed

Exactly-once delivery; "n8n alone is enough" or "n8n is broken" (one flow, one kill point, one version, default recovery settings); real CRM, mail or AI; queue mode; n8n's own crash-recovery settings; an n8n-only kill after the work (untested); the n8n status-plus-re-send shape at this kill point (untested); the cause of the n8n variant a duplicates. Repo text says an UNKNOWN follow-up is for a person to decide and that wrongly marking it "not sent" can cause a second e-mail on a blind mail system (`docs/limits.md`; not tested here).
