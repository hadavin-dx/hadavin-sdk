# Fix round 16: patch-copies README.md and DEAD-MAN-CHECK.md (one fixer, security path)

## Failures and uncertainty first
- The recipe was NOT run as one piece. Not run at all: the real test suite, the real gates (`uv run ruff/bandit/pytest`), `gates`, `run` and `proof` as functions, any database, any real scheduler, any real alert channel, any real `psql` connection, `bash -x` of the whole README. `verdict` ran on MADE-UP logs but on the REAL clones that `setup` made.
- Everything about the password blocks and the job script ran with FAKE stand-ins (`psql`, `xclip`, `send_ok`, `send_alert`, `read_deadman_secret`; real `openssl`, `shred`, `mktemp`, `/dev/shm`). The simulated "no /dev/shm" case was done with a fake `mktemp` that refuses `/dev/shm`, not on a real macOS.
- Test-harness slips of mine, no effect on the files: one run wrote a helper file into the patched clone (a relative path after `setup` had changed the folder); one `${CA:?}` test aborted my non-interactive script (in a pasted terminal it only stops the line). Both fixed in the harness and re-run.
- UNVERIFIED and stated as such in the text: swap behaviour of tmpfs, the `PG*` list (from memory), clipboard behaviour of other systems, `wl-copy` (never run, only the `command -v` branch is shaped like `xclip`/`pbcopy`, which was run through a fake `xclip` only).
- Contested reviewer words: none. Partial points (below): M1 "give one concrete way" is met by Block 2b; a stored copy of the secret stays UNANSWERED (owner gap, unchanged, Block 3 still refuses without `STORED_OK=yes`).

