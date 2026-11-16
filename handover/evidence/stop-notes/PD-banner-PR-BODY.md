## Mode banner and demo-only folder guard

promoted from the public demo repo duplicate-proof-lead-desk-n8n at 43110e7

Part 6 of the demo promotion, batch 2 (round 1 review fixes on head dd5c7242). Core had no code for either part: the demo-only folder rule existed only as prose, and core has no web page, so there was no place for a mode banner.

### LEAD DECIDES BEFORE MERGE: signature change (decided yes, 2026-11-12 20:30Z / 02:00 IST, lead answer in `handover/LEAD-ORDERS.md`)
`banner_from_config(config, names=None)` is now the ONLY public way to build a banner. The earlier public names `banner_for` and `stand_ins_in` are private (`_banner_for`, `_services_in`), and a test fails if they reappear as public. Reason: with a list passed by hand, a caller could leave out a real service and the screen would say "made up". Nobody outside this branch uses the old names (Part 3 consumers use `stages.py` and `backends/table.py`, whose public names are unchanged).

### What this adds, in plain words
1. **Mode banner.** The one line at the top of a screen that says what the system is connected to.
   - `src/hadavin_sdk/mode_banner.py`: the stage and the services are read from the config, in one place. Every kind in the config is put in exactly one of three groups: stand-ins (kinds in `backends.table.DEMO_ONLY`), connects-nothing kinds (signer none, anchor none, detector regex: not listed, they reach nothing), and real (everything else, so an unknown kind is named, never hidden). In the demo stage with nothing real it says the data is made up and lists the stand-ins. With any real service it names it and never says "made up". A banner is always shown.
   - It refuses an unknown stage, a bare string where a list is wanted, a name that is not plain words, and a banner longer than the page accepts.
   - `templates/mode-banner/mode_banner.js` (framework-free, text only) paints the finished banner and fails closed: it checks the banner is consistent (stage, tone, lists), builds the lines before it fills the page, never throws, and on anything odd paints "The mode of this system could not be confirmed. Treat everything here as real." `mode_banner.css` is an optional look.
2. **Demo-only folder guard.** `tools/demo_only_guard.py`, settings in `tools/demo_only_guard.toml`. It reads every path from `git ls-files` (plus files not yet added), reports every symlink under a product folder and any link elsewhere that points into the folder, matches the folder name in any case and separator ("Demo_Only", "demo-only", "demo only"), reads every file type except a listed set of binary endings (anything else that is not text is refused), scans four product roots (src, templates, tools, demos), caps loader files, and keeps a short stale-checked list of allowed phrases. The copy run proves that deleting the folder keeps the build: it copies the repository without the folder, imports the product package from that copy, and runs the guard and the tests there.
3. **CI.** The main job runs the guard, the copy run, a node version check and the banner mutants as blocking steps.

### Answers to the questions in the brief
- Does `tools/scan_repo.py` cover the new files? Yes for secrets and banned names (all tracked, non-binary files). It does not check the demo-only rule; the guard does.
- Is there a demo-stage constant? No public one in `stages.py`. `mode_banner.py` holds a private `_DEMO_STAGE`, checked against `STAGES` at import.
- Is `templates/` packaged? No: the build packages only `src/hadavin_sdk`. That is why the page script is a template to copy, not an import.
- Python 3.12 is not available here (3.13.18 is); the 3.12 CI job was not run.

### Rung table (tool ladder / code-last)
| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Mode banner words and choice | say demo / real / stand-in truthfully | 2/4: exists in the public demo (browser-side words in `portal.js`) | promoted from the public demo repo duplicate-proof-lead-desk-n8n at 43110e7 (read 2026-11-12) | the rule "made-up only when demo and nothing real", stage names from core | KEEP-CODE (a safety claim), generalised, words moved to Python so a screen only paints |
| Page painter | show the banner | 2: demo `paintBanner/modeSeen`; no library needed | same | never hidden, text only | CUT-TO-CONFIG+GLUE: about 45 lines, optional template |
| Folder guard script | keep demo data out of product code | 2: demo `test_hygiene` + CI step; no ready-made tool found that knows the rule | same | the exact rule and fake-id check | KEEP-CODE (small), config-driven |
| Copy-without-folder run | prove deleting the folder keeps the build | 2: demo `test_demo_folder_guard.py` | same | none beyond the copy | CUT-TO-CONFIG+GLUE |


### Demo names removed
`lead_desk`, `DPLD_REQUIRE_DEMO`, `DPLD_REQUIRE_SCAN`, `DPLD_` prefix, `REAL_NAMES` (crm / mail / ai step), `lead-desk-demo-line`, `demo-line`, `offline-banner`, HubSpot, n8n, "desk" wording, `loader.py` of the demo, `portal_probe.js` (rewritten as `tests/mode_banner_probe.js`). Service names now come from the caller. The old first stage name is not used; stage names are demo, pilot, prod.


### Tests that fail on the old code (dd5c7242)
Run with the new test files and the old `src`, `tools` and `templates`: 81 failed, 13 passed. Log: `/home/user/build/B-PD-banner-b2-failbefore.log`.
- The 13 that pass are controls (they pin behaviour that was already right): `test_no_new_module_keeps_its_own_loopback_list`, `test_the_page_fallback_has_the_same_words_as_the_python_fallback`, `test_markup_in_the_text_is_shown_as_text_never_parsed`, `test_the_page_script_has_no_way_to_parse_html_or_load_anything`, `test_the_folder_name_is_in_the_settings_file_only`, five of the bad-settings cases, `test_a_folder_name_that_is_a_path_stops_the_guard`, `test_the_script_runs_as_a_program_on_this_repository`, `test_ci_runs_the_scan_in_the_main_check_job_with_read_only_permissions`.
- Everything else fails on the old code, including the symlink, folder-coverage, spelling, binary-file, copy-run and "old public names are gone" tests.

