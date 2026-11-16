<!-- full hand-back report of sub-agent a02708cc, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW round 2, implementation readiness, PR H rev 2

Plan: /home/user/build/snap/prh-plan-r2/tickets/PRH-strip-hidden-controls-at-the-choke-point.md (632 lines read in full). I also read both stubs, evidence/README.md, di-312-313.out, the range file, scripts/di312.py, scripts/fixes.py, and the round-1 readiness review (partly). I read `/home/user/build/heavy.sh`. Main source is `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/`. Note that the directory is 2a8c2aa (7 characters) and the plan says 2a8c2aac. This is harmless.

VERDICT: NOT READY, 0 Blockers, 9 Majors, 9 Minors, 4 Nits. The two round-1 Blockers are answered by the text. Case 790 is diagnosed with a design change, and the commit order is now stated as green per commit. Neither is verified, though (see M7). A fresh Sonnet builder can start WP1 today, but only after making three guesses: the string-sequence rule, the scope of `strip_sequences`, and the environment setup. WP2 as written cannot be finished by a builder who has only this ticket (M3, M4).

## What I confirmed in main (grep and read)

Line numbers and names are real for these:
- **redact.py:** `_ANSI` 820-822 and `strip_ansi` 825-838. Its call sites are 877, 920 and 1254. `_Redactor.find` is at 919, and `redact` is at 862.
- **runmap.py:**
  - `nfkc` 103, `undo` 141, `_within_cap` 175, `fits_after_nfkc` 197
  - `canonical` 276-282, `_canonical_view` 285, `replace_canonical` 298
  - `escape_placeholders` 322, `_MARKER` 330, `escape_markers` 333, `neutralise_untrusted` 340
  - `_clean` 395, `_views` 401-414 (and `_clean` inside it at 411), `_held` 417, `MAX_DECODED_MASKS = 256` at 423
  - `_decoded_masks` 426, with the `InputTooLarge` raise at 441-442
  - `_keep_earlier_masks` 455 (list order), `redact_text` 464-526 (steps and line numbers as described in 2.2), `safe_head` 532, `redact_bounded` 554, `redact_value` 568
- **tools.py:** `_decoded` 726, `_sanitise` 730 (NUL to U+FFFD), `_first_decoded` 786, `_decoded_clean` 794, `_scrub` 898, `_scrub_layers` 906, `prepare_output` 936, `redact_layered` 976, `error_reason` 987. `_sanitise` is called a second time at 1194 and the digest line is 1197.
- **defaults.py:** `MAX_REDACT_CHARS` 38, `REDACT_BUDGET_S` 49.
- **Other callers:** gate.py:74, 125, 162, 197, 205 and 212 match. evidence.py:57, 87, 88, 154 and 191 match. The callers in judge.py:71, bedrock_guardrail.py:98, channel.py:29 and 36, slack_channel.py:81, evals.py:63, k1b/redaction.py:188, agent_loop.py:412 and 534, and tick.py:292 all match.
- **Acceptance 8:** `guard/__init__.py` imports egress, injection and redact, so the expected `sys.modules` list is plausible.
- **Counts in the plan's tables:** I recounted these from the plan's own definitions. 55 removed, 9 space-like and 95 items are correct.
- **Machine facts:** `/home/user/build/heavy.sh` exists and uses `/tmp/heavy-slot-{1,2,3}.lock`, which matches acceptance 4. `/home/user/build/bin/gitleaks` exists. A `.gitleaks.toml` exists in `/home/user/build/prh-author/main/`. The queue scripts are absent, as the plan says.

## Unicode data file and hash pin

