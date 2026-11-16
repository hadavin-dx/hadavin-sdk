# Fix pass 12 for patch-copies README.md and DEAD-MAN-CHECK.md (security path, uncapped)
Fixer session (Sonnet 5.5), 2026-11-16. Edited only `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. Nothing committed. Reviewer words were treated as unverified: every cite was re-read in the file text before use.

## Failures and uncertainty first
1. NOTHING of the new recipe, job script or query was RUN. The only commands were `bash -n` (syntax), `sha256sum`, `git diff --stat`, the three checkers and `ruff format --check`. `bash -n` finds syntax errors only; it says nothing about logic. The new functions `final`, `cleanup`, `gd`, the `setup.ok` test, `EXTRA_ENV` and the `${EXTRA_ENV[@]+...}` expansion have never run.
2. The new query (WITH/UNION ALL, `OK` sentinel row, `CLOCK AHEAD` test, `ORDER BY 1`) was read against `0003_approvals_tick.sql:30-35` and the Postgres rules from memory; it was NOT run on any Postgres. Where the `OK|||n` line sorts among problem lines depends on the database's sorting rules (the file says so and shows no order).
3. I made one slip while editing and caught it: the first build replaced the wrong lines of `DEAD-MAN-CHECK.md` (line replacements applied in the wrong order, which put the new run command inside the SQL block). Found by looking at the output, fixed by re-running in the right order, re-checked (sections of the file printed, SQL block read, all fenced blocks re-extracted).
4. Python is now pinned to 3.13 (`PY`). The test counts quoted in the README (9364 and so on) came from runs without the pin; whether the pin changes them is NOT known (the file says so; the verdict computes numbers from the user's own logs).
5. Not changed, with reason: the reviewer's "README 111-112 STOP lines only print" cannot become a hard stop without restructuring a pasted block; I added a comment on both lines that they only print and that `setup` repeats the checks and stops (setup does: it tests `C`, `W`, `P`, `PY`). "tick_state lands in public cannot be checked" was already marked UNVERIFIED in the file; unchanged.
6. The `git diff` settings in `gd` (`diff.srcPrefix`, `diff.dstPrefix`, etc.) were written from the git manual, not tested against a hostile git config.

## Commits checked by text before relying on them
`git diff --stat bbfbeee19 80e9b09a7 -- src tests .github` and `git diff --stat 80e9b09a7 HEAD -- src tests .github`: both printed nothing (head of the day: `ecf701c2a`). `git diff --stat b4cce5b 80e9b09a7 -- src tests .github`: `75 files changed, 8459 insertions(+), 184 deletions(-)`. `HADAVIN_REQUIRE_PINNED_UNIDATA` is at `ci.yml:91` at the newest commit and absent at `b4cce5b` (grep printed nothing there).

## Finding to result table
| Finding (reader r12 = R, code r12 = C) | Result |
|---|---|
| R-M1 / C-Major1 silent psql counts as healthy | Fixed in the job and the query: `psql -X -w`; `unset PGPASSWORD PGSERVICE PGSERVICEFILE PGSYSCONFDIR PGOPTIONS PGHOSTADDR PSQLRC`; query always prints one `OK|||<n>` line and the job requires exactly that line (`NAMES_EXPECTED`); job checks the query file's sha256 (`QUERY_SHA256`, exit 74); T1 and the "Which names" section updated for both settings; T2 one-liner now has `-X -w` and `-p`; alert rule 1 and the unhealthy/healthy examples rewritten |
| R-M2 CLOCK AHEAD | Fixed: `last_ok_at > now() + interval '1 minute'` in WHERE and CASE; clock note explains the 1 minute margin |
| R-M3 unquoted placeholders | Fixed: T2 line, check 1 command and the password block use `"${CA:?}"`, `"${DBHOST:?}"`, `"${DBPORT:?}"`, `"${DBNAME:?}"` after the values are set as variables; a note says `<database>` in the SQL table is typed inside psql, never pasted in a shell |
| R-M4 E() unguarded; cp path | Fixed: `E` refuses to run unless `W`, `$W/home` and `$W/tmp` exist; offline cache copy is `cp -R "${SRC_CACHE:?}"/. "${W:?}/uv-cache/"` with the reason written |
| R-M5 proxy rule contradiction | Fixed: one rule: never edit `E`; the only edit is the line `EXTRA_ENV=(...)` (default empty); line 10 and the setup text say so; process-list exposure of a proxy password stated; redaction advice widened to home path, user name, proxy and machine host names |
| R-M6 proof result not in verdict | Fixed: `proof` compares exit code 1 and the exact last line (12 failed, 18 passed / 13 failed, 19 passed) and prints PROOF OK / PROOF FAILED; `verdict` saves `$W/verdict.txt`; new `final` prints the verdict only after PROOF OK; Pass rule clause (f) added |
| R stale commit pointers (DMC 7) | Fixed: `80e9b09a7`; README head sentence now says "head of the day" with the two dated checks |
| R DMC "row 7" / C-Nit9 | Fixed: "only S7" |
| R RV-D3 (2), RV-X6.6 | Explained in the words row (item (2) of row D-3; part 6 of row X-6, parts X-6.1 to X-6.9); read in `REVIEW.md` lines 105, 113, 117, 180 |
| R T1-T3, D5 missing | Added to the numbering-schemes row |
| R "all is well" signal only in DMC | New words row and a gloss in decision row 8 |
| R clauses before defined | One-line definitions added before the verdict block |
| R sha256 list = drift check | Stated; take values from the lead in a separate message if tampering matters |
| R patch.sha256 one line | `setup` requires exactly two lines |
| R S1 login before password | S1 now `NOLOGIN`; S2 runs `ALTER ROLE ... LOGIN` after `\password`; rollback `NOLOGIN PASSWORD NULL`; "Which login" S2 row updated |
| R secret file in $HOME, clipboard | Password block uses a 700 `mktemp -d` (memory-backed `/dev/shm` where it exists), no `$HOME`; empty-variable guards; clipboard-history warning |
| R no cleanup | New `cleanup` section (requires the `recipe.mark` file, refuses unsafe `W`); token-in-`SRC` warning |
| R STOP lines only print | Comment added (see uncertainty 5) |
| R query a: extension view adds a row | Note added to query a |
| C-Major2 TMPDIR | Fixed: `$W/tmp` made in setup, `TMPDIR` set in `E`; the "writes only into the temporary folder" claim now says exactly what is and is not covered |
| C-Nit3 need_w | `setup.ok` written last, tested by `need_w` |
| C-Nit4 | Same as STOP lines (comment) |
| C-Nit5 git config | `gd` helper with `-c diff.noprefix=false -c diff.mnemonicPrefix=false -c diff.srcPrefix=a/ -c diff.dstPrefix=b/ -c diff.renames=false --no-ext-diff --no-renames`, used in clause (e) |
| C-Nit6 verdict always returns 0 | `verdict` returns the status (`return`, never `exit`) |
| C-Nit7 no Python pinned | `PY=3.13`, `--python "$PY"` in gates, run, proof; CI env var difference stated |
| C-Nit8 NOINHERIT | S1 text names the three attributes correctly (NOINHERIT is not the default) |
| C-Nit10 stale commit | Same as R pointers |
| C-Nit11 trap/timeouts/negative test | SIGKILL limit stated; `PGCONNECT_TIMEOUT=10`, `timeout 60`; TERM/INT/HUP traps; send_alert/send_ok failure exits 75/76; negative test (iii) split into (iii-a) exit 71 and (iii-b) exit 75, plus (iv) fingerprint and (v) psqlrc/wrong count |
| C-Nit12 command -v | Text and script: executables on PATH or functions in the file `DEADMAN_LIB`, sourced before the check |

## Raw command outputs
```
$ sha256sum *.patch   (in patch-copies; equal to the values listed in README, unchanged)
64fdf315221fb9d653fe8defc844aa438c39c56bc32c5a86c70d8aab67892095  A-01.patch
e7ff677e70d0c1fd61e9c4e2f1024c58fd35b83bc715abd3d0449202038dae01  C-01-price-only.patch
ca4982ebb9daef2d5c96e1538d2cdde5291d2d9a948c70553b5661a0a17fded0  C-01.patch
```
`bash -n` on fenced blocks: the extraction loop (script `extract.py` in the scratchpad) printed `README.md fenced blocks 7` and `DEAD-MAN-CHECK.md fenced blocks 6` (13 files). Of these, 8 are shell and were each run through `bash -n`: DEAD-MAN-CHECK job script (21 lines) rc=0; DEAD-MAN-CHECK password block (10 lines) rc=0; README setup (45 lines) rc=0; gates (12) rc=0; run (9) rc=0; verdict (48) rc=0; proof plus final (23) rc=0; cleanup (6) rc=0. The other five blocks are not shell: the sha256 lines, two SQL blocks (query, catalog queries), the unhealthy-result example, the role-finding queries. The two one-line `psql` commands (T2 and check 1) extracted from backticks: `bash -n` rc=0.
Checkers, from `handover/flows-audit`:
```
python3 -I tools/check_refs.py     -> PASS 5171 references        (rc 0)
python3 -I tools/check_names.py    -> PASS 655 rows               (rc 0)
python3 -I tools/check_secrets.py  -> PASS 0 hits in 2690 files   (rc 0)
ruff format --check .              -> 838 files already formatted
```

## Next step
A fresh reader (not the author) should read both files again; the first real test is a run of the recipe and of the changed query on a throwaway machine and a test database, which needs the studio head's test database (already the standing next action in `DEAD-MAN-CHECK.md`).
Files changed: `/home/user/hadavin-sdk/handover/flows-audit/reviews-of-core-patches/patch-copies/README.md`, `/home/user/hadavin-sdk/handover/flows-audit/reviews-of-core-patches/patch-copies/DEAD-MAN-CHECK.md`, this report. No head SHA change (nothing committed; working-copy head `ecf701c2a`). R-numbers: none looked up (static text edit; the bible is a studio-laptop file not in this checkout).
