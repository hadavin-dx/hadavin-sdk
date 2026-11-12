# Lane 13: long unbroken name in the lead side panel (BUILDER; fresh egm reviewer reads it next)

Base: public branch pr-3-tests head **0841f36d1edf381b67a0da4793afacf834a36707** (verified with git rev-parse in a fresh clone; the brief first said 558d37f, then 2ce1f98, then 0841f36: I rebuilt everything on 0841f36). Tools: python3.12 venv outside the tree, `requirements-dev.txt` installed with --require-hashes, then `pip install playwright==1.63.0` (NOT hash-locked: evidence-run install), chromium from /opt/pw-browsers. No commit, no push.

## Failures and uncertain (first)
1. **Pillow is missing in my venv** (not in requirements-dev.txt on this head; the lane-8 docs-and-deps patch adds a browser requirements file). So `test_the_sidebar_column_is_one_colour_to_the_page_bottom_at_1100[light|dark]` in tests/test_portal_lead_pages.py fail with `ModuleNotFoundError: No module named 'PIL'` both on the OLD and the NEW css (2 failed, 89 passed before; 2 failed, 93 passed after, the 93 = 89 + my 4). Not caused by this change; I did not install Pillow (outside the brief's install list).
2. **390 px Leads page horizontal overflow is PRE-EXISTING and NOT fixed here** (scope rule). Control with harmless names only (long row removed from the DOM, 3 ordinary names): document scrollWidth 632 vs clientWidth 390, light and dark; identical with the hostile row present. Cause seen: the summary strip (`.sumstrip`) and the search toolbar (`.toolbar`, `label.search`) start at x=232 (the sidebar stays 232 px wide at 390 px) and are 400 px wide, ending at 632. Different CSS, different bug; it needs its own lane.
3. Control for the 390 px panel with a normal name: no overflow in the panel (head 389/389).
4. My "harmless-only" page control removes the long row from the DOM of a running page instead of starting a desk without it (same numbers 632/390 either way for the document; I did not run a second desk).
5. Not checked: other places where a long unbroken name appears (Needs a person cards, Request log, Overview feed, confirm dialogs). Lane 12 saw no overflow of the page there at 1280 px, I did not re-measure them at other widths. RTL/zero-width names are refused by the desk, so not testable.
6. The two "normal name" screenshots before/after show different rows (the lead list order differs between desk restarts), so they are not pixel-comparable. The same-row proof is evidence-5 (measured on the 558d37f tree, same CSS lines as 0841f36 which are unchanged between the two heads): with the fix loaded, then the two new rules overridden inline back to the old values, h2, chip and close-button rectangles are identical for all 3 names, light and dark.

## Reproduction (OLD css, 0841f36; evidence-1, probe-before.json)
200 x "W" name (made-up, example.test), unmasked, panel opened, 1280 px: `.drawer-head` scrollWidth **4346** vs clientWidth 599 (lane 12 saw 3097: its glyphs differ); h2 left edge at x = -3042 (cut off at the left), status chip right of the panel, close button squeezed from 36 to **32 px** and flush with the window edge (left 1248, right 1280, was 1220..1256 for a normal name). At 390 px: 4346 vs 389, h2 at -3932, close 358..390. Light and dark the same.

## The fix (src/lead_desk/portal/app.css, 3 lines changed, 1 file)
```
.drawer-head h2 { ...unchanged...; min-width: 0; overflow-wrap: anywhere; }
.drawer-head .pill, .drawer-head .icon-btn { flex: none; }
```
Choice: wrap, not ellipsis, because the rest of the portal handles long text by wrapping with `overflow-wrap: anywhere` (`.guard-val` line 150, `.kv dd` line 317); the table cell uses ellipsis only because it is a one-row cell and has no tooltip need in a heading. A wrapped title keeps the full name readable. `min-width: 0` lets the flex item shrink below its content; `flex: none` on the chip and close button stops them being squeezed (the first try with only the h2 rule fixed the overflow but left the close button 32 px wide: the test caught it, so the second line is needed).

## Numbers (same desk script, same posts; evidence-1 vs evidence-4, probe-*.json)
| case | OLD head sW/cW | NEW head sW/cW | OLD close button left..right | NEW close left..right |
|---|---|---|---|---|
| 1280 long, light and dark | 4346/599 | 599/599 | 1248..1280 (32 wide, flush) | 1220..1256 (36 wide) |
| 390 long, light and dark | 4346/389 | 389/389 | 358..390 | 330..366 |
| 1280 normal | 599/599 | 599/599 | 1220..1256 | 1220..1256 |
| 390 normal | 389/389 | 389/389 | 330..366 | 330..366 |
New long title wraps over 10 lines (h2 height 300 px at 1280, 600 px at 390); the panel body scrolls below it. Document scroll width unchanged (1280/1280 at 1280; 632/390 at 390 both before and after, the pre-existing item 2). Screenshots: before-*/after-{light,dark}-{1280,390}-{long,normal}.png. The long-name panels are readable but tall at 390 px (600 px of title); I judge it acceptable for a hostile 200-character name, not tested against the premium-UI bar beyond that (normal names are unchanged).

## Test (tests/test_portal_drawer_long_name.py, NEW file, 46 lines, 4 cases: light/dark x 1280/1100)
Uses the shared helpers by import (`_browse`, `_flow_rig`, `_new` from test_portal_lead_pages), posts a 200 "W" name through the in-process desk, unchecks the hide switch, opens the panel, waits 400 ms for the slide-in, asserts: head scrollWidth <= clientWidth + 1; close button width >= 35; close button inside the panel box and the window (1 px tolerance); then clicks it and expects the panel to go. Skips without playwright or browser (same `_browse`).
- OLD css: evidence-2: **4 failed** in 7.7 s (assertion on scrollWidth 4366/4346 vs 599).
- NEW css: evidence-3: **4 passed** in 6.6 s.
- Mutation (fix reverted in app.css, same tree): evidence-7: **4 failed** again. Fix restored afterwards (patch is built from the fixed state).
- Other portal browser files (one pytest process): evidence-6a OLD css: 2 failed (Pillow, item 1), 89 passed; evidence-6b NEW css + new test: 2 failed (same two), 93 passed in 142 s.
- evidence-8: `ruff check` and `ruff format --check` on the new test pass; tests/test_hygiene.py 9 passed, 1 skipped (the skip is the gitleaks scan: no gitleaks program here; I did not run it). The new file has no absolute path and no personal name.

## Overlap (evidence-9-apply-check.txt, fresh clone of 0841f36)
My patch touches only `src/lead_desk/portal/app.css` (lines 331-332) and the NEW file `tests/test_portal_drawer_long_name.py`. `git apply --check` alone: OK. Against every patch in triage/ and fixes/docs-and-deps(.patch, -v2.patch) in both orders: no conflict with any (none of them touches app.css or my new file; docs-and-deps edits tests/test_portal_lead_pages.py sidebar region, I do not). Patches that fail alone on 0841f36 (codeant-gitleaks*, extra-demo-only, js-portal, py-retry, docs-and-deps, docs-and-deps-v2) fail without mine too: they are already in the head or were written against 558d37f; that is not caused by my patch. Not done: nothing in docs/tests.md lists test files here as far as hygiene showed (hygiene passes); the lane-8 patch edits docs/tests.md, no conflict seen by apply-check.

## Files
drawer-long-name.patch (against 0841f36, git diff, 2 files, +48 -1), SUMMARY.md, evidence-1..9 (command on the first line of each), probe-before.json, probe-after.json, evidence-5 (558d37f tree, same-row A/B), screenshots. Probe scripts: /tmp/work/l13-scripts/. Rules used: R-numbers not looked up (the private studio bible is not available here); rules 6, 7, 13 (EGM review of the result is the lead's step: I did not self-review), 19 applied.
Cleanup: desk reset via scripts/reset.sh after each phase; pgrep for lead_desk|fakes_server|chrom shows none of mine.
