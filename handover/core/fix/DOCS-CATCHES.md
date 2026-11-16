# CATCHES: what the docs test found in the FROZEN docs (doc claim vs tool output)

Honest count: **2 real mismatches** (a sentence of the frozen docs that the tool contradicts), plus 4 gaps (true or unchecked text that the test now pins or that lacked a fact). Everything else the test checks already held on the frozen docs.

## Real mismatches (fixed in the docs)
1. `docs/hubspot-probe.md:45-46`, frozen text: "`--token-env NAME` ... must be a plain variable name, anything else is refused without being printed". The tool (`scripts/hubspot_probe.py:300-305`) does not refuse a bad name with `--plan` (exit 0, only prints the call count) and refuses for the count before it looks at the name when `--yes-spend-calls` is not 7. Only `--yes-spend-calls 7` plus a bad name gives the refusal. Test: `test_the_probe_checks_the_token_variable_name_only_when_calls_are_confirmed` (runs `hubspot_probe.main` three times, no call is made). Fixed by the F4 wording (`--plan` clause, count-first clause).
2. `contract.md:323`, frozen text: a repeat of a `new` request drives the follow-up "only if it is due: no automatic try yet, or its backoff is over". For a follow-up given back for lack of resources (`no_descriptors`, model busy) the code waits 5 seconds even with no try used (`gate.wait_before_drive(0, ...) == 5`, `desk._pending_and_due` checks that first), so "no automatic try yet" alone is wrong for those rows. Test: `test_the_pages_about_a_repeated_request_say_it_can_start_a_follow_up_that_is_due` (calls the real function). Fixed: one clause added.

## Gaps (not false; now stated and pinned)
3. README/tests.md: "can use up a receipt number (no test pins this)". Now concrete and run: the repeat takes number 2, the same person through the other door gets `"receipt_id": 3` (`test_a_repeat_uses_up_a_receipt_number`, real desk over HTTP).
4. `docs/real-services.md` did not say that a config file with a byte-order mark is refused on line 1 (run: `load_env` on such a file), that `--assume-yes` exists and is only for `--dry-fakes` (run: refused), or that paths must be full paths (read from the code, `cwd=REPO`; not run).
5. `docs/settings.md` did not say when the HubSpot key file and the mail password file are opened (every CRM call / every send; read from the code, not run with a changed file).
6. `scripts/crash_desk.py` docstring gave a PowerShell form without saying it was not run.

## Count that changed because of our own file
`versions.md` and `docs/limits.md` say "92 test files": true on the frozen tree, 93 once `tests/test_docs_match_tools.py` is added. Both are changed to 93 and `test_the_number_of_test_files_that_two_pages_give_is_the_number_of_test_files` pins them (a future new test file turns it red until the number is updated).
