# Raw evidence, pull request 89, head c2f98f49 (round 22)

EVIDENCE RUNNER record: what was run and what came out. No verdict. Run as root on Linux. Times UTC (IST = UTC + 5:30). Start 17:09 UTC (22:39 IST), finished about 17:27 UTC (22:57 IST): about 18 minutes of real clock.
Raw logs (not in git) are in `/home/user/build/evidence-raw/PR89-c2f98f49/`; copies of the small ones are in this folder. The big JUnit file `full.xml` is NOT copied: it holds made-up secret-shaped strings from other tests (gitleaks flagged 4 hits in it: aws-access-token, slack-app-token x2, curl-auth-user). Keep `full.xml` out of any push.

## Not run, slips, odd results (read first)
1. **My slip:** I killed my own first full-suite queue entry (wrong process id, ~17:11) and restarted it. The full suite and the mutant list reported below are the restarted runs. Nothing else was affected (`slip.txt`).
2. **Leak probe, 2 of 498 cases SHOWN (new against 7a2eb4cc, which had 0 of 498):** password = a made-up value equal to the name of a built-in error class (`TimeoutError`) and the child test raising that class: `first_lines` is `TimeoutError [expect found] value must be one` (plain form found; both cases `exc_class_dynamic_plain` and `exc_class_literal`). On 7a2eb4cc the same case gave `[REDACTED] [expect found] ...`. All other 496 cases, all other forms and channels: NOT SHOWN. The old "halves" case (`PATH_PART--class_literal`) is gone. Tables: `leak-table.md`; raw `leak.out`.
3. **Address probes behave differently from 7a2eb4cc in two accepted cases:** key `HOST=localhost` (upper-case key): ACCEPTED then, REFUSED now; scheme `POSTGRESQL://`: ACCEPTED then, REFUSED now. 26 accepted / 110 refused now (28 / 108 then). The refusal message wording changed for most refused rows (compare `address-table.md` with the 7a2eb4c one). URL port `99999999999` is still accepted. Refused-and-a-child-ran: 0. Secret text in any output: 0 of 136.
4. **Fail-before:** two of the builder's new tests PASS on the old src (`test_a_failed_baseline_with_an_unusable_result_file_says_only_how_the_run_ended`, `test_a_link_to_a_private_folder_is_no_runtime_folder_for_the_lock`), as the builder said. 
5. **bandit:** the repo venv has no `bandit`; I ran it with `uv run --with bandit`. 
6. Not run: Windows, macOS; the perf-marked tests; `tests/stage_mutants.py` (not in the brief). Lock probes ran as root (uid 0) and as the postgres user (uid 102) on Linux only. The full suite ran while my address, lock and leak probes ran on the same machine, and other sessions' heavy jobs were running too.
7. Side effect of my own lock probe: it created `/tmp/hadavin_mutation_locks_102` (17:13); I removed it. `/tmp/hadavin_mutation_locks_0` (16:11, not mine) and two `/tmp/mutants_*` / `mutant_ini_*` entries that were there before the mutant run were left alone (two entries exist in /tmp now; I did not make them: the mutant run ended with 0 left by itself at 17:25, the two present now are from other sessions or earlier).

## Results
| # | item | command (all under `env -u AWS_ACCESS_KEY_ID ... -u VAULT_SECRET_ID`) | exit | output |
|---|---|---|---|---|
| 1 | head | `git rev-parse HEAD` in worktree `/home/user/build/EV-PR89-r22` | 0 | c2f98f490f1f585ba4f5b50bb71b4fef32b3327b (clean tree) |
| 1 | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 1 | ruff format | `ruff format --check` | 0 | 323 files already formatted |
| 1 | bandit | `bandit -ll -r src demos tools` | 0 | Medium 0, High 0 (Low 18) |
| 1 | scan_repo | `python tools/scan_repo.py` | 0 | no findings printed |
| 1 | gitleaks | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 2 | full suite | `heavy.sh ... pytest -q -m "not live and not perf" --junitxml -rfEs` | 0 | 10777 passed, 1 skipped, 28 deselected in 411 s (skip: bedrock stub case) |
| 3 | mutant list | `heavy.sh ... python tests/mutation_runner_mutants.py` | 0 | 261 of 261 good; problems: []; 0 BAD/weak rows; 17:18:38 to 17:25:55 |
| 4 | fail-before | worktree of 7a2eb4cc, head's `test_mutation_runner_keywords.py`, `test_mutation_runner_meta.py`, `mutation_runner_mutants.py` overlaid (manifest NOT overlaid; src/tools of 7a2eb4cc), `pytest tests/test_mutation_runner.py tests/test_mutation_runner_keywords.py tests/test_mutation_runner_meta.py` | 1 | 42 failed, 276 passed in 102 s; list `fb-failed-list.txt`. hadavin_sdk resolved to the old worktree (checked) |
| 5a | address probes | `addr.py` (136 cases, instrument of the 7a2eb4c evidence) | 0 | 26 accepted, 110 refused, 0 harness errors, 0 secret in output, 0 refused-but-child-ran |
| 5b | lock probes | `lock.py` (as root and as postgres) | 0 | `lock-table.md`; `lock.out` |
| 5c | leak probes | `leak.py` (498 calls, 3 min) | 0 | 2 SHOWN (item 2 above), 0 worker failures; forms planted in raw JUnit in 476 of 498 |
| 6 | mypy | `mypy tools/mutation_runner.py` | 1 | 1 error (untyped import). With `--platform win32`: 13 errors (the same import, 4 `getuid`, `O_DIRECTORY`, `O_NOFOLLOW`, `P_PID`, `WEXITED`, `WNOHANG`, `WNOWAIT`, `killpg`, `SIGKILL`) |
| 7 | suppressions | `git diff origin/main...HEAD | grep -nE '^\+.*(noqa|nosec|type: ignore|pragma: no cover|mark\.skip|xfail)'` | | 20 lines (`suppressions.txt`); 4 of them added since 7a2eb4cc |
| 7 | wall clock | | | about 18 min |

Lock probe highlights (full rows in `lock-table.md`): symlink, dangling link, regular file, fifo, folder with mode 0777/0750/0701, folder owned by another user, planted-link folders, lock file that is a link, hard link, fifo, folder, mode 0666/0640, owned by another user, and a lock held by another process: REFUSED with a message, no child ran. Folder mode 0700/0500/1700 own, lock file 0600/0400 own, TMPDIR read-only, XDG folder missing/relative/empty/world-writable: RAN. Run as postgres with read-only root-owned TMPDIR: RAN, it created `/tmp/hadavin_mutation_locks_102` (the fallback folder).

## Files with made-up secret-shaped text (keep out of the push unless the lead decides otherwise)
Files in the PR diff holding a URL with a made-up password or `password=` text (no key-shaped strings such as AKIA..., ghp_..., sk-...): `CHANGELOG.md` (1 url, 2 `password=`), `tests/mutation_runner_mutants.py` (1 `password=`), `tests/test_mutation_runner_keywords.py` (6 urls, 4 `password=`), `tools/mutation_runner.py` (2 urls, 3 `password=`). gitleaks on `origin/main..HEAD` found none. In this evidence folder: `full.xml` (removed here, kept in the raw folder).

## Files in this folder
`ruff-*.log bandit.log scan_repo.log gitleaks-git.log mypy-*.log suppressions.txt full.log full.times mutants.log mutants.times fb.log fb.xml fb.time fb-failed-list.txt addr.out lock.out leak.out address-table.md leak-table.md lock-table.md slip.txt uv-sync.log instruments/` (the probe scripts and run scripts, copied from the 7a2eb4c evidence with paths changed).
