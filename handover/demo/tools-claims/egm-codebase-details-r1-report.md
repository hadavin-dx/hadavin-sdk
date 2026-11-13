Review of /tmp/work/d/final-series.diff against /tmp/review-tree (read-only; no files changed, no tests run). I found 4 Major and 3 Nit defects. Everything I checked besides these held.

The Majors are two cross-document contradictions (the Semgrep run record; the versions.md count that does not exist), one PR-body arithmetic error, and one overstatement in hubspot-probe.md. I could not check the 16-commit count (the diff has no commit headers) or the claim that the syntax trees equal main's (no main in the tree).

## Findings

| # | Severity | Location in tree | Exact words | What I checked | Replacement |
|---|---|---|---|---|---|
| 1 | Major | `.github/workflows/semgrep.yml:55` | "The job log is not stored in this repository; docs/tests.md repeats the same text only." | `docs/tests.md` no longer holds the run text. Grep for `43403502735` and `Ran 77 rules` finds only `semgrep.yml:55`. The series replaced the "Status of the scan" paragraph in `docs/tests.md` (line 36) with "no result of a run of this workflow is recorded in this file". | "The job log is not stored in this repository, and no other file here repeats this text." |
| 1b | Major | `docs/tests.md:30` | "No result of the CodeRabbit, SonarQube Cloud or CodeQL checks is claimed here; the one Semgrep run that was read is reported below." | `docs/tests.md:36` says no result of a run is recorded in the file. The two sentences contradict each other. | "No result of the CodeRabbit, SonarQube Cloud, CodeQL or Semgrep checks is claimed here (the Semgrep status paragraph below says why)." |
| 1c | Major | `docs/tests.md:111` | "no CI run of these tests has been seen (the only CI run reported in this file is the Semgrep one)" | The file reports no CI run at all after the series. | "no CI run of these tests has been seen" |
| 2 | Major | `docs/limits.md:68` | "The collection count for this commit is in `versions.md`; it is a count of listed tests, not a run result." | `versions.md:9` holds only "The `tests/` folder holds 92 test files." (that figure is correct: 97 `.py` files in `tests/` minus 5 non-test files). No collection count appears in any doc. | "The `tests/` folder holds 92 test files (`versions.md`); no count of collected tests is recorded in this repository." |
| 3 | Major | PR body, "What this changes" | "12 are documentation, 4 are workflow files (comments only), 14 are code files" | 12 + 4 + 14 = 30, not 31. The diff has 14 `.py` files plus `scripts/start_all.ps1`, so 15 code files. The other numbers hold: 31 files (62 header lines), +490 (476 plus 14 blank added lines) and -432 (414 plus 18 blank removed lines). | "…14 are Python files and 1 is a PowerShell script (code, 15 in all)…" |
| 4 | Major | `docs/hubspot-probe.md:3` and `:18` | ":3 'A small script that makes a few HubSpot calls and then deletes its test contact.'" and ":18 '7. Always deletes it'" | The series changed the docstring in `scripts/hubspot_probe.py` to "tries to delete it" and warns by hand-delete. The script's own code at lines 259-288 prints a WARNING when the delete fails, and the doc's own call arithmetic says the fallback delete may have no call left. | ":3 '…and then tries to delete its test contact (a WARNING names it if the delete fails).' :18 '7. Always tries to delete it: …'" |
| 5 | Nit | `README.md:31` | "**Demo servers** … small programs … that play the CRM, the mail system and the AI step and only count what they receive" | Contradicts README item 4 in the same file, which says "one demo server that plays the CRM and the mail system, and a file of pre-written answers that plays the AI step". The AI step is the in-process `RecordedQualifier` reading `replies.json`. | "**Demo servers** …: small programs in this repository (`demo_only/`) that play the CRM and the mail system and only count what they receive. The AI step is played by a file of pre-written answers." |
| 6 | Nit | `docs/settings.md:3` | "a loopback address … `localhost`, any IPv4 address starting with `127`, or `::1`" | `is_loopback_host` in `src/lead_desk/config.py:64-78` also accepts IPv4 loopback in `::ffff:` form. A later bullet in this file points back to "as defined at the top of this file" and lists that form. | Add ", or an IPv4 loopback address written in the `::ffff:` form". |
| 7 | Nit | PR body, "What a command prints" row | "for example `python -m pytest --collect-only -qq` prints one line per test file" | No doc in the final tree contains `--collect-only` or `-qq` (grep over the tree). The example is stale for a row that says "the commands named in the docs". | Drop the example, or name a command that is in a doc. |

