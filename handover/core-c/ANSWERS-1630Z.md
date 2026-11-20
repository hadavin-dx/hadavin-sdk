# ANSWERS 1630Z (core-c)
Load (/proc/loadavg): 4.59 3.49 2.22 on 4 cores. Merged head: cloud/core-c 0e33c0641 (one head; g2/g3 content already in it, see evidence/REC-notes.md).

| row | package | branch | sha | state |
|---|---|---|---|---|
| C1 | NO_MAP request 3 (mapping REQUIRED in bind) | cloud/core-c | c11fafb99 | DONE, merged |
| C2 | usd_cap in SPEND_REASONS | cloud/core-c | c11fafb99 | DONE, merged |
| C3 | gate honours the mark on ProviderExhausted | cloud/core-c | bfc13e45e, e05cee9f0 | DONE, merged; inert until core-b's retry layer sets the mark |
| C4 | K5 | cloud/core-c (core-a's K5 branch merged) | n/a | BLOCKED: Q17, lead must say which K5 item |
| C5 | ONE merged head | cloud/core-c | 0e33c0641 | DONE |
| C6 | grant tests re-pinned to core-b head | wip/cloud-core-c/grants | b55d21865 | DONE: 117 passed on PG16; core-a's file fails 28 on core-b head |

Agents running (4): G12d builder (G12c review fixes, /tmp/core-c-g12d), G9c builder (G9b review fixes, /tmp/core-c-g9c), G4d builder (G4c review fixes, /tmp/core-c-g4d), DOCS3 builder (root docs style fixes, /tmp/core-c-docs3). Merged since 15:00Z: G13c, G12c, G9b, G4c, G13d, docs root pass + DOCS2, gate mutant fixes, PU1 re-pin, pii recording re-key. Suites at idle on 2552bcc95: non-perf 16071 passed 2 failed (lead-file vendor string; k5 recording fixed), perf 96 passed.
