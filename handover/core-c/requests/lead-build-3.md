# core-c -> core-a (via lead): heavy runs for core-a's idle box (13:11Z); base = origin/cloud/core-c head c6a42ce74 (G8, G10, E14, G9 and G4 Phases 0-3 are MERGED there; wip/cloud-core-c/g4 and g9 are the builders' heads, now subsets of the head)

Frozen on the cloud box (SIGSTOP, resumable): the G11 drafter's whole-suite pytest (pids 28435 tree and the earlier 10068 tree), the G12 builder's perf run (pid 3842/3845). Kept: ONE heavy run (the M3 builder's textnorm deadline mutant run).

Setup on core-a's box:
  git fetch origin && git worktree add /tmp/ca-c-run origin/cloud/core-c -d && cd /tmp/ca-c-run && uv sync --all-extras --group test
Write results to handover/core-a/evidence/c-run-<n>.md on your branch (exact command, sha, load average at start/end, last 5 lines of output, every failure id + first error line).

RUN 1 (whole suite, no perf):  uv run --all-extras --group test pytest -q -n 3 --no-header -p no:cacheprovider -m "not perf and not live"
  Expected at the builders' Phase 3 head (wip/cloud-core-c/g4, no G9): 15236 passed, 1 failed (tests/test_no_reference_material.py, fails at the base too), 561 skipped, 15 xfailed. Expected at the current head (c6a42ce74) with G9 + E14: the same plus the G9/E14 tests, plus 3 KNOWN failures being fixed by builder a40ba60b (TB-2.8 map 1 in tests/test_b64_scan.py::test_tie_break_keeps_the_order_of_different_originals, TB-2.11 tests/test_runmap_enforce_map.py::test_e5b_..., TB-3.4 tests/test_b64_scan.py::test_no_run_no_extra_work): E20 in handover/core-c/ESCALATIONS.md. Report any other failure.
RUN 2 (perf only, on an IDLE box, one process): uv run --all-extras --group test pytest -q -n 0 -m perf -p no:cacheprovider --durations=15 tests/test_redact_fold_budget.py tests/test_k5_perf.py tests/test_textnorm_perf.py tests/test_textnorm_round2.py tests/test_redact_finder_cap.py tests/test_redact_settle_loop.py tests/test_runmap_enforce_map.py tests/test_model_gate.py
  Expected: all pass; tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse passes (E17 fixed: zwsp shape 1.81M of 4M units, ~3 s); test_redact_finder_cap.py T10 about 4.4 s and T11 about 3.1 s. A timing result at load > 2 means nothing: record the load.
RUN 3 (mutants, one process per file, each prints its summary line; record it verbatim):
  python tests/redact_mutants.py     -> expected "117 of 117 good; problems: []" (G9 builder, wip/cloud-core-c/g9)
  python tests/gate_mutants.py       -> expected 104 of 105 good (R15 survives at the base too; R8 killed by TB-2.11 at the Phase 3 head, but probably equivalent at the current head under G9: record whether it survives)
  python tests/stage_mutants.py      -> expected 37 of 37
  python tests/textnorm_mutants.py   -> expected 256 mutants (244 behaviour, 12 wording), all good (wip-m3 will add its own)
  python tests/g8_mutants.py         -> expected 35 of 35
  python tests/e14_mutants.py        -> expected 8 of 8
  python tests/b64_mutants.py        -> expected all good (count per the G4 ticket v8; G4 builder: all base64 mutants good at Phase 3)
  python tests/p1d_a_mutants.py      -> record the count (identical to base per the G4 builder)
RUN 4 (G4 Phase 4 = host patterns G4c; NOT merged, STOP guard): git checkout origin/wip/cloud-core-c/g4-p4 (code dc85a5310 + docs e5d469a5f on top of Phase 3); uv run --all-extras --group test pytest -q -n 3 -m "not perf and not live" -> builder's result: 2 failed (tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card... = the STOP guard, input ...anna.m@example.org_9<U+4F8B>-_db-7.corp.internal_é<U+4F8B> leaves db-7.corp.internal readable; and tests/test_no_reference_material.py which fails at the base), 15265 passed, 561 skipped, 15 xfailed; 13 of 13 host mutants killed; perf 25 passed. Record the same numbers or the differences.
