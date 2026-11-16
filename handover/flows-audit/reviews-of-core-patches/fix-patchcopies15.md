# Fix round 15: patch-copies README.md and DEAD-MAN-CHECK.md (one fixer, security path)

## Failures and uncertainty first
- The recipe was NOT run as one piece. No full test suite, no real database, no scheduler, no alert channel, no real `psql` connection. Real runs in this pass: `setup` (end to end, local clone of this checkout, 42 s, `setup ok`); one real `uv run ... ruff check src tests demos` on the unpatched clone through the NEW `E` (exit 0, `All checks passed!`).
- Everything else was run with stand-ins or fragments (list under "What I ran"). `gates` ran with a stub `uv` (not real gates on both clones). `verdict` as a whole did not run; only the new wrapper, with a stand-in for `verdict_run`.
- UNVERIFIED, written into the files as such: the list of cleared `PG*` variables is from memory (no libpq manual here); `tmpfs` swap behaviour; psql error text content; what a failed offline `uv` run prints; psql behaviour in general (reviewer's own "not checked" list stays unchecked by me).
- OPEN question for the lead (written into DMC as UNANSWERED, third point after the job script): where the scheduler keeps the stderr of the job (exits 70 to 76). The failure-report channel stays an open question in the README (unchanged text).
- Contested findings: none. Two partial deviations, stated: (1) M8 asked for a log "only root reads": the job writes the error log with `umask 077`, so it is readable by the job's user and root; whether the job runs as root is the scheduler operator's decision (D6), written into the text. (2) The `grep -E '^(FAILED|ERROR) '` item is below threshold and fail safe (only a false failed (a)/(c)); I did not change the regex (a tighter one could miss a real failure, which is fail unsafe); a comment says so.
- Left over in /tmp: three or more `tmp.*` folders (`patch.sha256` only, or empty) that I cannot prove are mine (other agents' extracts are also there); I removed only the two I am sure about.

## Finding to result
| # | Check against text / src | Result |
|---|---|---|
| M1 evidence lost | Confirmed: `gates` kept exit codes only, setup output not saved, `verdict.txt` held one line, `keep_logs` omitted files; README line 12 said setup prints a log line (it prints none; `run` and `proof` do). | `setup` output now goes to `$W/setup.log` (`${W:?}` guard); `gates` writes six `gate-<folder>-<cmd>.log` files (rc still captured right after the command); `verdict` is now a wrapper over `verdict_run` that tees every clause line to `$W/verdict-clauses.txt`; `keep_logs` copies 15 named files (setup, gate logs, rc files, failed lists, clauses, o-*.txt, proof files); line 12 rewritten with the full file list and the false sentence fixed. |
| M2 kept folder never deleted | Confirmed. | `keep_logs` writes `keep.mark`; new `keep_delete` removes only a folder with that mark (tested: refuses empty K, `/`, `$HOME`, `/tmp`). |
| M3 proxy credentials in `ps` | Confirmed (`env -i` argv). | `E` now reads a private file `$W/extra.env` (mode 600) through an inner `bash -c` that sources it and `exec`s the command; safe command given in the text; `EXTRA_ENV` comment says never put a proxy there; "not a sandbox" says the code can read it; allowed edit (2) names the command; delete command and `/dev/shm` option given. Tested: values reached the command, file mode 600, `ps` showed no value, real `uv` ran through it. |
| M4 offline route | Confirmed unverified. | Text now says it was not seen, and lists three observable signs (non-zero first code, `uv` text in the first gate log, no pytest summary line last in `baseline.log`), marked UNVERIFIED. |
| M5 job temp folder on disk | Confirmed (default `/tmp`). | Job default is `/dev/shm`; job refuses (exit 70) unless GNU `stat -f -c %T` says `tmpfs` or `ramfs`; ran: `/dev/shm` accepted, `/tmp` refused with exit 70 in the job. macOS and swap limits written as limits. |
| M6 S2 block | Confirmed (delete lines commented; STOP echoes did not stop; psql in a pasted block would swallow the following lines). | Three blocks; real `if` guards; real delete lines in Block 3 gated by `STORED_OK=yes`; clipboard overwrite is a real command; "exists until the last line runs" replaced by a true sentence. Ran Block 1 + 3 (file 32 bytes, folder mode 700, removed, `/dev/shm` empty after) and the not-stored branch. |
| M7 two "T2" | Confirmed. | One-liner relabelled "MANUAL TEST ... NOT for scheduling" with its gaps listed; T2 row says job only; alert rule says the job applies it; "Run (T2)" references renamed. |
| M8 psql error text lost | Confirmed. | New required setting `DEADMAN_ERRLOG`; job appends time, exit code and `$D/err` when rc is non-zero or err is non-empty; alert says the text is in the log (not sent); stderr place named as an open question. Ran with a fake `psql`. |
| M9 S2 order, "two logins" | Confirmed (S2 was row 2; README said two logins, DMC table needs up to four). | Statement table has a "Run order" column and the rows are placed in that order, S2 last (labels unchanged so every cite holds); heading rewritten; README table row and DMC "two logins" sentence now say up to four. |
| M10 pass history / setup comment | Confirmed (`git add -A` had no `|| return 1`; also `rm -f`, `: >` lines). | All three given `|| ... return 1`; comment now "every command that can fail has a `|| ... return 1`" (checked by eye); pass history rewritten for passes 13, 14, 15 in line 4, line 20, and the `gd` sentence; `setup` call line no longer has nested double quotes. |
| M11 verdict/proof | Confirmed. | Definitions list (f), heading "Six clauses (a) to (f)", verdicts PASSED/ADDS NO NEW FAILURE name (f); `verdict_run` deletes `proof.txt`; the last printed line says "NOT the result yet ... do NOT run verdict again after proof". |
| Check Major (T1 says exit 74) | Confirmed against job: `case "$QUERY_SHA256"` gives exit 73, no `send_alert`, stderr only; exit 74 only at the fingerprint compare. | T1 rewritten: exit 73, no alert, stderr only, receiver alarms later; exit 74 only for a correct value of a changed file. |
| psql unset list | Confirmed overstated. | List extended (PGHOST, PGPORT, PGDATABASE, PGUSER, PGSSLCERT, PGSSLKEY, PGSSLCRL, PGSSLCRLDIR, PGSSLSNI, PGSSLCERTMODE, PGGSSENCMODE, PGTARGETSESSIONATTRS, PGCHANNELBINDING, PGLOADBALANCEHOSTS, PGTZ, ...) and the comment narrowed: the list is from memory, a variable not on it could still act, the exact-output test and exit code are the control. |
| macOS `timeout`, nit quotes | Confirmed. | Text says macOS lacks `timeout`/`sha256sum` and the job refuses there (exit 70) until wrappers exist. Quote nit gone with the new setup line. |
| Cross-file notes | Confirmed. | README line 16: recipe applies A-01 only in its throwaway clone, no A-01-free variant. DMC "What it does not cover": the two outages separated (outage while the check runs = exit 2; outage inside the tick = `STALE`). |
| Reads of src/migrations | Checked only what my edits rely on: `0003_approvals_tick.sql` unchanged assumptions (not re-read in full; reviewer's verification accepted for the query). | No claim about src was added. |

## What I ran (and nothing else)
`bash -n` on every shell block of both files (all exit 0, re-run after the last edit); `setup` end to end on a local clone (real); one real `ruff check` through the new `E`; `gates` with a stub `uv` (six lines in `gates.txt`, six logs, bandit stub code 1 captured correctly); `E` with made-up proxy values (mode 600, values visible to the command, absent from `ps`, STOP when `W` unset); `keep_logs`/`keep_delete`/`cleanup` on a real `$W`; `verdict` wrapper with a stand-in; the job script with fake `psql`, `send_ok`, `send_alert`, `read_deadman_secret` (healthy, failing psql, disk folder, relative error log, hash with file name); S2 Blocks 1, 3 and the empty-F branch of Block 2; `stat` and `case` fragments.

## Raw outputs
```
$ sha256sum patch-copies/*.patch   (prefixes)
64fdf315  A-01.patch
e7ff677e  C-01-price-only.patch
ca4982eb  C-01.patch
$ python3 -I tools/check_refs.py    -> PASS 5177 references
$ python3 -I tools/check_names.py   -> PASS 655 rows
$ python3 -I tools/check_secrets.py -> PASS 0 hits in 2727 files
$ ruff format --check .             -> 874 files already formatted
setup (real):  ... A-01.patch: OK / C-01-price-only.patch: OK / check ... ok / setup ok   (42 s)
real gate:     Installed 76 packages ... All checks passed!   (rc 0, unpatched, via new E)
job (fake tools): healthy -> exit 0, send_ok called; psql fails -> send_alert "psql exit 2", error log "rc=2 / FATAL: password authentication failed ..." mode -rw-------;
                  DEADMAN_TMP=/tmp -> exit 70; relative DEADMAN_ERRLOG -> exit 73; hash+file name -> exit 73
S2 Block 1+3:  secret 32 bytes, folder drwx------, "secret file and folder removed", /dev/shm deadman folders left: 0
keep_delete:   removed own folder; refused '', '/', $HOME, /tmp
```

## Process
Files changed: only `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md` (plus this report). REVIEW.md not edited; cited by section heading only. Nothing committed. EGM: this is a fix batch for the lead's round; EGM skills not invoked by me (the next independent read is the lead's step). Studio bible not in this checkout: no R-numbers cited. No sub-agents; no background processes left running.
