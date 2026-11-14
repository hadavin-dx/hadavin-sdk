# N8N-RERUN-1 (facts only): independent rerun of the n8n evidence harness on Linux. RESULT: THE RUN DID NOT REACH ANY MEASUREMENT.
Harness: public repo branch n8n-evidence-rerun, commit ad612e2 (one commit on origin main f3c39cf); sums.py check printed ok. Machine: this Linux box (x86-64, 4 cpus, 16 GB, Python 3.13.18; Docker 29.9.2 daemon started by me; Node 24.22.2 from the official download site with its SHA-256 check; n8n 2.46.6 by npm ci from the harness lock, 2219 packages, 2 min; rebuild of isolated-vm rc 0). Raw output in the folder n8n-rerun/ next to this file (paths shortened, links and long ids written in words).

## What ran, in order
1. Harness tests (README step 4, venv with pytest): 173 passed, rc 0.
2. Quiet machine check before the full run: vmstat 120 s, mean idle 92.2 percent, load 0.05. The harness's own idle reading at start: 99.3 percent, at end 99.5.
3. FULL RUN (README step 6, nohup, new empty work folder), started 03:22:39Z. The harness pulled nothing new (image by pinned digest already local), started Postgres, started the fake servers and n8n (up), ran setup.py ok, deployed workflows a, d, c, b (deploy_b printed activated), then stopped itself at 03:24:06Z with exit 1: "n8n did not come up (default): see n8n2.log". Postgres container removed by the harness cleanup; ports 5679 5780 8790 55432 free afterwards; 0 containers.
4. SMOKE RUN (README step 5, run after the failure to see the cause; its own work folder, node_modules shared with the full-run folder by hard links to save 3 GB of disk: a deviation from "its own npm ci"): exit 1 after 85 s: "smoke: n8n readiness or the webhook never answered". smoke_readiness.json: readiness_answered true; webhook_path g2-b2 (variant b); webhook_registered FALSE; 234 probes over about 60 s after readiness, every one HTTP 404 with the n8n text: The requested webhook "GET g2-b2" is not registered (hint: the workflow must be active).
Same result both times (full and smoke): variant b only.

## Facts about the failure
- The other three webhooks (g2-a, g2-d, g2-c2) answer the harness probe in the accepted way (404 with the text "not registered for GET requests", meaning the POST webhook exists). g2-b2 does not: it answers the other 404 text (no webhook of that path at all).
- n8n's own database (smoke work folder, opened read only): table workflow_entity shows all four workflows with active = 1 and an activeVersionId, including wp0b2-g2-b2; table webhook_entity has only THREE rows (g2-a, g2-d, g2-c2, method POST); no row for g2-b2.
- The workflow g2-b2 (file wf2_wp0b2-g2-b2.json) has the nodes Webhook (POST, path g2-b2), PgInsert (Postgres node, credential n8n-publish-pg), RowReturned, CRM, Outbox. The credential exists in the database.
- n8n log of the second start (the one the harness polls): no line mentions activation, the workflow, or g2-b2 other than the 404 answers; the only errors are the n8n.io lookup failures (no outside network for n8n; unrelated) and "Failed to start Python task runner in internal mode" (virtual environment missing; the JS task runner registered).
- Not found: the cause. NOT established whether the webhook of b2 is registered in the FIRST n8n process (before the restart) or whether activation at boot silently skips it; not established whether it is Linux-specific, version-specific (2.46.6 at install time) or Postgres-credential-specific.
- The README says the smoke run is where a problem like this should show up: it did (as expected by the README), and it shows now that the full run cannot be completed on this machine without a harness or setup change that I have NOT made ("compare, do not tune").

## Numbers next to the published ones
None exist: no variant produced a count. Published numbers (from n8n-published-numbers.md) for comparison once a run completes: variant a ten at once 18 of 20; K1 crashed entry visible 1 of 5; kill runs with no effect 1 of 15; variant e second CRM row 4 of 10. All other published counts: the branch README tables. Rerun counts: NONE.

