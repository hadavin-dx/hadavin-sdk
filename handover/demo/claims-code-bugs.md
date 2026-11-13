# Claims audit: places where the CODE (or a test) may be wrong, not only the words

Source: claims-fix-v1 stage 1 (builders A, B1, B2), base main c30c3737590de3ea226f82cdd165bf39c5701dce. NOTHING here was changed: the lead decides. Each entry: file:line, evidence, failing example, what is unsure.

## 1. `scripts/start_all.ps1:9` sets `DESK_NUDGE_TO` when `DESK_LEADFLOW_FILE` is an empty string (the desk then refuses to start)
* Evidence: line 9 is `if ($env:DESK_LEADFLOW_FILE -cne 'off' -and $null -eq $env:DESK_NUDGE_TO) { $env:DESK_NUDGE_TO = 'reminder@example.test' }`. It has no test for an empty value. `scripts/start_all.sh:15` has `[[ -n "$DESK_LEADFLOW_FILE" ]]` (handles the empty case). `src/lead_desk/config.py` reads an empty `DESK_LEADFLOW_FILE` as off and `config.py:507-508` then refuses with "DESK_NUDGE_TO is set but DESK_LEADFLOW_FILE is not" (exit 4). `docs/settings.md:17` describes the .sh behaviour.
* Failing example (from reading the code, NOT run: no PowerShell here): set `DESK_LEADFLOW_FILE` to empty text and run the .ps1 start script: the script sets `DESK_NUDGE_TO`, the desk refuses to start with exit 4.
* Unsure: PowerShell normally deletes an environment variable that is set to empty text, so line 8 may then see it as unset and use the demo file; the bug may be reachable only when the variable arrives empty from a parent process.
* Suggested fix (not applied): add `-and $env:DESK_LEADFLOW_FILE` to the condition on line 9.

## 2. `tests/test_input_edge_cases.py::test_two_drives_one_email`: a stale, looser docstring and assertion (a TEST text item, not a code bug)
* Evidence: its docstring says the AI step "may run on both (at most 2 calls)" and it asserts `calls in (1, 2)`; `tests/test_ai_after_claim.py::test_two_drives_ask_model_once` asserts exactly 1 call (passes) and `test_reaper_does_not_ask_model_again` asserts 1. The desk's `_run_followup` claims first and `_after_claim` asks the model only for the claim's winner (`src/lead_desk/desk.py`). So `contract.md:28` ('two simultaneous drives ask the AI step once') is right and the looser test text is stale.
* Not changed because the order says no test changes. A later test patch could tighten the docstring and the assertion to exactly 1 (check the other test first: it may already cover it).

## 3. Not a bug, a choice for the lead: the workflow time-limit comment (`lint.yml:19` vs `sonar.yml:30`)
* The two comments differed ('about twice the first real run' vs '1.6 times the longest observed run'). Builder B2 made `lint.yml` say 1.6 times, the same rule as `sonar.yml`. Neither number is measured. Say if you prefer the other wording or no number.

## 4. Start-up without a reaper ignores the backoff of a pending follow-up (found 12:50Z by the D11 trace; for the lead to decide; code NOT changed)
* Where: `src/lead_desk/desk.py:612-616` (`Desk.startup()` step 3: `if not self._background:` it selects every `pending` row and calls `run_followup`), then `_claim` with `_CLAIM_SQL[("pending",)]` at `desk.py:190-194` (`auto_attempts=auto_attempts+1`, no time test).
* The reaper (`reap_once`, `desk.py:737-744`) and client replays (`_pending_and_due`, `desk.py:1417-1431`) honour the backoff; the reaper-off start-up path does not. The server always starts the reaper first (`server.py:1195-1196`), so production is not affected; a start-up without a reaper (tests, a future caller) spends one try on every pending row, even one whose backoff has not passed, and a send may happen at once.
* Failing example (reading, not run): pending row, `auto_attempts=1`, `updated_at=now`; `Desk(...).startup()` with no `start_background()` -> `auto_attempts` becomes 2 at once. No test covers it in either mode (D11 found none). Two tests to add if wanted: reaper off -> 2; reaper on -> stays 1 until the clock passes the backoff.
* Words fixed in contract.md (v8): both start-up sentences now say which mode they describe.
