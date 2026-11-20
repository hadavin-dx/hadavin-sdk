# G2 evidence: P1d-a on main (ticket G, part G2)

Builder: core-c (TEXT), 2026-11-20. Worktree `/tmp/core-c-g2`, branch `wip-g2-p1d-a`, base `refs/inputs/main` = 51c9fc4. Nothing pushed.

## Commits
- `4bd78f68ff284cff38de1a266df56ed93c2f9356` code G: G2 path tests: redact then defang on every approval text path, stored request, SECRET pattern timing
- `53349848cc4e19bb523bd0fa3b2d7766b7a2bfc1` code G: G2 P1d-a defang after the redactor, SECRET pattern fixes (INFO-K41)

Commit 1 is `git cherry-pick -x 6875f27` (clean, no conflict, CHANGELOG included), message amended: first line "code G: G2 P1d-a ...", the original subject and the `(cherry picked from commit 6875f27...)` line are in the body. Commit 2 adds ONE file, `tests/test_p1d_a_paths.py` (27 tests).

## Verdict in short
- FAILING: 2 property tests of the cherry-picked `tests/test_p1d_a_rows.py` (`test_no_link_outside_code_on_card`, `test_stored_card_round_trip`). INHERITED: the same two fail on the input head 6875f27 itself (exported with `git archive` to a scratch folder, run with the same venv: "2 failed, 3 passed, 91 deselected"). The head's own commit message says "Property failures are listed in the build notes" (build notes not found, not read). `git diff 6875f27 HEAD~1 -- src/hadavin_sdk/guard src/hadavin_sdk/approvals tests/fixtures/p1d_cases.py tests/test_p1d_a_rows.py` is empty, so the merge onto main did not cause them.
- BLOCKED: the mutant script. Its baseline runs the whole `tests/test_p1d_a_rows.py`, which holds the two failing properties, so the runner stops with "the unmutated copy does not pass its tests" after 9 s. 0 of 50 mutants judged.
- Everything else green: ruff check, ruff format --check, bandit, 7,866 other tests of the batch, all 27 new path tests.

## What the two failures show (both are fuzz texts, seeded, deterministic)
1. `test_no_link_outside_code_on_card` (tests/test_p1d_a_rows.py:127). First error line: `AssertionError: LINK: '3anna.m@example.orgmrn_．g_h。udb01.corp.example.com43 evil.com...` ... `'w-?v例z6ydb01[.]corp[.]example.com' matches (?<![\w.\[/-])((?:[\w-]+\.)+)(...)`. Plain words: in a glued fuzz text the final card holds `db01[.]corp[.]example.com`: the last dot of a host is NOT defanged, so `example.com` stays linkable in a renderer that makes links. This is a defang completeness gap, not an order gap.
2. `test_stored_card_round_trip` (tests/test_p1d_a_rows.py:148). First error line: `AssertionError: ROUND TRIP: 'www.evil.digitalgfso.<evil.com<EMAIL_1>=...`. Diff: stored card `&<EMAIL_2>.m@example.orgsq?...`, Slack re-render `&<EMAIL_2><EMAIL_4>?...`. Plain words: for two addresses glued together the first `clean()` leaves the residue `.m@example.orgsq` of the second address on the stored card; the second pass in `SlackChannel._blocks` then masks it. So (a) `clean` is not a fixed point under the Slack re-render, and (b) the FIRST pass shows part of an address (local-part tail and full domain) on any path that cleans once (cards, notify, FakeChannel).
Neither was fixed here (not in the task; no test weakened, skipped or xfailed).

