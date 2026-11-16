# EVIDENCE RUNNER results: Q8b round 2, head bcb2bfec179f18bd58de0df2b6669d94a9312472 (parent be53718c, merge base 2a8c2aac = origin/main)
Raw output only; this file does not judge. Run 2026-11-11 (UTC), clean detached worktree `/home/user/build/EV-Q8b-bcb2bfec/wt` (git status: 0 changed files before and after every run, also after the mutant runs), own venv, own Postgres 16.15 (port 56913, started and stopped by me), cloud variables unset. Raw logs: `/home/user/build/evidence-raw/Q8b-bcb2bfec/`. Probe scripts here are copies with made-up values replaced by `<made-up-value-...>` (so gitleaks passes); the runnable originals are in `/home/user/build/EV-Q8b-bcb2bfec/scripts/`.

## Not run, or run differently from the brief (first)
- `uv sync --locked --no-build ...` as written in the brief FAILED here (`hadavin-sdk` editable "marked as --no-build but has no binary distribution"); I ran `uv sync --locked --all-extras --group test` instead (rc 0). Same lock file.
- NOT RUN: semgrep, zizmor (CI steps with network tools), the Python 3.12 job, Postgres 17, the Vault service tests, the perf run and the flaky `test_the_timing_harness_flags_a_quadratic_stand_in` x3 (the round-2 brief did not name a perf item).
- Fail-before (item 7): the test files as they are do NOT run on main src: 4 test files fail at collection (`tests/q8b_helpers.py` reads `R._ONLY_PLACEHOLDERS`, missing on main). To get per-test counts I ran a second variant with ONE helper line changed (pattern built from `runmap.PLACEHOLDER`); both outputs are kept (06a, 06b/06c). The fail-before run did not go through `heavy.sh` (about 215 tests, 30 s; my first queued attempt waited more than 25 min for a slot and I cancelled my own job).
- Heavy slots: the full suite got a slot within about 1 minute; the Q8b mutant run waited about 35 minutes in the queue before running (not counted).
- My probe generator for the "assignment readable" count is my own, not the round-1 one, so I cannot reproduce the round-1 number 87 (46 e-mail-glued + 33 Bearer + 8 other); I give my own head and main numbers below.
- The ticket says no edit of `guard/redact.py` (PR77 owns it); the diff list (item 1) contains `src/hadavin_sdk/guard/redact.py`. Recorded as a fact.

