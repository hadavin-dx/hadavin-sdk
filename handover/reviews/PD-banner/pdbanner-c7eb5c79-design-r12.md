# PD Part 6 round 12, design reviewer (egm-design), head c7eb5c79

Read-only, snapshot /home/user/build/snap/pdbanner-c7eb5c79/. Condensed by the lead session from the inline report. Result: 0 Blocker, 1 Major, 4 Nit. No new fail-open found. Ran nothing; fail-before labels judged from comments only. No SonarCloud claim.

Suppressions: inline markers on added lines of DIFF.patch: 0.

M1 pyproject.toml:78-90 per-file ignores. BLE001 for app.py and mode_banner.py: extend-select is B,DTZ,I,S,TID,UP so BLE is not enforced; the waiver does nothing, comment says "owner decision pending" and names four sites (there are five); it is a suppression by another route added while the decision was OPEN. Fix: delete both BLE001 entries and the comment. S603 for tests/fixed_run.py, tools/demo_only_guard.py, tools/scan_repo.py: real waivers (S selected); r11 brief said escalate if the rule still fires; no escalation seen; scan_repo.py:74 passes a variable cmd (likely cause).

Broad except sites (5): app.py:295 (_known_overrides; could reuse _SEAL_ERRORS; NameError test at test_mode_banner.py:3105-3135 and KeyError :3160); app.py:312 (App.mode_banner; narrowable, only AttributeError tested :3150-3155); app.py:471 (channel post_card; third-party may raise anything; matches main; not a mode site); mode_banner.py:731 (banner_or_unconfirmed; probably narrowable to TypeError/ValueError; tests :1346-1385); mode_banner.py:759 (cannot-fail contract; RuntimeError test :1797-1805). Seal vs read asymmetry: seal error propagates (fail closed), read error becomes unconfirmed.

Seven classes: 1 PIN-LABELS mostly fixed (tolerant _given :2217-2223; once-test asserts 1 :3515). Nit test_mode_banner.py:3638-3660 label cites missing _UNREADABLE name (name-only failure, does not count). Nit :3105 and :3490 overlap. 2 SEAL-COMPLETE fixed (_stage app.py:236-244, compare :292, test :3593-3602, R12B1). 3 MUTANT-KILLER fixed in substance (R12C1/R12C2, equivalence note banner_mutants.py:2412-2420 holds; COMPUTED_EXPECT exempts 20 rows: confirm in row run; R12C1 weak kill by message). 4 inline suppressions done. 5 SEAL-TEST fixed. 6 CHANGELOG fixed as far as read (lines 7, 15, 219-221, 226 not read in full). 7 TEXT not verified; long comment lines (200+ chars at test_mode_banner.py:3592, :3605) break 100 columns (E501 not selected).

Not checked: no tests, ruff or mutants run; dd827d79 claims; JS/CSS painter; guard tools; other ruff configs; Part 2 interaction.
