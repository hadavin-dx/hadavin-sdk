# Exit-code and visible behaviour changes: the whole v2 diff plus builder F8

Written 2026-11-13. "Before" for the v2 rows = demo base 61ded9e, measured by running the command on an unpacked copy
(`out/F8/v1`, probes below) or read from the code where marked "read". "v2" = tree-V2d (core-fix-v2.patch).
"F8" = this builder's change on top of v2. Exit 1 with a Python traceback is written "traceback (1)".

Not re-measured here: Windows scripts (`.ps1`), macOS. The v2 rows are NOT a complete list of every refusal text change in the
72-file v2 diff; they are every row where an exit code, a hang or a traceback changes, found by reading the v2 diff of
`scripts/`, `src/`, `tools/`, `load_tools/`, `demo_only/` and probing. Anything I did not probe says "read".

| # | Command / cause | Before (61ded9e) | v2 | F8 (this change) | Measured or read |
|---|---|---|---|---|---|
| 1 | `scripts/feed.py`, bad DESK_* setting (`DESK_PORT=abc`) | traceback (1) | 2 | 4 | measured (before); after: tests |
| 2 | `scripts/reset_check.py`, bad DESK_* setting | traceback (1) | 2 (and `reset.sh` stops before it deletes) | 4 | measured (before); after: test |
| 3 | `scripts/crash_desk.py`, bad DESK_* setting | traceback (1) | 4 | 4 | measured (before) |
| 4 | `python -m lead_desk.server`, bad DESK_* setting | 4 | 4 | 4 | measured |
| 5 | desk or `crash_desk.py`, `DESK_DB_PATH=/dev/null/x.db` (a part of the path is a file) | traceback (1, FileExistsError) | 4, one line | 4, one line | measured (before) |
| 6 | `crash_desk.py` with a refused book path | (traceback) | printed `crash flag file: <typed path>` first | prints no typed path before a refusal | F8 test |
| 7 | `scripts/run_real_check.py`, book path refused (`:memory:`, a part of the path is a file, a pipe) | no book-path check in this script (v1 has no `EXIT_BOOK_REFUSED`; the desk answered later) | 4 (`EXIT_BOOK_REFUSED`), `refused: DESK_DB_PATH: <fixed text>` | 4 | read + the 4 updated V6 tests |
| 8 | `scripts/run_real_check.py`, finished without writing (`wrote` false) | 0 when `ok` and nothing left | 3 (`EXIT_FAILED`) | 3 | read (v2 diff line) |
| 9 | `scripts/run_real_check.py --config <pipe>` | hang (measured, rc 124 after 8 s) | not shown by the command line here: the terminal check comes first and refuses (2) | `load_env` raises PathRefused for a pipe; `main` prints `refused: --config: ...`, 2 (tested at `load_env`, not through a terminal) | measured (before) + F8 test |
| 10 | `scripts/run_live_check.py`, standard input is not a terminal | asked y/N on a pipe | 2 (`NO_TERMINAL_TEXT`) | 2 | read (v2 docstring) |
| 11 | `scripts/run_live_check.py`, no `--base-url` | default vendor address used | 2, refused | 2 | read (v2 docstring) |
| 12 | `scripts/run_live_check.py`, typed host is not the provider's | read as "n" -> 1 | 1 | 1 | read |
| 13 | `scripts/run_live_check.py`, a call failed | 3 | 3 | 3 | read |
| 14 | `scripts/run_live_check.py`, `--model` text wrong | argparse error echoing the typed text, 2 | `refused: --model: needs ID=IN_PRICE,OUT_PRICE`, 2 | 2 | read |
| 15 | every script/tool parser, a bad option or value | 2, argparse text (could echo the typed value) | 2, one fixed line (RefusingParser) | 2 | read + probes (hubspot_probe, run_live_check) |
| 16 | `scripts/hubspot_probe.py`, bad arguments | 2 | 2 (new text) | 2; the file now needs `tools/refusing_args.py` next to it | measured (before) |
| 17 | `scripts/n8n_api.py`, any refusal | 1 | 1 (texts no longer echo the name or the file path) | 1 (not changed; see the open item below) | measured |
| 18 | `tools/scrub_n8n_export.py`, input unreadable or not a workflow | traceback or 2 | 2, `refused: in.json: ...` | 2 | read + test |
| 19 | `tools/scrub_n8n_export.py`, output that cannot be written (unencodable text, pipe, folder) | traceback / half file | 2 | 2, and NO half file (text is encoded before the file is created); written through `open_output` (kind checked on the open handle, `O_NOCTTY`) | F8 test |
| 20 | `python -m load_tools.catcher --port 70000` (or `-1`, `abc`) | traceback (OverflowError, 1) | traceback (1) | 2, `refused: --port: needs a port from 0 to 65535` | measured (v2, by the reviewer) + F8 test |
| 21 | catcher / `fake_model_server` / `fakes_server`: host that does not resolve, port already in use, no permission | traceback (1) | traceback (1) | 2, `refused: --host/--port: cannot listen there ...` (fixed text, no host, no port) | F8 test |
| 22 | `fake_model_server` / `fakes_server --port 99999 / -1` | traceback (OverflowError) | traceback | 2, `refused: --port: needs a port from 0 to 65535` | F8 test |
| 23 | `load_driver --scenario burst:nan / inf / 1e400 / rate:inf:1 / rate:1:nan` | traceback (1) | traceback (1) | 2, refused (fixed text) | F8 test |
| 24 | `load_driver --scenario burst:1e18` (or any plan above 100,000 requests) | runs for ever / memory | runs for ever | 2, refused before the schedule is built | F8 test |
| 25 | `load_driver --scenario burst:１０` (full-width digits) | accepted | accepted | 2, refused (ASCII digits only) | F8 test |
| 26 | any file the tools read, when it is a pipe (FIFO), device or socket: `DESK_SMTPP_CA_FILE`, `--config` CA file, checker `--requests/--facts/--catcher/--crm/--model-log`, the control file, `--key-file`, the crash flag file, the armed flag in `portal_demo`, the term lists in `hygiene` | hang (rc 124 in the review) | hang | refused at once, as a refusal or as "no flag" for the crash hooks (never a wait) | F8 test (13 readers in a child with a 20 s limit) |
| 27 | crash flag file or crash-window file that is not UTF-8 or is huge | traceback in the request path (1) | traceback | treated as "no flag" (quiet), size capped at 1 MiB | F8 test |
| 28 | a setting URL (`DESK_HUBSPOT_BASE_URL`, `DESK_LIVE_BASE_URL`, `DESK_FAKES_URL`) with a zero-width, bidi or BOM character, or a non-ASCII host | accepted (Cf not refused) | accepted | `SettingRefused` -> 4 for desk scripts, 2 for the option forms | F8 test |
| 29 | `DESK_LIVE_EFFORT` with a word the vendor does not list | accepted (any non-empty text) | accepted | `SettingRefused` -> 4: `DESK_LIVE_EFFORT must be one of: low, medium, high, xhigh, max` | F8 test |
| 30 | `reset.sh` / `reset.ps1` when `reset_check.py` exits 2 or 4 | no refusal path | stops, nothing deleted (`set -eu`) | same; exit 4 now ALSO means "bad DESK_* setting" in `reset_check.py` | read + `test_reset_scripts` |

