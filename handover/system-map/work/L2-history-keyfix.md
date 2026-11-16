Terms are explained in the inline key on the next line; work/GLOSSARY.md has the rest.
Inline key (added 16 Nov by the system-map session; meanings not found in any file are marked NOT RECORDED): take = one recorded run of the demo on made-up data. DECISION line N = line N of the one-store decision file (two copies exist; source unknown; the quoted sentence is NOT RECORDED, so each finding that cites one is UNVERIFIED). job keys = STORE, RETRY, NOTICE, FILTER, COUNTER, LOG, OTHER (see work/GLOSSARY.md). lane3, GO-1, K1 K2 K3 K6, Fa/Fb/Fc, B20/B90/B780, hygiene rule 19, CODE-LAST = NOT RECORDED; ignore them. "lane L3" means the helper session L3, not the parked group L of decision 3. Severity labels are the lane's own; the lead session has confirmed none. register.md: NOT-READ in this lane; a continuation owner is NOT NAMED (the earlier line saying it was fully read is withdrawn).
# Lane L2

> LEGEND (added 16 Nov 2026): a lane = one read-only audit pass over a set of files, run by one agent (lane L1, L2 ... L6; not the parked group L of decision 3). A continuation lane (L1c ...) reads what the first lane left. READ = opened fully. SKIMMED = headers or grep or first and last slice. NOT-READ = not opened or only the top (draw no conclusion from it). OWNER-ONLY = never opened (work/OWNER-ONLY.txt). Scope: real-v5 scenes 1 to 4 (decision 1). Decisions = inputs/DECISIONS-2026-11-16.md. Owner and date of each continuation lane: the studio lead, in the lead's launch message (none named yet).

## Coverage
PARTIAL: one file (register.md) was NOT-READ in this lane. No continuation lane has read it yet, and no owner is named for that.

| path | bytes | status | note |
|---|---|---|---|
| handover/demo3/FREEZE.md | 3597 | READ | read fully (lines wider than 700 chars were cut once; whether the cut text was read afterwards is NOT RECORDED) |
| handover/demo3/MATRIX-1.md | 23617 | READ | read fully (lines wider than 1200 chars cut once: 144, 187) |
| handover/demo3/ORDERS.md | 54514 | READ | read fully; lines 1-140 wider than 420 re-read from col 421; lines 141-203 to col 2200 |
| handover/demo3/REPORT.md | 10715 | READ | read fully; tails of lines wider than 500 re-read |
| handover/demo3/WINDOWS-RUN-1.md | 11823 | READ | read fully |
| handover/demo3/kill/COMPARE-demo.md | 1900 | READ | read fully |
| handover/demo3/kill/PLAN-GO1.md | 940 | READ | read fully |
| handover/demo3/kill/PLAN-V3-ALERT.md | 4196 | READ | read fully |
| handover/demo3/kill/PLAN.md | 4409 | READ | read fully |
| handover/demo3/kill/RESULTS.md | 12859 | READ | read fully |
| handover/demo3/kill/analyze.py | 3049 | READ | read fully |
| handover/demo3/kill/data/last-run-b.out | 0 | READ | run output; empty (0 bytes), nothing to read |
| handover/demo3/kill/data/last-run-d.out | 0 | READ | run output; empty (0 bytes), nothing to read |
| handover/demo3/kill/data/last-run-e.out | 979 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-g.out | 471 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-h.out | 948 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-i.out | 958 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-j.out | 457 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-k.out | 619 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-l.out | 677 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-n.out | 710 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-p0.out | 710 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-p1.out | 718 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-p2.out | 676 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-q0.out | 580 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-q1.out | 580 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-q2.out | 560 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/last-run-q3.out | 580 | SKIMMED | run output; first 300 chars read |
| handover/demo3/kill/data/results.jsonl | 85243 | SKIMMED | parsed by own script (126 labels, flows, errors, go1 rows read); individual rows not read one by one |
| handover/demo3/kill/data/run_all.progress | 5339 | READ | read fully; cross-checked against results.jsonl labels |
| handover/demo3/kill/data/runs/c1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1/events.jsonl | 584 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1L/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1L/events.jsonl | 2380 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1L/mails.jsonl | 521 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1L/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1L/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1b/events.jsonl | 190 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1c/events.jsonl | 5049 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1c/mails.jsonl | 1195 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1d/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1d/events.jsonl | 615 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1d/mails.jsonl | 86 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1d/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/c1d/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cb/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cb/events.jsonl | 191 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cb/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cb/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cp/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cp/events.jsonl | 1052 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cp/mails.jsonl | 175 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cp/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cp/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cs/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cs/events.jsonl | 612 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cs/mails.jsonl | 86 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cs/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/cs/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fb1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fb1/events.jsonl | 615 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fb1/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fb1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fb1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/events.jsonl | 705 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/events.jsonl | 704 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/events.jsonl | 706 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fc1c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr1/events.jsonl | 2241 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr1/mails.jsonl | 107 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr2/events.jsonl | 2238 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr2/mails.jsonl | 107 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr3/events.jsonl | 2238 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr3/mails.jsonl | 107 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ferr3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa1/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa1/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa2/events.jsonl | 619 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa2/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa3/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa3/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffa3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/events.jsonl | 888 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/events.jsonl | 891 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/events.jsonl | 891 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffb3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc1/events.jsonl | 554 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc1/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc2/events.jsonl | 556 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc2/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc3/events.jsonl | 555 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc3/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ffc3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg1/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg1/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg2/events.jsonl | 621 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg2/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg3/events.jsonl | 621 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg3/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg4/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg4/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg4/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg4/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg4/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg5/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg5/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg5/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg5/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg5/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg6/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg6/events.jsonl | 621 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg6/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg6/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg6/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg7/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg7/events.jsonl | 620 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg7/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg7/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fjg7/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3a/events.jsonl | 990 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3a/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3b/events.jsonl | 990 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3b/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3c/events.jsonl | 991 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3c/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk3c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6a/events.jsonl | 1108 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6a/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6b/events.jsonl | 1109 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6b/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6c/events.jsonl | 1109 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6c/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fk6c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err1/events.jsonl | 1774 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err1/mails.jsonl | 110 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err2/events.jsonl | 1774 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err2/mails.jsonl | 109 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err3/events.jsonl | 1771 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err3/mails.jsonl | 109 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45err3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1a/events.jsonl | 843 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1a/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1b/events.jsonl | 842 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1b/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1c/events.jsonl | 844 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1c/mails.jsonl | 90 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1d/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1d/events.jsonl | 842 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1d/mails.jsonl | 90 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1d/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1d/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1e/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1e/events.jsonl | 842 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1e/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1e/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k1e/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2a/events.jsonl | 1013 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2a/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2b/events.jsonl | 1013 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2b/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2c/events.jsonl | 1015 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2c/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2d/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2d/events.jsonl | 1017 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2d/mails.jsonl | 91 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2d/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2d/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2e/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2e/events.jsonl | 1018 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2e/mails.jsonl | 90 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2e/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k2e/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3a/events.jsonl | 1013 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3a/mails.jsonl | 122 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3b/events.jsonl | 511 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3c/events.jsonl | 1010 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3c/mails.jsonl | 122 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3d/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3d/events.jsonl | 1012 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3d/mails.jsonl | 122 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3d/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3d/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3e/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3e/events.jsonl | 1010 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3e/mails.jsonl | 121 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3e/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3e/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3f/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3f/events.jsonl | 1011 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3f/mails.jsonl | 121 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3f/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k3f/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6a/events.jsonl | 1134 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6a/mails.jsonl | 212 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6b/events.jsonl | 1132 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6b/mails.jsonl | 213 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6c/crm.log | 849 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6c/smtp.log | 655 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6c/stage.log | 853 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6d/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6d/events.jsonl | 1134 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6d/mails.jsonl | 213 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6d/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/fl45k6d/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ft14n/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ft14n/events.jsonl | 191 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ft14n/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/ft14n/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/creds-lane.json | 460 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/events.jsonl | 1059 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/mails.jsonl | 221 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/n8n.log | 4836 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-b90/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/creds-lane.json | 460 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/events.jsonl | 1108 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/mails.jsonl | 219 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/n8n.log | 9691 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/creds-lane.json | 460 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/events.jsonl | 1113 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/mails.jsonl | 221 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/n8n.log | 9691 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-fix-ks2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/creds-lane.json | 459 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/events.jsonl | 1107 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/mails.jsonl | 218 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/n8n.log | 9691 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/go1-old-ks/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/i1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/i1/events.jsonl | 1514 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/i1/mails.jsonl | 327 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/i1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/i1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j0/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j0/events.jsonl | 612 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j0/mails.jsonl | 85 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j0/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j0/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1a/events.jsonl | 2865 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1a/mails.jsonl | 630 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1b/events.jsonl | 2867 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1b/mails.jsonl | 631 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1c/events.jsonl | 2865 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1c/mails.jsonl | 631 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j1c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2a/events.jsonl | 3031 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2a/mails.jsonl | 632 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2b/events.jsonl | 3032 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2b/mails.jsonl | 628 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2c/events.jsonl | 3033 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2c/mails.jsonl | 632 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j2c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3a/events.jsonl | 3026 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3a/mails.jsonl | 661 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3b/events.jsonl | 3026 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3b/mails.jsonl | 663 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3c/events.jsonl | 3024 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3c/mails.jsonl | 661 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j3c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6a/events.jsonl | 3142 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6a/mails.jsonl | 748 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6b/events.jsonl | 3146 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6b/mails.jsonl | 748 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6c/events.jsonl | 3146 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6c/mails.jsonl | 750 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/j6c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb1/events.jsonl | 616 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb1/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb2/events.jsonl | 617 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb2/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb3/events.jsonl | 617 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb3/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jb3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jcp2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jcp2/events.jsonl | 1066 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jcp2/mails.jsonl | 180 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jcp2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jcp2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je1/events.jsonl | 15078 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je2/events.jsonl | 15066 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/je2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa/events.jsonl | 617 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa2/events.jsonl | 621 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa2/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa3/events.jsonl | 621 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa3/mails.jsonl | 87 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfa3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/events.jsonl | 885 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/mails.jsonl | 204 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/events.jsonl | 889 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/mails.jsonl | 206 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/events.jsonl | 889 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfb3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc/events.jsonl | 1179 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/events.jsonl | 1150 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/mails.jsonl | 227 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/events.jsonl | 1149 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/mails.jsonl | 229 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/events.jsonl | 1151 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/mails.jsonl | 227 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/smtp.ctl | 2 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc1c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc2/events.jsonl | 1181 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc2/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc3/events.jsonl | 1186 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc3/smtp.ctl | 13 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jfc3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg1/events.jsonl | 1056 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg1/mails.jsonl | 195 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg2/events.jsonl | 1055 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg2/mails.jsonl | 194 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg3/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg3/events.jsonl | 1057 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg3/mails.jsonl | 196 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg3/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/jg3/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1a/events.jsonl | 2754 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1a/mails.jsonl | 632 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1b/events.jsonl | 1690 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1b/mails.jsonl | 327 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/k1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/events.jsonl | 1145 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/mails.jsonl | 206 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/smtp2.ctl | 19 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/events.jsonl | 1143 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/mails.jsonl | 206 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/smtp2.ctl | 19 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3a2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/events.jsonl | 1033 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/mails.jsonl | 211 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b20a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/events.jsonl | 1239 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/mails.jsonl | 332 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/events.jsonl | 1239 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/mails.jsonl | 332 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/events.jsonl | 1238 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/mails.jsonl | 332 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3b90c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/events.jsonl | 1340 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/smtp2.ctl | 34 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/events.jsonl | 1342 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/smtp2.ctl | 34 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v3c2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/events.jsonl | 1144 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/smtp2.ctl | 19 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/events.jsonl | 1143 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/smtp2.ctl | 19 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4a2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/events.jsonl | 1091 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/mails.jsonl | 213 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/smtp2.ctl | 21 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b780a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/events.jsonl | 1033 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/mails.jsonl | 211 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/events.jsonl | 1033 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/mails.jsonl | 211 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/events.jsonl | 1032 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/mails.jsonl | 211 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4b90c/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/events.jsonl | 1340 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/smtp2.ctl | 34 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/events.jsonl | 1343 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/smtp2.ctl | 34 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4c2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1a/events.jsonl | 833 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1a/mails.jsonl | 89 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1b/events.jsonl | 833 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1b/mails.jsonl | 89 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k1b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k2a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k2a/events.jsonl | 1002 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k2a/mails.jsonl | 88 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k2a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k2a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3a/events.jsonl | 997 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3a/mails.jsonl | 120 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3b/events.jsonl | 998 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3b/mails.jsonl | 119 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k3b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6a/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6a/events.jsonl | 1117 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6a/mails.jsonl | 208 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6a/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6a/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6b/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6b/events.jsonl | 1117 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6b/mails.jsonl | 209 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6b/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4k6b/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/events.jsonl | 1081 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/mails.jsonl | 207 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks1/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/crm.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/events.jsonl | 1081 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/mails.jsonl | 209 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/smtp.ctl | 11 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/smtp.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/smtp2.ctl | 20 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/runs/v4ks2/stage.log | 0 | SKIMMED | run log; folder listing, e-mail-domain and secret-pattern grep over all run folders; c1, c1c opened |
| handover/demo3/kill/data/trace-b90-report.md | 5350 | READ | read fully |
| handover/demo3/kill/fakes.py | 12413 | READ | read fully (columns past 200 cut) |
| handover/demo3/kill/flows-go1/V4-README.md | 2178 | READ | read fully |
| handover/demo3/kill/flows-go1/mf-form.json | 7971 | READ | read fully (own JSON dump of every node; position fields not shown) |
| handover/demo3/kill/flows-go1/mf-hook.json | 7986 | READ | read fully (own JSON dump; diffed against mf-form) |
| handover/demo3/kill/flows-go1/mf-recovery.json | 8446 | READ | read fully (own JSON dump of every node) |
| handover/demo3/kill/flows-go1/mf-sub-crm-mail.json | 13751 | READ | read fully (own JSON dump of every node) |
| handover/demo3/kill/flows-go1/mf_leads.sql | 1437 | READ | read fully |
| handover/demo3/kill/harness.py | 16672 | READ | read fully |
| handover/demo3/kill/make_all.sh | 946 | READ | read fully |
| handover/demo3/kill/make_go1.py | 1333 | READ | read fully |
| handover/demo3/kill/make_results.py | 2468 | READ | read fully |
| handover/demo3/kill/make_results_l45.py | 1228 | READ | read fully |
| handover/demo3/kill/make_results_v.py | 860 | READ | read fully |
| handover/demo3/kill/prepare_probe.py | 1406 | READ | read fully |
| handover/demo3/kill/run_all.sh | 598 | READ | read fully |
| handover/demo3/kill/run_b.sh | 957 | READ | read fully |
| handover/demo3/kill/run_c.sh | 509 | READ | read fully |
| handover/demo3/kill/run_d.sh | 1410 | READ | read fully |
| handover/demo3/kill/run_e.sh | 367 | READ | read fully |
| handover/demo3/kill/run_f.sh | 511 | READ | read fully |
| handover/demo3/kill/run_g.sh | 1399 | READ | read fully |
| handover/demo3/kill/run_h.sh | 870 | READ | read fully |
| handover/demo3/kill/run_i.sh | 836 | READ | read fully |
| handover/demo3/kill/run_j.sh | 637 | READ | read fully |
| handover/demo3/kill/run_k.sh | 909 | READ | read fully |
| handover/demo3/kill/run_l.sh | 723 | READ | read fully |
| handover/demo3/kill/run_m.sh | 606 | READ | read fully |
| handover/demo3/kill/run_n.sh | 788 | READ | read fully |
| handover/demo3/kill/run_p.sh | 875 | READ | read fully |
| handover/demo3/kill/run_q.sh | 582 | READ | read fully |
| handover/demo3/kill/run_r.sh | 605 | READ | read fully |
| handover/demo3/kill/v3.py | 4676 | READ | read fully |
| handover/demo3/questions-for-lead.md | 3227 | READ | read fully |
| handover/demo3/register.md | 67606 | NOT-READ | partial: lines 1-140 read to col 520; lines 141-403 only rows not marked closed (col 330) and closed rows (col 230); tails unseen; stale-row count taken by grep |

