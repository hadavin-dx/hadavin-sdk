<!-- full hand-back report of sub-agent a3040b43, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW round 1, design critic, branch core/q8a-2-neutral-callback-and-guard @ 02068ebe. Read-only; nothing was run.

VERDICT: NOT APPROVABLE YET. No Blocker in the code. 3 Major (one is missing evidence), 9 Minor. The receiver change is sound and does not move signature or freshness checking.

## What failed or is unproven (first)

- `/home/user/hadavin-sdk/handover/evidence/Q8a-2/02068eb/RESULTS.md` DOES NOT EXIST. That folder holds only `dryrun-2026-11-11.md` (pre-build, main only). Every "passes" for this head is unproven: fail-on-main runs, the removal probes, both scans returning `[]`, full suite, ruff, bandit, and green-per-commit.
- I had no builder report, so the errata items "paste the full hit list" (E4), "disposition in your report" (E5), "state the count" (E10) and the PR-body lines (E1, E7) cannot be confirmed.

## Major

**M1. No independent evidence for the head (process gate).**
- Scope: whole branch.
- Needed from an EVIDENCE RUNNER on 02068ebe:
  - must-fail items 1-10, 13 and 14 against main's `src/`;
  - the 5 + 5 removal probes and the 18-name pinned-set probe;
  - the HTTP path matrix and the hostile path list;
  - the widened scan's raw hit list on main;
  - the full suite with Postgres, ruff, bandit and `stage_mutants.py`;
  - each of the three commits green on its own;
  - the guard file run against the Q8a-1 head (see M-7 below).

**M2. Adding `gcs` to `_TABLE_VENDOR_NAME` switches the string scan off inside a class that main scans today. Require the stricter alternative.**
- Scope: `/home/user/build/snap/q8a2-02068eb/tests/test_lockin_guard.py:661-665` (pattern), `:758-768` (`_skipped_table_nodes`); class at `backends/table.py:185-189`.
- Scenario: someone adds `endpoint: str = "https://storage.googleapis.com"`, a default region or a 12-digit project number to `GcsRetentionLockSettings`. On main the `host`, region and `account id` patterns report it; on this head nothing does.
- Why not accept:
  - The ticket's own I4 rule says the pattern "is NOT widened (that would also stop the string scan inside the class)".
  - The class holds exactly one string that hits: `"gcs_retention_lock"` at `table.py:188`. I confirmed this by grep of main.
  - The CHANGELOG says only that the class "now belongs to them"; it does not say a scan was turned off.
- Fix:
  - Leave `_TABLE_VENDOR_NAME` as on main and keep the pinned set at 17.
  - Add `IDENTIFIER_OK[(backends.table, "GcsRetentionLockSettings")]`, the same shape as `OpenAICompatSettings`.
  - Add `LITERAL_OK[(backends.table, "gcs_retention_lock")]` with the reason "the kind's own name in its settings class".
  - Both entries are exact and stale-checked.
- The "like its S3 and Azure neighbours" argument is a reason to narrow those later, not to widen now.

**M3. The name scan does not look at the module path of an import; this false negative is not in the stated limits.**
- Scope: `_bound_names`, `tests/test_lockin_guard.py:795-799` (the `ast.Import` and `ast.ImportFrom` branches).
- Scenario: in neutral `approvals/requests.py`, write `from hadavin_sdk.approvals.slack import HEADER_PREFIX`, or `import hadavin_sdk.approvals.slack_channel as chat`, then branch on it.
  - Bound names are `HEADER_PREFIX` and `chat`, so the name scan passes.
  - Rule a allows any `hadavin_sdk.*` import (`:159`).
  - The string scan sees no string.
  - Result: a neutral module is tied to one vendor module (the F6 class) and CI is green.
- Plan-review M1 closed only the `from ... import slack` spelling.
- The docstring limit "a name that is only read" does not cover this.
- Fix: also scan every segment after the package of `ImportFrom.module` and of the full dotted `alias.name`. Simpler alternative: report any import of a `VENDOR_MODULES` member from a module outside that set, with exact allow pairs.
- Cost on main: my grep for `^\s*(from|import) hadavin_sdk\.[\w.]*(slack|aws|gcp|gcs|azure|bedrock|anthropic|gemini|s3|openai|vertex)` over all of main's src returned 0 lines, so I expect 0 new hits.
- Add two plants.

## Minor

**m1. Multi-word vendor names written with a separator are not seen, and the limits do not say so.**
- Scope: `name_parts` (`:836-845`) and the `PATTERNS` entry (`:727`).
- Scenario: `pager_duty_key = 1`, `cloud_watch_namespace`, `digital_ocean_token`, `open_ai_key`, `git_hub_token`, `"/pager-duty/hook"` all pass. Pairs are joined only inside one snake part.
- `sources/kinds.py:5` names CloudWatch and PagerDuty as the next kinds, so these are the likeliest next names.
- Fix: also join neighbouring snake parts (one line). For strings, test a copy with `[_-]` removed between letters, or state the limit and pin it.

