Status: resolved

# Goldfish Annotated Review Report: part 6 (mode banner, demo-only guard), round 3

**Target:** `/home/user/build/snap/pdbanner-482f7dcc/DIFF.patch` (full file), head 482f7dcc, SECURITY / mode-safety path.
**Sources:** `pdbanner-482f7dcc-design-r3.md` (0 Blocker, 2 Major, 7 Minor, 2 Nit), `pdbanner-482f7dcc-codebase-r3.md` (1 Blocker, 1 Major, 4 Minor, Nits). Evidence at 482f7dcc is interim (full pytest and mutants queued); not waited for. Source and snapshot not edited. Lead check: `tools.py:585` (`egress_check(url, frozenset(spec.hosts))`) and `:493` ("in-process boundary is code review") are at head, so the Blocker is real.

## Class A: the demo sentence is false when a tool module is configured (design M1 + codebase Blocker 1)
*   **PROPOSE FIX.** Two reviewers independently found it; round 2 design M2 already named "tool" and batch 4 answered with a false premise ("a tool module reaches only those systems, hosts and sources").
*   **Choice (least coupling that keeps the banner honest):** the banner counts what a tool can reach, and says plainly what it cannot check.
    1.  `banner_from_config` gets a REQUIRED keyword `tool_specs` (no default, so forgetting it is a TypeError, never a silent "demo"). Any tool spec with a host that is not this machine adds one real key `TOOL_HOSTS` ("tool-hosts"). A caller that cannot supply the specs passes `None`, and then a non-empty `tool_modules` counts as one real key `TOOL_MODULES` (fail closed).
    2.  The sentence about tool code that opens its own sockets cannot be checked by config at all. Reword the demo text, the docstring and the CHANGELOG to: tool modules are reviewed, not sandboxed in-process; the banner counts the hosts their manifests name. Delete the false premise ("reaches only those systems") everywhere.
*   **Reuse, not a rebuild:** read specs through the same registry loader (`_load_tools`) the app uses; do not parse manifests again.
*   **Test:** demo config (`llm: fake`, `store: memory`, no systems, egress hosts or sources) plus `tool_modules: [mymod]` and a manifest `hosts: [records.example.com]` gives the real banner naming `tool-hosts`; same with a loopback-only manifest gives demo; `tool_specs` omitted raises TypeError; `tool_specs=None` with a tool module gives `tool-modules`; no tool modules gives demo (control).
*   **Mutant:** drop the tool count (test killed); default `tool_specs=()` (TypeError test killed); treat `None` as empty (killed).
*   **Fail-before:** the first test fails on 482f7dcc (demo banner returned).
*   **Round needed:** confirming round (fourth, fresh).

## Class B: page script can end with an empty banner (codebase Major 2)
*   **PROPOSE FIX.** File `templates/mode-banner/mode_banner.js:78-110`: compute the fallback text first and write it before clearing; if the last-resort write throws, leave the previous text in place and unhide. Test `test_a_failed_last_resort_write_never_leaves_the_banner_hidden` also asserts the text is non-empty; probe `failing-all-writes` asserts it. Mutant J12 gains a second row (clear-before-write) that is killed by the text assertion. Fail-before: the text assertion fails on 482f7dcc (text is ''). Confirming round.

## Class C: demo-only guard (design M2 + codebase minor 6)
*   **PROPOSE FIX.** File `tools/demo_only_guard.py` (:152-155, :268, :279-292, :316).
    1.  NFKC-normalise each line and each path segment before matching (fullwidth `ｄｅｍｏ_ｏｎｌｙ` imports `demo_only` by PEP 3131). Test: a `.py` file with the fullwidth import, and a fullwidth folder name, are hits. Mutant: drop the normalisation. Fail-before: both pass on 482f7dcc.
    2.  Files with the endings `.pyc .so .zip .whl` inside a product root are refused as a hit (`binary-in-product-root`) instead of skipped; other binary endings are byte-searched for the name in UTF-8, UTF-16LE and UTF-16BE spellings. Test: a `.pyc` in a package dir, a `.whl` holding the name, UTF-16LE text without BOM; real PNG without the name stays clean. Mutant: skip them again.
    3.  Missing tests and mutants named by the codebase reviewer: a real binary with a UTF-8 error and NO NUL byte (kills deleting the `UnicodeDecodeError` branch), a submodule in `exempt` (kills dropping `and rel not in exempt`), a gitlink whose folder is missing (decide: a hit, fail closed). Read the file once (`_looks_binary` and `_scan_file` share the bytes).
    4.  CHANGELOG: replace "skipped only when it really is binary" with the real rule.
*   Confirming round (security path, the bypass changes what the guard catches).

## Class D: banner parser parity, duplicates, tests (design minors 3-9, codebase minors 3-5, nits)
*   **PROPOSE FIX** (batch only, checked in the fourth round):
    1.  `_url_leaves_this_machine` mirrors `tools.py:560-566`: a backslash, whitespace, control character, non-ASCII, `%` or `@` in the URL counts as leaving (so `https://evil.example\@localhost` is real). Test table with those inputs. Mutant per condition.
    2.  Loopback logic: reuse `guard.http.LOOPBACK` and `guard.egress.normalise_host` (and `app._source_host` for sources) instead of a fifth private copy; use ASCII `lower()` plus an ASCII check instead of `casefold`. If the existing helpers are private, promote the smallest one to a public name in its own module (one source of truth), no copy. A repo test (or the existing one) asserts the banner module keeps no loopback list.
    3.  Same name rule in Python and JS: whole word, same boundary characters (letters, digits, `.`, `_`, `-` all count as word parts in both); `_check_what_is_claimed` uses the rule, not `in`; an empty claim string is an error, not a skip. Test: "CRM" inside "CRM-lite" and "pre-CRM" is not a match on either side.
    4.  Fail closed: a real `Config` that loses `systems`, `egress_hosts` or `sources` raises; real-`Config` tests for `egress_hosts` and `sources`; declare the fields in `ConfigLike`.
    5.  Limits stated next to the sentence and in the CHANGELOG: loopback is not "nothing real" (port-forward, tunnel, sidecar); the banner is computed at call time and a caller that caches it can go stale (document, no code).
    6.  Mutant rows: J14 prefix (`xCRM`) and partial-then-whole (`CRMS and CRM`); a `systems` case with a non-loopback IP literal (B23); specific `expect` text for B20-B25 (one condition each); B25 `source.settings` build-failure path; B28 fixture uses a name that is not in the text.
    7.  Nits: add `EXTERNAL_SYSTEMS`, `EGRESS_HOSTS`, `READ_SOURCES`, `TOOL_HOSTS`, `TOOL_MODULES` to `__all__`; module docstring "Rules the tests pin" lists the endpoint fields and the claim check; revert the unrelated line-wrap in `tests/test_workflow_files_parse.py` or say why it is in the diff.

## Declined
*   None of substance. Reviewer text that a repo test bans private loopback lists could not be found by the codebase reviewer; the fix does not rely on it.

## Stop rule and order
One fix batch for A-D, gates once at the final head (full suite, stage and banner mutants, lint, bandit, gitleaks), independent evidence at the final head, then a FOURTH fresh round (security / mode-safety, no cap). Minors are fixed in the same push.

## Handoff
*   Accepted fixes (PROPOSE FIX): 4 classes covering 2 Majors + 1 Blocker (deduplicated to 3 findings) and 9 Minors/Nits
*   Contested: 0
*   Escalated: 0
*   Declined: 0
*   Remaining unaddressed: 0 in this report; all open until built and verified (ledger PDBANNER-r3-1..4)
