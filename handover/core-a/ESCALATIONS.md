# ESCALATIONS of core-a (problems and unresolved review findings for the lead; newest on top)

## E4 (05:38 UTC) n8n template cannot be finished without a real n8n (review finding IR-M11)
Item: n8n/hadavin-trigger.json, n8n/hadavin-trigger-error.json. Not decidable here: node versions, Crypto node or Code node for signing, where the signing secret may live in n8n, export format of the pinned n8n version, whether a retry re-runs the sign node. Tried: read of inputs/atlas-n8n.md only; no n8n exists in this container (CAPABILITY.md). What I did: outline files marked "not run in n8n", every unsure parameter marked UNVERIFIED, checks that run here (JSON parses, no secret-shaped text). Needed from the lead: one import and one test call on the laptop's n8n, or the word "leave as outline".

## E3 (05:38 UTC) worker.py repeats the agent qualification loop of cli.py:289-298 (review remark, codebase reviewer)
A shared helper would remove the copy but needs a change in core-b's file. Not done (DOOR creates new files only). Lead: request to core-b, or accept the copy.

## E2 (05:38 UTC) what wsgiref does on a real socket timeout is NOT RUN (review finding IR-M6)
The endpoint answers 400 with an empty body when the body read fails in-process. On a real socket, wsgiref's own error handler may send a 500 with a text body and print a traceback, which would break "every refusal has an empty body". Not tried yet: one test with a real loopback socket that sends fewer bytes than Content-Length. I will try it once in the batch; if it shows the 500, the fix (own handler class with quiet error output) comes back here as a ticket change.

## E1 (05:38 UTC) two open questions of ticket D change code and need the lead's word (review finding IR-M4)
(a) Should a signed request that gets 409 (same key, different document) write an audit event? Today it writes nothing (ticket invariant 7). Recommended: no event in this step; a log line with status and sender only. (b) Should the worker stop with exit code 4 after 3 store connection errors in a row? Today it keeps answering 503. Recommended: not in this step; the sender's retry covers it and the process supervisor is the client's. Raw: tickets/D-review-1.md rows IR-M4.
