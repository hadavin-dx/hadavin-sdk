# rv17 review: sonar-p3-path-helper-v3.patch (fresh clone db54e13, after P1 v3 and P2 v2; P3 also alone on base)

Reviewer: fresh, independent, shell. Scratch: /tmp/work/rv17-26592 (r = base+P1v3+P2v2+P3v3, p3only = base+P3v3, pr/ = my probe scripts and mut.py). No pushes, no network writes, made-up data only. The full suite was NOT run. Bible folder not in this environment (preamble rule 1: R-numbers not looked up). Rules used: 5, 6, 7, 12, 19, 20.

## Verdict
No Blocker. One Major (Windows, reasoning only, not run). The core confinement is sound: I found no bypass for the non-anywhere callers, and no caller can reach `anywhere=True` from user input. Several tests are weaker than the helper's text claims (6 of my 16 mutants survive).

## FAILURES FIRST

### MAJOR-1 (Windows only, reasoning, NOT run) `anywhere` mode refuses a config on a mapped network drive or a UNC path
`confine(..., anywhere=True)` checks `_inside(real, root)` for `root` in `_anchors()` = `os.path.abspath(os.sep)` plus `X:\` for each existing drive letter. `real = os.path.realpath(text)` on Windows (CPython 3.8+) resolves a mapped network drive to its UNC form (`Z:\cfg\run.env` becomes `\\server\share\cfg\run.env`, via `_getfinalpathname`). That UNC path is inside no `X:\` anchor, so `commonpath` raises or differs and the result is "path is outside the allowed folders", although the message of the helper says every folder of the machine counts. A config written as a UNC path directly fails the same way. The base code read both. Not measured: this box is Linux; I read the CPython behaviour from memory and did not run it. Fix (cheap, and right for `anywhere` in its own right): in `anywhere` mode do not test containment at all, take the root from the resolved path itself (`os.path.splitroot(real)[0]`, plus the separator) and walk from there; this also removes the `os.path.isdir("A:\\")..("Z:\\")` probe that rv13 noted can stall on a disconnected drive. Add a ntpath-based unit test with a UNC `real`.

### MINOR-2 six of my 16 mutants SURVIVE (tests are weaker than the helper's claims)
Mutants of tools/pathconfine.py, run against tests/test_path_confinement.py (152 tests, all pass on the unmutated code), `pytest -x`, 4 in parallel. My list, not the builder's (script: /tmp/work/rv17-26592/pr/mut.py; raw: pr/mut.out):
| mutant | result |
|---|---|
| N01 non-anywhere callers also use the fallback (`if not anywhere: raise` -> `if False`) | KILLED (test_v1_anywhere_works_when_an_ancestor_folder_cannot_be_listed) |
| N02 C1 controls (U+0080-U+009F) allowed | SURVIVED |
| N03 DEL (U+007F) allowed | SURVIVED |
| N04 no 255-character limit on a new name | KILLED |
| N05 new name copied from the argument instead of the table | KILLED |
| N06 no "link left after resolution" check | KILLED |
| N07 system temp folder not an allowed root | SURVIVED |
| N08 `LEAD_DESK_PATH_ROOTS` ignored | KILLED |
| N09 explicit `roots=` not realpath'd (abspath) | SURVIVED (a root that is itself a link would then refuse its own files; no test uses a link as a root) |
| N10 return `Path(real)` instead of the listing's path | KILLED |
| N11 SQLite option `mode=rw` | KILLED |
| N12 SQLite URI not percent-encoded | KILLED |
| N13 folder-in-the-middle check inverted | KILLED |
| N14 fallback tries the raw argument before the resolved path | SURVIVED (in `anywhere` mode the returned text would be the unresolved argument: exactly what the module says never happens; nothing tests the order) |
| N15 empty text allowed | KILLED |
| N16 path equal to an allowed root (`relative == "."`) handled as a name | SURVIVED (`confine(".")` / a folder equal to a root is untested; today it is refused with the new-name message when `output=True` and returns "no such file" otherwise) |
The README and the helper text promise control characters (all of C0, DEL, C1) are refused and the temp folder is allowed; neither is pinned by a test. Cheap tests: one parametrized over `\x7f`, `\x85`, `\x9f`; one `confine(tempfile.gettempdir()/x)` from an unrelated cwd; one with a link as an explicit root; one asserting the `anywhere` fallback result equals `realpath` when both exist (argument given through a link).

### MINOR-3 the allowed folders are wide, and an existing file inside them is overwritten (README says less than it could)
Measured (pr/p1.py): from a scratch cwd under /tmp, `../etc/passwd` resolves to /tmp/etc/passwd and is accepted, because the whole system temp folder is a root; on a shared host every file in /tmp can be read or overwritten by a wrong argument. The repository root is a root, so `--json src/lead_desk/desk.py`, `--out .github/workflows/x.yml` or `--log .git/hooks/pre-commit` pass (an existing name matches the listing, so the new-name table does not apply). The README states the right threat model (fence against a wrong argument, not a hostile shell, not an agent that sets `LEAD_DESK_PATH_ROOTS` or the working folder, no TOCTOU defence; also `TMPDIR` moves the temp root, same class), so it is honest. What it does not say: an existing file in an allowed folder, source code included, is overwritten by an output option. One sentence in load_tools/README.md would close the gap; no code change needed for the stated threat model.

### MINOR-4 a folder you can enter but not list inside an allowed root is refused (only `anywhere` has the V-1 fallback)
Measured as uid 65534 (python `os.setuid` in a child): `/tmp/work/rv17-26592/tv` mode 0711, file `tv/inner/c.env`: `confine(path)` -> "a folder on the path cannot be listed"; `confine(path, anywhere=True)` -> the path. The notes say so ("a listing refusal stays a refusal inside the allowed folders"), the README does not. Narrow (a 0711 folder under cwd or a listed root that you do not own).

### MINOR-5 sibling not covered: scripts/run_live_check.py `--key-file` and `--ledger`
Rule 7 (siblings). README lists it as "not covered, on purpose, for the same reason" (any folder). That reason holds for the key file the operator names, and for run_real_check; it is weaker for `--ledger` (a write target chosen on the command line). Sonar did not flag it (not part of the 11+1), so it is a decision for the owner, not a failure of this patch. All other argv/environment path sinks I grepped (feed.py, reset_check.py, crash_desk.py, hubspot_probe.py, check_schema.py, tools/hygiene.py) read fixed repository files; `N8N_API_KEY_FILE` (environment) is correctly left alone; run_real_check reads the book from the config path through the unconfined `read_book` by design (documented in docs/real-services.md).

### NIT-6 `python tools/scrub_n8n_export.py in.json out.json` (direct start) now fails
`ModuleNotFoundError: No module named 'tools'` (measured). Base worked, because it imported nothing from the repository. The documented form is `python -m tools.scrub_n8n_export` (usage text, docs), which works; the three load tools and n8n_api got a sys.path fallback, scrub did not. Same class as rv8 MINOR-5.

### NIT-7 default `--facts` name is a NEW name derived from an existing log name
`load_driver --log "my run.log"` (existing file) -> `ERROR: --facts: the name of a new file may only use letters, digits...` (measured), about an option the user never typed. Rare (existing log with a space). Mention it in the message or derive the facts name only from an allowed-character log name.

### NIT-8 text controls beyond `_CONTROL`
An EXISTING name with U+202E (right-to-left override), U+2028/2029 or zero-width characters is accepted (measured: `ex<U+202E>is` and `ex<U+2028>is` returned). Messages print `path.name` (for example "cannot read {name}"), so a file the operator already has could spoof a printed line. Impact negligible (the name must already exist in an allowed folder). The README sentence "any name except one with a control character" is literally true (C0, DEL, C1).

### NIT-9 other
* `com0`/`lpt0` are allowed as new names (Python 3.13 `ntpath.isreserved` also says False; recent Microsoft documentation lists them as reserved; unverified).
* `os.getcwd()` in `allowed_roots` raises `FileNotFoundError` (traceback) if the working folder was deleted.
* Windows: a name `con.` or `nul.txt` as an EXISTING file is read normally (by design), but a NEW `x. ` cannot occur (table has no space). Fine.

## What I checked and found CORRECT (measured on Linux, Python 3.13.18)
* Is the `anywhere` fallback a bypass for non-anywhere callers? No. `except _Unconfirmed: if not anywhere: raise` is the only branch that reads `text`; N01 (removing the guard) is killed by a test. `anywhere` is a keyword-only argument; the only caller passing it is scripts/run_real_check.py:844 with the literal `True`, applied to the operator's own `--config` (grep over load_tools, scripts, tools, src: one hit; tests excluded). No `**kwargs` forwarding, no env or flag reaches it.
* The fallback in `anywhere` mode (returns `realpath` or the argument) is by construction what an unchecked open does; `/etc/passwd` anywhere -> accepted, `/etc/nonexist` -> "no such file", `/dev/fd/0`, `/proc/self/environ` without anywhere -> outside.
* Output rules (pr/p1.py): `con`, `CON.txt`, `Com1`, `lpt9.x`, `aux.tar.gz` refused; `nul.`, `a.`, `...` refused; `com0`, `..x`, `.hidden` allowed; names with space, `:`, `*`, non-ASCII, RLO refused; 256 characters refused; NUL and newline in the text refused; 4096+ characters refused. NFD file found by an NFC argument. Trailing slash on an output is stripped (`newf/` -> `newf`). `ntpath.isreserved` agrees on the device list.
* Links: a link out refused, a link in resolved, a link loop refused, a dangling link whose target is outside refused, one whose target is inside resolves to the target (written there, inside the root, fine).
* Roots: env root accepted, empty and `os.pathsep`-only env ignored, relative env root `..` resolved against the cwd; `LEAD_DESK_PATH_ROOTS=/` allows everything (operator's choice).
* 100,000-file folder: missing name 0.05 s, last name 0.09 s per call. Fine.
* SQLite URI (pr/p2.py): `a?b.db`, `a#b.db`, `a%3Fb.db`, `a&mode=rw.db`, `ü.db`, `a b.db` connect read-only and an INSERT fails ("readonly"); the helper adds only the fixed `?mode=ro`.
* Every flagged site (issues-pr4-0253.json: 11 S8707 + 1 S8706). check_invariants.py:63/82/96/597/605/614: all reached only through `main` after `_confined` (requests, book, catcher, crm, model-log, drain, facts, json); `read_book` builds its URI through the helper. load_driver.py:366/377: `run()` confines `--log` and `--facts` first (before any send), the part files and writes use only the confined log. n8n_api.py:192: `confine(a[2], what="FILE")`. run_real_check.py:645: `load_env(confine(a.config, ..., anywhere=True))`. scrub_n8n_export.py:178/179: both confined before read and write. catcher `--out`/`--control` (not flagged) also confined, nothing created when refused (measured: `--out /etc/zz.jsonl` rc 2, no file; `--control /etc/x.mode` rc 2, no `c2.jsonl` created either).
* Behaviour for documented runs. Real run, config and book outside cwd, repository and temp (I set TMPDIR to a scratch folder so /tmp was not a root; config and DESK_DB_PATH in another scratch folder), against local fakes only (DryFakes: every base URL 127.0.0.1 or localhost, no vendor host; I answered `y` only to that): exit 0, result file written. Missing config: `refused: PathRefused: --config: no such file` rc 2 (before: a different OSError text; refusal is before the Start question). Config with a newline in the name: refused. Config that is a folder: `refused: IsADirectoryError` rc 2. scrub with a missing input: `refused: in.json: no such file` rc 2 (before: a traceback). Catcher `--out` in a folder with a space in the DIRECTORY name works; a NEW file name with an accented letter or a space is refused (documented in the README).
* "Pre-existing test fixed" claim: the test `test_a_real_run_with_config_and_book_outside_reaches_the_y_n_question_and_the_book` is NEW in this patch (it is in tests/test_path_confinement.py, which P3 creates); `git diff --stat -- tests` on base+P3 is empty (no existing test file is edited). So the claim means "my own test, which also exists in v2". True as far as it goes. That test and the whole-run test use `n` (first) and DryFakes with `y` (second; loopback fakes only).
* Gates on the stack (base+P1v3+P2v2+P3v3, after `git add -A`): `ruff check` clean; `ruff format --check` 150 files clean; `mypy --platform linux` and `--platform win32` clean (28 files); same four on base+P3 alone (27 files) clean. Apply: all three patches apply cleanly in order. Tests: tests/test_path_confinement.py 152 passed; test_load_tools + test_scrub_n8n_export + test_n8n_api_url + test_real_check_dry: 542 passed, 1 skipped; test_hygiene + test_gitleaks_exceptions + test_codeant_hygiene with `DPLD_REQUIRE_SCAN=1` and gitleaks 8.30.1 (/tmp/work/gl/gitleaks): 111 passed. (`uv run --group test` does not work in this checkout: the project has no `test` group; I used a prepared venv with the same pins.)
* Not run: bandit -ll (not installed here), full suite, Windows, macOS, Sonar, CodeQL, the unprivileged-user case beyond the single 0711 check above.

