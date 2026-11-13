# Crash soak (evidence runner Q3)

Public main f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree `/home/user/work/q3-base`, Python 3.12.3). Start 2026-11-13 12:36:21Z (18:06 IST), end 12:52:30Z (18:22 IST). This file records raw results; it does not judge the product.

## Summary

| rounds | violations | hangs | seeds |
|---|---|---|---|
| 300 of 300 | 0 | 0 | master seed 20261113; round n uses seed string `20261113-n` (`random.Random("20261113-n")`) |

Violations: none. Rounds over 120 s: none (longest round 11.3 s). Harness errors: none. The repo checker `load_tools/check_invariants.py` exited 0 (all 7 checks hold) on the book of all 300 rounds.

## What was run (numbers from `raw/q3-rounds.jsonl`)

- 7220 distinct leads (N per round 5 to 40), 11576 planned sends: 2153 same-person sends through the second door (same request id, other door) and 2203 exact replays.
- 386 kills in 300 rounds: 214 rounds with 1 kill+restart, 86 rounds with 2 kills+restarts (second kill happens during the resend phase).
- Kill kinds: 239 crash-point kills, 147 random-time SIGKILLs.
  - Crash points (flag file, `scripts/crash_desk.py`), fired = desk exited 137 at the point: A 25, A2 29, B 18, C0 16, C1 25, D1 18, D1b 24, D2 23, D3 24, L 19. 18 point kills did NOT fire before the sends finished and a 8 s wait ran out (A 5, A2 6, B 1, C0 1, D1 2, D1b 2, D3 1); the harness then SIGKILLed the desk at a random moment (recorded as `not-fired-then-sigkill`). Point N1 (reminder mail) was not used: reminders are off by default (no leadflow file), so the desk never reaches it.
- Final state over all 300 rounds: 7220 follow-ups `sent`, 0 failed, 0 unknown, 0 pending; 7220 mails in the fake mail system; 7220 CRM rows. Every round reached idle.

## Assertions (own code, from the book plus the fakes' own lists) and the repo checker

| # | Assertion | Result |
|---|---|---|
| 1 | no lead processed twice: per person one lead, at most one `new` verdict row, at most one CRM row per lead, no CRM row for an unknown lead | 300/300 rounds hold |
| 2 | at most 1 mail per lead (per send key and per recipient address) in the fake mail system | 300/300 hold |
| 3 | no lead lost: every request id has a decided receipt, a lead and a follow-up out of pending/sending | 300/300 hold |
| checker | `check_invariants.py` exit code | 0 in 300/300 |

## Limits of this evidence (read before relying on it)

