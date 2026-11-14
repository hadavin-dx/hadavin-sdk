# Published numbers to compare (author's own earlier run, laptop, NOT independently reproduced)
Source: the branch README table (n8n-evidence-rerun) and the lead's LinkedIn draft 003. Compare, do not tune.
- variant a, ten at once: 18 of 20 at one CRM row and one email (builder's overloaded-laptop rerun showed 10 of 20, so this is the number to settle)
- K1 (crash after step 1): crashed entry visible 1 of 5 (builder rerun matched differently)
- kill runs with no effect: 1 of 15
- variant e: second CRM row appeared in 4 of 10 (builder rerun 1 of 10)
Everything else: read from the branch README tables and report your own counts next to them.

## PUBLISHABLE-NUMBERS table (written 07:08Z; lead's order of 07:00Z)
Rule applied: a number is listed as reproduced only if a rerun on this quiet cloud machine gave the same count, with the stack condition. "Reused stack" = one stack (one n8n, one Postgres) served all bursts or rows of the run in order (R2, R2b series). "Fresh stack" = a new work folder, new Postgres and new n8n for each unit (R2c, R2d). Rerun sources are in `N8N-RERUN-1.md`; raw rows are in `n8n-rerun/`. Our reruns carry two labelled scratch patches (P1: wait for the webhook before the restart; P2: a digit in the owner password); they are not in the published harness. No significance level is claimed anywhere; intervals in the branch tables treat dependent runs as independent.

| published line | published | our rerun | status | stack condition |
|---|---|---|---|---|
| variant a, ten at once, one CRM row and one email | 18 of 20 | reused stack: R2 12 of 20, R2b 2 of 5; fresh stack, 1st burst: 12 of 12 clean (R2c 5 slots, R2 and R2b first burst, R2d burst 1 on 5 stacks); fresh stack, 2nd and 3rd bursts (R2d): 8 of 10 clean | NOT REPRODUCED on a reused stack (12 of 20 and 2 of 5 against 18 of 20). On a fresh stack the first burst is clean 12 of 12, which is not the same measurement as 20 bursts on one stack | say which: "18 of 20 on one long-running stack (author's run); we saw 12 of 20 on one reused stack and 12 of 12 on a fresh stack's first burst" |
| variant a, duplicates equal the replies of 200 | published rows: (3,3) and (8,8) with 200 x3 and 200 x8 | every one of 45 own bursts and 20 published bursts: CRM rows = number of 200 replies | REPRODUCED (pattern, reused and fresh stacks) | both |
| variant b, ten at once | 20 of 20 | R2 20 of 20 (21 attempts, 1 invalid: no overlap) | REPRODUCED | reused stack |
| variant c, ten at once | 20 of 20 | R2 20 of 20 | REPRODUCED | reused stack |
| variant d, ten at once | 20 of 20 (d cannot race) | R2 20 of 20 | REPRODUCED | reused stack |
| replay added posts, a to d | 0 of 20 each | R2 0 of 20 each; variant a in R2b, R2c, R2d: replay added 0 in every burst | REPRODUCED | reused stack (R2), fresh stack (R2c, R2d for a) |
| kill rows where no client lost its connection, a, b, c, d | 0 of 15 each (README) | R2 a 0 of 15, b 0 of 13 valid (2 invalid), c 0 of 15, d 0 of 15 | REPRODUCED (b: 13 valid rows, not 15; R3-partial added 2 b rows on a fresh stack, see N8N-RERUN-1.md) | reused stack |
| a kill, CRM request in flight: 1 CRM row, 0 emails after one retry | 5 of 5 | R2 1 of 5 | NOT REPRODUCED (1 of 5 against 5 of 5) | reused stack |
| a kill, the two email points: 1 CRM row and 1 email | 9 of 10 | R2 3 of 10 | NOT REPRODUCED (3 of 10 against 9 of 10) | reused stack |
| b kill, CRM in flight / two email points | 5 of 5 / 10 of 10 | R2 4 of 4 / 9 of 9 valid rows (+ R3-partial rows) | REPRODUCED for the valid rows; the invalid rows (stale running after kill) are listed in `N8N-RERUN-1.md` | reused stack (R2), fresh stack (R3-partial) |
| c kill and d kill, in flight / two email points | 5 of 5 / 10 of 10 each | R2 5 of 5 / 10 of 10 each | REPRODUCED | reused stack |
| crashed entry visible, kill points of variants a to d | 5 of 5 (table rows) | R2 5 of 5 (b K2 and K3: 4 of 4) | REPRODUCED | reused stack |
| variant e, ten at once | (1,1) x5 | R2b 5 of 5; R2c 25 of 25, each (1,1), status sent | REPRODUCED | reused stack (R2b), fresh stack (R2c) |
| variant e, two or more emails at the two email points | 10 of 10 | R2 10 of 10; R2b 50 of 50 | REPRODUCED | reused stack (R2), fresh stacks (R2b units) |
| variant e, second CRM row at the two email points | 4 of 10 | R2 1 of 10 (reused stack); R2b 1 of 50 (5 fresh stacks, one of 10 rows each: 0, 0, 1, 0, 0) | NOT REPRODUCED (1 of 10 and 1 of 50 against 4 of 10) | both |
| variant e, status not sent at 60 s | 0 of 15 | R2 0 of 15; R2b 0 of 50 (status sent 50 of 50) | REPRODUCED | both |
| "K1 (crash after step 1): crashed entry visible 1 of 5" (lead's list) | not in the branch tables | none | NO MATCHING ROW | - |
| "kill runs with no effect: 1 of 15" (lead's list) | not in the branch tables (README says 0 of 15; DETAILS.md names one b kill in a busy-machine development test) | R2 0 of 15 | NO MATCHING ROW | - |

Which number may be used in a post, and how: only the REPRODUCED rows, each with its stack condition; for variant a no single headline figure fits both: the 18 of 20 comes from one long-running stack and our reused-stack reruns gave 12 of 20 and 2 of 5, while a fresh stack's first burst was clean 12 of 12. Every NOT REPRODUCED and NO MATCHING ROW line should come out of the README table and the post unless the original run's raw files turn up (open question for the lead to ask the owner).

NOT CHECKED here: the lead's draft 003 (not available to me); whether the original run's stack was fresh when its first burst ran.
