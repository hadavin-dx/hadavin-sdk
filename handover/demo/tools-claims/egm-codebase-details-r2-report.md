FACT REVIEW, round 2 of cap 2 (read-only; Grep/Read only).

WHAT WAS NOT DONE (read first)
- No tests, commands or scripts were run. Every finding comes from reading the diff against the tree files.
- No R-numbers were looked up: the studio bible is not reachable from here, so none are cited.
- Not checked: the "AST-identical except docstrings/comments" claim; the 17-commit / 41-file / 571+/528- totals (only file and test counts inside the docs were checked); test_backfill_classes; browser tests; test_slow_sender; the A2 test description; imap_count header-only fetch; reset-script exit-code details beyond reading reset.sh; the semgrep comment exit codes; whether SQLite really burns an AUTOINCREMENT id on an upsert (needs a run).
- Result: the series is NOT clean. There is 1 Blocker and several Majors.

BLOCKER
| Where | Exact words | Problem | Replacement |
|---|---|---|---|
| README.md:117 (diff ~321) | "The measured figures in `docs/limits.md` come from one Windows computer, were tried by the author ... their raw logs are not shipped" | docs/limits.md now says "No measured load figure is stored here" (and its item 9 says the same). The README contradicts it and claims an earlier run the repo cannot prove. | Delete the sentence. Keep: "A load of 10,000 requests was not tried. No measured load figure is stored in this repository (`docs/limits.md`)." |

MAJOR
| Where | Exact words | Problem | Replacement |
|---|---|---|---|
| pr-body-final-draft.md:39 | "* RESULTS-PLACEHOLDER" | The Checks section has no result at all. There is no command output and no head SHA for the final tree. The PR claims checks but shows none. | Paste the real output of `uv run --all-extras --group test ruff check`, `ruff format --check`, `pytest` and `bandit -ll` on the final tree, plus the head SHA. If something was not run, say so. |
| docs/tests.md, P5 row (diff ~1643, unchanged context line) | "Larger bursts are reported separately in `docs/limits.md` (measurements, not part of the test run)" | limits.md has no measurements now, so this is stale. | "A larger burst can be run with the optional measurement test described in `docs/limits.md`; no result is stored." |
| docs/why-this-code.md (diff ~1727) | "the one real-service try was the separate probe script ... which made a few calls to a free HubSpot account" | An earlier-run claim that cannot be proved here. The PR body says such claims were deleted. | "`scripts/hubspot_probe.py` is a separate script you run yourself against a free HubSpot account; no run of it is recorded here." |
| docs/n8n-recipe.md §0 (diff ~1149 and ~1156) | "The runs used its free community licence" and "The demo ran n8n on port 5679 (n8n's own default is 5678)" | These are earlier-run and outside facts, and they contradict the new header "No result of running them in n8n is stored". | "The scripts and `proof.json` expect port 5679. Which licence applies was not checked here." |
| README.md ~lines 20, 37, 62, 79, 104 | "uses up one receipt number ... (for example receipt 1, then 3)" | Stated as fact, but no test checks it; docs/tests.md P1 itself says "no test pins the skipped number". The code has `receipt_id INTEGER PRIMARY KEY AUTOINCREMENT` and `ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts + 1`. Whether this skips a number was not run. | Add a test and cite it, or write "may skip a receipt number (no test checks this)". |
| README.md:41 | "review-item ids (`D3`, `N5`), which are explained in `contract.md`" | contract.md does not explain `N5`; the id format there is `N<lead_id>`. `N5` appears only at README.md:41 in the tree. | Use example ids that match the contract and name the exact contract section. |

NIT
| Where | Exact words | Problem | Replacement |
|---|---|---|---|
| contract.md, Windows limit paragraph | "tests use port 0" | The same paragraph cites 20 restarts on one fixed port. | "most tests use port 0" |
| contract.md (test_followup_edge_cases.py case) | "a plain object" | The test uses `object()`. | Say "a bare `object()` instance". |
| src/lead_desk/desk.py comment vs test | "4301-digit" | The test uses 10**4400, which has 4401 digits. | Make the comment and the test use the same number. |
| docs/limits.md:30 | "run only against a local stand-in server; no real provider was called while this was written" | Earlier-run wording; the docs elsewhere say "demo server". | "run only against the local demo server" |
| scripts/crash_desk.py docstring | "(on Windows: set PYTHONPATH=src;. first)" | cmd syntax, while the README uses PowerShell `$env:PYTHONPATH`. | "(PowerShell: `$env:PYTHONPATH='src;.'`)" |

VERIFIED AGAINST CODE (by reading only)
- File and test counts, lock-file line counts.
- scripts/start_all.ps1 empty-leadflow condition equals start_all.sh.
- Constants and stuck grace (send_timeout + 5 busy waits of 5 s).
- Worker caps and desk exit codes; Host/Origin gate and loopback definition.
- crm_hubspot `set_fields` and smtp_provider `make_outbox`.
- n8n JSON values.
- Probe arithmetic.
- `in (1, 2)` to `== 1` change: the new test_two_drives_one_email docstring and assertion are consistent with test_ai_after_claim.py as cited.
- reset.sh exit codes 2, 3, 5 and 6 match what I read (not run).

Relevant paths: /tmp/work/d/final-series-r2.diff, /tmp/work/d/pr-body-final-draft.md, /tmp/review-tree2/ (README.md, docs/, contract.md, src/lead_desk/desk.py, tests/test_input_edge_cases.py, scripts/reset.sh).