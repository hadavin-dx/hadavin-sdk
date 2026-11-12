Status: resolved

# Goldfish Annotated Review Report (round 5, Part 6 mode banner and demo-only guard)

**Target:** `/home/user/build/snap/pdbanner-3d7967cb/DIFF.patch` (full file), head 3d7967cb, wip/cloud-pd-banner. SECURITY / mode-safety path: no round cap, a clean round is needed.
**Inputs:** `pdbanner-3d7967cb-design-r5.md` (0 Blocker, 3 Major, 6 Minor, 5 Nits) and `pdbanner-3d7967cb-codebase-r5.md` (0 Blocker, 2 Major, 7 Minor, 6 Nits). Independent runner a686336c was still running when this was written; nothing here depends on it.
**Mode:** automated; no person available; recommended option for every item.

## Handoff counts
- Accepted fixes (PROPOSE FIX): 5 Major (4 distinct: the lstat fail-open was found by both reviewers), 13 Minor (some overlap between the two reviewers), 9 Nits.
- Contested: 0. Escalated: 0. Declined: 2 Nits (D-n1, D-n2 below).
- Remaining unaddressed: 0 after the fix brief. Round 6 is required.

## Classes (fix by class, at the choke point)
- **A. "Connects to nothing" is decided by the wrong table.** The banner must name a service as real unless an explicit, pinned list says it touches nothing.
- **B. The folder guard can skip or wave through a file it lists (fail-open).** The path-gone test, the picture and font endings, the marker and exempt files, the copy run.
- **C. Tests that pass for the wrong reason.** Odd-banner entries, loose `expect` fragments, whole-job CI pins.
- **D. Words that say more than the code does.** CHANGELOG and docstrings.
- **E. Small defects and sibling gaps.** Required `words`, safe error path, tag length, manifests for several modules, comments, probe names.

## Prioritized Findings & AI Suggestions

### [R5-1] [design M1] Severity: Major (class A)
*   **Scope:** src/hadavin_sdk/mode_banner.py:114 and :483 (`_NOTHING_CONNECTED = NOT_PROD | {detector}`)
*   **Description:** "Connects to nothing" is taken from `NOT_PROD`, the table the prod gate uses. A kind added there later for being dev-only (dev secrets kind, `openai_compat` pointed at a dev server, a local Vault) silently drops out of the "real" list and a demo banner then says "made-up". No test pins the content. Unconfirmed as a live bug (NOT_PROD was outside the snapshot); the design is wrong either way.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The comment at line 112 already states the right rule (unknown kind = real, naming too much is the safe mistake); the code does not implement it. An explicit allow-list is deny-by-default.
*   ***Proposed Edit:*** Replace the subtraction with `NOTHING_CONNECTED = frozenset({("signer", ...), ("anchor", ...), ("detector", DEFAULTS["detector"])})` (read the real signer and anchor kinds that have no network path from the kinds modules; list each pair with a one-line reason). Pin the exact content in a test. Add a test that adds a made-up dev-only pair to `NOT_PROD` (monkeypatch) and checks the banner still names the component as real. Mutants: widen the allow-list by one pair; revert to `NOT_PROD |`.

### [R5-2] [design M2] Severity: Major (class B)
*   **Scope:** tools/demo_only_guard.py:465-469 (allowed endings at :72-75)
*   **Description:** A non-text file with an allowed ending (.png .jpg .gif .ico .pdf .woff .woff2) is searched only for the folder name as raw bytes; `_magic_kind` knows zip, ELF, gzip, bzip2, xz, tar, pyc. A zstd, 7z, rar, lz4, PE, Mach-O or compressed JSON named logo.png passes; the docstring "renaming it to .png does not help" is overstated.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as round 4 (a name decides what a file is). The content must decide.
*   ***Proposed Edit:*** A table ending -> accepted magic prefixes (`\x89PNG\r\n\x1a\n`, `\xff\xd8\xff`, `GIF87a`/`GIF89a`, `%PDF-`, `wOFF`, `wOF2`, ICO `\x00\x00\x01\x00`). An allowed-ending file whose first bytes do not match is a hit (`ending-does-not-match-content`). Tests: one real tiny sample per ending passes; for each ending a zstd, 7z, rar, lz4, PE and Mach-O header named with that ending is a hit. Mutants: drop one table row; accept any content.

### [R5-3] [design M3 and codebase M2] Severity: Major (class B), found by both reviewers
*   **Scope:** tools/demo_only_guard.py:360-372; tests/test_demo_only_guard.py:678
*   **Description:** `Path.is_symlink/is_dir/is_file` swallow some OSErrors on some Python versions (3.13 by recollection, unconfirmed). With an unreadable parent, `os.path.lexists` is False and the entry takes `continue` ("gone from the disk"): no hit, contradicting "a hit, never a skip". Test only monkeypatches `Path.open`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The decision "this entry is gone" must come from one primitive that does not swallow errors.
*   ***Proposed Edit:*** One helper `_stat_kind(full)` using `os.lstat`: `FileNotFoundError` -> "gone" (continue), `S_ISLNK`/`S_ISDIR`/`S_ISREG` -> kinds, every other result or any other `OSError` (incl. `PermissionError`, `NotADirectoryError`) -> hit `unreadable-file`. Test: tracked `src/pkg/locked/x.py` with `locked/` mode 000, run as a non-root user (skip when `os.geteuid() == 0`; the runner uses `setpriv`/`su postgres`-style non-root run); also a monkeypatched `os.lstat` raising `PermissionError`, `OSError(ELOOP)` and `FileNotFoundError` (only the last continues). Mutants: treat every OSError as gone; revert to `Path.is_*`.

### [R5-4] [codebase M1] Severity: Major (class C)
*   **Scope:** tests/test_mode_banner.py:422-445; templates/mode-banner/mode_banner.js:54
*   **Description:** Odd entries #4-#9 lack `real` and `stand_ins`, so they hit `isTextList(undefined)` before the field under test. Deleting `if (!isText(tag) || !isText(text)) return NOT_CONFIRMED;` survives; J5 is killed only by the standins case.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A test that fails for another reason proves nothing about its own line.
*   ***Proposed Edit:*** Build every odd entry as `{**GOOD_DEMO, "<field>": <odd>}` (one field changed; `GOOD_DEMO` valid by itself, asserted first). Add a J row deleting the `isText(tag)`/`isText(text)` line, expecting the `text`/`tag` entry's name in the failure; check J5 is killed by the 601-character `text` case. Fail-before: new test on old table must show the survivor.

### [R5-5] [design m4] Severity: Minor (class B)
*   **Scope:** tools/demo_only_guard.py:319, :382-384
*   **Description:** Exempt files and the marker (`tools/demo_only_guard.copy_run`, "empty") are skipped whole: content never read, size never checked; the exempt check runs before the symlink check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** An exempt path is a hole by name; make it a hole only for exactly the intended shape.
*   ***Proposed Edit:*** Check symlink first for every path. Marker: must be a regular file of size 0, else a hit. Exempt files: not a symlink, size cap still applies. Tests and mutants for each (marker with content, marker as symlink into the folder, exempt file as symlink).

### [R5-6] [design m5 and m6, codebase m8 and m9] Severity: Minor (class B and C)
*   **Scope:** tools/demo_only_guard.py:589-597; ci.yml step "Demo-only folder copy run"; tests/test_demo_only_guard_ci.py:29 and :41; tools/demo_only_guard.toml
*   **Description:** `--require` silently ignored with the copy-run flags; the CI copy run passes no pytest arguments (runs live and perf tests); `HADAVIN_REQUIRE_NODE: "1"` pinned for the whole job not the pytest step; the copy drops HADAVIN_TEST_PG_DSN and HADAVIN_TEST_VAULT_ADDR so those tests skip silently.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is a flag or pin that says more than it checks.
*   ***Proposed Edit:*** argparse mutually-exclusive group (exit 2 with a message) for `--require` vs the copy-run flags, with a test per combination. CI copy run: `-- -m "not live and not perf"`; the test extracts that step's block and asserts the arguments and the node variable inside that block (and the pytest step block for `HADAVIN_REQUIRE_NODE`). Toml comment: database and Vault variables are left out on purpose; those tests skip in the copy.

