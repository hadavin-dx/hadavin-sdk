# R-gaps: first-time-reader gaps (read-only reviewer, egm comprehension; README of origin main f3c39cf plus agent A and C evidence; B suite evidence was not yet there)
Reviewer could not write files; its list is copied here by the evidence runner. Line numbers are README lines of origin main. "In frozen series" is my check against the claims tree 49d3c859, which was not part of the review.

| id | rank | where | gap | proposed words | in frozen claims series? |
|---|---|---|---|---|---|
| G1 | Blocker | docs/tests.md line 26, scripts/crash_desk.py header, README line 132 | crash command with PYTHONPATH=src stops: "the folder demo_only is missing" (C run 1, rc 1) | PYTHONPATH=src:. (Windows src;.) | YES, fixed (tests.md line 26 and the script header) |
| G2 | Major | docs/tests.md line 26 | does not say to stop the running desk first (not reset.sh: it deletes the records) nor how to restart; a hand-started desk lacks the lead-flow setting unless exported | one sentence: stop the desk by its pid file; restart with PYTHONPATH=src:. python -m lead_desk.server; export DESK_LEADFLOW_FILE for lead flow | NO (open) |
| G3 | Major | README line 63 and Windows line 80 | webhook feed prints 200, the comment names only the verdict while lines 61-62 say 201 | "same person through the other door: prints 200 (not 201) and "verdict": "duplicate"" | NO (open) |
| G4 | Major | README line 64 and Windows line 81 | webhook receipt number 3 while counts say received 2: looks like a lost request; reviewer says verify the reason first | "the replay can use up a receipt number" | PARTLY (frozen line 62 says the replay can use up a receipt number; the counts line does not mention numbers can skip) |
| G5 | Nit | README lines 60, 64, 65 | curl without -s shows a progress table when output is piped (weak evidence: A captured to a file) | curl -s on both lines, curl -si on the last command of line 60 | NO (open) |
| G6 | Major | README line 130 | tests also need Node and a Playwright browser; README names neither; reader may not know tests skip | "Some tests also need Node and a Playwright browser (Chromium); without them those tests are skipped, not failed; see docs/tests.md" | NO (open); verify against B suite skip list first |
| G7 | Major | README line 130 | "about 20 minutes" unchecked | state the measured wall time and the machine (B suite) | see B-suite wall time |
| G8 | Nit | README line 47 | "3.12 or newer": plain python3 may be older | add "python3 -V   # must print 3.12 or higher" | NO (open) |
| G9 | Nit | README line 41 | crash point definition points to a command that failed (G1) | fixed when G1 is | YES via G1 |
Matched the README (no gap): quick start steps 1-13 rc 0 on 3.12.3 and 3.13.18; counts received 2/new 1/duplicate 1; outbox count 1; reset done; ports free.
Not checked by anyone: the portal in a browser, Windows, blind mode, reset exit codes 2 to 6, the nine other crash points.
