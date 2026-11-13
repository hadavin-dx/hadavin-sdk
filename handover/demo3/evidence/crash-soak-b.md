# Crash soak B (agent Q3b): second seed, N=5, double kills

Evidence only. Product code at public main f3c39cf89ec989f032ea48a23cfd824b88da9c68 (private worktree /home/user/work/q3b-base), Python 3.12 venv. Run 2026-11-13 12:49:28Z to 13:02:57Z (18:19 to 18:33 IST), 13.5 minutes. Loopback only, ports 25000-25999, one process at a time.

## Summary

| rounds | violations | hangs | seeds | double-kill rounds |
|---|---|---|---|---|
| 300 (rounds 1-300) | 0 | 0 | master seed 20261114, per-round seed `20261114-<round>` | 150 (rounds 151-300) |

Other counts, all from raw/q3b-rounds.jsonl:
- Harness errors: 0. Rounds where the desk never became idle: 0.
- Every round: 5 leads, 5 mails, 5 follow-ups in state `sent` (1500 of 1500). Planned sends per round 7 to 12 (each round has person 1 through two doors and person 2 as an exact replay).
- `load_tools/check_invariants.py`: exit 0 in 300 of 300 rounds.
- Rounds 1-150: 1 kill each, 150 kills (81 at a documented crash point, 69 at a random time), all fired.
- Rounds 151-300: 2 kills each (300 kills): first kill 92 crash point and 58 random time, all fired. Second kill (during the restart's recovery): 104 SIGKILL after a random 0 to 1.5 s delay, 11 crash-point kills that fired, 35 crash-point kills that did NOT fire (flag armed but the point was not reached before 2 s, so the desk was SIGKILLed instead).
- Slowest round 5.32 s (limit 120 s). No leftover desk or fakes process of mine at the end (checked with ps); PIDs in raw/q3b-pids.txt.

## Violations

None found. Nothing to quote. Note this is a result of 300 rounds of one harness; it is not a proof.

## Gaps and honest limits

- 35 of 46 recovery crash-point kills did not fire. The point-based second kill is therefore mostly a plain SIGKILL during recovery. The 104 time-based second kills land 0 to 1.5 s after spawn; the harness does not record whether the desk was already serving by then.
- The harness does not record the book contents of clean rounds (the data folder of a clean round is deleted by Q3's logic); only counts and checker results are kept. Violations would have kept the book, desk log and mail list.
- Not run: the full repo test suite, any other build.

## Harness differences vs Q3 (copy of q3-soak.py, edited only as below)

1. Master seed 20261114 (Q3: 20261113). Output names q3b-*, progress-Q3b.txt.
2. Ports: desk 25000+off, fakes 25500+off, off 0-499 (Q3: 18100/18600).
3. Leads per round fixed at 5 (Q3: random 5 to 40). Person 1 always sent through both doors; person 2 always replayed exactly; others random at 30%.
4. Kills: rounds 1-150 one kill (Q3: 1, or 2 at 30%). Rounds 151-300 always two. After kill 1 the desk is started without waiting; kill 2 hits it during recovery (random SIGKILL delay 0 to 1.5 s, or a random crash point with traffic for up to 2 s), then a normal restart, resend of all leads, wait idle, assertions, checker.
5. Assertions unchanged (no lead twice, one mail per key and per address, no lead lost, checker).

Files: tools/q3b-soak.py, raw/q3b-rounds.jsonl, raw/q3b-rounds-table.md, raw/q3b-run.out, raw/q3b-pids.txt, raw/progress-Q3b.txt. Full per-round logs: /home/user/work/q3b-logs/main/.
