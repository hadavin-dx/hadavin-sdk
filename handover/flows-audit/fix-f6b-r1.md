# fix-f6b-r1: fixes to F6B-AUDIT.md after reviews/f6b-naive-r1.md
Unverified: every n8n/Postgres statement (nothing run); line numbers re-read only for build_mainframe.py:98-100, V5-README.md:8-9, SCENE-FLOW-MAP.md:66, the [demo] subject; others not re-checked. No EGM review ran before this fix. reviews/f6b-design-r1.md did NOT exist when I finished, so those findings are not fixed; the lead must re-run this fix when it lands.
Fixed (each finding of the naive review):
- Top: 3 action lines; honesty block (nothing run, no EGM review, test-build warning); glossary before first use incl. recovery, claim, door, Nit*, n8n, real/film sets, scenes, C1, [demo], stand-in CRM; one-line meaning of every F-/F6-/F6B-/K/T/AF/B/R code.
- F6B-01 re-rated Nit* to Major (reachable in the take); counts now 0 Blocker, 1 Major, 6 Nit*, 5 Nit.
- "cannot" replaced by "I found no path that" where nothing ran; "Checked and found fine" renamed "Read and found no problem".
- Warning that T10/T11/AF1 may run a different build than the filmed flows, at the top, in the table header and at T10/T11 cells.
- Empty Unverified cells now say "none"; EGM note updated at the end.
Not done: dense table cells left as is (style only; splitting would change row structure).

## Round 2 (after reviews/f6b-design-r1.md)
Unverified: nothing ran; the review's claims were checked by reading only: C1 text (SCENE-FLOW-MAP.md:66), mf.py:72, build_mainframe.py:8,54,59,98-113, PLAN-002.md:61, and `ls` showing 11 mf-recovery.json files. Ratings are my reading, not confirmed by any run. Sub-workflow JSON, SMTP timeouts, RERUN-RUNBOOK, VIDEO-RUNSHEET not read.
Fixed in F6B-AUDIT.md:
- F6B-03 recipe: was defective (left mail_sent=true on unknown rows, causing an alert loop). Now two recipes (failed / unknown) with mail_sent=false and a sent-folder check first; T-RESET extended.
- F6B-01: admitted C1 already covers the wrong-destination case; row now says what C1 lacks. F6B-02 reframed as mostly C1 plus missing command/owner/place. F6B-05: mf.py:72 checks recipient and key. F6B-12: lease comes from the command line, not typed in.
- Ratings: every row has take and client-build ratings (Blocker for client build: F6B-01, F6B-03; take Major: 01, 02, 13). "0 Blocker" now explained as counting lead mail only; alert-mail duplicates stated.
- Summary no longer claims alert at most once (contradiction with the fine-section fixed). F6B-08 take-risk noted. Clock bullet notes run duration uses the n8n clock.
- New rows F6B-13 to F6B-17 for items a to e. Top actions now 4 (added scenes 6-8, re-take, old flows).
