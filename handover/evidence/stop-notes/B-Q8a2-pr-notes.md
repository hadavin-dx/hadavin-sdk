# PR notes for Q8a-2 (branch core/q8a-2-neutral-callback-and-guard), written by the builders for the lead

State after fix batch 2. Head: see the last line of /home/user/build/B-Q8a2-checkpoint.md. Raw proof files of fix batch 2: /home/user/build/q8a2-fb2/.

## Lines the PR body must carry

- **Owner, please say yes or no.** Today the core can read from one kind of system only: Kubernetes. Our rule asks for two, or a written exception with an end date. This change writes that exception: it stays until the first client needs a second system to read from, and it is looked at again by 30 April 2027. If you say no, a second read source must be built before this merges.
  (For the lead, not for the owner: the date was checked against the code and is the same, `date(2027, 4, 30)` in the `sources` entry of `EXCEPTIONS`, tests/test_lockin_guard.py. The code already records the entry as "accepted", decided 2026-11-11, before the owner has answered; if the answer is no, the entry is removed and the guard fails until a second read source exists.)
- The `audit` exception and its "none" trigger are NOT touched (ticket errata E1; owner decision pending).
- `approvals/gate.py`: `_SLACK` was renamed `_CHAT_CONTROL` (two lines, same regular expression). The record of whose control syntax the pattern removes moved from the name to the comment directly above it, which still names Slack.

## DEVIATIONS from the frozen ticket (two; both need the lead's recorded yes)

1. **DEVIATION: the receiver compares the path as written in the first line of the request, not `self.path`.** The ticket says "`do_POST` compares `self.path != path` exactly ... Nothing else in `do_POST` changes". The code compares the second word of the request line (`self.requestline.split()[1:2]`). Reason: Python's http.server rewrites a path that starts with `//` to a single `/` before `do_POST` runs, so with `self.path` the ticket's own table ("anything else: 404") was not true for `//<path>`.
   **The real behaviour change:** on main a correctly SIGNED request to `//slack/actions` was handled exactly like one to `/slack/actions` (answer 200, the click went on to the approval code). Now it is answered 404 and the click is never looked at. Proof over a loopback socket, clean origin/main worktree against this head: /home/user/build/q8a2-fb2/signed-double-slash.txt (main: `POST //slack/actions`, correct signature, 200; head: `POST //channel/actions`, correct signature, 404). An earlier version of these notes said such a request "was still refused there with 401"; that was true only for a wrong or missing signature and was wrong as a general statement.
   Fix batch 2 changed more of `do_POST` on the lead's instruction (security path): the path is judged before the `Content-Length` header is read; see "Receiver faults" below.
2. **DEVIATION: the allow key of a module's own name.** Errata E4 says the module-name line and its allow key "use the single segment". The key is `"module:" + the dotted name up to that segment` (for example `module:llm.openai_compat`). Reason: with the bare segment as key, an allowance for a module name also allowed a variable of the same name (round 1), and two equal segments (`aws/aws.py`) shared one key (round 2, F4). The reported line still shows the single segment.

## For the later hosting decision (recorded, not changed)

