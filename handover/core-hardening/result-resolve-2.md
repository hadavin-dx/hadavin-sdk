# result-resolve-2: egm-resolve, round 2 of max 2 (headless, auto-accept PROPOSE FIX)
Status: resolved. Target: AUDIT-FINDINGS.md. Inputs: result-review-2a.md, 2b.md, 2c.md.
Method: each Blocker/Major was categorised; applied fixes were checked in the rebuilt file by search (key phrases present: five call sites, scope note, step 0, guarded_call, deferral list, section 9f, about 120 distinct, pending question 5, owner/lead question labels, grants note, extra glossary line). No lane severity was changed.

ESCALATE (to the lead; a decision, or evidence outside the reviewers' files):
- 2b A1/A2: the Blocker rule was applied unevenly and nobody has fixed the final Blocker set. The document says list 1 (builders' five) stays in force until the lead decides.
- C-01: the patch lets the fake kind keep a zero price (tests and demos use it); not approved yet.
- New question: CLAUDE.md says "money is integers" but the core uses Decimal for prices and spend. UNVERIFIED which is wrong.
- Whether the studio-laptop items D3-10, D3-11, D3-19 belong in this repo's audit.

PROPOSE FIX, applied to AUDIT-FINDINGS.md:
- 2c: B1 (wired versus works), B2/B3 (three lists, who decides, count basis), B4 (12 questions, labelled decision or fact), B5 (pre-review label, D2-01 conditional, B-04 conditional on question 3), M1 (call sites), M3 (counts), M4-M6 (glossary terms), M7/M8 (wording "reviewers' proposed set", "no code found").
- 2b: C2 (five model-call sites), C3 (no executor in pilot/prod), D1 (one `guarded_call`), D2 (patch not approved, max_tokens bound), D3 (one grants design for X-02 and X-16), D4 (decide G5 before deleting A-10 lines), D5 (list of Majors outside any step), D6 (step 0: heartbeat and B-10), D7-D10, E (two spend tallies, no log of record), A3 (about 120 distinct issues).
- 2a: D1-01 (36 uses, rule line 23), D2-04 (data files), D3-01 and D3-07 notes, line fixes (B-01 cli.py:299, C-02 :440, k1b 166-172), section 4 friction notes (max_tokens, existing guard test, A-10 caution).
Applied as proposals only (severity left to the lead): re-ratings in 9f (D1-03, D3-06, D3-07, stage rename, D2-15).

DECLINE (Nit): id clash M-C-24 and C-24; thin map rows (listed in 9f); wording nits.

NOT applied, disclosed: Part IV and X-06 lane text still carries the old D1-03 wording (the correction is in 9d and 9f; lane texts stay as the builders returned them). Part III still prints the wrong limits.py line numbers (listed in 9a and 9f).

Counts: about 34 fixes applied, 0 contested, 4 escalated groups, 3 declined, 2 disclosed leftovers. Round cap: result round 2 is done; no round 3. The changes are text only. A fresh reviewer has NOT read the round 2 rewrite.