## Table (failures and oddities first)
| # | Item | Command | Exit | Result | File |
|---|---|---|---|---|---|
| 7 | fail-before, files as they are, over main src | pytest of the 6 test files, `--continue-on-collection-errors` | 1 | 69 passed, 4 collection errors (`AttributeError: module ... k1b.redaction has no attribute '_ONLY_PLACEHOLDERS'`) | 06a |
| 7 | fail-before, one helper line changed | same files | 1 | 133 failed, 109 passed, 14 xfailed. Failed per file: card_text 37, credential_keys 68, glued_and_whole_values 22, random 6. Passed on old code (list in 06c): 25 test_k5_producers, 44 test_k5_round11, 3 card_text, 32 credential_keys, 4 glued_and_whole_values, 1 random | 06b, 06c |
| 7 | same 6 files on the head | pytest | 0 | 241 passed, 16 xfailed | 06d |
| 1 | head, merge base, file list | git | 0 | head bcb2bfec, clean tree; 18 files changed (ci.yml, CHANGELOG, app.py, approvals/{channel,gate,requests,slack_channel}.py, guard/{producers,redact}.py, k1b/redaction.py, 8 test files) | 01-head.txt |
| 2 | ruff check / ruff format --check (src tests demos tools) | uv run | 0 / 0 | All checks passed / 324 files already formatted | 04-lint.txt |
| 3 | bandit `-q -r src demos tools -ll` | uv run --with bandit | 0 | no issues (2 harness warnings about a `nosec` in tools.py) | 04b |
| 4 | `tools/scan_repo.py`; gitleaks `origin/main..HEAD` | | 0 / 0 | no output; 2 commits scanned, no leaks | 04c |
| 4 | `python tests/stage_mutants.py` | | 0 | 37 of 37 good; problems: [] | 05b |
| 5 | full pytest `-p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | | 0 | 10696 passed, 1 skipped, 28 deselected, 16 xfailed in 386.18 s | 02-full-pytest-tail.txt |
| 6 | `python tests/q8b_mutants.py` (the CI step) via heavy.sh | | 0 | 46 of 46 good; problems: [] (the round-1 head had 26) | 05-q8b-mutants.txt |

## Round-1 findings re-run on the head (my own inputs; "readable" = the made-up value is still in the output)
Head output is compared with clean main 2a8c2aac run through the same scripts (`*-main.txt`). Import paths printed in each file.

**E1 e-mail or host directly followed by a credential key** (08-e1-head.txt, 08-e1-main.txt): grid of 8 left parts x 10 separators (glued, 5 invisible characters, space, newline, comma, semicolon) x 8 key forms = 640 texts, on three paths (record walk, card `clean`, Slack block).
- Named cases, head: `bob.smith@example.com` + `password=<value>` glued and `token=` glued: walk `<EMAIL_1>=<SECRET_1>`, card `<EMAIL_1>=<SECRET_1>`. With U+200B between: walk `<EMAIL_1>​password=<SECRET_1>`, card `<EMAIL_1>=<SECRET_1>`. Value readable: 0 of these. Main (walk path): glued `<EMAIL_1>=<value readable>`.
- Whole grid, readable: head walk 0, card 8, Slack 8; main walk 15, card 8, Slack 8. The 8 on both: left part `https://example.com/x` followed by `password: ` (also after any separator except space/newline): output `[link removed] <value>` (the key is swallowed by the link text, value readable). Unchanged from main.
- Property run (own generator, seed 20261111, 3000 texts, 17 left-part kinds, 14 keys, 9 separators; 08-prop-*.txt): value readable in the assignment: head walk 38 (all start with `Authorization: Bearer ` followed by the key, which the Bearer rule takes as the token), head card 38 (same kind); main walk 432 (e-mail 84, upper-case e-mail 101, e-mail + dot 106, percent-encoded e-mail 94, zero-width + e-mail 9, Bearer 38), main card 38. Exceptions 0 on both. Card path idempotent (clean twice): 0 differing on head and on main. (My walk-path idempotence figure, 1622 of 3000 on head and on main, compares a second pass that escapes placeholders; not a useful number, kept raw.)

**E2 card path value with spaces** (08-cases-head.txt `[E2 ...]`): `password=correct horse battery staple` on the card: head clean `password=<SECRET_1>`, Slack block `password=<SECRET_1>`, nothing readable; same for `password: `, `password%3D...%20...`, quoted, `db_password`, `PASSWD`, `pwd`, with a prefix, with a trailing dot, `Password = `; main leaves `horse battery staple` readable on all of them. Record-walk path (`{"message": "password=correct horse battery staple"}`): head `password=<SECRET_1> horse battery staple` (readable, same as main). Key `passphrase=correct horse battery staple` on the card and walk path: nothing masked on head and on main (all four words readable). Idempotent: yes for all card rows.

**E3 Secret cases** (walk path, Secret record plus a log record that repeats the value; `<A>` = made-up value):
- `kind: secret` lower case, `SECRET` upper case, `kind: Secret` with `data` under `spec`, `spec.spec`, `stringData`, `data` a base64 string, `data` a list: under the key and in the log copy masked (value and its base64 not readable); main leaves all of these readable.
- `kind: " Secret "` (with spaces): the entry is masked under its key, the log copy stays readable.
- `data` not a map and not valid base64 (`"!!not base64*<A>"`), and an entry that is not valid base64 (`"***<A>"`): masked under the key, the log copy stays readable (same on main). `data` None, an int, an entry that is a number: the value only appears in the log, stays readable (not registered anywhere).
- Kind spelled `ſecret`, `ſECRET`: masked. Kind spelled with İ, ı, Kelvin sign, no-break space, zero-width space, full-width S: not recognised as Secret (value readable under the other key and in the log).

