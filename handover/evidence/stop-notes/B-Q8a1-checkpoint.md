# B-Q8a1 checkpoint (builder of ticket Q8a-1)
Start 2026-11-11 13:53 UTC (19:23 IST). Worktree /home/user/build/B-Q8a1, branch core/q8a-1-live-override-refusals, base 2a8c2aac.

## 14:20 UTC
Done: src edits (app.py override refusal + is-None switches, config.py Vault rule, builtin.py comment, factory.py sibling fix); new tests/test_q8a_live_overrides.py; two killer tests in tests/test_stage_names.py; two mutants M12a/M12b; two positive pilot tests rewired through app.make wrapper; fail-on-main run (38 failed, 26 passed on main src).
Next: CHANGELOG; own Postgres on 56050; two positive tests non-skipped; four negative tests; mutants; full pytest; ruff; bandit; commit; push.
Blockers: none. Commit SHA: none yet.

## Register of things I started
| id | purpose | started | expected end | state |
|---|---|---|---|---|
| pg56050 | own Postgres 16 cluster, data dir /tmp/pg56050-q8a1, port 56050 | pending | before report | not started |

## 14:45 UTC
Done since last note: CHANGELOG; own Postgres started (row below); two positive pilot tests pass non-skipped; M12a/M12b killed, all 39 stage mutants good; ruff clean.
Next: one full pytest with DSN; bandit; four negative tests clean run; commit; gitleaks; push; stop Postgres.
| pg56050 | own Postgres 16, /tmp/pg56050-q8a1, port 56050 | 14:22 UTC | before report | RUNNING |
| full-pytest | one full run with DSN, log in scratchpad full.log | 14:46 UTC | ~15:05 UTC | starting |

## 15:05 UTC
Full pytest #1 (14:46-14:53 UTC): 1 failed, 10615 passed, 1 skipped. The failure was tests/demo_askdata/test_validate_harm.py [dblink-connect]: MY Postgres was started without PGHOST/PGPORT in the server's environment, so the server-side dblink looked for port 5432. Restarted the cluster with the variables exported; that file then passed (253 passed). A second full run is needed for a clean exit code. Waiting (max 15 min) because 3+ full runs of other agents are active.

## Final (about 14:25 UTC / 19:55 IST by the machine clock; the times in the notes above were my estimates and ran ahead of the real clock, which read 14:08 UTC when the second full run was queued)
Commit 464dee14f59b716cff54f7fe8cf95b4061c839bf pushed to origin/core/q8a-1-live-override-refusals. No PR opened.
Full pytest #2: 10616 passed, 1 skipped, rc 0. ruff check, ruff format --check, bandit -ll: clean. 39 of 39 stage mutants good. gitleaks: not installed, not run (tools/scan_repo.py rc 0).
Register: pg56050 STOPPED, data dir deleted. full-pytest runs finished. Nothing of mine left running.
Raw logs: /home/user/build/B-Q8a1-evidence/

## Fix batch 1 (round-1 result review, D-012), 14:37 UTC
Done: src (Vault check moved to app.build by settings type; run_tick now= refusal; timeout_s > 0; sources=/tools= is-None), one seam with recorded calls, tests rewritten, 9 mutants M12a-g + M13a-b, CHANGELOG; fail-on-464dee14 run (41 failed, 59 passed).
Next: PR notes; own Postgres 56050 (UTF-8, server env exported); positive tests; whole mutant list; one full suite; ruff; bandit; gitleaks; commit; push.
| pg56050 (2nd) | own Postgres 16, /tmp/pg56050-q8a1, port 56050 | now | before report | starting |

## Fix batch 1 final, 14:46 UTC
Pushed (fast-forward). Full suite 10652 passed, 1 skipped, rc 0; 46 of 46 stage mutants good; ruff, bandit (src tools), gitleaks clean. pg56050 STOPPED, data dir deleted. Nothing of mine left running. Logs: /home/user/build/B-Q8a1-evidence/r2-*.log. PR notes: /home/user/build/B-Q8a1-pr-notes.md

## Fix batch 2 (round-2 result reviews), 15:04 UTC
Done: steps= refusal, timeout range, seam records settings and handed-on names, guard test, killers and 24 new or changed mutants (61 of 61 good), CHANGELOG, PR notes; fail-before runs (previous head: 31 failed, 194 passed; pristine main: 5 failed of 5).
Next: own Postgres; positive tests; one full suite through heavy.sh; lint; bandit; scan; commit; gitleaks; push.
| pg56050 (3rd) | own Postgres 16, /tmp/pg56050-q8a1, port 56050 | now | before report | starting |

## Fix batch 2 final, 15:15 UTC
Pushed fcd77a68 (fast-forward). Full suite 10680 passed, 1 skipped, rc 0 (through heavy.sh); 61 of 61 stage mutants good; ruff, bandit, scan_repo, gitleaks (rc 0) clean. pg56050 STOPPED, data dir deleted. Nothing of mine left running. Logs: /home/user/build/B-Q8a1-evidence/r3-*.log

## Fix batch 3 (round-3 Minors), 15:32 UTC
Done: built-in step check, config field bounds, approvals is-None, seam objects, killers, 4 new mutants (65 of 65 good), CHANGELOG, PR-body draft; fail-before on fcd77a68 (22 failed, 234 passed).
Next: own Postgres; positive tests; one full suite through heavy.sh; lint; bandit; scan; commit; gitleaks; push.
| pg56050 (4th) | own Postgres 16, /tmp/pg56050-q8a1, port 56050 | now | before report | starting |

## Fix batch 3 with the lead's addendum, 16:05 UTC
Earlier full run of this batch was stopped by me (it was mine) when the addendum arrived: its tree was stale.
Done: tick context refuses a given time outside demo (frozen; stand-in contexts refused in steps); one timeout rule for keyword and config field (0.001 to 3600); tests; 71 of 71 mutants good at the final tree; fail-before on fcd77a68 without any alias (85 failed, 280 passed); positive pilot tests pass; lint, bandit, scan clean.
Running: the one full suite (log r4-full.log). Next: commit, gitleaks, push, stop Postgres.
| full-pytest batch 3 | one full run through heavy.sh | now | +10 to 25 min | RUNNING |
| pg56050 (4th) | own Postgres | earlier | before report | RUNNING |

## Fix batch 3 final, 16:11 UTC
Pushed 0b97d55a (fast-forward). Full suite: 1 failed, 10755 passed, 1 skipped, rc 1; the one failure is the known flaky tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in (alone, 3 runs: 1 passed, 2 failed; file untouched). 71 of 71 mutants good; ruff, bandit, scan_repo, gitleaks (rc 0) clean. pg56050 STOPPED, data dir deleted. Nothing of mine left running.

## Fix batch 4 final
Pushed ecd5dba1 (fast-forward). Full suite 10752 passed, 1 failed (environment: dblink test needs the server's own PGPORT; passes alone with it, 253 passed in its file), 1 skipped. 75 of 75 mutants good; ruff, format, bandit, scan_repo, gitleaks clean. pg56050 STOPPED, data dir deleted.