## Components
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L2-C-001 | flows-go1 main frame (4 n8n flows plus table) | the take's front door, claim, CRM, mail, recovery and alert | `handover/demo3/kill/flows-go1/mf-form.json:2 "Lead desk main frame: form entry"` | STORE; RETRY; NOTICE |
| L2-C-002 | kill harness (harness.py, v3.py, fakes.py) | runs the four flows against fake CRM, fake stage and fake SMTP, kills n8n at named points, counts outside n8n | `handover/demo3/kill/harness.py:1 "lane3 kill script driver"` | LOG; COUNTER |
| L2-C-003 | result builders (make_*.py, analyze.py, make_all.sh) | turn results.jsonl into RESULTS.md | `handover/demo3/kill/make_all.sh:2 "Builds RESULTS.md from results.jsonl"` | LOG; COUNTER |
| L2-C-004 | queue scripts run_*.sh (17 files) | run the case lists one after another | `handover/demo3/kill/run_all.sh:2 "the whole sequence, one run at a time"` | RETRY; OTHER |
| L2-C-005 | GO-1 fix builder make_go1.py | adds the n8n start trigger plus one SQL to the v4 recovery flow | `handover/demo3/kill/make_go1.py:2 "Adds to mf-recovery"` | RETRY; NOTICE |
| L2-C-006 | lane3 order and report documents (ORDERS, REPORT, register, FREEZE, MATRIX-1, WINDOWS-RUN-1, questions-for-lead) | instructions and status of the product-test lane, mostly about the desk repo, not the take | `handover/demo3/ORDERS.md:1 "ORDERS for cloud session 3"` | LOG; OTHER |

