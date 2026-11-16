# REPORT-c13-v2 (builder, Sonnet 5.5): fix pass on the gate rows. Not a verdict; the lead runs the reviews.  **[SUPERSEDED by REPORT-c13-v3.md (patch plan-v5-gate-rows-v3.patch)]**

## Failed or not checked (first)
- Nothing ran on the real stack; tests are bash and dash with a stand-in `pgq` and made-up JSON. `drive.py` is not on disk, so `RI=3`, the `keys.txt` shape, the lease length and whether 11.8's A and B lines carry `mails` and `model_calls` are all UNVERIFIED (named in the plan text).
- No A/B count was recorded before S10, so stale rows could let G2 pass; stated in the plan text, not fixed (it would need a new pre-S10 command; I judged a low risk because P-C2 printed 0 and I found no earlier A or B send, not checked step by step). The lead may want a baseline command; tell me and I add it.
- G1-B still passes with 0 "not repeat" replies (the S10 rule allows it); now written down, not changed.
- Not tried: `plan-v5-repin-v6.patch` (10:33, exists on disk) and the v6 edit list with this patch. The chain tested is fixes, repin-v5, gate-rows.
- I wrote two scratch files under `/tmp/blk_*` during the syntax check (deleted); everything else in the scratchpad.

## Done, by review finding
1. Readiness M1: G1 now requires index 4 (`n8n_error`) to be true/false and false in every reply (tests: A and B with an error reply fail). `RI=3` default, UNVERIFIED, cited to plan line 353 (373 patched). One rule: `RIOK=` must be set to `yes` by the lead after reading `drive.py`; empty `RI` or `RIOK` prints STOP (tested in both shells).
2. Readiness M2 / facts: caption needs 11.8 `mails == 1` and `model_calls == 1` positively reported, else the shrunk caption; the lead states the lease number first (in the patch's Decision paragraph); the "flow's own claim step" line is deleted.
3. Readiness M3: G2 prints `GATE2 count: N` then `GATE2 PASS` or `GATE2 FAIL: STOP`, test `[ "$N" = 2 ]`, spaces and CR stripped, `LC_ALL=C` in a subshell. Notes added: G2 counts A and B together; stale rows can pass.
4. Facts M1: rows numbered S10-G1 and S10-G2; section 7 header 21 to 23 rows plus both rows; section 5 S10 5 to 7 min, steps 152 to 154, total 172 to 174 min = 2 h 54 min (three text places incl. the header line 6). There is no separate claims table in the patch; section 7 is the claims table.
5. Facts M2 / nits: plan line 281 cited for the primary key; `ANSWER-Q18-lead.md` cited as the source; file names corrected to `gate-rows/`; shells labelled; the stale first-version block deleted (output regenerated).

## Evidence (raw files in `paste-check/gate-rows/`)
- `gate-rows-test-output.txt`: 15 G1 cases and 11 G2 cases in each of bash and dash. `GATE1 ROW: PASS` appears 4 times (pass case and the allowed "B all repeat" case, twice each shell), `GATE2 PASS` 4 times (count 2 and the CR/space case, each shell); every failure shape printed FAIL or STOP. Bash and dash output identical apart from the label (diff clean).
- `syntax-check-output.txt`: `bash -n` and `dash -n` rc 0 on both blocks as they stand in the patched plan and on the changed S10 line; blocks identical to `G1.sh` and `G2.sh`.
- `patch-chain-output.txt`: fixes patch rc 0, repin-v5 as on disk rc 0, gate-rows dry run rc 0 and apply rc 0, result identical (cmp) to the prepared copy; applying gate-rows first fails (5 of 6 hunks); real `inputs/` file unchanged (sha256 starts `67a0a195537de875`).

## Files
`GATE-ROWS-resmoke.md`, `plan-v5-gate-rows.patch` (98 lines, 6 hunks), `gate-rows/G1.sh`, `gate-rows/G2.sh`, the three outputs, this report. No other builder's files touched; nothing committed.
