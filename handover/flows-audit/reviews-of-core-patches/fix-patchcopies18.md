# Fix report, patch-copies, pass 18 (inputs: patch-copies-reader-r18.md and patch-copies-reader-r18b.md)

Editor: the only editor of `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. The three `.patch` files were not touched. Nothing committed. Reviewer claims were checked against the file text first; all five Majors of the stranger read and all three of the technical read were right (the minors are listed below, with the two that needed no change).

## What failed, what is uncertain, what was not checked
- Static project: no run against a real repository, `uv`, pytest, n8n, Postgres or HubSpot. `shellcheck` is not installed. The new `pg_hba.conf` lines, check 3 g and check 4 (SQL and `psql` commands) were NOT run; they come from the Postgres manual and are marked UNVERIFIED in the text.
- The cites "at `b4cce5b`" were not re-checked (no git data of that commit in this folder): UNVERIFIED, as the technical reader also said.
- Test stand-ins: fake `uv` (prints a chosen last line and exit code), fake `psql`, `send_ok`, `send_alert`, `read_deadman_secret`; real mini git repositories with made-up patch files for `setup`, `verdict_run` and `final`. Running as root, so the "file of another user" tests used `chown nobody`.
- Two slips of mine, found by the tests and fixed before the end: (1) my first pytest-summary pattern in `run` required a space after the word `failed`, so a real summary line ("2 failed, 9364 passed ...") was refused; fixed to `'[0-9]+ (failed|passed|skipped|deselected|errors?).* in [0-9.]+s'` and re-tested; (2) my first test harness lost the fake mode because `E` clears the environment (a harness error, not a text error).
- Not decided here (needs the studio head or the lead, still written in the files): where failure reports go (the new START HERE (0a) says "no named place, no run"), D3, D4, D6, D7, D8, the secret-storage place, the archive of `b4cce5b`.

## Items
| Item | Verdict on the claim | Done | How checked |
|---|---|---|---|
| R18 M1 (line 3 "MAY run" vs line 13 "answer needed first") | right | line 3 and a new START HERE (0a): run only if whoever gave you the recipe named where to send the output (a studio session's own report counts); line 13 points to it | read back |
| R18 M2 (verdict string without scope; "patch is clean") | right | `verdict_run` writes `scope="[scope: commit $SHA; $C and A-01.patch applied in a throwaway clone; database and secrets-store tests skipped; CI and the A-01 database path not run; NOT a merge clearance]"` at the end of every `VERDICT-PENDING-PROOF` line; `final` passes it into `final.txt`; the README text no longer says "The patch is clean" | `verdict_run` and `final` run on scratch git repos: final line printed with the scope; hand edit of the patched clone gave `(e) FAILED` and NOT PASSED with scope; `final` still treats NOT PASSED correctly (the scope text holds no "NOT PASSED") |
| R18 M3 (`run` always printed "expected 1") | right | `run` prints the "expected" text only when pytest exit is 0 or 1 AND the last log line is a pytest summary; else `UNEXPECTED ...` and `return 1`; the two calls are joined with `&&` so the patched run does not start | fake `uv`: exit 1 with summary ok, exit 0 ok, exit 2 with a summary line refused, exit 1 without summary refused, exit 5 refused, `uv` missing (127) refused; chain test: second run skipped |
| R18 M4 (`LIMIT_S` unbounded; fingerprint omits it) | right | job refuses non-numbers, more than 4 digits, and outside 30 to 900 (exit 73); `send_ok` gets one argument `limit_s=<n> names=<n>`; the alert text carries `limit_s`; settings and exit tables updated; "at most 60 seconds" became 65 (see M3 technical) | job script run: 0, 29, 901, 12345, 99999, abc refused (73); 30 and 900 accepted; signal args printed |
| R18 M5 (signal read as "store healthy") | right | defined in the README words box, DMC D7, DMC "What the signal means, exactly", exit table row 0, rule 5 | read back |
| R18 minor: prerequisites omit awk, diff, tee, sed -E, grep -o, openssl, shred | right (awk was used in clause (e) although its comment said it is not needed) | `awk` replaced by `cut -f3` in clause (e); README START HERE (0b) lists the programs; DMC START HERE lists the programs of the blocks and job | `(e)` ok in the scratch test with `cut -f3` (2 changed files, same patch-id) |
| R18 minor: Linux/macOS bash only | right | stated in START HERE (0b) | read back |
| R18 minor: `extra.env` command not in the START HERE order | right | added to item (4) | read back |
| R18 minor: sample `W=/tmp/tmp.` ignores TMPDIR | right | row says "under `/tmp` or under your own `TMPDIR`" | read back |
| R18 minor: sample numbers lack the "from other runs" warning | right | rows for run and proof marked as examples | read back |
| R18 minor: PROOF OK shows counts only | right | text now says `PROOF OK` compares exit code and counts only, and to read `proof.log` against the failure list | read back |
| R18 minor: recovery of W/K | right | new paragraph: set `W` by hand only for `keep_logs` and `cleanup`; `K` for `keep_delete` | read back |
| R18 minor: `<address>/32` not shell-safe; `<database>` note after the table | right | pg_hba lines in a code block marked "file content, not shell"; note moved before the statement table | bash -n on the new block (trivial); read back |
| R18 minor: read-only / statement_timeout checks not numbered; 1b misses pg_service.conf | right | new numbered check 4; 1b has `-u PGSERVICE PGSERVICEFILE=/dev/null` | NOT run (UNVERIFIED, manual) |
| R18 minor: sample from old query form (DMC 99-104) | already answered in the text (line says "first-pass query", and after it "today's form") | only added "shape only, not today's output" | read back |
| T18 M1 (role valid for every database; only an allow line) | right | two reject lines after the allow line (`host all deadman_reader all reject`, `local ... reject`), reason, IPv6 fails closed, exposure to be accepted in writing when the provider allows no lines; new check 3 g (`pg_database` + `has_database_privilege`) and "run check 3 in every database listed"; check 1a expects the reject lines | NOT run (UNVERIFIED, from the manual) |
| T18 M2 (newline in the secret; error log without mode or link check) | right | secret with line break or CR: alert and exit 72; error log: link, directory or file of another user refused (73), mode 600 set on every run | secret with LF and with CR refused; symlink refused and the link target not created; mode 666 file became 600; file owned by `nobody` refused; directory refused |
| T18 M3 (`timeout` without `-k`, 137 undocumented) | right | `timeout -k 5 60`; 137 documented next to 124 | a fake `psql` that ignores the terminate signal, with a test copy `timeout -k 1 2`: killed, `psql exit 137` in the alert, error log line `rc=137` |
| T18 minor: README scrub strips only to first `@` | right | regex now strips up to the LAST `@` before the next `/` | `scrub` run on a made-up web address whose password held an at-sign: removed whole; `https://example.invalid/path@notuser` untouched |
| T18 minor: extra.env may pre-exist (154) vs written after setup ok (182) | right | `extra.env` removed from the allowed list; the STOP message says why | `setup` run: refused with extra.env, then full `setup` with fake patches rc 0 |
| T18 minor: no PATH guard in `E` | right | `E` refuses an empty or relative PATH entry | `E` run with `/usr/bin::/bin`, `/usr/bin:rel/bin`, `:/usr/bin` (refused) and a clean PATH (runs) |
| T18 minor: `git fetch` without `--` | right | `fetch -q origin -- "$SHA"` and `-- cloud/core-hardening` | scratch repos: fetch by commit id and by branch name with `--` both worked |
| T18 minor: S7 connection limit 2 vs manual checks | right | S7 reason says run checks one at a time and not in the job's minute, or raise to 3 temporarily | read back |
| T18 minor: pg_authid read impossible on a managed service | right | "password check skipped", accepted in writing, rely on check 1b | read back |
| T18 minor: DEADMAN_LIB check only in prose | right | `-f`, not a link, `-O`, no group/other write (`find -perm /022`), else exit 73 | group-writable, symlink, other owner each refused; private file accepted |
| T18 remarks (pipes fail closed; S5 rollback; cites not checkable) | no defect | no change; cites not re-checked (stated) | n/a |
| History entries | | "Eighteenth pass" in both files; README date line; DMC test status 2c | grep |

## Required checks (from `handover/flows-audit`, each run with its own exit code captured)
- `python3 -I tools/check_refs.py`: rc 0, PASS 5182 references
- `python3 -I tools/check_names.py`: rc 0, PASS 655 rows
- `python3 -I tools/check_secrets.py`: rc 0, PASS 0 hits in 2798 files
- `python3 -I tools/check_counts.py`: rc 0, PASS 52 files / 655 nodes
- `ruff format --check .`: rc 0, 924 files already formatted
- `bash -n` on every fenced block of both files: all shell blocks ok; the four blocks that fail are SQL or sample output (README none; DMC: the query, the sample output, the catalog-finding queries, the check 3 queries), as expected.
- `sha256sum` of the three patch files, prefixes: A-01 64fdf315, C-01-price-only e7ff677e, C-01 ca4982eb (unchanged).

Not run: EGM review of this result (the lead runs it). Backups of the originals: scratchpad `bak18/`. Scratch tests: scratchpad `t18/`. No process left running; `/dev/shm` holds no leftover job folder.