### Mutants (`python tests/banner_mutants.py`, 98: 37 banner, 22 page script, 39 guard; 98 of 98 good at 482f7dcc)
Each new rule has at least one. Reason for none: the order "build the lines before clearing the page" cannot be seen from outside because the fallback overwrites the element. Touched rows re-run after the last edit: 13 of 13 good (first run) and 4 of 4 good after re-pinning the expected text.

### Round 3 (head 482f7dcc)
- Demo sentence "Nothing here is sent to real customers or real systems" is now checked against every config field that can name an endpoint, not only the backends: a `systems` base_url, an `egress_hosts` entry or a `sources` endpoint that is not this machine counts as one real service each. A claim post-condition refuses a banner that omits a real name or holds the made-up sentences when it should not.
- Guard: submodule under a product root is a hit; a binary ending is skipped only when the file really is binary (NUL in first 8192 bytes or not valid text); listed phrases are exact-case and not beside a dash. Page script: frozen exports and fallback, whole-word name match, element unhidden first in the last-resort write.
- New tests that fail on the old code (17d7ec3c): 19 failed, 104 passed in the two test files (the 104 include controls); mutants: 19 new rows.
- Gates at the final head: full pytest 10211 passed, 458 skipped, 0 failed (own UTF-8 Postgres 16); stage mutants 37 of 37; banner mutants 98 of 98; ruff, bandit, scan_repo, gitleaks exit 0.
- Limits kept: duplicate YAML keys in workflows are not flagged by the new test; PyYAML reads YAML 1.1, GitHub reads its own dialect; the guard still skips files git ignores and the packaging files at the repository root.

### Round 4 batch (round 3 review; head a16b7635 on top of 482f7dcc)
- Demo sentence: `banner_from_config` now REQUIRES a keyword `tool_specs` (no default; a missing one is a `TypeError`). A tool manifest host that is not this machine adds `tool-hosts`; `tool_specs=None` with a configured tool module adds `tool-modules`. The sentence now reads "Nothing here is set up to send data to real customers or real systems." The false premise "a tool module reaches only those systems" is removed. Limit stated: tool code runs in the process, is reviewed and not sandboxed, so the banner counts what manifests name.
- Page script: writes the plain words before it clears the element, so a failed write keeps the old text; the fallback always holds text (tested and mutant J15, J16).
- Guard: NFKC on lines and path parts; compiled or packed files (.pyc .so .zip .whl) refused; other binaries byte-searched in UTF-8, UTF-16LE, UTF-16BE; UTF-16 text without a byte-order mark found; a submodule with a missing folder is a hit; an exempt submodule gives only the stale entry; each file read once.
- Parser parity: urls read like the tool client (backslash, white space, control, non-ASCII, `%`, `@` count as leaving); shared `guard.http.LOOPBACK` and `normalise_host`; new public `sources.kinds.source_endpoint` (the app uses it too); one whole-word name rule in Python and JS with a parity table; empty claim sentence raises; a config missing an endpoint field raises; real-Config tests for egress hosts and sources.
- Limits kept: "this machine" means only localhost, 127.0.0.1 and ::1 (other 127.x addresses count as outside); the banner is worked out when called, so a page that cached an older banner keeps it; tests/test_workflow_files_parse.py is a new file in this branch (no line-wrap change in this round).
- Old-code proof: new tests against 482f7dcc src/tools/templates: 41 failed, 93 passed (some failures only from the new signature; the exempt-submodule and page non-empty-text tests pass on old code and are pins). Log: evidence-raw/b4/b4-oldcode.txt.
- Mutants: 130 rows (98 before plus 32 new: B30-B47, J15-J18, G30-G39 and re-pointed rows); full run at a16b7635: 130 of 130 good, exit 0, git status clean.
- Gates at a16b7635: full pytest `-m "not live and not perf"` 10208 passed, 457 skipped, 28 deselected, exit 0 (own UTF-8 Postgres 16; the postgres-service tests skip without HADAVIN_TEST_PG_DSN); stage mutants 37 of 37; ruff check and format, bandit -ll, scan_repo, demo_only_guard, gitleaks origin/main..HEAD all exit 0. The perf test test_the_timing_harness_flags_a_quadratic_stand_in is a known load-dependent failure of main when perf is not excluded; CI excludes perf.

### Gates
- `ruff check` and `ruff format --check` on src tests demos tools: pass. Targeted tests (banner and guard files, `HADAVIN_REQUIRE_NODE=1`): 94 passed. `bandit -ll` (run through uvx): exit 0. `tools/scan_repo.py`: exit 0.
- GATE OWED to the session gate runner (not run here, order 262): `HADAVIN_REQUIRE_NODE=1 ../heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs`; `python tests/stage_mutants.py`; `python tests/banner_mutants.py` (full run on the final head). The earlier full pytest on 431ac906 (10115 passed) is out of date for this head.
- Not run: gitleaks (not installed here), CodeQL, SonarCloud, CodeRabbit, the 3.12 job, postgres and vault service tests.

### Not checked / limits
- Not run in a real browser: the page script is tested in node with a tiny stand-in page. No screenshots (no UI product is added).
- The `loaders` and `fake_id_patterns` lists are empty in core; the guard is exercised on made-up trees. A demo repository fills them.
- The branch has diverged from origin/main (3 commits against 1); not rebased here.

Co-Authored-By and session lines are on the commits.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac
