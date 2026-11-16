<!-- full hand-back report of sub-agent a0759fb8, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Mode: REVIEW, implementation readiness, round 1. Target: `/home/user/hadavin-sdk/handover/tickets/Q8a-2-neutral-callback-and-guard.md` (rev 1).

No blockers. Four majors, each closed by a few sentences in the ticket. Almost every cited fact holds on main 2a8c2aa; the false ones are listed under Minors. Everything below was checked by reading and reasoning only; nothing was run.

## Majors

**M1. Section 1, `callback_path()` in receiver.py (ticket line 46): `{name}` in the error message is not defined.**
- The message is `f"channel {name}: callback_path must be a path such as /channel/actions"`, but nothing says where `name` comes from.
- Test 4 passes "a channel object with no `callback_path`"; if that object also has no `name`, `approvals.channel.name` raises AttributeError instead of ConfigError.
- The import source of `ConfigError` is not stated either.
- Add: "`name` is `getattr(approvals.channel, "name", None)` when that is a `str`, else `type(approvals.channel).__name__`. Import `ConfigError` from `hadavin_sdk.errors` (as slack_channel.py:21 does) and `CALLBACK_PATH` from `hadavin_sdk.approvals.channel`. In test 4 the 'no callback_path' object is a class that does not derive from `FakeChannel`, with `name = "bare"` and a `parse_decision` returning None; the bad values are set on a `FakeChannel` subclass. Every `serve()` call in test 4 passes `port=0` and closes the server if one is returned (on main it is returned)."

**M2. Tests, contract test `test_channel_names_its_callback_path` (ticket line 243): it sits under regression guards but is marked "Fails on main".**
- It needs `CALLBACK_PATH`, which main does not have. A module-level import in `tests/contracts/test_capabilities.py` would make the whole contract file fail to import when the test files are run against main's `src/`.
- That is the ImportError the ticket itself says does not count as proof, and it would hide every other contract test in that run.
- Add: "This is must-fail item 14. Inside the test: `from hadavin_sdk.approvals import channel as channel_module`; `grammar = getattr(channel_module, "CALLBACK_PATH", None)`; `assert grammar is not None`; then the fullmatch assertion. No new module-level import in that file. `tests/test_q8a2_callback.py` likewise never imports `CALLBACK_PATH`, `DEFAULT_CALLBACK_PATH` or `handle_action` at module level."
- "Not established" item 5 can be closed: the suite builds both kinds (`tests/contracts/kinds/builtin.py:62-65` builds fake through `make`; `channel_slack.py:10-14` yields a real `SlackChannel`), so a class attribute satisfies the test for both.

**M3. Section 2, `identifier_problems` (ticket lines 100-117): the output is not pinned, yet test 9 and probe 11 demand exact lists.**
- **Lines per name:** not stated whether a name with two words (`AwsKmsSettings` has aws and kms) gives one line or two. Add: "one line per (name occurrence, word), words sorted."
- **Repeated bindings:** not stated whether a name bound several times is reported each time. Add: "each binding node is reported at its own `lineno`; identical (module, line, name, word) lines are de-duplicated."
- **Order:** `ast.walk` is breadth-first, not line order. Add: "modules in `sorted(src.rglob('*.py'))` order; within a module sorted by (line, name, word); the module-name line comes first, at line 1."
- **Module-name message:** add "`name` in the message and in the `IDENTIFIER_OK` key is the single segment (`openai_compat`), reported once per module file; a vendor-named package folder is therefore reported once for every module under it."
- **Splitting rule:** the prose differs from the dry-run script it claims to equal. The script's `parts()` also adds the whole lower-cased snake part. Add that sentence, or say "copy `parts()` from `/home/user/build/q8a2-dryrun/dryrun.py` verbatim and return it as a set."
- **Binding forms missing from the node list (3)-(6):** `ast.ExceptHandler.name`, `ast.MatchAs.name`, `ast.MatchStar.name`, `ast.MatchMapping.rest`, and `ast.alias` with no `asname` in a `from` import. Either add the first four with one plant each, or list all five under "Not scanned" with the reason.
- **`table_names`:** clear enough as written. The 17 names equal exactly the top-level class and def names in `backends/table.py` that `_TABLE_VENDOR_NAME` matches. `GcsRetentionLockSettings`, `GuardrailSettings` and `OpenAICompatSettings` are not matched and stay scanned.

