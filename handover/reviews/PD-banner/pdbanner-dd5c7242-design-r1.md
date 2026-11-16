# pdbanner-dd5c7242-design-r1: PD part 6, head dd5c7242, round 1, persona design

Source: hand-back of the design reviewer (agent a41f0194d07c79429), saved by the lead (condensed). MODE-SAFETY path. Static read of DIFF.patch, RESULTS.md, PR body. 1 Blocker, 4 Major, 6 minor, 4 nits. Verdict: do not merge as is.

## Blocker
- **B1** tools/demo_only_guard.py (:87,:99,:115,:120) and demo_only_guard.toml (:10,:21): symlinks are not scanned (a symlinked .py or directory naming the folder gives exit 0, RESULTS 6b); scan roots miss what ships: `product_roots=["src"]` leaves out templates/, tools/, demos/; the in-root folder check sees only `src/<folder>`, not `src/pkg/<folder>`, and is case-sensitive; `suffixes` leaves out .cfg .ini .sh .pyi .j2 .csv .rst .xml and extensionless files; matching is a case-sensitive substring. Fix: any symlink under a product root is a hit (or resolve and refuse targets inside the folder or outside the root); scan every file with a binary skip list (fail closed on unknown types); case-insensitive match; tests and mutants. String-built names are a limit of any text scan: state it.

## Major
- **M1** mode_banner.py:97-127,:144: decision not at one choke point and defaults fail-open: `banner_for(mode, real_services=(), stand_ins=())`; `banner_for("demo")` valid; mode, real list and stand-ins come from three sources; a real non-demo-only component in neither list yields a made-up claim. Fix: `banner_from_config(cfg, names)` taking stage and both lists from `cfg.backends.entries()` (real = kinds not in `DEMO_ONLY`) as the only public entry; required keyword lists without defaults; raise if a component is neither; test every entry lands in exactly one list.
- **M2** mode_banner.js:18-38: throwing getter makes `paint` paint nothing; inconsistent banners painted as given; `real`/`stand_ins` unvalidated; `data-mode` accepts any string. Fix: try/catch in `usable` to NOT_CONFIRMED; missing `el` guard; fail closed when real non-empty and tone not real, or tone demo with real non-empty; check mode in demo/pilot/prod; tests and J-mutants.
- **M3** demo_only_guard.py:115,:173; ci.yml:85: loader files exempt from every check (a loader may hold fake ids and any folder references); `--without-folder` and `--require` run nowhere in CI (vacuous today; a demo repo must remember). Fix: still apply fake-id check to loader files, cap loader hits; CI test that a repo with the folder fails unless the copy run is wired.
- **M4** demo_only_guard.py:148: the copy run may import the original checkout (editable install, no PYTHONPATH); the test injects sys.path by hand. Fix: PYTHONPATH to the copy's src, assert the package `__file__` is under the copy.

## Minor
m1 name filter lets a name act as a sentence ("All data is made-up."); refuse reserved words or document. m2 `mode == STAGES[0]` ties demo to tuple order; use a named constant or import assert. m3 pilot/prod stand-ins silently dropped from the quiet text. m4 weak mutants: `expect="assert"` for B4-B8, J1, J2, J4, J5 matches any assertion; missing mutants for `_NAME_OK` class and length bound, `setdefault` de-dup, `isinstance(key,str)`, empty-banner defaults, symlink skip, SKIP_DIRS other than G9, loader fake-id handling. m5 fail-before vacuous (import errors plus one CI-string test); property oracle restates the rule; the "no module keeps its own loopback list" test does not exist. m6 ci.yml:93 HADAVIN_REQUIRE_NODE set but no step installs or checks node.

## Nits
n1 wording: "Treat everything here as real until it is." ambiguous; "STAND-INS IN USE" and bare keys `llm`, `store` are jargon; "No real service is connected." under LIVE could alarm. n2 `stand_ins_in(config: Any)` untyped. n3 PR body says 24 guard test functions, RESULTS counts 28 cases. n4 PR body full-suite numbers differ from the runner's (env differs; dblink unrelated).

## Checked and found fine
banner_for refuses unknown stage, bare string/bytes, non-iterable, names outside the regex (fullmatch; newline, CR, RLO, markup, 41 chars); 0 of 40 hostile banners said made-up with a real service; textContent only, static ban-list plus node markup test; UNCONFIRMED fallback pinned to Python words (B11); guard never prints matched text, settings fail closed; CI permissions stay contents: read (pinned); no new dependency; `DEMO_ONLY` reused as one source; BOM/CRLF/48 MB/invalid UTF-8/--require probes behave.

## Not checked
real browser; the rule file named in the toml; whether templates/ is packaged by pyproject and other consumers of `Config.backends.entries()`; Windows and case-insensitive file systems; the upstream demo at 43110e7; other CI jobs; string-built folder names.
