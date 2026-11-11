# Ticket PR H-b (STUB, split out of PR H by ERRATA rev 2 on 2026-11-11): a secret cut by a backslash at a line end

Status: stub written by the PR H ticket author. Not reviewed, not built. It needs its own EGM plan review before any build. Depends on PR H being merged (it reuses PR H's "find on one reading, mask on the other" step).

## What and why it was split out
A shell command or a log can break a long line with a backslash directly followed by a line end ("line continuation"). A key cut that way (`AKIA` + backslash + line feed + rest of the key) is shown on main as two halves and is not masked (PR H ticket, section 2.4, row "visible separators").

PR H rev 1 tried to mask this inside PR H. Both plan reviewers of round 1 asked for it to go (design review: "visible text, not a hidden item; inconsistent with the tab and line-break rule; turns every multi-line shell result into a two-pass text; stated over-masking"). ERRATA rev 2 of PR H moved it here. PR H itself now leaves a backslash and a line end exactly as written and lists this case under "not promised".

## What this ticket must decide (inputs for the plan review)
1. Whether the case is in scope at all, or stays "not promised" like a tab or a plain line break inside a key (D-018 white-space rule). The owner question about tabs (questions-for-lead, 15:34Z) is the same kind of decision.
2. If in scope: the reading definition (the pair is deleted in the reading used to FIND values and kept in the reading used to MASK them), an example table, the over-masking limit (two long words joined across a continuation), Windows folder paths that end in a backslash at a line end, and the cost (every multi-line shell text becomes two passes).
3. Tests: the author prototype's switch (`/home/user/build/prh-author/scratch/proto.py`, `--cont`) is a starting point only; its numbers are not independent evidence.

Proposed ledger row date for the decision: 2026-11-18.
