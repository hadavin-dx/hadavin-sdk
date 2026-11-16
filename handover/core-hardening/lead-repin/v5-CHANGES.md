# v5 changes (script `lead-repin-verify.sh` and guide `LEAD-REPIN-VERIFY.md`)

Written Mon 16 Nov 2026 by a builder. v4 is kept as `lead-repin-verify.v4.sh` and `LEAD-REPIN-VERIFY.v4.md`. Fixes are by class, not by instance. "Finding" names the review file: SEC = `review-repin4-security.md`, NAIVE = `review-repin4-naive.md`, CIT = `review-repin4-citations.md`, IND = the independent run `evidence-repin4-independent/00-TABLE.md`, COORD = the coordinator's extra findings.

| Class (what was wrong) | Fix | Closes |
|---|---|---|
| Secret names were a list; names such as `secretValue`, `tokenString`, `passwordHash`, `cookie`, `session`, `signature`, `hmac`, `dsn`, `webhook`, `salt`, `otp`, `cert` showed their value | One general name rule: a strong word anywhere in the name, or a weak whole word (also with value, string, data, text, hash, bytes, material after it) | SEC majors, NAIVE |
| Prefixes and labels were put inside sed expressions (file names with `# & \` could change a rule) | Every prefix and label is built outside sed expressions; a self-test case runs a file called `a#b&c.json` in a folder `d#x&y\z` | SEC nits |
| YAML block scalars: only some header forms and continuation lines were hidden | All header forms (`\|`, `>`, indent and chomp marks, anchors, tags, comments) and their continuation lines; a line-start YAML name hides the whole rest of the line | SEC, IND |
| Canary lines covered few characters | One canary line per character class (`@`, `/`, `;`, comma, spaces, upper case, digits), checked by a 6-character head and a tail | SEC, IND |
| A container longer than the line limit was printed | Fail closed: it is hidden whole (150-line test) | SEC |
| Signals: QUIT was not handled; child programs could stay running | QUIT trapped (exit 131); the whole pipeline is stopped with `kill_tree`; the folder is removed on every signal | SEC |
| Hand-typed commands could be redirected by `PATH`, trace or git settings | Script sets its own `PATH` without `.`, `set +x`, `LC_ALL=C`, `grep -a`, `git --no-optional-locks -c core.fsmonitor=false`; `git status` is skipped under git 2.36 | SEC |
| Six leaks of `--mask` | mysql `-pVALUE`, `sshpass -p`, triple-quote body with 20 hex characters, XML attribute pair, netrc, `Passw0rd list` line: all hidden; each is a canary line | COORD 1 |
| Mutant m05 (URL rule) survived: no canary depended on it alone | Two canaries where only the `user:password@` rule can hide the value (one with `@` inside the password) | COORD 2 |
| Mutants m09, m13, m26, m27, m28 | m09 and m13 killed by new canaries (line-start YAML, key block with body on the same line); m09a (the quoted-string rule) killed by a kept-text check; m26 killed by the cleanup checks; m27 by the `LC_ALL` check; m28 by a left-out-files report check. See `evidence-repin5/04-mutants.txt` | COORD 2 |
| m19: the exit code did not follow the tally | Two independent judges (`st_verdict`, `st_recount`) plus the return value of `self_test`; each judge is tried alone on forged results | COORD 3 |
| Stray sed and awk after a signal in `--mask` | The masking pipeline is stopped with `kill_tree`; checked with a python launcher (`evidence-repin5/05`) | COORD 4 |
| Non-root: `sha256sum` printed Permission denied text, and the checksum block did not count the unreadable file | The text is not shown; block R00 counts the unreadable file and the run-check names it | COORD 5 |
| m3 was read as an equivalent mutant | Wrong: it is caught. The guide says so; the late-failure hook `LEAD_REPIN_TEST_LATE_FAIL` proves it | COORD 6 |
| Checksum lines were kept by shape | An allow-list (`SHAOK`) keeps only the exact checksum lines the script made | SEC |
| Guide: wrong sources, jargon, no quick start, no stop table | Rewritten: 3-step quick start, plain stop table with who decides, terms explained before use, release note v8 and owner sheet v24-A with re-checked G and R numbers (R2 and R3 do not exist in v24-A), ORDERS lines 185 to 194, owner-sheet "NOT SHOWN" at line 62, mutation count stated (7 mutants under 2 shells = 14 runs in v4), timing re-measured | NAIVE, CIT |

New tests: 388 of the v5 checks fail against the v4 filter (`evidence-repin5/01`). The v5 self-test has 1022 checks and passes under dash and bash.

Not fixed, and why: a bare `passwd NAME` or `-p VALUE` line with no command stays visible (a user name; ambiguous flag). The guide lists both. Not tested: busybox, macOS, WSL, Windows, the real test program.
