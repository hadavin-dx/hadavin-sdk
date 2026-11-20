# ANSWERS 1726Z (core-c)
Load (/proc/loadavg): 1.48 1.39 1.90. Head cloud/core-c d993b4eed.
Lead decisions 17:28 received and started (one builder each, own branch, merged in sequence with a fresh reviewer per diff):
| row | package | branch | state |
|---|---|---|---|
| Q1 | E25 (a): reply masking in the gate + put-back function; flip the F2 strict xfail | wip/cloud-core-c/q1-reply-mask | RUNNING |
| Q2 | P8 item 3 fail-closed spend, gate side (unknown worst case reserves usd_cap; Decimal(0) never free unless verified; settle every retry attempt; mark only from a verified source); worst-case-function interface note for core-b | wip/cloud-core-c/q2-spend | RUNNING |
| Q3 | G15 independent plain-substring/Aho-Corasick final net (not _Redactor machinery) | wip/cloud-core-c/q3-g15-net | RUNNING |
| Q4a | P7b LimitsMeter review fixes | wip/cloud-core-c/p7b | RUNNING |
| Q4b | P10 perf at idle | - | WAITS: whole-tree mutant runs (g12, gate, redact) in progress, then perf |
Merged this hour: G9c, G12e, G14 (head d993b4eed). Reviews done: G13d, G12d, G4d, P7, P8; docs frozen (cap).
