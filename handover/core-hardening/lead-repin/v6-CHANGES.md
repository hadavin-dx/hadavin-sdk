# v6 changes (lead re-pin script and guide), 16 Nov 2026

Builder note. Script: `lead-repin-verify.sh` (v6). Guide: `LEAD-REPIN-VERIFY.md` (v6). The v5 files are kept as `lead-repin-verify.v5.sh` and `LEAD-REPIN-VERIFY.v5.md`. The EGM result review is the lead's step; this builder did not run it.

## Failures and gaps first
- Found by me during the build and fixed (not deferred): (1) my first rewrite of the multi-line rule hid the closing bracket of a JSON list, so the second step hid every later line (35 kept-text checks failed); fixed in the rule, not in the test. (2) My stray-program check counted a finished but uncollected program (state Z) as running; in this machine's init that made TERM and HUP look broken. Fixed by testing the program state. (3) The word-piece rule hid the made-up name `com.example.MyClass2.HandlerFactory`; fixed.
- Real bug in v5, confirmed and fixed: when a run was stopped by a signal while a program was busy in the foreground (a slow `git`), that program kept running. v6 stops every program below the script. This is the cause of the stray `sleep 29` the independent v5 run saw once (security review m1). I reproduced the mechanism with a fake slow `git` (v5 behaviour reproduced as "programs left"); I did not reproduce the exact one-in-five-repeats case from the independent run.
- Still showing in v6 (stated in the guide, not hidden): a short secret under 24 characters with an unknown name and no known shape; a bare `passwd NAME` or `-p VALUE` line with no command in front; a digit-only password after a command not on the list; a secret that starts with `/`, `.` or `~` cut by slashes into pieces under 24 characters; a look-alike letter inside a plain sentence (`the pa<Cyrillic s>sword is hunter99`). The password-flag rule is a list plus a shape rule; the guide says so.
- Not run: busybox, macOS, WSL, Windows; the real test program.

## Finding -> fix -> where (by class)
| # | Class (what was wrong) | Fix | Where in the script | Test that fails on v5 |
|---|---|---|---|---|
| 1 | Passwords in web addresses: an empty user part (`://:PW@host`) and the other userinfo forms | one rule family for every form (`:PW@`, `//PW@`, tokens in userinfo, `@` after the host part) | mask rules, userinfo block; tests v6 `url*` | 13 of 13 baseline values show in v5 (`baseline-v5-result.txt`); probe 55 lines: 15 of 55 show in v5, 0 in v6 |
| 2 | Password given as a flag after any command | `PWCMDS` list (66 command names) plus a shape rule for lines that look like a command; the guide says it is a list | `PWCMDS`, `:pwl` rules | `docker login -p`, `redis-cli -a`, `ldapsearch -w`, `zip -P`, `7z -pPW`, `htpasswd -b`, `smbclient -U user%PW`; and kept: `docker run -p 8080`, `mkdir -p 755`, `ls -a`, `grep -a -n` |
| 3 | Value over several lines (open bracket or trailing backslash after a secret name) | awk pre-step (step 0): hides following lines until the brackets close, a `--` line or the input end; covers a secret name anywhere before `=` or `:` on a line that opens a bracket | `ml_scan`, `ml_start`, `pre_line` | six "wrapped assignment" cases, block-value cases |
| 4 | The guide told the reader to write output to a fixed `/tmp` name, and said "writes only into one private folder" | the guide now says: read the masked copy in the work folder; or `umask 077` and a private folder; the script never needed the fixed name | guide section "Where it writes" | read-through; no `/tmp/lead-repin-out` string left in the guide (grep below) |
| 5 | The self-test could kill other jobs' programs | recorded process ids only; no `pkill`/name matching | meta checks | meta cases |
| 6 | The start check did not compare the planned number of cases | `CANARY_PLANNED=1167`, `SELFTEST_PLANNED=1191`; both judges refuse a different number | `st_verdict`, `st_recount`, `run_canary` | new case: a good result with a wrong planned number is refused by both judges |
| 7 | No length guard or time bound on the filter; pre-main phase delayed signals | line cut at 20000 characters before the filter reads it; time limit 1200 s (`LEAD_REPIN_MAX_SECONDS`); pre-main `find` and `grep` run through `bg_wait`; every program below the script is stopped on a signal | `pre_line`, `start_watchdog`, `bg_wait`, `on_signal`, `kill_tree ... kids` | new cases: TERM while the file lists are made (fake slow `find`), the time limit (2 s), TERM and HUP with a fake slow `git` |
| 8 | Zero-width and other non-ASCII bytes inside a name hid nothing | a name with a byte outside plain ASCII before `=` or `:` is treated as a secret name; value hidden | `nonascii_names` | zero-width space, accented letter, no-break space cases |
| 9 | Blob splitting at slashes and dots | dotted tokens judged piece by piece (CamelCase pieces kept); a mixed-case piece of 24 or more characters with slashes is hidden (v5: 32). **Residual gap stated in the guide**: a path-like secret cut into pieces under 24 characters can show | `blob`, `dotted_secret`, `piece_nodot` | dotted cases |

## Guide changes (naive review B1 to B6, M1 to M8, minors)
Who is who and a who-decides column; full `"$S"` and `"$T"` in every command; one rule for `MATCH WORD HIDDEN` (stop for that search) and a definition of "stop for that search"; STOP lines and the work-folder path are both on the screen, the path is in the first two lines, and the guide gives `ls -d` to find it again; every placeholder step is now one pasteable line or says "cannot be done with this guide: needs X from Y; write not done"; a "What you hand in" section with the block-finding commands; the glossary is above the quick start; "head", "test", "stage", "take", "output file" each have one meaning (final commit, self-test, filter step, test program, masked copy); no builder guess is written as an order: three blanks for the lead; a version warning (release notes up to v11 and owner sheets up to v27-A exist); the exact last line of the self-test; one delete-word list (`clean.?up`); the mutation text moved to an appendix; both hidden-count claims are quoted from the script's own wording.

## Citation fixes (cites-table rows)
- Row 11: the 1 MB timing statement is now measured for v6 (`timing-1mb.txt`) and no longer quotes v4's "about 0.5 s" as a figure.
- Row 25: delete words are `clean.?up` (as in `DELETE_RE`), in the guide list and in the hand command.
- Row 40: the lease sentence is on line 123 of release note v8 (line 33 only says the sentence must be decided).
- Row 60: the gates are G1 to G42.
- Cannot-find rows stated plainly in the guide: the BL-wp6-G1 row; the exact wording "End-date refusal: shown"; lines 1045-1056 and 500-512 of the real code; `review-codebase-1.md`.

## Counts
Filled in from the files in `evidence-repin6/` (see `checkpoint-repin6.md` and `evidence-repin6/00-RESULTS.md`).