**M4. `.claude/rules/class-level-fixes.md` asks for property or fuzz tests; the ticket has example plants only.**
Add to Tests:
- "(a) For every word in `VENDOR_WORDS`, every separator in `/ _ . -` and the three positions (start, middle, end), the string gives exactly one 'vendor word in a path or key' line; the bare word gives exactly one 'bare vendor name' line.
- (b) For every word, the identifier forms `x_{w}_y`, `{W}_X`, `{w.capitalize()}Client` and `my{w.capitalize()}` hit; `x{w}y` does not.
- (c) For `CALLBACK_PATH`, generated strings containing any character outside `[a-z0-9/-]`, an empty segment, or no leading slash are all refused; a 64-character valid path is accepted and a 65-character one refused."

Test (b) will expose two limits that should go into the stated-limit sentence. Both follow from "digits stay with the letters before them":
- `slack2_url` and `aws1` do not hit.
- `AWSclient` splits as `AW` + `Sclient` and does not hit.

## Minors

1. **False claim, ticket line 93:** "no string matches both" entries. `"slack:/aws/x"` matches both. Replace with: "a string that holds one vendor word matches at most one of the two entries."
2. **Wrong line:** `sources/kubernetes.py:7` should be `:8` (the `Neutral protocol:` line).
3. **Unexplained count, ticket line 244:** "57 passed". Main's guard file has 56 `def test_` functions and no parametrised ones. State the count of existing tests (56) and the count after this ticket.
4. **Heading count:** "13 must fail on main" overstates it. Item 11 says itself it is not a fail-on-main test, so the count is 12 (13 with M2).
5. **Item 13 has no defined run on main:** `coverage_table` does not exist there. Add: "the main-side evidence for 13 is dry-run part 4.0 (`coverage_problems(TABLE, ..., EXCEPTIONS, TODAY) == []` with one source kind and no entry) and part 4.1 (AttributeError on a plain merge)."
6. **Item 12:** the `...` dates are not given. Use `date(2026, 10, 1), date(2027, 1, 1)`, as dry-run 4.3 did.
7. **Section 3 test (b):** say that `today` is `TODAY` and that the other arguments are `DEMO_ONLY, NOT_PROD, NULL_KINDS`.
8. **Receiver rewording:** lines 17 and 25-26 have no target text. Suggest `# interactive callback payloads are a few KB` and "...the outcome is audited and the channel message updated; a refused click is not an HTTP error".
9. **CHANGELOG placement:** `## Unreleased` has `### Upgrade steps` (line 5, about 228 lines long) and `### Changed` (line 277) in the tree I could read. Say "new bullets go first in `### Upgrade steps` and first in `### Changed` under `## Unreleased`" (or last; pick one).
10. **I5 consistency:** `defaults.py:42` also uses the English word "slack" in a comment. Not scanned, but the "one word, one meaning" reason for the rename suggests rewording it to "margin" in the same edit.
11. **Reuse:** `_SourceEntry` duplicates `_E` (guard:437-439, same single field). Either move `_E` above and reuse it, or say why not.

## What checked out

