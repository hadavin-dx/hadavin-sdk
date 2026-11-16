<!-- full hand-back report of sub-agent adaafa73, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT READY. Blocker 2, Major 9, Minor 8. Round 1 of the plan review. Read-only; I ran no tests and no commands.

SCOPE AND LIMITS
- The main tree at /home/user/build/q8a2-dryrun/main-2a8c2aa holds only src/hadavin_sdk/ and tests/__init__.py plus tests/test_lockin_guard.py. It has no tools/, CHANGELOG.md, SECURITY.md, ci.yml, fixtures, mutation runner or any test the ticket names. I could not check the following against main:
  - every test and fixture name, the two mutants/stage_mutants.py files, tools/scan_repo.py, tests/fixtures/timing.py and reference_material_sha256.txt;
  - the test_k5_tools.py lines 306-317 claim, and the CI Python 3.12 job.
- I ignored the on-disk checkout for code, as instructed.

WHAT CHECKS OUT (24 citations sampled, all correct on main)
- guard/runmap.py: 276-282, 285-295, 298-320, 330, 346-350, 395, 423, 455-461, 464, 486-526 (491, 492, 496, 498-505, 508, 512-513, 517-518, 519, 524-525 all as stated), 532-541, 554, 568, 590, 593.
- guard/redact.py: 820-822, 825-838, 877, 919-923, 1254.
- tools.py: 726-727, 730-732, 898-904, 906-933, 936, 949-973 (951, 959, 967), 976-984, 987, 1002, 1005.
- approvals/gate.py: 74, 125-136, 162, 197, 200-205, 212-220.
- approvals/channel.py: 29, 36, 47. approvals/slack_channel.py: 81. Other callers: judge.py:71, bedrock_guardrail.py:98, evidence.py:57, 87, 88, 151, 154, 191, agent_loop.py:412, 534, 580, k1b/redaction.py:188, evals.py:63, tick.py:292, k1b/loop.py:187, 194, extract.py:58, injection.py:96, migration_numbers.py:76.
- defaults.py: 31 (262,144), 38, 49 (6.0). `MAX_DECODED_MASKS` = 256 at runmap.py:423.
- Gate set check (T8): the gate set holds every member of REMOVED and SPACE_LIKE except U+2028 and U+2029, as the ticket says.
- Wrong or stale citations: none. The section 4 "33 items" count is wrong (finding 14); everything else cited is correct.
- Every function name the ticket uses exists on main.
- Time limits and cap constants exist: the 262,144 cap, the 6.0 s budget, and `MAX_DECODED_MASKS` at 256.
- `redact()` has no bare callers in src outside `redact_text` (runmap.py:494, 515) and the `guard/__init__.py` re-export. `redact_many` has no caller in src. The ticket's remark about "tests and demos" cannot be checked here.

BLOCKERS

B1. Section 3 "Words", section 4.1 `strip`, and W2 step 5: the line continuation is not defined in the two readings. "Joined reading" and "spaced reading" are defined only for removed and space-like items. The continuation row says it is "ignored for MATCHING only; kept in the output", and the fast-path rule says `strip` also looks for a backslash-line-end pair. A builder cannot write the first `strip` unit test. It is unclear whether `joined` drops the pair, whether `spaced` keeps it, and what happens when a removed item sits next to a pair. Step 5 allows "at most one gap", so a removed item plus a pair gives two gaps and falls back to step 6.
Fix: add one sentence to "Words" and a three-row example table for `strip`. Joined = removed items AND continuation pairs deleted. Spaced = glue space where a removed item stood, pairs kept. Say what step 5 does with an item next to a pair.

B2. "Not established" 3 and open question 8: the builder must "diagnose case 790 before anything else on the card path", but only the author's throwaway prototype fails it. The builder has no implementation yet, and the prototype is outside the repo (/home/user/build/prh-author/scratch/proto.py).
- The ticket does not say whether the builder gets that path.
- It does not say whether the builder first builds commit 1 and the wiring, then diagnoses.
- It does not say which commit is red until 790 is understood.
Fix: state the sequence. Build commit 1, wire the choke point, then run `tests/test_k5_round12_fuzz.py::test_no_fragment_of_an_encoded_secret_value_survives_any_producer` on the builder's own code. Give the builder read access to scratch/proto.py and scratch/dbg*.py. Say the card path (channel.clean, slack_channel) stays out of the commit-2 green claim until 790 is fixed, or that the builder stops and reports.

