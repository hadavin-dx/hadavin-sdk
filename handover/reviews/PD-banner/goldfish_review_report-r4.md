Status: resolved

# Goldfish Annotated Review Report: Part 6 round 4

**Target:** `/home/user/build/snap/pdbanner-a16b7635/DIFF.patch` (full), head a16b7635. SECURITY path (no round cap).
**Inputs:** `pdbanner-a16b7635-design-r4.md` (2 Major, 11 minor, 8 nit) and `pdbanner-a16b7635-codebase-r4.md` (3 Major, 8 minor, nits). 0 Blocker.
**Resolver:** lead session via egm-resolve (Opus). Automated: recommended option for every item.

Handoff: 33 findings in total. Accepted fixes (PROPOSE FIX): 30. Contested: 0. Escalated: 0. Declined: 3 (codebase m8 top-level imports, design n4 host in the fallback text, overlong docstring lines). Remaining unaddressed: 0 until the fix batch lands. Round 5 is REQUIRED (security path needs a clean round).

## Root causes (six classes; fix each at its choke point)

The round has one theme: the banner still has two ways to read the same fact (a bare host and a URL; a tool spec that is real and one that is missing), and its claims are wider than what tests pin.

### Class A: one host validator for bare hosts and URLs (codebase M1, design m3)
`_is_this_machine` (mode_banner.py:292) accepts "localhost\n", " localhost", full-width and U+02E1 spellings because only `_url_leaves_this_machine` rejects whitespace, controls, non-ASCII, `%`, `@` first. Egress hosts and tool hosts use the weaker path.
- **PROPOSE FIX.** Move the pre-check INTO `_is_this_machine`: a host counts as this machine only if it is `str`, non-empty, `isascii()`, has no whitespace or control character, equals its own `.strip()`, and then `normalise_host(host) in LOOPBACK`. The URL function keeps its URL-only checks and then calls the same function.
- Decision on design m3: the stricter reading wins everywhere (a full-width host is "leaving", in a URL or a host list). State it in the docstring and CHANGELOG.

### Class B: `tool_specs` must fail toward showing the risk (design M1, nit on typing)
- **PROPOSE FIX.** In `_services_in`: every spec must have `hosts` as a tuple or list of `str`; a spec without it raises `TypeError` naming the tool. An inner value that is not a Mapping raises `TypeError` (not `AttributeError`). Non-empty `tool_modules` with an empty mapping (no spec at all) adds `TOOL_MODULES` (the same as `None`). Type the parameter `Mapping[str, Mapping[str, ToolSpec]] | None` (import under `TYPE_CHECKING` only, so no load-time cost). Re-point B34 to the new messages.

### Class C: parity with the tool client is a pinned property, not a claim (design M2, nit n5, n8; codebase m3, m4)
- **PROPOSE FIX.** Tests: (1) `LOOPBACK == {"localhost","127.0.0.1","::1"}` pinned by contents; (2) a parity test that feeds every row of `LEAVING_URLS` (and every `THIS_MACHINE` row) to the tool client's own validator (`forbidden_host` / the url check in `ToolContext.fetch`, read from the real `tools.py` in the repo) and asserts the banner is at least as strict (banner says leaving whenever the client refuses a host or a url); (3) reject any text after `]` other than `:port`, `/`, `?`, `#` and add `http://[::1]evil.example/` and `http://[::1]:80x/` to `LEAVING_URLS`; (4) the CHANGELOG says "modelled on the connection guard's loopback names and normaliser, and at least as strict as the tool client", not "exactly the way". (5) Rewrite the test named `test_a_real_registry_tools_mapping_is_what_the_banner_reads` to build a real `Registry` (or name it for what it checks). (6) Code comment that a tool-host loopback exemption cannot occur in production (the manifest refuses loopback), kept for fail-safe reading.