## Stores
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-S-001 | Postgres table mf_leads | claim and state of every lead | owner of STORE per DECISION | Claim insert and updates from the four flows | rows read by Stored, sweep, independent count | N/A: table | N/A: table | N/A: table | primary key lead_key plus claim_token and state checks | N/A: table (audit = lifecycle rows per DECISION line 16) | credential name n8n-publish-pg; harness reads as database user postgres | harness.py kill points K1 K2 K3 K6, Fa Fb Fc, error, burst | all four flows | `handover/demo3/kill/flows-go1/mf_leads.sql:4 "CREATE TABLE mf_leads("`; `handover/demo3/kill/flows-go1/mf_leads.sql:5 "lead_key"` | STORE |
| L2-S-002 | n8n internal data (workflows, credentials, execution history) | n8n own state | owner per DECISION line 14: the same Postgres, own schema | n8n import commands in the harness | n8n process | N/A: engine | N/A: engine | N/A: engine | N/A: engine | execution history OFF in the flows | n8n process; per-run encryption key generated by n8n | ALL kill runs ran it on the default SQLite file, not Postgres (CONFLICT WITH DECISION line 14) | n8n | `handover/demo3/kill/RESULTS.md:40 "n8n_folder:email=n8nhome/.n8n/database.sqlite-wal"`; `handover/demo3/kill/harness.py:31 "def env_n8n(home):"` | STORE; LOG |
| L2-S-003 | stage journal (fake, in memory) | stand-in for the model-call write-ahead guard | real owner is stage.journal, NOT VISIBLE: qualify_stage.py | POST /qualify | label, repeat answer | N/A: fake | N/A: fake | N/A: fake | journal keyed by lead | events.jsonl | N/A: fake | RESULTS Part 1 column model_calls | harness only | `handover/demo3/kill/fakes.py:137 "requests, model_calls, journal, lock"` | STORE; COUNTER |
| L2-S-004 | fake CRM rows (in memory) | stand-in for the client CRM | client CRM (HubSpot) in the take | POST /upsert /create | GET /rows | N/A: fake | N/A: fake | N/A: fake | match on lead id or e-mail | events.jsonl | N/A: fake | K2 Fa | harness only | `handover/demo3/kill/fakes.py:75 "rows, lock, ctl_path"` | STORE |
| L2-S-005 | events.jsonl and mails.jsonl per run | fake servers record every event and every stored mail; the harness counts from them | none in the take | fakes | analyze, make_results, harness counts | N/A: file | N/A: file | N/A: file | N/A: file | itself | file owner | harness.py count() | harness, analyze | `handover/demo3/kill/fakes.py:18 "events.jsonl"`; `handover/demo3/kill/fakes.py:265 "mails.jsonl"` | LOG; COUNTER |
| L2-S-006 | results.jsonl (one JSON line per run) | the raw result record of 126 labels | own file; committed copy is handover/demo3/kill/data/results.jsonl | harness.py and v3.py append | make_results*.py read | N/A: file | N/A: file | N/A: file | label may repeat (c1 appears 3 times; last record wins in the builders) | itself | file owner | none | make_results.py, make_results_v.py, make_results_l45.py, analyze.py | `handover/demo3/kill/harness.py:18 "/home/user/work/kill"`; `handover/demo3/kill/make_results.py:19 "results.jsonl"` | LOG |
| L2-S-007 | RESULTS.md (generated) | second view of results.jsonl | none (derived) | make_all.sh | readers | N/A: file | N/A: file | N/A: file | regenerated each time | itself | file owner | none | REPORT.md calls it THE results file | `handover/demo3/REPORT.md:48 "THE results file"` | LOG |
| L2-S-008 | run_all.progress (queue progress lines) | third record of the same runs (one line per finished run) | none | queue scripts append | people read it | N/A: file | N/A: file | N/A: file | N/A: file | itself | file owner | none | REPORT.md names it the truth for runs | `handover/demo3/REPORT.md:47 "the truth is"` | LOG |
| L2-S-009 | control files crm.ctl stage.ctl smtp.ctl smtp2.ctl | fault switches the harness writes and the fakes read | none | harness | fakes | N/A: file | N/A: file | N/A: file | N/A: file | N/A: file | file owner | all fault runs | fakes | `handover/demo3/kill/fakes.py:24 "def read_ctl(path):"` | OTHER |
| L2-S-010 | run folders data/runs/<label> (127 folders) | raw logs per run | none | harness | readers | N/A: files | N/A: files | N/A: files | N/A: files | itself | file owner | none | people | `handover/demo3/REPORT.md:51 "runs/<label>/"` | LOG |
| L2-S-011 | register.md (agent register) | live list of agents and jobs required by the supervision rule | none | lane3 session | lead | N/A: file | N/A: file | N/A: file | N/A: file | itself | file owner | none | lead | `handover/demo3/REPORT.md:47 "rows for runs e to l are stale"` | LOG; OTHER |

