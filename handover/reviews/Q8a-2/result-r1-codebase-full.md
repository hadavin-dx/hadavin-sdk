<!-- full hand-back report of sub-agent ae979d0b, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW round 1, Q8a-2, head 02068ebe (snapshot /home/user/build/snap/q8a2-02068eb/). Mode: REVIEW.

Outcome: no Blocker and no Major found. 11 Minor findings and 4 nits. Everything below is from reading and grep only; nothing was executed.

Evidence: /home/user/hadavin-sdk/handover/evidence/Q8a-2/02068eb/RESULTS.md is NOT present. The only file in that directory is dryrun-2026-11-11.md (pre-build, not read). So there is no run evidence for this head: no fail-on-main runs, no suite, ruff or bandit result.

## Failures of things you asked me to confirm

**F1. Minor. Two suppressions were added.**
- /home/user/build/snap/q8a2-02068eb/tests/test_q8a2_callback.py:183 and :193: `rng = random.Random(8802)  # noqa: S311 - test data, not a secret` (and 8803).
- I cannot confirm "no noqa added". No `nosec`, `type: ignore` or `pragma: no cover` was added.
- The repo has 8 existing uses of the same suppression (e.g. tests/test_runmap_partial_escape.py:44, tests/test_k5_round12_fuzz.py:138).
- Fix: accept by precedent and say so in the PR, or add `"tests/**" = ["S101", "S311"]` to per-file-ignores (pyproject.toml:79), or replace the random draw with a fixed enumeration.

**F2. Minor. Errata items that cannot be found in the diff or snapshot.**
- E4: the pasted full hit list of the widened scan on main, and the measured count for must-fail test 9.
- E5: the per-hit dispositions in the builder's report. Only their results are visible: three new LITERAL_OK entries (`gcloud`, `metadata.google.internal`, `.metadata.google.internal`) and `GcsRetentionLockSettings` in the pinned set.
- E6: the "0 new hits on main" confirmation.
- E7: the PR sentence that the record of `_SLACK` moved to the comment.
- E1: the PR-body line "OWNER-ACK needed: sources exception".
- E10: the stated test count after the ticket, and the three-commit green order (the snapshot is one squashed diff).
- My own count by reading: 56 test functions on main, 80 at head (24 new), about 122 collected items with the four parametrised tests.
- Everything else in E1 to E10 is present in the code (see "Checked and found correct").

## Findings

**1. Minor. tests/test_lockin_guard.py:890-893 (`_bound_names`): a vendor module reached through the import path is not seen, and the docstring limits (lines 12-19) do not say so.**
- Repro: in a neutral module write `from hadavin_sdk.approvals.slack import HEADER_PREFIX`, or `import hadavin_sdk.approvals.slack` followed by `hadavin_sdk.approvals.slack.X`.
- The bound names are `HEADER_PREFIX` and `hadavin_sdk`, so `identifier_problems` returns `[]`. Rule a also passes, because it is not a vendor SDK.
- This is the sibling of design M1's scenario. The code matches E4's wording exactly, so it is a limit, not a deviation.
- Fix: also scan each segment of `ImportFrom.module` and `alias.name` after the package name. My grep of main's neutral modules finds only store/postgres.py:115, already allowed, so the cost today is zero. Otherwise add the limit to the docstring with a pinning test.

**2. Minor. tests/test_lockin_guard.py:664-666: the `gcs` prefix change also narrows the existing string scan.**
- `_skipped_table_nodes` now skips everything inside `GcsRetentionLockSettings` (backends/table.py:185-189: `Literal["gcs_retention_lock"]` and the bucket regex), which main scanned.
- This is the only existing check that sees less than on main. It is needed, because the new pattern would hit `gcs_retention_lock`, and it follows E5 and the S3 and Azure neighbours.
- It contradicts the ticket's out-of-scope line "the prefix-based skip of the STRING scan is unchanged". The CHANGELOG discloses it only indirectly ("now belongs to them").
- Fix: one explicit sentence in the PR or CHANGELOG. Nothing in code.

