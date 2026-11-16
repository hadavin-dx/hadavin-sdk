# PR89 round 16, head f552f26 - slice tests/test_mutation_runner_keywords.py 1-1450 (+ runner 430-610). Read only, nothing run.
No Blocker/Major. Fake secrets all built from parts. Round-15 key=value and lock-name items fixed in slice.
- R16-T1 Minor :782-794 test_one_ellipsis_costs_no_search_per_candidate_start counts find/rfind, which KMP never calls, so it passes for any implementation (even quadratic); docstring describes pre-KMP design. Linearity is covered by the line-event test at 797. Delete or retarget.
- R16-T2 Nit :797-830 sys.settrace may clash with a settrace-based coverage tool. R16-T3 Nit :1229 header "defaults unchanged" above env-read-once test. R16-T4 Nit :1417 redundant startswith("E").
