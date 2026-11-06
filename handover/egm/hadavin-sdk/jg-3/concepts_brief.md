> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# JG-3: chat-ops notifier (an incident summary posted as a threaded reply under the alert message, with a portal link)

* **Author:** Claude (ticket author session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06 (written about 07:50 UTC / 13:20 IST)

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill asks for six reviewer lenses run as fresh sub-agents. This session has no sub-agent tool, so none ran. A review in the same context does not count as a Goldfish review. The "Analysis" below is the author's own stress test. The independent check is the ticket review rounds (order 47 item 1: three rounds, then freeze) and the build-start review.
- **AUTO mode.** The readiness gate, the iteration loop and the handoff gate were skipped, as the brief requires. Where the skill would ask, this brief takes the option a frozen ticket already took; each such choice names its precedent under "Key decisions".
- **Sources.** LEAD-ORDERS orders 23, 27 (item 63) and 47; `tickets/AK1.md` rev 3 FROZEN (Decision 2, lines 55-63); `tickets/AK-G1.md` rev 3 (lines 96-97, 183, 194, 448); `tickets/P2d.md` rev 6 FROZEN (words section); core code read at `ce70eb5` (the last commit touching `src/`). File:line cites to code are in the design (`design.md`) and the ticket.

## Overview

Jagrat (the one showcase demo, order 47) must put an incident summary into Slack as a reply in the thread of the monitoring alert message (Datadog posts the alert; our reply sits right under it), with a link to our portal where the full incident lives. JG-3 is the core part that does the posting: one new kind, `notifier`, with a recorded (fake) backend as the neutral default and Slack as the first real backend; a second backend (e-mail, then Teams) is written as an outline with a trigger only.

Who uses it: Jagrat's incident flow (after JG-2 turns an alert into a work item and the agent writes a summary), and through it the client's on-call people, who read the reply in Slack and click through to the portal.

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **The existing channel removes every link.** The approval channel's `clean()` is documented "template-built, redacted and link-free" and strips links, images and mentions from text. A portal link put inside the summary text would be stripped. So the link cannot travel in the text. It must be a separate element our code builds from config (base URL) and a validated incident id, added after the text is cleaned, never parsed out of model text.
2. **The "outbound gate from AK-G1" does not exist as a thing to reuse.** AK-G1 has no gate of its own: its replies leave through a hook (`Hooks.deliver_reply`) that the AK-G22 recipient gate must implement, and AK-G22 has no ticket yet. AK1 says plainly that until AK-G22 merges, recipient paths (Slack posts included) go through neither gate. What does exist in code is the text choke point: `clean()` (sanitise, withhold commands, then ONE redaction through `runmap.redact_text`), which P2d hardens. JG-3 reuses that choke point, registers itself as a producer and as a recipient path, and is refused in pilot and prod until AK-G22 is wired, as AK-G1 does.
3. **Who knows the alert message's id?** A threaded reply needs the alert's channel id and message time stamp (`thread_ts`). A monitoring webhook payload very likely does not carry the Slack message id (UNVERIFIED). Finding it means reading Slack (a new read scope) or listening to Slack events (a new inbound door). That is alert intake work (JG-2, on AK-G2's door), not posting. JG-3 takes the thread reference as an input and states the gap.
4. **"Posts once" cannot be fully promised.** Slack's post call has no idempotency key that this design can rely on (UNVERIFIED). If the process stops after Slack accepted the post but before we record it, a blind retry posts twice. The honest rule: claim a record before posting; a record left in "sending" with no answer is NOT re-posted automatically; it becomes "outcome unknown" and a person looks (in the portal). Duplicates are then impossible from our side; a missing reply is possible and visible.
5. **The pattern redactor does not catch a person's name in free text.** It finds keys, e-mail addresses, card and account numbers and similar patterns (P2d words section). An incident summary written by a model may name an engineer or a customer. This is a limit to state to the owner, not hide.
6. **Rate limits.** The core retry helper caps a server's `Retry-After` at 8 seconds. Slack may ask for longer (UNVERIFIED). Sleeping in-process for a long wait blocks a run; so a long wait becomes a scheduled retry done by the `tick` housekeeping pass.
7. **One identity per function.** The approval channel and the notifier would both post with a bot token. Sharing one token mixes two functions. The notifier gets its own secret name; whether it is a separate Slack app is an owner choice.

**Counter-arguments weighed.**
- *"Just extend the approval channel with a `thread_ts` argument."* Rejected: the channel's contract is approval cards and button callbacks (`send`, `update`, `parse_decision`) and link-free text; a notifier needs a link, a thread and a durable once-only record. Bolting those on weakens the approval contract. The Slack HTTP call itself is shared (moved, behaviour-preserving), not copied.
- *"Use a no-code tool (n8n) to post to Slack."* Considered (tool ladder rung 3). The posting is plumbing, but the text must pass our redaction choke point and the once-only record is state we must own. A no-code flow may sit behind the same kind later as a backend (outline row); the default stays ours.
- *"A signed, short-lived link is safer than a plain link."* A short-lived link dies in the Slack history (useless next week); a long-lived signed link is a bearer secret in a chat that many people read. A plain link that only works after portal sign-in (AK-G17) leaks nothing but an opaque id. Chosen: auth-gated plain link; signed variant is a pending owner choice.

## Goals vs. Non-Goals

* **In-Scope Goals:** capability `notifier` with kinds `recorded` (neutral default, dev only) and `slack`; a threaded reply (`thread_ts`) to a given message; a portal link from `portal_base_url` config plus the incident id; the summary through `clean()` and a size cap; bot token through the secrets kind (mounted file in deployment), never in config; a once-only record per (tenant, incident, alert message); bounded retry with backoff and a tick step for later retries; failure never deletes or blocks the incident; the environment name ("demo") as a config value shown in the reply; pilot/prod refusal until AK-G22 is wired.
* **Out-of-Scope Non-Goals:** finding the alert message (JG-2); the portal pages and sign-in (JG-4, AK-G17); the recipient gate itself (AK-G22); the e-mail and Teams backends (outline rows only); editing or deleting a posted reply; mentions of people; any button that changes a system (approvals are JG-5 and G14).

## Alternatives Weighed

- Extend `approvals/channel.py` `Channel` with threads and links. Rejected by author: mixes approval and notice contracts; the link rule would weaken the approval text rule.
- Put the link inside the cleaned text. Rejected by author: `clean()` removes links by design.
- Automatic re-post of an unknown outcome. Rejected by author: risks a double post; a person decides.
- Signed short-lived link. Rejected by author as the default (dies in history or becomes a bearer secret); kept as an owner option.
- Sleep in-process for any `Retry-After`. Rejected by author: blocks a run; long waits go to the tick step.
- No-code flow as the default backend. Rejected by author: redaction and the once-only record are "brain" parts that stay in our code (tool ladder rung 7).

## Key Decisions & Staging for Next Steps

1. New capability `notifier`, not an extension of `channel` (precedent: AK-G1 rev 3 adds its own hook contract `deliver_reply` instead of reusing the channel; AK1 rev 3 Decision 1 "a barrier at the place parts are made").
2. Pilot/prod refusal of the `slack` notifier until AK-G22 is wired (precedent: AK-G1 rev 3 row T19 (b), blanket refusal until wiring ticket V12).
3. Once-only record with one final state and no blind re-post (precedent: AK-G2 inbound ledger "dedupe with one final state", write-ahead receipt, R368).
4. Second backend as an outline row with a named trigger (precedent: AK-G16 outline rows, e.g. V17).
5. Neutral default `recorded`, dev-only (precedent: `channel` `fake` in the dev-only table).
6. Owner-only items (separate Slack app, signed link, the names limit, pilot gate) go to PENDING LEAD with a recommendation.
