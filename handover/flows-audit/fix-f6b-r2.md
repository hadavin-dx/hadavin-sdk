# fix-f6b-r2: fixer report, round 2 (last), for F6B-AUDIT.md
Static edit only. Nothing run. n8n facts UNVERIFIED. Only F6B-AUDIT.md edited, plus this note.

## Not done / still open
- The Postgres database name is not in the repository: action 1 tells the person to run `SELECT current_database();` and check. Needs the owner or the laptop.
- No independent EGM review of the audit exists; the file now says so plainly. All SQL stays UNTESTED; T-xxx tests PROPOSED.
- Reviewer claims were condensed; I checked cites myself (FINDINGS.md:93, PLAN-002.md:61, build_mainframe.py:28-29,51,54,97,103, SCENE-FLOW-MAP.md:66, 12 recovery files by `find`, tick arithmetic for F6B-16).

## Done
- F6B-01: false F-031 sentence removed (F-031 = invalid e-mail to `review`); rated take Blocker unless action 2 done, by the rubric; client Blocker.
- Recipe B2 has its own full statement (state='unknown'); recipe B1 closes; F6B-03 rating reconciled with the recipes.
- TRUNCATE warned (deletes all, no undo, demo database only); all SQL labelled UNTESTED, not for live systems.
- F6B-05/07: crm_id may be empty in the race; contact found by e-mail or `hadavin_lead_id`.
- F6B-16: 2 min 15 s to 4 min 15 s, tick-phase note.
- Action 2: all four real flows; where and who added to actions 1 to 4.
- Nits: MarkFailed has no lock; 30 s timer is a node setting; table screen not run; 12 recovery files; F6B-04 reason; F6B-17 reading; F6B-13 unverified; T-xxx PROPOSED.
- Undefined labels: new "Words you need first" block; rating terms unified; count line matches table (1 Blocker, 2 Major, 2 conditional, 1 open, 11 Nit); line-94 contradiction removed; UTC/IST note.
