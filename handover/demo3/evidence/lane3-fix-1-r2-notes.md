# lane3-fix-1, round 2 (builder B1b): notes
Gaps first: (1) I did NOT run the full suite; only tests/test_hygiene.py, the doc-related existing tests and the new file (counts below). (2) Not tried: Windows, n8n (not installed), any claim about n8n menus. (3) D10 and the rest of D11 are not mine (lead / B2). (4) Product code is unchanged (git diff touches README.md, docs/limits.md, docs/n8n-recipe.md and tests/test_docs_claims_lane3.py only). (5) I ran no ruff, mypy, bandit or gitleaks (owner rule: CI only), so the new test file is not lint-checked. (6) The desk ran on private ports 26765/26766 (DESK_PORT, DESK_FAKES_PORT) instead of 8765/8766 because the README's docs take them from the settings; the documented text still says 8765/8766 (defaults). All processes I started were stopped with scripts/reset.sh; the 15-second fakes probe on 26790 ended by its own timeout.

## Real output seen (fresh desk after `bash scripts/reset.sh` then `bash scripts/start_all.sh keyed`, TMPDIR private, 2026-11-13 about 12:58 UTC / 18:28 IST)
/counts reply, verbatim (HTTP 200):
{"received": 0, "new": 0, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "failed_followups": 0, "unknown_followups": 0, "sending_followups": 0, "hung_workers": {"model": 0, "crm": 0, "send": 0, "refresh": 0}, "decide_integrity_errors": 0, "decide_transient_errors": 0, "reaper_running": true, "last_reaper_pass_at": 1794574676, "expected_match": null, "ok": null}
CORRECTION to the round-1 resolver plan (D1): `last_reaper_pass_at` was a number (seconds since 1970), not null, on the first read after start; it is a time, not a count, so "every other NUMBER is 0" would have been false. The text now says "every other COUNT in the reply is 0" and explains `last_reaper_pass_at` separately.

Burst command, three runs in a row on that desk (`--n 100 --email ada@example.com --source form`), verbatim:
- run 1, `--ref-prefix run1`: `STATUS 201=1 200=99`; after it /counts received 100, new 1, duplicate 99; outbox `"count": 1`.
- run 2, SAME `--ref-prefix run1`: `STATUS 201=1 200=99` (the resolver's derivation is CONFIRMED); /counts received 100 (unchanged), new 1; outbox count 1.
- run 3, DIFFERENT `--ref-prefix run2`: `STATUS 200=100`; /counts received 200, new 1, duplicate 199; outbox count 1.
Also: the demo servers answer 404 for `/` (curl on a private port): README's 404 sentence confirmed.

## Items
| item | done how | rung (who decides) | test | before/after |
|---|---|---|---|---|
| D1 README:60 counts comment | rewritten from the real reply above: five counts 0, every other count 0 (named examples), `reaper_running` true, `last_reaper_pass_at` is a time or null, `expected_match`/`ok` null; Windows line says "and so are the other counts; `reaper_running` is `true`" | a ready-made reply read by hand; our words | test_readme_counts_line_matches_the_real_counts_of_a_fresh_desk (starts the real desk, reads its /counts, checks every field the text names) | before: "the other fields ... are not 0" (false); after: true |
| D2 limits.md burst bullet | "fresh desk" defined (reset.sh then start_all.sh keyed); `STATUS 201=1 200=99`; `new` 1 and outbox `"count": 1`; same prefix -> same STATUS and `new` stays 1; different prefix -> `200=100`; deleted "lead count and follow-up count", "just started" | our words from real output | test_readme_demo_and_burst_bullet_match_a_real_replay (real replay: 201 new, 201 replayed, 200 duplicate, 200 replay of duplicate) | before: "all 200" for the repeat (wrong) |
| D3 n8n-recipe key and import | 4 numbered steps; "environment variable" with Linux and PowerShell forms; no delete command (USAGE line), delete on the n8n screen (not tried); import twice = two workflows, `activate` then stops; one word on one line | read from n8n_api.py | test_the_recipe_import_steps_match_the_script | |
| D4 ports | per-file: form and webhook need only 8765; proof needs 8765, 8766 and 5679; files do not read settings; editing needs permission; "three workflow files" removed | counted in n8n/*.json | test_premise_workflow_files_carry_the_default_ports_each + test_the_recipe_names_the_ports_each_workflow_file_needs | |
| D5 reset | "start the demo servers and the desk again" with both start commands; reset deletes records and logs | | test_the_recipe_says_to_reset_and_start_everything_again | |
| D6 port check | `http_code` explained; 000 "usually"; also program that does not speak web or no answer in time; 404 means a program answers (the desk if started earlier; demo servers also 404 on `/`, seen); otherwise stop it or reset | one curl run | test_readme_port_check_explains_000_and_404 | |
| D7 receipt wording | "took a receipt number (2) ... can skip a number" | fact 1 of the resolver; real desk gave receipt_id 3 in the test | in test_readme_demo_and_burst_bullet_match_a_real_replay (receipt_id == 3) | |
| D8 Windows webhook line | same wording as Linux (HTTP 200 not 201, receipt_id 3) | | same test | |
| D9 exit code 1 | "a long error text that means a bug in the program itself, not a setting (the program checks its own built-in constants when it loads; one someone edited to a value that does not fit stops it)" from server.py:1119-1120 | read code | test_exit_code_1_uses_the_words_the_desk_prints | |
| D11 (checkable part) | `list` shows only the first 250 workflows (n8n_api.py:167 `?limit=250`) added in the steps | read code | test_the_recipe_import_steps_match_the_script | the n8n-term explanations NOT done (cannot be verified here; owner / lead) |
| D12 test file | reworked (a)-(g): premise tests renamed `test_premise_...`; fresh-desk test reads a real replay; /counts test reads a real fresh desk; exit-code env built without any DESK_* key; every assert message starts "this sentence protects:" (premise asserts say "premise:"); regex on facts, said in the docstring; docstring says "earlier review readers" | | 9 tests | see proof |

## Proof
1. New test file on the UNPATCHED base (fresh worktree of f3c39cf8, only the test file copied in): `7 failed, 2 passed` (the 2 passing are the premise tests that read files). First failure line: `AssertionError: this sentence protects: limits.md quotes the words the desk prints for exit code 1` (test_exit_code_1_uses_the_words_the_desk_prints). On the patched tree: `9 passed in 1.83s`.
2. Hygiene and doc-related tests on the patched tree: see the result line in the final section below.

## Patch
/home/user/hadavin-sdk/handover/demo3/evidence/lane3-fix-1-r2.patch (against f3c39cf89ec989f032ea48a23cfd824b88da9c68; lane3-fix-1.patch untouched). sha256 3850d88a3d025b60bf70944abf4d035b4694de8283e6a920015f8cda8b9f31ee (computed before the last note edits; the patch file was not changed afterwards). `git apply --check`: OK on a fresh f3c39cf8; OK after claims-stack-on-f3c39cf8.patch; OK after claims stack plus lane3-fix-3.patch.

## Not changed, and why
D10 (code comments in constants.py:256 and server.py:1112 use "sender": product code; contract.md:142 and settings.md:12: B2's files). The unexplained n8n terms of D11 (cannot verify without n8n). The `receipt_id` 3 sentence in the Linux README line was left as the resolver specified; confirmed by a real reply in the test. The tests/ folder has no other doc test changed.
