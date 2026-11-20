# QUESTIONS from core-a

Written 05:22 UTC / 10:52 IST from the plan read-back (PLAN-READBACK.md section 7 holds the full text and what was checked). None of these stops work now; the ticket writers carry a proposed answer for each.

1. ENDPOINT TO WORKER HAND-OVER. plan-v4 row D says the endpoint "records the request and acks" and a worker calls Runtime.handle, but with no new table nothing can carry a request from one process to another. Tried: read agent_loop.py:465-585 (handle blocks through the model calls). The lead draft (inputs/draft-tickets-C-D.md finding 1) answers it: ONE process, ack once the run row exists, no table. Recommended answer: keep the lead draft's shape; ticket D checks it against the code. Lead: confirm.
2. HOW THE SENDER IS FOUND BEFORE THE SIGNATURE CHECK. Read-back recommends a sender header that must equal a signed value; the lead draft says try every sender's secret, no header. Recommended: lead draft (no unsigned input decides anything) while senders are few. Ticket D states the trade-off.
3. HEADER NAMES AND URL PATH are in no plan file. Recommended: the lead draft's POST /v1/trigger, X-Hadavin-Request-Timestamp, X-Hadavin-Signature.
4. WHO WRITES TEST GROUP T2 NOW. plan-v3 gave it to DOOR, plan-v4 row D lists only T5. Recommended: DOOR writes the thin-endpoint cases; the 25-hour and 31-day cases go with step H (or are cut with it).
5. WHERE THE n8n TEMPLATE FILES LIVE. Not in any plan file; the repo has none today. Read-back recommends src/hadavin_sdk/triggers/n8n/, the lead draft says n8n/ at the repo root. Recommended: decide in ticket D after checking how the wheel is built (a JSON file inside src ships to every client).
6. BASELINE OF core/T1-T2-tests (an input of step D) has no row in the queue or in inputs/lead-baselines-SUMMARY.md. Recommended: lead adds it to the laptop baselines.
7. SOCKET GUARD: no source for it in inputs or in the repo. Recommended: step E writes it new (ticket E decides if it is needed at all).
8. CONFIG FIELD NAMES for tenant, per-sender secrets, agent and principal per sender. Recommended: ticket D proposes them as ONE request file to core-b (handover/core-a/requests/).
9. INTERFACE (i) of core-b is not in inputs/ yet, so the store contract tests (queue item T4) cannot start. Lead: please drop it in inputs/ when core-b publishes it.
10. src/hadavin_sdk/testing/ already exists (__init__.py, mutation.py). Step E would only ADD new files in it and not change __init__.py. Lead: is adding files to that existing package allowed for DOOR, or must the helpers go in a new package?
