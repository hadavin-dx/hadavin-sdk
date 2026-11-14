# Trace: why a 90 s held alert answer produced two alert mails (v3b90a/b/c)
Read-only. No process started or stopped. No R-numbers looked up (not needed for this trace; bible not read).

## Verdict (cause)
Failure name: ALERT-CLAIM-SHORTER-THAN-SEND. Cause: the alert claim (60 s on the first attempt) is shorter than one held send (90 s). The recovery sweep claimed the same lead a second time while the first send was still waiting, so two sends ran in parallel.
Both mails are real sends from two separate SMTP connections, not a duplicate delivery by the server.

## (1) Sweep in probe-v3/mf-recovery.json
- Trigger: node Every30s (scheduleTrigger 1.2), every 30 s. It fans out to MarkFailed, ClaimStuck and AlertClaim at once.
- AlertClaim (postgres executeQuery): UPDATE mf_leads SET alert_until=now()+interval '60 seconds'*(1+LEAST(alert_attempts,4)), alert_token=gen_random_uuid()::text, alert_attempts=alert_attempts+1 WHERE lead_key IN (SELECT ... WHERE state IN ('unknown','failed') AND alert_sent=false AND (alert_until IS NULL OR alert_until < now()) ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 5) RETURNING lead_key,state,alert_token.
- AlertRow (if lead_key notEmpty) -> AlertSend (emailSend 2.1, onError continueErrorOutput, no node timeout set) -> AlertMark.
- AlertMark: UPDATE mf_leads SET alert_sent=true,updated_at=now() WHERE lead_key=$1 AND alert_token=$2 AND alert_sent=false RETURNING lead_key; parameters come from $('AlertRow').item (token of THIS execution's claim).
- Timing, v3a (seconds after fake-SMTP "up"; events.jsonl): lead mail stored 7.11; first alert connect 36.36 (hold starts 36.37); second connect 126.33; hold ends 126.37; both alert mails stored 126.38 and 126.41.
- First claim happened a few ms to tens of ms before 36.36, so alert_until is about 96.3. Ticks fall about every 30 s: 36.4, 66.4, 96.4, 126.4. The 96.4 tick is only about 0.1 s after the claim expiry; it did not claim (not proven why: n8n tick jitter vs claim time; I could not read the database). Next tick 126.4 claimed. The 126 s timing fits: claim ends about 96, next possible tick 126.
- Same in v3b: connect 39.27, second 129.26 (+90.0). v3c differs: connect 38.45, second 98.45 (+60.0, the 96-equivalent tick did claim), stored 98.49; first send released at 128.46 and stored 128.50. So in c the second claim came at the first possible tick, in a and b one tick later. Both are the same defect; the margin to the tick is about 0.1 s.
- Second send was not held (hold applied once; smtp.ctl contains {"drop":0}, meaning not read by me beyond that).

## (2) Real timeouts for a held reply (nodemailer 10.0.14, n8n-nodes-base EmailSend v2)
- n8n node: v2/utils.js:29 createTransport(connectionOptions,...) sets only host, port, secure, ignoreTLS, name, auth, tls. No connection, greeting or socket timeout is set. send.operation.js:256 `await transporter.sendMail(mailOptions)`: no timeout wrapper (grep for timeout in send.operation.js found none).
- Defaults, nodemailer/dist/cjs/smtp-connection/index.js:49-52: CONNECTION_TIMEOUT 2 min (used at line 350-352, cleared when connected), SOCKET_TIMEOUT 10 min (set at 749 and 1027), GREETING_TIMEOUT 30 s (set 751-756, cleared on greeting at 1312), DNS_TIMEOUT 30 s.
- So a held RCPT reply (after greeting) is bounded only by socket inactivity: 10 min (line 749/1027, handler 945-946 gives error "Timeout"). Hold of 90 s is well inside it. I found no per-command response timer.
- Workflow-level: @n8n/config executions.config.js default timeout -1 (no limit), maxTimeout 1 h. Whether the run used a different EXECUTIONS_TIMEOUT: not checked (no env file read).
- Held greeting would instead die at 30 s.

## (3) Late finish and parallel sends
- Late finish after claim expiry: expiry alone does not stop AlertMark. The mark checks only lead_key, alert_token and alert_sent=false. A send finishing late marks true if its token is still the current one (i.e. no newer claim ran). If a newer claim ran, AlertClaim overwrote alert_token, so the old send's mark matches zero rows and does not mark; the newer send's mark does. In this trace: first send's mark (token 1) should have failed and second's (token 2) succeeded. Inferred from SQL; database rows not read.
- Two parallel sends can both succeed: yes, shown by the two stored alert mails in a, b, c. The token guard protects only the mark, not the send. Nothing blocks a send once claimed. Result: one lead, two alerts, alert_sent true once.
- Not 'exactly once' anywhere: n8n retry or process death after the send but before the mark would also send again at the next claim (at-least-once).

## Not verified
- Database content (alert_attempts, alert_token, alert_sent) during the runs: not read, so the token inference in (3) is from SQL only.
- Why the 96 s tick missed in a and b but hit in c (exact ms of now() vs alert_until): n8n.log has no timestamps for ticks.
- That the held reply was RCPT specifically: events only say alert_hold_start after connect.
- Execution timeout actually set in the run's environment.
- Whether the n8n log shows AlertMark results: grep of n8n.log found nothing relevant.
Suggested fix (not applied): claim longer than the worst send (>= 10 min socket timeout, or set socketTimeout shorter and claim above it), or add an idempotency key the mail receiver can dedupe. Needs EGM before change.
