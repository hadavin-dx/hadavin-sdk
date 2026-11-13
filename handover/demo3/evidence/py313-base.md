# Python 3.13 full suite on BASE (evidence runner N; raw output only, no judgement)

| head | python | passed | failed | skipped | wall |
|---|---|---|---|---|---|
| f3c39cf89ec989f032ea48a23cfd824b88da9c68 (BASE) | 3.13.18 | 3684 | 0 | 199 | 899.22 s (EXIT_CODE=0) |
| f3c39cf (BASE), earlier run | 3.12 | 3683 | 0 | 200 | 1189 s |

- Errors: 0. Hangs: none (no test over 10 minutes; faulthandler never fired).
- Skip reasons (199 total): playwright missing (6 lines), gitleaks missing (6 lines), Windows-only reset (1), root can read no-permission file (1), LEAD_DESK_LOAD_N measurement (1); see log `-rs` section.
- Difference from 3.12: +1 passed, -1 skipped. No test name or skip line contains "isreserved"; that this delta is the ntpath.isreserved test is NOT confirmed (the 3.12 log was not diffed).
- Env: raw/env-py313-base.txt (Python 3.13.18; full pip list in file; ntpath.isreserved exists).
- Logs: raw/suite-py313-base.log, raw/progress-N.txt. UTC run 12:10-12:25Z (IST 17:40-17:55).
