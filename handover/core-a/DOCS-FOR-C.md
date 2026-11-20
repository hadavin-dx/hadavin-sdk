# Root docs review round 2: state at d53d6e7d1 (core-a check)

Source: handover/core-c/tickets/DOCS-style-review-2.md (2 Blocker, 7 Major, 6 Nit). Commit 035c923f4 (DOCS3) already applied most fixes. I verified each against the current files and the code; round-3 review file is not on the branch.

| Id | Sev | Doc file:line (now) | Was | State / change | Proof |
|---|---|---|---|---|---|
| 1 | Blocker | SECURITY.md:562-576 (2.10), 50, 102-105, Words used here ~582 | TESTED label with no batch result | Already fixed by DOCS3: UNVERIFIED defined as "note names tests, no result line"; last 2.10 row UNVERIFIED; K12/K80a/K80b/K85 OPEN. Verified, no change | SECURITY.md:582-583 definitions |
| 2 | Blocker | CHANGELOG.md 1-300 | K/G/P1 codes, test-file codes | Verified: none left in lines 1-299. Older sections (300+, P1a/P1b, G10) still carry codes and are pinned by tests: NOT changed (see below) | grep of codes, lines <300: no hits |
| 3 | Major | SECURITY.md 2.10 | paths, G12/G8T/MIX/R8 | Verified gone from SECURITY.md and README.md | grep: no hits |
| 4 | Major | README/CHANGELOG/SECURITY | brand strings | Verified: tests/test_no_reference_material.py list has no hit in the three root files. Config values slack/bedrock_guardrail kept (code requires them). Only hits: handover/BRIEF-PREAMBLE.md (lead file) and DOCS3-notes.md (fixed by me: the banned list is no longer spelled out) | test run |
| 5 | Major | SECURITY.md:9-28 | no status labels | Verified: Status/Evidence line at :24 and UNVERIFIED label at :26. No change | SECURITY.md:24-26 |
| 6 | Major | README.md:82-83 vs CHANGELOG | decode disagreement | Verified fixed by DOCS3: README says redact_text decodes; marked UNVERIFIED (read in code). Not re-run | README.md:82 |
| 7 | Major | CHANGELOG.md:114, 120, 139 | sentences of 46-52 words | FIXED by me: split into short sentences, wording and facts unchanged (no test pins the phrases) | same lines |
| 8 | Major | CHANGELOG.md:5,7,37,126 | headings / unlabelled line | Verified: unlabelled-statement line at :5; Upgrade steps (:126) holds actions. No change | CHANGELOG.md:5 |
| 9 | Major | SECURITY.md K50, K75/K76 | "Accepted" without decision | Verified fixed by DOCS3 notes (K50 source named, "accepted" only where a decision is on file per definition of STATED). Not re-read entry by entry | SECURITY.md Words used here, STATED |
| 10 | Major | SECURITY.md Words used here | TESTED names test | Verified: definition weakened to state where names are given | SECURITY.md:581 |

## Not done or disagree
- Finding 2 and 7 in CHANGELOG lines 300-806 (P1a/P1b/G4/G10 sections, ORDER and finding ids): the reviewer did not read them; DOCS3 left them because several phrases are pinned by tests. Removing them needs a per-phrase pin check; left open.
- Finding 6 and 9 rest on UNVERIFIED reading; I did not re-run a test for them.
- Nits not touched.
- Test: tests/test_no_reference_material.py still fails on handover/BRIEF-PREAMBLE.md (lead file, vendor string).
