# Fix report, patch-copies, pass 19 (inputs: patch-copies-reader-r19.md = R19, patch-copies-reader-r19b.md = T19)

Editor: the only editor of `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. The three `.patch` files, their fingerprint list and `REVIEW.md` were not touched. Nothing committed. No secret and no personal handle printed.

## What failed, what is uncertain, what was not checked (first)
- Static project. Nothing ran against a real repository, `uv`, pytest, Postgres, a scheduler or an alert channel. `shellcheck` is not installed.
- UNVERIFIED (Postgres behaviour I cannot run, from the manual only): the new `pg_hba_file_rules` query of check 1a (`'deadman_reader' = ANY(user_name)`, how `all` is shown), the claim that the view shows the file on disk and not the loaded rules, the reload with `SELECT pg_reload_conf();`, the exact refusal text of check 1c (`pg_hba.conf rejects connection`), and the new filter of check 3 g (`datallowconn`).
- Cites "at `b4cce5b`" (T19 note) were NOT re-checked: this folder holds no git data of that commit, so it is physically impossible now (exception 2a). Next step: the studio head names where an archive copy of the commit is kept (open question already in the README).
- The repeated-alert question (R19 minor "no alert de-duplication") is not built: it depends on the alert channel and the scheduler, which are unanswered (D4, D6, D7; exception 2b/2c). It is now written down as fact 7 with the exact open point.
- The scheduler's maximum run time and no-overlap rule cannot be set in the script (the scheduler is unknown); the text now REQUIRES them and the script adds its own lock (exit 77).
- Tests ran as `root` in a scratch folder (outside the repo), with fake `psql`, `send_ok`, `send_alert`, `read_deadman_secret`; "file of another user" used `chown nobody`. A test copy of `timeout` with shorter times was used for the "psql ignores the terminate signal" case (real line is `-k 5 60`).
- My own slips, found by the tests: (1) first fake `timeout` wrapper shifted the wrong number of arguments (harness error, fixed); (2) my "missing flock" first try cleared PATH so `env` could not find `bash` (harness error, redone with a PATH holding links to every program except `flock`); (3) in a test of the new `setup` fragment, `return 1` inside a sourced file inside a function did not end the function, so the "reached end" line printed; that is an artefact of my harness (in the real `setup` the `|| return 1` is inline), the STOP message and the failure itself were shown.

## Items
Reviewer claims were checked against the text first; every Major and every minor below was right unless marked.

| Item | Verdict | Done | How checked |
|---|---|---|---|
| R19 M1 (reject lines can sit after a catch-all line; 1a passes anyway) | right | DMC: the three lines must be next to each other and before every line that could match the login; 1a now selects the rows for `deadman_reader` or `all` and expects the FIRST THREE to be allow, reject, reject with consecutive line numbers and no `trust`; new check 1c (other database refused, expected failure output quoted); reload step named; temporary allow line described for running checks from the administrator's machine | read back; 1a/1c/reload UNVERIFIED (Postgres). Negative: expected failure output of 1c is quoted in the text; a catch-all first row makes 1a fail by its stated expectation |
| R19 M2 and T19 M3 (3 g "the one database"; template0; query b errors where the table is absent) | right | 3 g filters `datallowconn`, expects this note's database plus `postgres` and `template1`, names `pg_hba.conf` as the control; a, c, c2, d, e, f run in each listed database, b only in this note's database (expected error text stated) | read back; UNVERIFIED (Postgres) |
| R19 M3 (manual test, 1b and 4 from the administrator machine while `pg_hba.conf` allows only the scheduler; a pg_hba refusal read as "password required") | right | text says to run them on the scheduler machine (or with the temporary allow line); a message holding `pg_hba.conf` is named a SETUP failure in the manual test, 1b and the ORDER line | read back |
| R19 M4 (STOP message names functions defined only at the end; each Cleanup block defined AND ran) | right | README: ONE definitions block (`scrub`, `keep_logs`, `cleanup`, `keep_delete`; runs nothing) and three separate one-line call blocks; the STOP message, START HERE (5) and the failure-report paragraph say to paste the definitions first | definitions sourced in a scratch shell: printed nothing, removed nothing; then `keep_logs` (2 files, scrubbed copy: home path replaced), `cleanup` (folder removed), `keep_delete` (copy removed), each alone |
| R19 M5 ("ends the run after 60 seconds" overclaims; no overlap lock) | right | reworded: only `psql` is bounded (60/65 s); the scheduler MUST set a maximum run time (proposal 120 s) and refuse overlapping starts; the script holds `flock -n` on the open error log, a second run ends with exit 77 (new row in the exit table, new fact 6) | test: lock held by another process, job exit 77, no output; healthy runs unaffected |
| T19 M1 (`DEADMAN_LIB` check fails open, not bound to the sourced file) | right | absolute path required; `DEADMAN_LIB_SHA256` required; the file is copied into the private folder, the COPY is hashed and the copy is sourced; `find` removed; the program check (including `sha256sum`, `cp`) runs before the library | tests: wrong hash, no hash, relative path, link: each exit 73; correct hash: runs |
| T19 M2 (error log check-then-use, follows swapped links) | right | folder must be the job's own and closed to group/others; the file is opened once (fd 9), checked on the open file (`[ -f /proc/self/fd/9 ]`, owner and link count 1 via `stat -L`), mode 600 set through the open file, all writes go to fd 9; the lock is the same file | tests: link, folder, file of another user (`chown nobody`), two hard links, folder mode 777: each exit 73; mode 666 file became 600 |
| T19 M4 (no negative tests for pass-18 controls) | right | items (vi) to (xi) added to the negative test with expected exit codes (LIMIT_S 29/901/12345 = 73; two-line secret = 72; log link/folder/other user/hard link/open folder = 73; LIB cases = 73; psql ignoring TERM = alert `psql exit 137`, job exit 0; psql too long = 124; second run = 77) | each case run with fakes (see Evidence); NOT run on a real store |
| R19 minor `proof && final` skips final.txt | right | `proof; final`; text says no `final.txt` means NOT PASSED | `final` run with a failed proof (prints `FINAL: NOT PASSED`, rc 1), a good proof (prints the verdict), no proof (NOT PASSED) |
| R19 minor README 295 vs 333/336 scope suffix | right | text says only `FINAL: VERDICT:` lines carry the scope; `FINAL: NOT PASSED` lines carry none | read back |
| R19 minor PROOF OK lacks "counts only" | right | echo now `PROOF OK (counts only; read proof.log against the list of failures)`; `final` still matches `^PROOF OK` | `final` test above |
| R19 minor scope text states skipped tests as fact | right | scope and PASSED line say "probably skipped (skip reasons not read)" | read back |
| R19 minor sentinel `OK|||n` beside problem lines | right | renamed `WATCHED|||<n>` in the query, job, tables, alert text, tests; comment about "last line" corrected (it is sorted in, not last); note that the fingerprint of the query file changes | job tests: healthy output `WATCHED|||4` accepted; two lines refused |
| R19 minor DMC 220/311 vs 315 (which checks need the password file) | right | 1b, 1c, 4 need it; 3 runs as administrator; S7 text and ORDER agree | read back |
| R19 minor README 292 vs 280/313 | right | "never run verdict after proof; start again" | read back |
| R19 minor DMC 363 rule 4 vs exit table | right | rule 4 names the job exits that send no alert (1, 70, 71, 73, 75, 76, 77) as caught only by the missing signal | read back |
| R19 minor LIMIT_S bound missing in D2 and README row 8 | right | added in both | read back |
| R19 minor / T19 minor failed `send_alert` on exit 72; `unset PW` | right | `|| echo ... >&2` on both exit-72 paths; `unset PW` after the settings check; exit 72 row says "tried" | tests: secret with line break, empty secret: exit 72 with alert text |
| R19 minor README 0b "since the eighteenth pass" | right | "`awk` is not used" | read back |
| R19 minor history entries both "this one" | right | 17th and 18th entries no longer say it; the new one does | read back |
| R19 minor `git clone` prompt | right | `GIT_TERMINAL_PROMPT=0` on clone and both fetches | clone run in a scratch repo with the prefix: ok |
| R19 minor 1b PGPASSFILE | right | `PGPASSFILE="${DM_DIR:?}/pgpass"` | read back |
| R19 minor no alert de-duplication | right | NOT built; fact 7 says why and who must answer (exception 2b/2c) | n/a |
| R19 minor G5 list lacks the commit | right | stated at the start of the list | read back |
| R19 minor "ceiling / token limit / C-01 extras" | right | one sentence: three names for one thing | read back |
| T19 minor traps before `mktemp -d` | right | traps set first with `D=''`; trap removes only when `D` is set | HUP test: exit 129, no folder left in `/dev/shm` (count 0) |
| T19 minor `DEADMAN_TMP` absolute | right | exit 73 if relative | test: `rel` gives 73; `/tmp` gives 70 |
| T19 minor no timeouts around send_*/secret | right | text: only `psql` bounded; scheduler maximum run time required (see M5) | read back |
| T19 minor README scrub scheme case-sensitive; user/host rewrites test names | right | scheme `[A-Za-z]...`; user and machine name replaced only as whole words (underscore counts as part of a word) | scrub run: `test_root_case` and `rootroot` unchanged, `root`, `root,root`, `HTTPS://a:b@c@host/p` and a mixed-case scheme replaced; `https://example.invalid/path@notuser` untouched |
| T19 minor E PATH guard misses `/tmp` | right | refuses `/tmp`, `/var/tmp`, `/dev/shm`, `TMPDIR`, `$W` and below; other writable folders are NOT checked (stated) | `E` extracted from the README: `/usr/bin:/tmp` refused, clean PATH runs; pattern test on `/tmpfoo/bin` (ok), `/w/tmp.abc/bin` (refused), TMPDIR case (refused) |
| T19 minor README 375 stale `extra.env` comment | right | comment fixed | read back |
| T19 minor README 173 `cd` leaves shell in clone | right | apply steps run in a subshell | scratch repo with two tiny patches: both applied, staged, calling shell's directory unchanged |
| T19 minor DMC 111/154 omit find and chmod | right | list now names `id`, `chmod`, `flock`, `stat`; `find` is no longer used | read back |
| T19 minor `statement_timeout=0` can occupy both connections | right | stated in the S8 row | read back |
| T19 note b4cce5b cites NOT CHECKABLE; README 37 vs 87 | cites: cannot check (2a). README 37 was ambiguous | line 37 now says "identical among themselves, not between them and `b4cce5b` (75 files changed)" | read back |
| T19 "verified OK" list | no defect | no change | n/a |

