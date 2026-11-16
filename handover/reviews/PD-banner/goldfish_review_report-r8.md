Status: resolved

# Goldfish Annotated Review Report: PD Part 6 (mode banner, demo-only guard), round 8

**Target:** `/home/user/build/snap/pdbanner-07bfda12/DIFF.patch` (full), head 07bfda12678f49b90f970ad320cb8f07580f44cb. Path: MODE-SAFETY (no round cap, a clean round is needed). Automated mode; every valid finding is PROPOSE FIX, auto-accepted into the one fix brief below. No source, snapshot, ledger or other file was edited by this step.

**Handoff counts:** findings 24 (design 7: 3 Major, 4 Nit; codebase 17: 2 doc-contradicts-code, 8 Major, 7 Nit groups; overlaps merged into 11 issues below) | PROPOSE FIX accepted: 24 | CONTESTED: 0 | ESCALATED: 0 | DECLINED: 0 | remaining unaddressed: 0 | Round 9 required: YES.

## Facts for the builder and the reviewers (not a verdict)

- Neither reviewer ran anything. The independent runner a773a83b (cloud-limited) is still running on 07bfda12; its findings arrive as an addendum. The full pytest and the complete banner_mutants of this head run on the lead's laptop (lead order 02:30Z); no run on this head shows any batch 8 row killed yet.
- The builder admitted: no full suite or complete table on the final head; 7 tests pass on old code (renamed `test_pin_*`); the git-message masker test was never run on old code; 14 older comments say "not re-run against older code"; the 3.12 loop behaviour is emulated.
- Reviewer fact: the row count is 247, not 246 (226 plus 21 R7* rows); the 12 crash rows are right.
- Lead decisions (binding): the banner stays banner-only and fail-closed; Part 6 does NOT call `is_stand_in` until Part 2 has merged (ledger PDBIND-r7-10); for a bare scheme word plus token the guard hides EXACTLY what main hides: `src/hadavin_sdk/guard/redact.py` lines 401-405, BEARER `(?i)\bbearer\s+([a-z0-9._~+/\-<>]{12,}=*)` and BASIC `(?i)\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})`. I read both lines on origin/main: they match what the lead quoted. I also read `k1b/redaction.py` line 36: `SCHEME` there is a prose sentence describing the redactor (a string, not a list of patterns), so it is not a second rule to match; nothing from it is claimed. A bare `bypass=true` is shown; `bypass_key` and `bypass_token` stay hidden.

## Prioritized findings

### [Issue 1] [design M1 + codebase M4] - Severity: Major
*   **Scope:** app.py 54-110 (`_connected_parts`, `seal`, `mode_banner`).
*   **Discrepancy:** the connected-parts fingerprint stores `id()` at the top level only: replaced hooks (`hold_run_ids`, `post_card`, `toolbox`, `execute`, `request_approval`), a new `Hooks` with the same `tools` dict, replaced `runtime.store/audit/registry`, replaced channel (in `approvals`), in-place change of a source/store/llm/executor, and id reuse of a freed object all leave the seal equal. The CHANGELOG claim "every part that can connect" is wider than the code. No tests for these; R7A2 only removes the whole comparison.
*   ***AI Suggestion:*** PROPOSE FIX (class: identity/claim-only trust; id reuse).
*   ***Proposed Edit:*** see Fix class 1.

