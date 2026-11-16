# fix-patchcopies28 (twenty-sixth fixer pass on patch-copies/README.md and DEAD-MAN-CHECK.md; answers patch-copies-reader-r27.md)
Security path, no round cap. Static work; made-up data; nothing applied to a real repository; no secret written; no pytest, no psql; hashes shortened. Report time: about 20:45 UTC = 02:15 IST on 2026-11-17 by the clock of the machine. EGM: the lead runs the review of this result; the fixer did not review itself. Backups: scratchpad PCREADME.before28 and DMC.before28. No .patch file, REVIEW.md or other file touched.

## Per item (all fixed)
- M1 FIXED: first command of `setup` requires `git`, `scrub`, `keep_logs`, `cleanup`, `keep_delete` to be functions, else STOP, return 1.
- M2 FIXED: `setup` STOPs (return 1) when home holds `.ssh`, `.aws`, `.config/gcloud` or `.config/gh` (also as a link). No override variable (fail closed).
- m1 FIXED: STOP on `*://*@*`, `git@*`, `ssh://*`, `*@*:*`; the value is not printed.
- m2 FIXED: `scrub` prints a WARNING and skips a proxy host that starts with `[`.
- m3 FIXED: `cleanup` accepts an EMPTY `$W` (ls -A must succeed and print nothing); a non-empty folder without the marks is still refused.
- m4 FIXED: "lint steps" is "lint parts".
- m5 FIXED: rule 9 quoted in full ("Never merge; the lead merges.") in the words table and in the merge row.
- m6 FIXED: one explanation and one list of which report belongs to which pass (22=fix22, 23=fix25, 24=fix26, 25=fix27, 26=fix28), says reader and fixer files do not share a counter; checked against `ls` of the folder.
- m7 FIXED: passes 23 and 24 carry the report-file time in UTC and IST (20:09Z = 01:39 IST; 20:21Z = 01:51 IST). Found while doing this: the text of the pass-24 report says about 20:35Z, the file time says 20:21Z; written as UNVERIFIED which is right. The pass 25 text (started 20:25Z, its report says 20:40Z, file time 20:32Z) was not changed.
- m8 FIXED: D2 "Who" = "the lead sets the values (default in last column), the studio head confirms"; README row 8 says the studio head names the persons and answers D8, the lead sets D2 and D9. No new "LEAD DECIDES: owner, due" line was added (no owner/due values exist in the folder for D2).

## Evidence (commands and output, scratch shell; scratch folder is the session scratchpad)
- `bash -n` on all 12 fenced blocks extracted from the new README: no output (OK). Functions extracted to scratch files: `bash -n` OK.
- M1, no helpers: `STOP: the helper block was not pasted (the function git is missing) ...` rc=1; only git defined: same STOP naming `scrub`, rc=1.
- M2 with a `.ssh` folder in a scratch HOME: `STOP: your home folder holds ~/.ssh (keys or logins; ...)` rc=1; same with `.config/gh`. (`.aws`, `.config/gcloud` use the same loop; not run each.)
- m1: SRC with `user:pw@`, `git@host:o/r`, `ssh://`, `me@host:path` each: `STOP: SRC holds a user name or password ...` rc=1; plain https address passes this guard (stops later at the patch copy because the scratch folder has no patch files).
- m2: `HTTPS_PROXY=http://[::1]:3128` gives `WARNING: scrub skipped a proxy host written as an IPv6 address ...`; a normal host is still replaced (`via PROXYHOST ok`).
- m3: empty W + `DISCARD_LOGS=yes cleanup`: `removed <scratch>/tmp.XXXX`, rc=0; W with a foreign file: `STOP: ... holds neither recipe.mark nor patch.sha256.all and is not empty ... nothing was removed`, rc=1.
- From handover/flows-audit, last lines: patch sha256 prefixes `64fdf315 e7ff677e ca4982eb` (unchanged); check_refs `PASS 5190 references`; check_names `PASS 655 rows`; check_secrets `PASS 0 hits in 3027 files`; check_counts `PASS 52 files / 655 nodes`; `ruff format --check .` `1152 files already formatted`.

## NOT checked
The recipe as one piece, a real clone, real uv or pytest, macOS, bash versions other than the local one. `.aws` and `.config/gcloud` guards were not run separately. I did not run an old-code comparison for m2 (the old line `v=${v%%:*}` visibly cut `[::1]:3128` to `[`).