## Workflows
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-W-001 | mf-form (form entry) | receive a form submission, claim it, run the sub-workflow, answer the caller | owner of this job per DECISION | POST /webhook/mf-form with submission_id, email, name | JSON verdict; row in mf_leads | caller sees n8n_error false and a verdict; no error branch | none in the flow; caller resends | N/A: no timeout set | claim insert ON CONFLICT DO NOTHING | execution log not saved (settings none) | n8n-publish-pg | harness send() default path | callers of the take | `handover/demo3/kill/flows-go1/mf-form.json:7 "mf-form"`; `handover/demo3/kill/flows-go1/mf-form.json:424 "saveDataSuccessExecution"` | STORE; FILTER; LOG |
| L2-W-002 | mf-hook (e-mail-style entry) | same as mf-form for a second source | DUPLICATE of L2-W-001 (see FD-004) | POST /webhook/mf-hook with message_id, from_email, from_name | same as mf-form | same as mf-form | none | N/A: no timeout set | same as mf-form | execution log not saved | n8n-publish-pg | NEVER POSTED by any harness case: only listed in FLOWS | unknown | `handover/demo3/kill/flows-go1/mf-hook.json:7 "mf-hook"`; `handover/demo3/kill/harness.py:26 "FLOWS = "` | STORE; FILTER |
| L2-W-003 | mf-sub-crm-mail (sub-workflow) | stage call, CRM upsert, mail, state marks | owner of this job per DECISION | lead_key, claim_token, email from caller | outcome done, unknown, stage_failed or lost_claim | error outputs go to OutStage or MarkUnknown*; row state guards | node retry 3 tries on Qualify and CrmUpsert; mail retry off | stage 15 s default via MF_STAGE_TIMEOUT_MS; CRM 15 s; mail: no timeout setting (V4-README) | token plus state conditions on every write; keyed CRM upsert | execution log not saved | n8n-publish-pg, mf-mail-smtp | all kill points | form, hook, recovery | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:36 "maxTries"`; `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:230 "retryOnFail"` | STORE; RETRY; NOTICE |
| L2-W-004 | mf-recovery (every 30 s plus start event) | re-run stuck leads, mark failed, send and mark alerts, clear stale alert claims at start | owner of this job per DECISION | schedule 30 s; n8n init event | re-run of the sub-workflow; alert mails; state changes | onError continueRegularOutput on database nodes; AlertSend error goes to AlertBackoff | sweep every 30 s, at most 3 attempts per lead; alert backoff 60 s to 300 s | lease 120 s; alert claim 720 s | SKIP LOCKED plus tokens | execution log not saved | n8n-publish-pg, mf-mail-smtp | all kill points, v3 A B20 B90 B780 C KS cases | n8n schedule | `handover/demo3/kill/flows-go1/mf-recovery.json:10 "secondsInterval"`; `handover/demo3/kill/flows-go1/mf-recovery.json:124 "720 seconds"` | RETRY; NOTICE; FILTER |

## Workflow walk
| id | flow | node | type | trigger or branch | error path | retry or timeout | on kill or restart | on duplicate | on out-of-order | on empty or huge input | writes where | person sees | identity | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-WK-001 | mf-form | Receive | webhook | web request to /webhook/mf-form | N/A: entry node; reply is by respond nodes | N/A: no retry setting | caller gets no reply; caller must resend; row not yet written | second request reaches Claim; Claim decides | UNVERIFIED | empty body gives empty lead_key (see Valid) | N/A: reads only | caller sees JSON verdict | n8n webhook (no auth set in the file) | `handover/demo3/kill/flows-go1/mf-form.json:12 "n8n-nodes-base.webhook"` |
| L2-WK-002 | mf-form | Item | set | after Receive | no error branch | N/A | same as Receive | N/A: pure mapping | UNVERIFIED | missing field gives undefined, passed on | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-form.json:47 "n8n-nodes-base.set"` |
| L2-WK-003 | mf-form | Valid | set | after Item | no error branch; regex only checks shape | N/A | same as Receive | N/A | UNVERIFIED | empty e-mail fails regex so valid=false and lead goes to review | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-form.json:87 "n8n-nodes-base.set"` |
| L2-WK-004 | mf-form | Claim | postgres | after Valid | alwaysOutputData true: a database error is not routed; UNVERIFIED what n8n does on a Postgres error here | no retry set | kill before the insert: no row, caller resends; kill after: row exists (processing) and the recovery sweep re-runs it after 120 s | ON CONFLICT DO NOTHING: second insert returns zero rows, so Claimed is false and Stored answers | two different flows with the same lead_key share one key space (form id and mail id); UNVERIFIED if ids collide | invalid e-mail gives state review, attempts 0 | mf_leads row (Postgres) insert (claim); lease 120 s | nobody | credential name n8n-publish-pg (one credential for every Postgres node) | `handover/demo3/kill/flows-go1/mf-form.json:103 "n8n-nodes-base.postgres"` |
| L2-WK-005 | mf-form | Claimed | if | after Claim | N/A: if node | N/A | N/A | true branch: we own the claim; false branch: duplicate | UNVERIFIED | empty item (conflict) goes to false branch | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-form.json:142 "n8n-nodes-base.if"` |
| L2-WK-006 | mf-form | IsProcessing | if | true branch of Claimed | N/A: if node | N/A | N/A | N/A | UNVERIFIED | state review goes to ReplyReview | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-form.json:173 "n8n-nodes-base.if"` |
| L2-WK-007 | mf-form | SubInput | set | true branch of IsProcessing | no error branch | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-form.json:207 "n8n-nodes-base.set"` |
| L2-WK-008 | mf-form | RunSub | executeWorkflow | after SubInput | no onError set: a failing sub-workflow fails this run; row stays processing until the sweep | no retry set | kill inside the sub-workflow: row stays processing, sweep re-runs after lease | N/A | UNVERIFIED | N/A | N/A: sub-workflow writes | caller waits (waitForSubWorkflow true) | n8n | `handover/demo3/kill/flows-go1/mf-form.json:228 "n8n-nodes-base.executeWorkflow"` |
| L2-WK-009 | mf-form | ReplyRan | respondToWebhook | after RunSub | N/A | N/A | caller gets no reply if n8n dies; row state already written | N/A | UNVERIFIED | unknown outcome maps to processing | N/A | caller sees verdict new/unknown/processing | n8n | `handover/demo3/kill/flows-go1/mf-form.json:244 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-010 | mf-form | ReplyReview | respondToWebhook | false branch of IsProcessing | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A | caller sees verdict review; NO mail or alert goes to a person (see finding) | n8n | `handover/demo3/kill/flows-go1/mf-form.json:260 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-011 | mf-form | Stored | postgres | false branch of Claimed | alwaysOutputData true; no error branch | no retry set | N/A: read only | this is the duplicate answer path: returns stored state and repeat true | UNVERIFIED | no row found gives verdict processing | N/A: reads only | nobody | n8n-publish-pg (same credential) | `handover/demo3/kill/flows-go1/mf-form.json:276 "n8n-nodes-base.postgres"` |
| L2-WK-012 | mf-form | ReplyStored | respondToWebhook | after Stored | N/A | N/A | N/A | answers with the stored state; no second CRM row or mail | UNVERIFIED | N/A | N/A | caller sees stored verdict | n8n | `handover/demo3/kill/flows-go1/mf-form.json:299 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-013 | mf-hook | Receive | webhook | web request to /webhook/mf-hook | N/A: entry node; reply is by respond nodes | N/A: no retry setting | caller gets no reply; caller must resend; row not yet written | second request reaches Claim; Claim decides | UNVERIFIED | empty body gives empty lead_key (see Valid) | N/A: reads only | caller sees JSON verdict | n8n webhook (no auth set in the file) | `handover/demo3/kill/flows-go1/mf-hook.json:12 "n8n-nodes-base.webhook"` |
| L2-WK-014 | mf-hook | Item | set | after Receive | no error branch | N/A | same as Receive | N/A: pure mapping | UNVERIFIED | missing field gives undefined, passed on | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:47 "n8n-nodes-base.set"` |
| L2-WK-015 | mf-hook | Valid | set | after Item | no error branch; regex only checks shape | N/A | same as Receive | N/A | UNVERIFIED | empty e-mail fails regex so valid=false and lead goes to review | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:87 "n8n-nodes-base.set"` |
| L2-WK-016 | mf-hook | Claim | postgres | after Valid | alwaysOutputData true: a database error is not routed; UNVERIFIED what n8n does on a Postgres error here | no retry set | kill before the insert: no row, caller resends; kill after: row exists (processing) and the recovery sweep re-runs it after 120 s | ON CONFLICT DO NOTHING: second insert returns zero rows, so Claimed is false and Stored answers | two different flows with the same lead_key share one key space (form id and mail id); UNVERIFIED if ids collide | invalid e-mail gives state review, attempts 0 | mf_leads row (Postgres) insert (claim); lease 120 s | nobody | credential name n8n-publish-pg (one credential for every Postgres node) | `handover/demo3/kill/flows-go1/mf-hook.json:103 "n8n-nodes-base.postgres"` |
| L2-WK-017 | mf-hook | Claimed | if | after Claim | N/A: if node | N/A | N/A | true branch: we own the claim; false branch: duplicate | UNVERIFIED | empty item (conflict) goes to false branch | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:142 "n8n-nodes-base.if"` |
| L2-WK-018 | mf-hook | IsProcessing | if | true branch of Claimed | N/A: if node | N/A | N/A | N/A | UNVERIFIED | state review goes to ReplyReview | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:173 "n8n-nodes-base.if"` |
| L2-WK-019 | mf-hook | SubInput | set | true branch of IsProcessing | no error branch | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | nobody | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:207 "n8n-nodes-base.set"` |
| L2-WK-020 | mf-hook | RunSub | executeWorkflow | after SubInput | no onError set: a failing sub-workflow fails this run; row stays processing until the sweep | no retry set | kill inside the sub-workflow: row stays processing, sweep re-runs after lease | N/A | UNVERIFIED | N/A | N/A: sub-workflow writes | caller waits (waitForSubWorkflow true) | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:228 "n8n-nodes-base.executeWorkflow"` |
| L2-WK-021 | mf-hook | ReplyRan | respondToWebhook | after RunSub | N/A | N/A | caller gets no reply if n8n dies; row state already written | N/A | UNVERIFIED | unknown outcome maps to processing | N/A | caller sees verdict new/unknown/processing | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:244 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-022 | mf-hook | ReplyReview | respondToWebhook | false branch of IsProcessing | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A | caller sees verdict review; NO mail or alert goes to a person (see finding) | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:260 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-023 | mf-hook | Stored | postgres | false branch of Claimed | alwaysOutputData true; no error branch | no retry set | N/A: read only | this is the duplicate answer path: returns stored state and repeat true | UNVERIFIED | no row found gives verdict processing | N/A: reads only | nobody | n8n-publish-pg (same credential) | `handover/demo3/kill/flows-go1/mf-hook.json:276 "n8n-nodes-base.postgres"` |
| L2-WK-024 | mf-hook | ReplyStored | respondToWebhook | after Stored | N/A | N/A | N/A | answers with the stored state; no second CRM row or mail | UNVERIFIED | N/A | N/A | caller sees stored verdict | n8n | `handover/demo3/kill/flows-go1/mf-hook.json:299 "n8n-nodes-base.respondToWebhook"` |
| L2-WK-025 | mf-sub-crm-mail | SubIn | executeWorkflowTrigger | called by RunSub of form, hook, recovery | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:9 "n8n-nodes-base.executeWorkflowTrigger"` |
| L2-WK-026 | mf-sub-crm-mail | Qualify | httpRequest | after SubIn | error output goes to OutStage (stage_failed); row stays processing | retryOnFail true, 3 tries, 1000 ms apart; timeout from MF_STAGE_TIMEOUT_MS (default 15000) | kill during the call: sweep re-runs; the stage journal prevents a second model call (fake in tests; real stage NOT VISIBLE) | stage repeats answer from its journal | UNVERIFIED | empty lead_key sends an empty request (phantom, see finding) | stage.journal (real, NOT VISIBLE: qualify_stage.py) | nobody | HTTP to MF_STAGE_URL, no credential in the node | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:29 "n8n-nodes-base.httpRequest"` |
| L2-WK-027 | mf-sub-crm-mail | LabelOk | if | after Qualify | N/A: if node | N/A | N/A | N/A | UNVERIFIED | label other than hot/warm/cold or unknown_model true goes to OutStage | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:65 "n8n-nodes-base.if"` |
| L2-WK-028 | mf-sub-crm-mail | CrmUpsert | httpRequest | true branch of LabelOk | error output goes to OutStage | retryOnFail true, 3 tries, 1000 ms apart; timeout 15000 ms | kill after CRM stored, before answer: sweep re-runs; keyed upsert gives one CRM row (K2 tests) | upsert is keyed on lead id; the fake also matches on e-mail | UNVERIFIED | empty lead id gives phantom CRM row (F-REC-EMPTY, old flows) | client CRM (HubSpot in the take; fake CRM in tests) | nobody | HTTP to MF_CRM_URL, no credential in the node | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:85 "n8n-nodes-base.httpRequest"` |
| L2-WK-029 | mf-sub-crm-mail | SetCrmId | postgres | after CrmUpsert | alwaysOutputData true; no error branch | no retry set | kill before: CRM row exists, crm_id empty; sweep repeats the keyed upsert | token plus state check: only the owner of the claim writes | UNVERIFIED | N/A | mf_leads row (Postgres) crm_id | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:105 "n8n-nodes-base.postgres"` |
| L2-WK-030 | mf-sub-crm-mail | OwnsClaim1 | if | after SetCrmId | N/A: if node | N/A | N/A | zero rows means another run took the claim: OutLost | UNVERIFIED | N/A | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:144 "n8n-nodes-base.if"` |
| L2-WK-031 | mf-sub-crm-mail | MailClaim | postgres | true branch of OwnsClaim1 | alwaysOutputData true; no error branch | no retry set | kill after this write and before the mail: row has mail_sent true and no mail: ends unknown with an alert (K3 tests) | mail_sent=false condition: second run gets zero rows | UNVERIFIED | N/A | mf_leads row (Postgres) mail_sent (write-ahead before the send) | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:160 "n8n-nodes-base.postgres"` |
| L2-WK-032 | mf-sub-crm-mail | MailRowBack | if | after MailClaim | N/A: if node | N/A | N/A | zero rows goes to MarkUnknownB | UNVERIFIED | N/A | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:199 "n8n-nodes-base.if"` |
| L2-WK-033 | mf-sub-crm-mail | SendMail | emailSend | true branch of MailRowBack | error output goes to MarkUnknownA | retryOnFail false (deliberate: no second mail) | kill after the mail was stored: unknown plus alert (K6 tests) | no second send: retry off and mail_sent set before | UNVERIFIED | N/A | intake mailbox via SMTP; credential mf-mail-smtp | intake mailbox gets one mail | credential name mf-mail-smtp | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:218 "n8n-nodes-base.emailSend"` |
| L2-WK-034 | mf-sub-crm-mail | MarkDone | postgres | success of SendMail | alwaysOutputData true; no error branch | no retry set | kill after mail and before this write: unknown plus alert | token plus state check | UNVERIFIED | N/A | mf_leads row (Postgres) state done | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:242 "n8n-nodes-base.postgres"` |
| L2-WK-035 | mf-sub-crm-mail | MarkUnknownA | postgres | error of SendMail | alwaysOutputData true | no retry set | N/A | token plus state check | UNVERIFIED | N/A | mf_leads row (Postgres) state unknown | alert follows from the sweep | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:265 "n8n-nodes-base.postgres"` |
| L2-WK-036 | mf-sub-crm-mail | MarkUnknownB | postgres | false branch of MailRowBack | alwaysOutputData true | no retry set | N/A | token plus mail_sent check | UNVERIFIED | N/A | mf_leads row (Postgres) state unknown | alert follows from the sweep | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:288 "n8n-nodes-base.postgres"` |
| L2-WK-037 | mf-sub-crm-mail | UnknownNewA | if | after MarkUnknownA | N/A: if node | N/A | N/A | N/A | UNVERIFIED | both outputs go to OutUnknown: the check changes nothing (dead decision) | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:327 "n8n-nodes-base.if"` |
| L2-WK-038 | mf-sub-crm-mail | UnknownNew | if | after MarkUnknownB | N/A: if node | N/A | N/A | N/A | UNVERIFIED | both outputs go to OutUnknown: the check changes nothing (dead decision) | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:359 "n8n-nodes-base.if"` |
| L2-WK-039 | mf-sub-crm-mail | DoneOwned | if | after MarkDone | N/A: if node | N/A | N/A | zero rows goes to OutLost | UNVERIFIED | N/A | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:391 "n8n-nodes-base.if"` |
| L2-WK-040 | mf-sub-crm-mail | OutDone | set | true branch of DoneOwned | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | caller sees verdict new | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:419 "n8n-nodes-base.set"` |
| L2-WK-041 | mf-sub-crm-mail | OutUnknown | set | after UnknownNew or UnknownNewA | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | caller sees verdict unknown | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:447 "n8n-nodes-base.set"` |
| L2-WK-042 | mf-sub-crm-mail | OutStage | set | error of Qualify, CrmUpsert or false of LabelOk | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | caller sees verdict processing; the row stays processing until the sweep | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:475 "n8n-nodes-base.set"` |
| L2-WK-043 | mf-sub-crm-mail | OutLost | set | claim lost at OwnsClaim1 or DoneOwned | N/A | N/A | N/A | N/A | UNVERIFIED | N/A | N/A: in-run data only | caller sees verdict processing | n8n | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:503 "n8n-nodes-base.set"` |
| L2-WK-044 | mf-recovery | Every30s | scheduleTrigger | schedule every 30 s | N/A | N/A: the schedule itself is the retry engine | after a restart the schedule resumes; stuck rows wait for the lease | N/A | fires three branches at once (MarkFailed, ClaimStuck, AlertClaim): order between them not guaranteed | empty table: ClaimStuck returns zero rows and StuckRow stops it (fixed flows) | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:16 "n8n-nodes-base.scheduleTrigger"` |
| L2-WK-045 | mf-recovery | ClaimStuck | postgres | Every30s | onError continueRegularOutput: a database error is swallowed | N/A: runs again 30 s later | N/A | FOR UPDATE SKIP LOCKED plus new token: one runner per row | UNVERIFIED | at most 5 rows per tick, oldest first | mf_leads row (Postgres) lease 120 s, attempts plus 1, new token | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:30 "n8n-nodes-base.postgres"` |
| L2-WK-046 | mf-recovery | StuckRow | if | after ClaimStuck | N/A: if node | N/A | N/A | N/A | UNVERIFIED | no row stops the branch (no phantom call) | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:70 "n8n-nodes-base.if"` |
| L2-WK-047 | mf-recovery | RunSub | executeWorkflow | after StuckRow | onError continueRegularOutput: failure swallowed, row stays processing | no retry set | kill inside: next sweep after lease | token guards writes | UNVERIFIED | N/A | N/A: sub-workflow writes | nobody | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:91 "n8n-nodes-base.executeWorkflow"` |
| L2-WK-048 | mf-recovery | MarkFailed | postgres | Every30s | onError continueRegularOutput | N/A | N/A | idempotent update | runs in parallel with ClaimStuck; conditions on attempts are disjoint (3 or more versus under 3) | no row, no output | mf_leads row (Postgres) state failed or unknown | alert follows from AlertClaim | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:106 "n8n-nodes-base.postgres"` |
| L2-WK-049 | mf-recovery | AlertClaim | postgres | Every30s | onError continueRegularOutput | claim 720 s (12 min) per attempt | after a kill the claim stays up to 12 min unless ClearStaleAlertClaims runs | FOR UPDATE SKIP LOCKED plus alert_token | UNVERIFIED | at most 5 rows per tick | mf_leads row (Postgres) alert_until, alert_token, alert_attempts | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:128 "n8n-nodes-base.postgres"` |
| L2-WK-050 | mf-recovery | AlertRow | if | after AlertClaim | N/A: if node | N/A | N/A | N/A | UNVERIFIED | no row stops the branch | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:168 "n8n-nodes-base.if"` |
| L2-WK-051 | mf-recovery | AlertSend | emailSend | true branch of AlertRow | error output goes to AlertBackoff | retry by AlertBackoff: 60 s times min(attempts,5) | kill during the send: up to 12 min late unless cleared at start | two parallel sends possible when a send outlasts the claim (v3 B90 gave 2 alerts; v4 claim 12 min) | UNVERIFIED | N/A | alert mailbox via SMTP (the same SMTP server as the lead mail) | a person gets the alert mail (the only notice in the flows) | credential name mf-mail-smtp | `handover/demo3/kill/flows-go1/mf-recovery.json:187 "n8n-nodes-base.emailSend"` |
| L2-WK-052 | mf-recovery | AlertBackoff | postgres | error of AlertSend | onError continueRegularOutput | sets next try 60 to 300 s later | N/A | token guard | UNVERIFIED | N/A | mf_leads row (Postgres) alert_until | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:210 "n8n-nodes-base.postgres"` |
| L2-WK-053 | mf-recovery | AlertMark | postgres | success of AlertSend | onError continueRegularOutput: a failed mark after a sent alert gives a second alert (V4-README says so) | no retry set | kill after send, before mark: a second alert later | alert_sent=false and token check | UNVERIFIED | N/A | mf_leads row (Postgres) alert_sent true | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:234 "n8n-nodes-base.postgres"` |
| L2-WK-054 | mf-recovery | OnN8nStart | n8nTrigger | n8n start event (init) | N/A | N/A | this node IS the kill-recovery for alert claims | N/A | two n8n instances at once: not tested (REPORT line 37) | N/A | N/A | nobody | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:256 "n8n-nodes-base.n8nTrigger"` |
| L2-WK-055 | mf-recovery | ClearStaleAlertClaims | postgres | after OnN8nStart | onError continueRegularOutput | N/A | N/A | clears claims another live instance may still hold (not tested) | UNVERIFIED | N/A | mf_leads row (Postgres) alert_until and alert_token set to null | nobody | n8n-publish-pg | `handover/demo3/kill/flows-go1/mf-recovery.json:270 "n8n-nodes-base.postgres"` |

