# Investigation AK-G2 repro (ORDER 173 d), 2026-11-09, read-only

## What I could not settle (first)
- NOT CHECKED: GitHub state. `gh pr list` returned no usable output (no login in this cloud box), so "merged / not merged" comes from `git` only (origin/main head `0dabf1f`, branch heads and commit counts ahead of main).
- NOT CHECKED: Postgres. All repro runs are on the in-memory store (`MemoryStore`). The Postgres race (two processes, same key) cannot be shown on main at all, because main has no receipt table; I did not start `pgstart.sh`.
- NOT CHECKED: whether the lead has made the "peel" / P5c choice (BN-21) or given an order releasing AK-G2-a; grep of `LEAD-ORDERS.md` and `questions-for-lead.md` for "peel" finds no lead decision (hits are only the ticket's own text and unrelated "peel" words: none about AK-G2).
- NOT CHECKED: whether the 5 repro tests are the same as the ticket's test row D0 ("fail-before"); I did not read ticket lines 236-480 (test rows). My tests show the problem class; they are not a copy of D0.
- Repro limit: the "door" in my script is a naive one I wrote (check signature, then `Runtime.handle`), because main has no inbound door at all. It shows what any consumer gets from main today, not a bug in an existing door.

## What AK-G2 fixes (READ, `tickets/AK-G2.md` banner/Words)
Write a receipt before answering a signed message; at most one run per message; every message ends in exactly one of `done` / `needs_person` / `refused`; a changed body under a reused id is refused and recorded.

## Repro (RAN)
Base: `git archive origin/main` (head `0dabf1f`) extracted to `/home/user/build/ak-g2-repro/main` (repo itself untouched). Test file: `/home/user/build/ak-g2-repro/test_akg2_repro.py` (copied to `main/tests/_akg2_repro_tmp.py` to use the repo's own `tests/k5_support.py` builders). Fake model (`ScriptLLM`), fake clock (a dict), signature code from main (`approvals/hmac_v0.py`), secret built from parts, no network, no spend.

Command:
```
cd /home/user/build/ak-g2-repro/main
uv run --all-extras --group test pytest tests/_akg2_repro_tmp.py -q -s -p no:cacheprovider > ../repro-out.txt 2>&1; echo rc=$?
```
Output (raw file `/home/user/build/ak-g2-repro/repro-out.txt`):
```
runs: run-f997da2b... run-8837572c... model calls: 2
.(200, 'run-af51f5ab...') (200, 'run-6b1c93ce...') model calls: 2
.distinct runs from 4 simultaneous deliveries: 4 model calls: 4
.runs stuck in WORKING after crash: [('run-856a53bd...', 'msg-1')]
...
6 passed in 0.64s          rc=0
```
Each test PASSES by asserting the BAD behaviour (so "passed" = problem reproduced):
- R1: same message id and same bytes, re-sent 5 minutes later and freshly signed: 2 runs, 2 model calls. Should be 1 run.
- R1b: an unchanged captured request replayed inside the 5-minute signature window: 2 runs. (`hmac_v0.verify` only checks age; nothing remembers a request.)
- R2: 4 simultaneous identical deliveries: 4 distinct runs, 4 model calls.
- R3: the door says "200 accepted" before any durable record; then the process dies inside `handle` (a `BaseException`, like a kill): the sender will not retry, one run is stranded in `WORKING` with no final state, and a later re-delivery starts a second run while the first stays stranded. Note: the stranded run carries `trigger_ref` only because my door passed it; the store has no message-to-run mapping or uniqueness.
- R4: same id, different body (amount 100 then 999): both processed, no conflict answer, no refused row.
- R5: main has no `triggers` package, no inbound/receipt method on `Store`, and `Runtime.handle` has no `run_id` keyword (so a caller cannot even derive a run id from a message key).
Side finding (RAN): `Run.trigger_kind` accepts only `event`, `schedule`, `user`; `webhook` raises a pydantic error at `agent_loop.py:342`. Not in the ticket text I read; NOT CHECKED whether the ticket handles it (it uses `event` or a new value; check before build).

"Lost without a record" (message acked then never run) is shown by R3(a)+(b): the only trace is a stuck run; no receipt exists to find the message again.

## What blocks the build
All below READ unless marked.
1. Hard dependencies (BN-21): P4d, P3a, P2a-1, AK1-a. State on main: no `reserve_spend`, no `pipeline/` package (RAN `ls`, `grep`), migrations stop at `0005_evidence.sql`; P3a-1 only is merged (`0dabf1f`). Branches ahead of main (git rev-list): `core/P4d` 10 commits, `core/P2a-1` 9, `core/P3a-2` 28, `core/P4b1` 14, `core/P6a` 13. AK1-a has no branch at all.
2. Merge order: P4c-2 and P5c edit `runtime/agent_loop.py` first; no branches exist for either. BN-21: AK-G2-a cannot start until P5c merges unless the lead takes the "peel" (early PR adding the `run_id` keyword to `Runtime.handle`) or lets P5c rebase on AK-G2-a. No lead decision found (see top).
3. Build-start review: not done. `handover/reviews/` has only AK-G2 round1-3 files; the ticket banner and LEAD-ORDERS order 19 A require one build-start review (fresh egm reviewers, then egm-resolve) before build.
4. AK-G2-b additionally needs AK-G2-a and P6a-1 (PR 72; `core/P6a` exists, not merged).
5. Lead answers to PENDING LEAD 9-12: ANSWERED, quotes from `LEAD-ORDERS.md` order 34 (lines 196-199) and `questions-for-lead.md` q79:
   - "69. AK-G2 PL9: option (a) per-source key check value, door answers 503 and dispatch fails loudly until `inbound.key_check_ack` names the new check; keep the derived key (PL6 c)."
   - "70. PL10: option (a), app.build refuses two sources sharing an agent id or principal id across tenants in every environment; sharing inside one tenant stays allowed."
   - "71. PL11: option (a), refuse a reopen while the earlier run is still open."
   - "72. PL12: move compare_ids, IdComparison and list_inbound to AK-G15/V7 ..., keep the door's one-final-state guarantee in AK-G2."
   - Also: order ~111 (line 333) "AK-G2 BN-24 choice (i)/(ii): take your recommendation and record which."; ruling L10 (line 1017): "AK-G2 is ACTIVE per freeze-list.md:48 ... sequence it after the P1b and P4d merges."; later lead text (line 1019) "no build before the P1b/P4d merges".
   - Still open (no lead answer found): BN-28 audit proposals (use AK-G16-d `door_app` with `wsgiref`, k6 for B2). BUT LEAD-ORDERS line 398 says "ACCEPT as build notes (BN) now: ... AK-G2 reuse of door_app and stdlib wsgiref, B2 request generator to k6", so that is decided; whether `door_app` (AK-G16, deferred) exists to reuse: NOT CHECKED. A soak row for R370: no decision found.
6. Environment: Postgres 16 only locally (`pgstart.sh`); CI matrix is 16+17 (order q380). Store contract group `inbound` on Postgres 17 cannot run in this box. The hard owner rule on migrations (next free number at merge) means the migration number depends on P4d/P2a-1 merge order.
7. Nothing needs the owner's money or keys.

## Can AK-G2-a start today?
NO. From which base: not from current `origin/main` (`0dabf1f`): P4d, P2a-1 and AK1-a are not there. The earliest honest base is `origin/main` after the money chain (P4d and the stacked PRs) and P2a-1 merge, plus AK1-a built, plus the lead's P5c route (peel or rebase). Building on top of an open `core/P4d` branch would make AK-G2-a a stacked PR on an unmerged money chain; not recommended (order 1036 merge sequence).
Useful today without waiting: (1) the build-start review of the frozen ticket (text only); (2) the repro file above can be kept as the base for test row D0 / T2; (3) the lead decides the peel: one small PR adding `run_id: str | None = None` to `Runtime.handle` would remove blocker 2 and is cheap (my recommendation, not a decision).
Next owner of each step: lead (peel choice, order releasing the build, build-start review launch); P4d chain builders (merge); AK1-a author.

R-numbers used: R368 (no lost/double-applied message), R369/R370 (isolation, load) via the ticket text; R448/R449 (rung table present per BN-28; "dev" read as "demo"). I did not grep `bible/` for more.
Files: this note; `/home/user/build/ak-g2-repro/test_akg2_repro.py`; `/home/user/build/ak-g2-repro/repro-out.txt`; extract `/home/user/build/ak-g2-repro/main`.
Processes started: none left running (no Postgres, no background jobs). EGM skipped: read-only investigation, no repo code changed.
