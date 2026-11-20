# FINDINGS of core-a (non-builder) on core-b's trigger config. Written 06:04 UTC, core-b commit 2b086c2

Test file: tests/test_trigger_config.py (new, mine). Run against core-b's tree unpacked in a scratch folder (nothing of core-b was changed): **93 passed, 16 expected-failures (strict), 20 skipped**. Raw: raw/trigger-config-tests-on-core-b.log. On my own branch the file skips (the config is not there yet). Not checked: pilot and prod configs (demo fixture only), a draft or retired agent as a sender's agent, sender names equal to a tool secret or source token, the whole suite, the database.

## Findings (each is a strict expected-failure in the test file; it turns into a test error the day the code is fixed, so the marker must then be removed)
| id | what the code does today | why it matters | cases |
|---|---|---|---|
| F2 | a sender secret name equal to another platform secret name (tested: the restored-hash key name) is not refused at start | one secret would serve two jobs; a leak of the door secret would also be a leak of the other | 1 |
| F3 | no reader limited to the sender names exists: App has only `secrets`, the whole secret store, so a name no sender lists is handed out | least privilege (preamble rule 11): the worker could read every secret | 1 |
| F4a | text typed into secret_names is echoed by the start check ("secret '<text>' cannot be read at start-up") | someone who pastes a secret VALUE where a NAME belongs gets it printed | 1 |
| F4b | a sender secret name equal to an action secret is refused with the backend sentence, naming neither the sender nor the triggers block | the operator cannot tell where the mistake is | 1 |
| F5 | blank, whitespace-only, newline-holding or leading-space secret names load; a whitespace-only agent_id or principal_id passes the model | bad input should be refused at load, not fail later | 8 |
| F8 | `true` loads as 1 for max_running, max_body_bytes and ack_wait_s | a boolean is not a number | 3 |
| F7 | the default body cap 262144 equals the document cap | a full-size document wrapped in JSON can never be sent (request 001 asked for 2 times) | 1 |

## Differences between core-b's code and requests/001 DRAFT 3 (core-b built the earlier draft)
- `senders` is a map from sender id to sender; a sender has no `id` field; `secret_names` is a tuple.
- `host`, `port`, `allow_non_loopback`, `poll_s` do not exist (my worker uses its own fallbacks).
- `App.trigger_resolve` does not exist; the built way is `app.secrets.get(name)` (finding F3).
- max_running default 4 (asked: 1 until spend reservations exist); body cap default 1 times and ceiling 2 times the document cap (asked: 2 and 8).
- No limit on the number of senders; no TRIGGER_* defaults for port, poll, minimum secret length.
- The two secret-name refusals are joined to the stage "refused" list (asked: their own error).

## What this means for my worker (ORDER 013 item 3)
endpoint.py accepts the map form already. worker.py reads the secrets through `trigger_resolve` and stops with a clear config error while it is missing, so against core-b's code AS IT IS the worker refuses to start. I keep it that way until core-b answers request 001 (the lead said a reader bound to the sender names is coming); switching to `app.secrets` now would build on finding F3.

## Update after the newest heads (core-b c4c7b5522; run 2026-11-20, log raw/MAINT-core-b.log)
- T1 (env-kind alias of a secret name): FIXED. core-b compares secret names in one canonical form (`secret_name.canonical_secret_name`, config.py `_trigger_refusals`), so the 4 alias cases are now refused at start. Verified by reading the code, not only the test. Commit: 6cc472c0a (a commit titled "board" that carries the code; the plan is in handover/core-b/requests/001.answer.md DRAFT 3). The strict marker is removed; the 4 cases are normal tests.
- NEW, not a finding (INTERFACE CHANGE, decided by core-b in requests/001.answer.md DRAFT 3, built in 6cc472c0a): "/" left the secret-name characters (`^[A-Za-z0-9_.:-]{1,128}$`); "." and ".." and a name with ".." or without a letter or digit are refused. Our test `test_secret_name_characters_allowed_as_built[all]` now uses `Key_one.v2:eu.primary-1`; a new test `test_secret_name_with_a_slash_or_a_path_trick_or_no_letter_refused` pins the new refusal.
- Still open: none from this file. The 20 skips (fields not built on core-b: senders limit, poll_s, port, allow_non_loopback) are unchanged.
- Result on c4c7b5522: 696 passed, 20 skipped for the four core-b files together.