### [Issue 2] [design M2 + codebase M6] - Severity: Major
*   **Scope:** app.py 84, 95-98, 106 (`overridden`, `seal`); mode_banner.py 476-486 (`NOT_CONNECTIVITY`).
*   **Discrepancy:** `overridden` is not in the sealed value; `app.overridden = ()` after `build(channel=Fake)` and the public `seal(())` launder a demo banner (the builder's own proof test uses `seal(())`); `clock` is asserted "reaches no service" while `hold_run_ids` (also a callable) is an override.
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 1.

### [Issue 3] [design M3 + codebase M5] - Severity: Major
*   **Scope:** app.py 86-110: `mode_banner()` computes `_connected_parts()` and reads `registry.tools` outside the never-raises function. Inputs: `app.runtime = object()`, non-mapping `sources`, `sources=None`, mixed int/str keys in `sorted`, non-mapping `hooks.tools`; a hand-made stub runtime. A tampered app crashes the screen instead of the unconfirmed banner (fail-open for availability of the warning). Also: the expected hand-made state logs a WARNING (ValueError caught) per call.
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 1.

### [Issue 4] [codebase M3 + design N7] - Severity: Major
*   **Scope:** tools/demo_only_guard.py 252-260 (`_hide_secrets`, `_SECRET_PAIR`, `_URL_USER`, `_AUTH_HEADER`).
*   **Discrepancy:** quoted values not hidden (`password="…"`, `token='…'`); an inner quote or `&` cuts a value (`password=ab'cd` leaks `'cd`); `@` or `/` inside a URL password leaves part visible; `Authorization: Digest …` hides two tokens only; names `passwd`, `pwd`, `auth`, `credential` not covered; the pin test uses only easy inputs; a hand-rolled copy of what `guard.redact` already does; a quadratic pattern on long hyphen runs.
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 4.

### [Issue 5] [codebase M7 + M8 + M9 + design N6] - Severity: Major
*   **Scope:** tests/banner_mutants.py and the killers: B20/B23 share a killer and the same first failing entry; weak generic expects ("banner_for", "xCRM", "CRM.v2", "a.cfg", "demo-only", "Demo_Only"); R7D3 killer is timing-based (`ms < 200`, 5M astral characters = 10M UTF-16 units) and may survive on a fast runner or fail on a slow one; R7A4 name overclaims (changes only message wording; the rule `if overridden is None: raise` has no row); shared killers R7A3/A4, R7B1/B2, R7E2/E3, R7E4/E5, R7D1/J27; SAME_ASSERT compares pairs only.
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 3.

### [Issue 6] [codebase M10 + design N4 + N5] - Severity: Major (mode-safety: page fail-open)
*   **Scope:** templates/mode-banner/mode_banner.js `usable()`/`isOverrideList`; mode_banner.py 308 `_banner_for(overridden=())`.
*   **Discrepancy:** the page paints tone demo/quiet next to a non-empty `overridden` list and accepts duplicates and any order (Python dedups and orders by `OVERRIDES`); `_banner_for` keeps a default that means "none handed in".
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 2.

### [Issue 7] [codebase doc items 1, 2 + docs] - Severity: Major (doc contradicts code, mode-safety wording)
*   **Scope:** mode_banner.py 316-319 (`_banner_for` docstring: only tone "real" uses `overridden_note`; unconfirmed shows exactly `words.not_confirmed` and the page builds its own English note; a reworded `not_confirmed` makes the page paint the English fallback and lose the names; unstated); demo_only_guard.py 14-16 (module docstring lists 9 kinds, `MAGIC_KINDS` has 12; docstring not pinned by a test); CHANGELOG "four listings compared" (true for three; one is a superset check); "copied after build" (true for `dataclasses.replace` and `deepcopy`, not `copy.copy`); row count 247 not 246; test_banner_mutant_table.py 214 tells the reader to update a CHANGELOG crash-row figure that does not exist.
*   ***AI Suggestion:*** PROPOSE FIX. *Proposed Edit:* Fix class 2.

### [Issue 8] [codebase nits: pin names] - Severity: Minor
*   `test_pin_the_page_lists_and_the_python_lists_of_overrides_agree` and `test_pin_the_blank_set_...` test new features and cannot pass on old code: not pins; the real pins are the tag/text plain-text tests, the crash-rows test and the endings test; `test_the_page_paints_an_unconfirmed_banner_only_when_..._plus_a_note` says "not re-run against older code". PROPOSE FIX: rename, and re-run fail-before after the renames (the builder's run was before them). Fix class 3.

### [Issue 9] [codebase nits: guard] - Severity: Minor
*   Fat Mach-O 64 (`cafebabf`/`bfbafeca`) not recognised though the kind reads as complete; compiled-Python magic range 3000-3999 only (3.12 is 3531; 4000 and above and Python 2 pycs not covered); `_copy_regular` Windows fallback calls `os.fchmod` (absent before 3.13) and a link-to-file swap raises an unhandled OSError instead of a refusal; `_link_problem` calls a long non-loop chain "loop"; a directory replaced by a symlink while git's index lists `dir/file` is lstat'ed through (docstring "symlink of any kind" covers tracked links only). PROPOSE FIX: recognise `cafebabf`/`bfbafeca` as the same kind; derive the pyc check from `importlib.util.MAGIC_NUMBER` plus the range check documented; guard `fchmod` with `hasattr`; wrap the swap race in the refusal; rename "loop" to "link chain too long or looped"; walk the parents with `lstat` per component in the scan too, or state the docstring limit. Fix class 5.

### [Issue 10] [codebase: reuse] - Severity: Minor (inside Issue 4)
*   Core has a redactor (`guard.redact`, `guard.runmap.redact_text`). PROPOSE FIX: reuse it in the git-message masker if the copy-run isolation allows (the guard must run without importing the product package into the copy: decide and state); otherwise keep the small hand-written masker and prove it equals the core BEARER and BASIC rules on a table of inputs generated from the quoted patterns.

### [Issue 11] [codebase: shared-classes decisions] - Severity: Minor
*   `NOT_CONNECTIVITY` honesty and the tick: confirm that the tick (probe) never mutates `app.sources` or `runtime.limits` (a reviewer could not check); add a test that a normal production run keeps its banner (no false unconfirmed).

## ONE FIX BRIEF (batch 9, one small builder, fast-forward only to wip/cloud-pd-banner, no handover files, no pyproject.toml or uv.lock change)

Builder rules: fix by class at the choke point; for every new test run it against the 07bfda12 src and list which fail (name by name); a test that passes on old code is a pin and is named so; no claim without the list; do not call `is_stand_in`; no secret-shaped value in any file: build fake credentials from parts (for example `"to" + "ken"`); focused tests only here (see Evidence).

**Fix class 1: seal, reference identity, never-raises (Issues 1-3, 11)**
- File: src/hadavin_sdk/app.py (`_connected_parts`, `seal`, `mode_banner`, `build`); mode_banner.py `NOT_CONNECTIVITY` reasons.
- Change: the sealed value holds REFERENCES (a tuple of the parts themselves) and `mode_banner()` compares with `is` per part (no `id()`); it covers every `Hooks` member, `runtime.store/audit/registry/llm/detector/limits`, the channel (through `approvals`), every source value, `config`, and `overridden` itself (the recorded value is part of the sealed tuple, compared by value). `seal()` becomes private to `build` (`_seal`) or accepts only the value `build` computed (checked against `overridden`); the public name is removed. A nested in-place change is judged by an explicit list of attributes read by the core (state which: for a source/store/llm/executor the fingerprint is the reference plus its `__dict__` keys and the identity of each value) and the CHANGELOG says exactly that and no wider. `mode_banner()` wraps the comparison and every attribute read in one try: any exception means `overridden=None` (unconfirmed banner) with a quiet debug line (no WARNING per call for the expected hand-made state: use a flag, not a raise-and-catch). `clock`: decide: make it an override in `build` (recorded when given) unless a test shows the core uses it for time only; state the decision and the reason in one plain sentence; the reason string must say what was checked.
- Tests (each a separate case): every replaced part reads unconfirmed (one case per hook member, store, audit, registry, llm, detector, limits, channel, a source value, config); id reuse (replace a part twice so the original is freed: still unconfirmed); `app.runtime = object()`, `sources=None`, non-mapping `sources`, mixed int/str keys, non-mapping `hooks.tools` (no raise; unconfirmed); `copy.copy` of a built App (decide: the copy keeps the same parts so it stays known, state it) and `dataclasses.replace`/`deepcopy` (unconfirmed); `app.overridden = ()` after `build(channel=Fake)` is unconfirmed; the public `seal` name is gone (attribute test); a normal production tick keeps its banner (no false unconfirmed).
- Mutants: one row each: `is` replaced by `id` compare; hooks subset only; `overridden` left out of the sealed value; try/except removed from `mode_banner`; seal public again; clock decision reverted.
- Fail-before: all new cases against 07bfda12 src, listed by name.

**Fix class 2: page, docstrings, text (Issues 6, 7)**
- File: templates/mode-banner/mode_banner.js; mode_banner.py; tools/demo_only_guard.py docstring; CHANGELOG; tests.
- Change: `usable()` rejects tone demo/quiet with any `overridden` name, and rejects duplicates and any order other than the `OVERRIDES` order (the same rule Python applies); `_banner_for` has no default for `overridden`; docstrings fixed (the `_banner_for` docstring, the guard module docstring kinds list taken from `MAGIC_KINDS` and pinned by a test); the unstated limit (a reworded `not_confirmed` makes the page paint the English fallback) is fixed by passing the words to the page (`NOT_CONFIRMED.text` and the override note come from the Python banner, not hard-coded) or stated as a limit with a test that pins the fallback; CHANGELOG: "four listings" says what is compared and what is only a superset check, "copied after build" names exactly which copies (replace, deepcopy; copy.copy decision), the row count derived by a test from the table (no typed number), and the stale "update the CHANGELOG crash-row figure" message removed.
- Tests and mutants: page cases for demo+overridden, duplicates, wrong order, each with a mutant row; the docstring kinds test; the row-count test.

**Fix class 3: mutant table and test names (Issues 5, 8)**
- File: tests/banner_mutants.py, tests/test_banner_mutant_table.py, tests/test_mode_banner.py.
- Change: B20 and B23 get discriminating killers (an entry list ordered so the first failing entry differs, or per-row loop with the row's own entry); weak generic expects replaced by the row's own full message fragment; R7D3: replace the timing killer by a counted-work or structural assertion (for example the page function is given an object whose `length`/iteration is counted, and the pre-check must stop before any iteration), no `ms` limit; R7A4: the killer pins the rule (`overridden is None` raises ValueError) and a second row removes the `if`; R7A3/A4, R7B1/B2, R7E2/E3, R7E4/E5, R7D1/J27 each get their own killer assertion or are merged and the merge is said in the table text; SAME_ASSERT also compares the FIRST failing line of each killer under each mutant (the runner records it) so two rows failing the same line are listed; tests of new features are not named pins (`test_pin_*` only for tests that pass on old code); the three tests the reviewer named are renamed and re-run in fail-before AFTER the renames.
- Fail-before: list by test name with old-code result and killing rows.

**Fix class 4: git-message masker (Issues 4, 10)**
- File: tools/demo_only_guard.py `_hide_secrets` and tests.
- Change: (a) bare scheme words follow main exactly: BEARER `\bbearer\s+([a-z0-9._~+/\-<>]{12,}=*)` and BASIC `\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})` with case-insensitive flag, hiding the captured group; tests and mutant rows pin the minimum lengths 12 and 8 (11 and 7 characters stay visible) and no wider class; a table test proves the guard result equals `guard.redact` for these two classes on inputs built from parts (or imports the core patterns if isolation allows: state which and why). (b) After a literal `Authorization:` header name hide to the end of the line (any scheme, including Digest): this is wider than main on purpose because a header name was given; say so in one sentence. (c) `name=value` pairs: value may start with a quote (single or double) and then runs to the matching quote; an unquoted value runs to whitespace (an inner quote or ampersand does not end it); names containing key, token, secret, password, passwd, pwd, auth or credential (case-insensitive); `bypass=true` shown; `bypass_key`, `bypass_token` hidden. (d) URL credentials: hide everything between `://` and the LAST `@` before the next whitespace or path-less end (a password with `@` or `/` is hidden whole). (e) Linear-time patterns (no nested quantifier on hyphen runs); a 10000-character line test with a bound on counted steps or length, not seconds.
- Tests: every item above with fake values built from parts; each as a mutant row.

**Fix class 5: guard minors (Issue 9)**
- File: tools/demo_only_guard.py.
- Change: fat Mach-O 64 added to the Mach-O/Java kind; pyc check derived from `importlib.util.MAGIC_NUMBER` plus the documented range; `hasattr(os, "fchmod")` guard and a refusal for the swap race (SystemExit with the plain words, not an OSError); "link chain too long or looped" wording; scan walks parents with `lstat` per component or the docstring states the limit (decide, test).

## Round 9 and evidence

- **Round 9 is required** (mode-safety, no cap). Reviewers get the new snapshot, DELTA-vs-07bfda12.patch and the facts above, not the builder's verdict; two reviewers (design, codebase-details) in parallel with the runner.
- **Evidence for the final head (one runner per final head; never on a head that gets another batch):**
  - Cloud, each under 8 minutes and resumable (checkpoint per chunk), at most 2 heavy processes: focused tests of the changed files; fail-before of every new test against the 07bfda12 src (list by name); the new and changed banner_mutants rows plus every crash row plus a 60-row sample in chunks; stage_mutants (37); ruff, ruff format --check, bandit -ll, scan_repo, gitleaks, check-no-handover-files; hostile probes (replaced hooks, id reuse, stub runtime, mixed keys, copied Apps, page with demo+overridden, the masker table incl. a 10000-character line, non-UTF8 bytes).
  - **RUN ON LAPTOP (lead order):** the full pytest of the final head and the complete `banner_mutants.py` table, each with the exact sha; the lead puts the raw output on the branch under handover/.
- The runner a773a83b findings on 07bfda12 are added to this brief by the caller as an addendum when they arrive; ledger rows for these findings are added by the caller (PDBANNER-r8-1..9 already exist).
