# Evidence round 5 (F8 flow checker) - EVIDENCE RUNNER, raw results, no judgement

Date 2026-11-16. Working copy: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/handover/ (copies of flows-audit/flow-check, flows-audit/patches, demo/n8n-flows-real-v5, n8n-flows-v4, n8n-flows-film-v5, n8n-flows, n8n-mainframe, VIDEO-RUNSHEET.md). Originals untouched. The copy of check_flows.py is byte-identical to the repo file (cmp). Nothing was run in n8n. Made-up data only.

## FAILURES AND SURVIVORS FIRST

No command in sections 1-2 failed. Section 3: 10 of 25 mutants SURVIVED the self-test (exit 0, "629 as expected, 0 not as expected"):

| # | line | mutation | kind |
|---|---|---|---|
| 1 | 352 | `f"node {n['name']}: the query uses column(s) {miss} that the --ddl fil` -> `f"node {n['name']}: the query uses column(s) {miss} that the --ddl fil` | message text only |
| 3 | 890 | `f"{len(phs)} id(s) are still placeholders and must be replaced in n8n ` -> `f"{len(phs)} id(s) are still placeholders and must be replaced not in ` | message text only |
| 4 | 14 | `--quiet-info                  do not print the type table and the plac` -> `--quiet-info                  do print the type table and the placehol` | help text only |
| 8 | 519 | `if v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "":` -> `if v in PLACEHOLDERS and v.replace(AWS_EXAMPLE, "") == "":` | operator: value_is_safe() 'or' -> 'and'; no self-test case separates them |
| 9 | 212 | `"in",` -> `"not in",` | string in SQL stop-word tuple (not an operator) |
| 11 | 61 | `PARAM_PH = []  # placeholders found in node settings (not credential i` -> `PARAM_PH = []  # placeholders found in node settings (credential ids):` | code comment only |
| 12 | 177 | `"Not proven: that n8n accepts these files on import; what n8n really d` -> `"Not proven: that n8n accepts these files on import; what n8n really d` | message text only |
| 19 | 62 | `SQL_DONE = {"checked": 0}  # queries compared with the --ddl table def` -> `SQL_DONE = {"checked": 1}  # queries compared with the --ddl table def` | initial counter 0 -> 1 (SQL_DONE); no case reads the 'compared' count when 0 queries are read |
| 24 | 1663 | `"no --ddl file was given: the columns used in the SQL queries were NOT` -> `"no --ddl file was given: the columns used not in the SQL queries were` | message text only |
| 25 | 1508 | `quiet = True` -> `quiet = False` | --quiet-info parser sets quiet=False instead of True: the flag has no tested effect |

