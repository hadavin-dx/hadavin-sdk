# Lane 13b (BUILDER): fixes after REVIEW-1. Base 0841f36 (pr-3-tests head, verified). Not committed, not pushed.

## Failures and uncertain (first)
1. NOT RUN TO THE END: the full portal browser test files with both patches (evidence-b6) was stopped on the lead's order; its file holds no result. Proven instead: the new tests only (b1,b2,b4,b5). The two Pillow sidebar tests were not run (Pillow not installed, outside the lock).
2. NOT RUN: tests/test_hygiene.py with gitleaks, `gitleaks dir/git`, ruff via uv. Only `ruff check` and `ruff format --check` (hashed venv, ruff 0.17.4) on the 3 new test files: pass. Test literals: example.test addresses and "W"*200 only, but the gitleaks scan did NOT run on them. Lead must run it.
3. Tools: playwright 1.63.0 installed outside the hash lock (evidence run).
4. Screenshots: the many before/after PNG files copied here are raw sweep output (tag names base/after1/tryB...), not curated; not all viewed (viewed: confirm 390, needs 1280, overview/leads 390).
5. Nit 2 (header align-items with a long title at 390): NOT decided or measured; left as is.
6. Overview/needs/leads 390 layout fixes in patch 2 are my own layout choices (2 KPI tiles per row, tabs scroll sideways, search may shrink): reviewed only by my eyes on 3 screenshots; need the lead's look. Patch 2 also edits demo_only/portal_demo.css.
7. Needs/toast/dialog tests feed the page JSON from tests/portal_fixtures/review.json with long values (route interception), not a desk-made card.

## Findings table
| review finding | what I did | proof |
|---|---|---|
| M1 confirm dialog | MEASURED: 200-char name makes the dialog paragraph 2830 px wide, running to x=-1985 (cut off on the left); buttons stayed right. Fix `.dialog p { overflow-wrap: anywhere }`. Test fails on old css, passes on new. | evidence-b-sweep-sw-base/p1.txt, b1, b2 |
| M1 siblings | measured all (table below); fixed toast, needs card, leads company cell | sweeps, b1/b2 |
| M2 390 px root cause | Correction: not "sidebar stays 232 px". Cascade confirmed by measurement: `.shell` computed columns 208px at 390, 700, 900 (should be 64px at <=860); 64px after fix. A second, separate cause: masked-value `.sr-only` 1px spans are position:absolute inside the non-positioned `.table-wrap` scroller, so a span at x=650 stretched the Request log page to 651 px at 390 (fix `.table-wrap{position:relative}`). Then page-specific 390 causes (below). | pages-pg-*.txt/json |
| Nit 1 | test now: h2, pill, close inside panel on both sides, 390 case added, fixed 400 ms sleep replaced by waiting until the panel's right edge = window edge | tests/test_portal_drawer_long_name.py, b2 |
| Nit 2 | not done (see 5) | |
| Nit 3 | not touched | |

## Sibling sweep (200-char no-space value, real browser, getBoundingClientRect both sides; head css before -> after patch 1)
| place | overflow on head? | after |
|---|---|---|
| confirm dialog p | yes (p 2830 wide, left -1985, 1280 and 390) | none |
| toast (hint) | yes (toast 836..3763 at 1280) | none |
| Needs card name (need-who), heading, why, notes, desk-note row | yes (card contents 793..3521, clipped by card) | none |
| Leads table company | yes: company column 2077 px, name column squeezed to 63 px, table scrolls 2728 vs 974 | table 974/974, ellipsis at >1200 px |
| Leads table name / email | no (ellipsis rules) | - |
| .later-value (long first/this values) | NO (measured on head: 0 offenders, scrolls inside its box) | - |
| Overview feed | NO (0 offenders at 1280) | - |
| Request log cells (128-char request number = desk maximum, long name) | NO at 1280 (0 offenders, no scroll) | - |
| Data and AI page, Demo controls | NO at 1280 | - |
Note: the desk limits request number to 128 chars; name/company to 200. Tested with those maxima. Drawer title: lane 13 fix, measured again (no overflow).

## Page overflow, all pages, ordinary names, masked (default); doc scrollWidth vs clientWidth, light=dark (pages-pg-*.txt)
| width | HEAD / patch 1 only | with patch 2 |
|---|---|---|
| 390 | overview 754, leads 632, needs 608, log 803, data 423, demo 477, lead panel 632, dialog 608 (all > 390) | all 390 = no overflow, shell 64px |
| 700 | overview 754, log 803 (> 700), others ok; shell 208px | all ok, shell 64px |
| 900, 1100, 1280 | all ok | all ok (unchanged, 208/208/240) |
Wide tables (leads, log, data) scroll inside their card at 390/700: by design, not page overflow.

## Patch 2 content (mobile-cascade.patch): app.css: the three shell/page/strip lines of the 1200 block moved to `(min-width: 861px) and (max-width: 1200px)`; `.table-wrap{position:relative}`; leads.css (search shrink, hint wrap, toolbar-block column), needs.css (tabs scroll), overview.css (2 tiles per row, donut stacked, grid column), demo_only/portal_demo.css (.dm-proof-row wrap); test tests/test_portal_phone_layout.py (16 cases).

## Tests (command first line in each evidence file)
- b1 new tests on HEAD css: 33 failed, 3 passed (fail before). b2 patch 1 tests on patch-1 css: 20 passed. b3 phone tests on patch 1 only: 13 failed 3 passed. b5 phone tests on patch 2 only: 16 passed. b4 all 36 on both: 36 passed.
- Patch 1 tests do not depend on patch 2 (needs-card test compares with the card box, not the window; I fixed that after seeing a 390 fail with patch 1 alone).

## Apply matrix (evidence-b-apply-matrix.txt, fresh clone 0841f36)
Both patches apply alone, together in both orders. Against every pending patch that applies alone on the head (all codeant-*/codeant2-* except the 3 codeant-gitleaks, docs-and-deps.patch, docs-and-deps-v3.patch, semgrep-rebased.patch): ok in both orders and all three together. Patches already failing alone on the head (codeant-gitleaks*, extra-demo-only, js-portal, py-retry, docs-and-deps v1/v2) fail without mine too. File overlap: none (others touch js/py/docs/tests of other files; my css/test files are touched by no other patch). Overlap P1/P2: app.css (different hunks), leads.css, needs.css (different hunks).

Files: drawer-long-name2.patch, mobile-cascade.patch, evidence-b*.txt, sweep/pages json, PNGs. Scripts: /tmp/work/l13b-scripts/. Rules: 6, 7, 19 applied; no R-numbers looked up. EGM review of the result is the lead's step.
