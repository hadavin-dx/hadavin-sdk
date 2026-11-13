# PROBE-AB-V3: PROBE ONLY, DO NOT MERGE

Patch: `sonar/probe-ab-v3.patch` (7 files, +871/-5; applies on db54e13 alone, `git apply --check` on a fresh clone; also checked after sonar-p1-quickwins-v3.1 and after v3.1 + sonar-p2-regex-http-bug-v2.1: evidence-probe3-6). It replaces `probe-ab-v2.patch`, whose fresh review (rv19-report.md) said: safe to push, but pairs B, D and E were confounded. v3 implements the reviewer's better design.
Second push (a tiny change, the writes): `sonar/probe-ab-v3-writes2.patch` (a delta of 3 files on top of v3) and `sonar/probe-ab-v3-writes2-full.patch` (the same result as one patch on db54e13 alone, for convenience). See the last section.
How to push: ONE draft PR per patch (branch cut from db54e13, PR to main so every file is new code), title "MEASUREMENT ONLY, DO NOT MERGE", read the Sonar result, close the PR.
I cannot see any Sonar result. Everything below says what each outcome would MEAN, not what will happen.

## What changed from v2 (reviewer item, then the change)
| reviewer item | change in v3 |
|---|---|
| M2: sink API was mixed (`open()` at inline sites, `Path.read_text`/`write_text` at helper sites) | every read and write site now ends in `Path(...).read_text(...)` / `.write_text(...)`; the inline sites call `Path(real).read_text/write_text`. The sink API is a constant. (`_drain_marker` too: `Path(os.path.join(DRAIN_DIR, name)).read_text`.) |
| M1: pairs crossed the taint SOURCE kind (argparse vs `sys.argv`) | all pairs are inside the argparse family (`ap.parse_args`: check_invariants and load_driver). The three `sys.argv` sites (scrub 178, 179 and n8n_api 192) are REPLICATES, not pairs. |
| M3: one shared tuple path `(root, relative)` under every helper | new helper `confine_existing_ix` (below) is used at one extra site (#13) |
| no positive control | one extra function (#14, below) |
| m2 / n1: TMPDIR read through `tempfile` in the "no environment" variant; U+202E literal; four copies of `gettempdir()` | `fixed_roots()` uses the constant `FIXED_TEMP = os.path.join(os.sep, "tmp")`: no environment read in our code or in `tempfile` on that call path. U+202E is now written as an escape (`"‮"`); I checked the whole staged diff for bidirectional and other format characters: none. `tempfile.gettempdir()` is now called in 2 places (`pathconfine.allowed_roots`, and a local list in `scripts/n8n_api.py`, which cannot import `tools` when run as a script) instead of 4 |
| M4, m1, n2 | in the note: reading rules below, replicate row, wording corrected |

## What is wrong with this branch on purpose (so nobody merges it)
* `python3 load_tools/load_driver.py --help` and `python3 load_tools/check_invariants.py --help` WITHOUT `PYTHONPATH` fail with `ModuleNotFoundError: No module named 'tools'` (they work on db54e13). The helper v3 patch (sonar-p3-path-helper-v3.patch) is the place that handles this; this probe does not.
* `check_invariants.main` makes two extra calls that no finished design would have: it reads the catcher log a second time through the index helper (#13), and it calls the positive control (#14, a no-op for every typed name except two constants).
* The site shapes differ between functions of the same tool, which no finished design would do. The name-only site (#6) narrows behaviour on purpose.

## How to read the PR (match by RULE + FUNCTION NAME at the end of the message, not by line)
Lines move: every file gains 15 to 60 lines above the flagged code. API:
`https://sonarcloud.io/api/issues/search?componentKeys=hadavin-dx_duplicate-proof-lead-desk-n8n&pullRequest=<new PR>&resolved=false&rules=pythonsecurity:S8707,pythonsecurity:S8706&additionalFields=_all&ps=100`
Read ALL components in the answer, not only the 12 files. `load_driver.run` has TWO issues with the same message (base lines 366 and 377): tell them apart by the sink call (`facts_path` write / `log` write). `scrub_n8n_export.main` also has two (178 read, 179 write): the sink call.
Issue counts: `issues-pr4-0253.json` has 38 open issues; 13 of them are `pythonsecurity` issues (11 S8707, 1 S8706 at `read_book`, 1 S8703 at `scripts/feed.py:post`, which is untouched). The design uses 12 of the 13: the 10 probe sites and the 2 untouched negative controls.

### Reading rule M4 (sink moved)
An S8707 or S8706 that appears in `tools/pathconfine.py` (the likely place is `os.scandir(current)` in `_entry`, or the same call in `_ix_entry`) or at an inline `Path(real).read_text/write_text` means the SINK MOVED into the helper or to a new line. Then count EVERY site that uses that helper as STAYED, even if its own caller issue vanished: a caller issue that vanishes while a new one appears in `pathconfine.py` is not a clear. A new issue at another line of the same function counts as NOT cleared. Read the flow of every still-open issue.

## Table of the sites (A = argparse source, S = `sys.argv` source). All reads end in `Path(..).read_text`, all writes in `Path(..).write_text`.
| # | base file:function:line | rule | shape in the probe | family |
|---|---|---|---|---|
| 1 | load_tools/check_invariants.py:read_jsonl:63 | S8707 | helper `confine_existing`: must exist, no new-name branch, environment roots, internals `_text/_real_inside/_entry/_step` (returns the pair (root, relative)) | A read |
| 2 | check_invariants.py:read_crm:82 | S8707 | INLINE guard: realpath, commonpath against `allowed_roots()`, refuse, then `Path(real).read_text` | A read |
| 3 | check_invariants.py:read_book:96 | S8706 | UNTOUCHED negative control | must stay open |
| 4 | check_invariants.py:_intended:597 | S8707 | helper `confine` (existing or NEW name from a dict table, environment roots, same internals as #1) | A read |
| 5 | check_invariants.py:_facts_say_live:605 | S8707 | helper `confine_existing_fixed`: code identical to #1 except the folders come from `fixed_roots()` (no environment read anywhere). A refused path answers "live" (fail closed) | A read |
| 6 | check_invariants.py:_drain_marker:614 | S8707 | NAME-ONLY: `os.path.basename(str(path))` joined to the constant `DRAIN_DIR` | A read |
| 7 | load_tools/load_driver.py:run:366 | S8707 | helper `confine`, DICT table for a new name (the `facts_path` write) | A write |
| 8 | load_driver.py:run:377 | S8707 | helper `confine_iter`, ITERATION over a constant for a new name (the `log` write) | A write |
| 9 | tools/scrub_n8n_export.py:main:178 | S8707 | helper `confine_existing`, the same call as #1 (REPLICATE of #1 in the `sys.argv` family) | S read |
| 10 | scrub_n8n_export.py:main:179 | S8707 | INLINE guard on a write, `Path(real).write_text` (REPLICATE; its swap is the second push) | S write |
| 11 | scripts/n8n_api.py:main:192 | S8707 | INLINE guard, `Path(real).read_text` (REPLICATE of #2) | S read |
| 12 | scripts/run_real_check.py:load_env:645 | S8707 | UNTOUCHED negative control | must stay open |
| 13 | NEW: check_invariants._probe_index_read | none in base | INDEX helper `confine_existing_ix`, a second read of the catcher log (the field `catcher`, the same file as one of the three callers of #1) | A read |
| 14 | NEW: check_invariants._probe_control | none in base | POSITIVE CONTROL: the typed name is compared by equality with two constants, then used (`Path(DRAIN_DIR, name).read_text`) | A read |
Not in the probe design: `scripts/feed.py:post:49` (S8703, SSRF, not a path). Untouched.

### The index variant (#13) and what it shares with the others
`confine_existing_ix` does the same job as `confine_existing` (same checks, same refusals, same environment roots, same result for every input: test `test_index_helper_agrees_with_confine_existing_everywhere`, 17 to 21 inputs, with and without the environment). What differs: the allowed folder is chosen by an INTEGER index (`_ix_pick` returns `int`, -1 for none; `root = roots[index]`), the relative text is a separate local made with `os.path.relpath(real, roots[index])`, and NO function returns a `(root, relative)` pair.
It has its OWN internal functions `_ix_inside`, `_ix_pick`, `_ix_entry`, `_ix_step` and its own text checks inline. It shares NOTHING with the other four helpers except: `allowed_roots()` (a tuple of roots from the working folder, the repository folder, the temporary folder and `LEAD_DESK_PATH_ROOTS`; not made from the path, same roots as #1), the exception class `PathRefused`, and the constants `_CONTROL`, `MAX_PATH_CHARS`, `ROOTS_ENV`. So it does NOT share `_text`, `_real_inside`, `_inside`, `_entry`, `_step`, `_parts`, `_locate*`. One sharing I could not avoid: `allowed_roots()` itself returns a tuple (the roots), and `os.scandir`, `os.path.realpath` are the same library calls everywhere.

### The positive control (#14), honestly
Shape: `if name != "README.md" and name != "catcher.py": return None`, then `Path(DRAIN_DIR, name).read_text(...)`: an allow-list by EQUALITY against constants, the checked variable used afterwards (the textbook "fixed set" check). The function is reached from an argparse value (`main` calls it with `a.model_log`), so a tainted value can reach it.
I could NOT confirm that Sonar's public rule text names this shape as accepted: `rules.sonarsource.com` and the docs site are refused by this shell's proxy, and `api/rules/show` for pythonsecurity:S8707 returns no description text. So "known-accepted" is UNVERIFIED by me; it is the shape the lead named.
Reading: #14 absent from the issue list (no issue at its line or in `_probe_control`) with the negative controls open = the engine honours an equality allow-list, so a custom check CAN clear a flow (so a "stayed" elsewhere is about my shapes). #14 present = this engine does not honour an equality guard; it says NOTHING about function-type sanitizers (`basename`, #6), so do not conclude "the engine honours no sanitizer". Without an issue on #14 you also cannot tell "analysed and clean" from "not analysed": the negative controls #3 and #12 staying open is what shows the engine ran on this PR.

## The pairs (all inside the argparse family, all `Path.read_text` or `Path.write_text`): outcome and decision
Read "vanished / stayed" as the Sonar status of the matching issue after the push (a moved sink counts as stayed: rule M4). Controls #3 and #12 must stay open; if either vanished, distrust the whole run. Read T first: it decides how much the helper rows can say.
| pair | the ONE difference | outcome | decision for the final P3 |
|---|---|---|---|
| T: #13 vs #1 | the returned pair and the shared internals (#13: index, own functions) | #13 vanished, #1 stayed | the shared tuple/internals were the cause: rewrite the final helper in the index style (no returned pair, no shared internals) and treat every "stayed" of #1, #4, #5, #7, #8, #9 as NOT informative (they all share the tuple path); then re-run A, B, C on the index style |
| | | both vanished | the tuple is not the cause; the helper shape is accepted for reads; read A, B, C for the details |
| | | #1 vanished, #13 stayed | unexpected: read both flows (the walk with `enumerate` or the `-1` result may be what is tracked) |
| | | both stayed | no helper of this kind clears a read; go to E and F |
| A: #1 vs #4 | the new-name branch (a dict read keyed by the characters of the name) | #1 vanished, #4 stayed | the new-name branch is the problem: use `confine_existing` for every READ, writes need their own answer (C, second push) |
| | | both vanished | one combined helper is fine for reads |
| | | both stayed | see T (a shared cause is likely) |
| B: #1 vs #5 | environment roots (#1) or constant roots (#5) | #5 vanished, #1 stayed | the environment read is the cause: final roots must not read `LEAD_DESK_PATH_ROOTS` (a change the owner must accept: extra folders then need another mechanism) |
| | | both vanished | the environment is not a cause; keep `LEAD_DESK_PATH_ROOTS` |
| | | #1 vanished, #5 stayed | unexpected (the constant-roots variant should be at least as clean): read both flows; the field and the return value differ (`facts`, a bool) |
| | | both stayed | no help from B |
| C: #7 vs #8 | dict table (#7) or iteration (#8) for a new output name | #8 vanished, #7 stayed | iteration for every new output name |
| | | both vanished | either works: take the dict form (simpler) |
| | | #7 vanished, #8 stayed | dict form; iteration is not accepted |
| | | both stayed | see T; the second push (writes2) is the next measurement |
| E: #1 vs #2 | helper (#1) or inline guard (#2), both argparse reads, both environment roots, same sink API | #2 vanished, #1 stayed | inline guard for all reads |
| | | #1 vanished, #2 stayed | helper for reads |
| | | both vanished | take the simpler one |
| | | both stayed | neither shape works for reads: see F |
| F: #6 vs #1/#2 | name-only contract (basename into a fixed folder) | #6 vanished, the others stayed | only a name-only contract is accepted: the owner decides whether each tool may read and write only inside a fixed folder (a behaviour change). P3 becomes a redesign with a per-tool constant folder |
| | | #6 vanished and some others too | prefer the shape that vanished at the most sites without a contract change; name-only only for the sites that stayed |
| | | #6 stayed | the contract form is not accepted either |
| replicates disagree | #9 (helper, `sys.argv`) vs #1, or #11 (inline, `sys.argv`) vs #2, or #10 | #9 and #1 differ, or #11 and #2 differ | read the flows; treat that shape as NO RESULT (source kind matters, or the flow is merged), do not average. Replicates that agree with their argparse partner confirm the pair for both families |
| all designed sites stayed (controls open) | nothing tried works | | the owner marks the 12 as reviewed in the Sonar UI with a reason; no suppression comment. Read the flows first: a moved sink says which call the engine treats as a propagator |
| a control vanished | something else changed or Sonar merges flows | | discard the run; repeat on a branch where only that site differs |
A confound I cannot remove: sites share sources (`facts` reaches #4 and #5 and #7; `catcher` reaches #1 and #13) and Sonar's flow engine is interprocedural; a flow could be reported once for two sinks. Read the issue's flow ("previously assigned to the field ...") before trusting a pair. Pairs D (inline vs helper on a write) is NOT in this push: it needs an argparse inline write, which is the second push.

## Behaviour: never weaker than db54e13 at every site (tests per shape)
* Every site refuses `..` outside the allowed folders, an absolute path outside, a link to a file or folder outside, a prefix sibling folder, NUL, control characters, empty, and the over-long path (tests `test_all_checker_sites_inside_then_outside`, `test_links_and_prefix_sibling_...`, `test_nul_in_a_path_...`, `test_five_helpers_...`, scrub and load_driver tests). The index helper has its own prefix-sibling and folder-pick test and the 17-case equality test against `confine_existing` (also with an extra folder from the environment).
* `LEAD_DESK_PATH_ROOTS`: honoured at #1, #2, #4, #9, #10, #11, #13 and the helpers of #7 and #8; deliberately NOT at #5 (tested both ways: `test_fixed_roots_has_no_environment_and_existing_fixed_ignores_it`; `test_fixed_roots_never_ask_the_standard_library_for_the_temporary_folder` makes `tempfile.gettempdir` raise and shows `fixed_roots()` still works).
* #5 and fail closed: a facts file in a folder that only `LEAD_DESK_PATH_ROOTS` allows is now refused by `_facts_say_live` (it ignores the environment) while `_intended` accepts it. If that answered "not live", the model-required check could silently go OFF for a live run. So a refused path answers "live" (check ON, stricter, never weaker). Test `test_all_checker_sites_inside_then_outside` and the environment test. A missing facts file also answers "live", and `_intended` then ends the run with an input error, as before.
* Narrower on purpose, each noted: #6 reads only a file inside `load_tools/` and drops the folder part of what was typed; a NEW output name at #7 and #8 may only use letters, digits, `.`, `_`, `-`; #5 has no temporary folder except the constant `/tmp` (Linux CI is the target; on Windows or macOS a facts file in the system temporary folder is refused at #5 only and the run is stricter); scrub's missing input is "refused", exit 2, instead of a traceback.
* Extra reads and a no-op, noted above: `main` reads the catcher log a second time (#13) and calls #14 (reads `load_tools/README.md` or `load_tools/catcher.py` only if the typed `--model-log` is exactly that name; a read error is ignored).
* Dict table and iteration give the same result for every character of a name (`test_dict_table_and_iteration_rebuild_agree_on_every_character`, unchanged except the escape for U+202E).

## What was run (evidence-probe3-*.txt)
| rung | result |
|---|---|
| fails before: `tests/test_probe_ab.py` copied alone onto db54e13 | 9 failed BY BEHAVIOUR (the old code opens any path, crashes on NUL, ignores the roots, has no index read and no control), 8 skipped: the skipped ones test the helper functions themselves, which cannot import on db54e13 (no `tools/pathconfine.py`); they are not counted as "fails before". evidence-probe3-1 |
| affected tests after (19 files: the 15 that mention the touched modules plus gitleaks_exceptions, http_guard, codeant_hygiene, n8n_proof_result), `GITLEAKS_BIN=/tmp/work/gl/gitleaks` (8.30.1), `DPLD_REQUIRE_SCAN=1`, `DPLD_REQUIRE_DEMO=1`, new files `git add -A`-ed first | First run: 1185 passed, 1 skipped, 1 FAILED: `test_hygiene` found two literal-looking strings in my new test file (a docstring word list `A/B/C` and a `/etc/passwd` string). I fixed both in the test file only (no probe code). Second run on the final tree in a fresh clone: 1185 passed, 1 skipped, 1 FAILED: `gitleaks git` (the history scan) reported a finding. Cause: my scratch clone held two `git stash` commits from an earlier apply-check (a history scan reads every ref); I deleted the stashes, checked the tree is identical to the one I cut the patch from (`diff -r`: no difference), and re-ran hygiene, gitleaks_exceptions, codeant_hygiene and probe_ab: 83 passed. So NO single process of the 19 files is green; the evidence is two runs plus a re-run of the failing files. The one skip is `test_n8n_api_url.py:510` (root can read a file without permission). evidence-probe3-2 |
| ruff check, ruff format --check, mypy linux and win32 (27 files), bandit -ll -r src tools scripts load_tools | clean (bandit rc 0, no issue). evidence-probe3-3 |
| 26 hand-made mutants of the probe code against `tests/test_probe_ab.py` | evidence-probe3-4: 24 killed; 2 survive, both equivalent: `scrub: write uses dst not real` (the same text is opened; only Sonar's flow differs) and `NUL not a control character` (`os.path.realpath` raises on NUL anyway, as the reviewer found). The reviewer's survivor "symlink check off" is killed now (a link-loop test pins both `_step` and `_ix_step`) |
| `git apply --check` on a fresh clone at db54e13, and after P1v3.1 and P2v2.1 | evidence-probe3-6 |
Not run: the full suite as one process, Sonar, CodeQL, Windows or macOS, `--help` without `PYTHONPATH` (stated above), a fresh independent review of v3 (the lead runs the review step; I did not review my own work).
Other patches touched: P3 (`sonar-p3-path-helper-v2/v3.patch`) edits the same functions and the same new file `tools/pathconfine.py` (different content): never apply both; the probe is thrown away after the measurement. P1 and P2: no conflict (measured, evidence-probe3-6).
Preamble rules used: 5, 6, 7, 8 (venv from the existing fresh-venv5, no uv `test` group), 12, 13 (the EGM review of the result is the lead's step), 19, 20.

## The second push: `probe-ab-v3-writes2.patch` (pair D, the writes)
Why: v3 has only two argparse writes (#7, #8, both helpers) and one inline write on `sys.argv` (#10). The inline-vs-helper question on a WRITE needs an argparse inline write. Writes2 changes three write sites and nothing else (3 files: `load_tools/load_driver.py`, `tools/scrub_n8n_export.py`, `tests/test_probe_ab.py`; +39/-18):
| site | v3 | writes2 |
|---|---|---|
| #7 `load_driver.run` `facts_path` write | helper `confine` (dict table) | INLINE guard (realpath, commonpath against `allowed_roots()`, refuse with a `ValueError("... outside ...")`, then `Path(real_facts).write_text`) |
| #8 `load_driver.run` `log` write | helper `confine_iter` | UNCHANGED: helper `confine_iter` |
| #10 `scrub_n8n_export.main` write (S) | INLINE guard, `Path(real).write_text` | helper `confine`, `out_path.write_text` |
So in the same function, one argparse write is inline (#7) and the other a helper (#8): pair D inside one source family, same sink API, same function. And #10 is the same site, same source, same file with the shape swapped, so the two pushes compare it with itself.
Apply: the delta applies on v3 (checked); the `-full` patch applies on db54e13 alone (checked). Push it as its own draft PR (not on top of the first one if you want clean line numbers; the full patch is for that).
Reading (all outcomes read against the v3 result; rule M4 applies; controls #3, #12 must stay open):
| outcome | decision |
|---|---|
| #7 (inline) vanished, #8 (helper) stayed | inline guard for writes (3 write sites); helper for reads only if E/T say so |
| #8 (helper) vanished, #7 (inline) stayed | helper for writes (this also contradicts v3 only if #8 stayed there: compare) |
| both vanished | the simpler (inline) or one helper for all |
| both stayed | no shape tried clears a write: next candidate is the name-only contract on writes (F), or the owner marks them reviewed in the Sonar UI (no code comment) |
| #10 helper (writes2) vs #10 inline (v3) differ | same site, same source: this is the cleanest comparison in the whole probe; trust it over cross-site pairs. If #7 and #10 agree (both inline vanished or both stayed), the source kind (argparse vs `sys.argv`) does not matter for inline writes |
| #8 changed between v3 and writes2 while nothing about it was changed | the flow is shared with #7 (the same function, the same helper family): read the flows; treat as no result for C |
Tests of the second push: `test_writes2_inline_facts_write_and_helper_scrub_write` (outside, `..` and NUL are refused before anything is written; the helper's new-name rule; the environment root works for both); the other tests of the file pass unchanged (272 passed with `test_scrub_n8n_export.py`).