## NOT DONE / NOT CHECKED (my list, for the lead to decide)
- Cause of the unregistered g2-b2 webhook: not found; next: one bounded diagnostic with no harness change (start n8n by hand in the smoke folder with the harness's settings, read webhook_entity right after boot and after a manual activation through n8n's own interface, print the activation error text); default if told: do it, 20 minutes.
- Whether variant b works in the first n8n process (before the restart): not checked; same diagnostic.
- The variants a, c, d, e, ten-at-once, K1 to K3, replay: never ran; they follow only after the restart step that failed.
- Full run needing a different n8n version (for example a newer 2.4x) or a changed harness: not tried (would be tuning; the lead decides).
- The harness's own smoke list of unverified Linux texts (the "live text" wording): the default text matched the three working webhooks, not b2.
- Reviewer (read-only egm) on this file and the branch README: not started; next: start it after the lead reads this.
## WHAT I WOULD DO NEXT (ranked)
1. Run the bounded diagnostic above and write the exact n8n activation error for g2-b2 (facts only, no change to the harness).
2. If the cause is in the harness or the Postgres credential setup (not in n8n): write the one-line change as a proposed patch text for the lead, run it ONLY if told, as a separate labelled run.
3. Then the egm reviewer on N8N-RERUN-1.md plus the README of the branch, and delete the 2.8 GB node_modules after the lead says the result folders are saved.

---
# R2-PATCHED RUN (the lead's order 03:29Z/03:40Z). R1 above stays on record: exit 1, no counts, never replaced.
What R2 is: the same harness commit, run from a scratch copy with ONE change, patch P1 (text diff n8n-rerun/R2-patch-P1.diff, reason in n8n-diag-1.md): before every restart of n8n (and before the smoke kill), wait until the webhooks of the deployed workflows answer in the running process. SHA256SUMS of the harness no longer matches the scratch copy (not recomputed; not needed). No n8n version change; default idle gate 80 percent kept (no min-idle override). node_modules of the work folder are hard links to the first smoke folder's install (disk): a deviation from "its own npm ci". Same machine as R1 (Linux, 4 cpus, 16 GB, n8n 2.46.6, Node 24.22.2, Python 3.13.18).

