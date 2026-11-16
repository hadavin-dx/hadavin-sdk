UPDATED_UTC: 2026-11-16T08:25:42Z
SESSION: core-hardening
ORDER: 007 (and 008 board)
STATE: WORKING
BOOT_ID: 190f8fa6
ITEMS_TOTAL: 7
ITEMS_OPEN: 4
PERCENT: 60
AGENTS_RUNNING: 0
INTERRUPTED: none (first board; no previous BOOT_ID to compare, so a restart before now cannot be seen)
NEXT: item 7: start the two fresh reviewers on items 1-5 (egm-codebase-details + egm-zoom-out); then item 6 stays blocked
PUSHED_UTC: 2026-11-16T08:25:42Z

## ITEMS (ORDER 007)
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| 1 | correct audit text, add misses | done | 100 | AUDIT-FINDINGS.md (A-24, A-04, C-01, X-02 rows, 9g ADD-1..3) | cites re-read in source |
| 2 | re-rate by one rule + count table | done (unreviewed) | 90 | AUDIT-FINDINGS.md 2a; item2-rerating.md | two static re-raters; many cites NOT OPENED |
| 3 | redact.py pattern table, 4 readers | done (unreviewed) | 90 | AUDIT-FINDINGS.md 9h; item3-redact/reader-1..4 | static only, nothing run; lines 700-890, 1050+ unread |
| 4 | job-to-single-owner table | done | 100 | item4-job-owner-table.md | |
| 5 | right-size fix plan | done (unreviewed) | 85 | AUDIT-FINDINGS.md section 4 v5 | cites re-opened for the 4 core fixes only |
| 6 | task B r7u/r7v hygiene | blocked | 0 | none | needs frozen repo2 head 58aa4031 or restored src/lead_desk from the lead; nothing to apply or run here |
| 7 | fresh two-reviewer pass, resolve, FINAL | todo | 0 | none | max 2 rounds |

## AGENTS (none running; closed since the last board)
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a2227583ca61bc58d | redact reader 2 | sonnet | lines 255-484 | earlier | done | 100 | done | item3-redact/reader-2-*.md |
| a681f5d0c896e7103 | redact reader 3 | sonnet | lines 480-700 | earlier | done | 100 | done | item3-redact/reader-3-*.md |
| a62cd9dc77b778656 | redact reader 4 | sonnet | lines 890-1050 | earlier | done | 100 | done | item3-redact/reader-4-*.md |
| a10595b252fe9e380 | re-rater A,B,X | sonnet | one-rule re-rating | earlier | done | 100 | done | item2-rerating.md |
| ac62eedde24547dca | re-rater C,D1,D2,D3 | sonnet | one-rule re-rating | earlier | done | 100 | done | item2-rerating.md |

## LOST OR INTERRUPTED SINCE THE LAST BOARD
| agent | what it was doing | cause | restarted? new id |
|---|---|---|---|
| none | | | |

## LEAD ACTIONS NEEDED
- Item 6: provide frozen repo2 head 58aa4031 or the src/lead_desk tree, and say whether I may edit outside my folder.
- Three files outside my folder fail the vendor-brand guard test (BRIEF-PREAMBLE-studio-2026-11-06.md, portal-design-v2.md, reviews/P1a-idempotence-probe.txt non-UTF-8); not touched.
- Decide G5 (drop?), Q-X1, and whether B-05 folds into X-02 (I did).