**m2. The string-pattern limit in the guard docstring is looser than the regex.**
- Scope: `tests/test_lockin_guard.py:12-14`.
- The regex needs a boundary on BOTH sides: (start or separator) before, and (separator, `:` or end) after.
- Not seen and not stated: `"slack,teams"`, `"slack|teams"` (a regex alternation that branches on vendors), `"(aws)"`, `"aws+kms"`, `"/slack;v=1"`, `"x/slack y"`.
- Fix: state the rule exactly and pin one example, or add `, | ; ( ) +` to `_SEP` and measure.
- Non-issue I checked: `"/slack" + tail` and `f"/slack{x}"` ARE caught, because the inner constant is walked on its own.

**m3. "each limit is pinned by a test" is not true.**
- Scope: `tests/test_lockin_guard.py:10`.
- There is no plant for "only these words" (for example `datadog_key`) and none for non-Python files.
- Fix: add them or drop the claim.

**m4. The 64-character limit lives apart from the grammar, and the contract test does not apply it.**
- Scope: `receiver.py:21,30` against `channel.py:72` and `tests/contracts/test_capabilities.py:154-161`.
- Scenario: a future kind with a 70-character path passes its contract test and is refused only when `serve()` starts.
- Fix: one checker in `channel.py` (grammar plus length), used by both the receiver and the contract test.

**m5. "Read once at start" is not tested.**
- A mutant that re-reads `approvals.channel.callback_path` on every request passes all of `tests/test_q8a2_callback.py`.
- Fix: start the server, set `callback_path` on the instance to another valid path, and assert the old path still gives 401 and the new one 404.

**m6. CHANGELOG line 11 says the receiver "now answers only the path of the configured channel kind". That holds for `serve()` only.**
- `handle_action` is path-blind, as on main, and nothing makes another host call `callback_path()`.
- Fix: word it as "`serve()` answers only ...". The docstring sentence about other hosts is already there.

**m7. Sources adapter judges `neutral` by the settings module alone.**
- Scope: `tests/test_lockin_guard.py:443-444`.
- Scenario: a vendor source whose settings class is put in a module carrying a `Neutral protocol:` line (plan review m5 says `sources/kinds.py` has one), with its `build` in a vendor module, counts as neutral.
- Fix: require the same for `kind.build.__module__` and add a plant.

**m8. The new `sources` exception is "accepted", dated 2026-11-11, with no owner mark in the tree.**
- Scope: `tests/test_lockin_guard.py:420-427`.
- E1 moves the owner acknowledgement to the PR body, which I cannot see. The lead should confirm the line exists.
- Also `:391` still defines "accepted" as "permanent". That predates this branch and E1 forbids editing it; noted only.

**m9. Comment at `:667-669` says "both scans skip" the pinned names.**
- The string scan skips by the prefix pattern (and not `AsyncFunctionDef`); the name scan skips by the set. They are tied only by `test_the_table_skip_is_the_pinned_set`.
- This becomes moot if M2 is taken.

## Answers to the seven points

**(1) Receiver.**
- Line by line against main: `handle_action` body (head 42-52) is identical to main 27-37. `do_POST` keeps the order path, then Content-Length, then size, then handler. Only `PATH` became the closed-over `path` and the call was renamed.
- `Approvals.receive`, `parse_decision`, `hmac_v0.py` and `slack.py` are not in the diff. `slack_channel.py` gains one attribute line.
- Requests reaching signature checking: unchanged for the Slack kind. For the fake kind the path moves from `/slack/actions` to `/channel/actions`. Comparison is exact string equality; the grammar cannot hold `?`, `.`, `%` or upper case.
- Missing attribute, `None`, bytes or int: `ConfigError` before a socket is opened.
- Path changed after start: the old path stays (closure). Correct, but untested (m5).
- Two receivers: independent closures. One `Approvals` holds one channel, so there is no collision.
- Grammar: `fullmatch`, with length checked before the regex and no backtracking risk. It forbids `_`, `.` and upper case; a vendor-fixed path such as `/api/v1.0/x` would need a grammar edit. Acceptable.
- "No alias": main's src has no importer of `receiver`, `PATH` or `handle_slack_action` besides the module itself. The head's README and src are clean.