## Evidence (commands and results, scratch folder `t19/` in the scratchpad, outside the repo)
Job script exactly as in the file (compared with `cmp`: "job block equals tested job.sh"), run with `env -i` and fakes:
healthy: rc 0, `OK: limit_s=180 names=4`; unhealthy (`bad`): rc 0, alert "psql exit 0, 2 output line(s)"; failing psql: rc 0, alert "psql exit 2", error log holds `FATAL: password authentication failed`; ignoring TERM: rc 0, alert "psql exit 137", log line `rc=137`; LIMIT_S 29, 901, 12345: rc 73; secret with line break: rc 72 with alert; empty secret: rc 72; error log as link: 73 (target not created); as folder: 73; other user's file: 73; two hard links: 73; folder mode 777: 73; relative path: 73; mode 666 file: became 600; lock held elsewhere: rc 77; no `flock`: rc 71; query hash wrong: rc 74 with alert; LIB wrong hash / no hash / relative / link: rc 73; DEADMAN_TMP `/tmp`: rc 70, `rel`: rc 73; hang-up during a slow fake psql: rc 129; `/dev/shm` holds 0 `deadman.*` folders afterwards.

Required checks, from `/home/user/hadavin-sdk/handover/flows-audit` (last run after the final edit):
- `python3 -I tools/check_refs.py`: rc 0, PASS 5182 references
- `python3 -I tools/check_names.py`: rc 0, PASS 655 rows
- `python3 -I tools/check_secrets.py`: rc 0, PASS 0 hits in 2818 files
- `python3 -I tools/check_counts.py`: rc 0, PASS 52 files / 655 nodes
- `ruff format --check .`: rc 0, 944 files already formatted
- `bash -n` on every fenced block of both files (fences read line by line): README 12 of 12 ok; DEAD-MAN-CHECK 12 blocks, the 4 that fail are SQL or sample output (the query, the sample output, the catalog-finding queries, the check 3 queries), as before.
- `sha256sum` of the three patch files: A-01 `64fdf315...`, C-01-price-only `e7ff677e...`, C-01 `ca4982eb...`; `sha256sum -c` against the list: all OK.

Not run: EGM review of this result (the lead runs it); the recipe as one piece. Backups of the originals: scratchpad `bak19/`. No process left running.
