Status: resolved

# Goldfish Annotated Review Report, PD part 6 (mode banner and demo-only folder guard), round 7

**Target:** `/home/user/build/snap/pdbanner-41c84695/DIFF.patch` (full file), head 41c8469510bb883fa04c8d116ec69860a6ea177b. Path class: MODE-SAFETY (no round cap, a clean round is needed).
**Inputs:** `handover/reviews/PD-banner/pdbanner-41c84695-design-r7.md` and `pdbanner-41c84695-codebase-r7.md`. Both reviewers read the code only; they ran nothing. The independent runner (a389dd75) had not reported when this was written: its findings become ledger rows later and go to the next builder.
**Fixed lead decision (not reopened):** the banner stays banner-only and fails closed. Part 6 must not call `is_stand_in` until Part 2 has merged (ledger PDBIND-r7-10).

Result of the round: 0 Blocker, 5 Major, 3 Minor groups, 1 declined Nit. NOT clean. Round 8 is required.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design_critic` M1, `codebase_details` M2] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/mode_banner.py` 648-669 (`overridden=()` default), `src/hadavin_sdk/app.py` 63-70, `CHANGELOG.md` line 29 and 214.
*   **Discrepancy Description:** "no override was recorded" and "the caller did not say" are the same value `()`. An `App` built directly with a real kubernetes source, `dataclasses.replace(app, llm=real)` and `app.llm = X` after build all give tone "demo" and "Every record here is made-up demo data." The CHANGELOG headline still tells a screen to call `banner_or_unconfirmed(config, tool_specs=...)`, which cannot see overrides.
*   **Rationale:** a made-up claim next to a real service is the mode-safety failure this part exists to stop.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: unknown versus none. A missing value must mean unknown, and unknown must give the unconfirmed banner.
*   ***Proposed Edit:*** see ONE FIX BRIEF class A.