### [R5-7] [codebase m3 and design nit GIT_*] Severity: Minor (class B)
*   **Scope:** tools/demo_only_guard.py:511 (`copy_without_folder.ignore`); every `git` subprocess
*   **Description:** `tracked` holds file paths, so a tracked directory whose name matches `copy_exclude` (`src/hadavin_sdk/credentials/`, `.env.d/`) is dropped with its tracked files; a name deny-list over a full tree copy misses `.git-credentials`, `*.tfvars`, `.pgpass`, `secrets.yaml`, ignored build output. `git` inherits GIT_DIR, GIT_INDEX_FILE, GIT_WORK_TREE and can list the wrong tree.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Copy exactly what the scan reads: one list, no second rule.
*   ***Proposed Edit:*** Copy exactly `tracked_paths(repo)` minus the folder and the marker (copy file by file, make parent folders); delete the name deny-list. Keep a secret-looking tracked file out only if it is not tracked (it then is not copied anyway). Strip every `GIT_*` variable from the environment of the git subprocesses. Tests: tracked `src/pkg/credentials/__init__.py` is copied; an untracked `.pgpass` and an ignored `build/` are not; run with `GIT_DIR` pointing elsewhere and the result is unchanged. Mutants: re-add a name filter; stop stripping GIT_*.

### [R5-8] [design m7, codebase m4 m5 m6] Severity: Minor (class D)
*   **Scope:** CHANGELOG.md lines 214-215; mode_banner.py:30-31, :166-170, :344; demo_only_guard.py:27-29, :79, DEFAULT_SKIP_SUFFIXES
*   **Description:** Words say more than the code: "no token or key reaches the child" (environment only; HOME and PATH allowed); suffix list shorter than REFUSED_SUFFIXES; UTF-32 missing in one sentence; "never leaves the banner blank" vs the JS comment; `banner_from_config(config, names)` presented as the one way and without `tool_specs`; empty mapping case missing; "now REQUIRES", "Wording changes ... now reads", "Round 5 (fail closed)" in a new feature's release note; dangling comment at :79; `\xNN` vs `\uNNNN`/`\UNNNNNNNN`; dead skip suffixes; the claim-sentence reservation reserves only the whole sentence, not its key word (a Spanish rewording would not reserve "inventados"); "cannot occur in production" for a check read in `spec_problems`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Release notes and docstrings are claims; R330 requires them to match what the code checks.
*   ***Proposed Edit:*** Rewrite each sentence from the code: say "environment variables" only; list the full `REFUSED_SUFFIXES` by importing the tuple into a test that compares it with the CHANGELOG text; one sentence for UTF-8, UTF-16 and UTF-32; name `banner_or_unconfirmed` as the call screens use and show `tool_specs`; mention the empty mapping; present tense for a new feature, no round or review language; delete the dangling comment and the dead skip suffixes; fix the docstring escapes. For the key word: add `reserved_words` to `BannerWords` (default the English key words) and reserve them in names, with a test for a non-English `BannerWords`; the ASCII-only name rule is stated in the docstring. Replace "cannot occur in production" with what `spec_problems` actually enforces (builder reads `tools.py` and quotes the line).