### Class D: lint and mutant-table hygiene (codebase M2, M3; design m11, n1, n3)
- **PROPOSE FIX.** Move `from hadavin_sdk.tools import ToolSpec` (tests/test_mode_banner.py:722) to the top import block; run `ruff check src tests demos tools` and `ruff format --check` before pushing (the builder's evidence omitted ruff on this file). Make G5c and G14b search strings unique (include the `except UnicodeDecodeError:` line, and the `_name_pattern` return), and add a table self-test that every row's search text occurs exactly once in its file. Tighten the roughly 40 loose `expect="assert"` rows (B6, B7b, B8, B9, B10*, G1, G2, J2-J9, B23) to a fragment unique to the intended assertion (give each killer a message). Add mutants: `_field` type check, the `getattr(spec,"hosts",None)` default (Class B), `names_in("")`, egress `not` inside `any(...)`, `at >= 2`, `setAttribute` order, the bare-host pre-check pieces (isascii, strip, control). Renumber duplicate J11 and J12. Make `_check_what_is_claimed` match the formatted names segment only. Add NAME_TABLE rows: a name with space, dot or hyphen; a name at the start and at the end; a digit before; a double dot.

### Class E: claims wider than the code (design m1, m2, m4, m5, m6; codebase m1, m2, m5; design n2)
- **PROPOSE FIX** (all):
  - m1: add `banner_or_unconfirmed(config, tool_specs, ...)` that catches `Exception`, logs one line without the config values, and returns `not_confirmed()`; docstring says "a banner is always shown" only for that function and says plainly that `banner_from_config` raises.
  - m2 and codebase m5: limits list adds `app.build` overrides (`tools=` callables, `sources=`, `channel=`, `llm=`, `detector=`, `secrets=`), `localhost` trusted to resolve to loopback, page cache and config reloads, stand-in kind settings never inspected, callables handed to `app.build(tools=...)`.
  - m4: derive the reserved claim-word set from `words`; state that service names are ASCII only.
  - m5: in `fill`, set `data-tone` before the text; reword "never leaves the banner blank" to what holds.
  - m6: the page trusts `tone` (Python checks the made-up sentence); state it.
  - Codebase m1: fix the stale `ConfigLike` docstring. m2: CHANGELOG fixes ("read once" applies to files, not loaders or the git link call; LOCALHOST and trailing dot also count; a bare `[::1]` now counts as leaving, a round-3 behaviour change; the first sentence shows `words` and keyword `tool_specs`; mention `sources.kinds.source_endpoint`; guard limits for .gz and UTF-32). Design n2: remove the stale first sentence.

### Class F: demo-only guard fails closed everywhere (design m7, m8, m9, m10, n6, n7; codebase m6, m7, nit)
- **PROPOSE FIX** (all):
  - m7: an unreadable file under a product root is an `unreadable-file` hit, not a skip.
  - m8: check magic bytes (`PK\x03\x04`, `\x7fELF`, gzip `\x1f\x8b`, and pyc magic) whatever the extension; refuse `.gz`, `.tar`, `.tgz`, `.bz2`, `.xz` like `.zip`.
  - m9: search UTF-32 LE and BE too; add a size cap (a file over the cap is a hit, not read into memory); name in the limits: compile-time spellings, NFKC not applied to bytes inside binaries, fake-id patterns not run on binary files.
  - m10: print each path with control characters escaped, and a leading `::` shown as `\x3a:`.
  - n6: the `--without-folder` child gets an allow-listed environment and does not copy untracked secrets files such as `.env`.
  - n7: `d in loaders` compares the right kind (file or folder). Codebase m7: an exempt entry may be a git link (a clean exempt submodule gives no hit; a missing one gives `stale-exempt-entry`). Compute `_byte_patterns` once in `scan`. Add a mutant on `_nfkc(part)` for product roots. CI `tests-py312` job sets `HADAVIN_REQUIRE_NODE=1`.

## Declined (recorded, not fixed)
- **codebase m8** top-level imports of `guard.http`, `guard.egress`, `sources.kinds` in mode_banner.py: the coupling is the point (one source of truth for loopback names); Class C pins it. DECLINE.
- **design n4** name the outside host in the fallback `component tool-hosts` text: the 40-character budget and masking rules make it unsafe; DECLINE.
- **overlong docstring lines**: E501 is not selected; DECLINE.

## Findings table

| Finding | Severity | Class | Suggestion |
|---|---|---|---|
| design M1, codebase M1 | Major | B, A | PROPOSE FIX |
| design M2 | Major | C | PROPOSE FIX |
| codebase M2, M3 | Major | D | PROPOSE FIX |
| design m1-m6, codebase m1-m5 | Minor | E, C | PROPOSE FIX |
| design m7-m10, codebase m6-m7, n6, n7 | Minor/Nit | F | PROPOSE FIX |
| design m11, n1, n3, nits | Minor/Nit | D | PROPOSE FIX |
| codebase m8, design n4, line length | Minor/Nit | - | DECLINE |

## FIX BRIEF (one small builder, one push; batch 5 of this lane)

Branch: build on `wip/cloud-pd-banner` head a16b7635 (worktree under /home/user/build/wt/, never cd the main shell into it). Heavy jobs only through heavy.sh. No handover/(evidence|reviews|tickets) files on this branch (ORDER 266). Fix every class below in one batch; report once.

1. **Class A** (`src/hadavin_sdk/mode_banner.py`): move the pre-check into `_is_this_machine`. Tests: `THIS_MACHINE` and `LEAVES` rows for "localhost\n", " localhost", "ｌｏｃａｌｈｏｓｔ", "ˡocalhost", tab, NUL, in `egress_hosts` and in a tool spec; a URL row for each. Mutants: drop isascii; drop strip equality; drop control check; bare path calls `normalise_host` only (each killed with a message unique to its test). Fail-before: new tests fail on a16b7635.
2. **Class B**: strict `hosts` (tuple or list of str, else `TypeError` naming the tool), non-Mapping inner raises `TypeError`, modules plus empty mapping gives `TOOL_MODULES`, typed parameter. Tests for each; mutants on the `getattr` default, the empty-mapping rule and the type check; re-point B34.
3. **Class C**: pinned `LOOPBACK` contents, parity test against the real tool client validator, `]` tail rule and two new `LEAVING_URLS` rows, real `Registry` test, wording fixes. Mutant: `LOOPBACK` widened in the banner copy (killed by the contents test); tail rule dropped.
4. **Class D**: fix the import; unique search strings plus a table self-test (a row whose text occurs twice makes the self-test fail: prove it by a planted duplicate); tighten `expect`; the new mutants and NAME_TABLE rows listed above; renumber J11 and J12. Gate: `ruff check src tests demos tools` and `ruff format --check` exit 0 BEFORE pushing.
5. **Class E**: `banner_or_unconfirmed`, docstring, limits, `fill` order, CHANGELOG. Tests: raising config returns `not_confirmed()` and logs one line without values; node test that a failing `setAttribute` keeps the right tone with the text; limits text pinned by words, not by a grep of "reaches only".
6. **Class F** (`tools/demo_only_guard.py`, `tools/demo_only_guard.toml`): unreadable-file hit; magic bytes; refused archives; UTF-32; size cap; escaped paths; allow-listed environment; exempt git link; once-only `_byte_patterns`; CI env line. One test and one mutant per item; fail-before for each.
7. **Evidence the builder records** (its own, at the final head; the lead runs the independent runner): bind and banner mutants all good (the table grows; no rows dropped), stage mutants 37 of 37, ONE full suite via heavy.sh with a priority and exit code, ruff check and format, bandit -ll, scan_repo, node tests with `HADAVIN_REQUIRE_NODE=1`, gitleaks, check script `check-no-handover-files.sh`. Checkpoint every 30 minutes; stop at 60, commit, report.

## Stop rule
Security path, no cap. Round 4 had 5 Majors, so one fix batch (above) then round 5 must find 0 Blocker and 0 Major from fresh reviewers (design and codebase). Minors from round 5 are fixed in the same push as ORDER 256 allows only after a clean round. If round 5 finds a new form of Class A or B, fix the shared validator, not the form.

## Evidence the final head needs (for the independent runner)
Full suite exit 0 with the exact count; banner mutants all good (count stated); stage mutants 37 of 37; fail-before against a16b7635 for the new tests (each class listed); ruff, bandit, scan_repo, gitleaks exit 0; node banner tests with `HADAVIN_REQUIRE_NODE=1` run (not skipped); hostile probes: bare hosts with newline, padding, full-width, U+02E1; a spec without `hosts`; modules with an empty mapping; a renamed zip, a gzip, an unreadable file and a path with a newline under a product root for the guard.