**Code fence mention** `10.20.30.40@channel`: closed backtick fence, closed `~~~` fence: closed backtick fence head `<IPV4_1>@channel` (the word stays as written); closed `~~~` fence `<IPV4_1>at-channel`; inline code `<IPV4_1>at-channel`; plain text `<IPV4_1>at-channel`; unclosed fence `<IPV4_1>at-channel`. All 6 idempotent on head; 5 of the 6 not idempotent on main (clean twice differs).

**Appendix row M5** (`[{"kind":"Secret","data":{"DB_NAME":"<base64 of orders>"}}, {"message":"orders-api timeout"}]`): head output leaves `orders-api timeout` readable (the entry `orders` has 6 characters, under the 8-character rule); same on main. Other lengths: 7 and 8 lower-case letters, 8 digits: log copy readable on head and main; 8-character mixed case/digits and upper case: masked on head, readable on main.

**E4 keys** (walk path): masked as `<SECRET_1>` on head: env entry and map `PWD` (`/srv/app`), `OLDPWD`, `auth_method` (`oauth2`), `authorization_type`, `session_id`, `password_policy` (value `strict`). Kept as written: `author`, `authority`, `secretary`, `keyboard_layout`, `monkey`, `hostname`, `pwd_enabled: "true"`, `password_policy_enabled: "yes"`, `token_expiry` timestamp, `secret_count: 5`.

**F3 case folding** (key written in the record and in a card line): `paſſword`, `ſecret`, `ſecret_key`, `ApİKey`, `apıkey`, Kelvin-sign `TOKEN`, full-width `password`, `Authorİzation`: masked. `paßword` (ß folds to ss, so it reads as `password`): record walk masked on head (readable on main); card path value readable on head and on main. Not word equivalents (kra `toĸen`, `sİcret`, `passwıord`): value readable.

**256 caps** (08-f3cap-*.txt, 08-cap2-*.txt): Secret with N entries and the same N values repeated in log records: copies readable head N=255: 0, N=256: 0, N=257: 1, N=300: 44, N=1000: 744 (entries after the first 256 get the fixed mask under their key; repeated copies stay readable); main: all N readable. Three Secrets of 200 entries: 0 of 600 readable on head (cap is per Secret). A late entry equal to a registered value: masked. List of 300 values under a credential key: 0 readable in log on head (300 on main). Map of 300 values under key `credentials`: 300 readable in log on head and on main. Values of 254 to 1000 characters under a key or in a Secret: repeat not readable at every length on head and main. 255-character value with spaces: masked whole on head (`<SECRET_1>`), main leaves words.

**Card target with display label** (`summary(plan, None, labels)`; main has no `target_labels`): host target without label `<HOSTNAME_1>`; with label `orders-db`: ` on orders-db.`; host-shaped label `<HOSTNAME_1>`; e-mail label `<EMAIL_1>`; label with an assignment: value masked; markdown link label `x [link removed]`; label with `@channel`: `orders at-channel`; label for another system: ignored (`<HOSTNAME_1>`); IP label `<IPV4_1>`; 500-character label `<HIGHENTROPY_1>`; label with a zero-width character `orders-db`. A label `a\n# forged` is written as `a` then a line `# forged` (the heading line stays).

## Not checked
Round-1 appendix scripts and the 113-shape hostile list were not re-run (the round-2 brief named the cases above); Slack text was checked through `_blocks` with a stub request, not a real Slack call; no live model call.
