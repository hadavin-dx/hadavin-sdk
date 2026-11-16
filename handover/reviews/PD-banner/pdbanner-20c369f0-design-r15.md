# PD Part 6 round 15, design review (egm-design a54db384), head 20c369f0

Condensed by the lead from the reviewer's inline report. Snapshot: /home/user/build/snap/pdbanner-20c369f0/. The reviewer judged batch 15 from files/ and DIFF.patch (the 449 KB delta was not read whole), ran nothing and read no builder report. Verdict: 0 Blocker, 4 Major, 6 Nit. Round 16 required. No fail-open path found in the banner (Python and page side), the guard refusals or the helper.

## Major
- M1 CHANGELOG.md:229 still says a token of 11 characters or fewer after a bearer word stays visible "as in the core"; false: `Bearer a1b2c3` is hidden (demo_only_guard.py:399-407, and line 223 says so). Line 223 itself over-generalises (true only for letters-only tokens). The banned-phrase test (test_changelog_numbers.py:313-331) does not ban "stays visible, as in the core" and only scans the masker paragraph. Fix: "a letters-only token of 11 or fewer after a bearer word, or 7 or fewer after a basic word, stays visible"; make line 229 point at the one paragraph; extend the banned list.
- M2 "The ONE place the project starts a program" (tools/fixed_run.py:1, tests/fixed_run.py:3-5, CHANGELOG:221) is false: FOLLOW_UP_DIRECT_STARTS (test_demo_only_guard.py:3563-3573) lists 9 files with 22 direct starts. Reword to "the one starter for the guard, scan_repo and the tests moved onto it; nine files still start programs themselves". (Related fix-don't-defer: migrate them or justify.)
- M3 demo_only_guard.py:439-440: `--bypass=abc123secret`, `git.bypass=<token>`, `x-bypass=<token>` are shown (name scan includes `-` and `.`, then `name.lower() == "bypass"`), against the ruling "hide unless a plain boolean with nothing after it". Fix: apply the bare-word rule to any name whose last segment split on `. - _` is bypass; add rows for `--bypass=abc123`, `a.bypass=abc123`, `--bypass=true`. (Reviewer did not read the core: whether it hides `--bypass=abc` is unknown.)
- M4 test_changelog_numbers.py:255-304 / CHANGELOG:223: "HIDES MORE than the core" is not proven for `authorization=Bearer abcdefgh` and `authorization=Digest username="a", response="b"` (core_changes=True; the test compares only `redact(text).text != text`). Add a column for the substring the core leaves visible (and, for "shows what the core hides" rows, the substring it hides).

## Nits
- N5 CHANGELOG:223 name-word list omits `passwd`, `pwd` (code `_SECRET_NAME` line 356); "address" vs "URLs" naming.
- N6 CHANGELOG:222 `LATER_ASSERT_RUN` "each of which was run and killed" is a process claim; remove or pin by test.
- N7 comments demo_only_guard.py:321-348 still ragged hard-wraps; lines over 100 columns remain (tools/fixed_run.py:42 about 102; demo_only_guard.py:455, 1210). The one marker `# noqa: S603 - the shape is checked above: ...` has the separator and names the shape.
- N8 test_demo_only_guard.py:3576-3600 `_program_starts` misses aliasing (`x = subprocess`), asyncio.create_subprocess_*, pty.spawn, `__import__`, and does not scan demos; say it is a lint sweep, not a boundary.
- N9 templates/mode-banner/mode_banner.js:3 header shape omits `overridden`.
- N10 marker-count test counts four files only; whole-diff count stays the authority (reviewer found only the one added S603 at tools/fixed_run.py:42; removed: BLE001 app.py:434, S607/S603 at old git calls).

## True (reviewer)
fixed_run contract shape-only and honestly worded; the one marker is on the starting line; five masker passes match; bare `bypass` rule for the plain name; stage names demo/pilot/prod plus LIVE display word; copy-run messages reachable and honest; CI guard steps have no continue-on-error; six READ_ERRORS sites match CHANGELOG:219.