- **Ranges and count.** The file has 1 header line and 17 range lines, ascending, as W6 says. I summed the range lengths by hand: they give 4,174 code points. That is the claim, and the ranges match my memory of Default_Ignorable_Code_Point (the same ranges apply in Unicode 15.0 and 15.1).
- **Hash not recomputed.** The SHA-256 `b14f5d75…57f6` is the same string in the plan (W6) and in `evidence/di-312-313.out`. I could not recompute it, because I have no shell. The check is offline and trivial: `sha256sum` on the file. The hash also depends on the exact bytes, meaning the header text and the trailing newline. The builder must copy the file byte for byte (`cp`), and the plan should say so.
- **Reference-material test.** The deny-list test hashes tracked files and compares them with the listed hashes (fact 19, author's reading; I could not read the test). A hash constant inside a .py file cannot match a file hash, so pinning it in the unit test is safe against that test. Putting the hash into `reference_material_sha256.txt` would trip the test, so the author's decision is right.
- **scan_repo and gitleaks, not checked.** `tools/scan_repo.py` and the gitleaks rules were not in the export. See M8.
- **Equality test in oracle (c).** It needs the Other_Default_Ignorable ranges, which are not in the ticket (M9). The "from-memory rule" exists only in `evidence/scripts/di312.py`, line 2.

## Findings

### Major

**M1. W3 contradicts the code and the prototype on `_first_decoded` (W3 lines 362-363; mutant 33; 8.2 row FD).**
- W3 says `_first_decoded` has "NO change". Main's `_first_decoded` (tools.py:786-789) calls `_decoded(char)`, not `runmap.undo`.
- W3 also changes `_decoded` to the stripped decode. A builder who follows "NO change" therefore makes `_first_decoded` use the stripped decode. This is exactly the regression the plan says must not happen, and it is the one mutant 33 kills.
- The prototype did edit it (`evidence/scripts/fixes.py:80` rebinds `_first_decoded` to `runmap.undo(ch)[:1]`).
- Fix the text to say: edit `_first_decoded` to call `runmap.undo(char)[:1]` directly.

**M2. The reader grammar in 4.1 leaves design choices to the builder (lines 291-305), and the whole of WP1 hangs on it.**
- **String sequences.** The "body" is "anything" and the end is ST, BEL, CAN or SUB. The "never ended" row says the sequence ends at the next line end. The two rules conflict.
  - If a terminator exists after a line feed, does the sequence run past the line?
  - If the reader scans ahead for a terminator, an unterminated opener repeated n times is O(n²). That would break the "one pass, linear" claim. A state machine that ends at the line end avoids this.
  - The plan must state it: the body cannot contain U+000A or U+000D, so the string ends at whichever of the terminator or the line end comes first.
- **Opener inside a string.** What happens to ESC followed by `[`, or any ESC not followed by a backslash, inside a string? Main ends an OSC at any ESC. The grammar says "anything".
- **Scope of `strip_sequences`.** Line 273 says single control characters outside a sequence "stay". The grammar rows "lone ESC: removed" and "CSI aborted by CAN/SUB: both dropped" say otherwise. Main's `strip_ansi` leaves a lone ESC (2.3 table). Is a lone ESC in a sequence-only reader a "sequence" or not? The answer decides what `find` and the approval gate see.
- **Oracle for `strip_sequences`.** T10 checks `strip` against the oracle, but names no oracle for `strip_sequences`. State the rule: it is `strip` restricted to the sequence families, plus the glue rule.

**M3. T5 (and the T1 sources) need inputs the builder does not have (line 435).**
- The sources named are `reviews/PR77/round5-*.md`, `round6-*.md`, `round7-*.md` and the two full reports.
- Also named: `evidence/PR77/97fd202/probe-5ab`, `probe-5c` and `probe-5d`, sweep F1-F4, and "L1 to L12 ... M3a to M3d".
- None of these is in this snapshot (only `reviews/` has plan-r1 files) and none is quoted in the ticket. The builder cannot cut "every input" from files it cannot read.
- Either quote the inputs as parts-lists in an appendix, or state where the files live and add them to the brief.
- Read-first item 5 admits the inputs of rounds 5 and 6 were not re-read.

**M4. Tests are not mapped to files, and the mutant killers are not named (lines 412-451, 477).**
- **T3, T4, T7 and T8 have no file.** The file list has unit, contract, regressions, clean_corpus, grounding, tools and perf. The commit split says commit 1 holds the "gate set test (T8)", but T8 also contains card tests that must FAIL on main.
- **Acceptance 7 gives the pass criteria by category, not by test id.** Acceptance 7 runs five files and requires "every test in the must-fail list is FAILED". The runner cannot check that without node ids or at least a naming rule.
- **No killer tests are named.** Line 451 says each of the 37 mutants has a "named killer test and expected line" and then lists none. The builder must invent all 37 mappings.
- **Some mutants may be unkillable.** Mutants 35 and 36 (`_refuse_forgery`) are described as a backstop that "never fired" in prototype runs. Unless a test builds a stand-in that makes it fire, `37 of 37 good` is unreachable. No such test is listed, and nothing tests `_refuse_forgery` directly. Mutant 31 (`_scrub` returns the joined text) also needs a case whose only distinguishing signal is a boundary the joined text loses; none is named.
- **Mutant runner format.** The runner's format is said to be "same shape as `tests/migration_numbers_mutants.py`", which I could not check (tests are not in the export).

**M5. The cost gate in acceptance 9 is ambiguous and may be failed by design (4.4, 6.1 item 9).**
- **Which four shapes?** "The four shapes with no hidden item" is not defined. The table's candidates are plain ASCII, tab table, JSON, coloured output, Hindi and Persian. Coloured output has hidden items. Hindi is non-ASCII and has none.
- **Hindi may already fail.** The author's Hindi figure is 1.27 CPU against main's 0.80, a ratio of 1.59. That exceeds 1.25, so if Hindi is one of the four, acceptance 9 fails on the author's own numbers.
- **No unmeasured proof for the others.** The plan admits (line 406 and 8.5) that 1.25 for plain shapes is "NOT shown by any run".
- **No remedy.** The plan gives no rule for what the builder or runner does if the limit fails. It does not say whether to optimise, accept, or send the plan back to review.
- **Action.** Name the four shapes and state the remedy.

**M6. Environment setup for the builder and runner is incomplete, and some acceptance commands are not runnable offline as written.**
- **Placeholders in 5.1.** The recording command uses `<repo>` and `<branch venv>`, neither defined. The plan never gives the commands to create the branch worktree `/home/user/build/PRH`, the branch `core/prh-strip-hidden-controls`, or the venv.
- **Network and uv.** Acceptance 2, 3 (3.13), 4, 5, 6, 7 and 9 use bare `uv run --all-extras --group test …` in a fresh evidence worktree. With no external downloads and no `--offline`, `--frozen` or `UV_PROJECT_ENVIRONMENT` pointing at an existing venv, `uv` may try to resolve and fetch. Item 3's 3.12 branch does `uv sync --python /usr/bin/python3.12` with the same exposure.
- **`heavy.sh` and redirects.** `heavy.sh` runs `"$@"` as argv and has no shell. The commands with `> log 2>&1; rc=$?` and the `env -u …` prefix need an explicit form, such as `heavy.sh env -u … uv run … > log 2>&1`. Say it once.
- **Skip-list diff.** Item 3 needs a full-suite run on a main worktree for `skips-main.txt`. That run has no command, no slot, and no budget in 6.2.
- **Postgres.** The plan does not mention Postgres, so whether the suite needs a DSN or skips is unstated. The skip-list diff would show the effect, but nothing tells the runner what to export.
- **Evidence paths.** Paths like `handover/evidence/PRH-plan/target-files.txt` are used by the builder (the 43 files); this snapshot flattens them to `evidence/`.

**M7. Time boxes versus green-per-commit (6.1 commit split, 6.2, 6.3).**
- **WP2 is too big for 60 minutes.** WP2 is the core of the work: the `redact_text` rewrite, `_redact_stripped`, `_no_created_shapes`, `_refuse_forgery`, W3, T1-T3, T5-T8, T11, T12 and the main recording. That is a very large amount for one 60-minute box.
- **The stop rule conflicts with green-per-commit.** The brief says "at 60 minutes stop, commit, report". That would produce a red commit 2 in the common case, contradicting "at the end of every commit the WHOLE suite is green".
- **Green-per-commit is never verified.** Only the 43 files run at WP2, and the full suite runs once at the final head. Acceptance has no per-commit check. State that commits 1-3 are checked by the 43 files only, or say a WIP commit is allowed on the branch and squashed.
- **Impact of the checkpoint rule.** A "fresh agent resumes" rule is given, but not how an unfinished, uncommitted state is handed over.

**M8. scan_repo, gitleaks and invisible characters in committed source: late discovery risk.**
- The plan's own text and tests need literal invisible characters. Line 272 holds literal U+2028 and U+2029 in the `_ANY` regex, and the ticket uses literal U+FE0F, U+034F and U+200B.
- Nothing tells the builder to write all invisible characters as escapes in committed files. The regression JSON uses `{"cp": ...}`, but .py files do not.
- `tools/scan_repo.py`, gitleaks rules and the hash-constant naming (a 64-hex string beside a name containing "key" or "token" could trip a generic rule) are checked only at acceptance 5, at the very end. The rules were not in the export, so I could not check them.
- Add to WP1: write every control or invisible character as an escape (` `), never literally. Name the hash constant without key, secret or token words. Run `tools/scan_repo.py` and `tests/test_no_reference_material.py` after WP1.

**M9. The oracle's independent ignorable derivation cannot be built from the ticket (section 5 (c), line 414; section 1).**
- Section 1 describes the rule only as "Other_Default_Ignorable_Code_Point + Cf + Variation_Selector minus …". `unicodedata` does not carry Other_Default_Ignorable_Code_Point.
- The ranges are in `evidence/scripts/di312.py` line 2 (13 ranges) and the exclusion ranges in its line 6. That script also reads a missing `di-perl.txt` and is not referenced by the ticket.
- Put these lists in the ticket, or name that script as the source.

### Minor

- **m1. T1 pairs.** "Exactly 4,000 inputs … cycling through all unordered pairs of items" is impossible for 95 items: 95·94/2 = 4,465 distinct pairs, or 4,560 with same-item pairs. State which subset the 4,000 are.
- **m2. Pseudo-code line 334.** "`pairs = _decoded_masks(...) + _decoded_masks(...) (deduplicated) if readings else []`" is not valid code, and the dedup rule is unclear. `cache` is never defined (main has `cache = getattr(mapping, "redact_cache", None)`). The budget check before the first pass is not shown. "Budget before every pass" (section 3) is only in the view loop and in step 6 of `_redact_stripped`.
- **m3. `--from-ucd`.** The mode has no test and no offline sample. It must merge adjacent ranges, or it will not equal the perl file (for example 180B-180D, 180E and 180F becoming one range 180B..180F). Say so, or drop the mode.
- **m4. Oracle wording.** Line 414 says the oracle "imports nothing from `hadavin_sdk`" and also that the masked class is computed "by running the package's own `redact()` on the oracle's joined reading". The redaction call must live in the tests, not the oracle file. Say so. Also say that `record_prh_main.py` must not import `hidden`, which main lacks.
- **m5. Dict keys.** `redact_value` also passes dict keys through `redact_text` (runmap.py:593). Promise 4 covers "arguments" but not keys, which now lose controls. Tool-argument keys can change (schema validation). State it in the CHANGELOG list.
- **m6. T12 digest.** Line 1197 is `ctx.digest() or hashlib.sha256(...)`. The recorded digest comes from `ctx.digest()` when a context digest exists. The claim "the digest changes" holds only in the fallback path. T12's stand-in must not set a context digest.
- **m7. Existing tests.** Acceptance 1 forbids any other file, and acceptance 10 forbids editing the listed existing tests. No rule says what to do if another existing test (say one asserting U+FFFD for NUL or lone-ESC survival through `strip_ansi`) fails. The 43-file prototype run suggests none does, but that was a monkeypatch.
- **m8. Gitleaks and flock.** `gitleaks git --log-opts` needs a recent gitleaks (8.19 or later). I could not run the binary to check its version. The item 4 busy check `flock -n … true` is racy.
- **m9. Python versions.** The test (c) equality is checked on 3.12 and 3.13 only. A newer Unicode (Python 3.14 and later) may change the Cf set. Say which Pythons the project supports.

### Nit

- Header and 2.1 line numbers such as runmap.py:346-350 are off by one (the function is at 345).
- "WP1-WP4" appear only in 6.2. Say once that WP n equals commit n.
- The mutant list says "(or the real count if the builder adds mutants; never fewer)", which fits the text, but the CHANGELOG rule bans numbers not measured on the final head.
- Several rows (L2, L4, L10, F1d) depend on invisible literals that a reader cannot see. Express them by code point (for example `"️"`).

## Section contradictions and undefined terms

- **W3 versus main on `_first_decoded`.** See M1.
- **4.1 line 273 versus grammar rows 302-303.** See M2.
- **Open question 2 versus W1/W4.** Question 2 says `strip_ansi` delegates and the gate recognises more families, and W4 says there is no gate edit. This is consistent, but it makes the gate's `strip_ansi` import carry behaviour changes (card DCS payloads deleted). That is declared in W4 and T8.
- **The "four shapes with no hidden item" (M5), "named killer test" (M4), and `<repo>`/`<branch venv>` (M6)** are undefined terms.
- Terms "reading", "pass", "run", "find", "mask", "joined" and "spaced" are defined in section 3. Their later use is consistent.

## What I could not check

- **Test files.** `tests/` is not in the export. Not checked: `tests/test_no_reference_material.py`, `tests/fixtures/reference_material_sha256.txt`, `tests/test_k5_tools.py:306-317` (fact 17), `tests/test_k5_round12_fuzz.py` (seed 20261104 and case index 790), `tests/test_k5_producers.py`, `tests/warden_port/*`, `tests/fixtures/timing.py`, `tests/migration_numbers_mutants.py`, `tests/stage_mutants.py`, and the `perf` marker.
- **Non-source files.** `.github/workflows/ci.yml` lines 93-94 and the Stage-rename mutants step, `.gitleaks.toml` rules, `tools/scan_repo.py`, `demos/`, and CHANGELOG/SECURITY.md headings.
- **Hash and tools.** The SHA-256 of the range file (no shell). I did not run `gitleaks` or `uv`, and I did not check the Postgres need or the `uv` cache.
- **Plan facts I could not see.** The reviews/PR77 and evidence/PR77 files, `handover/*`, `AUTONOMOUS-DECISIONS.md`, and the Q8b ticket. I only skimmed the round-1 design review and the author report. I did not verify ECMA-48 or Unicode statements from the web (the plan itself marks them "from memory").
- **Prototype numbers.** I did not re-run the prototype or re-read its logs line by line, so the 7,505-passed, case-790 and leak-row claims are taken from the plan.
- **Behaviour rows.** I did not independently verify the behaviour rows of 2.4 and 2.5 (they need execution). I confirmed only the code facts they refer to.
- **Other callers.** I did not check line numbers in `k1b/loop.py`, `extract.py`, `agent_loop.py:580` or `guard/injection.py:96` beyond the grep hits above.
