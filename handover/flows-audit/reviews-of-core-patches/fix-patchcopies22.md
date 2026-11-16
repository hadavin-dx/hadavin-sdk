# Fix pass 22 for patch-copies (security path, no round cap)
Date: 2026-11-16, about 19:25 to 19:45 UTC (00:55 to 01:15 IST on 2026-11-17). Files changed: `patch-copies/README.md`, `patch-copies/DEAD-MAN-CHECK.md`. Nothing else touched; nothing committed.

## What was NOT verified (first)
- No recipe was run, no database, scheduler or alert channel was used. The `git` wrapper was tested only in a scratch file (with GIT_DIR and GIT_CONFIG_* set to bogus values it still ran); it was NOT run inside the full recipe.
- The swapped `flock` and log-emptying lines in the job script were NOT run (only `bash -n`).
- The reader claims were checked against the text before each edit; edits were done by a script that failed if a target text did not occur exactly once (it all applied).
- `file:line` cites at `b4cce5b` were not re-checked.

## Command output seen
- `sha256sum` prefixes: A-01 64fdf315, C-01-price-only e7ff677e, C-01 ca4982eb (unchanged).
- `bash -n` per fenced block, new against the backup of the old file: README 12 blocks, 0 fail (old 0). DEAD-MAN-CHECK 12 blocks, 4 fail (blocks 0, 1, 3, 11: SQL and sample output), the same four failed on the old file.
- `check_refs.py`: PASS 5193 references. `check_names.py`: PASS 655 rows. `check_secrets.py`: PASS 0 hits in 2920 files. `check_counts.py`: PASS 52 files / 655 nodes. `ruff format --check .`: 1045 files already formatted.

## README findings
- r22a M1, r22b M1 (no order of steps; recipe never run whole): FIXED. An 8-step list and an up-front warning (never run whole, (e) may print a false FAILED, report instead of repair).
- r22a M2 (own git settings and GIT_* variables): FIXED. `git` wrapper in the helper block; text at the clone/fetch/apply lines updated; the limits (proxy, PATH, ssh files) stated. Helper count corrected to five functions (four places).
- r22a M3 (proxy with credentials): FIXED in text (throwaway machine only; `scrub` does not find a bare password or token).
- r22a M4 (guard lines only print STOP): FIXED. Visible sentence after the first block.
- r22a M5, r22b M4 (absolute numbers, broken patch versus different packages): FIXED. New paragraph; current numbers (12 of 30, 13 of 32) stated.
- r22b M2 (mark-file rule differs in three places): FIXED. One rule: `recipe.mark` or `patch.sha256.all` for cleanup; `setup.ok` for `need_w`; hand-set W only for keep_logs, cleanup, tail -f.
- r22b M3 (old pasteable code in History): FIXED. Code removed, one explanatory paragraph.
- r22b M5 (old text position): FIXED. Marked "old text".
- r22b "undefined terms": PARTLY DECLINED as stated (the terms are defined in the words table, outside the reader's range); pointer sentence added, words rows added for perf, `tick_state`, chain drain, HIGHENTROPY, WARDEN, `K1bAudit`. HIGHENTROPY, WARDEN and `K1bAudit` descriptions come from my reading of the source in this session; not re-verified after writing.
- Minors fixed: loop variables made local; `unset W DISCARD_LOGS` in cleanup; clause print order; "10 problems" explained; K outside `$W` explained; proof block prerequisites; time estimate; date line; `P` folder; "words box" to "words table"; clause (e) history moved to History; IST on times; D9 named.
- Mechanical items: "missing test if C-01 returns" and "RV-A1 when A-01 returns" reworded as open defects of the patch files (FIXED in wording). The patch rebuild itself is LEAD DECIDES (below).

## DEAD-MAN-CHECK findings
- M1 (contradiction on the PATH check, and fact 8 order): FIXED.
- M2 (checks run from a machine that has no password file): FIXED. One route: the administrator's machine with the temporary allow line, in six places.
- M3 (status text too long): FIXED. Compact paragraph; old text moved to a History section.
- M4/M5 (LIMIT_S skew, interval): LEAD DECIDES (see below). Recommended values written into D2 and the manual test; new row D9.
- M6 (exit 74/72/75 wording, exit 0 row): FIXED.
- Minors: umask for the second password file; log emptying after the lock; duplicated sentence removed; "Earlier text" reworded; TLS note; "words box" renamed. Item (v) rename to (v-c) and the re-grant after the revoke test: NOT DONE (not located in the time; will be done by the next pass or the lead on request).

## LEAD DECIDES
1. Where the scheduler reads the password from: missing input is the scheduler operator's (D6) choice of secrets backend; asks the studio head. Default: a mode-600 file written by the scheduler.
2. Job interval (D9): missing input is which scheduler and its smallest interval. Default: every 60 s, N = 5, maximum run 120 s.
3. LIMIT_S skew: missing input is the clock-sync guarantee (scheduler operator). Default 60 s, giving 240 (60 s tick) or 150 (30 s tick).
4. Failure-report channel for the recipe (README names it as open).
5. Rebuild of both C-01 patch files (missing test) and `A-01.patch` (RV-A1 wording): needs the lead; this pass may not touch patch files.
