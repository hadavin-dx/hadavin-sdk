> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-3: chat-ops notifier (design)

* **Author:** Claude (ticket author session, `egm:egm-draft`, AUTO mode)
* **Date:** 2026-11-06 (about 07:55 UTC / 13:25 IST)
* **Intake:** `concepts_brief.md` in this folder (Priority 1 source). Code read at `ce70eb5` (last commit touching `src/`).

**Honest notes.** (1) AUTO mode: every section gate and the save-location gate were skipped; each architecture choice the skill would put to the author takes the option a frozen ticket took, named in "Decisions taken in AUTO mode". (2) The skill's `resources/execution_instructions.md` is missing from the installed plugin (`/root/.claude/plugins/cache/egm/egm/0.1.0/skills/egm-draft/resources/` does not exist); it was not applied. (3) No Goldfish review ran (no sub-agent tool in this session). (4) Saved here, not in `docs/designs/`, as the brief asked (handover rule: EGM artifacts stay out of `src`).

## Overview

When an alert fires, Datadog posts a message in the client's Slack channel. Jagrat investigates and writes a summary. JG-3 posts that summary as a reply in the thread of the alert message, with one link to the incident page in our portal. It posts each summary once, never leaks a secret or a matched personal value, keeps trying when Slack says "slow down", and never loses the incident when posting fails.

## The Problem

Core can post approval cards to Slack (`approvals/slack_channel.py:123-135`), but:
- it cannot reply in a thread: no `thread_ts` is ever sent (`slack_channel.py:124-133`, `:166-175`);
- its text rule forbids links (`approvals/channel.py:1`, `:18-21`), and the portal link is the point of the notice;
- `post_card` posts and forgets: a failure is a `Delivery(ok=False)` (`slack_channel.py:161-178`) with no record and no retry, so a second attempt by a caller can post twice and a lost attempt leaves nothing behind;
- there is no rate-limit handling on the Slack path; the only retry helper caps a server's wait at 8 s (`llm/retry.py:23`, `:66-74`).

## Goals

1. Capability `notifier`, kinds `recorded` (neutral default, dev only) and `slack`.
2. `notify_incident(...)` posts one reply under a given message (`ThreadRef`: channel id and message time stamp).
3. The text passes the existing choke point `clean()` (`approvals/channel.py:18-39`: sanitise, withhold commands, one redaction through `runmap.redact_text`), which P2d hardens; the notice is a registered producer (`guard/producers.py:1-9`).
4. The link is built by our code: `portal_base_url` from config + `/incidents/` + the validated incident id. It carries no token and no personal data; the portal page needs sign-in (AK-G17).
5. Once per (tenant, incident, alert message): a stored record with one final state.
6. Rate limit: a 429 schedules a retry for the `tick` pass, honouring `Retry-After` up to a configured ceiling.
7. Failure never deletes or blocks the incident; the record shows what happened (portal, JG-4).
8. The bot token comes only through the secrets kind (`backends/platform_secrets.py:18-31`: a factory may read only the `*_secret_name` values in its own settings); deployments use `mounted_file` (`backends/table.py:420-425`, `actions/secrets_file.py:1-10`).
9. The environment name ("demo") is a config value shown in the reply.

## Non-Goals

Finding the alert message's id (JG-2); the portal pages and sign-in (JG-4, AK-G17); the recipient gate (AK-G22); e-mail and Teams backends (outline rows); editing or deleting a posted reply; mentioning people; buttons that change anything (JG-5, G14); a model call (JG-3 makes none; no money path).

## Open Questions (go to the ticket as PENDING LEAD)

1. Who finds the alert message's `thread_ts` (recommend JG-2, through AK-G2's door).
2. A separate Slack app and token for the notifier (recommend: own secret name now; own app before any pilot).
3. Link form: sign-in-gated plain link (recommend) or signed short-lived link.
4. People's names in free text are not masked by the pattern redactor: owner-visible limit.
5. Pilot/prod refusal of the `slack` notifier until AK-G22 is wired (recommend yes).

## Critical User Journeys

### CUJ 1: normal post
Alert arrives; JG-2 makes the work item with `ThreadRef`; Jagrat writes the summary; `notify_incident` cleans the text, claims the record (`sending`), posts with `thread_ts`, records `posted` with Slack's reply ref. The on-call person sees the reply under the alert and clicks "Open the incident in the portal", signs in, sees the incident.