## Scripts
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-X-001 | harness.py | driver: fresh n8n folder, fakes, one lead, kill points, counting | test rig (not part of the take) | label, point | line in results.jsonl | writes error field and continues; kills n8n in finally | none | waits 90 s for n8n, 330 s or more for terminal state | TRUNCATE mf_leads at start, fresh run folder | results.jsonl, run folder | database user postgres (superuser) from the shell | not tested itself | all run_*.sh | `handover/demo3/kill/harness.py:261 "TRUNCATE mf_leads"`; `handover/demo3/kill/harness.py:24 "PSQL = "` | LOG; COUNTER |
| L2-X-002 | fakes.py | three fake servers (CRM, stage, SMTP catcher) | test rig (not part of the take) | kind, port, workdir | events and mails files | N/A: fake | none | hold and drop switches | N/A | events.jsonl | none | not tested itself | harness | `handover/demo3/kill/fakes.py:1 "loopback stand-ins"` | LOG |
| L2-X-003 | v3.py | alert-loss cases A, B20, B90, B780, C, KS | test rig (not part of the take) | label, case | line in results.jsonl | writes error field | none | MAX_S per case up to 1500 s | ALTER TABLE ADD COLUMN IF NOT EXISTS, TRUNCATE | results.jsonl | database user postgres | not tested itself | run_l..run_r | `handover/demo3/kill/v3.py:14 "MAX_S = "` | LOG; COUNTER |
| L2-X-004 | prepare_probe.py | builds import files with placeholders replaced by stand-in ids | test rig (not part of the take) | source folder, out folder | creds.json and four flow files | no handling | none | none | N/A | stdout | stand-in credentials with database user postgres | not tested | run_d.sh | `handover/demo3/kill/prepare_probe.py:11 "stand-in"` | OTHER |
| L2-X-005 | make_go1.py | adds OnN8nStart and ClearStaleAlertClaims to the v4 recovery flow | test rig (not part of the take) | v4 folder, out folder | flows-go1 copy | no handling | none | none | rewrites the file each run | stdout | none | KS runs on go1 flows | run_p.sh version 5 | `handover/demo3/kill/make_go1.py:2 "ClearStaleAlertClaims"` | RETRY; NOTICE |
| L2-X-006 | analyze.py | per-run table from run folders | test rig (not part of the take) | label prefixes | table on stdout | OSError gives empty list | none | none | N/A | stdout | none | not tested | people | `handover/demo3/kill/analyze.py:10 "/home/user/work/kill"` | COUNTER |
| L2-X-007 | make_results.py | RESULTS Part 1 builder | test rig (not part of the take) | results.jsonl | table | OSError gives empty list | none | none | N/A | stdout | none | not tested | make_all.sh | `handover/demo3/kill/make_results.py:31 "label[0] not in"` | LOG |
| L2-X-008 | make_results_v.py | RESULTS Part 2 builder | test rig (not part of the take) | results.jsonl | table | none | none | none | N/A | stdout | none | not tested | make_all.sh | `handover/demo3/kill/make_results_v.py:7 "startswith"` | LOG |
| L2-X-009 | make_results_l45.py | RESULTS Part 3 builder | test rig (not part of the take) | results.jsonl | table | none | none | none | N/A | stdout | none | not tested | make_all.sh | `handover/demo3/kill/make_results_l45.py:9 ")).startswith(("` | LOG |
| L2-X-010 | make_all.sh | assembles RESULTS.md | test rig (not part of the take) | three builders and COMPARE-demo.md | RESULTS.md | none | none | none | overwrites | stdout | none | not tested | people | `handover/demo3/kill/make_all.sh:6 "Flow sets"` | LOG |
| L2-X-011 | run_all.sh | first 18 runs | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_all.sh:2 "one run at a time"` | OTHER |
| L2-X-012 | run_b.sh | burst, error, grep, t14 batch | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_b.sh:5 "while pgrep"` | OTHER |
| L2-X-013 | run_c.sh | fault repeats on old flows | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_c.sh:3 "$(dirname"` | OTHER |
| L2-X-014 | run_d.sh | fixed flows batch, fetches flows with git | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_d.sh:7 "git -C"` | OTHER |
| L2-X-015 | run_e.sh | restart after container restart | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_e.sh:2 "restart"` | OTHER |
| L2-X-016 | run_f.sh | grep on fixed flows then run_c | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_f.sh:4 "while ! grep"` | OTHER |
| L2-X-017 | run_g.sh | resumable queue, starts Postgres as uid 65534 | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_g.sh:2 "resumable queue"` | OTHER |
| L2-X-018 | run_h.sh | grep with four env settings | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_h.sh:5 "while ! grep"` | OTHER |
| L2-X-019 | run_i.sh | grep with PRUNE false | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_i.sh:2 "EXECUTIONS_DATA_PRUNE"` | OTHER |
| L2-X-020 | run_j.sh | fault modes on fixed flows | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_j.sh:2 "fault modes"` | OTHER |
| L2-X-021 | run_k.sh | Fc1 variant | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_k.sh:5 "while ! grep"` | OTHER |
| L2-X-022 | run_l.sh | v3 alert cases | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_l.sh:5 "while ! grep"` | OTHER |
| L2-X-023 | run_m.sh | reordered v3 queue | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_m.sh:5 "while pgrep"` | OTHER |
| L2-X-024 | run_n.sh | v3 and v4 repeats | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_n.sh:5 "while pgrep"` | OTHER |
| L2-X-025 | run_p.sh | parallel lanes, go1 version 5 | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_p.sh:6 "while pgrep"` | OTHER |
| L2-X-026 | run_q.sh | v4 kill points | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_q.sh:2 "kill points on the v4"` | OTHER |
| L2-X-027 | run_r.sh | film-v4 lease 45 kill points | test rig (not part of the take) | queue arguments | lines in run_all.progress | rc written per run | resume skips labels already in results.jsonl (some scripts) | waits with sleep 5 loops where noted; no bound | skips finished labels where noted | run_all.progress | shell user | not tested | lane3 session | `handover/demo3/kill/run_r.sh:2 "kill points on the v4"` | OTHER |

