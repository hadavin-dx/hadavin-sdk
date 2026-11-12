# Lead note for the cloud session: demo parts to promote into core, not to rebuild (2026-11-12)

Status: PLAN ONLY. Do not start any item below until the lead's message starts with GO. The demo code is not public yet; its first public push comes after its last review round. This note holds no demo code.

## Why
A demo (a duplicate-proof lead desk: one lead processed once, with approvals and an audit trail) already has tested versions of several generic parts. Rebuilding them here would waste time and tokens. Rule: look at the demo version first (CODE-LAST ladder rung 2/4: exists, so promote), then generalise, keep its tests, and add tests that fail on the old core code.

## Parts that look generic (the lead confirms each at GO, with a snapshot or the public demo repo link)
| # | Part | What it does | Core module it likely belongs to |
|---|---|---|---|
| 1 | Per-request receipt and claim | every incoming request gets a durable receipt before any side effect; a second claim of the same key returns the first result, a blind sender gets a neutral "unknown" answer | idempotency / intake kind |
| 2 | Refuse a public bind with any real service | the process refuses to start on a non-loopback address whenever a real CRM, mail provider or live model is configured; checked before any socket opens; every spelling of "any address" tested | server settings / mode safety |
| 3 | Loopback-only stand-in hosts | a "stand-in" kind (test mail server, fake CRM) must resolve to a loopback address, otherwise the kind counts as a real service; a registry test fails when a new kind is missing from the real-service list | kinds registry / mode safety |
| 4 | Retry with backoff and a "gave up" state | a write to an outside system retries with growing waits (10, 60, 180, 420 s), a new stage restarts it, a gave-up item is shown as such and can restart; gates follow the database, not memory | outbox / sync kind |
| 5 | Safe reset script | a reset refuses to delete data while the process still runs, a port answers, a foreign process holds the lock or a pid file names another program; waits for a slow stop | tooling for demos and pilots |
| 6 | Mode banner and demo-only folder guard | a page banner that says honestly whether real services are connected; a test that deletes the demo-only folder and still passes | portal shell |

Parts that stay in the demo: lead-flow wiring, portal pages for the lead desk, the demo-only data, n8n recipes.

## Rules for the work (same as always)
- One draft PR per part, branch from main, tests that fail on the old code, a mutant per code item, hygiene scan with the required scan flag, a rung table in the PR body, no merge (the lead merges), no secrets, synthetic data only, no live model calls.
- Before writing, search this repo for an existing equivalent and say so in the PR body.
- Stage names are demo, pilot, prod only. Core modules stay generic: nothing specific to one project or tool.
- Reviews by fresh reviewers that get the diff and the spec, never the author's verdict; security and mode-safety paths have no round cap.
- If something here conflicts with a rule in your own brief, stop and ask the lead.

## Where the demo code will be
After the demo's public push the lead sends the repository link and the commit to read. Until then, ask the lead for a patch of the part you are about to promote; do not guess its shape.