- Mail assertion is weaker than it looks: the soak ran the KEYED fake mail system (`--outbox keyed`, the demo's idempotent sender), which refuses a second message with the same key. A desk that re-sent after a crash would have been stopped by the fake, not by the desk. The "at most 1 mail" result therefore shows the desk plus a keyed sender work together, not that the desk alone never re-sends. The blind sender (`--outbox blind`, a mail system that cannot recognise repeats) was run only as a 30-round harness self-test (seed 7, not part of the 300): the repo checker failed 4 rounds (16, 22, 25, 26), all on check 2 only, because 1 to 3 follow-ups per round ended `unknown` (documented: a person must look; the checker allows 0 by default). The mail count, doubled mails and CRM checks passed in those rounds; my own assertions A1 to A3 held there too (violation flag in those 4 rounds came from the checker exit). Raw files of the self-test: `/home/user/work/q3-logs/selftest-blind/` (not copied into evidence/raw). I did not check whether the Q3b agent covers blind.
- The checker was run with `--no-require-comparable`: the fake mail log offers recipient and subject but no body hash, so the "text matches" part of check 3 could not be compared (the recipient and subject fields were passed but the flag was off; the checker's own count says "30 not comparable" in a sample round). Everything else is the checker's default (no `unknown` or `failed` follow-up allowed, drain at most 120 s).
- Fresh book per round (not one book across rounds). The documented normal use is one long-lived book; the cross-round case (a book with thousands of old leads being restarted) was not tested.
- Model step is the recorded (pre-written) one, so the model call log is empty; the checker's model check is vacuous here.
- Each round's idle check waits for open receipts and pending/sending follow-ups to reach 0 and the mail count to stay unchanged for 3 looks (0.3 s apart); a slower retry that would come later than that would not be seen.
- Not covered: kill of the fakes, power loss, disk faults, real SMTP/HubSpot adapters, reminders (N1), second crash inside startup sweep except by chance in the 86 two-kill rounds.
- Crash points are one-shot flag-file crashes (`os._exit(137)` inside the desk), plus plain SIGKILL; the SIGKILL timing is uniform over 0.02 s to 0.5+0.03N s after the first send, so it falls both inside the send burst and after it.

## Harness

- `tools/q3-soak.py` (this folder's `tools/`). Per round: free ports from 18100-18499 (desk) and 18600-18999 (fakes), both on 127.0.0.1, offset by round number and checked free first. Fresh `demo_only.fakes_server --outbox keyed` and a fresh book directory (`DESK_DB_PATH`, `DESK_PORT`, `DESK_FAKES_PORT`; no other DESK_* set, so the lead-flow feature and reminders are off and the recorded AI step is used). The desk is started as `scripts/crash_desk.py` (documented crash script with the flag file `crash.flag` next to the book).
- Leads: made-up names and `@example.com` addresses; request id `r<round>-<i>`. Per person: first send on a random door (`form` or `webhook`); with 30% also the same request id on the other door; with 30% an exact replay.
- Kill phase (1 kill, or 2 with 30%): 60% crash point (random of A, A2, B, L, C0, C1, D1, D1b, D2, D3, flag written before the sends), 40% SIGKILL after a random delay. 6 sender threads, one try each, stop sending once the desk is dead. Then restart on the same book.
- After the last restart: resend ALL sends (every lead, second-door sends, replays) in a new random order, patient retries on 503 or connection errors (up to 30 s). Wait until `/counts` shows `open + pending_followups == 0` and the mail count is stable for 3 looks. Collect `/fake/outbox`, `/fake/crm`, stop the desk (SIGTERM, then SIGKILL after 12 s), stop the fakes, open the book read-only for the assertions, run the repo checker.
- Round limit 120 s (watchdog kills own PIDs and flags a hang). Every PID is recorded in `raw/q3-pids.txt`; only recorded PIDs were signalled. At the end, no process of this run was listening on the 18xxx ports. Note: `raw/q3-pids.txt` also holds a few PIDs from the 4-round and 30-round trial runs; some of those numbers were later reused by other agents' processes (I did not signal them).
- Product code untouched: `git status` of `/home/user/work/q3-base` shows 0 changed files.

Commands:

```
git -C /home/user/work/src worktree add --detach /home/user/work/q3-base f3c39cf89ec989f032ea48a23cfd824b88da9c68
cd /home/user/work/q3-base
timeout 4800 /home/user/work/final-venv/bin/python /home/user/hadavin-sdk/handover/demo3/tools/q3-soak.py run \
  --base /home/user/work/q3-base --python /home/user/work/final-venv/bin/python \
  --logs /home/user/work/q3-logs/main --evidence-raw /home/user/hadavin-sdk/handover/demo3/evidence/raw \
  --rounds 300 --master-seed 20261113 --deadline-utc 14:05
python tools/q3-soak.py report --logs /home/user/work/q3-logs/main --out evidence/raw/q3-round-table.md
```

The checker call per round (from the round folder): `python load_tools/check_invariants.py --requests requests.jsonl --book data/desk.sqlite3 --catcher mail.jsonl --crm crm.json --model-log model.jsonl --no-require-comparable --json checker.json` with `LEAD_DESK_PATH_ROOTS` set to the round folder. The soak script was edited once after the 4-round trial (an `--outbox` option, default keyed) before the 300 rounds; the trial and self-test outputs are not part of the 300.

## Raw files (`evidence/raw/`)

- `q3-rounds.jsonl`: one JSON line per round (seed, N, kills with type/point/outcome/exit code, restarts, assertion details, checker exit and failures, desk and fakes ports, timings).
- `q3-round-table.md`: the per-round table (round, seed, N, planned sends, kills, restarts, A1, A2, A3, checker exit, seconds).
- `q3-round-logs.tgz`: per-round desk log (all restarts appended), fakes log, request log, mail list, CRM dump, checker output (the book files were kept only for violating rounds, so none).
- `progress-Q3.txt`: start, every 25 rounds (UTC and IST) and end lines. `q3-rounds-partial-1246.jsonl`: one 10-minute snapshot. `q3-pids.txt`: PIDs started.
