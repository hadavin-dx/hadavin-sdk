---
name: fix-dont-defer-be-honest
description: "Owner rule 2026-10-29: never label a fixable problem a 'known limitation' and move on - fix it; always be brutally honest and truthful about every matter"
metadata:
  type: feedback
---

**The owner's words:** "earlier so many of them by claude agents said like known limitations and moved on, that should never happen again, i want fixing them not just slacking off or moving on" and "always brutally honest, truthful only, all the things and matters".

**Rules:**
1. A problem found is a problem fixed. This covers anything Claude or a subagent finds: a bug, a gap, a failing check, an unverified claim, a missed file.
   - Do not file it as a "known limitation", a "residual risk", "out of scope", "follow-up" or "TODO" and then move on.
   - Fix it in the same piece of work, verify the fix, and say how it was verified.
2. **The only allowed exceptions**, each stated plainly with the reason and the exact next step:
   - (a) it is physically impossible right now, for example an AWS Object Lock that not even root can lift;
   - (b) it needs the owner, for money, a login, or a decision only he can make;
   - (c) it needs a third party.

   Tell the owner, and put the item in the handoff with a date to finish it.
3. **Every subagent report counts as unverified** until checked.
   - If a subagent says "not done", "skipped" or "limitation", the main session fixes it or sends a fixer, and does not just relay the report.
   - Give subagents an explicit instruction: fix what they find, and never defer silently.
4. **Brutal honesty:**
   - Never claim done, passed or verified without evidence.
   - Say what failed, what is uncertain and what was not checked, in plain words, first.
   - No softening and no overselling.
   - If something earlier was wrong, say so and correct it.

**Why:** deferred "limitations" piled up in an earlier project, and the owner lost trust in "done" claims.

**How to apply:**
- Before calling anything done, search the work and the subagent reports for "limitation", "not done", "skipped", "TODO", "deferred", "out of scope", "not verified" and "could not". Fix each item, or classify it under exception 2(a), 2(b) or 2(c) with the reason.
- Related: [[dont-stop-keep-going]], [[fix-dont-defer-be-honest]].
