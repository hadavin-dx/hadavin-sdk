# CLEAN-MACHINE-1 (facts only). Shipped demo = origin main f3c39cf of the public demo repo, fresh clones, clean Linux machine, 2026-11-14 02:50Z to 03:25Z
Evidence files (same folder `clean-machine/`): A-quickstart.md, B-suite.md, C-e2e.md, C2-e2e-313.md, R-gaps.md (first-reader gaps), DOC-FIXES.md plus the .patch (doc fixes on top of the frozen claims tree). All agents ran with made-up data, loopback only, no prompt appeared, nothing was pushed to the public repo.

## 1 README quick start (agent A; python 3.12.3, then 3.13.18; fresh venv each; nothing installed)
- 13 of 13 documented Linux steps rc 0 on both versions; slowest step 3 s (venv). Step 6 counts page: 200, all counters 0. Form lead 201 new; same request 201 replayed; webhook feed prints 200 and verdict duplicate; counts received 2, new 1, duplicate 1; outbox count 1; reset.sh printed "reset done"; no processes left; ports 8765 and 8766 free.
- Not run: any test, the browser portal, blind mode, reset refusal codes, plain `python3` (explicit interpreter paths used).

## 2 Full suite (agent B; python 3.12.3; DPLD_REQUIRE_SCAN=1; 12 chunks, one pytest at a time, rc taken from pytest itself)
- 3883 collected. Without the gitleaks program: chunk 02 26 failed, chunk 03 4 failed (all: "gitleaks binary not found: put it on PATH or set GITLEAKS_BIN"). With gitleaks 8.30.1 set through GITLEAKS_BIN: chunk 02b 230 passed rc 0, chunk 03b 187 passed rc 0; chunks 04 to 11 run with it set. TOTAL with gitleaks: 3879 passed, 4 skipped, 0 failed; the hygiene scan RAN (not skipped); no browser test skipped (browser was already installed on the machine; not installed by the agent). Summed chunk wall time about 23 minutes (the docs say about 20).
- The 4 skips (reason in the log): running as root; needs python 3.13 (this run was 3.12); LEAD_DESK_LOAD_N not set; Windows only. docs/tests.md says 3 skipped.
- Not checked by B: ruff, mypy, bandit, coverage; why the hygiene-scan test prints two tracebacks inside chunk 03.

## 3 End-to-end scenario (agents C python 3.12, C2 python 3.13; unshare -n, loopback only)
- C (3.12): README steps ok; the documented crash command `PYTHONPATH=src python scripts/crash_desk.py` (docs/tests.md line 26 and the script header) FAILED: exit 1, "the folder demo_only is missing". With PYTHONPATH=src:. : crash at D2 (exit 137), restart, re-send. Final received 4, new 2, duplicate 2, 4 receipt rows, 2 leads, 2 CRM contacts, 2 mails (one per person), review/open/unknown/failed 0, stable 15 s later. Cleanup rc 0, ports free.
- C2 (3.13): three distinct people, crash at D2 with PYTHONPATH=src:., restart, re-send: 3 CRM contacts, 3 mails, received 5, new 3, duplicate 2, 0 pending, 0 failed, no second mail after 12 s. All steps rc 0.
- Extra facts from C and C2: the crash scene needs the normal desk stopped first (same port 8765); a hand-started or crash-script desk lacks the lead-flow file and reminder address settings that scripts/start_all.sh sets unless exported; the crash desk's pid still answered kill -0 one second after the crash (cause not examined).
- Not run: blind mail or CRM mode, the other nine crash points, Windows, the browser portal.

## 4 Findings list (all are in the evidence files; fixes in DOC-FIXES.md and the patch)
F1 crash command needs `src:.` (Blocker; already fixed in the frozen claims series 49d3c859). F2 gitleaks program needed for the full run with DPLD_REQUIRE_SCAN=1, not named in README or docs/tests.md (30 failures). F3 stop-the-desk-first and lead-flow settings missing in the crash scene text. F4 webhook feed prints 200 not 201. F5 curl without -s shows a progress table when piped. F6 README omits Node and a Playwright browser for some tests. F7 `python3` may be older than 3.12. F8 browser lock file documented only in docs/tests.md. F9 receipt number can skip (frozen series already says a replay can use up a receipt number).