**3. Minor. tests/test_q8a2_callback.py:49-56 and 219-224: every 404 probe sends a 9-byte body the server never reads.**
- receiver.py:64-65 answers 404 before `rfile.read`, then closes. A close with unread bytes can send a reset to the client.
- On Linux loopback the response normally survives. I did not observe a failure; this is a possible flake.
- Main's own 404 probe (tests/test_p7_tick.py:295) sends `data=b""`.
- Fix: post no body on probes that expect 404, or catch nothing and keep as is with a note.

**4. Minor. tests/test_q8a2_callback.py:223: the near-miss list lacks three shapes.**
- Present: trailing slash, query string, upper case, longer path, shorter path.
- Missing: percent-encoding (`/channel/%61ctions`), a double slash (`//channel/actions`, `/channel//actions`) and the absolute form (`POST http://127.0.0.1:port/channel/actions`).
- By reading receiver.py:64 (`self.path != path`, raw request target) all of them give 404.
- A later "normalise the path" change would pass the current list.
- Fix: add the three strings. `http.client` sends them unchanged.

**5. Minor. tests/test_lockin_guard.py:1318-1345: the removal test for string allowances has no completeness check.**
- `_NEW_LITERAL_OK` is a hand list of 5 keys.
- The name side has `test_every_name_allowance_is_checked_by_the_removal_test`; the string side has no equivalent.
- A future LITERAL_OK entry is therefore not forced through the "covers exactly its own hits" proof. The 4 older entries are not in it either.
- Fix: assert `set(_NEW_LITERAL_OK) | OLD_KEYS == set(LITERAL_OK)`, or extend the table to all 9.

**6. Minor. tests/test_lockin_guard.py:926-928: one IDENTIFIER_OK key covers two different things.**
- The key `(module, name)` is shared by the module-name line and by every binding of that name in the module, whatever the binder.
- Example: `(llm.openai_compat, "openai_compat")` also allows a variable `openai_compat = ...` in that file. `(store.postgres, "auth_aws")` also allows `def auth_aws()` there, though its reason says "lazy import".
- Stale detection cannot tell the two apart.
- Fix: accept and state it in the comment at lines 635-636, or key module names as `(module, "<module>")`.

**7. Minor. tests/test_lockin_guard.py:811-822: one f-string or `+` join gives two problem lines for the new pattern.**
- This is existing behaviour that the new entry inherits.
- Repro: `X = f"/slack/{y}"` reports `'/slack/{}'` (the JoinedStr) and `'/slack/'` (its inner Constant). An allowance would need two entries.
- "One planted string gives one line" holds only for plain constants, which is all the new tests plant.
- Fix: none required. Add one plant that pins the count, or skip Constants that are children of a folded node.

**8. Minor. tests/test_lockin_guard.py:836-845: snake-separated two-part words are not seen, and the limit is unstated.**
- Neighbours are joined only inside one snake part (`GitHub`, `OpenAI`).
- `git_hub_token`, `open_ai_key`, `pager_duty_id`, `cloud_watch_ns` and `digital_ocean` do not hit.
- The reverse also holds: a camel pair that happens to spell a word hits (`TeamS` gives teams, `maxGCs` gives gcs).
- Fix: one docstring line and a pinning plant.

**9. Minor. receiver.py:31-33: `name` goes into the ConfigError text unchecked.**
- An empty string gives "channel : callback_path ...". A name with a newline gives a two-line message.
- Fix: use the class name when `name` is empty or not printable, or format with `{name!r}`.

**10. Minor. tests/test_lockin_guard.py:35: the source registry is imported at module level.**
- `from hadavin_sdk.sources.kinds import KINDS as SOURCE_KINDS` is forced by E8's default argument.
- A future source kind whose module needs an optional extra would break collection of the whole guard file on a default install.
- `_source_docstring` (lines 232-239) exists to avoid exactly that.
- Fix: `kinds=None` and import inside `source_table`.

**11. Minor. tests/test_lockin_guard.py:482, 491, 506: three tests read the live module-level `KINDS` dict.**
- Today no test leaves it changed. tests/test_k5_round6_contracts.py:35-42 asserts `KINDS == before` and re-registers the same object.
- A later test that registers a kind without cleanup makes these three order-dependent.
- Only line 482 carries the explaining comment, and its bare `assert` has no message.
- Fix: add a message to the assert.

