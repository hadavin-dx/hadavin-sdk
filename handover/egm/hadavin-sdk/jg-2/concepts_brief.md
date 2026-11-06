> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-2: alert intake (a Datadog alert or a generic webhook becomes a work item)

* **Author:** Claude (ticket author session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06 (written from 07:46 UTC / 13:16 IST)

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill asks for six reviewer lenses run as fresh sub-agents. This session has no sub-agent tool, so none ran. A review in the same context does not count as a Goldfish review. The "Analysis" below is the author's own stress test across the six lenses. The independent check is the ticket's review rounds and the build-start review.
- **AUTO mode.** Every interactive gate was skipped (clarifying turns, readiness gate, iteration loop, handoff gate), as the brief from the lead's session requires. Where the skill would ask a person to choose, this brief takes the option that a similar FROZEN ticket (AK-G2, AK-G15, AK-G16) took, and names it under "Key decisions".
- **Sources.** `LEAD-ORDERS.md` orders 23, 27, 34 and 47; `tickets/AK-G2.md` (FROZEN rev 3 + BN-1..25), `tickets/AK1.md` (FROZEN rev 3), `tickets/AK-G15.md` (FROZEN rev 3); core source read-only at `src/` commit `631dd1d`; the Datadog webhooks integration page, read 2026-11-06 (`docs.datadoghq.com/integrations/webhooks/`).

## Overview

Order 47 makes Jagrat (the former Warden) the one showcase demo. Its story starts when a monitoring alert fires: Datadog sends an alert, Jagrat opens an incident, reads the cloud (JG-1), and posts a summary as a threaded Slack reply (JG-3). JG-2 is the first link: it turns one incoming alert into one **work item** (one incident record) and starts at most one agent run for it.

JG-2 is NOT a new way in. AK-G2 (frozen) already owns the one inbound door: a signed web address per source, a ledger that saves every message before answering, delivery dedupe, and a dispatch step that hands each saved message to a per-source pipeline step (`tickets/AK-G2.md:194`, `:483-485`). JG-2 adds three things on top: (1) a second way to check who sent a request, for senders that cannot sign (Datadog); (2) a step that reads the alert's fields and groups repeats of one alert into one work item; (3) a small work-item record that the portal (JG-4) and the notifier (JG-3) can read.

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **Datadog does not sign its webhooks.** The Datadog page lists basic auth in the address, custom headers, OAuth 2.0 client credentials and hidden custom variables; it says nothing about a signature over the body (read 2026-11-06). AK-G2's door accepts only `hmac_v0` signatures (`AK-G2.md:102`, `:209`). So a direct Datadog-to-door path needs a weaker check: a shared secret token in a header, compared in constant time. A token proves the sender knows the secret; it does NOT protect the body against change in transit (TLS does that) and it does NOT carry a signed time, so the 300 s replay limit of `hmac_v0` does not apply. This is the main security trade-off and it is owner-visible.
2. **Replay with a static token.** Anyone who captures one request (a log, a proxy) can resend it while the token is valid. The ledger already makes an exact resend a `duplicate` (no second run). A captured request with a changed body needs the token, so it is token theft, not replay. A late resend of an old alert with a fresh event id is the remaining case: the step refuses an alert whose own event time is outside a replay window. The event time is inside the token-protected body but is not signed; this is stated plainly.
3. **Grouping must not cost a model call per flap.** A noisy monitor can send "Triggered", "Re-Triggered", "Renotify" every few minutes. If every delivery started a run, one flapping alert would pay many times. Grouping must happen BEFORE a run starts.
4. **The door's `id_field` is the delivery id, not the alert id.** Using the alert id as `id_field` would make the second notification of one alert an "id reuse" (409, body not kept, AK-G2 `:181`), so recovery and renotify events would be lost. The delivery id must be the per-notification event id; grouping is a second key.
5. **Alert text is attacker-influenceable.** Monitor titles, messages and tags can be written by anyone with monitor-edit rights, and templated values can carry log text. It must reach the model only through `Runtime.handle`, which redacts before the injection check and before the model (`runtime/agent_loop.py:361-390`), and must never reach logs, audit, or the work-item record as anything but capped, stored data shown as text.
6. **Retries that are not byte for byte.** AK-G2 treats a retry with other bytes as an id reuse (409). Whether Datadog re-renders the template on retry (for example a changed `$LAST_UPDATED`) is UNVERIFIED. If it does, the first copy is kept and the retry is refused; nothing is lost, but the 409 shows in Datadog. A build-start check with recorded fixtures is needed.

**Counter-arguments weighed (by lens).**
- *Contrarian / YAGNI:* "Put a signing forwarder (n8n) in front of Datadog and add nothing to the door." Kept as the alternative, not the default: it adds a running component to the demo and to each client, and the forwarder still receives the same unsigned token from Datadog, so the weak link moves, it does not disappear.
- *Cost:* grouping before the run keeps cost at one run per alert cycle. One work-item write per delivery is cheap; the door's busy limit (`max_open`) already caps a flood.
- *Ergonomics:* the Datadog side is one webhook with a fixed JSON payload template and one hidden custom variable holding the token; the runbook gives the template.
- *Migration:* one new table, additive; the door change is one config field with a default that keeps today's behaviour (`hmac_v0`).
- *Observability:* closed log codes only; the work item shows count of deliveries, first and last time, last transition.
- *Tech debt:* the verify choice is a closed set of two schemes, not a plug-in API (cut surface, order 8).

## Goals vs. Non-Goals

* **In-Scope Goals:** a `header_token` check on the AK-G2 door (constant-time compare, two tokens for rotation, minimum length); a Datadog payload template and a generic alert payload, both normalised to one alert record; delivery dedupe by event id (AK-G2's ledger); alert grouping by (source, monitor, alert cycle) for Datadog and (source, monitor key, time window) for the generic payload; a replay window on the alert's event time; caps on body and field sizes; tenant from the source's config only; one run per new work item through AK-G2's `StartRun`; recorded Datadog fixtures; deployment name as a config value (`demo`).
* **Out-of-Scope Non-Goals:** live Datadog calls or accounts; the Slack reply (JG-3); portal pages (JG-4); reading the cloud (JG-1); closing or resolving an incident by a person (JG-4/AK-G15); OAuth client-credentials auth from Datadog (outline); other vendors (PagerDuty, Grafana, CloudWatch alarms: outline, they use the generic payload through a forwarder).

## Alternatives Weighed

- **Second door just for alerts.** Rejected by the lead's brief and by AK-G2's design: one door, one ledger (`AK-G2.md:101`).
- **Signing forwarder in front of Datadog as the default.** Rejected by author as the default (extra component; same unsigned hop); kept as the working alternative.
- **Datadog OAuth 2.0 client credentials (we run a token endpoint).** Rejected by author for v1: we would build a token issuer, which is crypto-adjacent code the tool ladder says not to write; outline with trigger "a client refuses a static token".
- **Basic auth in the address.** Rejected by author: the secret sits in the URL, which proxies and logs often record.
- **Alert id as `id_field`.** Rejected by author: later notifications become id reuses and are lost (risk 4).
- **Sliding grouping window (attach while the last delivery is recent).** Rejected by author for v1: needs a "current open item per monitor" index and an expiry rule; a fixed time bucket is one deterministic key. The cost is stated: a flap that crosses a bucket edge makes two work items.
- **Group inside the agent run.** Rejected by author: every delivery would start a paid run (risk 3).

## Key Decisions & Staging for Next Steps

1. **Verify schemes: closed set `{"hmac_v0", "header_token"}` on AK-G2's `WebhookSource`** (AK-G2 row V4's outline, `AK-G2.md:209`, made real). Same choice shape as AK-G2: closed sets, no plug-in API.
2. **`header_token` compare:** `hmac.compare_digest` over the SHA-256 of the presented and the configured token (equal-length inputs; stdlib; no home-made crypto). Two configured secrets (current, previous), as AK-G2's `signing_secret_names` (`AK-G2.md:197`).
3. **Delivery id = Datadog `$ID` (event id)**; grouping key = `$ALERT_ID` + `$ALERT_CYCLE_KEY`. Generic payload: `id` + (`monitor_key`, `floor(event_time / window_s)`).
4. **Replay window on the event time** (`replay_window_s` default 900, future skew 120) for `header_token` sources; `hmac_v0` sources keep the signed 300 s window and also get the event-time check.
5. **Reasons:** no new AK1 reason; use `refused invalid_input`, `refused forbidden`, `needs_person policy` (closed set `AK1.md:115`), with JG-2's own closed detail code in logs. Same choice AK-G2 made (no `REASON_BY_ERROR` row, `AK-G2.md:107`).
6. **Work-item record:** one table, tenant and readers in every row (order 27 item 56, as AK-G2 and AK-G15 did).
7. **Deployment name `demo`:** a config string used in the audience (`demo/<source>`) and the portal link; it is NOT the safety profile (`config.py:317`, `dev|pilot|prod`). Which profile the demo runs under is a PENDING LEAD item.
8. **Staging:** one design (`design.md`), then ticket JG-2 rev 1 with two sub-PRs (JG-2-a door scheme; JG-2-b intake step and work items), building after AK-G2-b.
