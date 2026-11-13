# Q9 cross-check: demo session's numbers-names check and 13-commit claims series

Run 2026-11-13 12:36-12:45Z (18:06-18:15 IST). Read-only on all repos. Public main = /home/user/work/src @ f3c39cf89ec989f032ea48a23cfd824b88da9c68 (the lead_desk repo, not hadavin-sdk). Private trees: /home/user/work/q9-base (plain main), /home/user/work/q9-series (main + series). I ran no test, only `pytest --collect-only`.

## 1. Mismatches and unverifiable claims (first)

| # | claim (verbatim, file:line) | my check | found | matches? |
|---|---|---|---|---|
| M1 | versions.md:9 "`python -m pytest --collect-only -q` ... prints one line per test file, in the form `tests/test_workflow_run_flags.py: 10` ... 92 lines in all ... with `-q` or `-qq` the output is these per-file lines and no total" | `final-venv/bin/python -m pytest --collect-only -q -p no:cacheprovider` (pytest 9.2.0, Python 3.12.3), then `-qq` | WRONG for `-q`: it prints one node id per test (3883 lines, 3885 with the blank line and the line `3883 tests collected in 7.17s`, a total). Only `-qq` prints per-file lines (92 lines, last `tests/test_workflow_run_flags.py: 10`, sum 3883). raw/q9-collect-series.txt, raw/q9-collect-qq.txt | NO (flag wrong; the numbers 92, 10, 3883 are right) |
| M2 | tests/test_input_edge_cases.py:80 assertion tightened from `calls in (1, 2)` to `calls == 1` (commit 0002 subject says "tighten one assertion") | AST diff of every changed .py: all AST-same except this test file | One real behaviour change in a test. Whether it passes (and is not flaky with two threads) was NOT run by me (no tests allowed) | UNVERIFIED |
| M3 | commit bodies: "Text and comment changes only, except where the subject says otherwise" | AST compare base vs series of the 13 changed .py files, plus diff of workflows and .ps1 | True for 12 .py files (docstring/comment only). Exceptions are disclosed in subject 0002: start_all.ps1 now also skips the nudge default when `DESK_LEADFLOW_FILE` is empty; the test assertion above. Workflow changes are comments only (semgrep.yml diff shows only comment lines) | matches (with the two disclosed exceptions) |
| U1 | versions.md:8,10,16,17: Python 3.13.3, SQLite 3.49.1, n8n 2.46.6, Node 24.22.2; tests.md:74/76: Chromium build 1243, Node 22 (v22.23.4); docs/limits.md:16,94 "about 150 simultaneous connections"; limits.md:70; "2 s refused connect on Windows"; "17 s install"; Semgrep run 43403502735 (64 files, 79 rules, 47 files, 77 rules) | no Windows, no n8n, no network | Not checkable here. The series itself labels each as the author's own run, no log shipped | UNVERIFIABLE |
| U2 | versions.md:9, tests.md:78-82, limits.md:72: 2449/15 (Win 3.13), 2462/2 and 2462/3, 2349/116, 2460+2+3, 2513/3 in 993 s, 114/113 and 92/135 skips (22 need Node), 2329/135 | I did not run the suite. Arithmetic only: 2349+116=2465; 2460+2+3=2465; 2462+3=2465; 2513+3=2516; 2516=2465+51; 49+1+1=51; 16 min 33 s = 993 s; 114+113=227=92+135; 114-92=22; 1+2+19=22; 22+28+60+3=113; 2329+135=2464; 2449+15=2464; 2462+2=2464 | all internally consistent; run results themselves unverifiable. The `52` tests in tests/test_except_clause_hierarchy.py: checked, 52 | arithmetic OK |
| U3 | versions.md action versions (checkout v7.0.1, setup-python v7.1.0, codeql v4.39.3, cache v4.3.0, sonar-scan v8.4.0), "SHA resolves to tag" | workflow `uses:` lines carry those tag comments; SHA-to-tag resolution needs network | tags in comments match versions.md; SHA-to-tag not checked | PARTLY |
| U4 | their script's "0 MISMATCH" | read the script | The final run has 32 rows turned into OK-explained by a hand-written EXPLAINED dict and one special case for MAX_HANDLER_THREADS; "OK" for a name only means the word appears somewhere in code or tests. Numbers are compared only when a constant name is next to number plus unit, and exit codes and `(default x)` pairs. Most numbers in the prose are not checked by the script (the script's own Method line says so) | limited power, stated honestly in its Method |