### [R5-9] [codebase m7] Severity: Minor (class C)
*   **Scope:** tests/banner_mutants.py (B23, B28, G9c, J6, truncation-string expects); tests/test_banner_mutant_table.py
*   **Description:** Weak `expect` fragments match almost any failure ("AssertionError: ('", "did not match", "boom"); B28 is half-equivalent (shadowed by the names-segment check); several expects are pytest repr truncations, brittle across versions; nothing checks `old != new`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A mutant that is killed by the wrong failure is a false kill.
*   ***Proposed Edit:*** Replace each flagged expect with text of the test's own assertion message (add a message to the assertion where needed); the table test rejects an expect that is a generic Python or pytest phrase (list: `AssertionError`, `did not match`, `boom`, a bare tuple repr) and any row with `old == new`. Re-point B28 to a case where only the demo-plus-real rule can fire, or remove the row with a written reason in the notes (equivalent mutant). Fail-before: plant `old == new` and a generic expect; both reported.

### [R5-10] [design m8 and m9] Severity: Minor (class A and E)
*   **Scope:** tests/test_mode_banner.py:1095-1148; mode_banner.py:454-457
*   **Description:** The class C parity pin matches refusal keywords only ("backslash", "percent-encoding", "credentials in the URL"); bare hosts and `_port_tail_ok` are not pinned against the executor; `Config.systems[*].base_url` type unknown (an `AnyUrl` would make every system read "real"); other URL fields not read. With several tool modules and a manifest for only one, the unmanifested module is not counted; a spec with `hosts=()` plus a configured module reads "nothing real".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The banner's reading of a host must be provably no more lenient than the one the executor uses; modules without a manifest must count.
*   ***Proposed Edit:*** Parity test over a fixed list of 40 URL spellings and 20 bare hosts: for each, `_is_this_machine` is True only if `ToolContext.fetch` (real code) would allow that loopback spelling (stricter is allowed; one-directional pinned and named so). Read the real type of `Config.systems[*].base_url`; if not `str`, convert with `str()` before reading and test with a pydantic URL object. Count a configured tool module with no resolved spec, or with `hosts=()`, as one real service; docstring limit states this. Test: two modules, one manifest, banner lists the other as real. Mutant for the module comparison.

### [R5-11] [nits accepted, 9] Severity: Nit (class E)
*   **Scope:** mode_banner.py:173-178 (`_clean_names words=None`), :318/:438 (`egress_hosts` typing vs a generator), tag length vs `MAX_TEXT_LENGTH`, :526 (`not_confirmed(words)` in the except); mode_banner.js:88-90 comment; mode_banner_probe.js:29 name; test name "give the same answer"; tests for `_under`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is a silent weaker default or an unflagged mismatch; cheap to fix with a test.
*   ***Proposed Edit:*** Make `words` required in `_clean_names`; type `egress_hosts` as `Collection[str]` or accept any iterable by `tuple()` (test with a generator); refuse a tag longer than `MAX_TEXT_LENGTH` in Python (test); in the except build the fallback from constants that cannot raise (test with malformed `words`); JS comment states both cases (data-mode not cleared when the tone write failed) and, if cheap, clears `data-mode`; rename the probe scenario to `failing-every-attribute` (or make it fail the tone attribute only and add the every-attribute one); rename the one-directional test to say "never more lenient than the tool client".

### [D-n1] [design nit] Severity: Nit
*   ***AI Suggestion:*** DECLINE
*   **Scope:** `_under` is case-sensitive (`SRC/x` not scanned on a case-insensitive file system).
*   ***Justification:*** The guard runs on git's own path list on Linux CI; folding case would also change which paths are product roots. Recorded in the guard docstring as a stated limit: "paths are matched as git lists them; on a case-insensitive file system a differently-cased spelling is not matched."

### [D-n2] [design nit] Severity: Nit
*   ***AI Suggestion:*** DECLINE
*   **Scope:** the phrase `DEMO_ONLY` also matches the quoted string `"DEMO_ONLY"`.
*   ***Justification:*** Over-detection is the safe side for a guard whose job is to find the folder name in product code; a product file that must name the folder for a real reason goes in the exempt list with its reason.

## ONE FIX BRIEF for a small builder (batch 6 of Part 6; branch core/P0b-banner worktree from wip/cloud-pd-banner 3d7967cb; push to wip/cloud-pd-banner)