## Finding to result
| # | Check against text | Result |
|---|---|---|
| M1 typed PGPASSWORD | Confirmed (DMC bullet 2 and the manual-test line). | Typed `PGPASSWORD=...` route removed. The second choice is now `read -rs PGPASSWORD; export PGPASSWORD` then `unset`, labelled "manual test only, never the job". New Block 2b builds the pgpass file from the secret file with `printf` and `esc` (shell builtins, so no secret on a command line or screen), mode 600, in the private folder, sets `PGPASSFILE`; Block 3 and the trap remove it. Manual-test line now points to Block 2b. |
| M2 clipboard | Confirmed (command was inside a `#` comment). | New Block 1b = real commands (`xclip`, `wl-copy`, `pbcopy`), opt-in with `USE_CLIPBOARD=yes`, says why it did not copy. Route B (no clipboard tool, ssh): the secret is shown once on screen, honestly labelled, with `clear; printf '\033[3J'` afterwards. Block 2 no longer has the comment line. |
| M3 setup/cleanup guard | Confirmed. | `setup` refuses: relative W, folder name not `tmp.??*`/`recipe.??*`, W not owned or a link, any content except `patch.sha256.all`, `extra.env`, `setup.log`. `cleanup` requires the same name pattern, a real owned folder, and the mark. |
| M4 start here | Confirmed. | Line 4 history (about 400 words) and the "Date of this text" paragraph moved to a new last section "History of the passes"; line 4 now short; "START HERE" paragraph added (by section name, not line numbers). |
| Minor SRC echoed | Confirmed, and a second leak found by test: git's own error text names the address. | STOP lines print no SRC; git's stderr goes to `$W/git-error.txt` (test: 0 hits for the bad address in `setup.log`, 1 in `git-error.txt`); `keep_logs` copies it; text says to clean it. |
| Block 1 disk fallback / rerun / openssl failure | Confirmed. | Refuses without `/dev/shm` unless `ALLOW_DISK=yes`; refuses to run twice (F or D set); on openssl failure removes the partial file and folder and empties F and D. |
| set +x | Confirmed. | `set +x` added to the job script; run with `bash -x`: 0 occurrences of the secret in stderr. |
| query read twice | Confirmed. | Job copies the query into `$D`, compares the first word of `sha256sum` of the copy as plain text (also fixes Nit 5), runs psql on the copy. Test: changed hash -> exit 74 + alert; missing file -> exit 74 + alert; psql saw the identical copy. |
| verdict_run rm after early return | Confirmed. | `rm -f` of old `verdict.txt`/`proof.txt` is now the first line (guarded by `W` naming a folder). Test: with SHA empty (early return) both files were removed. |
| PART 1 wording | Confirmed. | Screen line starts "PART 1 OF 2 (not the result yet) - VERDICT: ...". `verdict.txt` keeps the plain line so `final` is unchanged. |
| awk missing | Confirmed. | Clause (c) uses `! grep -qvE ' 0$'` (grep is already needed). Test: a gate code 10 -> (c) FAILED; 5-line `gates.txt` -> (c) FAILED. |
| "run one block only" | Confirmed. | Added before `keep_logs`, `cleanup`, `keep_delete`. |
| -w note | Confirmed. | Block 2 heading says the `psql` has no `-w` on purpose (it asks for the administrator's password). |
| Nit 3 HUP | Confirmed (HUP 1, so 129). | `trap 'exit 129' HUP`. Test: HUP during psql -> exit 129, no folder left. |
| Nit 4 deferred traps | Confirmed. | Documented in the trap comment and in fact 5. |
| Nit 6 exit 0 after alert | Confirmed. | New fact 4. |
| Nit 2 `$(cat)` strips newlines | Confirmed. | Line count tested too (`wc -l` = 1); test: `OK|||4` + empty line -> alert. Fact 5 says so. |
| Nit 1 IPv6 host | Confirmed (printf did not escape). | `esc` in the job and in Block 2b. Test: `2001:db8::1` -> `2001\:db8\:\:1:5432:...`. |
| Nit 7 trap after openssl failure | Confirmed. | See Block 1 row. |
| Nit 8 env pass-through | Confirmed. | `extra.env` command passes ten variables (proxy in both cases, NO_PROXY, four certificate settings); text says anything else is dropped. Test: file mode 600, `E env` sees the variables. |
| Stale line 75 | Confirmed (item 11 is at 85 in REVIEW.md). | Changed to 85. Also stated that REVIEW.md has a second "Plain summary" heading (line 724, old text) and that the first one is meant (REVIEW.md not edited). |

## What I ran (raw results)
- `bash -n` on all 17 shell blocks of both files, after the last edit: `shell blocks 17 bad 0` (three non-shell blocks, SQL/output, excluded).
- Job script with fakes (scratch folder): healthy -> exit 0, `send_ok`; extra blank line -> alert; wrong hash -> exit 74 + alert; missing query -> exit 74 + alert; psql exit 2 -> alert "psql exit 2"; IPv6 host escaped; psql query copy identical; `bash -x` secret hits 0; HUP -> exit 129, `/dev/shm` deadman folders 0.
- `setup` real, end to end, on a local clone (37 s): `setup rc=0`, `setup.ok`; refusals tested: stray file in W, hand-set W name, bad SRC (STOP messages as designed); `extra.env` mode 600 and seen by `E`.
- `verdict` on made-up logs with the two REAL clones: (a) ok, (b) ok, (c) ok, (e) ok (7 changed files, same patch-id), (d1) ok, (d2) ok, "PART 1 OF 2 ... ADDS NO NEW FAILURE", exit 0; gate code 10 and 5-line gates file -> (c) FAILED.
- `keep_logs` (14 files, no `extra.env`), `cleanup` (refused hand-named folder, `$HOME`, empty; removed the real one), `keep_delete` (removed): all as designed.
- Password blocks 1, 1b (with and without `USE_CLIPBOARD`, fake `xclip`: 32 bytes), Route B, 2 (fake psql args printed), 2b (mode 600, secret equal to file), 3 (without and with `STORED_OK=yes`), Block 1 twice (refused), Block 1 after Block 3 (works), openssl failure (no leftovers), no `/dev/shm` (refused; `ALLOW_DISK=yes` accepted); after each window closed: 0 `deadman.*` folders in `/dev/shm`.
- From `handover/flows-audit`: `sha256sum` prefixes `64fdf315` A-01, `e7ff677e` C-01-price-only, `ca4982eb` C-01 (unchanged); `python3 -I tools/check_refs.py` PASS 5178 references; `check_names.py` PASS 655 rows; `check_secrets.py` PASS 0 hits in 2743 files; `ruff format --check .` 890 files already formatted.

## Not run
Real gates/pytest/bandit, `gates`/`run`/`proof` functions, any database or `psql`, macOS, Wayland, a real scheduler or alert channel, `wl-copy`; the cites "at b4cce5b" (reviewer r16 also left these unchecked; I did not re-read the source).

## Open owner/lead items (unchanged, labelled UNANSWERED in the files)
Where the scheduler stores `deadman_reader_password` (blocks T2 and the password procedure); the failure-report channel; where the scheduler keeps the job's stderr; who merges.

## Process
Files changed: `patch-copies/README.md`, `patch-copies/DEAD-MAN-CHECK.md`, this report. Patch files and `../REVIEW.md` untouched. Nothing committed. Scratch files (including a test `extra.env`) were in the session scratchpad and removed. EGM: fix batch for the lead's round; I did not invoke EGM skills; the next independent read is the lead's step. Rules cited: BRIEF-PREAMBLE 3, 5, 6, 11, 14 (secrets, fix-not-defer, honesty, least privilege, wording). Token use: not measured by me.
