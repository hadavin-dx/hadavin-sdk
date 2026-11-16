# v24 changes (builder, Mon 16 Nov 2026). Failures first.

## NOT fixed or not shown
1. **Word limit NOT met.** OWNER-SHEET-v24-A.md and -B.md are above 6,500 words (counts in evidence-v24/05-wordcount.txt, not copied here so no copy can differ). The cut list of review-v23-zoomout.md was applied only in part (section 4, lead-side glossary entries, the sample notice, the 7.2 checksum line, the 6.3 key-file listing and the 6.6 process listing commands). Next step: one more cut pass of about 1,300 words; candidates: rules R1/R4/R9 wording, numbers-message sample lines, section 1 glossary items, 5.x and 7.x prose.
2. The builder ran out of its 60 minute box; independent reviewers follow. Nothing was judged done.
3. Everything about vendor pages, buttons, Windows, WSL, PowerShell, n8n and real behaviour stays UNVERIFIED; nothing here ran on them.
4. ORDER 034: no outside reader is shown to have named the root cause; not shown as met.
5. M2 (film after the card) and M3 (ship B only) are not decided: v24-OPEN-FOR-LEAD.md rows 72 and 73. No extra variant was generated.
6. The checker never tests meaning; it tests listed properties only (see evidence-v24/02-plants.txt for what the 42 plants did and did not catch).
7. The note LEAD-RELEASE-NOTE-v8.md is the v7 note edited (stale terms replaced, a v8 section added), not rewritten; its gate list G1 to G42 was not re-derived against every new sheet step. Next step: independent read of the note against sheet A and B.

## Where each fact lives once
All numbers, times, UTC/IST pairs, run day, deadline, post-by and set phrases: `facts-v24.py`. Prose: `OWNER-SHEET-v24-SOURCE.md` (A and B variants by markers, removed at build), `LEAD-RELEASE-NOTE-v8-SOURCE.md`, `v24-OPEN-FOR-LEAD-SOURCE.md`. `build-v24.py` writes the finished files; `check-v24.py` rebuilds and fails when a file differs. The cancel rule: the card in sheet section 2 only.

## Adversarial review (review-v23-adversarial.md) 1 to 14
1 card (g) exception; 2 no checksum line in the sheet (7.2 removed; check C14x); 3 owner switches Recording OFF himself; 4 third phone alarm at the latest start, card (e), date check at 7.3; 5 backtick sentence; 6 paste only after the last line `paste key, Enter:`; 7 READ and TEST paper notes; 8 ignore `.used`; 9 A: older key cancelled only after the earliest key time, right before create; 10 notice window has a clock; 11 card (f) says test terminal; 12 "if 7.4 never happened, tell none"; 13 SAMPLE label; 14 lead cannot reverse the order (R8).

## Other
Rules R2 and R3 are not used (v23 open rows 59 and 68 contradiction removed). Stale "Part 2", "re-pin", the old minutes figure removed from the note and open list. HubSpot is delete or revoke only. "no key was made" starts clean-up (8.2). Full date compared at 6.3 and 7.3; balance and auto-reload re-read at 6.2 and 7.1. The last-resort step is bounded (10 + 10 minutes) and named in the yes. Key-save line: empty paste and a second pasted line handled in the sheet text; behaviour re-tested in evidence-v24/04.
