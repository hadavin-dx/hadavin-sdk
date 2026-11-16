# Evidence for CORE-PR-HANDOFF-v4 section 4.9 (EVIDENCE RUNNER; raw output, no judgement)

Run date 2026-11-16. Repo HEAD of the read-only source copy: `8b80d61ee2ca226dd840a27b78c1fe7e8d89b74d` (branch `cloud/core-hardening`). The gate under test is the CURRENT ("old") `approvals/gate.py`; nothing was edited.

## Surprises and failures first

1. **No claim in v4 was contradicted** for any example v4 gave a definite claim for: 0 mismatches in the table below (every row says yes or n/a).
2. **v4 marks two rows "candidate / not traced"; the run shows them differently from what "candidate" suggests:**
   - `git rebase -i HEAD~3` (G5b): the current gate ALREADY WITHHOLDS it. Under v4's own rule (4.9: only rows that leak on old code ship) this row is dropped, not a candidate.
   - `KUBECTL.EXE delete ns prod` (G2c): `withhold_commands` leaves it SHOWN, but `channel.clean` (the real display path) rewrites the dot to `KUBECTL[.]EXE`, so the reader sees a defanged, non-pasteable string. It is a partial leak at most; whether that counts is for the reviewer.
3. **The G3 lowercase examples are all shown today, as v4 says, but v4's "Today" column only states "leaks (lowercase and alias)" for the whole row**; I treated "shown" as the implied claim for each of the 12 lines (F2: no ignore-case). If the lead meant something else for a specific line, the observed column is the fact.
4. **v3's example `> /dev/null kubectl delete pod x` IS withheld today** (output `> /dev/null [command withheld (G4)]`), confirming v4 section 0 item 2(b) that it was not the real bypass; `kubectl > /dev/null delete pod x` is shown (the real bypass), confirmed.
5. The instruction said `python -I` with `PYTHONPATH`. `-I` ignores `PYTHONPATH`, so the read-only source copy was put on the path by `sys.path.insert` at the top of `probe.py` (path passed as an argument). Same effect, stated so nobody thinks the env variable was used.
6. The first `pytest` run happened with three AWS environment variable NAMES present in the sandbox (`AWS_SECRET_ACCESS_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_CA_BUNDLE`; values never read or printed); I unset only two of them for that run. I then re-ran with all three unset. Both runs: 125 passed. Both logs are saved.
7. An untracked file `handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v4.md` appeared in the repo during my run. I did not create or touch it.

## What was run (exact commands)

Registry reachable: yes.
- Scratch venv outside the repo: `python3 -m venv <scratchpad>/venv`
- `<scratchpad>/venv/bin/pip install markdown-it-py` installed 4.3.0 first; then, to match the repo pin (`pyproject.toml`: `markdown-it-py==4.2.0`), `pip install "markdown-it-py==4.2.0"`. **The probe ran on markdown-it-py 4.2.0.** The gate imports `markdown_it` at `gate.py:72`.
- `pip install pydantic==2.14.1 pydantic-settings==2.16.1 pyyaml==6.0.3` (needed because `approvals/__init__` imports `models`, which imports pydantic). Full list: `raw-v4/pip-freeze.txt`.
- Read-only copy: `cp -r src <scratchpad>/srcro && chmod -R a-w <scratchpad>/srcro`.
- Probe: `<scratchpad>/venv/bin/python -I raw-v4/probe.py raw-v4/probe.json <scratchpad>/srcro`. Functions called: `hadavin_sdk.approvals.gate.withhold_commands(text)` and `hadavin_sdk.approvals.channel.clean(text)`. "withheld" = the string `[command withheld (G4)]` appears in the output; "shown" = output equals input. Exact outputs for every example: `raw-v4/probe.txt` and `raw-v4/probe.json`.
- Scratch repo copy (tar, no `.git`, no wheel files): `uv run --all-extras --group test pytest tests/test_g4_parity.py -q -p no:cacheprovider`, run alone, timeout 1200 s. Result: `125 passed in 0.62s` (rc 0), and with all AWS variables unset `125 passed in 0.31s` (rc 0). Logs: `raw-v4/pytest-g4-parity.log`, `raw-v4/pytest-g4-parity-nocloud.log`. The in-place repo was not used for the test run.

## Table: example | v4 claims on old code | observed on old code | match?

Legend: claim "shown" = v4 says the gate leaks it or must keep it; "withheld" = v4 says the gate withholds it today. "candidate-untraced" = v4 said not traced. The G3-01..G3-12 rows are the twelve lines of the 4.9 G3 table; T98, T221, T222 are `tests/test_g4_parity.py` lines 98, 221, 222 (all three are asserted to stay shown there, and are).