## G2-I1 path table: every function in src/hadavin_sdk/approvals/ that produces text for a card or a channel
| # | function (file:line) | how its text reaches `runmap.redact_text` | where `defang_text` runs | test |
|---|---|---|---|---|
| 1 | `channel.clean` (channel.py:18) | calls `redact_text(text, mapping, neutralise=_neutralise)` (29) and, when a tag removal joins text, a second `redact_text(joined, ...)` (36) | `return defang_text(alt)` (38) / `return defang_text(out)` (39): last statement on both exits | test_path_channel_clean; rows `*_card` |
| 2 | `channel._neutralise` (channel.py:47) | it IS the hook the redactor calls on the text and on each decoded view: `withhold_commands(sanitise_text(text, defang=False))` | never (defang=False): writes no `[.]` | test_path_neutralise_hook_does_not_defang |
| 3 | `requests.summary` (requests.py:34), both branches (39 and the RedactionError fallback 47) | through `clean()` (row 1) | inside `clean`, last | test_path_requests_summary (normal branch only) |
| 4 | `cards._card` (cards.py:58), used by `render_shadow` (67) and `render_abstain` (99) | `text = clean(text)` (59), the one text of the card; `blocks` and `display_hash` are built from that cleaned text | inside `clean`, last | test_path_cards_render_shadow, test_path_cards_render_abstain |
| 5 | `cards.would_be_text` (cards.py:52) | fixed strings or `rule_id`; only used inside `render_shadow` lines, so through `_card` -> `clean` | inside `clean` | covered by row 4 |
| 6 | `FakeChannel.send` (channel.py:103) | `clean(req.summary)` | inside `clean`, last | test_path_fake_channel_send |
| 7 | `FakeChannel.notify` (channel.py:110) | `clean(text)` | inside `clean`, last | test_path_fake_channel_notify |
| 8 | `FakeChannel.post_card` (channel.py:113) | stores the `Card` as given; a Card from `cards._card` is already cleaned (row 4). No redaction of its own | none of its own | not tested (no text made) |
| 9 | `SlackChannel._blocks` (slack_channel.py:68), used by `send` (129) and `update` (181) | `withhold_commands(undefang_text(req.summary))` (75), then `redact_text(withheld, seeded, neutralise=_neutralise)` (82) | `defang_text(...)` wraps that redact call (82): last | test_path_slack_blocks, test_path_slack_blocks_of_a_summary_built_by_summary; rows `*_slack` |
| 10 | `SlackChannel._blocks` context lines | `req.status`, step numbers, `_who(approver_id)`: NOT redacted, NOT defanged (ids and an enum, not free text) | none | not tested |
| 11 | `SlackChannel.notify` (slack_channel.py:195) | `clean(text)`; the prefix `_who(principal_id)` is NOT cleaned (a mention on purpose, or the principal id as written) | inside `clean`, last | test_path_slack_notify |
| 12 | `SlackChannel._card_blocks` / `post_card` (slack_channel.py:142, 165) | no redaction of its own: sends `card.blocks` text unchanged as plain_text; safe only for a Card built by `cards._card` (row 4). Callers: `app.py:233`, `runtime/agent_loop.py:610` (NOT READ whether every Card there comes from `cards.render_*`) | none of its own | test_path_slack_post_card_sends_the_card_text_unchanged |
| 13 | `SlackChannel.send` / `update` fallback `text` | fixed: "Approval needed", `f"Approval {req.status.lower()}"` | none | not tested |
| 14 | `slack.py`, `receiver.py`, `hmac_v0.py` | produce no card or channel text (verification, parsing, HTTP status; log lines hold a fixed text and a reason code) | - | - |

Result: on every path that makes free text (rows 1, 3, 4, 6, 7, 9, 11) the redactor runs before `defang_text`, and `defang_text` is the last step. No path defangs first. `sanitise_text` keeps `defang=True` as its default, but the only caller in src is `_neutralise` with `defang=False` (grep over src).