### CUJ 2: the same incident is notified twice (a retried run)
The second call finds the record `posted` and returns `duplicate`; nothing is posted.

### CUJ 3: Slack says "rate limited"
Slack answers 429 with `Retry-After: 30`. The record becomes `retry` with `next_try_at = now + 30 s` (at most `max_retry_after_s`). The next `tick` pass after that time takes it (CAS `retry` to `sending`) and posts.

### CUJ 4: the process stops mid-post
The record stays `sending`. When its lease ends, `tick` marks it `unknown`, never re-posts. The portal shows "the reply may or may not be in Slack; check the thread". The incident itself is untouched.

### CUJ 5: the bot is not in the channel
Slack answers `ok: false, error: not_in_channel` (code name UNVERIFIED). The record becomes `failed` with reason `not_in_channel`; no retry.

## Technical Plan (Architecture)

```
JG-2 work item (incident id, ThreadRef) + Jagrat summary text
        |
        v
notify/service.py  notify_incident(store, notifier, settings, notice, now)
  1 validate ids (incident id, ThreadRef patterns)          -> refused (nothing stored)
  2 text = header(environment_name, incident id) + clean(summary)
       too long -> fixed sentence "The summary is too long to show here; open the incident in the portal."
  3 link = portal_link(portal_base_url, incident_id)         (our code only; never from text)
  4 store.notice_claim(key, ...)  key = AK1 tenant_key(tenant, "notice", incident, channel, ts)
       existing posted|failed -> duplicate ; existing sending|unknown|retry -> already_in_hand
  5 outcome = notifier.post_reply(thread, text, link)       (never raises)
  6 store.notice_finish(key, from=sending, to=posted|retry|failed|unknown, ref, reason, next_try_at)
        |
        v
runtime/tick.py  step "notify_retry": due rows ->
   sending with lease ended -> unknown ; retry with next_try_at <= now -> notice_take (CAS) -> step 5, 6
```

**Record states.** `sending` (claimed, lease `lease_s`), `retry` (waiting, `next_try_at`), and three final states: `posted`, `failed`, `unknown`. Every record reaches exactly one final state or stays `retry` until `max_attempts`, then `failed` (reason `attempts_exhausted`). The masked text is kept only while the record is not final (so `tick` can retry without the caller); it is set to null at the final state.

**What is retried and what is not (once-only rule).** Retried: HTTP 429 or Slack `ratelimited` (Slack did not accept it); a connection that never opened (DNS failure, connection refused, TLS handshake drop before the request was sent). Not retried, final `unknown`: a read timeout or a dropped connection after the request was sent, and any 5xx (Slack may have posted). Not retried, final `failed`: any other `ok: false` code, 4xx other than 429. This means duplicates cannot come from us; a missing reply can, and it is visible. Reason: R368 (no lost or double-applied messages) cannot be fully met without an idempotency key from Slack; the design picks "visible miss" over "silent double".

**Slack backend.** `chat.postMessage` with `channel`, `thread_ts`, `reply_broadcast: false`, `unfurl_links: false`, `unfurl_media: false`, a fallback `text` ("Incident update"), and blocks: one `section` with `plain_text` (the cleaned text, as `slack_channel.py:85`), and one `context` block with one `mrkdwn` element that is ONLY our link `<URL|Open the incident in the portal>` (precedent for a code-built `mrkdwn` context element: `slack_channel.py:92-97`). The URL is built from validated parts and contains no `<`, `>`, `|`, space or `&` unescaped (checked; refused otherwise). The HTTP call is the existing `SlackChannel._call` (`slack_channel.py:50-60`), moved behaviour-preserving to `approvals/slack.py` as `call(...)` so both kinds share one transport, which uses `post_json` (`llm/common.py:255-265`). 429 handling reads the status and `Retry-After` through `llm/retry.py` `status()` (`:31-36`) and `retry_after()` (`:66-74`), with `retry_after` given an optional `cap` argument (default unchanged, `MAX_DELAY_S`) so the notifier can use its own ceiling.

**Recorded backend (neutral default).** `RecordedNotifier` keeps every post (thread, text, link) in memory and answers from a script of outcomes given by tests (default: `posted`). No network, no secret. Dev only.

