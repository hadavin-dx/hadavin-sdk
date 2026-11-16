# Fix report, patch-copies, pass 17 (input: patch-copies-reader-r17.md)

Editor: the only editor of `patch-copies/README.md` and `patch-copies/DEAD-MAN-CHECK.md`. The three `.patch` files and the sha256 list were not touched. Nothing committed. Reviewer claims were checked against the file text first (two were wrong or partly wrong: the job script checks 6 tool names, not 7; the "token ceiling" quote was a misquote, `REVIEW.md` says "token limit").

## What failed, what is uncertain, what was not checked
- No `shellcheck` (not installed). No run against a real repository, `uv`, n8n, Postgres or HubSpot. Checks were `bash -n` (all blocks: ok) and runs of the block functions in scratch folders with FAKE stand-ins (real mini git repos with fake patch files; fake `psql`, `send_ok`, `send_alert`, `read_deadman_secret`).
- UNVERIFIED (marked in the text): git identity `recipe@example.invalid` accepted by git, `/dev/shm` size, `pg_authid.rolpassword` visible only to a superuser, the `pg_hba` `hostssl` line, `VALID UNTIL` behaviour, `PSQL_HISTORY=/dev/null`.
- OPEN questions (need an owner, written in the files): (1) commit `b4cce5b` may disappear, so an archive such as `git bundle` is needed (the studio head answers via the lead); (2) D8, password expiry for `deadman_reader` (studio head); D1-D7 unchanged.
- Test notes: `${VAR:?}` exits 127 in `bash -c`, 1 in a script file, 2 in `sh` (documented in the exit-code table). A hostname under 3 characters is skipped by `scrub` by design.

## Items
| Item | Done | How checked |
|---|---|---|
| S1 verdict written before proof | Done. `verdict_run` now writes `VERDICT-PENDING-PROOF: ...`; only `final` writes `FINAL: VERDICT: ...` through `tee final.txt`; `verdict_run` and `proof` remove stale `final.txt`; no `set -e` abort. | `bash -n`; function test with real mini git repos and fake patches |
| S2 `rm -rf` of relative W/K | Done. `cleanup` and `keep_delete` require absolute path, `mktemp` name pattern, owner, not a link, and a mark file (`recipe.mark` or `patch.sha256.all`; `keep.mark`), then remove the `pwd -P` real path. | Test: setup failure (P=/nonexistent) gave rc=1, then `cleanup` printed "removed /tmp/tmp...." and the folder was gone |
| R1 expected output per block | Done. New section "What a good run prints"; `gates` prints `GATES OK (6 x 0)` / `GATES FAILED`; `run` prints expected and actual exit. | read back; function run |
| R2 prerequisites | Done. START HERE item 0, Needs sentence restructured. | read back |
| R3 failed setup leaves folder, `extra.env` | Done. Failure message says: `keep_logs`, `cleanup`, restart with NEW folder; `extra.env` is written only after `setup ok`; `keep_logs` copies through `scrub()`. | failed-setup test above |
| D1 DEAD-MAN-CHECK no entry point | Done. "START HERE: can I run anything from this note today? No." with reading order and words. | read back |
| D2 "DO NOT RUN" only a comment | Done. Block 1 needs `STORAGE_ANSWERED=yes`, refuses if an EXIT trap exists. | block tests with fake stand-ins |
| D3 LOGIN before password check, `pg_hba` order | Done. S2 row requires `pg_hba` line and check 1a first; Block 2 checks `pg_authid` before `LOGIN`; password expiry added as D8. UNVERIFIED on a real store. | `bash -n`; read back |
| Other Minors and cheap Nits | Done: `public.tick_state` and quoted `"<database>"`, `PSQL_HISTORY=/dev/null`, `set +a`, `DBNAME`/PATH rejections (exit 73), `compgen -e` clearing of `PG*`/`PSQL*`, `readonly D` and EXIT trap, D4 text matches the script, settings and exit-code tables, clipboard clearing, git `--` guard, "FIVE named blocks ... six code blocks". | `bash -n`; fake-stand-in run of the job script |
| Wording "token ceiling" | Done: "token limit" in both files. | grep (no hit left) |
| History entries | Done: "Seventeenth pass" in both files, per item; test status line 2b added in DEAD-MAN-CHECK; stale `verdict()` comment fixed. | grep |

## Required checks (from `handover/flows-audit`)
- `python3 -I tools/check_refs.py`: PASS 5182 references
- `python3 -I tools/check_names.py`: PASS 655 rows
- `python3 -I tools/check_secrets.py`: PASS 0 hits in 2784 files
- `python3 -I tools/check_counts.py`: PASS 52 files / 655 nodes
- `ruff format --check .`: 911 files already formatted
- `sha256sum *.patch` starts: 64fdf315 (A-01), e7ff677e (C-01-price-only), ca4982eb (C-01): unchanged.

Not run: EGM review of this result (not invoked from here; the lead runs the EGM step). Backups of the originals are in the scratchpad `bak/` folder.