## Run facts
- Quiet check before: vmstat 5 s x 22, mean idle 91 percent, load 0.11. Harness idle reading at start 100 percent, at end 100 percent (run_manifest). Run folder load file: see R2-tables.md section "Machine load".
- Started 03:47:23Z, ended 04:37:22Z (50 minutes). EXIT CODE 2: "RUN ALL INCOMPLETE": g3 b K2: expected 5 valid kill runs, found 4; g3 b K3: expected 5 valid kill runs, found 4. The harness printed, for b K2 and b K3, "exited with code 4 (kill rows that do not count)". Reason in the summary: stale_running_after_kill x2 (an execution still showed running after the kill and the retry): 1 attempt in b K2 and 1 in b K3. Both attempts are kept and counted as invalid, not hidden. I did NOT run extra attempts (the harness does not).
- The P1 wait passed every time: the program did not stop through its exit line. (The log lines "n8n default up: True" and "n8n limit 1 up: True" are printed after the restarts, not by the wait.) The P1 smoke branch ran twice (smoke3, cut by my own timeout at the K2 step; smoke4, exit 0). Variant e's path is not in the harness's check list; e ran through.
- Raw files: R2-tables.md (the harness's own summarise output, unedited apart from path/long-id masking), R2-full.out.txt, R2-run_manifest.json.txt, R2-exit.txt, in n8n-rerun/.

## Counts next to the published ones (rerun = this run R2; published = the branch's tables.md; the lead's numbers file in the last column). Differences are marked, not explained.
| item | published (tables.md) | R2 rerun | lead's number list |
|---|---|---|---|
| variant a, ten at once, exactly 1 CRM row and 1 email | 18 of 20 | 12 of 20 (attempts 20, invalid 0) | 18 of 20 (builder's overloaded-laptop rerun 10 of 20) -> DIFFERENT |
| variant b, ten at once | 20 of 20 (attempts 20) | 20 of 20 (attempts 21, invalid 1: no overlap) | - |
| variant c, ten at once | 20 of 20 (attempts 75, invalid 55) | 20 of 20 (attempts 20, invalid 0) | - |
| variant d, ten at once | 20 of 20 (attempts 55, invalid 35) | 20 of 20 (attempts 20, invalid 0) | - |
| replay added posts, a to d | 0 of 20 each | 0 of 20 each | - |
| kill rows where no client lost its connection (kill possibly without effect) | a 0 of 15, b 0 of 15, c 0 of 15, d 0 of 15 | a 0 of 15, b 0 of 13 valid, c 0 of 15, d 0 of 15 | 1 of 15 -> that figure is NOT in tables.md as I read it; I report both without a reading |
| a kill runs, CRM request in flight: 1 CRM row and 0 emails after one retry | 5 of 5 | 1 of 5 | -> DIFFERENT |
| a kill runs, the two email points: 1 CRM row and 1 email | 9 of 10 | 3 of 10 | -> DIFFERENT |
| b kill runs, CRM in flight / two email points | 5 of 5 / 10 of 10 | 4 of 4 / 9 of 9 (2 attempts invalid) | - |
| c kill runs | 5 of 5 / 10 of 10 | 5 of 5 / 10 of 10 | - |
| d kill runs | 5 of 5 / 10 of 10 (2 attempts invalid) | 5 of 5 / 10 of 10 | - |
| crashed entry visible (variant a K1, email request in flight) | 5 of 5 | 5 of 5 (table rows, all "yes") | "K1 crashed entry visible 1 of 5" -> that wording is not in tables.md as I read it |
| variant e, ten at once (final 1 CRM, 1 email) | 5 runs, (1,1) x5 | 5 runs, (1,1) x5 | - |
| variant e, second CRM row at the two email points | 4 of 10 | 1 of 10 -> DIFFERENT (equals the builder's overloaded-laptop rerun in the lead's list) | 4 of 10 (builder rerun 1 of 10) |
| variant e, 2 or more emails at the two email points | 10 of 10 | 10 of 10 | - |
| variant e, status not sent at 60 s | 0 of 15 | 0 of 15 | - |
| cross-check with the stand-in's own log | (see tables.md) | 138 runs equal, 0 differ, 2 kill runs left out | - |
Reading note, fact only: variant a ended with more than one CRM row and one email in 8 of 20 ten-at-once runs here (published 2 of 20), and variant a's kill runs ended with a different number of rows than published. The two 95 percent intervals overlap (38.7 to 78.1 here, 69.9 to 97.2 published); this is a difference in counts from two single runs on two machines, not shown to be a difference in behaviour. No reason is given.

## Did P1 touch any published claim?
P1 changes only run_all.py (the wait before a restart of n8n). It does not change g3.py or g3e.py, which hold the trigger code of the kill points K1 to K3 (I read the file names and the diff; I did not read those scripts line by line). It DOES change the state of n8n before the first kill (publication of workflow b finished, webhooks probed). Whether this explains any difference in the kill rows below is NOT known.

## NOT DONE / NOT CHECKED (my list, for the lead to decide)
- The two missing valid kill rows (b K2, b K3): not repeated (harness has no extra attempts; running them by hand is outside the order); next: if told, run b K2 and K3 only, labelled R3-partial.
- Reason for variant a's 12 of 20: not investigated; next (if told): a second quiet full run to see whether 12 repeats, or variant a alone.
- Published "1 of 15" and "K1 crashed entry visible 1 of 5": I could not find them in tables.md; lead to say where they come from.
- Whether the pre-restart wait changes counts: not tested (would need R1-style runs with no wait, which fail).
- Hard-linked node_modules and the scratch copy: disclosed deviations.
- Egm reviewer on this file and the branch README: not started; next: start now.
- CI-equivalent run, non-root skip chunk, v3 doc tests: now allowed (the run ended); not started yet.
## WHAT I WOULD DO NEXT (ranked)
1. Egm read-only reviewer on N8N-RERUN-1.md + the branch README (gaps list).
2. Machine is free now: v3 doc tests, hygiene, CI-equivalent run on main and on the frozen tree + patches.
3. If the lead says so: a second quiet full run (R2b) to see whether variant a's 12 of 20 repeats.

## CORRECTIONS AND ADDITIONS FROM THE READ-ONLY REVIEW (04:45Z; facts, mine to apply, the lead decides on the rest)
- Names: in this file "R1" and "R2" mean RUN 1 (unmodified harness) and RUN 2 (patched); they are not the README's rules R1 and R2. "P1" = the one patch. K1 to K3 for variants a to d: K1 email request in flight (CRM already stored), K2 email stored with its reply held, K3 CRM request in flight; for variant e the letters name other moments (see R2-tables.md). "The lead" = the person who ordered this rerun; "the author of the published run" = whoever made the published numbers; the column "lead's number list" is their note of what to compare and is not part of any public text.
- Cross-check row: published = 140 runs equal, 0 differ (tables.md); run 2 = 138 equal, 0 differ, 2 kill runs left out.
- Kill rows differ in more than counts (facts from R2-tables.md versus tables.md): published rows mostly show one crashed entry after the restart with one retry press; run 2 rows for variants a and b mostly show ten crashed entries with ten retry presses; variant a K1 final (CRM, email) were (2,1) and (4,3) in two rows, K2 (4,3) in two rows, with (1,1) published; variant e client replies read RemoteDisconnected here and ConnectionResetError in the published file. I give no reason.
- Quiet check per test configuration (summarise --busy on run 2): every one of 21 configurations "not busy" (means 90.7 to 99.3 percent); lowest single readings: e kill K1 47.9, e kill K2 66.3, e kill K3 67.6, a kill K2 70.7, b kill K3 74.6, b ten-at-once 81.4. The one invalid ten-at-once attempt of b ("no overlap") ran when the reading was 81.4 percent; that it is related is NOT known.
- b K2 run 4 and b K3 run 5 are the two excluded attempts (stale_running_after_kill: an execution still showed running after the kill and the retry). README says exit code 2 is "incomplete, not a reproduction as a whole": so run 2 is not a complete reproduction.
- Only ONE patched full run exists: variant a's 12 of 20 may be run-to-run spread; no claim about variant a before a second run (R2b, not run).
- README of the branch says it was never run on Linux and gives 1.5 to 2 hours; run 2 took 50 minutes after the patch; run 1 (unmodified) fails at the first restart. A reader following the README on Linux meets run 1's failure unless P1 (or the equivalent) is applied: this is for the lead (README text or harness change), not applied by me.
- Hard-linked node_modules: install checksums not compared. Machine facts not recorded: Postgres image version, CPU model.
- Who ran: an AI agent session (Claude), on the lead's order; scratch-copy hashes not recorded.

## R2b: VARIANCE RUNS ON THE QUIET MACHINE (written 05:57Z; lead's order of 04:44Z)
**What was run.** Same machine, same scratch harness copy with P1, same flags as R2 (default idle gate 80%), nothing else running (agent H stopped before start; no tests, no hygiene run). The harness cannot start one case alone: `g12.py` takes a count, `g12e.py` is fixed at 5 bursts, `g3e.py` takes a kill point and a count, and all need Postgres, the stand-in, n8n, setup and deploys first. So I used three scratch drivers (copies of `run_all.py` with the body cut; the files are in `n8n-rerun/R2b-driver-*.py.txt`). This is the smallest unit the harness allows, said plainly. The versions are the same as R2: n8n 2.46.6, Node 24.22.2, Python 3.13.18, Linux, 4 cpus.

**Variant a, ten at once, 5 bursts in ONE stack (04:47:51 to 04:48:37Z; file `R2b-a-5bursts.jsonl.txt`).** Five raw rows, not averaged. "Duplicates" = rows beyond the one CRM row and one email that a single lead should end with.

| burst | client replies | final CRM / email | duplicates |
|---|---|---|---|
| 1 | 200 x1, 500 x9 | 1 / 1 | 0 |
| 2 | 200 x2, 500 x8 | 2 / 2 | 1 CRM row and 1 email extra |
| 3 | 200 x10 | 10 / 10 | 9 CRM rows and 9 emails extra |
| 4 | 200 x1, 500 x9 | 1 / 1 | 0 |
| 5 | 200 x2, 500 x8 | 2 / 2 | 1 CRM row and 1 email extra |

Plain sentence: 3 of 5 bursts ended with duplicates (1, 9, 1 extra pair), 2 of 5 with exactly one CRM row and one email. In all five the replay of the same ten added no rows. R2 had 12 of 20 exactly right, published 18 of 20. Load: CPU idle 97.3 to 99.8 percent in the 3 samples of the variant a step (the file `R2b-a-load.jsonl.txt` also holds 7 samples of the later variant e ten-at-once step, lowest 95.3).

**Variant e, WRONG UNIT first (my mistake, kept).** I first ran `g12e.py` (ten at once for variant e, 5 bursts, 04:48:40 to 04:51:40Z): 5 of 5 ended with 1 CRM row and 1 email, 0 second CRM rows. That is not the measure named in the order: the published "second CRM row 4 of 10" is the variant e KILL runs at the two email points (K3 and K2, 5 each = 10). The row is kept and labelled; it is not compared to 4 of 10.

**Variant e, kill runs at the two email points, 5 units of 10 rows (one FRESH stack per unit; `g3e.py K3 5` then `K2 5`). Final counts at 60 s after the restart, per row (CRM / emails / database status):**

| unit | when | rows | second CRM row | 2 or more emails | other | lowest CPU idle in the unit |
|---|---|---|---|---|---|---|
| 1 | 04:52Z | NOT RUN: setup failed (see below) | - | - | - | - |
| 2 | 04:52:56 to 05:05Z | 10 | 0 of 10 | 10 of 10 | all rows 1 / 2 / sent | 35.2 |
| 3 | 05:05:38 to 05:17Z | 10 | 0 of 10 | 10 of 10 | all rows 1 / 2 / sent | 41.7 |
| 4 | 05:18 to 05:30Z | 10 | 1 of 10 | 10 of 10 | one row (K3 run 4) 2 / 3 / sent, the rest 1 / 2 / sent | 39.4 |
| 5 | 05:31 to 05:43Z | 10 | 0 of 10 | 10 of 10 | all rows 1 / 2 / sent | 63.3 |
| 1b | 05:43:28 to about 05:56Z | 10 | 0 of 10 | 10 of 10 | all rows 1 / 2 / sent | 46.8 |

Total over the five valid units: second CRM row in 1 of 50 rows (per unit 0, 0, 1, 0, 0 of 10); 2 or more emails in 50 of 50; status `sent` in 50 of 50. R2 was 1 of 10, published 4 of 10. Each unit has 10 rows; every unit's rc was 0 (no row invalid). Load: median CPU idle 99.5 percent in every unit; the dips below 80 percent are single 30-second samples taken while n8n restarts after the kill (the test's own start-up), nothing else of mine ran. The lowest value of each unit is in the table; the samples are in `R2b-e-unit*-load.jsonl.txt`, the rows in `R2b-e-unit*-rows.jsonl.txt`.

**What these runs say, and do not say.** On a quiet machine the repeated variant e kill-run unit gave 0, 0, 1, 0, 0 second CRM rows of 10 each, so one unit of 10 varies (0 to 1 here). The published 4 of 10 was not seen in any of the five units (the probability of that is not computed here: five units are too few to call a range). Variant a varies a lot between bursts in ONE stack (1, 2, 10, 1, 2 CRM rows); whether the stack matters is the fresh-stack control (below). No cause is claimed for the difference to the published run (the earlier timing hypothesis in this file, that a slower or loaded machine changes when the kill lands, is not tested by R2b; note that the sources say the LOADED run was a separate, unpublished rerun on the author's laptop, not the published run).

**Finding: the owner-setup password can fail on any run (harness bug).** Unit 1 stopped at `setup.py` with `owner setup answered 400 ... "Password must contain at least 1 number."` before any test ran (files `R2b-e-unit1-FAILED.out.txt`, `R2b-e-unit1-setup.out.txt`). The line that draws the password is `harness/setup.py` line 21: `"password": secrets.token_urlsafe(24)`. A 24-byte urlsafe token has 32 characters from a 64-character alphabet with 10 digits, so a draw has no digit with probability (54/64)^32 = 0.44 percent per run; it is in the branch harness (`setup.py` calls itself new, not part of the 2026-11-09 run's code). Scratch fix P2 (only in my scratch copy, not pushed to the public repo): `+ "7"` appended so a digit is always there (diff: `R2b-patch-P2.diff`). P2 was written at 05:49Z, AFTER the variant a bursts, the variant e ten-at-once run and units 2, 3, 4, 5 and 1b had all passed setup, so those SEVEN setups ran on the unfixed draw and passed by chance; only the fresh-stack control and R3-partial used P2. (P2 = the one-line scratch change that appends a digit to the owner password.) The fresh-stack control runs below use P2.

**Mapping of the two published lines (lead's order 1; source file `n8n-published-numbers.md`, which names the branch README table and draft 003):**
- "K1 (crash after step 1): crashed entry visible 1 of 5": NO MATCHING ROW. In `tables.md` (the README gives no visibility count) every kill point of every variant shows "crashed entry visible 5 of 5" (variants a to d, kill points K1, K2, K3; the variant e tables have no such column). In R2 also 5 of 5 (b K2 and K3: 4 of 4). The nearest published sentence is the README line "CRM request in flight (first step): variants a to d ended with one CRM row and no email in 5 of 5 runs each"; that is not "crashed entry visible" and not 1 of 5. My earlier "a CRM-in-flight 1 of 5 vs published 5 of 5" is the row "variant a, kill point K3 (CRM request in flight), final 1 CRM row and 0 emails after one retry": a different measure from the published line, compared with the README's 5 of 5, not with the lead's "1 of 5".
- "kill runs with no effect: 1 of 15": NO MATCHING ROW. `tables.md` says, for variants a, b, c, d, "Kill rows where no client lost its connection: 0 of 15 valid kill rows". The nearest text is `DETAILS.md`, "A kill can fail to take effect": ONE kill run of variant b in a short development test of the rerun harness on a busy computer, not one of the full runs, not 15 rows. R2 also shows 0 of 15 (b: 0 of 13 valid rows).
Scope: only the branch files were read (README, tables.md, DETAILS.md, GATES.md, REPRODUCTION-RULE.md, GLOSSARY.md); the second source named in `n8n-published-numbers.md`, the lead's draft 003, was not available to me. Other visibility figures exist in the branch text: REPRODUCTION-RULE.md gives 4 of 5 for the email-request-in-flight point in the earlier same-computer rerun against 5 of 5 published, and GLOSSARY.md says the loaded run gave different counts for crashed-entry visibility; the lead's "1 of 5" may come from that unpublished loaded run. Within the branch files both lines are therefore not backed by a published row; they come out of the README comparison unless the original run's raw files turn up (lead's note of 05:04Z).

**READ (not repeated): why b K2 and b K3 each had one row `stale_running_after_kill`, in plain words.** Each kill run sends ten requests at once. After the kill and restart the harness reads n8n's list of executions. In both rows 9 of the 10 executions showed `crashed` and ONE showed `running` and stayed `running` for the whole 60 s wait (K2 run 4: execution 2484 between crashed 2483 and 2485; K3 run 5: execution 2606 between 2605 and 2607). The harness code that gives the verdict is `lib.wait_quiet(... stale_outcome=True)` in `lib.py`: if an execution still shows `running` when the time limit is reached while the counts stood still and the stand-in was idle, the row is marked stale (`summarise.py` turns that into `stale_running_after_kill` and the row does not count). The harness only READS that status; it does not write it. n8n's own log of that restart (`Found unfinished executions: ...`) lists 9 ids and leaves out 2484 (and, for K3, 2606); the later restart after the next kill run lists 2484 and 2606 and marks them crashed (the saved database copy says 2484 `crashed`, stopped 04:13:58, 2606 `crashed`, stopped 04:17:33). So the stale `running` row is n8n's own record: n8n's start-up recovery did not mark one of the ten at that restart. Why it skipped that one is NOT established (the harness presses retry through the API on the crashed ones (`g3.py`, `POST /executions/{id}/retry`) but never sets an execution's status; one possible reading, not tested, is a race between the kill and what n8n had written for that execution). Whether this is "n8n behaviour" or "a harness timing effect" cannot be decided from these two rows; the lead accepted the cause as not established (05:04Z). The retry presses worked for the 9 crashed ones; the final counts of both rows (1 / 1 and 1 / 0) match the other rows, so the rows are kept as invalid and counted, never dropped.

**R2b control (lead's note of 04:49Z): variant a, ONE burst on a FRESH stack each (P1 and P2, same flags; ran 05:56:39 and about 05:57:30Z; files `R2b-control-a1/a2-*.jsonl.txt`).** Stack stopped and started clean between them (new work folder, new Postgres container, new n8n).

| control | client replies | final CRM / email | duplicates | CPU idle before / after |
|---|---|---|---|---|
| fresh stack 1 | 200 x1, 500 x9 | 1 / 1 | 0 | 99.7 / 97.8 |
| fresh stack 2 | 200 x1, 500 x9 | 1 / 1 | 0 | 99.8 / 99.0 |

Plain sentence: both fresh-stack bursts ended with exactly one CRM row and one email, replay added nothing. In the one-stack run the first burst was also (1,1), then (2,2), (10,10), (1,1), (2,2). Two bursts cannot show whether stack reuse changes the count (the one-stack run had 2 of 5 at (1,1) and bursts 1 and 4 looked like these two); this control neither shows nor excludes an effect. A fair control would be five fresh-stack bursts; not run.

## R3-PARTIAL: the 2 missing variant b rows (lead's order 4; ran 05:58:17 to 05:59:20Z, rc 0; files `R3p-*`)
Scratch driver (copy of `run_all.py`, body cut: setup with P2, deploys, restart with P1, then `g3.py b K2 1` and `g3.py b K3 1`), fresh stack, quiet machine (CPU idle 97.5 to 100 percent, 4 samples). One row each, not repeated until they were valid:

| row | killed | client replies | executions after restart | retries pressed | final CRM / email | wait for quiet | valid |
|---|---|---|---|---|---|---|---|
| b K2 (email stored, reply held) | yes | RemoteDisconnected x10 | crashed x10 | 10 | 1 / 1 | 3.0 s, no stale row | yes |
| b K3 (CRM request in flight) | yes | RemoteDisconnected x10 | crashed x10 | 10 | 1 / 0 | 3.0 s, no stale row | yes |

With these, b K2 and b K3 have 5 valid rows each when R2 and R3-partial are put together (R2's 4 valid + this 1). These two rows come from a different (fresh) stack than R2's rows, not from the same run: stated, not merged into the R2 tables. Both agree with the R2 b rows (1 / 1 and 1 / 0). This does not explain the two stale rows; it shows that on a fresh quiet stack both points gave all ten executions as `crashed`.

**Evidence files added after the review (so the READ can be checked):** `R2-stale-rows-evidence.txt` (the two stale rows from the R2 result file with their execution ids, the n8n log lines "Found unfinished executions" before and after, and the database rows of executions 2483/2484/2485 and 2605/2606/2607: 2484 and 2606 are `crashed` with stop times 04:13:58 and 04:17:33, minutes after their kill); `R2b-e-tenatonce-WRONGUNIT-rows.jsonl.txt` (the five variant e ten-at-once rows). Two precisions on the READ: (a) the harness counts `running`, `new` and `waiting` as unfinished; the "crashed x9, running x1" in the table is the first read after restart, and that the same execution still ran 60 s later is inferred from the stale flag at the end of the wait (the exec lists after retry show the same id 2484 / 2606 as `running`). (b) The load dips below 80 percent have no event marker in the load files; that they coincide with the n8n restart after the kill is my reading, not recorded. The 80 percent busy rule (two consecutive readings below 80) was not run with `--busy` for R2b.

**Definitions for a cold reader.** "Unit" (variant e): one fresh stack running `g3e.py K3 5` then `g3e.py K2 5` = 10 kill rows; units were 1 (failed at setup, 0 rows), 2, 3, 4, 5, then 1b (the redo of unit 1, run last): 5 valid units, 6 attempts. "Stand-in" = the fake CRM and e-mail server the harness runs (see DETAILS.md). "Agent H" = the helper that runs the CI-equivalent checks; it was stopped before R2b. "The lead's order 1 / 4 / note of 04:49Z or 05:04Z" = entries in `ORDERS.md` of this folder. "The builder's overloaded-laptop rerun" = the unpublished loaded run named in GLOSSARY.md. The lead's list in this file is a comparison column only, not public text.

**Limit of the R3-partial completion.** REPRODUCTION-RULE R2 asks for the full count in one run. The two b rows from R3-partial come from a separate fresh stack with P2, so they do not turn R2's exit 2 into a complete run under that rule; R2 stays "exit 2, shortfall", and R3-partial is an addition next to it.