Other findings from the hostile inputs (section 4), stated as seen:
- A flow file that is not valid UTF-8 / not JSON (mf-bad.json) produced only the file-list mismatch FAIL; no separate line about that file being unreadable (grep for "mf-bad" gives line 13 only).
- A non-UTF8 --ddl file ends in exit 3 "INTERNAL ERROR ... UnicodeDecodeError" (documented meaning of exit 3: the checker itself broke), not exit 2 usage error.
- --ddl without the alert_* columns gives WARN only (exit 0), 4 query strings flagged on real-v5 (AlertClaim, one more, and two others), "RESULT: 0 FAIL, 25 WARN".
- Tool versions: local ruff is 0.16.9; repo pyproject pins ruff==0.17.1 (not available here), so lint/format results are from 0.16.9.
- First mutation run (before widening the pool) found only 13 mutable lines among the 104 lines added in round 5, so the pool was widened to added lines plus lines matching ddl|placeholder|saveData|unv(|quiet (162 lines), as the brief allows.

## 1. run_all.sh and take_check.sh (from the copy, rc taken directly, no pipe)

- `bash run_all.sh` : rc=0 (run twice: 8.5 s wall each; last line "OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s)...").
- Summary lines: selftest exit=0 "SELFTEST: 629 as expected, 0 not as expected, 62 skipped (not applicable)"; take_check.sh exit=0 "missing lines: none"; "run_all exit status (real-v5 default runs + self-test): 0"; "real-v5 placeholder ids: 8 file(s) warn".
- film-v5 (not gating): pristine/patched default exit 0 (0 FAIL, 20 WARN); strict exit 1 (4 FAIL, 16 WARN).
- `bash take_check.sh` : rc=0. Closing blocks, verbatim from /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/take.out:

```
No static tool can see whether n8n blocks environment-variable access inside nodes (an n8n instance setting): check it on the machine that films the take; run with --block-env-access to see which steps depend on it.
IF branches accepted by a recorded decision (--accept-if): 2
SQL columns compared with the --ddl file: 14 query string(s) read.
PLACEHOLDERS IN NODE SETTINGS (3): these must be filled before import (they are not credential ids; a mail address left as a placeholder means no mail or alert can be sent):
  - demo/n8n-flows-real-v5/mf-recovery.json node AlertSend setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'fromEmail': FROM_ADDRESS_PLACEHOLDER
  - demo/n8n-flows-real-v5/mf-sub-crm-mail.json node SendMail setting 'toEmail': INTAKE_ADDRESS_PLACEHOLDER
Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql. The take needs THAT table (with the four alert columns), not the older one in demo/n8n-flows.
GATE BEFORE THE FIRST SEND (decided by the lead, order Q16): the take uses demo/n8n-flows-v4/mf_leads.sql. In psql, run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out. This script cannot see your database.
These files do NOT contain F-002 (the check that a lead key is well formed, the answer for a bad key, and the answer when the table write fails) or F-008 (saving of past runs, so the run list in n8n shows what happened). Apply both patches first if the take should show them.
Environment variables that n8n must hold for these files: DESK_ALERT_TO DESK_TIMEOUT_MS DESK_URL 
Two steps of real-v5 read environment variables (the $env form): if n8n on the filming machine blocks that, they stop working. No file check can see that setting.
To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 below does NOT mean authentication was checked.
```

  (a psql gate line is printed: 'GATE BEFORE THE FIRST SEND ... select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts'); It must list all four alert_ columns...'; SQL COLUMNS NOT CHECKED is NOT printed with --ddl: 'SQL columns compared with the --ddl file: 14 query string(s) read.' is printed instead.)

Full outputs: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/run_all2.out, /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/take.out, selftest /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/selftest.out (rc=0, ran with a kept patched folder /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/w/g/real).

## 2. Self-test, ruff, format, bandit (repo pyproject, line-length 100)

- selftest.py (real-v5, patched real, film-v5): rc=0, "SELFTEST: 629 as expected, 0 not as expected, 62 skipped (not applicable)", about 6 s.
- `ruff check --config pyproject.toml check_flows.py selftest.py`: rc=0, "All checks passed!" (ruff 0.16.9; repo pins 0.17.1).
- `ruff format --check ...`: rc=0, "2 files already formatted".
- `bandit -ll -r check_flows.py selftest.py`: rc=0; summary shows Low: 1, Medium: 0, High: 0 (the -ll filter hides Low; no medium/high issue).

## 3. 25 random single-line mutants (seed 20261118)

Base for "round 5 new code": git diff fcbb73222 (the round-4 evidence commit) -> HEAD on check_flows.py = 104 lines added, 13 removed. Pool = 104 added lines + lines mentioning ddl|placeholder|saveData|unv(|quiet = 162 lines; 22 operator rewrites (== != and or in/not in True/False not, if, comparisons, any/all, 0/1, "none") applied one at a time with random.seed(20261118), each checked to compile. Each applied in the COPY of check_flows.py, self-test run (rc != 0 = KILLED), file restored after each (final cmp identical to repo file). Script: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/mut.py. Result: 15 KILLED, 10 SURVIVED (listed first above). Table (line numbers are lines of check_flows.py):

| # | line | result | self-test rc | mutation |
|---|---|---|---|---|
| 1 | 352 | SURVIVED | 0 | `f"node {n['name']}: the query uses column(s) {miss} that the --ddl file does not define; i` -> `f"node {n['name']}: the query uses column(s) {miss} that the --ddl file does not define; n` |
| 2 | 908 | KILLED | 1 | `known=True,` -> `known=False,` |
| 3 | 890 | SURVIVED | 0 | `f"{len(phs)} id(s) are still placeholders and must be replaced in n8n before import: "` -> `f"{len(phs)} id(s) are still placeholders and must be replaced not in n8n before import: "` |
| 4 | 14 | SURVIVED | 0 | `--quiet-info                  do not print the type table and the placeholder list (the cr` -> `--quiet-info                  do print the type table and the placeholder list (the creden` |
| 5 | 815 | KILLED | 1 | `if idv and any(p in idv for p in PLACEHOLDERS):` -> `if idv and any(p not in idv for p in PLACEHOLDERS):` |
| 6 | 1631 | KILLED | 1 | `if not quiet:` -> `if not not quiet:` |
| 7 | 1111 | KILLED | 1 | `if st_.get(k) == "none"` -> `if st_.get(k) != "none"` |
| 8 | 519 | SURVIVED | 0 | `if v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "":` -> `if v in PLACEHOLDERS and v.replace(AWS_EXAMPLE, "") == "":` |
| 9 | 212 | SURVIVED | 0 | `"in",` -> `"not in",` |
| 10 | 1631 | KILLED | 1 | `if not quiet:` -> `if quiet:` |
| 11 | 61 | SURVIVED | 0 | `PARAM_PH = []  # placeholders found in node settings (not credential ids): they must be fi` -> `PARAM_PH = []  # placeholders found in node settings (credential ids): they must be filled` |
| 12 | 177 | SURVIVED | 0 | `"Not proven: that n8n accepts these files on import; what n8n really does when a step fail` -> `"Not proven: that n8n accepts these files on import; what n8n really does when a step fail` |
| 13 | 823 | KILLED | 1 | `if any(p in wv for p in PLACEHOLDERS):` -> `if not any(p in wv for p in PLACEHOLDERS):` |
| 14 | 1526 | KILLED | 1 | `if not OPTS["ddl"]:` -> `if not not OPTS["ddl"]:` |
| 15 | 1111 | KILLED | 1 | `if st_.get(k) == "none"` -> `if st_(None or {}).get(k) == "none"` |
| 16 | 815 | KILLED | 1 | `if idv and any(p in idv for p in PLACEHOLDERS):` -> `if idv or any(p in idv for p in PLACEHOLDERS):` |
| 17 | 340 | KILLED | 1 | `known = set().union(*[ddl[t] for t in tables if t in ddl]) if tables else set()` -> `known = set().union(*[ddl[t] for t in tables if t in ddl]) if not tables else set()` |
| 18 | 1660 | KILLED | 1 | `if OPTS["ddl"] is None:` -> `if OPTS["ddl"] is not None:` |
| 19 | 62 | SURVIVED | 0 | `SQL_DONE = {"checked": 0}  # queries compared with the --ddl table definition` -> `SQL_DONE = {"checked": 1}  # queries compared with the --ddl table definition` |
| 20 | 340 | KILLED | 1 | `known = set().union(*[ddl[t] for t in tables if t in ddl]) if tables else set()` -> `known = set().union(*[ddl[t] for t in tables if t not in ddl]) if tables else set()` |
| 21 | 519 | KILLED | 1 | `if v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "":` -> `if not v in PLACEHOLDERS or v.replace(AWS_EXAMPLE, "") == "":` |
| 22 | 346 | KILLED | 1 | `f"node {n['name']}: the query uses table(s) {absent} that the --ddl file does not define",` -> `f"node {n['name']}: the query uses table(s) {absent} that the --ddl file does define",` |
| 23 | 165 | KILLED | 1 | `if OPTS["ddl"] is None:` -> `if OPTS["ddl"] is not None:` |
| 24 | 1663 | SURVIVED | 0 | `"no --ddl file was given: the columns used in the SQL queries were NOT compared with any t` -> `"no --ddl file was given: the columns used not in the SQL queries were NOT compared with a` |
| 25 | 1508 | SURVIVED | 0 | `quiet = True` -> `quiet = False` |

Count check: SURVIVED=10 KILLED=15

## 4. Hostile inputs (checker run as `python3 -I check_flows.py <dir> ...`; raw output files in /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/hostile/out-*.txt)

| case | command (short) | rc | closing block / warning shown? |
|---|---|---|---|
| H1a placeholder in a node setting (extra emailSend node, fromEmail FROM_ADDRESS_PLACEHOLDER, toEmail INTAKE_ADDRESS_PLACEHOLDER) + --quiet-info | h1 --quiet-info | 1 (4 FAIL, 7 WARN; FAILs come from the incomplete file list / no --expect, not from placeholders) | YES: WARN line per flow and closing block "PLACEHOLDERS IN NODE SETTINGS (2): these must be filled before import ..." both present with --quiet-info. "SQL COLUMNS NOT CHECKED: no --ddl file was given" also present. |
| H1b same without --quiet-info | h1 | 1 | YES, same blocks (also the per-flow table line). |
| H2 --ddl file missing all alert_* columns, real-v5 pristine, --accept-if x2, --quiet-info | R --ddl ddl-noalert.sql | 0 (0 FAIL, 25 WARN) | Warning shown: yes, 3 WARN lines "the query uses column(s) [...alert_...] that the --ddl file does not define; in n8n this step would fail on every run" (AlertClaim: 4 columns; two other nodes: 4 and 2 columns), repeated under "Known open problems: 15". "SQL columns compared with the --ddl file: 14 query string(s) read." shown; SQL COLUMNS NOT CHECKED not shown. Exit stays 0. PLACEHOLDERS block (3) shown. |
| H3a webhook flow, saveDataSuccessExecution none + saveDataErrorExecution none, --quiet-info | h3a --quiet-info | 1 (1 FAIL = file list, 6 WARN) | YES: WARN "settings ['saveDataSuccessExecution', 'saveDataErrorExecution'] are 'none': n8n keeps no run list..." and the same under "Known open problems". |
| H3b webhook flow, saveDataSuccessExecution all, error none | h3b --quiet-info | 1 | WARN names only ['saveDataErrorExecution']. |
| H4 empty --ddl file | R --ddl ddl-empty.sql | 2 | "usage error: --ddl file holds no CREATE TABLE definition" (no flow output). |
| H5a non-UTF8 flow file mf-bad.json next to mf-hook.json | h5a --quiet-info | 1 | FAIL only "file list ['mf-bad.json', 'mf-hook.json'] != expected [...]"; no line about the file being unreadable; mf-hook.json warnings printed normally. |
| H5b non-UTF8 --ddl file | h5b --ddl ddl-nonutf8.sql | 3 | "INTERNAL ERROR (exit 3): the checker itself broke: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 31: invalid start byte" |
| H6 --ddl path that does not exist | h5b --ddl /nonexistent.sql | 2 | "usage error: --ddl file cannot be read" |

Hostile files built in /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5/hostile (h1, h3a, h3b, h5a, h5b dirs, ddl-noalert.sql made with sed '/alert_/d' of mf_leads.sql, ddl-empty.sql, ddl-nonutf8.sql).

## Cleanliness

Only this file was written in the repo. No planting script ran in the repo. Background jobs I started (mutation run, monitors) have all ended. Copy folders under /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/f8ev5 remain for inspection.
