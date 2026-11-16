# PR H fix batch b4 (builder's own evidence). Base e852b577, head d08ec151 (code head 0561c618 plus a one-test fix)

FAILED / NOT CLEAN first:
- Full pytest (own Postgres 16, port 56347, through heavy.sh) at 0561c618: 2 failed, 12895 passed, 1 skipped. (a) tests/test_k5_fixes3.py::test_the_decoded_view_is_computed_once... patched the renamed `_decoded`; fixed in d08ec151 (file re-run alone: 9 passed). The full suite was NOT re-run after that fix. (b) tests/demo_askdata/test_validate_harm.py [dblink-connect]: needs a Postgres on the default socket /var/run/postgresql; fails with my own server on another port (re-run alone with PG env: same one failure). Not caused by this change; not run on main by me.
- First full-pytest attempt was killed (Terminated, exit 143) by the environment; re-run once; both logs kept.
- G4 against main (alone): H1 2.82x, H2 3.28x, H3 (new sgr0 shape) 4.72x, H4 (new, large colourised log with sgr0) 3.01x; no-hidden shapes 0.97 to 1.10. The old limit 1.25 applies to shapes without hidden items only. H4 at the 262,144 cap is shown (not refused), 1.0 s CPU. Slowest, H3: 1.76 s CPU, under the 3.0 s gate.
- No gitleaks run on the evidence text beyond the commit scan; the evidence files hold no secrets (made-up values).

PASSED: ruff check, ruff format --check, bandit -ll, scan_repo (exit 0); prh_mutants 55 of 55 good; stage_mutants 37 of 37 good; perf file 34 passed; gitleaks on e852b577..0561c618 no leaks.
Fail-before on old src: 58 new test ids, 49 fail, 3 pass on old code (list in pass-on-old-code.txt): the count of pinned rows (data only), the converse check (lists are true on old code too), and the clean control row b4_ctl_colour (passes by design); 6 perf ids not run on old code.
Pass bound: 24, measured worst 17 (60 s hill climb), random 16, rows 7 or fewer.
