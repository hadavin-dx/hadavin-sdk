# Crash soak in BLIND mail mode (evidence runner Q3c)

Public main f3c39cf89ec989f032ea48a23cfd824b88da9c68 (worktree `/home/user/work/q3c-base`, Python 3.12, `git status` of the worktree: 0 changed files). Main run 2026-11-13 13:10:13Z to 13:24:36Z (18:40 to 18:54 IST). This file records raw results and my classification; I did not change product code.

## Summary

| rounds | violations A | violations B (documented) | violations C (undocumented) | unknown follow-ups | hangs | kill points fired vs not fired |
|---|---|---|---|---|---|---|
| 300 of 300 (master seed 20261115, round n = seed string `20261115-n`) | 0 | 197 follow-ups in 70 rounds | 0 | 197 (all `crash_while_sending`), every one listed in `GET /review` | 0 (longest round 4.98 s) | point kills 229 fired / 0 not fired (Q3: 239 / 18 not fired); random-time kills 156, all ended the desk |

Answer to the open question: the `unknown` follow-ups that Q3 saw in blind mode are the DOCUMENTED behaviour, not a defect. Check 2 of `load_tools/check_invariants.py` fails only because its default allowance for `unknown` is 0 (`check_invariants.py:46-47`, `--max-unknown`). With `--max-unknown 100000` the checker exits 0 in 300/300 rounds; with the default it exits 1 in 70/300 rounds and every failing line is check 2 only.

Things I did not check: the real HubSpot/SMTP adapters, a blind CRM (CRM was keyed, the fakes default), reminders (N1), power loss, a person pressing Retry or "not sent" (no person action was simulated), whether `GET /api/ui/review` also lists each unknown (I only checked `GET /review`; the code did not store the portal-API result), one long-lived book across rounds (fresh book per round).

## What the documents promise for blind mode and `unknown` (plain words, file:line)

1. UNKNOWN means the desk cannot tell whether a follow-up email left; it does not guess, does not resend, and a person must check (`README.md:40`).
2. The desk does not send a follow-up twice by itself; an unconfirmed send is listed for a person (`README.md:99-100`). A wrong "not sent" answer by a person can cause a second email on a blind mail system (`README.md:100`, `docs/limits.md:12`, `docs/limits.md:74`).
3. Crash table for a blind mail system (`docs/tests.md:98-110`): A, A2, B, L, D1, D3 give one email; D1b gives no email and UNKNOWN; D2 gives one email and UNKNOWN. C0 and C1 depend on the CRM kind, not the mail kind (a keyed CRM, used here, gives one row and one email).
4. A send that may have started and ends unclear on a blind sender goes to `unknown` at once; a `sending` row put back by a restart or the reaper goes to `unknown` when its send may have started, to `pending` when it never sent (`contract.md:47`, `contract.md:256`, `contract.md:295-297`, `docs/limits.md:77`, `desk.py:542-575`). The stored reason for the restart path is `crash_while_sending` (`desk.py:561`).
5. An UNKNOWN row is never resent by the desk; Retry on it answers 409 `unknown_needs_person` (`docs/tests.md:125` P6, `contract.md:195`, `desk.py:2226`). UNKNOWN items stay unseen unless someone opens the review list (`docs/limits.md:75`): no alert is promised.
6. `GET /review` lists each unknown follow-up as item `F<lead_id>`, kind `unknown` (`contract.md:192`). `/counts` carries `unknown_followups` and `ok` is false while it is above 0 (`contract.md:209`, `contract.md:261`).
7. Checker: check 2 requires states add up, nothing pending or open, and at most `--max-failed` / `--max-unknown` rows ending failed / unknown; default 0 for both; a book where every follow-up is unknown always fails (`check_invariants.py:44-47`, `:283-340`). Check 3 allows no message for failed or unknown rows, but an unknown that did send is "reported, not a failure" (`check_invariants.py:402-410`).

