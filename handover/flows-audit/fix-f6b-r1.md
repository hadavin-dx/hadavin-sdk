# fix-f6b-r1: fixes to F6B-AUDIT.md after reviews/f6b-naive-r1.md
Unverified: every n8n/Postgres statement (nothing run); line numbers re-read only for build_mainframe.py:98-100, V5-README.md:8-9, SCENE-FLOW-MAP.md:66, the [demo] subject; others not re-checked. No EGM review ran before this fix. reviews/f6b-design-r1.md did NOT exist when I finished, so those findings are not fixed; the lead must re-run this fix when it lands.
Fixed (each finding of the naive review):
- Top: 3 action lines; honesty block (nothing run, no EGM review, test-build warning); glossary before first use incl. recovery, claim, door, Nit*, n8n, real/film sets, scenes, C1, [demo], stand-in CRM; one-line meaning of every F-/F6-/F6B-/K/T/AF/B/R code.
- F6B-01 re-rated Nit* to Major (reachable in the take); counts now 0 Blocker, 1 Major, 6 Nit*, 5 Nit.
- "cannot" replaced by "I found no path that" where nothing ran; "Checked and found fine" renamed "Read and found no problem".
- Warning that T10/T11/AF1 may run a different build than the filmed flows, at the top, in the table header and at T10/T11 cells.
- Empty Unverified cells now say "none"; EGM note updated at the end.
Not done: dense table cells left as is (style only; splitting would change row structure).