MAJOR

M1. W2, `canonical`: the ripple is not in the edit list. `canonical` is called from `runmap.nfkc()` (runmap.py:103-109), and `nfkc` runs inside `undo()` (runmap.py:141). That feeds the scrub (`_decoded`), `_views` (runmap.py:410), and `evidence.py:57, 87, 88, 151`. At `evidence.py:151` the check is `canonical(value) != value`. A model-typed identifier containing U+FE0F, U+034F, U+3164 or a tag character now fails grounding, and where it was accepted before it is now refused. Section 2.3 lists the evidence.py lines but W2 says "nothing else changes".
Fix: add a W2 bullet. Name `nfkc`, `undo`, `_views` and the four evidence.py sites. State the expected change (identifiers with newly ignorable characters are refused). Add a test, or state that tests/test_k5_round12_fuzz and the evidence tests must stay green unedited.

M2. W3 `_decoded` (tools.py:726): its other caller `_first_decoded` (tools.py:786-791, used at :866 in `_strip_fragment`) is not mentioned. After `hidden.strip` a single control character decodes to "". `_decoded_clean` (:794) uses `undo(clean=True)` directly and is not changed. The ticket does not say whether the fragment scan should see stripped or unstripped decodes.
Fix: say `_first_decoded` is intentionally changed or unchanged, and `_decoded_clean` unchanged (or changed), with a test.

M3. W3 `_sanitise` has a second call site that the ticket forgot: tools.py:1194, just before `digest = ... sha256(raw)` at :1197. Stopping the NUL-to-U+FFFD replacement changes the stored digest for outputs that contain NUL. NUL then also reaches `prepare_output`'s `_cut` and `_scrub` untouched.
Fix: list tools.py:1194-1197 in W3. Say whether the digest change is accepted, and add a test.

M4. W2, "other readings ... built by the existing `_views` from the escaped ORIGINAL text exactly as today". This conflicts with the new order (strip first, then escape) and with section 3, which builds the extra readings "from the escaped joined reading". The prototype already broke a test on exactly this point. It is also unclear which order applies to `_views`' own `_clean` at runmap.py:411, which deletes NUL in decoded views before `hidden.strip`, so a decoded NUL gives no boundary space while a raw NUL does.
Fix: give pseudo-code with the exact order for `redact_text`: text → surrogate repair → strip → escape → views of the escaped original and of the escaped joined reading → per view strip → escape → `_keep_earlier_masks` → `_redact_stripped`. Say what `_clean` does inside `_views`.

M5. Unicode data source, section 4 "Single-dependency line", W6 and section 5.
- The ticket contradicts itself on the file format. Section 4 says "a text file of code-point ranges". W6's perl one-liner prints one decimal code point per line. `tools/gen_default_ignorable.py` "reads the pinned range file".
- The file name is given only in section 5 (`default_ignorable_perl538_unicode1500.txt`). W6 does not name it.
- Nothing says what the builder does if perl 5.38.2 / Unicode 15.0.0 is missing, or gives a different list, so the SHA-256 would not match.
- `UNICODE_DATA_VERSION` has no value, and the hash-file format cannot be checked (the file is absent from the tree I read).
- Section 5 (c) says a third derivation must equal the file and the ranges "on both CI Python versions". The ticket never says whether CI has perl (it does not need it), nor what happens when 3.13 (15.1.0 categories) and 3.12 (15.0.0) differ.
Fix: decide here.
(a) The committed file is the perl output. Give the exact file format (range lines "XXXX..YYYY", ascending) and the one conversion command. Make the generator emit ranges.
(b) The builder commits the perl-produced file and records perl version and SHA-256 in `reference_material_sha256.txt`.
(c) If perl is unavailable the builder stops and asks. The 15.1.0 file stays a separate owner/third-party item.
(d) Set `UNICODE_DATA_VERSION = "15.0.0"`.
(e) State whether the "equal over all code points" test is skipped or must pass on Python 3.12.

