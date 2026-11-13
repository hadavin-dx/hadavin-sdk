# Lane 3 fix 4, round 4 (B4d): remedy text names what the Leads list shows (documents + pinning test; no product code changed)
Base f3c39cf89ec989f032ea48a23cfd824b88da9c68; started from lane3-fix-4-r3.patch (improved, not restarted). Worktrees: /home/user/work/b4d-base (plain, `git add -A`, nothing committed), /home/user/work/b4d-stack (claims stack + for-stack r3 + r4 delta). Python 3.12.3 (final-venv). Made-up data only.

## Failed / not checked (read first)
* JS lower-casing was READ and ALSO run with node v22.23.4 (/opt/node22/bin/node, no browser): raw/b4d-node-lower.txt: "STRASSE"->"strasse", "ISTANBUL"->"istanbul", "SAM"->"sam", and ß ı ſ are unchanged. portal/pages/leads.js lines 27 and 94 call `String(...).toLowerCase()` (verified by grep). What was NOT run: the real portal in a browser (the 4 browser tests are skipped here, playwright absent). So "the portal shows ..." rests on the two code lines plus node's rule, not on a rendered page.
* gitleaks absent (4 hygiene skips, as in r3). ruff, mypy, bandit: CI only (not run). README/limits.md lines are long single paragraphs (existing style; limits.md longest line already 1636 chars); no rule found for Markdown line length.
* Documents say nothing about Windows or other Python/Node versions: all behaviour is Python 3.12.3 and Node 22.
* The README now still names the three pairs twice (the definition, then the on-screen forms in the remedy sentence). The reviewer asked to cut the repeat to one sentence plus a pointer; the remedy sentence is that one sentence, but the first listing (the definition) remains by design.
* Not mine: `# noqa: S603` at tests/support.py:112 (fix-5).

## Items
| Item | Fixed how | Verified how |
|---|---|---|
| MAJOR 1 remedy | README "Same lead" bullet and docs/limits.md "What to do": two entries "whose addresses look the same except for one rare letter: `straße@…` next to `strasse@…`, `ıstanbul@…` next to `istanbul@…`, `ſam@…` next to `sam@…` (the portal shows every address in small letters, so a capital spelling appears as the plain letters). The desk does not merge them." | New test `test_remedy_names_what_the_list_shows` (2 places x 4 phrases). |
| m1 | Comment in `test_other_forms_stay_apart`: the bracket form is accepted only while the domain check leaves brackets alone; lane3-fix-8 text says "Not checked: ... an IP address in square brackets after the @". I READ evidence/lane3-fix-8.patch and notes (docs line 3b) and ran the file on r4+fix-8 (raw/b4d-other-trees.log): claim agrees. | Run on base+r4+fix-8: 88 passed. |
| m2 | README remedy cut to one sentence + "See docs/limits.md for the other letters." (the long second listing and the second sentence of three examples are gone) | text only |
| m3 | README letter sentence: "(see docs/limits.md for one more case, a Greek final sigma)" | New test `test_readme_points_to_the_limits_page` |
| m4 | TRUE: check_payload accepts both spellings for µ ŉ ǰ and οδος.x / ΟΔΟΣ.X (probe run first; note the capital of ŉ is two characters `ʼN`, of ǰ is `J` plus a combining caron). `test_other_rare_letters` now asserts acceptance and two different keys. The docs wording "behave the same way" stays true. | passes; was not asserted before |

## Fails-before (old wording, new test file) raw/b4d-fails-before.log
r3 documents + r4 test file: 2 failed, 25 passed [exit 1]: `test_remedy_names_what_the_list_shows[README, definition of Same lead]` and `[docs/limits.md]`. Per-place mutations on the r4 tree (raw/b4d-mutation-summary.txt): in each of README and limits, reverting the ſ pair to `SAM@…` = 1 failed; removing "shows every address in small letters" = 1 failed; removing the README pointer = 1 failed (after I added the pointer test; first run showed the pointer was unpinned, 27 passed, which is why the test was added). The m4 acceptance assertion has no old-code failure to show: it asserts current true behaviour (not a regression of code; it pins it).

## Evidence (raw in evidence/raw/)
* Test file on patched tree: 28 passed [exit 0] (b4d-pass-patched.log, written before the pointer test was added; after adding: 28 passed, shown in the run recorded by the final full suite).
* ONE full serial suite on the final plain tree: `3711 passed, 200 skipped in 1229.40s`, EXIT_CODE=0, WALL_SECONDS=1230 (b4d-full.log). The 200 skips are the existing ones.
* Added lines over 120 characters in the test file: 0 (counted in characters). `noqa` / `type: ignore` added: 0.
* Apply checks (raw/b4d-apply-check.txt), all rc 0, on f3c39cf8: A r4 plain; B r4 then fix-8; C fix-8 then r4 (both orders OK, no conflicts; fix-8 touches contract.md and docs/limits.md in other hunks); D claims stack + for-stack r4; E stack + for-stack r4 + fix-8; F stack + fix-8 + for-stack r4.
* Tests on the trees of B, E, F (email case rule + domain labels + hygiene): 88 passed, 4 skipped each [exit 0] (b4d-other-trees.log). The FULL suite was run only on the plain tree.
* for-stack r4 was built as: stack tree + for-stack r3 + the r3-to-r4 delta (README, limits, test), then diffed against the stack-only tree; contract.md and docs/tests.md hunks are the same as r3.

## Rung table
| Component | Rung | Why |
|---|---|---|
| Remedy wording | 1 reuse (existing README/limits text, edited) | no code |
| Pinning tests | 1 reuse (existing `_line`, DOC_PLACES helpers, `check_payload`) | no new helper beyond two small tests |
| Node check | 1 (tool on the machine) | evidence only |
No custom code, no product code changed.

## sha256
b4bbb734311c787538bbccda3051d57b68fbfee204e3dd0dd90405e334e4f45d  lane3-fix-4-r4.patch
0a10a3659d240c79adc7414088517268121b7b5bddef5792a36e49256bcb2c63  lane3-fix-4-for-stack-r4.patch
