# Fix round 14: patch-copies README.md and DEAD-MAN-CHECK.md (one fixer, security path)

## Failures and uncertainty first
- The new text and shell lines were NOT run. All I ran: `bash -n` on the four touched shell blocks (README: the `EXTRA_ENV` block, `setup`, `keep_logs` + `cleanup`; DMC: the job script), all exit 0; one throwaway test of the new `QUERY_SHA256` check (below); the four tool checks and `sha256sum`.
- OPEN question for the lead (not invented): the channel that receives a failure report is still unnamed. The README still says so (UNANSWERED). I only made sure the logs exist to be sent.
- I did not read the patch files, src or migrations beyond what M2 needed: the query in DMC (lines 54-76 of the file at the time) selects only `step, last_ok_at, last_run_at, problem` and the file itself says it reads no `last_error`; so stdout holds no host name or secret (checked against the file text; the query was not run against a database).
- `keep_logs` is new and NOT run. The new `QUERY_SHA256` check in the job script was tested only as a standalone fragment (3 inputs, see below), not inside the full job.
- Both files are very long; I re-read only the passages I changed plus the passages the findings name.

## Finding to result
| # | Check against text | Result |
|---|---|---|
| M1 logs not kept | Confirmed: `run`/`proof` write `$W/baseline.log`, `patched.log`, `proof.log`, `gates.txt`, `verdict.txt`; `cleanup` deletes `$W`. | README: "Where to send a failure report" now says where the full output is and to copy it before `cleanup`; new function `keep_logs` (copies the six files to a new `mktemp -d` folder, prints it, says to clean them first) placed before `cleanup`; the two "read the two logs" places now name `$W/baseline.log` and `$W/patched.log` and the copy step. Channel stays an open question. |
| M2 alert lacks which step | Confirmed (alert had only exit code and line count). stdout safe per query columns; stderr stays unsent. | DMC job: alert now adds the first 10 lines of `$D/out` (max 600 characters, `;` joined); comment says why stdout is safe and stderr is not sent. |
| M3 may P be edited | Confirmed unclear: line 13 lists (1) values incl. P, (2) EXTRA_ENV, (3) macOS; line 124 said "the ONE line". | README: edit (1) now says P MUST be set; the `EXTRA_ENV` comment now says it is "the line of allowed edit (2)" and names (1) and (3). |
| M4 QUERY_SHA256 whole line | Confirmed: job builds `"<hash>  <file>"` itself; T1 said "record `sha256sum dead-man-check.sql`". | DMC T1: record only the first word (64 hex characters), why. Job script: new check right after `NAMES_EXPECTED`: exit 73 with a plain message unless exactly 64 lowercase hex characters (fragment test: valid hash accepted rc 0; hash plus file name rc 73; empty rc 73). Uppercase hex is refused too (sha256sum prints lowercase). |
| M5 verdict after proof | Confirmed: proof copies test files into `$W/unpatched` and runs `git add -A`. | README proof section: says a second `verdict` after `proof` prints "(e) FAILED"/NOT PASSED with nothing wrong; do not rerun, use `keep_logs`, `cleanup`, start again. |
| M6 false STOP on fetch | Accepted (low). | `setup`: `git cat-file -e "$SHA^{commit}"` is tried first; fetches only if the commit is not already in the clone. Not run (no clone made). |
| Cite by heading | Requested by lead. | README line 8 and DMC line 4 now cite `../REVIEW.md:77` plus section "Plain summary (read this first)" and the item text "3. C-01: DO NOT APPLY NOW" (checked: line 77 starts that text, under heading at line 74). |

Unconfirmed test claims named by the reviewer ((d1), (d2), (e) behaviour) were left as the README already states them (fail safe, UNVERIFIED).

## Raw outputs
```
$ sha256sum patch-copies/*.patch   (after all edits; equals the three required)
64fdf315221fb9d653fe8defc844aa438c39c56bc32c5a86c70d8aab67892095  A-01.patch
e7ff677e70d0c1fd61e9c4e2f1024c58fd35b83bc715abd3d0449202038dae01  C-01-price-only.patch
ca4982ebb9daef2d5c96e1538d2cdde5291d2d9a948c70553b5661a0a17fded0  C-01.patch
$ python3 -I tools/check_refs.py   -> PASS 5175 references
$ python3 -I tools/check_names.py  -> PASS 655 rows
$ python3 -I tools/check_secrets.py -> PASS 0 hits in 2708 files
$ ruff format --check .            -> 856 files already formatted
bash -n (README blocks 0,1,2; DMC job script): exit 0 each
QUERY_SHA256 fragment: valid -> accepted rc=0; "hash  x.sql" -> bad rc=73; "" -> bad rc=73
```

## Process
Files changed: only `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. Nothing committed. EGM: this is a fix batch for the lead's round; the next independent read is the lead's step (EGM skills not invoked by me). R-numbers: the studio bible was not available in this checkout; none cited. No sub-agents or background processes started.