**Nits**
- approvals/channel.py:78-80: the formatter split the annotation into `callback_path: (\n str  # ...\n)`. Move the comment above the line.
- tests/test_lockin_guard.py:636: the comment says the key is "(module, its last segment)", but the code at 922 uses every segment after the package. A package folder `aws/` needs `(module, "aws")`.
- tests/test_lockin_guard.py:692: "the one word list" overstates it. `_SQL_LITERAL` (743), "vendor header" (728) and `_TABLE_VENDOR_NAME` (664) keep their own lists.
- tests/test_lockin_guard.py:758-768 against 960-966: `_skipped_table_nodes` ignores `AsyncFunctionDef`, while the pinned-set test and the name scan include it. No such name exists today.

## Checked and found correct

**approvals/receiver.py**
- `callback_path()` (25-34): `getattr(..., None)` never supplies a path. It checks str, then length against `MAX_PATH_CHARS = 64`, then `CALLBACK_PATH.fullmatch`.
  - bytes, int and None are refused.
  - `"/a\n"` is refused because the check is `fullmatch`.
  - The `name` fallback to the class name is as E2 asks.
- Validation runs once, at the top of `serve()` before the Handler class exists. `handle_action` does not check the path; the E2 docstring sentence is at line 6.
- Handler: exact raw comparison, so query string, trailing slash, other case, percent-encoding and double slash all give 404.
- Lines 62-75 match main line for line apart from the two renames. The 404, 400, 413 order, `MAX_BODY` and the 401, 413, 200 results of `handle_action` are unchanged.
- No vendor word in code, constants, comments or docstrings.
- E2's rewording targets are met.

**approvals/channel.py, approvals/slack_channel.py**
- `DEFAULT_CALLBACK_PATH`, `CALLBACK_PATH` (unanchored pattern, used with fullmatch only, ASCII ranges, no flags), the Protocol member and `FakeChannel.callback_path` are as specified.
- `SlackChannel.callback_path = "/slack/actions"` is the one added line.
- `Channel` is not `runtime_checkable` and no `isinstance` against it exists.
- The only classes with `parse_decision` are `FakeChannel` and `SlackChannel`.
- The only `serve()` caller is tests/test_p7_tick.py:284.

**The five renames**
- No leftover in the head files. On main the uses are exactly the lines the diff changes:
  - gate.py:102, 254
  - defaults.py:130 and kubernetes.py:286
  - openai_compat.py:35, 47
  - tick.py:38, 304 and README.md:40
  - receiver.py and test_p7_tick.py:18, 259, 263, 265, 273
- Remaining mentions are CHANGELOG history, the no-alias assertion and the meta-test plant.
- docs/slack-app.md:14 and the manifest lines 5 and 30 stay true.
- The gate.py diff is two lines, and the comment at line 100 is kept.
- defaults.py:42 says "margin".

**PATTERNS**
- The new entry expands to `[/_.=?&#@-](W)([:/_.=?&#@-]|$)|^(W)[/_.=?&#@-]`. The hyphen is last in both classes, so it is literal.
- Against the ticket's hits:
  - `/slack/actions`, `guard/bedrock_guardrail.py` (twice) and `openai_compat` match the new entry only.
  - `aws`, `s3`, `slack` and `slack:{}` match the bare entry only.
- A string with one vendor word cannot match both entries.
- Main's neutral strings, grepped with the widened list, give only the allowed set:
  - producers.py:29 and :60
  - openai_compat.py:75
  - gate.py:464 `gcloud`
  - tools.py:142 and :170
  - the skipped table parts
- The migrations give 0 hits.

**Existing guard tests**
- None weakened; no expected count changed.
- `[0]`-indexed and `len(...) == 4` plants are unaffected.
- The coverage test is stronger: it now uses `coverage_table()` and asserts the kind set.
- The `audit` entry, the comment at line 391 and the reason-and-trigger condition (line 473) are untouched. No NO_ANSWER rule exists (E1).

**Identifier scan**
- `_CAMEL` and `name_parts` behave as specified:
  - `S3ObjectLockSettings` gives s3.
  - `OpenAICompatSettings` gives openai through the Open+AI pair.
  - `GitHubClient` gives github.
  - `AWSclient` gives nothing; that limit is stated and pinned.
