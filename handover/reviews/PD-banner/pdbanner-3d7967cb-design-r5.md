# pdbanner-3d7967cb-design-r5: Part 6 batch 5, head 3d7967cb, round 5, persona design

Source: hand-back of the design reviewer (agent adc5a7677), saved by the lead (condensed). Mode-safety path (clean round needed). Static read of snapshot `/home/user/build/snap/pdbanner-3d7967cb`; no code run; snapshot lacks tools.py, guard/egress.py, guard/http.py, backends/table.py, config.py (so normalise_host, LOOPBACK, NOT_PROD, Config.systems type, ToolContext.fetch, CI Python version not checked). 0 Blocker, 3 Major, 6 Minor, nits. Classes A, B, D, E hold; C holds for URL syntax only; F has holes.

## Major
- **M1** `_NOTHING_CONNECTED = NOT_PROD | {detector regex}` (mode_banner.py:114, :483) ties "connects to nothing" to the prod-gate table. A kind later added to NOT_PROD for being dev-only (dev secrets, openai_compat to a dev server, local Vault) silently drops from the "real" list and a demo banner says "made-up". No test pins its contents. Fix: explicit allow-list of (component, kind) pairs, pinned by a test; unlisted = real. Unconfirmed as an existing bug (NOT_PROD not read).
- **M2** demo_only_guard.py:465-469 (suffix list :72-75): a non-text file with an allowed ending (.png .jpg .gif .ico .pdf .woff .woff2) is searched only for the folder name as raw bytes; `_magic_kind` knows only zip, ELF, gzip, bzip2, xz, tar, pyc. zstd, 7z, rar, lz4, PE, Mach-O or any compressed JSON named logo.png passes; docstring "renaming it to .png does not help" overstated. Fix: require the real magic bytes of each allowed type, refuse otherwise.
- **M3** demo_only_guard.py:360-372: `Path.is_symlink/is_dir/is_file` swallow some errors on some Python versions; EACCES on a parent can make `lexists` False and the "listed by git but gone" branch `continue`s, skipping an unreadable entry. Fix: `os.lstat`, only FileNotFoundError = gone, other OSError = hit. Input: tracked `src/pkg/` mode 000, non-root user.

## Minor
- **m4** exempt files and marker skipped whole (:319, :382-383): `tools/demo_only_guard.copy_run` ("empty") content never read; exempt check before symlink check. Marker must be a regular empty file, exempt files not symlinks.
- **m5** `--require` silently ignored with copy-run flags (:589-597): make it an argparse error.
- **m6** CI copy run passes no pytest args (ci.yml new step, test_demo_only_guard_ci.py:29 pins the line): runs live and perf tests; allow-list drops HADAVIN_TEST_PG_DSN and HADAVIN_REQUIRE_PINNED_UNIDATA so those skip. Add `-m "not live and not perf"` and pin.
- **m7** CHANGELOG/docstring overstatements: line 215 "no token or key of the caller reaches the child" true only for env vars (HOME, PATH allowed); suffix list shorter than REFUSED_SUFFIXES (:78); UTF-32 missing from the text; line 214 "never leaves the banner blank" vs mode_banner.js:98-101; banner_from_config shown as the one way in without required `tool_specs`; empty-mapping case not mentioned; mode_banner.py:30-31, :166-170 reserve only the whole claim sentence, not the key word (Spanish "inventados"); non-ASCII sentence vacuous under the ASCII name rule.
- **m8** class C parity pin covers URL syntax only (tests/test_mode_banner.py:1095-1148); system `base_url` type (str vs AnyUrl) unchecked; other URL fields (auth, token) not read.
- **m9** several tool modules, manifest for only one (mode_banner.py:454-457): `modules and count == 0` fires only with no specs; spec with `hosts=()` and a module reads "nothing real". Compare modules to resolved specs, or state as limit.

## Nits
`_under` case-sensitive; phrase `DEMO_ONLY` matches quoted path; git subprocess inherits GIT_DIR/GIT_INDEX_FILE/GIT_WORK_TREE (strip GIT_*); test name "give the same answer" overclaims (one-directional); mode_banner.py:344 "cannot occur in production" (spec_problems not read).

## Holds
Class A `_is_this_machine` single decider (mode_banner.py:335-347; odd host forms read as leaving); class B required tool_specs, every spec read, banner_or_unconfirmed logs no values; class D 180 rows, non_unique_rows; class E CI node step, JS tone-first; class F suffix list, magic, size cap twice, unreadable/pipe/socket hits, allow-listed env, git failure stops, printable escapes.
