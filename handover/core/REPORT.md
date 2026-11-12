# CORE session report (the ONE file this session reports to the lead in; newest block on top)
Session: https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac (core modules, hadavin-sdk). Write here: a status block at least every 10 minutes (UTC and IST, running agents, what is pushed, what is stuck, what you need from the lead). Questions that need a decision keep going to handover/questions-for-lead.md as before; PULSE.md may stay as your one-line heartbeat.

## ORDER 256 received - 2026-11-12 19:02Z / 00:32 IST (next block by 19:07Z)
- Clock correction: my last three block titles said 19:05Z to 19:10Z; the machine clock read 18:55-19:00Z then. Times from now are read from `date -u`. Honest slip, no work affected.
- Applying: (A) stop rule. Q8a-1 b19 round 20 had 0 Blocker and 0 Major in BOTH reviews: no further review of minors; batch 20 will fix the r20 minors in one push, then ONE more round because it is a security path (the first clean round was r20). Q8c-1 b15 still has a Major (N1): batch 16 then continue. (B) class first in every new brief. (C) READY-TO-MERGE.md: agent ad5f13... building it now from the PR list. (E) ledger triage and (F) open questions: two agents started, both write only under handover/core/ and change no existing file. (D) rebase builders for the stacks start next, after the PR table shows the real state (queue by heavy slot).
- Running agents: 15. Review-fix builders PRH b12, P3a-2 b9, Q8b b14c; evidence runner Q8a-1 b19; promotion builders parts 2, 3, 6, 5 and AK-G2-a; helpers: ledger triage, open questions, READY-TO-MERGE table. Q8c-1 b15 evidence landed (full suite 11000 passed 13 skipped; stage 37/37; policy 350/350; fail-before 41 failed on old code), committed now.
- Pushed: part 2 first commit on wip/cloud-pd-bind (34ff7bf7). Stuck: nothing. Needs from the lead: nothing.