- Digit rule: `slack2_url` and `aws1` hit, `s3` is kept whole, `xs3y` does not hit.
- Every E4 binder is scanned and each has a plant. I traced all 29 parametrised cases to exactly one line each:
  - all alias forms
  - ExceptHandler
  - MatchAs, MatchStar, MatchMapping.rest
  - TypeVar, TypeVarTuple, ParamSpec, and a type alias
  - call keywords
- `ast.TypeVar` and its siblings need Python 3.12; `requires-python` is `>=3.12`.
- Order and de-duplication: modules sorted, module-name lines first at line 1, then sorted (line, name, word), set-based. The order test's seven expected lines are right.
- Allow lists: 5 IDENTIFIER_OK entries (the ticket's 4 plus `auth_aws`), all exact, stale-checked, with removal tests. My grep of main found no further bound name or keyword with a vendor word.
- Pinned set: 18 names, equal to what the widened prefix matches in table.py. Removing any one name reports it.

**Sources**
- `source_table(kinds=...)` and `coverage_table(kinds)` reuse `_E`, moved above.
- `neutral` is the docstring line AND not in `VENDOR_MODULES`.
- The EXCEPTIONS entry matches the ticket's text and dates exactly.
- Plants for no-line, vendor-module and two-kind cases are present.

**Word-list drift test**
- Its regex extracts the 22 words of tests/test_http_metadata.py:114-116; all are in the 26.
- `tests/__init__.py` exists and `pythonpath = ["."]`, so the import resolves to the collected module.

**Can each new test fail?**
- Yes for all. None is a tautology.
- Property tests (a) and (b) are exhaustive over 26 words (9 separators by 3 positions; 5 name forms), not random.
- Property test (c) uses `random.Random(8802)` and `random.Random(8803)`, fixed seeds.
  - It asserts accept-and-return for generated valid paths.
  - It asserts 64 accepted and 65 refused.
  - It asserts refusal for one foreign character, an empty segment, a missing leading slash and a trailing joiner.
  - The generator always yields valid paths of the exact length, and the bad cases stay under 64 characters, so they are refused for grammar, not length.
- test_q8a2_callback.py loads on main: no module-level import of new names, and each must-fail test fails on its own assertion.

**Sockets**
- Every `serve()` call uses `port=0` on 127.0.0.1.
- `_served` does `shutdown()`, `server_close()` and `join(5)` in `finally`.
- `_assert_serve_refuses` closes a server that was returned.
- Client timeout is 5 s.

**Meta test**
- `shutil.copytree(SRC / PKG, tmp_path / PKG)`, clean-copy assertions first, the plant written only under `tmp_path`.
- Expected line numbers (`lines + 1`, `lines + 4`) are right.
- A final assertion checks the real receiver is unchanged.

**tests/contracts/test_capabilities.py**
- Exactly as E3 asks; no new module-level import.

**CHANGELOG, sentence by sentence**
- Accurate: 15 to 26 words and the 11 names; 18 pinned names; the paths and messages; "values unchanged"; the grammar sentence; the sources exception with its review date.
- Placement is first in `### Upgrade steps` (line 5) and first in `### Changed` (line 261), both under `## Unreleased`.
- No NO_ANSWER sentence, which is correct under E1.
- Two soft spots:
  - "A custom channel class must set `callback_path`" is enforced only by `serve()`.
  - The Gcs string-skip change is only implied (finding 2).

## Not checked
- Nothing was run: no test, ruff, format or bandit. Every pass or fail statement is by reading.
- /home/user/build/q8a2-dryrun/dryrun.py was not read (outside the allowed paths), so E4's "copy `parts()` verbatim" is unverified. I checked behaviour against the ticket's prose only.
- The full-source scans (`literal_problems`, `identifier_problems` returning `[]` at head) were approximated with ripgrep patterns over main's src, not an AST walk. Camel-case locals and multi-line constructs could escape my grep.
- Not opened: tests/test_g4_parity.py, the G3 tests, tests/contracts/kinds/*, demos, tests/mutation_runner_mutants.py, and the body of gate.py beyond the diff.
- Whether tests/test_http_metadata.py:161-167 still gives 0 hits on guard/http.py with the wider list. I inferred this from its stricter check at line 154 and did not read http.py's strings.
- The Q8a-1 branch interaction, CI, CodeQL and SonarCloud results, commit order, and the PR body.
- Unchanged head files outside the snapshot were assumed equal to main.
