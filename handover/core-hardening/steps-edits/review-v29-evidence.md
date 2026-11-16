# Owner sheet v29 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: steps-edits/evidence-v29-independent/ (copies in work/ and rebuild/). Recorded, not judged.

## Failures and deviations first
- Own checker found 10 failure lines on unmodified v29 (none in sheet A or B text):
  - UTC time with no IST pair (6 lines): OWNER-APPENDIX-v29-A.md and -B.md line 10 ("after 18:30 UTC your phone's IST date is already the next day"); v29-OPEN-FOR-LEAD.md line 26 ("15:00 UTC"), lines 106, 107, 109 ("11:30 UTC", "17:39 UTC").
  - Placeholder spelling in v29-OPEN-FOR-LEAD.md (4 lines): `[LEAD FILLS before the message ...]` and `[OWNER FILLS ...]` are not the exact spellings.
- check-v29.py C07 info line prints file names that no longer exist (OWNER-NUMBERS-v29-x.md, OWNER-FILM-v29.md), total 7792 counts sheet plus card only.
- v29-fail-proof.py: 9 checks do not fail on built v28 (C161, C162, C164-C169, C171); the reasons in v29-CHANGES.md were not verified.
- The runner's own checker was tuned after the first plant run (38 of 43 caught, then 43 of 43).

## Results
Words: sheet A 6,296, B 6,070 (limit 6,300); card A 1,496, B 1,444; appendix A 3,078, B 3,055; film page 361. All IST pairs on sheets, cards, appendices, film page +5:30; weekdays correct. Key end 18:19 UTC = 23:49 IST, money stop 18:29 UTC = 23:59 IST, 18:14:40 UTC = 23:44:40 IST always labelled "refusal limit". Sheet letter correct. 43 own plants, 43 caught after tuning. Rebuild: sha256 of all 9 built files equals disk. check-v29.py 0 failures; v29-fail-proof 16 of 25 fail on v28, 0 on v29; mut29.py 182 plants, 181 caught, 0 missed. Banned scan 0 over 30 files.

## Not run
Repo pytest guard, ruff, bandit, v24-v28 scripts; whole-repo banned scan; sheet step logic and clarity.