### [Issue 2] [`design_critic` M2, `codebase_details` M3] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/app.py` 83-115 (`_given_overrides`), `mode_banner.OVERRIDES`, `tests/test_mode_banner.py` 1942-1944.
*   **Discrepancy Description:** the six build keywords are listed by hand. `hold_run_ids` is not in the list; a new build keyword is silently not recorded. The docstring says "a new override cannot be added without teaching the banner"; the ValueError fires only for names someone passes in. The test pins a literal set, not `inspect.signature(build)`.
*   **Rationale:** a claim not derived from the code, the round 6 class again.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decision. `hold_run_ids` is caller code that decides which runs are held and can query any store: record it as an override. `clock` returns a time only and cannot hold records: it goes on an explicit NOT_CONNECTIVITY list with that reason (limit stated in the docstring: a clock callable could in theory do other work; trigger to revisit: Part 2's judging of callables merges). The test must make every `build` parameter fall in exactly one of the two lists.
*   ***Proposed Edit:*** class B.

### [Issue 3] [`design_critic` M3, `codebase_details` M1, N1-N4] - Severity: Major
*   **Affected Scope:** `tests/banner_mutants.py` 246-252 (B13), 1013-1019 (B54), 1387-1392 (J23), 1546 (G91), 1573 (G95), 1660-1669 (SAME_ASSERT), `tests/test_banner_mutant_table.py` 105-136, `tests/test_mode_banner.py` 2016-2020.
*   **Discrepancy Description:** J23 still removes the tag check and the text check in one row and expects `"tag = "`. B13/B54 (and B43, B44, B52, B53) expect interpreter or pydantic text. There are 12 crash rows, not 11, and the set is not pinned. The SAME_ASSERT comment names a function that does not exist (`shared_assert_problems`; it is `shape_problems`), misdescribes the key, and the G13/G23 reason says one check where the killer has two. G91 and G95 names do not match what they mutate (G95 is inverted). A dead local `words` and a test name that says Python at 600/601 but checks only the tag.
*   **Rationale:** a row that passes on the wrong failure proves nothing; the round 6 report asked for these.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: a mutant row must fail on its own assertion. Crash rows are allowed only when the crash is the stated intended reaction, and then the set is pinned by name.
*   ***Proposed Edit:*** class C.

### [Issue 4] [`codebase_details` M4, N5] - Severity: Major
*   **Affected Scope:** `templates/mode-banner/mode_banner.js` 23, 61-67; `src/hadavin_sdk/mode_banner.py` 317-319, 679.
*   **Discrepancy Description:** under tone "unconfirmed" the page paints any text that starts with the not-confirmed words, so a faulty server can add "Every record here is made-up demo data." after "Treat everything here as real." Python `strip` and JS `trim` disagree on U+0085, U+001C-001F and U+FEFF; the CHANGELOG sentence overclaims. `Array.from` allocates for an arbitrarily long string.
*   **Rationale:** the page is the last line before a person reads the banner.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: the page trusts only what it can recompute. Decision: under "unconfirmed" the page paints exactly the not-confirmed words and builds the override note itself from a separate list of names (text nodes only); a text that is anything else is replaced by the fallback. One explicit whitespace set (code points listed in one Python constant and one JS literal; a test parses the JS literal and compares). Check `v.length <= 2 * MAX_TEXT` before `Array.from`.
*   ***Proposed Edit:*** class D.

### [Issue 5] [`codebase_details` M5] - Severity: Major
*   **Affected Scope:** `tools/demo_only_guard.py` 316-322 (`_MAGIC_CHECKS` Mach-O), CHANGELOG guard bullet.
*   **Discrepancy Description:** a fat (universal) Mach-O starts `CA FE BA BE` (or `BE BA FE CA`) and is not detected; the CHANGELOG says "Mach-O".
*   **Rationale:** fat binaries are the common macOS format; a product root could carry one with a text ending.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decision: add both fat magics as one kind named "fat Mach-O or Java class file". `CAFEBABE` is shared with Java class files; both are compiled code that must not be in a product root, so one kind and one hit is correct and no byte-count rule is needed. The CHANGELOG names that kind; the MAGIC_KINDS test derives the CHANGELOG list from the code.
*   ***Proposed Edit:*** class E.

### [Issue 6] [`design_critic` 4, `codebase_details` N8-N11] - Severity: Minor (security path, fixed in the same push)
*   **Affected Scope:** `tools/demo_only_guard.py` 109, 259, 309, 403, 417, 488, 519, 645-677.
*   **Discrepancy Description:** `_link_stays_in_copy` resolves link targets by text: tracked `dir/k -> ..` and `dir/l -> k/../../outside` pass, and the copy run reads outside its copy. `O_NOFOLLOW` guards only the last path component (a swapped parent folder is not caught; on a platform without it the flag becomes 0). `Path.resolve()` raises RuntimeError on a symlink loop on Python 3.12. A second `os.lstat` after `_stat_kind` can raise FileNotFoundError. git's stderr is discarded (dubious ownership gives only "git ls-files failed"). bzip2 level byte (`1`-`9`) is not checked. Orphan comment at line 109.
*   **Rationale:** each is a way the check can be fooled or can die without a clear message.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: path decisions must come from the file system, not from text. Decisions: (a) after copying, resolve each copied link with the copy's links in place (`os.path.realpath` inside the copy) and fail when the result leaves the copy root; also refuse a target holding `..` after another link component. (b) Open files by walking the parent chain with `dir_fd` and `O_DIRECTORY|O_NOFOLLOW` where `os.open` supports `dir_fd`; where it does not (Windows), refuse a link anywhere in the path and say so in the docstring. (c) Replace `Path.resolve()` by `lstat` plus text; a loop is a hit, never a traceback, on 3.12 and 3.13. (d) One `lstat` per file. (e) On a git failure print git's stderr first line, masked. (f) bzip2 needs level `1`-`9` and `BZh` followed by a block or end-of-stream magic.
*   ***Proposed Edit:*** class E.

### [Issue 7] [`design_critic` 6-7, `codebase_details` N6, N7, N12, N13] - Severity: Minor
*   **Affected Scope:** `src/hadavin_sdk/mode_banner.py` 115-126, 167-170, 232-237, 513-520, 539-542; `CHANGELOG.md` 29-32, 214; `tests/test_demo_only_guard_ci.py` 33-50, 135; `tests/test_mode_banner.py` 1915.
*   **Discrepancy Description:** NOTHING_CONNECTED comment says "not derived from any other table" while line 126 uses `DEFAULTS["detector"]`. CHANGELOG says every list is "one of those types" while ordered readers take list or tuple only. `ModeBanner` docstring says unconfirmed comes only from `not_confirmed`. CHANGELOG does not say the public demo loses its made-up banner when it builds with fakes. The allowed-ending list in the CHANGELOG is not derived from `ENDING_MARKS`; the regex runs over the whole CHANGELOG; substring pins repeat the parsed YAML test. A test imports `tests.test_k3_pilot` for SECRETS. Three near-identical TypeError wrappers. The tracked-file listing exists in four places and only the guard sets `core.excludesFile`.
*   **Rationale:** docs versus code, and duplication at a choke point.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix every false sentence, derive lists from code in a test, one `what`-parameterised TypeError wrapper. For the four listings: check by reading whether `tools/scan_repo.py`, `tests/test_repo_rules.py` and `tests/test_no_reference_material.py` need the same override; if a core helper already lists tracked files, reuse it; if the stdlib-only copy run forbids that, state the duplicate and add a test that the four commands agree on a made-up repo with a global ignore file.
*   ***Proposed Edit:*** class F.

### [Issue 8] [`design_critic` 5] - Severity: Minor
*   **Affected Scope:** `tests/test_mode_banner.py` 1769, 1793, 1807; the list of seven pins.
*   **Discrepancy Description:** seven new tests pass on the old code; some comments say "fails on old code" or imply it.
*   **Rationale:** a pin cannot show the fix.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Rename and re-comment them as pins (or make them fail on the old code by aiming at the new behaviour); the fail-before log lists pins and proofs separately and honestly.
*   ***Proposed Edit:*** class C.

### [Issue 9] [`design_critic` 8] - Severity: Nit
*   **Affected Scope:** `tools/demo_only_guard.py` `-c core.excludesFile=/dev/null`.
*   **Discrepancy Description:** the brief asked for an empty HOME; the builder overrode only the excludes file. The override does not isolate other global git config.
*   **Rationale:** reviewer accepts it.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** Not a defect: an empty HOME would also drop `safe.directory`. Recorded.
*   ***Proposed Edit:*** none.

## ONE FIX BRIEF (small builder, Part 6 batch 8, head 41c84695, fast-forward on `wip/cloud-pd-banner`; mode-safety path)

Rules for the builder: fix every item below, none deferred; state which fail-before tests fail on the old code and which only pin; do not call `is_stand_in`; do not touch Part 2 files; no handover files.

**A. Unknown versus none (Issue 1).**
- `app.py`: `App.overridden: tuple[str, ...] | None = None`; `build` sets a tuple explicitly (possibly `()`); `App.mode_banner()` gives the unconfirmed banner when it is `None`. `dataclasses.replace` and attribute set after build must also give unconfirmed: either make `App` frozen (check callers first) or record a fingerprint of the connected parts at build and compare at `mode_banner()`; pick the smaller change and say why.
- `mode_banner.banner_or_unconfirmed` and `banner_from_config`: `overridden` is a required keyword (no default). A caller that does not know passes `None`, which gives unconfirmed. Update every caller (grep).
- CHANGELOG and module docstring lead with `App.mode_banner()` as the supported call; state the public demo built with fakes shows the unconfirmed banner (Issue 7).
- Tests: direct `App(...)` with a real source; `dataclasses.replace(app, llm=real)`; `app.llm = X`; `banner_from_config` without the keyword is a TypeError. Mutants: default back to `()`; fingerprint compare removed.

**B. Override list derived from `build` (Issue 2).**
- Record `hold_run_ids`; put `clock`, `config_dir`, `agents`, `timeout_s` and any other non-connecting parameter on `NOT_CONNECTIVITY` with a reason each.
- Test: set of `inspect.signature(build).parameters` equals `OVERRIDES | NOT_CONNECTIVITY` (disjoint). Fix the `_given_overrides` docstring to say what is true. Mutant: a new build keyword added to a copy of `build` is reported by the test.

**C. Mutant table (Issues 3 and 8).**
- Split J23 into J23a (tag check) and J23b (text check) with their own messages. B13, B43, B44, B52, B53, B54: give the killer's own assert message or keep as crash rows. Pin the crash set (12 names, derived by the table test from `crash=` rows) in one place; the table test refuses a crash row whose expect is the interpreter's message unless the row name is in the pinned set. Fix the SAME_ASSERT comment (function name `shape_problems`, key is the space-joined labels in row order), the G13/G23 reason (two checks, both fail check 1), G91 name ("only the feedface magic is recognised") and G95 name ("a second accepted mark is added for .otf"). Remove the dead `words`; make the 600/601 test check the Python text as well. Rename the seven pins; the fail-before log separates pins from failing proofs.
- Re-read the six SAME_ASSERT killers (B3f B8 B9, G9b G14c, G13 G23, J10 J19, B31 B35, G38 G72) yourself and write the reason from what you read.

**D. Page (Issue 4).**
- `mode_banner.js`: under tone "unconfirmed" paint exactly `NOT_CONFIRMED.text`; show override names only from a separate array in the banner object, as text nodes, with the note words fixed in the page; any other text goes to the fallback. Length pre-check before `Array.from`. One explicit whitespace code point set in one Python constant and one JS literal; a test parses the JS literal and compares the sets; use that set in both the Python and JS checks. Tests under node: the forged text from the review, U+0085, U+001C, U+FEFF tags, a 10 million character string (time bound), astral characters at 600/601. Mutants: prefix check back; set differs by one code point.

**E. Guard (Issues 5 and 6).**
- Add the fat Mach-O/Java class kind (both byte orders) to `MAGIC_KINDS`; the CHANGELOG list is derived from the code by a test. bzip2: level `1`-`9`, then block or end-of-stream magic. Copy run: link target check against the copy with its links in place, refuse `..` after a link component; `dir_fd` walk with `O_DIRECTORY|O_NOFOLLOW` per component where supported, otherwise refuse links on the path and say so; `lstat` plus text instead of `Path.resolve()`; one `lstat` per file; git stderr first line (masked) shown. Remove the orphan comment.
- Tests: two chained links (`dir/k -> ..`, `dir/l -> k/../../outside`); a parent folder swapped for a link between check and open; symlink loop as the demo-only folder and as a tracked link (must be a hit with exit 1, not a traceback; also run on Python 3.12 semantics by patching `Path.resolve` to raise RuntimeError); file deleted between two checks; fat Mach-O blob with a text ending and with no ending; bzip2 variants; dubious-ownership message (fake git on PATH printing the known sentence, exit 128). Mutants for each fix.

**F. Documentation and reuse (Issue 7).**
- Fix NOTHING_CONNECTED comment, "list or tuple only" sentence, `ModeBanner` docstring, the "11 crash rows" figure (12), the resolve-loop claim, the allowed-ending list (derive from `ENDING_MARKS` in a test), CI test regex scoped to the guard entry, duplicate substring pins removed. Replace `tests.test_k3_pilot` import by a local constant. One `what`-parameterised TypeError wrapper. Decide the four tracked-file listings as stated in Issue 7 and write the decision in the CHANGELOG or the code comment.

**Evidence the final head needs (runner, independent):** full pytest `-m "not live and not perf" -rs` on a UTF8 Postgres with `HADAVIN_REQUIRE_NODE=1` (expect one skip, tests/contracts/test_llm.py:95); stage mutants complete; banner mutants complete (count equals the table length; every row good; crash rows equal the pinned 12); lint, format, bandit, scan_repo, server_scan, gitleaks, handover-files check; fail-before for every new test in a worktree of 41c84695 with its old src (record which fail, which pin); probes: the three direct-App cases, `hold_run_ids` build, forged page text under node, whitespace set, fat Mach-O, link chains, loop folder, swapped parent.

**Is round 8 needed?** Yes. Mode-safety path, no cap: 5 Major found this round. Round 8 reviewers: `egm-design` and `egm-codebase-details`; they must check by running or reading the runner's evidence, not the builder notes. Round 8 is the clean round only if it finds 0 Blocker and 0 Major.

## Handoff counts
- Accepted (PROPOSE FIX): 8 issues (5 Major, 3 Minor groups).
- Contested: 0. Escalated: 0. Declined: 1 (Issue 9, Nit).
- Remaining unaddressed: all 8 until the batch 8 builder reports; runner findings on 41c84695 not yet in.
