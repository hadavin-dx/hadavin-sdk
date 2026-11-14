# n8n-diag-1 (facts, then one clearly marked reading): why the webhook g2-b2 never registers in the harness run
Same machine, harness commit as in N8N-RERUN-1.md, n8n 2.46.6, no change to harness or n8n. Raw excerpts in n8n-rerun/ (smoke2.out.txt, smoke2_readiness.json.txt, outbox-states.txt, diag-first-start-debug-lines.txt).

## Facts
1. Diagnostic A (03:29Z, by hand, in the folder of the failed smoke run, debug log level, harness settings): n8n started; about 3 s after "ready", n8n's log says: started processing workflow publication outbox record 4 (workflow wp0b2-g2-b2), calculated trigger diff 1 to add, added webhook "Webhook" for workflow wp0b2-g2-b2, finished record 4 result completed. GET on g2-b2 then answered the accepted text (404, "not registered for GET requests"). webhook_entity then had FOUR rows including g2-b2. So the workflow itself, its Postgres node, its credential and its path are accepted by n8n 2.46.6 on Linux.
2. n8n 2.46.6 publishes (activates) a workflow through a table workflow_publication_outbox (columns id, workflowId, publishedVersionId, status, errorMessage, createdAt, updatedAt, reason) worked off by a consumer in the n8n process. A record being worked on has status in_progress. The consumer takes a pending record, or an in_progress record whose updatedAt is older than the lease. Lease default in the n8n files: 2 minutes (an environment setting with the words N8N, WORKFLOW, PUBLICATION, OUTBOX, LEASE, SECONDS joined by underscores). I read this in n8n's installed code; I did not change it.
3. Diagnostic B (03:33Z): the README smoke run repeated in a new work folder (smoke2, again hard-linked node_modules): same result as before, exit 1, readiness answered, webhook_registered false, all probes 404 "requested webhook GET g2-b2 is not registered". Directly after the failure, n8n's database in smoke2 showed outbox records 1, 2, 3 (workflows a, d, c) status completed at 03:33:30, and record 4 (workflow b) status IN_PROGRESS, updatedAt 03:33:31. webhook_entity: g2-a, g2-c2, g2-d (three rows).
4. Diagnostic C (03:34:50Z): n8n started by hand in smoke2, no change. Record 4 turned to completed at 03:35:42 (about 52 s after this start, about 131 s after it was set in_progress); after that g2-b2 was registered. (My poll text cut the answer short, so I did not record the exact second the webhook answered; the database time is the evidence.)
5. Order of events in the harness (run_all.py, read, not changed): deploy a, d, c, then deploy_b; right after that the first n8n is killed (smoke branch: kill_n8n_confirmed; full run: restart()), then n8n is started again and webhooks_live waits 60 s for the webhooks. Record 4 was in_progress at the moment of the kill in both smoke runs and in the full run's state (same sequence).
6. 60 s wait of the harness < 120 s lease of n8n 2.46.6: the record cannot be taken again within the harness's wait.

## Reading (mine, not a fact)
The cause is in the order of events, not in the workflow: the first n8n is killed within about a second after deploy_b while the publication of b is still in_progress; n8n 2.46.6 takes that record again only after 120 s; the harness gives up after 60 s. The three other workflows finished within the same second and are unaffected. Not established: whether the publication of b would have completed in the first process (it is not known whether the kill came before or during processing); why b is slower than a, d, c (it is the last one deployed, and the only one with a Postgres node); whether the published laptop run used an n8n version that has this outbox (I do not know that version).

## Proposed one-line fixes (TEXT ONLY, nothing applied to the public repo; for the lead)
P1 (smallest, my pick): in run_all.py, before every kill that follows a deploy (first line of restart(), and the smoke branch before its kill), wait until the webhooks of the deployed workflows answer in the running process: `lib.webhooks_live(PATHS_ABCD, 60) or sys.exit("webhooks not live before the restart")` (smoke: `lib.webhooks_live(["g2-b2"], 60)`). This changes only when the harness restarts n8n, not what is measured.
P2 (not my pick): set the lease setting from fact 2 to a small number for n8n; this changes n8n's behaviour and is not what the published run did.
R2-patched would use P1 in a scratch copy; its SHA256SUMS will no longer match (recomputed only inside the scratch copy). R1 (exit 1, no counts) stays on record.

## NOT DONE / NOT CHECKED (my list, for the lead to decide)
- Whether b2 registers in the FIRST process by itself before the kill: not checked directly; the R2-patched smoke would show it (P1 waits for exactly that). Next: run P1 smoke, 2 minutes.
- The exact second g2-b2 answered in diagnostic C: not recorded (my poll cut text); the outbox time is used instead.
- Why record 4 is the slow one: not investigated (no n8n debug log of the first process; the harness runs it at info level).
- n8n version of the published run: unknown to me; the lead can say.
- Different n8n version: not tried (lead's rule: no version change).
## WHAT I WOULD DO NEXT (ranked)
1. Make the scratch copy with P1, run its smoke (R2-patched smoke), then if registered in the first process, the full R2-patched run on a quiet machine.
2. Write N8N-RERUN-1.md update (R1 stays; R2 added) and the numbers next to the published ones.
3. Egm reviewer on N8N-RERUN-1.md + branch README; cleanup.
