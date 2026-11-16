# Resolution log, EDITS round 10 (builder). Result NOT reviewed yet.
Files: `EDITS.md` (round 10), `EDITS.round9.md` (copy of round 9), `build-r10.py` + `build-r10-rows.py` (patch scripts, every old string asserted once), `verify10.py`, `resolve-r10-check-output.txt` (raw: FAILURES 0; 54 rows; every old text occurs once on its line; 0 overlaps; banned-list hits 0 of 10, only counts printed). Nothing else was run; no spend; `inputs/` untouched.

## NOT FIXED (read first)
These findings were not applied in this round (builder ran out of its time box; no impossible-now reason). They are open and need one more fix pass:
- E-36: quote the E-17 clause, relabel text W `NEW (exact)` and text N `NEW [HOLD ...: DO NOT APPLY]`, drop the circular last Why sentence (naive minor).
- E-17: circular Why not fixed. The "Q22(c) lease sentence" was NOT added: Q22(c) in ORDERS concerns the v19 hand-off item 8, not this public post (needs-lead, confirmation i).
- E-22: link to the phrase "crash check untested" not added. E-43 ("ONE Postgres server for the take's data"), E-49/E-50/E-53 (`<day>` example "Wed 18 Nov 2026", consent only after the assistant's message a to d, E-53 override of section 4), E-51 ("spending window", show only the two settings lines, "stated" not "checked"), E-52 (new bullets: request/reply, last time to revoke, revoke, WSL terminal, web address vs mail address, app 1/app 2), E-04 final full stop, E-07/E-08 "nobody on this branch has read", line 40 record format and line 808 "rehearsal": not done.
- Only "posts" became "sends" in E-49 (one place).

## FIXED (design review r9 = D, naive review r9 = N; ids as in the review files)
- N B2, D m1, D m2 (E-09): steps a to e before the database starts; step a is a promise not a control; "you may look again"; step f fourth credential; step g n8n's own database user password in `n8n.env`; "WSL" wording; "table user"; E-09 does not fall away with step 8 (line "How the rows are used").
- N B1, D M3, N M10 (E-11): procedure not control; address exactly `127.0.0.1` plus port (`127.0.0.1.example.com` named as not allowed); asked before EACH test; reply "ok"/"no" plus which; "ok" is about intent; one cost sentence.
- D M2, N M2, N M3, N M5, D m4 (E-12): second yes example folded into the old text and replaced; "request for your yes" / "your reply" split; one typeable line with every placeholder explained, closing sentence REQUIRED, crash-check slot; last day 23 Nov, planned day Wed 18 Nov, latest start 18:04 UTC = 23:34 IST on 23 Nov.
- D M1 (E-55 new): step 22 heading carries both times (revoke 18:19 UTC = 23:49 IST, rest 18:29 UTC = 23:59 IST).
- D M4 (E-56 new): UNVERIFIED flag in front of AGENT-SCOPE line 20 (removed when G1 opens; G1, R9, confirmation j).
- N M5 (E-48): ND7a question and plain replies; question before item 1; shred of the take-folder copy when the key stays; running-take case; older keys; "revoke" only.
- N M6 (E-16): result and counts saved first; only the container the assistant started; "items 2 to 6"; exact reply `Yes, remove the container only` / `No`.
- N M7 (E-39) and ND3: one version per answer; invented "deletes the 3 credentials" removed.
- E-13 (Hold): two `NEW [HOLD G3: DO NOT APPLY]` template blocks.
- E-14: one default (do not film the detail of the mail step), owner decides.
- E-37: heading says the 16 Nov deadline is not the spending window; typing bullet in three parts; fourth credential; E-20 "saved credentials"; E-31 "(UNVERIFIED)"; E-07/E-08 "Linux part of your laptop (WSL)".
- Header: "Read first" section (Apply now, Hold, E-nn, Conditional, studio lead, builder, runner, round, re-pin, final head, studio terms, contact number); "yes message" and "last time to cancel" replaced everywhere; ND1, ND3, ND4, ND7, ND13 edited; confirmations g to j added; R6, R9, G1 updated; counts and index updated (54 rows; Apply now 42; Hold 12; CONTRADICTION 14).

## needs-lead (exact questions)
1. (g) Is the take's Postgres credential a fourth credential, and does step 22 item 1 (line 121, "the 3 credentials") say four?
2. (h) On 23 Nov: latest start 18:04 UTC = 23:34 IST, and revoke the model key at 18:19 UTC = 23:49 IST even if a take runs? Both are builder choices from Q25.
3. (i) Does Q22(c)'s lease sentence belong in the public post of E-17? If yes, give the exact sentence.
4. (j) Is the E-56 flag bullet placement acceptable?

sha256 of EDITS.md: see report.

# r10b (second pass of round 10; builder; result NOT reviewed)
Files: `EDITS.md` (r10b; the first pass is kept as `EDITS.round10a.md`), `build-r10b.py` (anchored patches, each old string asserted), `verify10b.py` (same checks as `verify10.py` plus checks for every r10b change and 24 negative controls), `resolve-r10b-check-output.txt` (raw output: FAILURES 0, rc 0; every negative control printed "caught"). No spend, `inputs/` untouched, banned-list hits 0 of 10 (counts only).

## NOT DONE or only partly done (read first)
- Negative controls exist for each NEW r10b check (22) and for 2 older checks (row ids, confirmation letters). They do NOT exist for most older checks (old-text-once, overlaps, banned and secret scans, UTC pairing, fence parity, gate consistency, scratch-copy presence, E-09/E-11/E-16/E-48 round-10 row checks). Stated plainly: "a negative control for each check" is met for the r10b checks only.
- Naive minors "app / window / screen / post / address / round": defined once in E-52 (new bullets) and convention-fixed for the edited texts; old uses inside unedited v3 lines are not touched (NOT DECIDED 13 covers words no row touches).
- E-14 (who decides the footage) was already stated in round 10 ("You decide what is filmed"); r10b only replaced "post" by "publishes". E-20 has no "saved passwords" in its owner text (the phrase occurs only in the Why of E-03 that explains the change).
- Design m4 (take still running at 18:19 UTC = 23:49 IST): the assistant now says in writing what happens next (E-12, E-48); the latest start for 23 Nov stays 18:04 UTC = 23:34 IST (builder choice, confirmation h). That a take stops safely when its key is revoked is flagged UNVERIFIED, not proven.
- Not independently reviewed; no EGM step run by this builder (the studio lead runs egm:* reviewers).

## FIXED in r10b
E-36 (labels `NEW (exact; TEXT W ...)` and `NEW [HOLD Cb: DO NOT APPLY]`, the E-17 clause quoted, circular sentence removed; line 20 explains `Cb`); E-17 (circular Why replaced; lease sentence NOT added, new NOT DECIDED 14); E-22 (same words "crash check untested" as E-12 and E-17); E-43 (ONE Postgres server kept, two databases, `stage.journal` exception, never "one store"); E-49/E-50/E-53 (`Wed 18 Nov 2026` example, yes only after the assistant's message that states (a) to (d), E-53 says section 4b overrides line 27 only for that case); E-51 ("spending window", only two lines shown, decision's statement not checked in code); E-52 (7 new bullets); E-04 full stop; E-07/E-08 "nobody on this branch has read that evidence"; record format of line 48 equals the ND "Record:" lines (ND8, ND12, R7 aligned); "flow rehearsal" always with its first word (line 3, line 27, E-19 Why, line 863); Q19.5 stated in E-48 ("every key except the one made for this take") and in its Why; E-31 (unproven safety claim removed, search path explained); line 14 (first smoke, stage settings file, search path); ND6 "same spending window".

## needs-lead (exact questions)
1. ND14: does a lease sentence belong in the public post of E-17? (default: no; Q22(c) is about the v19 hand-off item 8).
2. E-36 text N label uses `Cb` (confirmation b) instead of a gate letter: acceptable, or define gate G6?
3. E-52 says app 1 is the read-only app and app 2 "the second app": what is app 2 for? (no input says).
4. Confirmation h (latest start 18:04 UTC = 23:34 IST on 23 Nov) still the builder's choice.