Class rules I used per lead after idle: A = more than one mail from the desk alone, a follow-up `sent` with no mail, a follow-up still pending or sending after idle, an unknown not listed in `GET /review`, two leads or CRM rows per person, any broken A1-A3 assertion, or a checker failure with the unknown allowance lifted. B = state `unknown`, reason `crash_while_sending`, `ambiguous_prior` or `ambiguous`, 0 or 1 mails, listed in `/review` (documented: items 3, 4, 6). C = anything else (a `failed` row, another unknown reason, an unknown with more than one mail).

## Results of the 300 rounds (raw: `raw/q3c-rounds.jsonl`, `raw/q3c-round-table.md`)

- 9154 distinct leads (N per round 5 to 40, plus 3 to 8 fresh leads in every kill phase), 11261 planned sends: 2132 same-person sends through the second door, 2091 exact replays. 215 rounds with 1 kill, 85 with 2 kills (385 kills): 229 crash-point kills (all printed `simulate crash`, exit 137), 156 SIGKILLs at a random time.
- Final state: 8957 follow-ups `sent`, 197 `unknown`, 0 failed, 0 pending or sending; 9154 CRM rows (one per lead); 9100 mails in the blind fake outbox. Mails per lead: 9100 leads had exactly 1 mail, 54 leads had 0 mails, none had 2 or more. All 54 zero-mail leads are `unknown` (the D1b-type case: send marked, mail system not called). Of the 197 unknown: 143 have 1 mail (the email did leave), 54 have none.
- Unknown rounds by the kill that was armed in the round (a round can have two kills, so counts overlap): D2 25, D3 16, D1b 15, random time 31, B 5, D1 4, C1 2, A2 2, L 1.
- All 197 unknown are visible: `GET /review` listed each as kind `unknown` (197 of 197).
- Checker, default settings: exit 0 in 230 rounds, exit 1 in 70 rounds (check 2 only, `unknown` above 0). Checker with `--max-unknown 100000`: exit 0 in 300 of 300 rounds (check 3 "message only for failed or unknown" and check 4 "CRM rows match" held every round).
- Hangs 0, harness errors 0, longest round 4.98 s, every round reached idle.

Why unknown also appears at points where the table says "one email" (A2, B, L, D1, D3, C1): the table describes one follow-up. In a round many follow-ups are in flight, and any of them that is in `sending` with its send mark written when the desk dies becomes `unknown` by rule 4. I checked this with a one-lead probe (`tools/q3c-single-probe.py`, `raw/q3c-single-probe.json`): one lead, blind mail fake, one named point, 10 runs per point, all 100 point kills fired. Result matches `docs/tests.md:98-110` exactly: A, A2, B, L, C0, C1, D1, D3 gave state `sent` with 1 mail; D1b gave `unknown` with 0 mails; D2 gave `unknown` with 1 mail; always 1 lead.

## Reproduction of Q3's 4 failing self-test rounds (master seed 7, rounds 16, 22, 25, 26)

Same seeds, Q3's kill plan unchanged (`--legacy`), blind mail, 30 rounds, run twice (`raw/q3c-legacy-run1-rounds.jsonl`, `raw/q3c-legacy-run2-rounds.jsonl`):

| round | Q3 original (unknown) | my run 1 | my run 2 | kill plan |
|---|---|---|---|---|
| 16 | 2 | 1 | 1 | D2 (fired), then B (not fired, SIGKILL) |
| 22 | 1 | 2 | 5 | D2 |
| 25 | 3 | 0 | 0 | random-time kill at 0.286 s |
| 26 | 1 | 1 | 1 | D1b |