## What changed for a reader of exit codes (summary)

- Exit 4 now means "a DESK_* setting or the book path is refused" for every script that reads the desk settings:
  `lead_desk.server`, `crash_desk.py`, `feed.py`, `reset_check.py`, `run_real_check.py` (book path), `desk_setting.py`.
  F8 changed `feed.py` and `reset_check.py` from 2 to 4 for this one cause (finding m1).
- `reset_check.py`: exit 4 now has two meanings (something still answers on a port, or a DESK_* setting is wrong). The
  output line says which (`refused: ...; nothing was deleted` against the port line). This is stated in its docstring and
  README, and `reset.sh`/`reset.ps1` stop on any non-zero code either way.
- Exit 2 stays "a wrong option, value or input (refused)" for every other script and tool.
- Exit 5 (`lead_desk.server`: the port cannot be bound) is unchanged. The catcher and the two fake servers use exit 2 for
  a listen failure (a tool, not the desk); their README lines say so.

## Open item (not fixed, stated)

- `scripts/n8n_api.py` exits 1 for every refusal and 0/1 for HTTP results. It was not part of the F8 findings (reviewer: "not
  changed by the diff"), and changing its codes would break its own tests and docs for no safety gain. Next step: the owner
  decides whether it should join the 2/4 scheme; nothing is hidden by leaving it.
