# GATE-ROWS-resmoke, version 3 (C13 fix pass 3 after the round-2 reviews, `review-c13-r2.md`). Plan text for the studio lead. Builder: sub-agent (Sonnet 5.5). NOT a verdict: the lead runs the EGM reviews (EGM-GATE v1).
Source of the rule: `handover/core-hardening/ANSWER-Q18-lead.md`, Q18 item 2 ("loopback re-smoke cases A and B (same id twice) plus one psql count on mf_leads are the explicit pass/fail gate"). Round-1 and round-2 reviews: `review-c13-readiness.md`, `review-c13-facts.md`, `review-c13-r2.md`. Current chain: `plan-v5-fixes.patch`, then `plan-v5-repin-v6.patch` (the one `LEAD-CHECKLIST-v5.md` names; v5 and older are replaced), then `plan-v5-gate-rows.patch`.

## 0. Read first: what failed, what is uncertain, what I did not check
1. **Nothing was run on the real stack.** Both commands were tested only in bash and dash here, against a stand-in `env.sh` whose `pgq` prints a number I choose, and against made-up JSON files I built from the reply shape in the plan. No Postgres, n8n, Docker or WSL. Raw output: `gate-rows/gate-rows-test-output.txt` (every case labelled with its shell; bash and dash output are identical after removing the shell label; 25 G1 and 19 G2 cases per shell, plus the baseline command).
2. **`drive.py` is not on disk.** UNVERIFIED, not read from any file:
   - the position of the repeat flag. G1 now uses `RI=3`, taken from the reply shape `[status, verdict, lead_key_ok, repeat, n8n_error, tries]` printed at plan line 353 of v5 (373 after the fixes and re-pin patches). That is the plan's own text about `drive.py`, not `drive.py`.
   - that the last JSON line of the A and B output has a `replies` list (read in the plan only for B2, plan line 349 of v5).
   - that `$T/keys.txt` has lines `A <id>` and `B <id>` (plan readers use `$1` = case, `$2` = id for B2 and C; A and B lines are inferred), and that the id equals `lead_key` (plan line 281: `lead_key text PRIMARY KEY`).
   - the lease length (not in the plan; the C14 check says "45 s" second-hand only).
   - whether the A and B lines of 11.8 carry `mails` and `model_calls` (the plan names them for the C line in 11.5).
3. **Safe rule for `RI`:** the paste carries `RI=3 RIOK=` and prints a STOP line until the lead has read `drive.py`, confirmed the index and WRITTEN the line that sets `RIOK=yes`; the runner only copies that line and never sets `RIOK` itself (plan text says so). Empty or non-numeric `RI`, a negative `RI`, `RI=4`, and an `RIOK` other than `yes` all stop (tested; `int(RI)` is now inside the guard, no traceback). I did not test every possible wrong index.
4. **G1-B now passes only on exactly 1 reply that is not a repeat** (R2-1). Zero (stale or reused id) and two or more are FAIL; tested. This is stricter than the S10 rule ("at most 1"); the plan text says so.
5. **G2 limits:** it counts the A id and the B id together; a second row for one id cannot exist (primary key), so G2 shows nothing was lost, not that the second send was recognised (that is G1). The S10 paste now saves the line count of `keys.txt` to `$T/keys-before-s10.txt` before drive A (0 if the file is absent, tested); G2 reads only lines after it and needs exactly one distinct A id and one distinct B id (R2-2), printing both ids and the line counts. An id stored in the database earlier by other means is not excluded (P-C2 printed `0`). Whether `drive.py` writes one `keys.txt` line per case or per send is UNVERIFIED: G2 accepts repeated lines with the same id, and stops on two different ids.
6. **Patch chain:** valid only in this order: `plan-v5-fixes.patch`, `plan-v5-repin-v6.patch`, `plan-v5-gate-rows.patch` (8 hunks). Tried: rc 0 dry run, rc 0 apply, result identical to the prepared copy; wrong order fails. `plan-v6-real-v5-edits.md` and `plan-v7-real-v5-edits.md` (a different edit mechanism) were NOT tried with it.
7. **PASS here does not mean PASS on the laptop** (Git Bash path forms, WSL, CRLF). The commands use only `awk`, `case`, `tr`, `python3 -I`, `tee`, `head`, plus the plan's own `pgq` and `$T`. `LC_ALL=C` is set inside a subshell in G2 (dash ignores locale; bash tested).