- **Receiver:** receiver.py lines 1, 3, 4, 5, 17, 18, 22, 25-26, 41, 47, 54 are as cited. The whole-text pattern finds exactly 9 vendor words on main (lines 1, 3, 4, 17, 18, 22, 26, 41, 54).
- **Other source citations:** all as cited — channel.py:5, 69-71, 90; slack_channel.py:23, 34; requests.py:68, 76-78; app.py:187, 195; config.py:95, 97, 98; gate.py:89, 100, 102, 254, 404, 595, 597; defaults.py:130; kubernetes.py:286; tick.py:38, 304; openai_compat.py:8, 35, 47, 74, 75; table.py:71, 502-511, 529-535; producers.py:1-9, 29, 60; kinds.py:5-7, 39-47; runmap.py:215; hmac_v0.py:4; chain.py:1-22.
- **Guard citations:** 215-222, 240, 389-395, 406-426, 429-430, 486-488, 493-501, 510-513, 516-518, 519-536, 552-562, 592-622, 633 and 655-657 are as cited.
- **Test and doc citations:** `test_http_metadata.py:114-118` and `:165`, `contracts/conftest.py:68-70`, `llm_wire.py:89, 91`, README.md:40, slack-app.md:14 and the manifest lines 5 and 30 are as cited.
- **Renames:** the use lists are complete across src, tests, docs, demos, README and CHANGELOG.
  - `_SLACK`: gate.py:102 and 254 only.
  - `K8S_LOG_SLACK_BYTES`: defaults.py:130 and kubernetes.py:286.
  - `_OPENAI_ALIAS`: openai_compat.py:35 and 47.
  - `TICK_SLACK_S`: tick.py:38, 304 and README.md:40.
  - `handle_slack_action`: receiver.py:1, 22, 54 and test_p7_tick.py:18, 259, 263, 265, 273.
  - `PATH` from receiver: no importer anywhere. The only importer of `approvals.receiver` is `tests/test_p7_tick.py`.
- **test_p7_tick.py:** exactly six lines change (18, 259, 263, 265, 273, 290). Line 45 builds `FakeChannel(SIG)`; 294 and 295-298 are unaffected; 537 is unchanged. `serve()` is called only at line 284.
- **PATTERNS:** the new regex compiles. The two entries together equal the dry-run candidate. Against the 8 constants: `aws` (twice), `s3` and `slack` hit the bare entry only and are covered by `LITERAL_OK`; `/slack/actions`, the producers path (twice) and `openai_compat` hit the new entry only. Test 8's single line on main is therefore right.
- **Existing plant tests:** none gains an extra line, including the `len(...) == 4` test and the `[0]`-indexed ones.
- **Other users of PATTERNS:** migrations get no hit (the only vendor word is in a `--` comment). `test_http_metadata.py:154` already applies a stricter word check to the strings of `guard/http.py`.
- **Tests 1-7:** each can fail on main on its assertion. A bad signature returns before the store is touched, and with an empty secret `hmac_v0.verify` returns False with no network call.
- **Slack regression guards:** they pass on main.
- **Test 9:** the five lines are consistent with the dry run. My grep of neutral modules found no further parameter, local or attribute name with a vendor word in snake case, and `llm.openai_compat` is the only neutral module whose name holds one.
- **`CALLBACK_PATH`:** it refuses all 11 hostile values and accepts the three real paths.
- **Sources adapter:** the entry fits `ExceptionEntry(status, reason, trigger, decided, review_by)` and the `coverage_problems` signature. `KubernetesSettings.__module__` is `sources.kubernetes`, which has the docstring line. Both exact messages in section 3 match guard:414-416 and 421.
- **Trigger rule:** `store` and `channel` keep passing; only `audit` ("none") is refused, as intended. Every existing plant uses "r" and "t", which are not in `NO_ANSWER`; the empty-reason plant still gets the same message.

## Verdict

NOT READY (four majors, all fixable with the text above).

## Not checked

- **Nothing was executed.** No test, regex, probe or the author's prototype in `/home/user/build/q8a2-author/` was run.
- **Main's own non-src files.** Its CHANGELOG.md, README.md, tests other than the guard, and docs were read in the db0d9eb tree, on the ticket's statement that they are identical.
- **Wider identifier scan.** The "0 extra hits" claim was only spot-checked by grep on snake-case names. Camel-case locals and lambda parameters were not enumerated.
- **Citations not opened:** gate.py:648 and 670, table.py:135 and store/postgres.py:120.
- **Mutant lists:** the claim that the three mutant files do not name the guard or the receiver.
- **Out of my remit:** `handover/TICKET-TEMPLATE.md` rung numbers, the Q8 audit findings F6, F8 and F11, the Q8a-1 branch, and whether the proposed audit trigger sentence is right (owner decision).
