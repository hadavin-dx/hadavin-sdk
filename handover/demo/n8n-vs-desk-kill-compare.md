# Kill test: n8n alone vs the desk's own design, three kill points

Written by the demo cloud session. Everything below is "in my runs": n8n 2.46.6 (regular mode, not queue mode), Node 24, Docker Postgres 16, one Linux machine, loopback only, made-up data, small stand-in programs for CRM and mail. A "kill" is a real process end (the desk exits with code 137; n8n is killed as a whole process group and its end is confirmed). Each point has 5 kills, each on a freshly started stack. Counts are per lead id. No independent rerun exists yet, so nothing here goes into the post draft (owner rule, 2026-11-12).

## Plain result

- **n8n alone LOSES a lead** when it is killed after its own database insert and before the work (5 of 5), and the same happens when n8n is the front door and the desk has not got the request yet (point 1, flow P1a, 5 of 5). Cause in these runs: the insert row survives, the run is marked "crashed" and is not run again, and the repeat request is answered "duplicate".
- **The desk lost no lead and did the work twice 0 times** at the points A, C0, D2 (keyed mail stand-in) and D2, D1b (blind mail stand-in): 25 of 25 kills. At D2 and D1b on a blind mail system the follow-up is marked UNKNOWN for a person (not resent by the desk); this is the designed behaviour in the repo text, not a clean finish.
- **The desk needs the caller to send again** at point 1 and at point A (the first call lost its connection in 5 of 5; the repeat got 201 "replayed"). If nothing ever sends again, no system in this test brings the lead back.

## The three kill points and how each was covered

| Point | n8n alone / n8n first | Desk (own design) | Covered by |
|---|---|---|---|
| 1. after the n8n insert, before the desk receipt | P1a (n8n insert first): LOST 5 of 5 (n8n row 1, desk 0 leads, 0 receipts, 0 work; repeat answered "duplicate"). P1b (desk first, no n8n insert): lost 0 of 5, 1 lead, 1 CRM row, 1 e-mail after the caller sent it again | not reached (the desk has seen nothing yet) | NEW: my driver `skipd.py`, 10 kills |
| 2. after the desk receipt, before the work | n8n has no receipt step; the nearest n8n shape is variant e (status column plus re-send job), a separate earlier test, e-mail re-sent in every kill run | A: receipt written, no verdict: 5 of 5 first call dropped, repeat got 201 replayed, 1 lead, 1 CRM row, 1 e-mail. C0 (keyed): 5 of 5 killed after the receipt and the reply, before the work; after restart 1 lead, 1 CRM row, 1 e-mail (0 e-mails before the restart) | NEW for A and C0 (desk crash points, real kills); the published tests simulate these points by an exception |
| 3. after the work, before the reply | n8n alone, flow with insert then work then reply: NOT tested at this point (my kill was before the work, inside a 4 s Wait) | D2 (after the e-mail was sent): keyed 5 of 5 one e-mail, follow-up sent; blind 5 of 5 one e-mail, follow-up UNKNOWN. D1b (before the e-mail): blind 5 of 5, 0 e-mails, UNKNOWN | D2 also covered by the repo's own real-kill tests and my earlier runs (keyed 3, blind 1); the 5-each rows are new |

## Raw counts (every kill, per lead)

| Series | Kills | Real end (exit 137) | First call | Repeat call | Desk leads | Receipts | CRM rows | E-mails | Follow-up state | Lost | Work twice |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n8n alone, kill in the Wait after the insert | 5 | n8n process group | dropped 5 | "duplicate" 5 | n/a | n/a | n/a | 0 (outbox calls 0) | n/a | 5 of 5 | 0 |
| n8n P1a (insert first, then desk) | 5 | n8n | dropped 5 | "duplicate" 5 | 0 | 0 | 0 | 0 | n/a | 5 of 5 | 0 |
| n8n P1b (desk first) | 5 | n8n | dropped 5 | new 5 | 1 each | 1 each | 1 each | 1 each | n/a | 0 of 5 | 0 |
| Desk A (keyed) | 5 | 5 | dropped 5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | sent | 0 of 5 | 0 |
| Desk C0 (keyed) | 5 | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each (0 before the restart) | sent 5 | 0 of 5 | 0 |
| Desk D2 (keyed) | 5 | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | sent 5 | 0 of 5 | 0 |
| Desk D2 (blind) | 5 | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 1 each | UNKNOWN 5 | 0 of 5 | 0 |
| Desk D1b (blind) | 5 | 5 | 201 x5 | 201 replayed 5 | 1 each | 1 each | 1 each | 0 | UNKNOWN 5 | 0 of 5 | 0 |

For the n8n rows, "n/a" = that system was not part of the flow. Raw files: `n8n-kill-between-steps.md`, `n8n-rerun/desk-p1/` (point 1), `n8n-rerun/desk-kill/` (desk, with a per-kill table and my scripts as .txt).

## What went wrong in my own run (kept visible)

My first D2 and D1b "blind" series ran against a mail server that was still in keyed mode (a stale server; the new one could not bind its port while the old connections were closing). Those files are kept, renamed NOTBLIND, and were not used. The driver now waits for both ports and requires the server mode to equal the series and its counters to be empty. The blind rows above are the rerun. My first keyed C0 and D2 series had counters that ran on across kills (per-kill change was exactly +1); the rows above are the fresh rerun.

## Not claimed

Exactly-once delivery; "n8n alone is enough" or "n8n is broken" (one flow, one kill point, one version); real CRM, mail or AI; queue mode; n8n's own crash-recovery settings; a kill after the work on the n8n side (point 3 for n8n alone is untested); the cause of the n8n variant a duplicates. The desk repo text says an UNKNOWN follow-up is for a person to decide; a person marking it "not sent" wrongly can cause a second e-mail on a blind system (`docs/limits.md`, repo text, not tested here). Not independently rerun.
