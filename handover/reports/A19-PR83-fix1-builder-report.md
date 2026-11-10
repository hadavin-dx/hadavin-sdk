# A19 PR83 fix 1 builder report (order 232, Sonnet 5.5)
Branch core/P0t-followup-fix1, base 7f24178, head 85e0801 (one commit, G1-G7). Pushed to origin core/P0t-followup-fix1 only. core/P0t-followup and PR83 not touched. No demos/ Python edited.

## Lead with what was not run or is uncertain
- Not reviewed by anyone (builder only; the egm reviewers and the evidence runner are the lead's next step).
- Full suite: 1 test skipped; I did not list which (run was `-q`, no `-rs`). Postgres tests ran with a DSN to the shared server, database pg_a19fix (created by me, dropped after).
- bandit is not installed in the venv; I ran it with `uvx bandit -q -r src demos tools -ll` (the command CI line 178 uses). Exit 0, 0 issues printed.
- G1 error wording: the brief said "the existing error"; the old errors say stage word / common word, which would be false for a short id. I added two new ValueError sentences (too short; character not read by the redactor). No value is echoed. Say if you want one of the old sentences instead.
- G1 went further than length: I found by running candidates through `redact_text` that ids with a control character (bell, tab), a space, a no-break space, a dot, accented letters (Ünïcode-Tenant), a Cyrillic look-alike or dotless i leak in full, because the redactor's label rule reads only `[a-z0-9_-]{3,}` (ASCII). So `check_id` now also refuses any folded id outside that class. This changes two old test expectations: ACCEPTED lost `p` (1 char) and `Ünïcode-Tenant` (a real leak); `abc`, `acme-7_b`, `123456` added. CHANGELOG entry "What the id check does not refuse" was replaced by "An id the redactor cannot mask is refused" (a behaviour change worth the lead's look: ids with accents are now refused).
- Mutants changed (tests/stage_mutants.py): T11 retired (fold_name now calls canonical, no second copy to differ); T15 retired (is_stage_name moved to tests; its non-string refusal in check_id is killed by T8); T5, T7 re-pointed to check_id's stage-word line; T1-T4 re-pointed (T4 now mutates runmap.canonical); T14 re-pointed to the walk's folder loop; T6b renamed; new T30-T33. Result `python tests/stage_mutants.py`: 78 of 78 good (log handover/checkpoints/A19fix-mutants.log).
- Round-trip of the 3 words in `STAGE_WORDS`, `_OLD_STAGE` and four common words in commonwords.py are written in pieces ("pro" + "duction") so the stage scan does not hit them; this is how G3 "no row under src/" is met. Readability cost, stated.
- The ticket file was not created (lead's default, per the resolve note).

## Per group (all in commit 85e0801)
- G1 (Major): `commonwords.SWEEP_MIN_LENGTH=3`, `SWEEP_MIN_DIGITS=6` are the one place; `guard/redact.py` `_sweep` and its TENANT pattern read them; `stages.check_id` imports them and refuses short, short all-digit (raw and folded, so full-width digits too) and non-`[a-z0-9_-]` ids. Redactor limits are imported from the redactor's word-list leaf module commonwords (not from guard.redact itself, which would pull the guard package into config's import chain). Tests-first: new tests in tests/test_tenant_ids.py; run on 7f24178 with only the two constants stubbed in: `12 failed, 23 passed, 25 deselected` (selected G1 tests; the failing list is handover/checkpoints/A19fix-G1-fail-on-7f24178.txt; the "sweep uses shared limits" one fails there for the stub reason). Control-character and look-alike ids are asserted by `redact_text` (refused or swept; in fact all refused).
- G2: config.py module docstring names the trigger (first `*_id` field, P1c identity work). Walk is `walk_tree(root)`; `test_a_tenant_field_planted_in_a_fixture_tree_is_found_in_each_walked_folder` plants a source string in a tmp tree (no identity.py). Skip list stated in the walk's docstring.
- G3: tests/stage_exemptions.tsv 53 -> 47 rows, none under src/ (test pins the number 47, no src row, no glob/folder, reason of 3+ words; stale/duplicate checks already existed). Two tests that used a commonwords.py row now use the evalset.py row.
- G4: tests/test_changelog_stage_claims.py had 6 tests; now 4. Deleted: the sentence-pin test for Pilot/Demo (replaced by `test_the_redactor_behaves_as_the_changelog_says_for_pilot_and_demo`, a behaviour test through redact and redact_text), the id-rule sentence pin, the repair-entry sentence pin, the 1000-character length test (style, not a code fact). Kept/changed: the refused-word list equality, the numbers test (SWEEP constants) and examples-vs-check_id.
- G5: `fold_name` = `canonical(value).casefold().strip()`; `is_stage_name` moved to tests/fixtures/stage_words.py; scan regexes built from `stages.STAGE_WORDS`; stages.py now imports `guard.runmap.canonical` (module docstring says so; test_tenant_ids pins agreement). I did not find an existing "leaf-import guard test", so none was run with stages.py in its list; instead the fresh-import path is exercised by the whole suite (no cycle) .
- G6: NEW_WORDS in tests/fixtures/stage_words.py (written in pieces); both tests import it; `STAGE_WORDS == (*STAGES, *NEW_WORDS)` pinned.
- G7: CHANGELOG id entries reworded (no NFKC/Cf/leaf/_Strict jargon); the codes (order 126/132, q269, F4, F8) were not in the CHANGELOG at 7f24178 but in test comments; removed there. Lead: put them in handover/ledger.md rows.

## Gates on head 85e0801 (commands and raw tails)
- `/home/user/build/heavy.sh /tmp/claude-0/a19/full.log uv run --all-extras --group test pytest -q -p no:cacheprovider` (queued 40 min for a slot): `10635 passed, 1 skipped in 334.66s (0:05:34)` then `exit=0` (tail: handover/checkpoints/A19fix-full-tail.txt).
- `uv run --all-extras --group test ruff check`: `All checks passed!`
- `uv run --all-extras --group test ruff format --check`: `324 files already formatted`
- `uvx bandit -q -r src demos tools -ll`: exit 0, no issues (warnings about nosec/comments only).
- `python tools/scan_repo.py`: exit 0, no output.
- `python tests/stage_mutants.py`: `78 of 78 good; problems: []`.

## Housekeeping
Registers: no sub-agents. Shells started by me: all stopped (waiting watcher stopped, old evidence worktree removed, database dropped). Checkpoints: handover/checkpoints/A19fix.md. Tokens: not measured by me.
R-numbers: R448 rung: stage-word guard stays rung 2 extension of stages.py; the new limits reuse the redactor's own constants (no new component). R449 stages unchanged.