## Jobs
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-J-001 | recovery sweep every 30 s | re-run stuck leads up to 3 attempts, mark failed or unknown | RETRY owner in the take (mf-recovery) | rows with expired lease | re-run, state failed or unknown | database error swallowed (continueRegularOutput) | up to 3 attempts, lease 120 s | 120 s lease | SKIP LOCKED plus token | none (execution log off) | n8n-publish-pg | K1 K2 K3 K6 error | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:26 "attempts=attempts+1"`; `handover/demo3/kill/flows-go1/mf-recovery.json:102 "attempts >= 3"` | RETRY |
| L2-J-002 | alert claim and send | tell a person about unknown or failed leads, exactly once as far as possible | NOTICE owner in the take (mf-recovery) | rows in unknown or failed with alert_sent false | one alert mail; alert_sent true | AlertBackoff 60 s to 300 s times attempts | claim 720 s | 720 s | alert_token | none | n8n-publish-pg and mf-mail-smtp | v3 A B20 B90 B780 C KS; v4 same | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:124 "720 seconds"`; `handover/demo3/kill/flows-go1/V4-README.md:8 "A send that outlasts 12 min"` | NOTICE; RETRY |
| L2-J-003 | clear stale alert claims at n8n start | make a late alert after a kill come within about 60 s | RETRY helper of the alert job | n8n init event | alert_until and alert_token set to null | database error swallowed | none | none | clears only unsent alerts | none | n8n-publish-pg | KS: 60 s in 3 of 3 runs; two n8n instances at once NOT tested | n8n | `handover/demo3/kill/flows-go1/mf-recovery.json:256 "n8n-nodes-base.n8nTrigger"`; `handover/demo3/REPORT.md:11 "fixed flows 60 s in 3 of 3 runs"` | RETRY |
| L2-J-004 | kill-test queues | run the case lists | none (test rig) | run_*.sh | run_all.progress lines | rc written | resume by label | none; unbounded sleep loops | skip finished labels | run_all.progress | shell | not tested | lane3 session | `handover/demo3/kill/run_b.sh:5 "while pgrep"` | OTHER |
| L2-J-005 | results build | build RESULTS.md from results.jsonl | none (test rig) | results.jsonl | RESULTS.md | none | none | none | overwrites | stdout | shell | not tested | people | `handover/demo3/kill/make_all.sh:8 "python3 make_results.py"` | LOG |

## Credentials
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2-K-001 | n8n-publish-pg | one Postgres credential used by every Postgres node in all four flows | per DECISION three roles are intended (n8n, app, read-only count); not decided for these flows | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | n8n-publish-pg | names only; value never read; stand-in value in tests (type: made-up password); kill runs: database user postgres (superuser); all runs | all flows that name it | `handover/demo3/kill/flows-go1/mf-form.json:112 "n8n-publish-pg"`; `handover/demo3/kill/prepare_probe.py:11 "kill_t"` | STORE |
| L2-K-002 | mf-mail-smtp | SMTP credential for lead mail and alert mail (same credential for both) | none stated | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | mf-mail-smtp | names only; stand-in value in tests; loopback fake; all mail runs | all flows that name it | `handover/demo3/kill/flows-go1/mf-recovery.json:196 "mf-mail-smtp"`; `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:227 "mf-mail-smtp"` | NOTICE |
| L2-K-003 | placeholders PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID | ids replaced at import by prepare_probe.py | test rig | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | placeholders PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, SUB_WORKFLOW_ID | names only; import step | all flows that name it | `handover/demo3/kill/flows-go1/mf-form.json:111 "PG_CREDENTIAL_ID"`; `handover/demo3/kill/prepare_probe.py:21 "SUB_WORKFLOW_ID"` | OTHER |
| L2-K-004 | MF_STAGE_URL, MF_CRM_URL, MF_STAGE_TIMEOUT_MS (n8n environment names) | addresses and timeout for the stage and the CRM | test rig and take scripts | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | MF_STAGE_URL, MF_CRM_URL, MF_STAGE_TIMEOUT_MS (n8n environment names) | names only; all runs | all flows that name it | `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:19 "MF_STAGE_URL"`; `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:75 "MF_CRM_URL"` | OTHER |
| L2-K-005 | n8n per-run encryption key (generated by n8n inside each run folder) | n8n encrypts stored credentials with it | n8n | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | n8n per-run encryption key (generated by n8n inside each run folder) | type only: key file in a run folder; was committed by mistake for 4 GO-1 runs and removed from the branch; still in git history; n8n; none | all flows that name it | `handover/demo3/REPORT.md:3 "encryption key n8n generated"` | OTHER |
| L2-K-006 | creds-lane.json in 4 run folders (go1-*) | stand-in credential file written by harness per lane | test rig | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: credential | N/A: names only, value never read | creds-lane.json in 4 run folders (go1-*) | type only: credential-shaped file, made-up value; none; none | all flows that name it | `handover/demo3/kill/harness.py:110 "creds-lane.json"` | OTHER |

