# Fix report, patch-copies, round 20 (twentieth pass)

Time of the work: 2026-11-16, about 18:53 to 19:40 UTC = 00:23 to 01:10 IST on 2026-11-17. Files edited: `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md` only. Not committed.

## What failed, what is uncertain, what was not checked (read first)
- NOT run: the recipe as one piece; real `uv`, real pytest; the real tree of `b4cce5b` (the commit object exists in this checkout, its files do not, so `git apply` of the real patches and the real clause (e) could not be tried); Postgres; any scheduler; macOS; bash other than 5.2.21; `shellcheck` (not installed). All fake-stand-in tests ran as `root`.
- Clause (e) now uses `git patch-id --verbatim`. It was proven on git 2.43.0 in a scratch repository (see below) but NOT on the real patch files. The first real run may print "(e) FAILED" for a whitespace reason nobody has seen (fail safe, never a false pass). From which git version `--verbatim` exists is UNVERIFIED.
- `PGOPTIONS` in the job script (5 s limit, read-only session) is UNVERIFIED against a real server or pooler; a pooler may refuse it and then the job alarms.
- Postgres `pg_hba` notes (group/file user fields, error rows, column grants dropped by `REVOKE`) are written from the manual, UNVERIFIED.
- Exceptions (not fixed, stated with next step): (1) the missing self-hosted-price test and the RV-A1 wording both need an edit of a frozen patch file, which would change the fingerprints; next step: the lead orders a patch rebuild, then fingerprints, counts and proof numbers are rewritten. (2) cites at `b4cce5b` cannot be re-checked here (tree missing); next step: an archive copy of the commit (OPEN question already in README).
- Nothing is claimed PASSED. Wherever tools printed the word PASS (below) it is the output of the four checking tools, not a claim about the recipe.

## Item by item
| Reviewer claim | Verdict | Fix |
|---|---|---|
| T20 M1: macOS wrapper functions in `DEADMAN_LIB` | right: the program, `stat` and `sha256sum` checks run before the library loads | text now says the job is Linux only; old wrapper advice removed (fact 2, line 3) |
| T20 M2: fd 9 (the lock) inherited by children | right; seen: with a background child in a fake `send_ok` the next run exited 77 without the fix, 0 with it | `9>&-` on `psql`, `send_alert`, `send_ok`, `read_deadman_secret`, library load; short programs still inherit (fact 6) |
| T20 M3: environment is the trust root | right in part: the script cannot undo what ran before line 1 | script drops exported functions and `PG*`, `PSQL*`, `LD_PRELOAD`, `LD_AUDIT`, `OPENSSL_*`, `BASH_ENV`, `ENV`, `SSL_CERT_*`; new fact 8 says the scheduler must use a clean environment (`env -i`). Forged `sha256sum` function: exit 0 without the unset line, 74 with it |
| T20 m1 inherited errexit | right (alert rc 2 with fix; exit 1 and no alert without) | `set +e`, `set +C` |
| T20 m2 link / pipe at log path | right | pipe refused before open (73), name vs open file compared by `stat -c %d:%i` (swap: 73, control 0) |
| T20 m3/m4 stale folder, traps | right | stale `deadman-job.??????` folders removed under the lock (own, not a link); traps for QUIT, PIPE, ALRM added; ignored HUP stated |
| T20 m5, m6, m7, m8, m9, m10, m11 | right | exit 77 wording; `cp --`; DBPORT digits, line break, `/` host (73); `PGOPTIONS`; Block 3 uses `${STORED_OK:-}`; Block 1 trap-capture control (printed control-ok in bash 5.2); D:38 sentence removed; `/tmp` case and exit 74 alert corrected |
| R20b M1 exit codes before defined, "70 to 76" | right | pointer at top; range 70 to 77 plus signal exits |
| R20b M2 proof compares counts only | right | scope text of every verdict says so; `proof`/`final` check a stamp of the patched clone; `proof` checks the unpatched clone holds only the two new test files; info line counts DID NOT RAISE lines |
| R20b M3 STOP far from cleanup | right | helper block (scrub, keep_logs, cleanup, keep_delete) now sits right after the first block; STOP text, START HERE, failure paragraph updated |
| R20c M1 600-word paragraph | right | short paragraph; old text and the other pass history moved verbatim into History |
| R20c M2 scrub skips names under 3 characters | right for USER/HOST, but HOME must keep 3 (a path of `/` would wreck every line) | HOME 3+, USER/HOST 1+ as whole words; adds `$USER`, `$LOGNAME`, `hostname -f`, proxy host names, query-string token masking, WARNING on stderr |
| Smaller README items (program list, setup/run output order, line 345 `need_w`, "newest commit", three ids, date with clock) | right | fixed as listed in the History entry |
| `git patch-id --stable` | found while checking: ignores spaces inside a line | `--verbatim` |
Where reviewers were partly wrong: macOS "fix by wrapper" (impossible, see M1); "scrub everything under 3 characters" (would break for HOME).

## Raw evidence (fake data, scratch folders only)
- scrub: `path HOME/x user USER zq7zq7 zq7_t host HOST proxy PROXYHOST url https://REMOVED@c/d?token=REMOVED&x=1 key=zz`; short HOME printed WARNING; one-character user replaced whole word only.
- keep_logs / cleanup / keep_delete: cleanup refused before keep_logs; second keep_logs refused; cleanup removed W and left shell in `/`; DISCARD_LOGS and a PASSED/ADDS NO NEW FAILURE final.txt let cleanup run; trailing-slash W refused with the hint.
- gates with fake `uv`: `GATES OK (6 x 0)`; cwd unchanged by the subshells.
- verdict/proof/final with a fake repository (trailing-space test file included): `(e) ok`, final line `FINAL: VERDICT: ADDS NO NEW FAILURE ...`; after editing the patched clone: `FINAL: NOT PASSED (the patched clone changed after verdict ...)` and `proof` refused; extra file in unpatched clone: proof refused; adding one space to a patched test file: `(e) FAILED`.
- git patch-id: `--stable` equal and `--verbatim` different after double-space and trailing-space edits (git 2.43.0); `--verbatim` same id for two files in either order.
- Job script (DEAD-MAN-CHECK.md): all controls listed in its fact 8 / test list (xii to xviii) run with and without each new line.

## Final checks (raw last lines)
```
64fdf315  A-01.patch
e7ff677e  C-01-price-only.patch
ca4982eb  C-01.patch
README.md fenced 12 shell-checked 11 bad 0
DEAD-MAN-CHECK.md fenced 12 shell-checked 7 bad 0
total shell blocks 18
check_refs rc=0   PASS 5192 references
check_names rc=0  PASS 655 rows
check_secrets rc=0  PASS 0 hits in 2856 files
check_counts rc=0  PASS 52 files / 655 nodes
981 files already formatted
```
Block parser: matches fence tags and untagged fences; the 6 skipped fences are SQL, sample output, `pg_hba` line and the fingerprint list (not shell). Count 18 is not 0.

Scratch cleaned: `/dev/shm/p20t` and my own folders under the scratchpad. Patch files untouched; `../REVIEW.md` untouched.