## Status - 2026-11-12 19:10Z / 00:40 IST (next block by 19:15Z)
- Running agents: 12. Review-fix: PRH b12, P3a-2 b9, Q8b b14c builders; Q8c-1 b15 and Q8a-1 b19 evidence runners. Promotion builders (all 5 started, 90-minute boxes, worktrees under /home/user/build): part 2 bind (wip/cloud-pd-bind), part 3 stand-ins (wip/cloud-pd-standins, waits for part 2's loopback helper), part 6 banner and demo-only guard (wip/cloud-pd-banner), part 5 reset (wip/cloud-pd-reset), AK-G2-a ledger = parts 1+4 (wip/cloud-ak-g2-a; ticket wins over demo code; it will not finish in one box).
- Pushed: only reports so far. No builder has pushed yet.
- Heavy slots: 3 max, queued through heavy.sh; load average about 3 at launch.
- Stuck: nothing. Needs from the lead: nothing.

## ORDER 255 received, promotion started - 2026-11-12 19:00Z / 00:30 IST (next block by 19:05Z)
- Running agents: 10. Review-fix: PRH b12, P3a-2 b9, Q8b b14c builders; Q8c-1 b15 and Q8a-1 b19 evidence runners. NEW promotion builders: part 2 public-bind refusal (core/promote-demo-bind -> wip/cloud-pd-bind), part 3 stand-in hosts and kind-registry test (core/promote-demo-standins -> wip/cloud-pd-standins; builds on part 2's shared loopback helper), part 6 mode banner and demo-only guard (core/promote-demo-banner -> wip/cloud-pd-banner). 90-minute boxes.
- Pushed: Q8a-1 b19 design and codebase reviews r20 (0 Blocker, 0 Major each). Not yet pushed by builders: nothing.
- Next in queue (dependency-free): AK-G2-a (parts 1+4) builder brief, then part 5 (safe reset); both launch as soon as a heavy slot and an agent slot allow. Q8a-1 b19 resolve waits for its evidence runner.
- Stuck: nothing. Needs from the lead: nothing.

## ORDER 254 step (a): overlap search - 2026-11-12 19:05Z / 00:35 IST
- Method: read-only search of hadavin-sdk against the demo head 43110e7 (agent report, ranges verified except part 1 symbols and lint.yml lines; I have NOT yet re-read the demo bodies myself).
- Part 2 refuse public bind: NO equivalent in core (no bind concept, no is_loopback_host). Promote whole. Demo: config.py 63-77, 449-474, tests test_bind_refusals.py, test_mode_safety.py 202-250.
- Part 3 loopback stand-ins and kind registry test: PARTIAL. Core has DEV_ONLY/NOT_PROD kinds (backends/table.py) and a loopback allowlist (config.py url_allowed), but four duplicated loopback sets (guard/http.py:21, llm/openai_compat.py:37, backends/table.py:68, store/postgres.py:55) and no "every kind is classified" test. Plan: extend core with one shared loopback check plus the registry test (improve before replace), not a copy.
- Part 6 mode banner and demo-only folder guard: NO code in core (rule exists only as prose); core has no tools/ or scripts/ folder and .github has only ci.yml. Promote whole, generalised (stage names demo/pilot/prod).
- Part 1 receipt and claim: NO equivalent in src. OVERLAPS my queue: ticket AK-G2 / AK-G2-a (inbound trigger, ledger, claim, lease, retry; FROZEN) and plan-v4-3 sections "Ledger" and "Claim, lease, retry". desk.py is a 2402-line monolith: the receipt pieces are about 1085-1350 plus the receipts table; must be cut out carefully. Decision: build part 1 as the AK-G2-a ledger work (one item, not two).
- Part 4 retry and gave-up state: PARTIAL. llm/retry.py has in-call backoff only (no per-key wait, no max-tries gave-up state). OVERLAPS AK-G2-a retry and AK-G15 durable queue. Promote `_MirrorWait` (29 lines, stdlib) plus the gave-up rule as a separate small module; fold into AK-G2-a.
- Part 5 safe reset: NO equivalent (P2a stop state is a different thing). Promote; demo-specific names (lead_desk.server, fakes, pid files, data/) become config.
- Queue items dropped or merged: none of my running batches overlap (they are review-fix batches). AK-G2-a and AK-G15 are not started, so parts 1 and 4 merge into them.
- Not yet checked: demo bodies outside the cited ranges; ticket bodies AK-G2/15/16 (title and grep only); core conftest and docs.
- Running agents: 5 (PRH b12, P3a-2 b9, Q8b b14c builders; Q8c-1 b15 evidence runner; Q8a-1 b19 evidence runner and design reviewer). Q8a-1 b19 codebase review r20 saved (0 Blocker, 0 Major, 3 Minor).

## ORDER 253 received (and ORDER 254 read) - 2026-11-12 18:52Z / 00:22 IST
- Running agents: 7. Builders: PRH b12 (on core/prh-b12), P3a-2 b9 (core/p3a2-b9), Q8b b14c (waiting on its own queued jobs). Q8a-1 b19 evidence runner and its two reviewers (design, codebase). Q8c-1 b15 evidence runner. Heavy queue (3 slots) is full.
- Pushed this block: handover reviews and ledger rows up to P3a-2 b8 r19, PRH b11 r11, Q8c-1 b15 design and codebase reviews r15.
- Waiting for results before the next resolve: Q8c-1 b15 evidence, Q8a-1 b19 evidence and reviews (round 20), Q8b b14c report.
- ORDER 254 (reuse the demo code, six parts): read. Public demo repo fetched read-only (branch initial-code, head 43110e7, 202 files) into /home/user/hadavin-dx/duplicate-proof-lead-desk-n8n; nothing pushed there. Plan: items in flight finish first; then step (a) search hadavin-sdk for an existing equivalent of each of the six parts and list overlaps with my queue here; then one draft PR per part on core/promote-demo-<part>, order 2, 3, 6 (mode safety) then 1, 4, 5. No part is started yet.
- Stuck: nothing. Needs from the lead: nothing now.

