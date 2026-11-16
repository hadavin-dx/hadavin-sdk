# pdbanner-a16b7635-codebase-r4: Part 6, head a16b7635, round 4, persona codebase details

Source: hand-back of agent aaabf7117e5d8c746, saved by the lead (condensed). Read-only; nothing executed. Used an older disk checkout for files missing from the snapshot (guard/http.py, guard/egress.py, tools.py, registry.py, config.py): findings that depend on them are marked. 0 Blocker, 3 Major, 8 Minor, Nits. Not clean.

## Major
- **M1** Bare-host path looser than the URL path, fail-open (mode_banner.py:292-295 `_is_this_machine`, used :345 egress_hosts and :360 tool hosts). `_url_leaves_this_machine` rejects whitespace, controls, non-ASCII, `%`, `@` first; bare hosts do not, so `normalise_host` (NFKC and strip) makes "localhost\n", " localhost", full-width and "ˡocalhost" (U+02E1) read as this machine, and a demo banner keeps "Nothing here is set up to send data". egress_hosts has no validation (disk config.py:441-450). Fix: require `host.isascii()`, no strip difference, no control or whitespace before normalise_host. Test gap: no non-ASCII or padded bare host in egress_hosts or a tool spec; B37 is killed only through the URL list.
- **M2** Probable CI lint failure E402: `from hadavin_sdk.tools import ToolSpec` mid-file at tests/test_mode_banner.py:722 (ci runs `ruff check src tests demos tools`). Move to the top block. Builder evidence does not list ruff on this.
- **M3** Mutant search strings not unique in tools/demo_only_guard.py: G5c `re.IGNORECASE)` matches lines 165 and 339; G14b matches lines 361 and 369. Effect depends on runner (first, all, or one-occurrence assert). Make unique (include the `except UnicodeDecodeError:` line, or `_name_pattern`'s return).

## Minor
- m1 stale docstring `ConfigLike` (mode_banner.py:262-263): says "when it has them"; `_field` now raises.
- m2 CHANGELOG (:214-215): "each file read once" false for loaders and `_gitlinks`; "this machine means exactly localhost, 127.0.0.1, ::1" overstated (LOCALHOST, trailing dot, padded/NFKC spellings; bare "[::1]" now outside, a round-3 behaviour change unmentioned); first sentence omits `words` and keyword `tool_specs`; `source_endpoint` not mentioned; .gz and UTF-32 limits missing.
- m3 tool-host loopback exemption dead in production (disk tools.py forbidden_host refuses IP literals and loopback); the test builds a spec that cannot load; add a code comment.
- m4 test name over-claims: `test_a_real_registry_tools_mapping_is_what_the_banner_reads` never builds a Registry; B36 pins only forwarding.
- m5 limits omit callables passed to `app.build(tools=...)`.
- m6 guard coverage: `.gz` byte-searched only (zip and whl refused); UTF-32 not found; NFKC not applied to the byte search; binary branch skips allowed-phrase and fake-id checks; no mutant on `_nfkc(part)` for product roots (guard :242).
- m7 an exempt submodule can never be clean (exempt entries must be files; stale-exempt-entry always).
- m8 mode_banner.py now imports guard.http, guard.egress, sources.kinds at top level (pydantic, kubernetes adapter, ssl) for a thin module.

## Nit
`_byte_patterns` compiled per file (compute once); duplicate or fragile tests (failed page write twice; docstring grep "reaches only"; "ipaddress" absent from whole source); NAME_TABLE lacks rows for space/dot/hyphen names, name at start or end, digit before, double dot; `tool_specs: object` and non-mapping inner value raises AttributeError; `app._source_host` lowercases only (reuse chance); overlong docstring lines; G14 row name stale; tests-py312 does not set HADAVIN_REQUIRE_NODE.

## Answers
LOOPBACK and normalise_host reused by identity; URL parity sound for URLs (equals tools.py `.lower().rstrip(".")`); bare-host path is the exception (M1). `source_endpoint` and `_source_host` a pure refactor, callers app.py:141, :376. Python/JS name rule agree on every NAME_TABLE row (run through node). `tool_specs` keyword-only, no production caller in the snapshot. NFKC order correct in guard; UTF-16 LE/BE searched. All other re-pointed and new mutant rows match exactly once with a killer present.

## Not checked
Anything executed (pytest 10208, stage 37/37, mutants 130/130, ruff, node, mypy); tools/mutation_runner.py replace behaviour; current-head versions of guard/egress, guard/http, tools, registry, config; manifest hashes; some DIFF hunks; import cycles; Python 3.12 NFKC tables.
