# PROBE-AB-V2: PROBE ONLY, DO NOT MERGE

Patch: `sonar/probe-ab-v2.patch` (7 files, +648/-6; applies on db54e13 alone, `git apply --check` on a fresh clone; also checked after sonar-p1-quickwins-v3 and after v3 + sonar-p2-regex-http-bug-v2: evidence-probe2-6). It replaces `probe-ab.patch` (v1), whose design the fresh review (rv13-report.md) found unreadable. Push ONE draft PR (branch cut from db54e13, PR to main, so every file is new code), title it "MEASUREMENT ONLY, DO NOT MERGE", read the Sonar result, close the PR.
I cannot see any Sonar result. Everything below says what each outcome would MEAN, not what will happen.

## What is wrong with this branch on purpose (so nobody merges it)
* `python3 load_tools/load_driver.py --help` and `python3 load_tools/check_invariants.py --help` WITHOUT `PYTHONPATH` fail here with `ModuleNotFoundError: No module named 'tools'` (they work on db54e13); measured in evidence-probe2-4. The helper v2 (sonar-p3-path-helper-v2.patch) has the sys.path guard; this probe does not.
* It confines files but does not carry the documented-real-run changes of v2 (`run_real_check --config` outside the repository, `read_book`, ...).
* The name-only site (`_drain_marker`) narrows behaviour on purpose: it reads only a file in the `load_tools` folder.
* The site shapes differ between functions of the same tool, which no finished design would do.

## How to read the PR (match by RULE + FUNCTION NAME at the end of the message, not by line)
Lines move: every file gains 15 to 60 lines above the flagged code. API:
`https://sonarcloud.io/api/issues/search?componentKeys=hadavin-dx_duplicate-proof-lead-desk-n8n&pullRequest=<new PR>&resolved=false&rules=pythonsecurity:S8707,pythonsecurity:S8706&additionalFields=_all&ps=100`
`load_driver.run` has TWO issues with the same message (base lines 366 and 377): tell them apart by the sink line (366: `facts_path.write_text`, 377: `log.write_text`; in the probe the call that writes `facts_path` / `log`). `scrub_n8n_export.main` also has two (178 read, 179 write): the sink call (`read_text` / the write).
A new issue at another line of the same function (the sink moved to the guard) counts as NOT cleared; read the flow of every still-open issue.

