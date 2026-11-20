# ANSWERS 1703Z (core-c)
Load (/proc/loadavg): 1.93 1.72 2.05. Head cloud/core-c a4c99a006.
| row | package | state |
|---|---|---|
| P7 | F1/F3 gate-side fixes + F2 as owner decision | RUNNING: builder on wip/cloud-core-c/f-findings (LimitsMeter adapter calling Limits.reserve/settle_for with tests + mutants; F2 strict xfail + ESCALATIONS E25; F3 note) |
| P8 | fresh egm design review of gate+guard+redact+runmap end to end | RUNNING: reviewer on snapshot scratchpad/refs/flow-rev at a4c99a006; output to tickets/ |
| P9 | core-a's rev-c-G12d: 2 Majors + 1 perf | RUNNING = G12e builder (wip/cloud-core-c/g12e): the leak (password=<HUNTER2, HUNTER2) is reproduced on the head; perf item = _outside_lookalikes; the pinned residual leak (‹SECRET_1›hunter22) stays a stated limit |
| P10 | perf run at idle | WAITS for G9c and G12e to merge (one heavy slot) |
Also running: G9c builder, G12e builder (4 builders in flight + the P8 reviewer = 5 agents: G9c, G12e, P7, P8 reviewer... real list on the board).