**(2) Guard dispositions.**
- 5 renames: each has exactly the cited uses and the regex and values are unchanged. Sound.
- `'gcloud'` (`gate.py:464`): a key of `_WORD_RUN` beside `az`, `gsutil`, `kubectl` and others; it recognises a command and creates no dependency. Accept.
- Two metadata host names (`tools.py:142,170`): a refusal list, so naming them is the control. Accept.
- `producers`, `openai_compat` and the 5 name allowances: exact pairs. Accept. Small note: the module-name entry `(llm.openai_compat, "openai_compat")` also allows a variable of that name in that module.
- My own grep of main for the 11 new words found exactly these hits plus `table.py:188`, and `table.py:367` and `:484` inside nodes already skipped. For the five new separators with the old words my grep (approximate) found 0 matches.
- 18 pinned names: see M2; I want 17.
- No allowance waves lock-in through except the widening in M2.
- False negatives beyond the stated limits: M3, m1, m2.
- `itertools.pairwise`: accept. It gives the same pairs as `zip(camel, camel[1:])` in the dry-run script. `requires-python` is `>=3.12` (read from the working tree's `pyproject.toml`, not the snapshot).

**(3) The two gate lines.**
- Mechanical. The regex text and flags are byte-identical, there is one definition and one use, and no `_SLACK` remains at head. The comment at `:100` still names whose syntax it is.
- It stays on the capped path. It still needs the gate tests shown green (M1).

**(4) Sources.**
- Honest as far as it goes. The Kubernetes docstring line is at `sources/kubernetes.py:8`. Plants cover no-line, vendor-module, two-kind and missing-entry cases.
- Gaps: m7 and m8.

**(5) Scope.**
- Nothing out of scope was built. The `audit` entry and line 391 are unchanged; there is no `NO_ANSWER` rule and no item 12.

**(6) Claims exceeding proof.** m2, m3, m6, and the CHANGELOG's silence about M2.

**(7) Sibling Q8a-1.**
- Not readable from the snapshot.
- Risk: its new code in `app.py` and `config.py` was written against the 15-word, start-of-string guard.
- Scenario: a refusal message or override list that holds `"AWS_PROFILE"`, `"GOOGLE_APPLICATION_CREDENTIALS"`, `"?kind=slack"`, or a parameter such as `aws_region`. Each branch is green alone; main goes red after the second merge.
- An edit to the exact string at `config.py:98` would also make `LITERAL_OK (config, "slack")` stale.
- Required: run this head's guard file against a merge of both before either merges.

## Errata checklist

| Item | State | Note |
|---|---|---|
| E1 | done | PR-body line not visible |
| E2 | done | name fallback, imports, `BareChannel` with `name = "bare"`, the five extra bad values, `port=0` with close, docstring sentence, both rewordings |
| E3 | done | lookup inside the test; no new module-level import in either test file |
| E4 | partly | Done: split copied (as a set, `pairwise`), trailing-digit rule, ordering and de-duplication, all listed binders with a plant each, `auth_aws` entry. Not verifiable: hit list pasted, measured count for test 9. Gap: M3 |
| E5 | partly | Done: 11 words, drift test (the other list must be a subset; its regex shape assumption is unchecked), dispositions visible in code. Not verifiable: report. Deviation: M2 |
| E6 | done | separators added, wording added; "0 new hits" unproven, though my grep agrees |
| E7 | done | `_CHAT_CONTROL`, comment kept, `defaults.py:42` now "margin"; PR text not visible |
| E8 | done | parameter, AND rule, `_E` reused, plants, set assertion |
| E9 | done | (a) over 9 separators, (b), (c); `AWSclient` limit stated and pinned |
| E10 | partly | CHANGELOG placement done. Guard file has 80 test functions at head against the errata's 56 on main; whether the builder stated this is not visible. Commit order and per-commit green unproven |

## Not checked

- Nothing was executed: no test, regex or `ast` behaviour.
- `docs/`, `demos/`, and tests other than the four in the snapshot, for leftover uses of the old names.
- `tests/test_http_metadata.py`, so the pattern-shape assumption of the drift test.
- `_SQL_LITERAL` (`:743`) still carries its own 11-word list; whether `sql_problems` also applies the widened entries was not read.
- The Q8a-1 branch, the PR body, the builder's report, and per-commit content.
- CI tools: CodeQL, SonarCloud, CodeRabbit.

Files: `/home/user/build/snap/q8a2-02068eb/DIFF.patch`, `/home/user/build/snap/q8a2-02068eb/TICKET.md`, `/home/user/build/snap/q8a2-02068eb/src/hadavin_sdk/approvals/receiver.py`, `/home/user/build/snap/q8a2-02068eb/tests/test_lockin_guard.py`, `/home/user/build/snap/q8a2-02068eb/tests/test_q8a2_callback.py`, `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/backends/table.py`, `/home/user/hadavin-sdk/handover/evidence/Q8a-2/dryrun-2026-11-11.md`.