| id | example (Python repr) | v4 claims on old code | observed: withhold_commands | observed: channel.clean | match? |
|---|---|---|---|---|---|
| G3-01 | `` 'drop table users;' `` | shown | shown | shown | yes |
| G3-02 | `` '`drop table users`' `` | shown | shown | shown | yes |
| G3-03 | `` 'delete from users where id = 1' `` | shown | shown | shown | yes |
| G3-04 | `` 'update only t as a set x=1' `` | shown | shown | shown | yes |
| G3-05 | `` 'insert into t values (1)' `` | shown | shown | shown | yes |
| G3-06 | `` '$ drop table users' `` | shown | shown | shown | yes |
| G3-07 | `` 'drop table pressure' `` | shown | shown | shown | yes |
| G3-08 | `` 'we should delete from the queue only after a fix' `` | shown | shown | shown | yes |
| G3-09 | `` 'update its set of rules' `` | shown | shown | shown | yes |
| G3-10 | `` 'delete from the queue where possible' `` | shown | shown | shown | yes |
| G3-11 | `` 'drop table users' `` | shown | shown | shown | yes |
| G3-12 | `` 'we will drop table pressure; then rest' `` | shown | shown | shown | yes |
| G3-UP-1 | `` 'UPDATE t AS a SET x=1' `` | shown | shown | shown | yes |
| G3-UP-2 | `` 'UPDATE ONLY t SET x=1' `` | shown | shown | shown | yes |
| G3-UP-0 | `` 'UPDATE t SET x=1' `` | withheld | withheld | withheld | yes |
| G3-UC-1 | `` 'DROP TABLE users' `` | withheld | withheld | withheld | yes |
| G3-UC-2 | `` 'DELETE FROM users WHERE id = 1' `` | withheld | withheld | withheld | yes |
| G2a-W | `` 'kubectl \\\ndelete ns prod' `` | shown | shown | shown | yes |
| G2a-W-caret | `` 'kubectl ^\ndelete ns prod' `` | shown | shown | shown | yes |
| G2a-W-tick | `` 'kubectl `\ndelete ns prod' `` | shown | shown | shown | yes |
| G2a-S | `` 'we wrap lines with a backslash \\\nlike this' `` | shown | shown | shown | yes |
| G2b-W | `` 'kubectl > /dev/null delete pod x' `` | shown | shown | shown | yes |
| G2b-v3 | `` '> /dev/null kubectl delete pod x' `` | withheld | withheld | withheld | yes |
| G2b-S | `` 'the aws Lambda runtime' `` | shown | shown | shown | yes |
| G2c-W | `` 'KUBECTL.EXE delete ns prod' `` | candidate-untraced | shown | changed | n/a (untraced) |
| G2c-S | `` 'the tf module was reviewed' `` | shown | shown | shown | yes |
| G4a-W | `` 'rm -v -rf /x' `` | shown | shown | shown | yes |
| G4a-S | `` 'rm the file' `` | shown | shown | shown | yes |
| G5a-W | `` 'aws secretsmanager get-secret-value --secret-id x' `` | shown | shown | shown | yes |
| G5a-S | `` 'aws s3 ls' `` | shown | shown | shown | yes |
| G5b-W | `` 'git rebase -i HEAD~3' `` | candidate-untraced | withheld | withheld | n/a (untraced) |
| G5b-S | `` 'the docker image was rebuilt overnight' `` | shown | shown | shown | yes |
| PIN-kubectl | `` "a 'kubectl rollout restart' replaced the pods" `` | shown | shown | shown | yes |
| T98 | `` 'update its set of rules' `` | shown | shown | shown | yes |
| T221 | `` 'we should delete from the queue only after a fix' `` | shown | shown | shown | yes |
| T222 | `` 'drop table pressure' `` | shown | shown | shown | yes |

Extra rows not listed as examples in v4 (G2a variants with `^` and backtick, upper-case controls G3-UP-0, G3-UC-1, G3-UC-2, v3 example G2b-v3) are marked in raw-v4/probe.py; they are my controls, not v4 claims, except G2b-v3 and the upper-case "withheld" statements in 4.9.

Observed texts for the interesting rows (from probe.txt): `UPDATE t SET x=1` -> `[command withheld (G4)] x=1`; `UPDATE t AS a SET x=1` and `UPDATE ONLY t SET x=1` unchanged (the alias gap is real); `rm -v -rf /x` unchanged; `aws secretsmanager get-secret-value --secret-id x` unchanged; `kubectl \<newline>delete ns prod`, the `^` and backtick forms, and `kubectl > /dev/null delete pod x` unchanged.

## What I did NOT check

- The v4 fixes (new code): none exist yet, so no "new code" column; no test was run against changed code.
- Behaviour on the whole recorded corpus, the 200-sentence false-positive rate, the 4.9 candidate rows not given as examples (dd, mkfs, chmod -R, kill, shutdown, crontab -r, sed -i, rsync --delete, tee, curl -X DELETE, PowerShell, and the rest), and the other items in section 7 (E0-1 to E0-5, E0-7 to E0-9).
- Whether the stray G2a examples differ when preceded by other prose or inside fenced code (marker M2 fence handling).
- The full test suite, ruff, bandit, mutation runs, Postgres.
- The `perf`-marked timing test in `test_g4_parity.py` is not deselected by `pyproject.toml`, so it was part of the 125; I did not read its timing numbers.

Files: `raw-v4/probe.py`, `probe.txt`, `probe.json`, `table.md`, `pytest-g4-parity.log`, `pytest-g4-parity-nocloud.log`, `pip-freeze.txt`. Spend: none. Secrets: none printed.
