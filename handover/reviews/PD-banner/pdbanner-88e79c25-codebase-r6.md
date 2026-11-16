# pdbanner-88e79c25-codebase-r6: Part 6 batch 6, head 88e79c25, round 6, persona codebase details

Source: hand-back of the codebase reviewer (agent a28abade8a6908b69), saved by the lead (condensed). MODE-SAFETY path. Static read only (no code, node, pytest or mutation runner run; not in snapshot: tools/mutation_runner.py, backends/table.py, guard/egress.py, guard/http.py, tools.py). Verdict: 1 Blocker (a wrong CHANGELOG claim), 3 Major, many Minors, Nits.

## Blocker
- **B1** CHANGELOG.md guard entry, bullet "What a file's content decides": says "a zip, gzip, ELF, Mach-O, PE or similar by its first bytes whatever its ending". `_magic_kind` (tools/demo_only_guard.py:270-289) knows only zip, ELF, gzip, bzip2, xz, tar, compiled Python; the test file says PE and Mach-O have no special rule (tests/test_demo_only_guard.py:1054 `FOREIGN_HEADERS`). A `blob.dat` starting `MZ\x90\x00` is refused only incidentally (not valid UTF-8); a PE image that is valid UTF-8 is not refused. `test_the_changelog_lists_the_refused_endings_the_guard_refuses` (tests/test_demo_only_guard_ci.py:81-90) checks only the text before " by ending". Module docstring (14-16) is right.

## Major
- **M1** Same bullet: "Any other file is read as text when valid UTF-8 without a NUL byte; otherwise its bytes are searched ... UTF-8, UTF-16 and UTF-32" is false for files whose ending is not on the skip list: not valid UTF-8 is refused as `unreadable-file` and never byte-searched (demo_only_guard.py:534-540; test at tests/test_demo_only_guard.py:222-229).
- **M2** mode_banner.py:482-487 and 211-212: a one-shot iterator for `egress_hosts` is accepted ("read once", pinned by test_mode_banner.py:1599-1608). `cfg.egress_hosts = (h for h in ("api.example.test",))`: first `banner_from_config(cfg, tool_specs={})` gives tone real; if the config property returns the same exhausted generator, a second call gives tone demo and "made-up demo data" over real hosts (the fail-open the module forbids). Require a `Collection` or return a fresh iterable; test the banner built twice. (bytearray/memoryview iterate as ints: safe direction.)
- **M2b** tests/banner_mutants.py:1461 row G88 expect "DID NOT RAISE SystemExit": pytest prints `DID NOT RAISE <class 'SystemExit'>`, so the fragment probably does not match and the row would be BAD (the 200 of 200 claim then conflicts: check against the runner). Use "DID NOT RAISE".

## Minor
- mode_banner.py:81 comment says NOTHING_CONNECTED "not derived from any other table" but the detector pair uses `DEFAULTS["detector"]` (pinned by literal "regex" test:1440-1444): reword.
- Module docstring limit (2) "or only manifests with an empty hosts list" vs code 463 (a module with ANY host-less spec is unaccounted): fix text.
- B10c name inverted ("kinds that connect to nothing are listed as real"; it adds ed25519_local to the allow-list); B10c and B10g share killer and message.
- B59 expect `url 'http://[::1]:80x/'` is the first failing URL only where `urlsplit` raises on index 13 of LEAVING_URLS (version dependent; mutants step runs only on 3.13: latent).
- B63 test vacuous for its stated reason (no exception text contains internal-host; killed only through the SimpleNamespace clause; "no name in the log line" untested). B54 expect "has no attribute 'items'" holds only if the runner reads the chained traceback. B13 expect "AttributeError" only a type name. G73 "' in []" and G80 "PermissionError: [" are pytest-rewrite fragments, not messages.
- Rows with bare "DID NOT RAISE" cannot show which input slipped (B2, B2b, B3, B3b, B3c, B3d, B26, B27, B45, B80-B83, G10, G11, G20, G90; B3 vs B3d indistinguishable). J23 removes isText(tag) and isText(text) as one row.
- JS length unit: Python counts code points, page counts UTF-16 units (mode_banner.js:21 vs mode_banner.py:269-273); safe direction, but no test of exactly 600 characters on the page. JS and Python accept whitespace-only tag or text (blank banner against "never blank").
- mode_banner.js:88-92 case (a): old text (possibly the made-up claim) stays under tone unconfirmed; CHANGELOG "old text stays under the old mode" omits the tone change.
- Test names that overclaim: `test_a_url_and_a_bare_host_give_the_same_answer_for_every_spelling` (one direction only, second assert is the contrapositive); `test_every_symlink_under_a_product_root_is_a_hit` check 2 (three dangling links = one case); "check N" numbering in the size-cap test skips check 3 and the message there is bare.
- CI test tests/test_demo_only_guard_ci.py:43-49 comment says node check comes before tests needing node, but in ci.yml the copy run (line 90) runs before `node --version` (92); the `HADAVIN_REQUIRE_NODE: "1"` check is a substring match on the step block (a YAML comment would satisfy it).
- Design gap: webp, ttf, otf cannot be listed (`load_config` refuses an ending without a mark, demo_only_guard.py:159-163): a product .ttf/.otf/.webp under templates/ is refused as unreadable-file with no way to allow it.
- Global git excludes (demo_only_guard.py:220-235): GIT_* stripped but HOME and XDG config (core.excludesFile, XDG ignore, .git/info/exclude) still hide untracked files from `--others --exclude-standard`; docstring mentions only .gitignore.
- No test proves `config.tool_modules` strings match the `function` module part of real specs (safe direction if mismatched).

## Nits
CHANGELOG:28 signature omits `words`; demo_only_guard.toml:37-38 lists "png, jpeg, gif..." and omits jpg; B56's first assert cannot fail under that mutant; test_mode_banner.py:489-490 same scenario twice.

## Verified correct
NOTHING_CONNECTED content `{("signer","none"), ("anchor","none"), ("detector", DEFAULTS["detector"])}` pinned by literal equality (B10c, B10g, B10f); unlisted kinds real, DEMO_ONLY first; tool module without manifest host real (B32, B55, B85); all eight ENDING_MARKS magic numbers right and `_magic_kind` marks right; `_stat_kind` (G80, G41); marker and exempt file shape (G83-G86, G17); copy run exactly tracked minus folder and marker (G68, G8), GIT_* stripped (G69), allow-list env (G18, G67), modes exclusive (G87, G88), notice (G89); CI copy step and HADAVIN_REQUIRE_NODE per step; JS textContent only, odd banners give NOT_CONFIRMED; mutant table 200 unique labels, every old text occurs once by eye, no old == new, no line-number references; B3f/B8/B9 each fail the single assert at test_mode_banner.py:122.

## Not checked
Code not run; the files above; real `DEFAULTS["detector"]`, `normalise_host`, `LOOPBACK`; runner's "first failing line" rule; whether the allowed_phrases occur in product files.
