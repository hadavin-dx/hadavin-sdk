PR H report. WP2a and WP2b are committed and pushed. WP2c is only partly done, and WP3 and WP4 are not started. The plan's "no step back" promise (everything main masks, the branch also masks) is not kept, and I did not redesign around it.

**Not done, and why**
1. **T1 generator tests (WP2c) are not committed.**
   - `test_no_step_back` and `test_not_promised_counts` are red.
   - After my fixes below, 517 (case, path) pairs are masked on main but not on the branch. Before the fixes it was 809. Evidence is in `/home/user/build/checkpoints/PRH-WP2c-stepback-evidence.txt`.
   - Biggest clusters (root cause from my diagnosis; not tested by a fix):
     - ESC + space + a value: the sequence grammar reads the value's first letter as the last byte of an nF sequence. Example: `id` + ESC + space + `AKIAIOSFODNN7EXAMPLE` comes out as `id KIAIOSFODNN7EXAMPLE` on every path. The approval card's own cleaning now uses the same grammar. This is a real leak of 19 of 20 key characters where main masked the key.
     - Direct `redact()` callers, about 150 of the 517. They read only sequences. The ticket says "direct callers included", but the design cannot give that.
   - The WP1 grammar needs a decision from the lead (for example, do not consume an alphanumeric final byte of an nF sequence). I did not touch it.
   - The T1 code is saved as `/home/user/build/checkpoints/PRH-WP2c-T1.patch` (base de5e1c24), and also in stash@{0} in the worktree.
2. **T5** (`tests/test_prh_regressions.py` and `tests/fixtures/prh_regressions.json`) is not started. The extraction covers about 15 review and probe files.
3. **WP3** (mutants, CI step, perf test) and **WP4** (CHANGELOG, SECURITY.md, docstrings, full suite) are not started. They need T1 and T5. Bandit was run once on the tree: no findings printed, but I did not capture its exit code.
4. **Not run:** perf and the full suite. I did not use my own Postgres at all. Time boxes were exceeded, and I wrote no 30-minute checkpoint notes during WP2c. One note is at `/home/user/build/checkpoints/PRH-WP2c.md`.

**Commits** (all on `core/prh-strip-hidden-controls`, pushed fast-forward de5e1c24..adf69605)
- **WP2a:** `de5e1c24`, pushed earlier.
- **WP2b:** `c59a421a`.
  - Changes: `tools._scrub`, `_decoded`, `_sanitise` and `_first_decoded`; `runmap.gap_pattern`; tests `tests/test_prh_tools.py` and `tests/test_prh_grounding.py`.
  - Also includes two fixes to `redact_text` found by the generator (next section).
  - Fail-before: `/home/user/build/PRH-fail-before-WP2b.txt`.
- **WP2c partial:** `adf69605`.
  - Contents: `tests/record_prh_main.py`, `tests/fixtures/prh_main_verdicts.json` (re-recorded from main; the percent-encoding fix is in), `tests/fixtures/prh_main_corpus.json`, and `tests/test_prh_clean_corpus.py` (T6, 63 tests).
  - Fail-before for T6: `/home/user/build/PRH-fail-before-T6.txt`. The ids `mf_cp1252_c1` and `mf_nroff_overstrike` fail on main; the other 61 pass on main.

**Deviations and findings**
1. **Views of the original text (my fix, in the WP2b commit).**
   - The views were built from the original text, so a string terminator (ESC + backslash) followed by `n`, `t`, `r` or three digits was read by the decoders as an escape.
   - Example: `password=hu` + OSC + terminator + `nter2secretXYZ` leaked `ter2secretXYZ`.
   - Fix: views now come from the joined reading.
   - Test: `test_mf_string_terminator_backslash_does_not_cut_the_value`. It fails on main (60 failed) and on the branch without the fix (40 failed): `/home/user/build/PRH-fail-before-WP2a-fix.txt`.
2. **Approval card cleaning (my fix, in the WP2b commit).**
   - The card's cleaning deletes control characters before any value is looked for, and main relied on that. That cleaned text is now one more reading in `redact_text`, appended last and shape-checked (`_no_created_shapes`). The same applies to the cleaned form of each decoded view.
   - Masks found by an accepted reading are now carried into the readings still to come: `make_pairs` is rebuilt after each accepted view. Without this, a later reading replaced the output and lost earlier masks. That showed as `tests/test_k5_round12_fuzz.py::test_no_fragment_of_an_encoded_secret_value_survives_any_producer` failing on the first 43-file run (183 leaks); it passes now.
   - Test: `test_card_masks_a_value_cut_by_a_character_the_card_deletes`. It passes on main, so it is a guard rather than a must-fail test.
3. **Direct `redact()` path:** a glue space can now appear inside a value there. The plan does not promise it.
4. **Item counts differ from the ticket:** the generator gives 99 items and 4851 pairs; the ticket says 95 and 4465.
5. **Fixed-length value swallow:** I found this case earlier and did not re-check it this session.
6. **`tools._scrub`:** I added one rule beyond the ticket. It withholds when the count of markers written is lower than the joined scrub would have written (token-cut percent encoding leaked without it).
7. **`test_mf_` / `mf_` naming:** the T6 cases that fail on main use `mf_` param ids. U+2028 is left out of the card test because main leaks it too ("not promised" row N3).

**Evidence on the pushed head** (`adf69605`; tests run on the same tree as `c59a421a` plus the recorder and fixtures)
- `PRH-43.sh final2-wp2b` (the 43 redaction files plus the steps, wiring, spans, tools, grounding and clean-corpus test files): `9515 passed, 1 skipped, 22 deselected in 144.90s`, `rc=0`. Log: `/home/user/build/PRH-final2-wp2b.log`.
- `ruff check`: All checks passed. `ruff format --check`: 334 files already formatted. `tools/scan_repo.py`: no findings printed. gitleaks: no leaks found, run after each commit.
- The earlier 43-file run failed on the fuzz test above; it is in `PRH-final-wp2b.log` (`rc=1`).
- `test_prh_contract.py` was not in that run. Its T1 part is stashed.

**What the evidence runner must check**
- Re-run the fuzz test and the 43 files on the final head, with `test_prh_contract.py` at its WP2a state.
- Confirm that every `test_mf_*` and `mf_*` id fails on a clean main checkout, and that all other tests pass there.
- Check the two `redact_text` changes for perf: the extra readings only run when hidden items are present. Gate G1 to G3 are not measured yet.
- Review the step-back evidence file and decide the grammar question (nF final byte) before T1 is committed.

The worktree is clean at `adf69605`. I started no background processes that are still running.