## G2-I2 stored request
- `SlackChannel._blocks` handles it: `undefang_text` first, then redact, then defang. Test: `test_stored_request_from_before_the_change_is_masked_on_the_slack_card` (old-format text `anna.m@example[.]org`, `db-7[.]corp[.]internal` comes out as `<EMAIL_1>`, `<HOSTNAME_1>` and equals `channel.clean` of the original). `test_undefang_text_leaves_code_and_placeholder_dots`.
- FINDING (not fixed, channel.py is not TEXT's file): `FakeChannel.send` does `clean(req.summary)` WITHOUT `undefang_text`. Fed an old stored summary it returns `mail anna.m@example[.]org host db-7[.]corp[.]internal` unchanged: unmasked (measured). The redactor does not recognise a `[.]` address. It is the test fake, not a production channel, but any other caller that passes old defanged text to `clean()` has the same gap. No test was added for it (it would fail).

## G2-I3 SECRET pattern
- Unbounded key prefix `(?<![\w.\-?&])(?<!&amp;)[\w.\-]*`: the lookbehind lets a match start only at the first character of a name run, so the prefix is tried once per run and backtracks linearly. Timing on 11 hostile 50,000-character texts (name run, dotted run, key-word run, `&a` value, `&amp;a` value, query pairs, comma value ...): each of the two changed patterns under 0.05 s, one `redact_text` call 0.06 to 0.21 s. No catastrophic backtracking seen. Test: `test_secret_patterns_are_linear_on_a_50000_character_run` (11 cases, `pytest.mark.perf`, ceilings 2 s per pattern and 10 s per `redact_text`).
- Key behind 39, 40, 41, 60, 400 name characters is masked: `test_secret_key_behind_a_long_prefix_is_masked` (and row K41, K41q).
- `&` and `&amp;` inside a plain-form value: `test_secret_value_keeps_an_ampersand_in_the_plain_form`.
- Query form: value ends before `&name=value`, keeps `&` otherwise: `test_secret_value_in_the_query_form_ends_at_the_next_parameter`.
- "No new false must-keep failure in the existing redactor suites": the batch below ran the 56 test files that mention approvals or redact: only the two inherited P1d-a properties fail.
- Recorded nit (G-review-1): `_VALUE_END` in runmap still lists `&`; not looked at.

## Files that are not TEXT's own (numstat 51c9fc4..HEAD)
| file | + | - |
|---|---|---|
| src/hadavin_sdk/approvals/channel.py | 5 | 5 |
| src/hadavin_sdk/approvals/slack_channel.py | 4 | 3 |
| CHANGELOG.md | 2 | 1 |
| tools/p1d_corpus.py | 423 | 0 |
TEXT's own: approvals/gate.py +62 -21, guard/redact.py +25 -6, tests/test_p1d_a_rows.py +148, tests/p1d_a_mutants.py +256, tests/fixtures/p1d_cases.py +705, p1d_a_base_rows.json +94, p1d_a_gate_base.json +24, tests/test_p1d_a_paths.py (new, commit 2).

## Commands and raw output (last 30 lines each)
### 1. `uv sync --all-extras --group test`
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Resolved 103 packages in 2ms
Checked 78 packages in 0.90ms
exit=0
```
### 2. `uv run --all-extras --group test ruff check src tests tools`
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
All checks passed!
exit=0
```
### 3. `uv run --all-extras --group test ruff format --check src tests tools`
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
296 files already formatted
exit=0
```
### 4. `uv run --all-extras --group test pytest -q -p no:cacheprovider -n 2 tests/test_p1d_a_rows.py tests/test_p1d_a_paths.py $(grep -l "approvals\|redact" tests/*.py)` (56 files matched; 1 try)
```
E                   AssertionError: LINK: '3anna.m@example.orgmrn_．g_h。udb01.corp.example.com43 evil.comksét\nwk=:_aqt｡/\nw-?v例z6ydb01.corp.example.com_?password=#[ke5ni_2&vx```.?password=u例k<EMAIL_1>lgpg7épassword=~~~2u1épr87>。xpl~~~｡ &．```lk4xKp2Vb9Lr3NcW8dYh6uJss8beb?\nh3/3iq4xKp2Vb9Lr3NcW8dYh6uJswj```jrs v:]ez.*kanna.m@example.org例www.evil.digital4xKp2Vb9Lr3NcW8dYh6uJs~~~m```~~~。例pb｡' -> '3anna.m@example.orgmrn_.g_h.<HOSTNAME_1>[.]example.com43 evil.comksét\nwk=:_aqt./\nw-?v例z6ydb01[.]corp[.]example.com_?password=<SECRET_2>&vx`\u200b`\u200b`.?password=<SECRET_
E                   assert not <re.Match object; span=(22, 33), match='example.com'>
E                    +  where <re.Match object; span=(22, 33), match='example.com'> = <built-in method search of re.Pattern object at 0xce6abe0>('w-?v例z6ydb01[.]corp[.]example.com')
E                    +    where <built-in method search of re.Pattern object at 0xce6abe0> = re.compile('(?<![\\w.\\[/-])((?:[\\w-]+\\.)+)([a-z]{2,24}|xn--[a-z0-9-]+|[^\\x00-\\x7f\\W\\d_]{2,})(?![\\w@-])', re.IGNORECASE).search

tests/test_p1d_a_rows.py:127: AssertionError
_________________________ test_stored_card_round_trip __________________________
[gw0] linux -- Python 3.13.18 /tmp/core-c-g2/.venv/bin/python

    def test_stored_card_round_trip():
        # G-TXT-B: a typed `[.]` between name characters is read as `.` by design (row L15), so it is not drawn.
        for x in C.texts("TXT-B"):
            stored = channel.clean(x)
            if len(stored) <= 2900:
>               assert C.e_slack(stored) == stored, f"ROUND TRIP: {x!r}: {stored!r}"
E               AssertionError: ROUND TRIP: 'www.evil.digitalgfso.<evil.com<EMAIL_1>=例e<édb01.corp.example.com2?t6例8nwww.evil.digital```3&anna.m@example.organna.m@example.orgsq?g5m61a<EMAIL_1>evil.comi_/4xKp2Vb9Lr3NcW8dYh6uJs<HOSTNAME_1>例éx~~~#p_`.ix<HOSTNAME_1>@.anna.m@example.org?password=?l5pr@ev=?password=>ng.k4xKp2Vb9Lr3NcW8dYh6uJso`?password=y<EMAIL_1><EMAIL_1>#?password=h www.evil.digital`é&n?5sxl4gr3~~~<é': 'www[.]evil[.]digitalgfso.‹evil[.]com<EMAIL_1>=例e‹édb01[.]corp[.]example.com2?t6例8nwww[.]evil[.]digital`\u200b`\u200b`3&<EMAIL_2>.m@example.orgsq?g5m61a<EMAIL_1>e
E               assert 'www[.]evil[....00b~\u200b~‹é' == 'www[.]evil[....00b~\u200b~‹é'
E                 
E                 Skipping 108 identical leading characters in diff, use -v to show
E                 - &<EMAIL_2>.m@example.orgsq?g5m61a<EMAIL_1>evil.comi_/4xKp2Vb9Lr3NcW8dYh6uJs<HOSTNAME_1>例éx~​~​~#p_`.ix<HOSTNAME_1>@<EMAIL_3>?password=<SECRET_1> www[.]evil[.]digital`é&n?5sxl4gr3~​~​~‹é
E                 ?           ^^^^^^^^^^^^^^^^
E                 + &<EMAIL_2><EMAIL_4>?g5m61a<EMAIL_1>evil.comi_/4xKp2Vb9Lr3NcW8dYh6uJs<HOSTNAME_1>例éx~​~​~#p_`.ix<HOSTNAME_1>@<EMAIL_3>?password=<SECRET_1> www[.]evil[.]digital`é&n?5sxl4gr3~​~​~‹é
E                 ?           ^^^^^^^^^

tests/test_p1d_a_rows.py:148: AssertionError
=========================== short test summary info ============================
FAILED tests/test_p1d_a_rows.py::test_no_link_outside_code_on_card - Assertio...
FAILED tests/test_p1d_a_rows.py::test_stored_card_round_trip - AssertionError...
2 failed, 7866 passed, 20 skipped in 165.29s (0:02:45)
exit=1
```
### 4b. Same two tests on the input head 6875f27 (git archive into a scratch folder, PYTHONPATH to its src): `pytest -q tests/test_p1d_a_rows.py -k "no_link_outside or stored_card_round or K41"`
```
FAILED tests/test_p1d_a_rows.py::test_no_link_outside_code_on_card - Assertio...
FAILED tests/test_p1d_a_rows.py::test_stored_card_round_trip - AssertionError...
2 failed, 3 passed, 91 deselected in 1.42s
```
### 4c. `pytest -q -p no:cacheprovider tests/test_p1d_a_paths.py` alone: `27 passed in 2.31s`. Hand mutant: `_neutralise` with the old defang-first order makes `_check` fail with "the address is shown".
### 5. `uv run --all-extras --group test python tests/p1d_a_mutants.py` (1 try, BLOCKED by the baseline)
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Traceback (most recent call last):
  File "/tmp/core-c-g2/tests/p1d_a_mutants.py", line 248, in <module>
    results = run_mutants(
        ROOT,
    ...<4 lines>...
        on_result=lambda r: print(r, flush=True),
    )
  File "/tmp/core-c-g2/tools/mutation_runner.py", line 388, in run_mutants
    return _run_mutants(
        root, mutants, tests, extra_dirs, only, timeout, baseline_timeout, on_result,
        {} if first_lines is None else first_lines,
    )  # fmt: skip
  File "/tmp/core-c-g2/tools/mutation_runner.py", line 527, in _run_mutants
    raise RuntimeError("the unmutated copy does not pass its tests")
RuntimeError: the unmutated copy does not pass its tests

real	0m9.038s
user	0m8.591s
sys	0m0.349s
exit=1
```
### 6. `uv run --group scan bandit -q -r src/hadavin_sdk/guard src/hadavin_sdk/approvals -ll`
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Installed 22 packages in 17ms
exit=0
```

## NOT RUN / NOT CHECKED
- Mutants: 0 of 50 judged (baseline refuses, see above). Not worked around.
- The whole repository suite (by order). Python 3.12. CI.
- The build notes that list the property failures: not found, not read.
- `requests.summary` RedactionError fallback branch: read, not tested.
- Whether every `Card` that reaches `post_card` (app.py:233, runtime/agent_loop.py:610) is built by `cards.render_*`: not read.
- `_who()` prefixes and Slack context lines carry ids unredacted: read, not judged.
- tools/p1d_corpus.py (423 lines) and the 705-line fixture were not read line by line; "secrets built from parts" checked only for the literals at the top of p1d_cases.py (`SV_B` there is a 22-character made-up literal in one piece, not built from parts).
- The two generated fixture JSON files were not regenerated with tools/p1d_corpus.py.
- Composition with the G1 fold and with P2d-1 (this landing is on plain main, not on top of G1 as the ticket's build order says).