Rounds 16, 22 and 26 reproduce (check 2 fails, only on `unknown`); round 25 did not reproduce in two tries (a random-time kill depends on exact timing, and unknown counts vary with how many follow-ups are in flight, so the counts in the other rounds differ too). The exact failure line of every reproduced round is the same shape, for example round 26 run 2: `2:follow-up states add up and nothing is left pending -> pending 0 + sending 0 + sent 39 + failed 0 + unknown 1 = 40; leads 40; 1 unknown, more than the allowed 0 :: ['L8eb452b10e60']`, reason `crash_while_sending`, 0 mails (class B). Round 25 timing in Q3 was a different load on the machine; I cannot say more.

## Fix of the Q3 harness gap (kill points that never fired)

Cause (from `raw/q3-rounds.jsonl`, all 18 not-fired point kills were the SECOND kill of a round): after the first kill and restart the second kill phase only replays request ids that already have receipts, decided leads and finished follow-ups. A, A2 and B are only reached when a NEW request id creates a receipt (`desk.py:1269`, `:1377`, `:1385`); L, C0, C1, D1, D1b, D2, D3 are only reached when a follow-up has work left (`desk.py:1642-2052`). A flag armed then is never reached before the send phase ends. (Q3b's 35 of 46 had the same cause: kill 2 during recovery with replay-only traffic.)

Fix in my copy `tools/q3c-soak.py`: every kill phase also sends 3 to 8 fresh made-up leads (new request ids, new addresses), and a point kill that has not fired within 5 s is re-armed with another fresh batch, at most 3 attempts. Result: 229 point kills, all fired on the first attempt (attempt count 1 for all 229; the re-arm never was needed); 0 not fired. The original-style plan (`--legacy`) still shows the old gap (rounds 9 and 23 of the legacy run: B and A not fired).

## Class A violations

None.

## Class C violations (UNDOCUMENTED)

None. One wording note for the caller, not a violation: `docs/tests.md:107-110` describes only the one-follow-up case, so a reader of the table alone could think `unknown` cannot appear after a kill at A2, B, L, D1 or D3. With many follow-ups in flight it can (rule 4, `contract.md:47`). This is a documentation gap I did not fix (not my brief).

## Class B (documented non-guarantees seen)

197 unknown follow-ups, 70 rounds, all reason `crash_while_sending`, all with 0 or 1 mails, all listed in `GET /review`. Per-round detail is in `raw/q3c-rounds.jsonl` (`classes.B`); no verbatim block is needed because there is no class A or C case.

## Harness, commands, files

- `tools/q3c-soak.py` (copy of `tools/q3-soak.py`): ports desk 27000-27399, fakes 27500-27899 only (checked free first); `--outbox blind` default; `TMPDIR=/home/user/work/q3c-tmp` (outside every worktree); extra RNG stream so the Q3 draw order stays identical in `--legacy`; classifier A/B/C; checker run twice (default, and `--max-unknown 100000`); `GET /review` and `GET /api/ui/review` fetched after idle.
- `tools/q3c-single-probe.py`: the one-lead probe.
- Main command: `timeout 3000 final-venv/bin/python -I tools/q3c-soak.py run --base /home/user/work/q3c-base --python /home/user/work/final-venv/bin/python --logs /home/user/work/q3c-logs/main --evidence-raw .../evidence/raw --rounds 300 --master-seed 20261115 --outbox blind --deadline-utc 14:10`. Legacy: same with `--rounds 30 --master-seed 7 --legacy`.
- Raw files in `evidence/raw/`: `q3c-rounds.jsonl`, `q3c-round-table.md`, `q3c-round-logs.tgz` (round logs of main and both legacy runs; books removed), `q3c-legacy-run1-rounds.jsonl`, `q3c-legacy-run2-rounds.jsonl`, `q3c-single-probe.json`, `q3c-pids.txt`, `q3c-q3c-rounds-partial-1320.jsonl` and `q3c-snapshot.jsonl` (snapshots), `progress-Q3c.txt` (UTC and IST lines every 25 rounds; it also holds the legacy runs' lines).
- Processes: every process was started by the harness and recorded in the pid file; all were stopped at the end of each round; none left (checked with `ps`; the processes still running on the machine belong to other agents and were not touched).