## Docs and tests and folders
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L2-D-001 | FREEZE.md | freeze report of the desk-repo patch series (fix-1..fix-8), not the take | `handover/demo3/FREEZE.md:1 "lane3 FREEZE REPORT"` | OTHER |
| L2-D-002 | MATRIX-1.md | Python and order matrix of the desk repo test suite | `handover/demo3/MATRIX-1.md:1 "MATRIX-1: test matrix facts"` | OTHER |
| L2-D-003 | ORDERS.md | all orders to lane3 (product tests, then kill script, then GO-1, STOP-2) | `handover/demo3/ORDERS.md:1 "ORDERS for cloud session 3"` | OTHER |
| L2-D-004 | REPORT.md | newest first status and final closeout; says RESULTS.md is the results file | `handover/demo3/REPORT.md:48 "THE results file"` | LOG |
| L2-D-005 | WINDOWS-RUN-1.md | steps for the lead to run two PowerShell scripts; never run | `handover/demo3/WINDOWS-RUN-1.md:3 "nothing below has ever been run on Windows"` | OTHER |
| L2-D-006 | questions-for-lead.md | 20 questions (Q-19 dotted domain, Q-20 slow SMTP leaves unknown with no alert) | `handover/demo3/questions-for-lead.md:13 "one open design question"` | NOTICE |
| L2-D-007 | register.md | agent register; 123 lines still say running | `handover/demo3/REPORT.md:47 "rows for runs e to l are stale"` | LOG |
| L2-D-008 | kill/PLAN.md, PLAN-V3-ALERT.md, PLAN-GO1.md | plans written before runs | `handover/demo3/kill/PLAN.md:1 "plan and pass criteria"` | OTHER |
| L2-D-009 | kill/RESULTS.md, COMPARE-demo.md | results and comparison with the demo session | `handover/demo3/kill/RESULTS.md:1 "lane3 kill and fault results"` | LOG |
| L2-D-010 | kill/flows-go1/V4-README.md | README of the v4 design; heading says built, not run | `handover/demo3/kill/flows-go1/V4-README.md:1 "BUILT, NOT RUN"` | NOTICE; RETRY |
| L2-D-011 | kill/data/trace-b90-report.md | trace of why v3 sent two alerts | `handover/demo3/kill/data/trace-b90-report.md:5 "ALERT-CLAIM-SHORTER-THAN-SEND"` | NOTICE |
| L2-T-001 | kill points K1 K2 K3 K6 | kill n8n at named steps, count outside n8n | `handover/demo3/kill/harness.py:245 "KILL_AT"` | RETRY |
| L2-T-002 | fault modes Fa Fb Fc Fc1 | CRM search blind, SMTP drop, SMTP pre-greeting hold | `handover/demo3/kill/harness.py:325 "elif point =="` | NOTICE |
| L2-T-003 | controls control1 control2same control2par controlbad | single, repeat, parallel, invalid e-mail | `handover/demo3/kill/harness.py:280 "control1"` | FILTER |
| L2-T-004 | error, burst, grep, idle (t14) | CRM refuses all; 10 parallel same lead; canary search; empty table ticks | `handover/demo3/kill/harness.py:295 "elif point =="` | FILTER; STORE |
| L2-T-005 | v3 cases A B20 B90 B780 C KS | alert refused, held, dead, killed | `handover/demo3/kill/v3.py:37 "case =="` | NOTICE |
| L2-F-001 | handover/demo3/kill/ | workflow tests, scripts, results | `handover/demo3/REPORT.md:50 "kill/harness.py"` | OTHER |
| L2-F-002 | handover/demo3/kill/flows-go1/ | the only copy of the flows in this box | `handover/demo3/kill/flows-go1/V4-README.md:1 "Design A v4"` | OTHER |
| L2-F-003 | handover/demo3/kill/data/runs/ | 127 run folders, 126 results labels | `handover/demo3/REPORT.md:51 "runs/<label>/"` | LOG |

