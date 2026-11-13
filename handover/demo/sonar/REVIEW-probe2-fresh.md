# rv19: fresh review of probe-ab-v2.patch (PROBE-AB-V2-NOTE.md, evidence-probe2-*)
Reviewer: fresh, independent, shell. Scratch /tmp/work/rv19-1 (clone at db54e13 in c/, probes in probe/, mutants in m/). No pushes, no network writes, made-up data only; no file written at an absolute system path (my first probe tried /root/..., was denied, redone with scratch folders only). Rules used: preamble 5,6,7,8 (venv fresh-venv5, no uv test group),12,13 (I am a reviewer, not the lead's EGM step). I read rv13-report.md only after my pass.

## VERDICT: PROBE SAFE (to push as a throwaway draft PR) -- but the experiment is NOT cleanly readable for pairs B, D and E (Majors below); fix the note (and, better, re-cut two sites) before relying on those rows.
Safe means: applies alone, no site weaker than base, no secret, correctly marked. It does not mean the Sonar reading will be unambiguous.

## FAILURES / FINDINGS FIRST
### Major M1: pairs B and D cross the taint SOURCE kind, so "the ONE difference" is false
Evidence: flows-s8707-s8706.json. check_invariants and load_driver sites start at `ap.parse_args` (message "faulty LLM-supplied CLI arguments", sink inside a callee, field store "previously assigned to the field"). scrub (#9,#10) and n8n_api (#11) start at `main(sys.argv)` (message "via command-line argument", a local variable / tuple unpack `_, src, dst = argv`, sink in the same function). Pair B = #1 (argparse, param in callee, Path.read_text) vs #9 (sys.argv, same function, other file): differs in source kind, file, call shape AND environment. Pair D = #10 (sys.argv, scrub) vs #7/#8 (argparse, load_driver): differs in source kind, file AND guard shape (and sink API, M2). Outcome "#9 vanished, #1 stayed -> the environment read is the cause" does not follow; the note's only hedge is for the "unexpected" row.
Better: take B inside one source family: #1 `confine_existing` (env) vs #5 or #2 with `confine_existing_fixed` (both argparse reads, Path.read_text). Use #9/#11 (sys.argv) only as a replicate: #9 helper vs #11 inline.

### Major M2: pairs D and E change the SINK API as well as the guard
Inline sites end in `open(real)` / `open(real, "w")` + `fh.write`; helper sites end in `Path.read_text` / `Path.write_text`. So in E (#1 vs #2) and D (#10 vs #7/#8) "inline vs helper" is mixed with "open() vs Path method". Sonar models these sinks separately (the base messages already differ: "injected into the caller" vs "used as argument"). Fix inside the same PR: inline sites use `Path(real).read_text(...)` / `Path(real).write_text(...)`, so only the guard differs. (#6 and #2/#5 both use open(), so F is fine.)

### Major M3: all four helper shapes share one code path; a common-mode cause makes A, B, C and the helper side of E unreadable
`confine`, `confine_iter`, `confine_existing`, `confine_existing_fixed` all go through `_text`, `_real_inside`, `_entry`, `_step`, `_parts`. `_real_inside` returns the tuple `(root, relative)`: `root` is clean, `relative` is derived from `os.path.realpath(text)`. If the engine taints a tuple as a whole (scrub flows say "previously assigned to this data structure"), `root` is tainted, `os.scandir(current)` starts from a tainted folder and every returned path is tainted, whatever the new-name branch looks like. Then #1,#4,#7,#8,#9 all "stay" and the result says nothing about dict vs iteration or env. No arm decouples this. Also the 12 sites hold only 4 helper summaries (confine is shared by #4 and #7), so #4/#7 are not independent observations.
Better design: add one variant where the root is chosen by INDEX: `i = _root_index(real, allowed)` (an int), `root = allowed[i]`, `rel = os.path.relpath(real, root)` kept as a separate local; use it at one read site (e.g. #5) next to #1.
Also the design has no positive control (a site known to clear). #6 (basename) is the only candidate; if everything stays the note's last row ("owner marks reviewed") is right, but you cannot tell "engine accepts nothing custom" from "my helper has a shared flaw".

### Major M4 (reading rule): the note does not say what to do with a NEW issue in another function or file
Note says a new issue at another line of the same function counts as not cleared. It must also say: any S8707/S8706 in `tools/pathconfine.py` (for example at `os.scandir(current)` in `_entry`, the likely place) or at an inline `open(real)` means the sink moved into the helper; count EVERY helper site as stayed even if its caller issue vanished (a caller issue that vanishes while a new one appears in `_entry` would read as "cleared" in the table). Add: query with `rules=...S8707,S8706` and read all components, not only the 12 files.

### Minor m1: the mapping has no row for mixed results inside a replicate set
E lists #2/#5/#11 as one group; "#2 vanished, #5 stayed" (same shape, other field) is not mapped. Add "replicates disagree: read the flows, treat as no result for that shape".

### Minor m2: B's "no environment read anywhere on the call path" is false in the strict sense
`fixed_roots()` calls `tempfile.gettempdir()`, which reads TMPDIR/TEMP/TMP inside the standard library. Harmless if the engine does not look inside the stdlib; say "no environment read in our code".

### Nit n1: the new test file adds issues the API filter hides
`tests/test_probe_ab.py:211` contains a literal U+202E (bidirectional override) inside a tuple of names: Sonar text:S6389 (base already has two such issues in test_followup_edge_cases.py). `tempfile.gettempdir()` at 4 places (pathconfine, check_invariants, n8n_api, scrub) is a likely S5443 security hotspot (hotspots are not in api/issues/search). Four copies of the inline guard add duplication. None can blur the S8707/S8706 reading (tests/ are not taint-scanned: the base has no S8707 in tests/); they only make the draft PR's gate red, which does not matter for a throwaway.
### Nit n2: wording
"13 issues in the file" is 13 pythonsecurity issues (38 in the file); 11 S8707 + 1 S8706 + 1 S8703 (feed, untouched). The design count of 12 is right.
### Nit n3: mutants that survive
Mine: M3 (NUL dropped from the control-character regex) and M11 (symlink-loop check off) survive; both equivalent in effect because `os.path.realpath` raises on NUL and `open` fails on a loop. A link-loop test would pin the `_step` branch. 

### Risk R1 (not proven): the Sonar workflow runs the whole test suite first
.github/workflows/sonar.yml runs `python -m pytest -q --cov` (DPLD_REQUIRE_DEMO=1) before the scan; a red test means NO Sonar run, i.e. no reading. The note did not run the full suite. I ran every test file that mentions the touched modules plus the note's list: 406 passed (probe_ab, load_tools, scrub, gitleaks_exceptions, hygiene; 0 skipped) and 492 passed (vendor_hosts, standins_body_before_answer, http, smtp_outbox, env_numbers, except_clause_hierarchy, DPLD_REQUIRE_DEMO=1); with the note's own 665 this covers all 15 files that reference the modules. The other ~80 test files do not import them (grep). Not run: the full suite as one process; the lead's run decides.

## What passed (measured)
* Fresh clone at db54e13: `git apply --check` and apply OK; 7 files, +648/-6 (matches the note). New files: tests/test_probe_ab.py, tools/pathconfine.py.
* Marking: "PROBE ONLY, DO NOT MERGE" is in tools/pathconfine.py, check_invariants.py, load_driver.py, n8n_api.py, scrub_n8n_export.py, tests/test_probe_ab.py (6 hits in the patch) and the note title; tests/test_load_tools.py has a one-line "probe:" comment only.
* Hygiene: `git add -A`, GITLEAKS_BIN=/tmp/work/gl/gitleaks (8.30.1), DPLD_REQUIRE_SCAN=1: tests/test_hygiene.py and test_gitleaks_exceptions passed. gitleaks on a copy of only the 7 changed files with the repo's .gitleaks.toml: no leaks; `gitleaks git`: no leaks (the 42 hits of `gitleaks dir .` are __pycache__/caches and base src files, not the patch). No secret-shaped literal in the patch.
* ruff check, ruff format --check (148 files) clean; mypy --platform linux and win32: no issues in 27 files; bandit -ll on src tools scripts load_tools: no issues at medium or high (the 10 High counts printed are the "nosec/test in comment" summary lines, none in findings).
* Behaviour per site (my own probes with cwd, TMPDIR and the outside folder in three separate scratch folders): all 4 helpers refuse `..`, absolute outside, link to outside file and folder, prefix sibling (`<tmp>-x/secret`), NUL, newline, ESC, C1 (U+0085), empty, spaces, 5000-char path, /etc/passwd; a new name with a space, a non-ASCII letter or U+202E is refused by the new-name helpers; `..` as new name is refused. Existing files and `.`: accepted (`.` is the cwd folder; reading it fails later with OSError, as base). Checker sites (read_crm, _facts_say_live, _intended, read_jsonl): inside OK; every outside/link/NUL/control/prefix/empty/folder case gives InputError (or False for _facts_say_live, then `_intended` refuses), no traceback. _drain_marker: NUL and `..` and empty and `/etc/passwd` (reads load_tools/passwd: not found) give InputError, an outside absolute path reads the same-named file in the fixed folder (the stated contract). scrub: src outside/NUL/missing: "refused", exit 2; dst outside, `..`, link to folder, link to file, NUL: refused, nothing written (outside folder listing checked). The only tracebacks: scrub with dst "" or a folder -> IsADirectoryError, identical to base (Path("").write_text), so not weaker.
* Dominance: at read_jsonl and _intended the helper call rebinds `path` before the only sink (`path.read_text`), in a try whose except raises, so no path reaches the sink unguarded. read_crm, _facts_say_live, n8n_api import, scrub 179: the guard raises/returns before `open(real)`; `real` is used, not the argument. load_driver.run: both confines are the first two statements, before machine_facts, before any write. scrub 178 returns before the read on refusal. Only run() uses `log` after rebinding (parts, with_name): derived from the confined path.
* 14 mutants of my own on tests/test_probe_ab.py (mut.py): startswith instead of commonpath KILLED; abspath instead of realpath KILLED; read_crm guard off KILLED; _facts_say_live guard off KILLED; scrub write guard off KILLED; n8n inline guard off KILLED; drain without basename KILLED; fixed-roots variant reading the environment KILLED; load_driver log unconfined KILLED; new name any char KILLED; allowed_roots ignoring the environment KILLED; existing-helper allowing a missing file KILLED; SURVIVED (equivalent): NUL out of the control regex, symlink check off.
* Controls: read_book (S8706 L96) and run_real_check.load_env (L645) are in no hunk; run_real_check.py is not in the patch. run_real_check imports `read_book`, `render_table`, `run_checks`, `InputError` from check_invariants and `send_with_retries` from load_driver: none of those call a probed helper; `load_env` takes `--config` (field `config`), flow lines 818-840, unrelated. Neither control is reachable from a probed helper. Both are only NEGATIVE controls (they detect "everything vanished"), not a positive one.
* Mapping check: each row follows from its premise (A, C, D, E, F rows are logically consistent) except where M1/M2/M3 break the premise "ONE difference" (B, D, E, and the "both stayed" rows of A/C).

## Pair-by-pair: is it ONE difference? (code read)
| pair | stated | what else differs | confounded |
|---|---|---|---|
| A #1/#4 | new-name branch | field (log vs facts), read_jsonl has 3 callers, shared `confine` with #7, common tuple path (M3) | mild; readable if helpers are not common-mode |
| B #1/#9 | environment | source kind (argparse vs sys.argv), file, local-var vs param/field, stdlib gettempdir | YES (M1) |
| C #7/#8 | dict vs iteration | field (log vs facts; facts also comes from a.log via `a.facts or a.log...`), same function, same sink API, same source kind | no: the cleanest pair; `confine` is shared with #4 |
| D #10/#7,#8 | inline vs helper on a write | source kind, file, sink API (open vs write_text) | YES (M1, M2) |
| E #1/#2 | inline vs helper on a read | sink API open vs read_text, field | YES (M2) |
| F #6/#2,#5 | name-only | sink API same (open); `os.path.join` | no |
Shared taint paths: #4 and #5 share `facts` (main line `a.facts or a.requests.with_name(..)`, so #4/#5 also share source a.requests with #1); all helper sites share `_real_inside`/`_entry` (M3). I found no way for one site's fix to clear another's flow except through those shared helper functions (a change there would move all five at once, which is the point of M3).

## A better design (if you can spend one more cut)
1. Keep sink API constant (Path(...).read_text / write_text everywhere).
2. Pair inside one source family and one function where possible: argparse reads: #1 `confine_existing`, #2 inline, #4 `confine` (combined), #5 `confine_existing_fixed` (env vs no env, same family as #1), #6 basename. argparse writes: #7 helper(dict), #8 helper(iter). sys.argv sites as replicates: #9 helper, #10 inline write, #11 inline read.
3. Write comparison "inline vs helper" needs an argparse inline write; only 3 write sites exist, so either run a second push (a draft PR cycle is cheap) with #7 inline and #8 helper, or accept D only as "sys.argv replicate".
4. Add one index-selected-root helper variant (M3) and say in the note that all-helpers-stay is ambiguous without it.
5. Add the M4 reading rule and the m1 row. Even without a re-cut, these two note edits (M4, m1) plus "B, D, E are confounded: read as hints, not as decisions" make the probe usable.

## Not checked
Sonar itself (nothing of it can be seen), Windows/macOS execution (mypy win32 only), the full suite as a single process, CodeQL, the effect of the PR's CI. No process of mine is left running.
Files: /tmp/work/rv19-report.md; scratch /tmp/work/rv19-1 (c/, probe/p.py, probe/q.py, mut.py, m/).