Rules: private worktree under /home/user/build/wt/; never cd the main shell into it; heavy jobs only via /home/user/build/heavy.sh (max 3); no commit under handover/(evidence|reviews|tickets); run `check-no-handover-files.sh wip/cloud-pd-banner <sha>` before the push; ruff check and format --check before pushing; no spend, no secrets; checkpoint note every 30 minutes, stop at 60 minutes. Every fix lands with: test, mutant row (in tests/banner_mutants.py, unique search text, specific expect), and a fail-before run (new tests on 3d7967cb src must fail; list the ones that pass on old code and say why).

| Class | Files | Change | Test | Mutant | Fail-before |
|---|---|---|---|---|---|
| A (R5-1, R5-10) | mode_banner.py, tests/test_mode_banner.py | explicit `NOTHING_CONNECTED` pairs; configured module without a spec counts real; host parity table; `str()` of the base_url | exact-content pin; dev-only pair added to NOT_PROD still real; 2 modules 1 manifest; 40+20 parity cases | widen list; revert to NOT_PROD; drop module comparison | pin and module tests fail on old code |
| B (R5-2, R5-3, R5-5, R5-6, R5-7) | tools/demo_only_guard.py, .toml, ci.yml, tests/test_demo_only_guard.py, tests/test_demo_only_guard_ci.py | `_stat_kind` via os.lstat; magic table per allowed ending; marker regular and empty; symlink check first; copy = tracked_paths; strip GIT_*; argparse refusal; CI copy args | chmod 000 non-root; foreign blobs named .png etc; marker with content or as link; tracked credentials folder copied, untracked .pgpass not; GIT_DIR set | each guard line | all new tests fail on old code |
| C (R5-4, R5-9) | tests/test_mode_banner.py, tests/banner_mutants.py, tests/test_banner_mutant_table.py | odd entries from GOOD_DEMO; J row for isText(tag)/(text); real expect fragments; `old != new` and generic-expect check; B28 re-pointed or removed with reason | planted generic expect and old==new reported | the J row | survivor shown on old table |
| D (R5-8) | CHANGELOG.md, mode_banner.py, demo_only_guard.py, mode_banner.js | wording from the code; `reserved_words` in BannerWords; suffix list compared by test | test comparing CHANGELOG suffix list and escapes with code | none (wording) plus the reserved_words mutant | key-word test fails on old code |
| E (R5-11) | mode_banner.py, mode_banner.js, probe, tests | words required; generator accepted; tag length; safe except; comments and names | one test per item | one per behavioural item | each behavioural test fails on old code |

Done when: the table is all good at its new row count, `HADAVIN_REQUIRE_NODE=1` banner and guard tests pass, full suite green (Postgres UTF8 with PGHOST/PGPORT in the server environment), stage mutants 37 of 37, ruff and bandit clean, gitleaks clean, handover-files check exit 0, and NOTES list every fix with its test and mutant id.

## Round 6 and evidence
- **Round 6 is required** (security and mode-safety path: one more fresh pass, a round with 0 Blocker and 0 Major is the only way out). Fix minors from round 6 in the same push without another review.
- **Evidence the final head needs (independent runner, UTF8 Postgres, own folder):** full pytest; banner mutants (all rows, new count); stage mutants 37 of 37; the guard tests with `HADAVIN_REQUIRE_NODE=1`; the node probe; fail-before on 3d7967cb; hostile probes extended with: a non-root run over a tracked folder of mode 000, a foreign-format blob under each allowed ending, a marker with content and as a symlink, a tracked `credentials/` folder in the copy, a copy run with `GIT_DIR` set, a dev-only kind added to `NOT_PROD`, a non-English `BannerWords`, two tool modules with one manifest, a generator for `egress_hosts`; ruff, format, bandit, scan_repo, gitleaks, handover-files check. Evidence at the head that is pushed, not an earlier one.
