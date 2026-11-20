# G9: the sweep to a fixed point over the text read with its placeholders put back, at most 4 passes, refused past them (ORDER 023, escalation E10)

Status: DRAFT v1 for plan review, core-c drafter, 2026-11-20. Nothing is built. Base: cloud/core-c 5702e4fc7 (G7 fix round 6, 9d8bc580a, merged).
Every number comes from clean `git archive` copies of the base in the drafter's scratchpad (`head`, the base as is; `proto`, this design).
The shared tree was not edited. (Measurements in progress; section 9 gets filled in.)

## 0. The finding that shapes the design (measured)
THE PLAIN LOOP DOES NOT CLOSE E10. Iterating today's `_Redactor.sweep` (or `_spelled_sweep`) on its own output reaches a fixed point at the
second pass in all three reproduced cases, with the leak intact:
| case | pass 1 | pass 2, 3, 4 |
|---|---|---|
| (a2) plain values `abcdefgh`, `efghijkl`; text `abcdefghijkl` | `<SECRET_1>ijkl` | unchanged |
| (a1) F1 = V+`ab`, F2 = `xyz`+V (V = `ab9x`); raw `see xyz`+V+`ab end` | `see <BEARER_2>ab end` | unchanged |
| (b) F1 registered, `xyz<SECRET_1>ab` swept, then F2 registered | `xyz<BEARER_1>` (round 2) | unchanged after F2 is registered |
(scratch script naive.py on `head`.) The swallowed characters are no longer in any text a pass reads: a placeholder hides them. A pass that
can change these texts must read the text WITH THE PLACEHOLDERS PUT BACK. So in G9 "a pass" is: the sweep as today, then an OVERLAP CHECK
on the expanded text; the loop iterates that to a fixed point (a pass whose check finds nothing) and is bounded by 4 passes. This keeps the
lead's frame (fixed point, bound 4, refuse, no derived forms, no new quadratic cap) and adds the one thing that makes iteration see the leak.

(draft in progress: sections 1-16 follow)
