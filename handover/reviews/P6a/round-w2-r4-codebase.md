# PR72 round 4 review - head a3d7eb0, reviewer egm-codebase-details (read-only, snapshot only)

Verdict: 0 Blocker, 0 Major, 3 Minor, 3 Nit. All five round-3 findings (BL-core-a14-w2-r3-01..05) fixed in the code the reviewer could read; the made_up_data_only-only split holds (one StrictBool in src: config.py:20 and :376).

Not checked: no code run; cli.py, tests/test_k5_tools.py, tests/test_k3_review_fixes.py, tests/test_k3_pilot.py not in the snapshot (so the cli mutant locate text and two named killer tests are unverified by the reviewer); CI state; the ticket P6a.md is stale (still says dev, DEV_ONLY, 42 rows, 45 mutants; code has demo, DEMO_ONLY, 82 mutants plus a channel item and a log line).

Minors
- m-A tools/client_profile_mutants.py:12-16 and :179-189: docstring says killers are anchored "at both ends"; only the end is checked. `::test_x$` also matches other.py::test_x (test_stage_names.py:216 test_demo_only_is_exactly_the_six_pairs shares a killer name). An alternation such as `::a$|b` passes. Fix: narrow the wording or require file::name and check each alternation branch.
- m-B :912-913 and :982: with MUTANT_ONLY a clean subset exits 0 though the docstring says exit 0 only if every mutant was located and killed. Make a partial run exit non-zero or say so.
- m-C :85-107 scrub gaps (belt and braces): no refusal prefixes for SLACK_, PG/DATABASE_URL, CLOUDFLARE_, KUBECONFIG; network not blocked (metadata endpoints reachable); credentials outside HOME not covered; on Windows HOME is ignored (test at :739 passes either way).
Nits
- n-A test_client_profile.py:766-767 positional row tuple.
- n-B CHANGELOG.md:14 and :11 name DEMO_ONLY and app._LIVE_HOOKS without a plain explanation.
- n-C builder note says 7 sub-bullets, CHANGELOG has 8.
Evidence note: the runner's partial folder at a3d7eb0 was incomplete (bandit missing from the test group in its environment); it was stopped and deleted because a minors push supersedes this head.
