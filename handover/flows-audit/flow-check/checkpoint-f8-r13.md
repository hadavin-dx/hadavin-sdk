# checkpoint f8-r13 (19:52Z)
Root cause phase 2: test mirror lacked README.md; test_take_check.sh reads it, so take suite failed, run exited 1 (test fault, not script). Phase 3 passed for the same wrong reason.
Done: test_run_all_raw.sh (mirror REQUIRED incl README, phase 3 reason asserted, child cleanup trap, safe rm), test_run_all_stop.sh (cases E,F,G, sid check, D rc 143), run_all.sh (limits, functions/PATH refused, scrub, RESULT check, publish guard), README, repeat_run_all.sh.
Next: one run_all.sh, stop test, raw test on final head; evidence file.
