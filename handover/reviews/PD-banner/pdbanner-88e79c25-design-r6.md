# pdbanner-88e79c25-design-r6: Part 6 batch 6, head 88e79c25, round 6, persona design

Source: hand-back of the design reviewer (agent a5c4e4876d5ffc4ad), saved by the lead (condensed). MODE-SAFETY path (no round cap). Static read only; not read: backends/table.py (not in snapshot), the mutant table and rewritten expectations (class C not judged), the DELTA patch, guard tests, CHANGELOG after line 337; it could not identify D-n1 and D-n2. Verdict: 0 Blocker, 1 Major, Minors and Nits. Classes A and B hold at their choke points with residuals; class D has wording defects.

## Major
- **M1** CHANGELOG lines 216-219 omit limits (1) loopback is a port-forward, (4) `localhost` resolution and (6) `app.build(tools=, sources=, channel=, llm=, detector=, secrets=)` overrides invisible to the banner; the module docstring states them. `sources=` objects are refused only in pilot and prod, so in the demo stage `build(sources=<real kubernetes object>)` with a stand-in-only config gives tone "demo" and "Every record here is made-up demo data". Add all three limits to the CHANGELOG; if cheap, have `app.build` refuse or flag overrides in demo mode.

## Minor
- **m2** mode_banner.py:125-127, 74-75 docstrings use history phrases ("the same as before this list was explicit", "older public names ... are gone").
- **m3** mode_banner.js:88-92 and CHANGELOG:218: when the tone write works and the text write fails, the old text (possibly the made-up sentence) stays under tone "unconfirmed" with stale `data-mode`; CHANGELOG "old text stays under the old mode" is true only for the other case. State precisely or also clear the text (`replaceChildren()`).
- **m4** demo_only_guard.py:575-591 copy run: lstat then `copy2` follows a swapped path; an absolute tracked symlink is recreated verbatim so it points at the original checkout, so the copy-run proves nothing for it; `run_without_folder` does not enforce that the scan ran first. Refuse symlinks in `copy_without_folder` or resolve targets against the copy.
- **m5** demo_only_guard.py:401, 676, 680 still use `Path.is_dir()` (swallows ELOOP, ENOTDIR); `--without-folder-if-present` returns 0 at 676 and skips the copy run; docstring line 20 and CHANGELOG:222 say only no-such-file means gone. Use `_stat_kind`.
- **m6** CHANGELOG:221 claims zip, gzip, ELF, Mach-O, PE are refused by first bytes; `_magic_kind` (270-289) detects zip, ELF, gzip, bzip2, xz, tar, compiled Python only; Mach-O and PE only via "not valid UTF-8". And "otherwise searched in UTF-8, UTF-16, UTF-32" does not match lines 534-540, 558-559 (unmarked non-UTF-8 ending is an unreadable-file hit; valid UTF-8 with NUL is text-scanned and byte-searched; byte search without text scan only for skip-suffix endings with right magic that look binary).

## Nits
- mode_banner.js:62-68 a quiet or real banner whose text holds the made-up sentence is painted (stated limit 7, honest).
- demo_only_guard.py:414-440, 397-400 exempt files and the marker are shape- and size-checked only (an 8 MiB ELF listed as exempt passes; the toml is itself exempt): state or run `_magic_kind`.
- A valid PNG mark followed by an appended archive is not scanned past 512 bytes; docstring limits do not name it.

## Holds
Class A: a component is a stand-in only if `(component, kind)` is in `DEMO_ONLY`; skipped only if in `NOTHING_CONNECTED`; unknown kind reads real (fixed-point and table-independence tests, test_mode_banner.py:1440-1464); `banner_or_unconfirmed`, `_check_what_is_claimed`, `_names_segment`. Class B: `_stat_kind` lstat with only FileNotFoundError = gone; magic before ending (line 523); every skip suffix has a mark and `load_config` refuses an unmarked ending; GIT_* stripped (223), child env allow-list; copy uses `tracked_paths(include_new=False)`. Class D: module docstring accurate (nine suffixes, UTF-16/32, banner_or_unconfirmed), `{}` versus `None` matches `_outside_endpoints`; no review-process words in the entries read.
