Status: resolved

# Goldfish Annotated Review Report (round 6, Part 6 mode banner and demo-only guard, head 88e79c25)

**Target:** `/home/user/build/snap/pdbanner-88e79c25/DIFF.patch` (full file). MODE-SAFETY path: no round cap, a clean round is needed. Automated mode, recommended option on every item. Source reports: `pdbanner-88e79c25-design-r6.md` (0 Blocker, 1 Major, Minors) and `pdbanner-88e79c25-codebase-r6.md` (1 Blocker, 3 Major, many Minors). The independent runner ae26ccbb was still running; its findings come later as ledger rows.

Class view: classes A (nothing-connected allow-list) and B (guard fail-closed) of round 5 HOLD at their choke points (both reviewers). What fails this round is a NEW class and its siblings: (1) docs-versus-code claims (the CHANGELOG says more than the code detects or searches, and omits limits the module states), (2) a read-once input left as a consumed iterator on the banner path, (3) mutant-expectation quality of the batch 6 rewrite, (4) guard residuals, (5) small defects.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase` B1, M1; `design` m6] - Severity: Blocker
*   **Affected Scope:** CHANGELOG.md guard entry, bullet "What a file's content decides"; tools/demo_only_guard.py:270-289 (`_magic_kind`), 534-540; tests/test_demo_only_guard_ci.py:81-90
*   **Discrepancy Description:** the CHANGELOG says a zip, gzip, ELF, Mach-O, PE "or similar" is refused by its first bytes; the code knows zip, ELF, gzip, bzip2, xz, tar and compiled Python. A `blob.dat` starting with the PE or Mach-O header is refused only because it is not valid UTF-8; a PE image that happens to be valid UTF-8 is not refused. The sentence "otherwise its bytes are searched in UTF-8, UTF-16 and UTF-32" is false for an unmarked ending (it is refused as `unreadable-file`, not searched).
*   **Rationale:** a guard that says it refuses more than it does is a false assurance on the mode-safety path; the existing test checks only the clause before " by ending".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid, and the class is "a claim about what is detected is not derived from what is detected". Decision: add real Mach-O and PE rules (cheap and exact) AND make the sentence testable.
*   ***Proposed Edit:***
    *   Location: demo_only_guard.py `_magic_kind`; CHANGELOG; tests
    *   Change: `_magic_kind` also returns kinds for Mach-O (the four 32/64-bit magic values in both byte orders) and PE (`MZ`, then the 4-byte offset at 0x3C read, then `PE\0\0` at that offset, bounds checked, fail closed to "not PE" only when the header is too short to say); refused whatever the ending, with the same hit text style. CHANGELOG sentence is rewritten from the code's own list. New test derives the list of first-byte kinds from the code (a module constant `MAGIC_KINDS` the function uses) and asserts each name appears in the CHANGELOG sentence AND that every name in the sentence is in the constant (both clauses). The sentence for unmarked endings is rewritten to the real rule: text if valid UTF-8; valid UTF-8 with a NUL is text-scanned and byte-searched for UTF-16/32; a file with an unmarked ending that is not valid UTF-8 is a hit (`unreadable-file`) and is not searched; byte search without text scan only for skip-suffix endings with the right magic that look binary. A test per branch of that sentence (blob.dat with `\xff\xfe\x00demo_only` stays a hit; PE-like and Mach-O-like blobs are hits by kind; a valid-UTF-8 PE-like blob is a hit by kind). Mutants: remove each new kind; remove the NUL branch.

### [Issue 2] [`codebase` M2] - Severity: Major
*   **Affected Scope:** src/hadavin_sdk/mode_banner.py:482-487, 211-212; tests/test_mode_banner.py:1599-1608
*   **Discrepancy Description:** a one-shot iterator is accepted for `egress_hosts` ("read once"); `cfg.egress_hosts = (h for h in (...))` gives tone real the first time and, when the config returns the same exhausted generator, tone demo with "made-up demo data" the second time over real hosts.
*   **Rationale:** the exact fail-open the module forbids: a made-up claim while a real host is declared.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. Copying once at entry cannot fix a config whose property returns the consumed object on the next call. Fail-closed decision: refuse anything that is not a `list`, `tuple`, `set`, `frozenset` or `dict` keys view (exact types or their direct subclasses through the builtin readers, never calling an overridden `__iter__`); an iterator, generator, `bytearray` or `memoryview` raises `TypeError`, which `banner_or_unconfirmed` turns into the unconfirmed banner. Same rule for every other read-once input on the banner path (`tool_specs` values, `names`, `words`): sweep for every `for x in <argument>` that is not a Collection.
*   ***Proposed Edit:***
    *   Location: mode_banner.py (one helper `_collection(value, what)` used at every entry), tests
    *   Change: helper plus use at all entry points; the old pin test (generator accepted) becomes "generator refused"; test builds the banner twice from the same config with a generator and expects unconfirmed both times; one test per other argument (names, words, tool_specs values) with a generator; mutants: helper removed at each entry.

### [Issue 3] [`design` M1] - Severity: Major
*   **Affected Scope:** CHANGELOG.md lines 216-219; mode_banner.py module docstring limits (1), (4), (6)
*   **Discrepancy Description:** the CHANGELOG omits the limits that the overrides passed to `app.build(tools=, sources=, channel=, llm=, detector=, secrets=)` are invisible to the banner, that loopback is a port-forward, and that `localhost` resolution is not checked. In the demo stage `build(sources=<real kubernetes object>)` with a stand-in-only config gives tone "demo" and "Every record here is made-up demo data".
*   **Rationale:** the most dangerous direction of the mode-safety path is stated where a maintainer reads the docstring but not where an upgrader reads the CHANGELOG.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. Decision on the code guard (needs the lead, see below): the banner is built from config, the override objects are judged by Part 2's `standins.is_stand_in`, which lives on the unmerged lane `wip/cloud-pd-bind` and is itself in round 7. So in this fix batch: state all three limits in the CHANGELOG with a test pinning the statement; and add a small, safe guard that needs no Part 2 code: in the demo stage `app.build` records which override arguments were given and the banner then adds the exact words "These parts were supplied by code and are not checked here: <names>" (names only, no values) to its text, tone stays "demo" only when none were given, otherwise tone "unconfirmed" and the made-up sentence is dropped. That is fail-closed and needs no stand-in judgement; after Part 2 merges a follow-up may relax it for objects that pass `is_stand_in` (named trigger: Part 2 merged).
*   ***Proposed Edit:***
    *   Location: app.py build (demo stage), mode_banner.py `banner_from_config` new keyword `overridden: tuple[str, ...] = ()`, CHANGELOG
    *   Change: as above; tests: each of the six overrides alone gives unconfirmed with the name listed; none given gives the old demo banner; a real kubernetes-like object as `sources=` never yields the made-up sentence; mutants: ignoring each override name.

### [Issue 4] [`codebase` M2b and Minors on the table] - Severity: Major
*   **Affected Scope:** tests/banner_mutants.py rows G88 (1461), B63, B59, B54, B13, G73, G80, B10c, J23 and the bare "DID NOT RAISE" rows (B2, B2b, B3, B3b-d, B26, B27, B45, B80-B83, G10, G11, G20, G90); tests/test_banner_mutant_table.py
*   **Discrepancy Description:** G88 expects "DID NOT RAISE SystemExit" but pytest prints `DID NOT RAISE <class 'SystemExit'>` (row probably BAD; the builder's 200 of 200 conflicts, check the runner); B63's test is vacuous for its stated reason; B59 depends on the Python patch release; B54, B13, G73, G80 expect an exception type or a pytest-rewrite fragment; the bare DID NOT RAISE rows cannot show which input slipped; J23 removes two checks in one row; B10c's name is inverted.
*   **Rationale:** the batch 6 rewrite meant every expect is the message of its own killer assert; these rows break that rule and the table test does not catch them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid; class: an expect fragment must be text the killer's own assert prints, distinct per input. If the runner shows G88 as 200 of 200 good, the finding is only the fragility; still fix it.
*   ***Proposed Edit:***
    *   Location: tests/banner_mutants.py, killer tests, tests/test_banner_mutant_table.py
    *   Change: every bare "DID NOT RAISE" killer uses `pytest.raises(..., match=)` replaced by `try/except` with `pytest.fail("<test>: input <label> was not refused")` so the message names the input, and each row expects its own label; G88 expects "DID NOT RAISE" only if no better text, preferably the new message; B63 gets a test that really puts the name into an exception text and a log line; B59 expect is made version-independent (the killer asserts on the label of the URL, not on `urlsplit` behaviour); B54/B13/G73/G80 expect the killer's own message; J23 split into J23a (isText tag) and J23b (isText text); B10c renamed "an unlisted kind that connects to something is listed as connecting to nothing"; the table test additionally refuses: a bare exception type, a bare "DID NOT RAISE", any fragment that starts with a quote and is the middle of a comparison; two rows sharing one killer must have different expects or an explicit "same-assert" flag with a reason.

### [Issue 5] [`codebase` and `design` Minors, guard residuals] - Severity: Minor
*   **Affected Scope:** demo_only_guard.py:575-591, 401, 676, 680, 414-440, 159-163, 220-235; toml:37-38
*   **Discrepancy Description:** the copy run recreates an absolute tracked symlink verbatim (proves nothing for that path) and follows a path swapped between lstat and copy; `Path.is_dir()` at 401, 676, 680 swallows ELOOP and ENOTDIR and `--without-folder-if-present` returns 0 at 676 (skipping the copy run); exempt files get shape and size checks only; webp, ttf, otf cannot be allowed; HOME and XDG git excludes still apply; appended data after a valid PNG mark is not scanned past 512 bytes; the toml lists "jpeg" and omits jpg.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid, each is small. Decisions: `copy_without_folder` refuses symlinks exactly as the scan does (and `run_without_folder` runs the scan first, enforced in code, not by call order); `_stat_kind` replaces the three `is_dir()` (an unreadable or looping folder entry is a hit, not "absent"); exempt files get `_magic_kind` (a binary exempt file is a hit); add marks for webp (`RIFF....WEBP`), ttf (`00 01 00 00` and `true`), otf (`OTTO`) so they can be allowed, svg stays text; git is run with `HOME` and `XDG_CONFIG_HOME` pointed at an empty temp folder and `GIT_CONFIG_NOSYSTEM=1` so excludes from them cannot hide a file (and say that `.git/info/exclude` and `.gitignore` are still honoured and why: tracked files only matter for the copy); the appended-data limit is stated in the docstring (first 512 bytes decide); toml wording fixed.
*   ***Proposed Edit:*** as above, with one test and one mutant per item (symlink in copy, is_dir cases through a chmod-000 or looping folder, exempt ELF, each new mark, excludes in a fake HOME).

### [Issue 6] [`design` m2, m3; `codebase` Minors, Nits] - Severity: Minor
*   **Affected Scope:** mode_banner.js:62-92, 21; mode_banner.py:74-75, 81, 125-130, 269-273, docstring limit (2), CHANGELOG:28, :218; tests names; tests/test_demo_only_guard_ci.py:43-49; test_mode_banner.py:489-490, 1285
*   **Discrepancy Description:** page: when the tone write works but the text write fails the old made-up text stays under tone "unconfirmed" and a stale `data-mode`; whitespace-only tag or text paints a blank banner; length counted in UTF-16 units on the page and code points in Python; history phrases in docstrings; comment says NOTHING_CONNECTED is "not derived from any other table" though the detector pair uses `DEFAULTS["detector"]`; limit (2) wording; CHANGELOG signature omits `words`; test names overclaim; CI order comment and substring pin.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. Decisions: the page's failure path also clears the banner (`replaceChildren()`) and sets `data-mode` before anything else, so a failed text write leaves the neutral unconfirmed text or nothing, never the old claim, with a probe scenario for it; both sides reject whitespace-only text and count code points (page uses `Array.from(text).length`), tests at exactly 600 and 601 on both; wording and names fixed (history phrases out, comment true about the detector pair, limit (2) as the code says, signature, B56 and 489-490 tests made meaningful); the CI test parses the workflow YAML and checks the env key of that step (a YAML comment no longer satisfies it) and its comment says what the order really is.
*   ***Proposed Edit:*** as above.

## ONE FIX BRIEF (small builder, branch `wip/cloud-pd-banner` from 88e79c25, no force-push, nothing under handover/)

| Class | File and change | Test | Mutant | Fail-before |
|---|---|---|---|---|
| 1 claims match code (Issue 1) | demo_only_guard.py `MAGIC_KINDS` incl. Mach-O, PE; CHANGELOG sentences rebuilt | CHANGELOG-versus-`MAGIC_KINDS` both clauses; blob.dat branches; PE and Mach-O by kind; valid-UTF-8 PE blob | remove each new kind; remove NUL branch | new tests fail on 88e79c25 |
| 2 read-once inputs (Issue 2) | mode_banner.py `_collection` at every entry | generator refused twice; one per other argument | helper removed per entry | pin test flips; others fail |
| 3 overrides (Issue 3) | app.py and mode_banner.py `overridden` words and tone; CHANGELOG limits | each override alone; none; real kubernetes-like `sources=` | ignore each name | fail on old code |
| 4 table quality (Issue 4) | banner_mutants.py rows, killers, table test | table test shapes; B63, B59 | J23a/b, B10c rename | table test fails on old rows |
| 5 guard residuals (Issue 5) | demo_only_guard.py symlink, `_stat_kind`, exempt magic, marks, env, docs | per item | per item | each fails on old code |
| 6 page and wording (Issue 6) | mode_banner.js/.py, tests, CI test | page probe (text write fails), whitespace, 600/601, YAML parse | page catch, length unit | probe fails on old page |

Gates once at the final head: ruff, format, bandit, scan_repo, full pytest (own UTF8 Postgres, HADAVIN_REQUIRE_NODE=1; skips grouped and explained), ALL banner mutants and 37 stage mutants (the builder reports counts at its own head; the independent runner repeats them), gitleaks, check-no-handover-files. Box 60 minutes, checkpoint every 30. Every new test listed with whether it fails on old code.

## Decision needed from the lead (stated, not blocking the builder)
Issue 3 uses a banner-only fail-closed rule now and leaves the "relax it for objects that pass `is_stand_in`" step for after Part 2 merges (trigger: Part 2 merged). If the lead prefers the banner to call Part 2's `is_stand_in` instead, say so; it ties Part 6 to Part 2 merge order.

## Round 7 needed? YES.
Mode-safety path and a Blocker was raised; a clean round (0 Blocker, 0 Major from both reviewers) is required. Evidence the final head needs: a complete independent runner (UTF8 Postgres, own folder) with full pytest (skips grouped), all banner mutants and 37 stage mutants (the batch 6 runner ae26ccbb result on 88e79c25 is the baseline), fail-before for every new test against 88e79c25, probes: first-byte kinds (PE, Mach-O, zip, gzip, ELF, bzip2, xz, tar, pyc) under unmarked and marked endings, webp/ttf/otf with right and wrong bytes, copy run with an absolute symlink and a looping folder, fake HOME with a global excludes file, the banner built twice from generator inputs, each override alone, the page script with a failing text write and whitespace-only text at 600/601 characters, lint, bandit, scan_repo, gitleaks, handover-files check.

## Handoff counts
Accepted fixes (PROPOSE FIX): 6 issues (1 Blocker, 3 Major, 2 Minor groups). Contested: 0. Escalated: 0 (one lead decision stated above, not blocking). Declined: 0 as separate items (nits are folded into Issues 5 and 6; the declined round 5 items D-n1 and D-n2 are not reopened: the design reviewer could not identify them from the snapshot and they are stated in the guard docstring). Remaining unaddressed: 0 (all fixes are in the brief; source and snapshot untouched).