## Findings
| id | claim type | severity | evidence | conflicts with | job key |
|---|---|---|---|---|---|
| L2-FD-001 | inconsistent | Blocker | ALL kill-test numbers were taken with n8n on its default SQLite file, not Postgres: the harness sets no DB setting and the GREP result lists the sqlite file. `handover/demo3/kill/harness.py:34 "N8N_USER_FOLDER=home"`; `handover/demo3/kill/RESULTS.md:40 "n8n_folder:email=n8nhome/.n8n/database.sqlite-wal"`. Results on Postgres-backed n8n: UNVERIFIED, needs a runtime. `handover/demo3/REPORT.md:55 "GREP on Postgres-backed n8n"` says it was not run. | DECISION line 14 | STORE |
| L2-FD-002 | security | Blocker | Made-up e-mail, name and an api_key canary planted in the request were found inside n8n's database files in every GREP run, also with execution saving off and PRUNE false: `handover/demo3/kill/harness.py:315 "api_key"`; `handover/demo3/kill/RESULTS.md:44 "n8n_folder:key=n8nhome/.n8n/database.sqlite-wal"`. No run shows zero hits, so the claim that no lead data reaches n8n's store has no support. Cause not found in any file (UNVERIFIED). Blocker: no fix possible statically; next step: run GREP on Postgres-backed n8n and inspect which table holds the webhook body. | DECISION line 14 | STORE |
| L2-FD-003 | inconsistent | Blocker | The four flows set execution saving to none, so no execution log exists, while the decision says to turn it on for the take: `handover/demo3/kill/flows-go1/mf-form.json:424 "saveDataSuccessExecution"`; `handover/demo3/kill/run_h.sh:9 "EXECUTIONS_DATA_SAVE_ON_SUCCESS=none"`; the tester could not read any node error text for that reason: `handover/demo3/questions-for-lead.md:11 "executions are not saved"`. | DECISION line 16 | LOG |
| L2-FD-004 | duplicate | Major | mf-form and mf-hook are the same flow: 10 of 12 nodes identical (own diff of the JSON); only the webhook path and three field names differ. `handover/demo3/kill/flows-go1/mf-form.json:7 "mf-form"`; `handover/demo3/kill/flows-go1/mf-hook.json:7 "mf-hook"`; `handover/demo3/kill/flows-go1/mf-form.json:27 "submission_id"`; `handover/demo3/kill/flows-go1/mf-hook.json:27 "message_id"`. The hook flow is never POSTed by any test case (only listed in `handover/demo3/kill/harness.py:26 "FLOWS = "`), so its behaviour is UNVERIFIED. Proposal: one entry flow with a source field (CODE-LAST: config, not a copy). Both flows share one key space in one table with no source column: `handover/demo3/kill/flows-go1/mf_leads.sql:5 "lead_key"`. | none | FILTER |
| L2-FD-005 | duplicate | Major | RETRY has four engines: node retry (3 tries) on Qualify and CrmUpsert, the 30 s sweep (3 attempts), the alert backoff, and the start-time clear; plus the stage journal (real one NOT VISIBLE). A stage or CRM failure can therefore repeat up to 3 x 3 times; safe only because the stage journal and the keyed CRM upsert absorb repeats. `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:36 "maxTries"`; `handover/demo3/kill/flows-go1/mf-recovery.json:26 "attempts=attempts+1"`; `handover/demo3/kill/flows-go1/mf-recovery.json:256 "n8n-nodes-base.n8nTrigger"`. Proposal: name the sweep as the single RETRY owner; keep node retry only for transient HTTP errors; state it in the plan. | none | RETRY |
| L2-FD-006 | dead | Major | UnknownNewA and UnknownNew are if nodes whose true and false outputs both go to OutUnknown, so they decide nothing. Evidence (own dump of the connections): `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:326 "UnknownNewA"`; `handover/demo3/kill/flows-go1/mf-sub-crm-mail.json:358 "UnknownNew"`. Proposal: cut both nodes, connect MarkUnknown* to OutUnknown. | none | FILTER |
| L2-FD-007 | inconsistent | Major | State review (invalid e-mail) parks a lead with no mail, alert or screen: `handover/demo3/kill/flows-go1/mf-form.json:97 "ELSE 'review' END"`; `handover/demo3/kill/flows-go1/mf-recovery.json:124 "'unknown','failed')"`. Only unknown and failed trigger an alert. Whether a person is meant to find review rows in the table is not stated anywhere in this box (UNVERIFIED). | none | NOTICE |
| L2-FD-008 | unverified | Blocker | When the mail server is slow, a lead ends unknown with no intake mail and no alert (3 of 3 on two flow sets), and nobody is told: `handover/demo3/kill/RESULTS.md:13 "lead_alerts=0"`; `handover/demo3/questions-for-lead.md:13 "one open design question"`. The alert uses the same SMTP server and the same credential as the lead mail, so the notice channel fails with the thing it reports (single dependency). Fc was never re-run on v3, v4 or go1 flows: `handover/demo3/kill/COMPARE-demo.md:12 "Not compared"`. Blocker (mail, notice). Exact blocker: a second notice channel was refused by order, `handover/demo3/ORDERS.md:197 "no second alert channel now"`; needs the lead's decision. | none | NOTICE |
| L2-FD-009 | inconsistent | Major | Six flow versions exist (11:05Z, 61e3804b, v3 6ebb7f62, v4 7709d058, film-v4 873a908a, go1) and only go1 is in this box: `handover/demo3/kill/make_all.sh:6 "Flow sets"`. The README in the go1 folder says the v4 design is not run, while v4 runs are in the results: `handover/demo3/kill/flows-go1/V4-README.md:1 "BUILT, NOT RUN"`; `handover/demo3/kill/RESULTS.md:72 "v3B780"`; the table note says the table matches v3 and the folder is v2: `handover/demo3/kill/flows-go1/mf_leads.sql:1 "NOTE (v3 table"`; `handover/demo3/kill/flows-go1/mf_leads.sql:2 "OLDER NOTE"`. The GO-1 fix is not in the demo flows and is not reviewed: `handover/demo3/REPORT.md:11 "NOT reviewed"`. Other versions: NOT VISIBLE: demo/handover n8n-flows-v3, n8n-flows-v4, n8n-flows-film-v4. | none | OTHER |
| L2-FD-010 | unverified | Major | V4-README names tests in mf.py, which is not in this box: `handover/demo3/kill/flows-go1/V4-README.md:10 "Tests (new, mf.py)"`. NOT VISIBLE: mf.py. | none | OTHER |
| L2-FD-011 | inconsistent | Major | Scripts hard-code paths, ports and database names (/home/user/work/kill, 55432, user postgres), and read results.jsonl from that path although the committed copy is under kill/data, so RESULTS.md cannot be rebuilt from the repo alone: `handover/demo3/kill/harness.py:18 "/home/user/work/kill"`; `handover/demo3/kill/make_results.py:7 "/home/user/work/kill"`; `handover/demo3/kill/analyze.py:10 "/home/user/work/kill"`; `handover/demo3/kill/harness.py:24 "PSQL = "`. Violates the no-hardcoding rule. Proposal: one config read in one place. | none | OTHER |
| L2-FD-012 | ops | Major | Unbounded wait loops (while ... sleep 5) in eight queue scripts, against the hygiene rule 19: `handover/demo3/kill/run_b.sh:5 "while pgrep"`; `handover/demo3/kill/run_f.sh:4 "while ! grep"`; `handover/demo3/kill/run_h.sh:5 "while ! grep"`; `handover/demo3/kill/run_k.sh:5 "while ! grep"`; `handover/demo3/kill/run_l.sh:5 "while ! grep"`; `handover/demo3/kill/run_m.sh:5 "while pgrep"`; `handover/demo3/kill/run_n.sh:5 "while pgrep"`; `handover/demo3/kill/run_p.sh:6 "while pgrep"`. A wait on a script that never ends waits forever. | none | RETRY |
| L2-FD-013 | inconsistent | Major | run_all.progress is called the truth for runs but 20 of 126 labels are missing from it (own cross-check): `handover/demo3/REPORT.md:47 "the truth is"`. Missing include v3a2, v3b90b, v3c2, v4a1 and all go1-* runs. run_r.sh labels film-v4 runs with the v4 commit: `handover/demo3/kill/run_r.sh:10 "(7709d058-v4)"`. | none | LOG |
| L2-FD-014 | inconsistent | Major | RESULTS.md is called THE results file but leaves out the GO-1 runs and the controls (cb invalid e-mail, cs same twice, cp parallel, c1L): the builders only take labels starting with j or f, or v3 or v4: `handover/demo3/REPORT.md:48 "THE results file"`; `handover/demo3/kill/make_results.py:31 "label[0] not in"`; `handover/demo3/kill/make_results_v.py:7 "startswith"`. The GO-1 numbers (60 s versus 750 s) exist only in `handover/demo3/REPORT.md:11 "fixed flows 60 s in 3 of 3 runs"` and results.jsonl. Provenance of the c* controls is not stated (flows field absent): UNVERIFIED which flow set they ran on. | none | LOG |
| L2-FD-015 | unverified | Major | Every model_calls=1 in RESULTS Part 1 is counted from an in-memory fake journal, not the real stage.journal: `handover/demo3/kill/fakes.py:137 "journal, lock"`; `handover/demo3/kill/RESULTS.md:8 "model_calls=1"`. The money guard (DECISION line 17) is therefore not tested here. NOT VISIBLE: qualify_stage.py. | DECISION line 17 | COUNTER |
| L2-FD-016 | unverified | Major | Idle-recovery check (no lead, empty table) rests on one run: three were planned and one recorded: `handover/demo3/kill/run_b.sh:10 "t14:ft14a"`; `handover/demo3/kill/RESULTS.md:37 "no lead, total_stage_requests=0, total_mails=0, alert_mails=0, crm_upserts=0"`. The old phantom calls (stage and CRM called with an empty lead) are described in `handover/demo3/kill/PLAN.md:32 "F-REC-EMPTY"` and are fixed in the go1 flows by StuckRow; only the single run shows it. Planned v3 repeats B20 and A (run_l.sh:6) also never ran (v3a3, v3b20b not in results). | none | RETRY |
| L2-FD-017 | inconsistent | Major | register.md disagrees with the results about which flows the later batches used: `handover/demo3/register.md:403 "newest flows (1ced4e1f)"`; `handover/demo3/kill/RESULTS.md:2 "61e3804b (fixed)"`. It also holds 123 lines marked running although no agent runs, as REPORT.md admits: `handover/demo3/REPORT.md:47 "rows for runs e to l are stale"`. The supervision rule says close rows when an agent reports. Proposal: archive the register under archive/ after the owner says yes. | none | LOG |
| L2-FD-018 | security | Blocker | Four n8n working folders with per-run encryption keys were pushed to git by mistake and stay in the history (about 220 MB): `handover/demo3/REPORT.md:3 "encryption key n8n generated"`; `handover/demo3/REPORT.md:5 "NOT FIXED, needs the lead/owner"`. Values are made-up stand-ins but credential-shaped. Four credential files are still tracked: data/runs/go1-fix-ks, go1-fix-ks2, go1-fix-b90, go1-old-ks (creds-lane.json, type: stand-in password). Exact blocker: history rewrite needs the owner (only the lead may force-push); next step: owner chooses leave or recreate the branch. | none | OTHER |
| L2-FD-019 | duplicate | Major | Three dedupe layers do one job: the claim insert, the stage journal and the CRM upsert that matches on lead id OR e-mail: `handover/demo3/kill/flows-go1/mf-form.json:97 "ON CONFLICT"`; `handover/demo3/kill/fakes.py:103 "hit = next((r for r in rows.values() if r["`. The e-mail match means two different leads with one e-mail become one CRM row; real HubSpot behaviour UNVERIFIED (the harness gives each lead its own e-mail to avoid it: `handover/demo3/kill/harness.py:161 "one e-mail per lead"`). | none | FILTER |
| L2-FD-020 | idle | Major | Ten patches lane3-fix-1..10 for the desk repo's reset and start scripts went through up to 13 review rounds although the video does not use them; three were paused: `handover/demo3/ORDERS.md:185 "PAUSED, not deleted"`; `handover/demo3/FREEZE.md:8 "No independent review at all"`. Several are marked not merge-ready: `handover/demo3/FREEZE.md:5 "NOT merged-ready"`. Their place belongs to lane L3 (evidence folder); recorded here because the docs I own describe them. Owner decision needed: archive or finish. | none | OTHER |
| L2-FD-021 | ops | Major | The EGM drift report and the blocker ledger were not run for lane3: `handover/demo3/FREEZE.md:27 "was NOT run"`. Fix needs the lead (the freeze order forbade more steps); nothing here can fix it. | none | OTHER |
| L2-FD-022 | inconsistent | Nit | Questions file names a node AlertUnknown, which does not exist; the node is AlertSend: `handover/demo3/questions-for-lead.md:12 "AlertUnknown"`; `handover/demo3/kill/flows-go1/mf-recovery.json:186 "AlertSend"` | none | NOTICE |
| L2-FD-023 | unverified | Nit | Nothing about the desk's PowerShell scripts has run on Windows: `handover/demo3/WINDOWS-RUN-1.md:3 "nothing below has ever been run on Windows"`. Not part of the take. | none | OTHER |
| L2-FD-024 | idle | Nit | Idle logs: crm.log, smtp.log and stage.log are empty in all 126 run folders (378 empty files); the fakes write everything to events.jsonl instead: `handover/demo3/kill/harness.py:72 "lg = open"` | none | LOG |
| L2-FD-025 | duplicate | Nit | Three run records of the same runs: results.jsonl, RESULTS.md and run_all.progress (STORE or LOG with three owners): `handover/demo3/REPORT.md:47 "the truth is"`; `handover/demo3/REPORT.md:48 "THE results file"`. Proposal: results.jsonl is the owner of this test-rig LOG; the other two are generated. | none | LOG |

## Checkpoint
Done: all 756 files have a status (READ 46, SKIMMED 709, NOT-READ 1). Workflow walk covers every node of the four flows (55 rows). 25 findings.
Next: register.md is the one NOT-READ file (partial read, tails unseen); a continuation lane can finish it. Nothing else pending.
Blockers for the lead: FD-001 to FD-003 need a runtime (Postgres-backed n8n); the second notice channel needs a decision; the history rewrite needs the owner.
Honest notes: I ran one read-only `git status` by slip (the must-not list says no git); no repo file was run or imported; I used my own scratch python (parsing JSON and checking citations) outside the repo; severity of FD-001..FD-003 follows the lane table. Time box: finished inside 60 minutes of my own clock is UNVERIFIED (no clock in my tools).