M6. Section 2.4 and acceptance 11: MAIL, PW and HAND are "a made-up ..." with no literals. L4, L5, L6, L7 and L12 cannot be replayed exactly by the evidence runner or by the builder's regression JSON. G1 and G2 are prose only. The rule file allows a fake credential only if built from parts, so give the parts.
Fix: add a short "constants" block, for example MAIL = "ops" + "@" + "example.com", PW = a 16-character string built from parts, HAND = a 15-character string with a hyphen, built from parts. Add the exact G1 and G2 expressions.

M7. Section 5 "no step back" and T6: the fixtures recorded from main (masked-on-main results, main's placeholder counts for the clean corpus) have no file name and no recording command. The ticket says "with the command" but gives none. The file list in section 5 omits them. T6 also is not in the fail-on-main command (contract and regressions files only), yet the ticket claims "must pass on main" for clean-corpus parts.
Fix: name the fixtures (for example `tests/fixtures/prh_main_masks.json` and `tests/fixtures/prh_main_corpus_counts.json`). Give the recording script and command. Add the corpus test file to the main-run command or drop that claim.

M8. Stop rule. The ticket says "Extended review: yes, no round cap" but never says what ends the work. CLAUDE.md requires the plan's stop rule to hold before step 7. For an uncapped path the rule needs an end condition.
Fix: add one paragraph, for example: "Done when a result-review round has 0 blockers and 0 majors on the final head, the independent evidence (acceptance 1-12) is attached for that head, and every minor is fixed in the same push or logged in the ledger. A new round is started only for a blocker or major."

M9. Studio time and batching rules are not applied (faster-builds-time-boxes-and-batching.md, review-loop-speed-rules.md). The builder brief has no 30-minute checkpoint note or 60-minute stop. No heavy job (full suite on two Python versions, the 34-mutant runner, the perf tests, 9,000+ single cases plus 4,000 pairs plus 20,000 random strings, the fail-on-main run) is routed through `tools\heavy_slot.py --slots 3 --timeout 2400 -- <cmd>`. No expected durations are given. The ticket also does not say who runs what: the builder runs the fail-before proof and the cost table, the runner runs acceptance 1-12. Perf must run alone, but nothing says how that fits the three-slot rule.
Fix: add a "Who runs what" table: the builder runs only the touched tests while iterating, plus ONE full suite and ONE mutant run at the final head. The evidence runner runs acceptance 1-12 through heavy_slot. Perf runs alone. Add expected durations.

MINOR

m1. Acceptance 2: `grep -c ... prints 0` exits 1 when the count is 0, which clashes with the "gate on the command's own exit code" instruction. Fix: `! git diff ... | grep -q ...`.

m2. Acceptance 3: it says "on Python 3.13 and 3.12" with no 3.12 command and no statement that 3.12 is installed. Fix: `uv run --python 3.12 --all-extras --group test pytest ...`, or say how to get 3.12.

m3. Acceptance 5: bandit is run without `uv run` while the others use it. The gitleaks "repository's configuration" path is not given.

m4. Acceptance 8: "what guard/__init__.py itself imports" is vague. `guard/__init__.py` imports `hadavin_sdk.guard.redact` (line 3), so `redact` also appears in `sys.modules`. The heredoc script is not given. Fix: give the script and the exact expected list.

m5. Acceptance 9 and 4.4: the measurement script has no path. The 1.25 times main's CPU limit is a cross-worktree comparison and cannot be a flaky in-repo `perf` assertion. Say it is checked only by the evidence table, and that the perf test asserts only the 3.0 s and doubling limits.

m6. Acceptance 1 allows `ci.yml` "(one step)" but does not say which step (mutants, perf, or the range-file test) or which job.

m7. The commit split says "each commit passes ruff and the tests it holds", not that the full suite is green at each commit. Commit 2 changes `redact_text` and `tools.py` while T1 hostile cases may still be red (see B2). Fix: state which tests are red at the end of commit 2 and why, or say all green.

m8. The T1 count of 33 removed items "that is not an escape opener" does not match the table. By my count the removed set is 55 code points (9 + 14 + 1 + 5 + 26), 54 without ESC, and about 48 without the C1 openers. Also, "cases >= 9,000" and "== 4,000 pairs" do not say whether a case is per path. Fix: restate the number from the table, or say "one per member".

Further ambiguous or contradictory pairs
- The title and section 1 say "once, at the one place". But W3 also strips in `_scrub` and `_decoded` (tools.py), and W1 keeps `strip_ansi` in `find`. The ticket says so plainly, but "one reader" should read "one reader, three callers".
- Section 4.1 says `strip` returns "the same object twice when they do not differ". T10 says `strip` applied twice equals once; `strip_sequences` idempotence is not tested.
- "Imports nothing from `hadavin_sdk`" for hidden.py, while `redact.py` imports it via `hadavin_sdk.guard`. That is fine, but the import cycle through `guard/__init__.py` (→ redact → hidden) should be named in W1.
- Open question 4 says continuation can be dropped and then lists the mutants to remove. B1 fixes the definitions first.
- `is_ignorable` cost for non-Latin text: the ticket does not say how it is implemented (frozenset of the 4,174, or bisect over 33 ranges). `canonical` calls it per character on non-ASCII text, and Hindi/Persian are the slow shapes. Decide here: a precomputed frozenset plus the Cf test.

DECISIONS STILL LEFT TO THE BUILDER (should be made in the ticket)
1. The new name for "repair lone surrogates only" (inline, or a new `_repair` next to `_clean`); `_clean` is used at runmap.py:411, 488, 519.
2. The file names for the fixtures recorded from main (M7), and the file format of the range file (M5).
3. Where `fits_after_nfkc` goes in the new order, and the cap check on the joined and spaced readings.
4. How `is_ignorable` is implemented (see above).
5. The regex that makes the fast path of `strip` (the compiled pattern).
6. Which step goes in ci.yml (m6).
7. Whether the digest and `_first_decoded` changes are accepted (M2, M3).

QUESTIONS A BUILDER WOULD HAVE TO ASK
1. Does `joined` drop the backslash-line-end pairs, and does `spaced` keep them (B1)?
2. Where do I get the prototype and its dbg scripts to diagnose case 790, and what do I do before I have an implementation (B2)?
3. Is `_views` fed the escaped original or the escaped joined reading, and where does `_clean`'s NUL deletion fall (M4)?
4. Are the evidence.py grounding changes through `canonical` intended (M1)? Is the sha256 digest change at tools.py:1197 accepted (M3)?
5. Which perl, and what file format and name for the pinned range file? What if perl is missing (M5)?
6. What are the literal MAIL, PW and HAND values (M6)?
7. What are the names and the recording command of the main-recorded fixtures (M7)?
8. What ends the work (M8)? How do I run heavy jobs, and do I checkpoint every 30 minutes (M9)?
9. Which ci.yml step? How is Python 3.12 invoked?

NOT CHECKED
- Every test, fixture and tool named in sections 5 and 6 (listed under scope).
- The ECMA-48, ECMA-35 and Unicode UAX #44 content, the CWE numbers, and the 4,174 / 15.0.0 versus 15.1.0 claim (I did not run perl or Python).
- The cost and prototype numbers, and the claim that the 1.25 times limit is reachable.
- Whether the grammar in 4.1 matches ECMA-48; I only read it for internal consistency.
- The history file round8-design-zoomout-full.md: I read it. The ticket's departures from it (NUL handling, keeping the gate untouched, `strip_ansi` kept in `find`) are stated in the ticket and consistent with main, except the NUL-versus-U+FFFD point, which the ticket argues from a main behaviour I did not run.
- The six "no escaping step" caller traces (the ticket's own "not established" 8).
- demos/ callers of `redact()`.

Relevant files:
- /home/user/build/snap/prh-plan/TICKET.md
- /home/user/build/snap/prh-plan/round8-design-zoomout-full.md
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/guard/runmap.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/guard/redact.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/tools.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/runtime/evidence.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/approvals/channel.py
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/approvals/gate.py