The standard library splits the first line of a request on ANY white space (Python's `str.split`: also tab, vertical tab, the characters 0x1C to 0x1F, 0x85 and the no-break space 0xA0), and the receiver takes the second word. So `POST<no-break space>/channel/actions<no-break space>HTTP/1.1` reaches the signature check, on main and on this branch alike (pinned by `test_pinned_other_white_space_between_the_words_of_the_request_line_is_accepted`: tab, no-break space, vertical tab, 0x1C, two spaces; all 401 for an unsigned request). A proxy in front that routes by path may read such a line differently. The signature is still required.
A request that is answered 404, 400 or 413 is answered without its body being read; a client that has already sent a body can see a connection reset instead of the status. Unchanged from main; draining the body first would be a behaviour change and was not made.

## Receiver faults fixed in fix batch 2 (all four were already on main)

| fault (an unsigned caller could cause each) | now | test in tests/test_q8a2_callback.py |
|---|---|---|
| `Content-Length` of more than 4,300 digits: no answer, traceback on stderr | more than 12 digits: 413 without conversion; not plain ASCII digits, empty, a sign, a space, or the header twice: 400; a wrong path: 404 whatever the header | `test_a_malformed_or_oversize_content_length_is_refused_with_a_normal_answer` (15 header forms), `test_the_body_length_reader_never_raises_and_accepts_only_plain_digits` |
| a request that announces more body than it sends, or sends slowly: the thread is held as long as the caller likes | the whole request (first line, headers, body) must arrive within `read_timeout_s` (default `defaults.RECEIVER_READ_TIMEOUT_S` = 10 s); then the connection is closed WITHOUT an answer. Chosen because that is what http.server itself does for a timeout (`handle_one_request` catches `TimeoutError`, logs through `log_message`, closes); a 408 would need the receiver to write on a connection whose state is unknown | `test_a_request_that_sends_less_than_it_announces_frees_its_thread_within_the_bound`, `test_a_request_that_arrives_too_slowly_is_dropped_at_the_bound_however_it_is_sent` (first line, headers; one byte every 0.2 s) |
| the caller closes or resets before the answer is written: traceback | one debug log line with the kind of error only | `test_a_caller_that_leaves_before_the_answer_causes_no_traceback` |
| a failure while a click is handled (the tests start the receiver with no store: `AttributeError`): no answer, traceback | answer 500 (so the sender delivers again), then one error log line with the kind of error only (no request text, no error message) | `test_a_failure_while_a_signed_click_is_recorded_is_answered_500_without_a_traceback` |

Decision on "store of None": `serve()` does NOT refuse to start without a store. Reason: the fault class is "any failure while a click is handled ends without an answer", and a store that is down at run time is the same class; one fix at the place every such failure passes (answer 500, log the kind) covers both. The tests keep starting the receiver without a store where no signed click is sent.
Behaviour changes from these fixes, also stated in the CHANGELOG: an empty `Content-Length` value is 400 (before: read as 0, then 401); the header twice is 400 (before: the first one was used).

## Merge with the sibling branch core/q8a-1-live-override-refusals

- `CHANGELOG.md` conflicts (expected: both branches add bullets at the top of "Upgrade steps" and of "Changed" under "Unreleased"). How to resolve: KEEP BOTH sets of bullets, in either order; no bullet of one branch replaces a bullet of the other.
- This branch's guard, run on the sibling's source (fcd77a68, no allowances changed), reports the same six things as before, all fixed by this branch. Because names that are only read are now scanned too, the six things are 11 lines (file /home/user/build/q8a2-fb2/guard-on-q8a1-source.txt):
  ```
  hadavin_sdk.approvals.receiver:18: vendor word in a string in '/slack/actions'
  hadavin_sdk.approvals.gate:102: vendor word 'slack' in the name '_SLACK'
  hadavin_sdk.approvals.gate:254: vendor word 'slack' in the name '_SLACK'
  hadavin_sdk.approvals.receiver:22: vendor word 'slack' in the name 'handle_slack_action'
  hadavin_sdk.approvals.receiver:54: vendor word 'slack' in the name 'handle_slack_action'
  hadavin_sdk.defaults:132: vendor word 'slack' in the name 'K8S_LOG_SLACK_BYTES'
  hadavin_sdk.llm.openai_compat:35: vendor word 'openai' in the name '_OPENAI_ALIAS'
  hadavin_sdk.llm.openai_compat:47: vendor word 'openai' in the name '_OPENAI_ALIAS'
  hadavin_sdk.runtime.tick:44: vendor word 'slack' in the name 'TICK_SLACK_S'
  hadavin_sdk.runtime.tick:310: vendor word 'slack' in the name 'TICK_SLACK_S'
  hadavin_sdk.sources.kubernetes:286: vendor word 'slack' in the name 'K8S_LOG_SLACK_BYTES'
  ```
  The merged tree of both branches was NOT scanned by the fix-batch-2 builder.

## Test counts

tests/test_lockin_guard.py: 56 test functions on main; 90 after fix batch 1; 102 after fix batch 2. tests/test_q8a2_callback.py: 17 after fix batch 1; 27 after fix batch 2 (72 collected cases).

## Measured hit lists on main 2a8c2aa

Fix batch 2, file /home/user/build/q8a2-fb2/measure-main.txt (script measure.py beside it; no allowances applied; the ticket's stop rule is "more than 10 new hits: keep the limit"):

| widening | new problem lines on main | decision |
|---|---|---|
| string boundary as a rule: each side is the start or end, or a character that is not an ASCII letter, digit or white space | +8 (gate.py:89, 648, 670; guard/runmap.py:215 three times; backends/table.py:135; store/postgres.py:120) | taken |
| white space as a boundary as well | +2 (config.py:97, 98), so 10 in all | taken: 10 is not more than 10, and the rule becomes one sentence |
| one separator inside the nine two-part words | +0 | taken |
| seven chat and paging words (discord, telegram, webex, whatsapp, twilio, zoom, opsgenie) | +0 strings, +0 names | taken |
| names that are only read (every Name and Attribute that is not a binding) | 30 lines on 25 names; every one is a name that this branch had already renamed (5), pinned as a kind-table name (15) or allowed (5); 0 names that need a new decision | taken |
| original name of an aliased `from` import; keyword names of a class pattern | +0 | taken |

Disposition of the 10 new string lines: 4 exact (module, string) allowances for refusal messages (config.py twice: where a retired setting moved; table.py and store/postgres.py: the package's own install extra `[aws]`); 4 allowances of the second form (module, assignment name, word) covering the other 6 lines: (approvals.gate, `_URL`, slack), (approvals.gate, `_URL`, teams), (approvals.gate, `_WRITE_SHAPES`, s3), (guard.runmap, `_GRAMMAR`, aws). The second form was chosen for these because the full text of a regular expression of up to 1,184 characters is a brittle key; it covers only "vendor word in a string" lines of the strings inside that one assignment, and a string only when each of its vendor words is listed. Note for the lead: guard/runmap.py:215 is the ARN-shaped pattern that the ticket ("Read first", item 6) left to the lead; it now has an exact allowance with the reason "recognising it is the control".
Totals now: 14 (module, string) allowances, 4 (module, assignment, word) allowances, 6 (module, name) allowances, 17 pinned kind-table names. Final scan of main's source with this head's guard and no allowances: 23 string lines, 23 name lines (file final-guard-on-main-no-allowances.txt); of this head's source: 22 and 13; with the allowances: 0 and 0.

Earlier batches (raw files in /home/user/build/q8a2-build/): the dry run's 25 names (28 lines) plus the module name `llm.openai_compat`; wider list of name kinds (errata E4) +1 `store/postgres.py:115 auth_aws`; 11 more words (errata E5) +1 name `GcsRetentionLockSettings`, +4 strings (`gate.py:464 'gcloud'`, `table.py:188 'gcs_retention_lock'`, `tools.py:142` and `:170` the metadata host name); separators `= ? & # @ , ; ( ) +` +0. Disposition: 5 renamed, 17 pinned, 6 name allowances, 10 string allowances.

## Every scan that sees less or more than on main (one sentence each)

- String scan (`literal_problems`): sees MORE (a vendor word between any two boundaries; 33 words instead of 15; two-part names with one separator). Sees LESS in one way only: a string whose words are all listed in a (module, assignment, word) allowance is not reported under the label "vendor word in a string" (4 entries); every other label is still reported there.
- The kind-table skip (`_skipped_table_nodes`): sees MORE: the skipped assignment must be named exactly `TABLE` (main skipped any top-level assignment whose first 12 characters contained "TABLE"); classes and plain functions are chosen by the same prefix pattern as on main; an `async def` is not skipped (as on main).
- Name scan (`identifier_problems`): new; main had none.
- SQL migrations scan (`sql_problems`): sees MORE (it applies the new word entry to the SQL text outside the quoted words its own older rule reports); 0 hits.
- tests/test_http_metadata.py reuses PATTERNS for the strings of guard/http.py: sees MORE; 0 hits.
- Rule "two kinds or a dated exception" (`coverage_problems`): sees MORE (the read-source registry); the function itself is unchanged.
- Import rule (rule a): unchanged.
- Whole-text check: new, for approvals/receiver.py only; it now uses the same boundary rule and word list as the string scan.

## Independent evidence

Lead's EVIDENCE RUNNER on head 5f94f598 (before fix batch 2): /home/user/hadavin-sdk/handover/evidence/Q8a-2/5f94f59/RESULTS.md. Fix batch 2 answers its items 4 (server tracebacks) and 5 (plants with an empty result). No independent evidence exists yet for the fix-batch-2 head.

## Fix batch 3 (head 3210f93a)
- The vendor word list is open-ended: a vendor that is not on it (datadog, jira, okta, splunk, snowflake, servicenow, mattermost, sendgrid ...) passes every scan until its word is added. Stated in the CHANGELOG.
- The evidence found 4 guard plants that no scan reports: a comment `# slack`, a docstring naming Slack, and the SQL comments `-- slack` and `/* slack */`. Decision: comments, docstrings and SQL comments are NOT scanned (a vendor word there is prose and cannot change behaviour). Stated in the guard docstring and the CHANGELOG, pinned by tests (test_a_comment_and_a_docstring_are_not_scanned, test_a_vendor_name_in_a_sql_comment_is_not_flagged). approvals/receiver.py stays checked as whole text.
- handle_error: a hang-up alone is DEBUG; a hang-up after a failed handler stays ERROR (names both kinds); tests with caplog.