**Config.** Kind settings in `backends/table.py` next to the channel block (`:558-566`): `RecordedNotifierSettings` (none), `SlackNotifierSettings(bot_token_secret_name, api_base="https://slack.com/api", timeout_s)` (same shape and https check as `SlackSettings`, `table.py:320-325`, `slack_channel.py:206-216`), `hosts` from `api_base` for the egress allow-list (as `table.py:563-564`). Shared settings in a new optional `notify:` block of the top-level config: `environment_name` (pattern `^[a-z][a-z0-9-]{0,31}$`, e.g. `demo`), `portal_base_url` (https; http only for a loopback host in dev), `max_text_chars` (default from `defaults.py`, `le` the backend's limit), `max_attempts`, `max_retry_after_s`, `lease_s`. `environment_name` is a display name; it is not the policy level `environment: Literal["dev","pilot","prod"]` (`config.py:317`), whose names are an owner-approved exception (`table.py:591-592`).
- `notifier` is NOT added to `DEFAULTS` (`table.py:582-589`): a config without it has no notifier. Adding a default would make every existing pilot config fail the dev-only table, as `channel: fake` does (`table.py:588`, `:596`).
- `("notifier", "recorded")` joins `DEV_ONLY` (`table.py:593-602`). `("notifier", "slack")` is refused outside `dev` until AK-G22 is wired (new refusal in the environment check, `config.py:365-373`, every refusal listed at once).

**Gates (order 27 item 63).** The notice text is DELIVERED text: AK1 classifies it `recipient` and lists it in `RECIPIENT_PATHS` (AK1 ticket `tickets/AK1.md:62`; code not merged, names UNVERIFIED in code). Until AK-G22 merges it goes through neither gate (as AK1 says at `:63`); the pilot/prod refusal keeps it closed there. The text is masked by its producer row (`clean`), as every recipient path today.

**Store.** Four methods on the store Protocol (`store/protocol.py:49`), memory and Postgres: `notice_claim`, `notice_take`, `notice_finish`, `notices_due`; one additive migration (next free number at merge, amendment A3; today's last is `0005_evidence.sql`); grants: runtime role SELECT, INSERT, UPDATE; portal role SELECT (`store/migrate.py:25-26`).

**Logs and audit.** Ids, state, reason code, attempt number only; never the text, never an exception message (as AK-G1 path (6), `tickets/AK-G1.md:97`).

## Alternatives Considered

### Alternative A: extend the approval `Channel`
Add `thread_ts` and a link to `Channel.post_card`. Rejected by author: `Channel` is the approval contract (`channel.py:69-82`: `send`, `update`, `parse_decision`), and its link-free rule protects approvers; a notice needs a link, a thread and a stored once-only record.

### Alternative B: link inside the cleaned text
Rejected by author: `clean()` removes links by design (`channel.py:19-21`), and a link parsed from model text could point anywhere.

### Alternative C: a URL button instead of a `mrkdwn` link
Rejected by author: a Slack button click may send an interaction payload to the app's request URL even for a URL button (UNVERIFIED); our receiver handles approval payloads only (`approvals/receiver.py`). A context link sends nothing to us.

### Alternative D: retry timeouts and 5xx automatically
Rejected by author: Slack may already have posted; a blind retry gives a double reply. Kept as an owner option if he prefers "no miss" over "no double".

### Alternative E: signed short-lived link
Rejected by author as the default: a short link dies in the Slack history; a long one is a bearer secret in a shared channel. Owner option (PENDING LEAD).

### Alternative F: sleep in-process for `Retry-After`
Rejected by author: blocks the run; retries go to `tick` (every 30-60 s, `runtime/tick.py:1`).

### Alternative G: a no-code flow (n8n) as the default backend
Rejected by author for the default: redaction and the once-only record must stay in our code (tool ladder rung 7). A webhook backend for a no-code flow is an outline row.

## Non-Functional Requirements

- Load: one post per incident; Slack limits per channel (about one message per second, UNVERIFIED) are far above alert rates; a burst test of 200 notices over 20 channels with injected 429s runs against the recorded backend (R368/R370 style, made-up data).
- Isolation: the key includes the tenant (AK1 `tenant_key`); colliding incident ids across tenants stay separate (test).
- No new dependency (stdlib HTTP only); no secret in config; no live Slack in tests.

### Future Improvements
Outline rows in the ticket: e-mail backend, Teams backend, webhook backend for a no-code flow, signed-link option, AK-G22 wiring, portal action to settle an `unknown` record.

## Decisions taken in AUTO mode (precedent)

| # | Choice | Precedent |
|---|---|---|
| D1 | New capability, not a `Channel` extension | AK-G1 rev 3 adds its own hook contract `deliver_reply` (`AK-G1.md:194`) |
| D2 | Refused in pilot/prod until AK-G22 is wired | AK-G1 rev 3 row T19 (b) (`AK-G1.md:183`, `:448` V12) |
| D3 | Write-ahead record, one final state, no blind re-post | AK-G2 inbound ledger (dedupe with one final state) |
| D4 | Second backend as outline rows with triggers | AK-G16 outline rows (V17) |
| D5 | Neutral default is a dev-only fake kind | `channel: fake` in `DEV_ONLY` (`table.py:596`) |
| D6 | Not in `DEFAULTS` | back-compatibility of existing pilot configs (own reasoning; no precedent) |

## Reconciliation with the brief (draft step 6.1)

No contradiction. Additions that change an interface: (1) a new top-level `notify:` config block; (2) a new optional `cap` argument on `llm/retry.retry_after`; (3) the Slack HTTP call moves to `approvals/slack.py`; (4) the link is a `mrkdwn` context element, not a button (Alternative C).

## UNVERIFIED (not read in code, or general knowledge not checked today)
Slack error code names (`not_in_channel`, `channel_not_found`, `thread_not_found`, `ratelimited`, `msg_too_long`); Slack sends HTTP 429 with `Retry-After` for rate limits; per-channel rate (about 1 per second); `chat.postMessage` has no idempotency key; URL-button interaction payloads; `thread_ts` and `reply_broadcast` field behaviour; monitoring webhook payloads lacking the Slack message id; AK1 names (`tenant_key`, `RECIPIENT_PATHS`) exist only in ticket text; Teams Graph reply endpoint and permission; e-mail threading by `In-Reply-To`/`References` (RFC 5322, not re-read today).

## Detailed Implementation Plan

### Target Files to Create/Modify
1. `src/hadavin_sdk/notify/__init__.py` (Create): package marker, one-line docstring.
2. `src/hadavin_sdk/notify/protocol.py` (Create): `ThreadRef`, `Notice`, `PostOutcome`, `NoticeResult`, `Notifier` Protocol, id patterns.
3. `src/hadavin_sdk/notify/recorded.py` (Create): `RecordedNotifier` and its `build`.
4. `src/hadavin_sdk/notify/slack.py` (Create): `SlackNotifier`, block building, outcome classification, `build`.
5. `src/hadavin_sdk/notify/service.py` (Create): `render_text`, `portal_link`, `notify_incident`, `retry_due`.
6. `src/hadavin_sdk/approvals/slack.py` (Modify): gains `call(...)`, moved from `SlackChannel._call`.
7. `src/hadavin_sdk/approvals/slack_channel.py` (Modify): `_call` delegates to `slack.call` (behaviour-preserving).
8. `src/hadavin_sdk/llm/retry.py` (Modify): `retry_after(exc, cap=MAX_DELAY_S)`.
9. `src/hadavin_sdk/backends/table.py` (Modify): `notifier` rows, settings classes, `ALLOWED`, `DEV_ONLY`.
10. `src/hadavin_sdk/config.py` (Modify): `NotifySettings` block, pilot/prod refusal of `slack` notifier.
11. `src/hadavin_sdk/defaults.py` (Modify): own JG-3 block (order 20 item 5).
12. `src/hadavin_sdk/store/protocol.py`, `store/memory.py`, `store/postgres.py` (Modify): four methods.
13. `src/hadavin_sdk/store/migrations/00NN_notices.sql` (Create) and `store/migrate.py` (Modify: grants).
14. `src/hadavin_sdk/runtime/tick.py` (Modify): step `notify_retry`.
15. `src/hadavin_sdk/guard/producers.py` (Modify): producer row.
16. `src/hadavin_sdk/app.py` (Modify): builds the notifier when configured, next to the channel build (`app.py:170`).
17. Tests: `tests/test_jg3_notify.py`, `tests/test_jg3_slack.py`, `tests/contracts/` store contract additions, `tests/test_k5_round9.py` driver.
18. Docs: `docs/slack-app.md` (Modify: notifier uses `chat:write` only; separate secret name).

### Verification Plan
The ticket's test rows, mutants and evidence commands (`handover/tickets/JG-3.md`).
