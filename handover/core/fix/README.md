# Core fix patches: what each one fixes and whether it applies (freeze README, DRAFT until the final evidence and review are in)

Written by the core lead session, 2026-11-13. All numbers marked "builder" were claimed by the agent that built the patch; numbers marked "runner" were measured by a separate agent. Nothing here is applied to any repository; nothing is pushed to the public demo repo. Made-up data only, no live service, no spend.

## What the patches fix (one problem class)
Scripts and readers in the demo (hadavin-dx/duplicate-proof-lead-desk-n8n) showed a Python traceback, echoed a typed value, hung on a named pipe, or read a huge file when given bad input (a bad number, a control character, a folder that cannot be made, a pipe or a 100 MB file where a small key file belongs). The patches give one short refusal line with a fixed exit code and no typed text, and add tests that fail on the old code.

## Which file to use
| File | What it is | Applies to | Status |
|---|---|---|---|
| `core-fix-on-frozen.patch` | the public-bound hardening, rebased by hand onto the frozen demo tree 49d3c859 (3698 lines, 49 files) | frozen 49d3c859 | applies (builder and runner, see EVIDENCE below). Not the whole of v2: see "Open" 1 and 2 |
| `docs-on-frozen-49d3c859.patch` | doc fixes plus `tests/test_docs_match_tools.py` (14 tests) | frozen 49d3c859 | applies; runner re-ran it: 14 passed, 10 fail on old docs |
| `core-fix-v2.patch` (v1 + F7) | the full fix on the OLD base (demo main 61ded9e + real-run patches) | handover chain only | applies there; not for the frozen tree |
| `f8-on-v2.patch` | review round 1 fixes (listen-port, scenario numbers, pipes at read sites, crash hooks) on the v2 base | handover chain only | complete on its own base (builder: 2220 passed, 6 skipped) |
| `f8-on-frozen.patch` | the same on the frozen rebase | frozen + core-fix-on-frozen | **INCOMPLETE**: 3 tests fail, no fail-before run (builder ran out of time) |
| `ontop-3files.patch` | the 3 files that exist only in the real-run patches | frozen + real-run chain | `git apply --check` exit 0 on that chain (builder) |
| `F1..F7`, `core-fix-v1`, `docs-F4-...` | the building blocks of the above, kept for history | | superseded |

## Open (stated plainly, none hidden)
1. core-fix-on-frozen is smaller than v2: `run_live_check.py` and `run_real_check.py` are ported without the flags the frozen tree lacks (`--assume-yes`, terminal guard, precheck, range limits); 2 control tests and 1 precheck test were dropped (REB-HUNKS.md).
2. COLLISION: the real-run patches applied AFTER core-fix-on-frozen conflict in `scripts/run_live_check.py`, `scripts/run_real_check.py` and `src/lead_desk/live_claude.py` (`_read_key`). No reconciling patch (lead order 15:16Z). The next step if wanted: take the v2-based text for those three files (REB-DEPENDS.md).
3. f8-on-frozen.patch: 3 failing tests (`test_every_reader_refuses_a_pipe_at_once[run_real_check._ca_context]`, `test_the_model_stand_in_refuses_a_pipe_or_a_bad_file_as_key_file`, `test_the_scrub_tool_writes_through_the_checked_helper`), cause not looked at. Next step: one fixer on the copy `/home/user/build/rr6/out/F8/reb/t` (not run: freeze order).
4. Five doc sentences have no test (OPEN TEST GAPS, lead answer 14:54Z): README "the replay uses up a receipt number"; `settings.md` HubSpot key file "not at start"; `settings.md` SMTP password file "opened again for every send"; `load_tools/README.md` port 18765; `load_tools/README.md` `seq 1 60`. Reason: the docs test pins counts and names, not these sentences; a test-only change of about 20 minutes closes them.
5. F8 side facts: one allow-list line added to `exceptions.txt` (owner accepts or rejects); `crash_desk` makes the book folder before printing the flag path; an empty `data/` folder appears in full runs (source not found); `DESK_FAKES_HOST/PORT` probe unexplained; `scripts/n8n_api.py` exits 1 for every refusal (owner decision).
6. Not tested: Windows (`.ps1` wrappers are text-tested only), macOS, Python 3.13 for most tests, the 5-second wait in `contract.md:323` (read from code, not run end to end). Earlier unexplained runs: baseline first-run rc=1 (UNKNOWN) and T2 failure (UNEXPLAINED).
7. The reviewer on core-fix-v2 was a general-purpose agent reading the persona file (the `egm:*` agent types are not registered here), labelled FALLBACK.

## Final head evidence and review
FINAL_EVIDENCE_AND_REVIEW