## Verified true

- **Code comments and docstrings:**
  - `scripts/hubspot_probe.py`: `CALL_BUDGET` is 8, the delete WARNING exists, the token is replaced by `***`.
  - `scripts/reset_check.py`: prints nothing on exit 0.
  - `scripts/start_all.ps1`: same condition as `start_all.sh`.
  - `src/lead_desk/gate.py`: 10 + 27 + 18 = 55, with `CALL_DEADLINE_MAX_SECONDS` 9, `MIRROR_PASS_SECONDS` and `NUDGE_PASS_SECONDS` 2.5.
  - `src/lead_desk/desk.py`:
    - `_MirrorWait` has four lock-guarded methods.
    - The 409 `in_progress` tests are in `test_desk_edge_cases.py:365` and `test_desk_http_edge_cases.py:231`.
  - `src/lead_desk/db.py`: `test_failed_migration_rolls_back` exists.
  - `src/lead_desk/imap_count.py`: `ssl_context` is a field of `ImapSettings`.
  - `src/lead_desk/run_stats.py`: writes a `.tmp` file, then `os.replace`.
  - `src/lead_desk/trace.py`: `test_trace_write_failure_does_not_change_the_call` uses `TracedCrm`.
  - `src/lead_desk/live_claude.py`: the 429 and 5xx tests do not read the ledger.
  - `src/lead_desk/constants.py`: the `DRAIN_MAX_BYTES`, `NUDGES_PER_PASS` and `NUDGE_PASS_SECONDS` values have no test. `test_portal_api.py` covers `PORTAL_MAX_INFLIGHT` and `DUPLICATES_MAX`.
- **Test edit:** `== 1` is true, backed by `test_ai_after_claim.py:54,65`.
- **Exit codes and limits:**
  - Exit codes 1 to 5, including exit 2 for `LockUnavailableError` and exit 4 for `:memory:`, the approvers file, the lead flow file and the bind check (`server.py` main).
  - The reset scripts' exit codes 2 and 3 and the `sh` refusal.
  - The `FD_RESERVE_ITEMS` entries (16 lingerer, 24 abandoned workers) and `ADAPTER_WORKER_CAPS` 4/8/8/4.
  - A send timeout above 9 s is accepted (max 600) and capped at 9 by the desk.
  - `DESK_SMTP_TIMEOUT_SECONDS` is used only when the timeout passed is zero or less.
  - `DESK_HUBSPOT_TIMEOUT_SECONDS` default 4.5 and `DESK_HUBSPOT_MAX_429_RETRIES` default 2.
  - `LIVE_MAX_TOKENS_MAX` is 1,000,000.
- **Doc facts:**
  - The `crm_done` backfill classes and the nine `test_backfill_classes` cases.
  - The `schema.sql` trigger columns.
  - `/counts` `ok` is `null` without `expected`.
  - The restart tests (`RESTARTS` 20; the Windows skip applies only to the in-process variant) and `test_broken_extension_leaves_no_socket`.
  - Test file counts (92), lock pin counts (18 Linux, 19 Windows), `exceptions.txt` (34 lines; the allowlist is line 31), the `.gitattributes` text, and `n8n/desk-form.json` (timeout 15000, 3 tries, 1000 ms).
  - Crash points: `test_crash_resume_each_point` and `test_crash_resume_after_label_crm_send_mark_and_result` together cover all ten.
  - `portal_api.py` has a single `sqlite3.connect`, reached through `_snapshot` by five routes.
  - Every test name I grepped from the diff exists, for example `test_busy_lead_waits_longer_each_time` in `test_codeant_desk.py`.
- **PR body:**
  - The three code changes are as stated. `lint.yml` and `sonar.yml` carry identical timeout comments. The Python hunks I read are docstring or comment only apart from the one assertion.
  - The four workflow hunks are comment-only.