## rv8 and rv13 findings: closed?
* rv13 V-1 (traverse-only folder, `--config`): closed for `anywhere` (re-measured as uid 65534: accepted; process substitution also covered by the fallback). Left open by design inside allowed roots: MINOR-4.
* rv13 V-2 (message): closed ("no such file" for reads; the new-name message only for `output=True`; but see NIT-7).
* rv13 V-3 (device names, trailing dot): closed on every OS, cross-checked with `ntpath.isreserved`.
* rv13 V-4 (NFC/NFD): closed, tested with a real decomposed name.
* rv13 V-5 survivors M01/M03/M05/M07: the builder's own tests now kill them (not re-run by me); my mutants N02, N03, N07, N09, N14, N16 are new survivors (MINOR-2).
* rv13 P-1..P-6 concern the probe, not this patch.
* rv8 MAJOR-1 (real run outside the repository): closed (exit 0 run above). MAJOR-2 (call-site test for the SQLite helper): N11 and N12 are killed through the helper test; I did not re-run the call-site mutant of rv8. MAJOR-3 (siblings): catcher done; run_live_check left, listed with a reason (MINOR-5). MINOR-5 (direct start): load tools fixed (verified `load_driver.py --help` without PYTHONPATH), scrub still broken (NIT-6).

## Strays
`/nonexistent` (mtime 03:02) and `/nonexistent-x` (03:18) exist at absolute system paths on this box. They predate my first command (about 04:09); rv8 saw them too. Not created by me; I did not delete them.

## Files
Patch: /tmp/demo-lead/handover/demo/sonar/sonar-p3-path-helper-v3.patch. Checked tree head db54e13 + three patches (uncommitted, index only) at /tmp/work/rv17-26592/r and /tmp/work/rv17-26592/p3only. Probes: /tmp/work/rv17-26592/pr/p1.py, p2.py, p3.py, p4.py, mut.py, mut.out. Processes I started (catcher with timeout, the backgrounded one stopped with TaskStop, the fakes) are all stopped.
