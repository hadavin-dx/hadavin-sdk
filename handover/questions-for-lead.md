# Questions for the lead


## Q1 (2026-11-05 14:3xZ / 20:0x IST) - cloud session, tickets P1, P3a, P2a, P4d
1. **New session for agent reload.** I cannot restart my own session from inside it. The egm model patch was run (grep: 12 opus / 102 sonnet / 0 inherit) but the agent list of THIS session was loaded earlier. Every Agent call sets `model` explicitly, so routing does not depend on the reload. Please confirm this is acceptable, or start a fresh session on branch core/cloud-handover and re-run `python3 handover/tools/egm_model_patch.py`.
2. **Where do the tickets go?** I wrote them to `handover/tickets/` in a local worktree of core/cloud-handover and committed locally only. I did NOT push: my session instructions name a different working branch and forbid pushing elsewhere without your explicit yes. Please say "push to core/cloud-handover" or tell me which branch. No pull request is opened.
3. **P0e memos do not exist yet** (text-folding base, store note, migration plan, file-overlap table). Each ticket states what it assumes from them and lists the unverified items under "Open points".
4. **EGM skills.** See the review notes in each ticket's review file under `handover/tickets/reviews/` for how the reviews were run (Skill tool or by hand with the egm:* reviewer agents) and why.

## Q2 (2026-11-05, after the laptop lead's message "NEXT-TERMINAL-PROMPT-2026-11-05")
1. The message repeats my instructions (no build, no pull request, tickets only, Tier A through egm-review-loop then egm-resolve, Sonnet except the three Opus skills). Nothing to change there.
2. New facts I will apply to the tickets: P1 becomes TWO pull requests (P1a, P1b); P4b is split P4b1/P4b2; money stays exact decimal in storage. **Open: which pieces belong to P1a and which to P1b?** The amendments file (A1-A9) is not on my branch yet. Until it arrives, the P1 ticket marks the split as UNVERIFIED and proposes one (see the ticket's open points). Please send the amendments or the split.
3. The message does not say whether I may push. Still NOT pushing to core/cloud-handover (see Q1.2). Tickets stay committed locally only.
4. The "start a new session" step: same answer as Q1.1.
