# EDITS r18 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: evidence-r18-independent/00-TABLE.md. Recorded, not judged.
## Misses first
- 6 of 24 fresh mutations NOT caught by verify18.py (18 caught): M10 first "Tue 24 Nov 2026" in the lead-confirmation text (EDITS.md line 87) changed to "Mon 23 Nov 2026"; M11 forged counts in r18-CHANGES.md (21,492 to 20,492, 198 to 199), verify18 never reads CHANGES; M15, M18, M22, M23 a safety sentence deleted or reversed identically in every copy ("the assistant answers it once" for a `key revoked` message changed to "never answers it"; "The assistant never opens the files." deleted; 2nd sentence of K-D deleted; "(never its content)" deleted). Shared cause: wording is pinned only through 32 phrases in _CANON18 plus older per-row checks; a sentence off those lists passes when changed the same way in all three copies (applied sheet, day sheet, appendix).
- Slot wait about 6 minutes; first queued attempt had a wrong path, killed (own pid). "EDITS.md 1087 lines" in r18-CHANGES is 1086 by wc -l (trivial).
## Builder claims re-run (confirmed)
NO_NEG=1 verify18: exit 0, FAILURES 0 (plants 167/167, pair 71/71, reversal 10/10, day sheet 10/10, appendix 9/9; 102 r18 checks). Full run with 198 negative controls via heavy-slot: exit 0, 198 caught, 0 NOT CAUGHT. On EDITS.round17.md: 113 FAIL lines (86 r18, 18 r17, 9 older). 60 rows (48 Apply now, 12 Hold).
## Words
Applied sheet 21,492 (wc -w; same with Python split; 21,325 by a stricter count); day sheet 2,020; appendix K 1,272 (identical to the section in EDITS.md); input OWNER-STEPS 4,488. L-LEN (6,300) not met.
## UTC/IST and weekdays
Applied sheet 71 times 0 wrong, day sheet 17, appendix K 6; weekdays 61 checked, 0 wrong.
## Scans
Banned 0 in 8 files; key-shape 0 (e-mail shapes only, reserved example domain).
## Not checked
Clarity of wording, inputs/ contents, each of the 198 controls re-derived, any real take, provider click path or spend.