No real number or name mismatch other than M1 found in the added or changed sentences.

## 2. Their check script and status block

- Files (origin/demo/handover): handover/demo/tools-claims/check_numbers_names.py, numbers-names-check-pass1.md, numbers-names-check.md (final), numbers-names-check-d2-after-v5.md; series log handover/demo/claims-fix/claims-series-log.txt. Copies: handover/demo3/tools/q9src/.
- What it claims. Pass 1 (script) on the 13-commit tree: 1046 items, OK 1006, OK-tests-only 5, CANNOT-TELL 17, MISMATCH 18 as printed; all 18+17 judged by hand as false positives (placeholders like /fake/..., /health "no page here", hidden file .gitleaks.toml, other programs' names). Pass 2: 166 number-plus-unit rows read by three builders; 7 real MISMATCHES fixed in claims-fix-v5 (and commit 0013): 55 s overrun comment (contract.md:309, limits.md:81, gate.py), body-cap "one byte more" (contract.md:155), reserve items 7 -> 9 (contract.md:137), "1 MiB or more" -> above 1 MiB (limits.md:97), Semgrep "retries three times" -> three tries in all (tests.md:34,42), n8n "repeats 3 times" -> 3 tries in all (n8n-recipe.md:77), 2516 belongs to commit 2ce1f98 (tests.md:82).
- Current version: the 13-commit series (log: last subject "Cross-check numbers and names against the code: fix four sentences, the 55 s overrun and the body-cap sentence"). The 13 patches contain those v5 fixes in the form I applied. I did not apply claims-fix-v4d/v5.patch separately.

## 3. Series application
Base f3c39cf8, `git am` of series/0001..0013: plain `git am` (no --3way) applied all 13 cleanly on q9-base (rerun after reset); `--3way` in q9-series also all 13. Resulting tree hash identical in both: 50da9cb2ddd6487da9c4f89a69ef0def07edbadd. Head 0fbb7b5. 30 files changed, 230 insertions, 215 deletions.

## 4. Their script, my run (verbatim, raw/q9-theirs-on-series.md)
`final-venv/bin/python check_numbers_names.py /home/user/work/q9-series`, rc 0, no stderr, no network (it reads files and imports lead_desk.constants/config):
`Tree: /home/user/work/q9-series. Items: 1049. OK-tests-only 5, OK-explained 32, OK 1012`
Rows 4 onward identical to their numbers-names-check-d2-after-v5.md (diff empty). 0 MISMATCH, 0 CANNOT-TELL (after the hand list, see U4).

## 5. Repo numbers, my commands
| claim | command | found | matches |
|---|---|---|---|
| main collects 3883 tests | `pytest --collect-only -q` in q9-base | `3883 tests collected` | yes |
| series tree also 3883 (adds no test) | same in q9-series | 3883 | yes |
| 92 test files | `ls tests/test_*.py \| wc -l` and `git ls-files` | 92 / 92 | yes |
| per-file lines sum | `-qq`, awk | 92 lines, sum 3883 | yes |
| last full runs 3683+200 (3.12), 3684+199 (3.13) | not run (not allowed). 3683+200=3883, 3684+199=3883 | consistent with 3883 | arithmetic only |
| 4 of 200 skips remain with Playwright+gitleaks | not run; tests.md:78 "four in tests/test_hygiene.py" skip points | 4 skip call sites in test_hygiene.py (lines 150, 344, 533, 580) plus others in test_gitleaks_*; not a skip count | partly |

## 6. Every changed sentence with a number, version, port, file or function name: true on the patched tree?
Method: wrote the added lines (187 lines with digits or backticks, raw/q9-added-lines.txt) and checked every backticked token in .md additions (428 tokens, tools/q9_names.py): paths, test names, ALL-CAPS names, identifiers. Not found: ALLOW_ANY_BASE_URL (contract.md:76; suffix after prefix DESK_LIVE_, explained) and MISSING_SCOPES (HubSpot error word). All else exists.
| sentence | check | result |
|---|---|---|
| limits.md:81, contract.md:309, gate.py:32 "10 + 27 + 18 = 55 s" | REAPER_PASS_SECONDS 10.0; CALL_DEADLINE_MAX_SECONDS 9.0 (3 x 9 = 27, 2 x 9 = 18); MIRROR/NUDGE_PASS_SECONDS 2.5 | true |
| contract.md:137 FD_RESERVE_ITEMS (8 portal connections x 2 files, 16 lingering, 24 workers) | constants.py: PORTAL_MAX_INFLIGHT 8, LINGER_MAX_SOCKETS 16, ADAPTER_WORKERS_TOTAL 4+8+8+4=24, 9 items; items sum 66, FD_RESERVE 96 | true (limits.md:120 "the 96" true) |
| limits.md:121 exit codes 1-5, "AI call budget of 9 s", BIND_RETRY_SECONDS | EXIT_* 1,2,3,4,5; CALL_DEADLINE_MAX 9.0; BIND_RETRY_SECONDS 5.0 | true |
| limits.md:126 256 connections, EVICT_MIN_IDLE_SECONDS 2 s, 0.1 s byte test | MAX_CONNECTIONS 256; 2.0; tests/test_stall_eviction.py sleeps 0.1 | true |
| contract.md:155 DRAIN_MAX_BYTES, 1 s | DRAIN_MAX_BYTES 1048576, DRAIN_TOTAL_SECONDS 1.0 | true |
| contract.md:148 ACCEPT_PAUSE_SECONDS 0.05 s | 0.05 | true |
| limits.md:138 waits 10, 60, 180, 420 s; five tries; about 11 minutes | MIRROR_RETRY_WAIT_SECONDS (10,60,180,420), MIRROR_MAX_TRIES 5; sum 670 s = 11.2 min | true |
| limits.md:14,80 put back five times ends `failed` | SEND_MAX_ATTEMPTS 5 | true |
| limits.md:97 "longer than 7 digits or above 1 MiB" (fake HubSpot) | `len(text) <= len(str(MAX_BODY_BYTES))` = 7; MAX_BODY_BYTES 1_048_576 | true |
| settings.md:51 rota 1 to 20 | LEADFLOW_ROTA_MAX 20 | true |
| settings.md:70/76 SMTP defaults (127.0.0.1?, desk@example.test, example.test, 5.0; example.invalid) | smtp_outbox.py DEFAULT_FROM/DEFAULT_MESSAGE_ID_DOMAIN, smtp_provider.py "example.invalid"; host and 5.0 accepted by their EXPLAINED list, not re-read by me | true for the three I read |
| constants.py:226,269 PORTAL_MAX_INFLIGHT 8, DUPLICATES_MAX 50; load_tools/catcher.py:21 backlog 1024 | constants 8, 50; BACKLOG = 1024 | true |
| n8n-recipe.md: 3 tries 1 s apart; three nodes; workflow names; files; path desk-form; proof-run; | n8n/*.json maxTries 3, waitBetweenTries 1000; desk-form 3 nodes; names match; paths desk-form, desk-webhook, proof-run | true |
| why-this-code.md:24 scrub tool "about 200 lines" | tools/scrub_n8n_export.py 205 lines | true |
| real-services.md:9 "about 12 invented people" | DEFAULT_PERSONS = 12 | true |
| tests.md:42 Semgrep "up to three times in all, 20 seconds apart" | semgrep.yml: `for attempt in 1 2 3`, RETRY_PAUSE_SECONDS "20" | true |
| tests.md:80 skip lines (110, 175, 27, 113, 488, 171, 204, 257) | each line holds importorskip or the node skip/decorator | true |
| tests.md:54, versions.md:57 Playwright 1.63.0; greenlet, pyee, typing-extensions | both browser locks: greenlet 3.5.6, playwright 1.63.0, pyee 13.0.1, typing-extensions 4.16.0 (same as dev lock) | true |
| versions.md:57 uv 0.11.32 in requirements-coverage.in | present | true |
| versions.md semgrep 1.185.0, gitleaks 8.30.1, anthropic-version 2026-10-21 | requirements-semgrep.txt, lint.yml, constants.py | true |
| README.md:21, 88 "2 requests received, 1 new, 1 duplicate"; "exactly one email"; /counts | README comments agree among themselves; code path not re-run | consistent, not run |
| tests.md:49 / versions: Dependabot GitHub Actions only; .codeant lists both browser locks; .gitleaks.toml path regex | dependabot.yml ecosystem github-actions only; .codeant/configuration.json lines 18-19; .gitleaks.toml line 97 | true |
| codeql.yml:3 languages python, actions, javascript-typescript; timeout 60/20/60/30 minutes | workflow matrix; timeout-minutes lines | true |
| tests.md:79 "the same file lists 52" | collect-only on that file | true |

Progress log: raw/progress-Q9.txt.