## 1. What the two rows decide (plain words)
The video caption needs both rows PASS, and more (section 3). G1 checks what the system **said back** to the two sends. G2 checks what the database **kept**. Neither alone is enough.

## 2. The gate rows (numbered S10-G1 and S10-G2; each has a row in plan section 7 and minutes in section 5, 1 min each, S10 now 7 min, heading and section 5 agree, total 174 min = 2 h 54 min)
Both run straight after the S10 paste. The S10 paste now ends cases A and B with `| tee $T/gate1-A.out` and `| tee $T/gate1-B.out`; the 13.8 copy list gets `gate1-*.out gate2.out`. Case P unchanged.

### S10-G1 (file `gate-rows/G1.sh`, first fenced block of the patch)
| field | content |
|---|---|
| input | `$T/gate1-A.out`, `$T/gate1-B.out` |
| checks | shape: a `replies` list; in every reply a true/false at `RI` (3) and at index 4 (`n8n_error`); `RI` is not 4. A: exactly 2 replies, `[False, True]`. B: exactly 10 replies, exactly 1 false. Both: `n8n_error` false in every reply |
| expected | `GATE1-A replies=2 repeat_false=1 repeat_true=1 first_repeat=False n8n_error_true=0`, `GATE1-A PASS`, `GATE1-B replies=10 repeat_false=1 repeat_true=9 first_repeat=False n8n_error_true=0`, `GATE1-B PASS`, `GATE1 ROW: PASS` |
| pass rule | last line is `GATE1 ROW: PASS` |
| does NOT prove | one mail and one model call (F lines of 11.8); lease expiry; recovery; real CRM node; real model; status code and verdict word (read by eye, REC) |
| on fail | STOP (R1); no caption; the lead reads the saved files; no S10 re-run on this take without his written go |

### S10-G2 (file `gate-rows/G2.sh`, second fenced block)
| field | content |
|---|---|
| input | `$T/keys-before-s10.txt` (line count saved before drive A) and the A and B lines of `$T/keys.txt` after that count (exactly one distinct id each) |
| command | one `SELECT count(*) FROM mf_leads WHERE lead_key IN (<A>, <B>)` by role `smk_count`, database `postgres` (same as P-C2); saved to `$T/gate2.out`, errors of `pgq` to `$T/gate2.err` |
| expected | `GATE2 count: 2` then `GATE2 PASS`; the test is `[ "$N" = 2 ]` after stripping spaces and CR |
| other results | `0`, `1`, empty: `GATE2 FAIL: STOP`. Baseline file missing or not a number, not exactly one A id and one B id after it, ids the same, or with a character outside `A-Za-z0-9_-`: a STOP line before any query |
| limits | section 0 items 5 |
| on fail | STOP (R1); the lead decides; rows are never edited to "fix" it |

## 3. Caption rule (only on PASS of both rows)
1. The lead first states the lease length, a number he read from the flow (not from this file).
2. Caption "a lead sent twice with the same id inside the lease is processed once" ONLY IF the 11.8 lines for A and B positively report `mails == 1` and `model_calls == 1`. Not reported or not 1: only the shrunk caption "a repeat of the same id was recognised as a repeat and one row was stored".
3. Never in the same caption: lease expiry, crash recovery, real HubSpot, a real model, "never". Row DM or 11.8 finding a double mail blocks the caption.
(The earlier line "the answer comes from the flow's own claim step" is deleted; it was not verified.)

## 4. Files (all under `paste-check/`)
- `gate-rows/G1.sh`, `gate-rows/G2.sh`, `gate-rows/run-tests.sh`: the two commands and the test script (blocks are extracted from the patched plan) (the patch blocks are byte-identical, checked).
- `plan-v5-gate-rows.patch` (98 lines, 6 hunks: S10 paste tee, the new block, section 5 estimate (3 places incl. the header line), section 7 table (header 21 to 23 rows plus the two rows), 13.8 copy list).
- Test output: `gate-rows/gate-rows-test-output.txt` (fully regenerated; the stale first-version block is gone), `gate-rows/syntax-check-output.txt`, `gate-rows/patch-chain-output.txt`.

## 5. Open items for the lead (each needs a person)
1. Read `drive.py`: confirm `RI=3`, then set `RIOK=yes`. Confirm `keys.txt` A and B lines and that the id is `lead_key`.
2. State the lease length from the flow before any caption.
3. Check whether 11.8's A and B lines report `mails` and `model_calls`; if not, only the shrunk caption is allowed.
4. Run the EGM reviewers on this fix pass (round 2).