## Table of every flagged site (issues-pr4-0253.json, 13 issues in the file; 12 are S8707/S8706 and are in the probe design)
| # | base file:function:line | rule | shape in the probe | the ONE difference from its pair |
|---|---|---|---|---|
| 1 | load_tools/check_invariants.py:read_jsonl:63 | S8707 | SPLIT helper `confine_existing` (reads; file must exist; NO new-name branch; allowed folders include `LEAD_DESK_PATH_ROOTS`) | pair A: vs #4 (the same reader helper with a new-name branch). Pair B: vs #9 (environment roots) |
| 2 | check_invariants.py:read_crm:82 | S8707 | INLINE guard (realpath + commonpath + refuse + `open(real)`), a read | pair E: vs #1 (inline vs helper, both reads, both environment roots) |
| 3 | check_invariants.py:read_book:96 | S8706 | UNTOUCHED control | must stay open |
| 4 | check_invariants.py:_intended:597 | S8707 | COMBINED helper `confine` (existing or new name; new name from a dict table; environment roots), a read | pair A: vs #1: same reads, same roots; the helper also has the new-name branch |
| 5 | check_invariants.py:_facts_say_live:605 | S8707 | INLINE guard, a read (refused path answers "not live") | duplicate of #2 (same shape, other field `facts`); #4 takes the same field with the helper |
| 6 | check_invariants.py:_drain_marker:614 | S8707 | NAME-ONLY contract: `os.path.basename(path)` joined onto the constant folder `DRAIN_DIR`, a read | pair F: vs #2/#5 (name-only vs inline guard, all reads, same function family) |
| 7 | load_tools/load_driver.py:run:366 | S8707 | helper `confine`, DICT table for a new name (the `facts_path` write) | pair C: vs #8 |
| 8 | load_driver.py:run:377 | S8707 | helper `confine_iter`, ITERATION for a new name (`"".join(next((k for k in ALPHABET if k == c), "") ...)`: the output is an element of a constant, the argument character only sits in a comparison) (the `log` write) | pair C: vs #7: same function, same helper, the table is the only change |
| 9 | tools/scrub_n8n_export.py:main:178 | S8707 | SPLIT-FIXED helper `confine_existing_fixed` (as #1, allowed folders WITHOUT any environment read anywhere on its call path), a read | pair B: vs #1: environment or not |
| 10 | tools/scrub_n8n_export.py:main:179 | S8707 | INLINE guard on a WRITE (`open(real, "w")`) | pair D: vs #7/#8 (inline vs helper on writes) |
| 11 | scripts/n8n_api.py:main:192 | S8707 | INLINE guard, a read (the import FILE) | duplicate of #2/#5 (different tool, a third reader) |
| 12 | scripts/run_real_check.py:load_env:645 | S8707 | UNTOUCHED control | must stay open |
Not in the probe design: `scripts/feed.py:post:49` (S8703, SSRF, not a path; P2 handles it). It stays untouched as well.

Deviations from the brief, with the reason: (a) the inline guard on a write is at scrub 179, not at load_driver 366/377: those two are needed as the dict-vs-iteration pair and a third shape in the same function would break it (all three flagged writes are 179, 366, 377). (b) the name-only contract is at `_drain_marker`, not at n8n_api: the helper's fixed folder would break five existing n8n_api tests that import a file from a temporary folder through a subprocess; `_drain_marker` has one in-process test, which I changed by one line (tests/test_load_tools.py monkeypatches `DRAIN_DIR`).

## The pairs: what an outcome means and what it decides for the final P3 (12 sites)
Read "vanished / stayed" as the Sonar status of the matching issue after the push (a changed sink counts as stayed). Controls #3 and #12 must stay open; if either vanished, distrust the whole run.
| pair | question | outcome | decision for the final P3 |
|---|---|---|---|
| A: #1 vs #4 | does the new-name branch (the dict read keyed by the argument's characters, in one return value) spoil the helper's reads? | #1 vanished, #4 stayed | the new-name branch is the problem: roll out `confine_existing` (no new-name branch) for every READ; writes need their own answer (pairs C, D) |
| | | both vanished | one combined helper is fine for reads; use the simplest (pair C decides how a new name is built) |
| | | both stayed | see pair B: if #9 vanished the environment is the cause, otherwise the listing-based helper is not accepted for reads |
| B: #1 vs #9 | does reading `LEAD_DESK_PATH_ROOTS` make the helper's result tainted? | #9 vanished, #1 stayed | the environment read is the cause: roll out with roots that do NOT read the environment (extra folders then need another mechanism, for example a file in the repository or an argument of the tool; a change the owner must accept) |
| | | both vanished | the environment is not a cause; keep `LEAD_DESK_PATH_ROOTS` |
| | | #1 vanished, #9 stayed | unexpected (the fixed variant should be at least as clean): read both flows, probably the cross-file difference (scrub) rather than the environment |
| | | both stayed | no help from B |
| C: #7 vs #8 | dict table or iteration for a new output name | #8 vanished, #7 stayed | use iteration for every new output name |
| | | both vanished | either works: take the dict form (simpler) or iteration, equal |
| | | #7 vanished, #8 stayed | dict form; iteration is not accepted |
| | | both stayed | listing-based helper does not clear WRITES; see D |
| D: #10 vs #7/#8 | inline guard or helper on a WRITE | #10 vanished, #7/#8 stayed | inline guard for writes (3 write sites), helper for reads if A/E say so |
| | | #10 stayed, #7 or #8 vanished | helper for writes |
| | | both vanished | take the simpler (inline), or one helper for all |
| | | both stayed | no shape tried clears a write: next candidate is the name-only contract on writes (see F), or the owner marks them reviewed in the Sonar UI (no code comment) |
| E: #1 vs #2 (and #5, #11) | inline guard or helper on a READ | #2/#5/#11 vanished, #1 stayed | inline guard for all reads |
| | | #1 vanished, #2/#5/#11 stayed | helper for reads (A/B say which one) |
| | | both vanished | take the simpler one; keep v2 if equal |
| | | both stayed | neither shape works for reads: see F |
| F: #6 vs #2/#5, #1 | name-only contract (basename into one fixed folder) | #6 vanished, #1/#2/#5/#9 stayed | only a name-only contract is accepted: the owner decides whether each tool may read and write only inside a fixed folder (a behaviour change: operators could no longer name a file elsewhere). Then P3 is a redesign with a per-tool constant folder |
| | | #6 vanished and some of the others vanished too | prefer the shape that vanished at the most sites without a contract change; name-only is the fallback only for the sites that stayed |
| | | #6 stayed | the contract form is not accepted either |
| all 10 designed sites stayed (controls open) | nothing tried works | the owner marks the 12 as reviewed in the Sonar UI with a reason; no suppression comment. Read the flows first: a moved sink says which call the engine treats as a propagator |
| a control vanished | something else changed or Sonar merges flows | discard the run; repeat on a branch where only that site differs |
A confound I cannot remove: the sites share sources (for example `facts` reaches #4 and #5) and Sonar's flow engine is interprocedural; a flow could be reported once for two sinks. The probe avoids this by giving each pair a different field wherever it can; read the issue's flow ("previously assigned to the field ...") before trusting a pair.

## Behaviour: never weaker than db54e13 at every site (tests per shape)
* Every site refuses `..` outside the allowed folders, an absolute path outside, a link to a file or folder outside, a sibling folder whose name starts like an allowed one (a prefix sibling): tests `test_all_checker_sites_inside_then_outside`, `test_links_and_prefix_sibling_...`, scrub and load_driver tests. The prefix check also has a direct test of `_inside`.
* NUL in a path (the reviewer's P-3): the inline sites no longer crash. `read_crm`: InputError; `_facts_say_live`: False; the n8n_api import ends in its existing "cannot read a workflow" message; scrub: "refused", exit 2; the helper sites refuse (control character). Test `test_nul_in_a_path_is_a_clean_refusal_never_a_traceback`. (On db54e13 `read_jsonl` already crashes on NUL with a traceback; the probe is better there.)
* `LEAD_DESK_PATH_ROOTS` at the inline sites (the reviewer's P-5, mutant P12): `read_crm`, `_facts_say_live`, scrub 179 and n8n_api honour it, tested with the real roots function (nothing monkeypatched); the helper sites #1 and #4 honour it; the fixed-roots site #9 deliberately does NOT (tested both ways). Mutants M2, M3, M4 kill an ignored or an added environment.
* Narrower on purpose, each noted: #9 a missing input file is "refused" (exit 2) instead of a traceback; #9 ignores `LEAD_DESK_PATH_ROOTS`; #6 reads only a file inside `load_tools/` and drops the folder part of what was typed (test: typing an outside path reads the file of that name in the folder; `..`, an empty name and an outside-only name are refused); a NEW output name at #7 and #8 may only use letters, digits, `.`, `_`, `-` (an existing file may have any name).
* Dict table and iteration give the same result for every character of a name (test `test_dict_table_and_iteration_rebuild_agree_on_every_character`).

## What was run (evidence-probe2-*.txt)
| rung | result |
|---|---|
| tests on the OLD code (fails before): `tests/test_probe_ab.py` copied alone onto db54e13 | 8 failed BY BEHAVIOUR (the old code opens any path, crashes on NUL, ignores the roots), 5 skipped. The 5 skipped are the tests of the helper functions themselves: db54e13 has no `tools/pathconfine.py`, so they cannot even import there; they are not counted as "fails before". evidence-probe2-1 |
| affected tests after: test_probe_ab, test_load_tools, test_hygiene, test_gitleaks_exceptions, test_n8n_api_url, test_scrub_n8n_export, test_real_check_dry, test_burst_retry, test_clock_steps, test_infra, with `GITLEAKS_BIN=/tmp/work/gl/gitleaks` (8.30.1), `DPLD_REQUIRE_SCAN=1`, new files `git add -A`-ed first | 665 passed, 1 skipped; 421 s. evidence-probe2-2 |
| ruff check, ruff format --check, mypy linux and win32 (27 files), bandit -ll -r src tools scripts | all clean (bandit rc 0, no medium/high issue). evidence-probe2-3 |
| 10 hand-made mutants of the probe code, run against `tests/test_probe_ab.py` | 8 killed. 2 survive, both equivalent by design: M9 (`..` allowed in the name-only site: opening a folder fails with an OSError, so behaviour is the same) and M10 (the write opens the argument text instead of `real`: same behaviour, only Sonar's flow differs). evidence-probe2-4 |
| `--help` without PYTHONPATH | probe fails with ModuleNotFoundError, base works (stated above). evidence-probe2-4 |
| `git apply --check` on a fresh clone at db54e13, and after P1v3 and P2v2 | applies in all three. evidence-probe2-6 |
Not run: the full suite, Sonar, CodeQL, Windows or macOS, the other test files, a fresh independent review of v2 of this probe (the lead runs the review step; I did not review my own work). The one skip is not in test_probe_ab, test_load_tools, test_hygiene, test_gitleaks_exceptions or test_scrub_n8n_export (re-run with `-rs`: 406 passed, 0 skipped, so the gitleaks tests really ran); it is in one of the other five files and I did not look up which.
Other patches touched: P3 v2 (sonar-p3-path-helper-v2.patch) edits the same functions and the same new file `tools/pathconfine.py` (different content): never apply both; the probe is thrown away after the measurement. P1 and P2: no conflict (measured).
Preamble rules used: 5, 6, 7, 8 (venv from the existing fresh-venv, no uv `test` group), 12, 13 (EGM review of the result is the lead's step), 20, 19.
