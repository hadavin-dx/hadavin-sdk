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
