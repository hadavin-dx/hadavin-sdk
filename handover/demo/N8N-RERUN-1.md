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
- n8n restarts passed the P1 wait every time (log: "n8n default up: True", "n8n limit 1 up: True"). Variant e's path is not in the harness's check list; e ran through.
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
Reading note, fact only: variant a in R2 ended far from 1 CRM row and 1 email more often than in the published table (12 vs 18 of 20), and variant a's kill runs ended with a different number of rows than published. I give no reason; the interval text in R2-tables.md says the runs are not independent.

## Did P1 touch any published claim?
P1 adds one wait (webhooks live in the running n8n) BEFORE the kill step of restart(); it does not touch g3.py or g3e.py, where the kill points K1 to K3 are set (the kill inside a test run happens at a known trigger in those scripts, read from their code names, not changed). So the kill windows and the ten-at-once tests are unchanged; only the time between deploy and the restart is longer in R2 than in R1. Whether a longer pre-restart wait could change a count is NOT established.

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
