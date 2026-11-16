# EVIDENCE RUNNER results: Q8b, head be53718ccbf5e2038cc18c87d334577e7b11ace8 (parent and merge base 2a8c2aac)
Raw output only; this file does not judge. Run 2026-11-11 (UTC) by the evidence runner in a clean detached worktree `/home/user/build/EV-Q8b-be53718` (git status: 0 changed files before and after every run), venv `/home/user/build/venv-evq8b`, own Postgres 16.15 (port 56871, started and stopped by me). All test commands run with the cloud variables unset (`env -u AWS_... -u VAULT_SECRET_ID`).

## Not run, or run differently from the brief
- Postgres 17: NOT RUN (only 16.15 exists on this machine).
- Heavy slots: `heavy.sh` had no free slot for more than 15 minutes (other agents held all three). A first queued perf job was cancelled by me (kill of my own pid 10108). Full suite attempt 1, and runs 2 and 4 and the perf runs, ran directly, not through `heavy.sh`. Nothing else of mine ran at the same time as a perf run; other agents' jobs did run (load average about 4.3 to 4.7).
- Full suite attempts 1 and 2 died silently mid-run (no pytest summary, exit 1, at about 10 % and 14 %; the same test passes alone). Cause not found (no kernel or memory evidence); runs 3 and 4 completed.
- Run 3 had one failure caused by MY Postgres setup (a test calls `dblink_connect` to the server's default socket, which my server did not serve); after restarting my server with `PGPORT`/`PGHOST` in its environment the file passed 253/253 and run 4 of the whole suite passed. Both logs kept.
- Mutants and fail-before ran in the same worktree layout, one after the other, never during a gate.

| # | Command | Exit | Result | File |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD`, merge base | 0 | head be53718c..., one commit, parent 2a8c2aac = origin/main | 01-head.txt |
| 2 | `pytest -q -m "not live and not perf" -rs` (run 4, direct venv python) | 0 | 10670 passed, 1 skipped, 28 deselected, 16 xfailed in 366.98 s | 02-full-pytest.log |
| 2 | same, run 3 (-v) | 1 | 1 failed (`demo_askdata/test_validate_harm.py::...[dblink-connect]`, my Postgres env, see above), 10669 passed, 1 skipped, 16 xfailed | 02-full-pytest-run3-1-failed-dblink-env.log |
| 2 | rerun of `tests/demo_askdata/test_validate_harm.py` after the Postgres env fix | 0 | 253 passed | 02c-rerun-validate-harm.txt |
| 2 | runs 1 and 2 | 1 | died silently, no summary | 02a-..., 02b-... |
| 3 | `pytest -q -m perf -rs` (direct, alone) | 1 | 1 failed, 27 passed: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` ("a quadratic function must be flagged") | 03-perf.log (= 03a) |
| 3 | perf rerun 1 / rerun 2 | 0 / 1 | 28 passed / same 1 failure | 03b-perf-reruns-and-flaky-test-alone.txt |
| 3 | that test alone x3 on head | 1,1,1 | failed 3 of 3 | 03b |
| 3 | that test alone x3 on clean main 2a8c2aac (PYTHONPATH main src, path printed) | 0,1,1 | passed 1 of 3 (so it is load-flaky on main too; the branch changes neither the test file nor the timing helper: 0 diff lines) | 03b |
| 4 | `ruff check` | 0 | All checks passed | 04-lint-scan.txt |
| 4 | `ruff format --check` | 0 | 326 files already formatted | 04-lint-scan.txt |
| 4 | `bandit -ll -r src tools` (via `uv run --with bandit`; bandit is not in the venv) and CI form `-q -r src demos tools -ll` | 0, 0 | Medium 0 / High 0 issues | 04b-bandit.txt |
| 4 | `tools/scan_repo.py` | 0 | no output | 04-lint-scan.txt |
| 4 | `gitleaks detect --log-opts=2a8c2aac..be53718c` | 0 | 1 commit scanned, no leaks | 04-lint-scan.txt |
| 5 | `python tests/q8b_mutants.py` | 0 | 26 of 26 good; problems: [] | 05-mutants.txt |
| 5 | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: []; worktree clean afterwards | 05-mutants.txt |
| 6 | the branch's 3 new + 2 changed test files over clean main src (import path printed: `/home/user/build/EV-Q8b-main/src`; src diff vs 2a8c2aac 0 lines) | 1 | 112 failed, 104 passed, 14 xfailed (37 card_text, 68 credential_keys, 7 random) | 06-fail-before.txt, 06b-fail-before-main-full-raw.txt (06c = an earlier attempt cut off) |
| 6 | the same files on head src | 0 | 215 passed, 16 xfailed | 06d-same-tests-on-head-raw.txt |
| 7 | 10 appendix scripts + 2 fixture shapes rerun on head | 0 | see below | 07/, 07-appendix-diffs.txt |
| 8 | hostile inputs, 113 made-up shapes + 3000-text property run (seed 20261111), on head and on clean main | 0 | see below | 08-hostile.txt, 08b-hostile-on-main.txt, 08c-probe-email-glued-key.txt |

## 7. Appendix scripts on be53718c versus the builder's saved outputs (46fdcfb2)
Identical (0 differing lines): keycheck, r2_f5, r2_f6, r2_xf, r3_f5 (except one timing figure), r3_card (except two timing figures), r3_slack, r3_stubs, both fixture shapes (JSON files equal the author's prototype files byte for byte; stdout equal). Differences: timing figures (r3_big, r3_card, r3_f5) and the 12-character plan hash in r2_m7 (also differs between the builder's saved file and the author's file, so it is not stable between runs). r3_card: P2 4000 texts leak 0, bare domain 0, not idempotent 0; N9 3000 texts with a readable first-pass original 0. Versus the author's prototype outputs: r2_f5 differs in two rows where the head masks less than the prototype (`M5 Secret DB_NAME b64 + log`: head leaves `orders-api timeout` readable, prototype wrote `<SECRET_2>-api timeout`; `F5b Secret b64 + decoded in log`: placeholder numbers 3 vs 1). r2_m7/r3_xf/keycheck: see 07-appendix-diffs.txt.

## 8. Hostile inputs (raw numbers)
Head: 113 shapes (walk path = `redact_bundle`'s `_walk`; card path = `channel.clean` and the Slack block `_blocks`), 10 shapes with a made-up secret substring still readable, 13 not idempotent, 0 exceptions. Clean main: 36 readable, 29 not idempotent, 0 exceptions.
Shapes where a made-up secret substring is still readable on HEAD (input class: what stays readable):
- `password=correct horse battery staple` on the CARD path (also `password: ...` and `password%3Dcorrect%20horse...`): output `password=<SECRET_1> horse battery staple` (clean and Slack block alike). Same on main.
- Secret with `data`/`stringData` not a map, or a list, or invalid base64, or `kind: secret` lower case: the Secret itself is masked (fixed mask or placeholder; lower-case kind NOT masked at all: base64 value readable), but the same phrase written in a LOG line stays readable (the copy is not registered). 
- `bob.smith@example.com Zx9 tail` under key `token`: value masked as `<SECRET_1>`, the log copy shows `<EMAIL_1> Zx9 tail`.
- ``10.20.30.40@channel`` inside a closed code fence: `<IPV4_1>@channel` (the word `@channel` stays as written; builder's notes say a fence body is not changed).
Cases the brief asked for, head output: passwords with spaces/multi-word/quotes/percent/backslash-u/ESC/zero-width/300 characters under key: masked, nothing readable; keys `PWD`, `OLDPWD` (env entries, value `/srv/app`) and `auth_method` (value `oauth2`): masked as `<SECRET_1>` although they hold no secret (the cost the builder's notes name; rows 17, 18, 21 of 08-hostile.txt); `Secret` data not a map: masked whole; lists under setting keys: masked; `10.20.30.40@channel` in inline code: `<IPV4_1>at-channel`; host target: `<HOSTNAME_1>`; e-mail: `<EMAIL_1>` (bracketed, wide-dot, percent and entity spellings too); zero-width character before `#` or `>`: `<EMAIL_1>` and the heading kept; forged `<SECRET_1>` look-alikes: kept as written, the real secret next to them masked, readable 0.
NEW FINDING (regression versus main), file 08c: an e-mail address directly followed, or separated only by a zero-width character, by a credential key swallows the key name and leaves the value readable. Input `bob.smith@example.com` + `password=<made-up-value>` (glued): head output `<EMAIL_1>=<made-up-value>` (value readable); main output `bob.smith@example[.]compassword=<SECRET_1>` (value masked; the e-mail itself was readable on main). Same for `token=`. With a space, newline, comma or semicolon between, head masks the value. In the property run this shows as 46 of 87 "assignment readable" texts on head versus 3 of 38 on main.
Property run (3000 random texts, one made-up secret each, plus a plain-text repeat in about half): readable in the assignment (or both) head 87 (46 e-mail-glued as above, 33 where the text starts `Authorization: Bearer ` followed by the key, which takes the key as the bearer value: same 33 on main, 8 other); readable only as the plain repeat copy head 118 versus main 120; not idempotent (clean twice differs) head 3 versus main 11; exceptions 0. The 8 "other" and the 3 non-idempotent texts are printed in 08-hostile.txt. Idempotence on the 113 fixed shapes: 13 not idempotent on head (walk path mostly, `walk` run twice with a fresh map; list in 08-hostile.txt `FLAG` lines), 29 on main.
