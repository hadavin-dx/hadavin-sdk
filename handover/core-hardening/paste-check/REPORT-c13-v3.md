# REPORT-c13-v3 (builder, Sonnet 5.5): fix pass 3 on the gate rows. Not a verdict; the lead runs the reviews.

## Failed, not checked, uncertain (first)
- **Nothing ran on the real stack.** Tests are bash and dash on Linux with a stand-in `env.sh` and `pgq` and made-up JSON. No n8n, Postgres, Git Bash, WSL or CRLF files on the laptop. A real `pgq` was not tested (stand-in only; nit "real pgq" stays open until the laptop run).
- **`drive.py` is still not on disk.** UNVERIFIED: `RI=3`, the `replies` list, the `keys.txt` shape (one line per case or per send; G2 tolerates repeated lines with the same id, stops on two different ids), that the id equals `lead_key`, the lease length, and whether 11.8's A and B lines carry `mails` and `model_calls`.
- **G2 baseline gap:** an id stored in the database earlier by other means is still not excluded (P-C2 printed `0`; not checked step by step).
- **My slip:** a redirect with an unset variable created an empty-root file `/syntax-check-output.txt` (356 bytes, root-owned, outside the project). The safety check blocked my `rm`; the lead or owner must delete it. Nothing else outside `paste-check/` and my scratchpad was written; no `/tmp/blk_*`.
- `plan-v6-real-v5-edits.md` / `plan-v7-real-v5-edits.md` (other mechanism) not tried with this patch. Nothing committed or pushed.

## Which repin patch the chain uses
`plan-v5-repin-v6.patch` (10:33). `LEAD-CHECKLIST-v5.md` and `LEAD-FILL-list-v5.md` say v6 only and call v5 and older replaced. Last round I tested v5; the gate-rows patch is now rebuilt on fixes then v6 (the v5 chain also still applies, with offsets, dry run only). Chain: fixes, repin-v6, gate-rows.

## Done, by finding
- **R2-1:** G1-B passes only on exactly 1 false reply (0 and 2 or more FAIL; tested).
- **R2-2:** S10 paste saves `wc -l < keys.txt` (0 if absent) to `$T/keys-before-s10.txt` before drive A. G2 reads only lines after it, needs exactly one distinct A id and one distinct B id, prints before/after counts, KA and KB; stale rows before the baseline stop (tested). The false "other readers" sentence is replaced with the true one (first match, `tail -n 1`, print every match; G2 is stricter).
- **R2-3:** the two history notes (plan lines 23 and 73) now say: re-pin patch made it 172 min, gate rows made it 174 min = 2 h 54 min, which section 5 says now. **R2-4:** S10 heading now 7 min.
- **Nits:** RIOK is set only from a line the lead writes (plan text); `int(RI)` inside the guard (abc, empty, -1 and 4 tested, no traceback); CR stripped from keys and counts; `LC_ALL` exported; `pgq` stderr to `$T/gate2.err` (tested); STOP text names the base version (line 353 of v5, 373 patched); Q18 "psql count" vs `pgq` explained in the plan text; section 4 recounted (8 hunks, listed); new tests: dict replies, 0/1 instead of true/false (at RI and at n8n_error), trailing non-JSON lines (ignored), broken last `{` line, no JSON, missing file, replies not a list, baseline missing, empty, non-numeric, quote in key, pgq failure, missing keys.txt. The 13.8 copy list also gets `gate2.err` and `keys-before-s10.txt`.

## Evidence (raw files in `paste-check/gate-rows/`)
- `gate-rows-test-output.txt`: 25 G1 and 19 G2 cases per shell plus the baseline command (file absent gives `0`, 3-line file gives `3`). `GATE1 ROW: PASS` twice per shell (normal case, trailing-lines case); `GATE2 PASS` 4 times per shell (normal, spaces and CR, CRLF keys with baseline 0, repeated same ids). Every other case printed FAIL or STOP. bash and dash output identical (diff clean after removing the shell label). Blocks were extracted from the patched plan, not from the .sh files.
- `syntax-check-output.txt`: `bash -n` and `dash -n` rc 0 on both blocks and the S10 line as they sit in the patched plan; blocks identical to `G1.sh` and `G2.sh`; G1's embedded Python parses.
- `patch-chain-output.txt`: fixes rc 0, repin-v6 rc 0, gate-rows dry run rc 0, apply rc 0, result identical (cmp) to the prepared copy; second dry run rc 1; `git apply --check` rc 0; wrong order: 7 of 8 hunks fail (rc 1); `inputs/` sha256 unchanged (starts `67a0a195537de875`). Line 18's "rc=0" is `tail`'s; the real rc is the last line (1).

## Files
`GATE-ROWS-resmoke.md` (v3), `plan-v5-gate-rows.patch` (122 lines, 8 hunks; v2 kept as `plan-v5-gate-rows-v2.patch`), `gate-rows/G1.sh`, `G2.sh`, `run-tests.sh`, the three outputs, this report.
